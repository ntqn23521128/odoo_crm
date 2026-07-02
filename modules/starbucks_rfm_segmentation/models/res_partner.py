from odoo import models, fields, api
from datetime import datetime, timedelta

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # RFM Fields
    rfm_recency_score = fields.Integer('Recency Score', compute='_compute_rfm', store=True)
    rfm_frequency_score = fields.Integer('Frequency Score', compute='_compute_rfm', store=True)
    rfm_monetary_score = fields.Integer('Monetary Score', compute='_compute_rfm', store=True)
    rfm_total_score = fields.Integer('Total RFM Score', compute='_compute_rfm', store=True)
    rfm_segment = fields.Selection([
        ('new', 'New Customer'),       # Khách mới
        ('potential', 'Potential'),    # Khách tiềm năng (Mới thêm cho rõ ràng hơn)
        ('loyal', 'Loyal Customer'),   # Khách trung thành (VIP)
        ('at_risk', 'At Risk'),        # Cần chăm sóc (Sắp rời bỏ)
        ('lost', 'Lost Customer'),     # Đã rời bỏ
    ], string='RFM Segment', compute='_compute_rfm', store=True)

    # Product Segment Fields
    product_segments = fields.Char('Product Segments', compute='_compute_product_segments', store=True)

    @api.depends('sale_order_ids', 'sale_order_ids.state', 'sale_order_ids.date_order',
                 'pos_order_ids', 'pos_order_ids.state', 'pos_order_ids.date_order')
    def _compute_rfm(self):
        for partner in self:
            # Recency: Days since last purchase
            last_sale = self.env['sale.order'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'sale')
            ], order='date_order desc', limit=1)
            last_pos = self.env['pos.order'].search([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['paid', 'done'])
            ], order='date_order desc', limit=1)

            last_order_date = max(
                last_sale.date_order if last_sale else datetime.min,
                last_pos.date_order if last_pos else datetime.min
            )
            recency_days = (datetime.now() - last_order_date).days if last_order_date != datetime.min else 999

            # Frequency: Number of orders in last 6 months
            six_months_ago = datetime.now() - timedelta(days=180)
            sale_count = self.env['sale.order'].search_count([
                ('partner_id', '=', partner.id),
                ('state', '=', 'sale'),
                ('date_order', '>=', six_months_ago)
            ])
            pos_count = self.env['pos.order'].search_count([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['paid', 'done']),
                ('date_order', '>=', six_months_ago)
            ])
            frequency = sale_count + pos_count

            # Monetary: Total spent in last 6 months
            sale_total = sum(self.env['sale.order'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'sale'),
                ('date_order', '>=', six_months_ago)
            ]).mapped('amount_total'))
            pos_total = sum(self.env['pos.order'].search([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['paid', 'done']),
                ('date_order', '>=', six_months_ago)
            ]).mapped('amount_total'))  # Sửa từ 'amount' thành 'amount_total'
            monetary = sale_total + pos_total

            # Scoring
            # Recency Score (Càng thấp càng tốt -> điểm cao)
            r_score = (
                5 if recency_days <= 7 else    # Mới mua tuần này
                4 if recency_days <= 14 else   # Mới mua 2 tuần đổ lại
                3 if recency_days <= 30 else   # Mới mua trong tháng
                2 if recency_days <= 60 else   # Đã 2 tháng chưa mua (Báo động)
                1                              # Hơn 2 tháng (Nguy cơ mất khách cao)
            )

            # Frequency Score (Càng nhiều càng tốt)
            f_score = (
                5 if frequency >= 50 else      # ~2 ly/tuần liên tục 6 tháng (VIP)
                4 if frequency >= 24 else      # ~1 ly/tuần
                3 if frequency >= 12 else      # ~2 ly/tháng
                2 if frequency >= 6 else       # ~1 ly/tháng
                1
            )

            # Monetary Score (Tổng tiền chi tiêu 6 tháng)
            m_score = (
                5 if monetary >= 5000000 else  # > 5 triệu 
                4 if monetary >= 2500000 else  # > 2.5 triệu
                3 if monetary >= 1200000 else  # > 1.2 triệu
                2 if monetary >= 600000 else   # > 600k
                1
            )
            total_score = r_score + f_score + m_score

            # Assign RFM Segment
            if r_score == 1:
                # Nếu quá lâu không mua -> Đã mất
                segment = 'lost'
            elif r_score == 5 and f_score == 1:
                # Mới mua gần đây nhưng tổng số lần mua ít -> Khách mới
                segment = 'new'
            elif total_score >= 12:
                # Điểm tổng cao -> Trung thành
                segment = 'loyal'
            elif r_score <= 2 and f_score >= 3:
                # Từng mua nhiều nhưng gần đây ít mua -> Có nguy cơ rời bỏ
                segment = 'at_risk'
            else:
                # Còn lại -> Tiềm năng
                segment = 'potential'

            # Update fields
            partner.rfm_recency_score = r_score
            partner.rfm_frequency_score = f_score
            partner.rfm_monetary_score = m_score
            partner.rfm_total_score = total_score
            partner.rfm_segment = segment

    @api.depends('sale_order_ids', 'sale_order_ids.order_line', 'pos_order_ids', 'pos_order_ids.lines')
    def _compute_product_segments(self):
        for partner in self:
            segments = []
            six_months_ago = datetime.now() - timedelta(days=180)

            # Define product keywords for segmentation
            product_categories = {
                'Coffee Lover': ['Espresso & Coffee'],
                'Frappuccino Lover': ['Frappuccino & Blended'],
                'Tea Lover': ['Teavana & Matcha'],
                'Food Lover': ['Bakery & Food'],
            }

            # Count purchases per product category
            for segment_name, keywords in product_categories.items():
                sale_lines = self.env['sale.order.line'].search([
                    ('order_id.partner_id', '=', partner.id),
                    ('order_id.state', '=', 'sale'),
                    ('order_id.date_order', '>=', six_months_ago),
                    ('product_id.name', 'ilike', '%' + '%'.join(keywords) + '%')
                ])
                pos_lines = self.env['pos.order.line'].search([
                    ('order_id.partner_id', '=', partner.id),
                    ('order_id.state', 'in', ['paid', 'done']),
                    ('order_id.date_order', '>=', six_months_ago),
                    ('product_id.name', 'ilike', '%' + '%'.join(keywords) + '%')
                ])
                total_count = len(sale_lines) + len(pos_lines)
                if total_count >= 3:  # Ngưỡng: 5 lần mua trong 6 tháng
                    segments.append(segment_name)

            # Update product segments
            partner.product_segments = ', '.join(segments) if segments else 'No Segment'

    def action_run_segmentation(self):
        """Manually trigger RFM and product segmentation"""
        self._compute_rfm()
        self._compute_product_segments()