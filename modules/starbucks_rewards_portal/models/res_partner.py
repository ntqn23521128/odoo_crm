# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Không đặt store=True để mỗi lần mở contact là đọc lại điểm mới nhất
    starbucks_stars = fields.Float(
        string="Starbucks Stars",
        compute="_compute_starbucks_stars",
        help="Số sao Starbucks (đọc từ Loyalty Card chương trình 'Starbucks Stars').",
    )

    def _compute_starbucks_stars(self):
        """Đọc điểm từ loyalty.card của chương trình 'Starbucks Stars'."""
        LoyaltyProgram = self.env['loyalty.program']
        LoyaltyCard = self.env['loyalty.card']

        # Tìm chương trình Starbucks Stars (đúng tên bạn đã tạo trong POS)
        program = LoyaltyProgram.search([('name', '=', 'Starbucks Stars')], limit=1)

        for partner in self:
            if not program:
                partner.starbucks_stars = 0.0
                continue

            card = LoyaltyCard.search([
                ('partner_id', '=', partner.id),
                ('program_id', '=', program.id),
            ], limit=1)

            # card.points chính là số "Star" mà POS đang dùng
            partner.starbucks_stars = card.points or 0.0
