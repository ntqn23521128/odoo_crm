from odoo import models, fields, api

# ---------------------------------------------------------
# CLASS 1: XỬ LÝ THẺ LOYALTY (Trừ điểm + Gửi Mail)
# ---------------------------------------------------------
class LoyaltyCard(models.Model):
    _inherit = 'loyalty.card'

    @api.model
    def action_redeem_and_notify(self, card_id, points_to_deduct, product_name):
        """
        Hàm này được gọi từ POS để:
        1. Trừ điểm
        2. Gửi email thông báo
        """
        # 1. Tìm thẻ Loyalty
        card = self.browse(card_id)
        if not card.exists():
            return {'success': False, 'msg': 'Không tìm thấy thẻ Loyalty.'}

        # 2. Trừ điểm
        new_points = card.points - points_to_deduct
        card.write({'points': new_points})

        # 3. Gửi Email (Nếu khách có email)
        partner = card.partner_id
        if partner.email:
            subject = f"Đổi thưởng thành công: {product_name}"
            body = f"""
                <div style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #008744;">Xác nhận đổi thưởng</h2>
                    <p>Xin chào <strong>{partner.name}</strong>,</p>
                    <p>Bạn vừa đổi <strong>{points_to_deduct} điểm</strong> tại cửa hàng để nhận món: <strong>{product_name}</strong>.</p>
                    <hr>
                    <p style="font-size: 16px;">Điểm còn lại của bạn: <strong style="color: #d62d20;">{new_points}</strong></p>
                    <p>Cảm ơn bạn đã sử dụng dịch vụ!</p>
                </div>
            """
            
            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_to': partner.email,
                'auto_delete': True,
            }
            try:
                self.env['mail.mail'].create(mail_values).send()
                print(f">>> [DEBUG] Email sent to {partner.email}")
            except Exception as e:
                print(f">>> [ERROR] Failed to send email: {e}")

        return {'success': True, 'new_points': new_points}


class PosOrder(models.Model):
    _inherit = 'pos.order'

    # Field 1: Bạn đã thêm lúc nãy
    reward_redeemed = fields.Boolean(string="Reward Redeemed", default=False)

    # Field 2: SỬA LỖI HIỆN TẠI (reward_points_spent)
    reward_points_spent = fields.Float(string="Points Spent", default=0)

    # Field 3: KHUYẾN NGHỊ THÊM LUÔN (để tránh lỗi tiếp theo nếu XML có gọi)
    reward_description = fields.Char(string="Reward Description")
