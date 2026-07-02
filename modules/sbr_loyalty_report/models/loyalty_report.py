# File: models/loyalty_report.py
from odoo import models, fields

class LoyaltyReport(models.Model):
    _name = 'starbucks.loyalty.report'
    _description = 'Starbucks Loyalty Report'

    name = fields.Char(string='Tên báo cáo', required=True, default='Báo cáo')
    min_points = fields.Integer(string='Điểm tối thiểu', default=0)
    
    # DÒNG QUAN TRỌNG NHẤT:
    partner_ids = fields.Many2many('res.partner', string='Khách hàng') 

    def action_generate_report(self):
        domain = [('star_points', '>=', self.min_points)]
        partners = self.env['res.partner'].search(domain)
        self.write({'partner_ids': [(6, 0, partners.ids)]})