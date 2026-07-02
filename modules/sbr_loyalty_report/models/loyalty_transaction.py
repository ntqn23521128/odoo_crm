from odoo import models, fields

# Tạm thời bỏ qua file này vì module gốc không có bảng History
# class LoyaltyTransaction(models.Model):
#     _inherit = 'starbucks.point.history' 
#     report_id = fields.Many2one('starbucks.loyalty.report', string='Report Reference')