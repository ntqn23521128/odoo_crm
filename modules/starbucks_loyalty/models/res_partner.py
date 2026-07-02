# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Tổng số Sao (Integer, khớp DB hiện tại)
    star_points = fields.Integer(
        string="Starbucks Points",
        default=0,
        help="Số Sao tích lũy (1 Sao ~ 40.000₫).",
    )

    # Hạng thành viên (tinh gọn: Green / Gold)
    loyalty_tier = fields.Selection(
        [
            ("green", "Green"),
            ("gold", "Gold"),
        ],
        string="Starbucks Tier",
        default="green",
        help="Hạng thành viên Starbucks.",
    )

    def _recompute_loyalty_tier(self):
        """
        Rule tinh gọn cho đồ án:
        - Green: < 100 Sao
        - Gold : >= 100 Sao
        """
        for partner in self:
            pts = partner.star_points or 0
            tier = "green"
            if pts >= 100:
                tier = "gold"

            partner.loyalty_tier = tier
            _logger.info(
                "🎖 Cập nhật Tier cho %s: %s Sao → %s",
                partner.name,
                pts,
                tier,
            )

    @api.model_create_multi
    def create(self, vals_list):
        # Đảm bảo mỗi partner mới đều có star_points = 0 nếu chưa set
        for vals in vals_list:
            vals.setdefault("star_points", 0)

        partners = super().create(vals_list)
        # Tính tier cho tất cả partner vừa tạo
        partners._recompute_loyalty_tier()
        return partners

    def write(self, vals):
        res = super().write(vals)
        if "star_points" in vals:
            self._recompute_loyalty_tier()
        return res
