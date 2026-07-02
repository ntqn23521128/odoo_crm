# -*- coding: utf-8 -*-
from odoo import models
import logging

_logger = logging.getLogger(__name__)

# Quy đổi tiền -> Sao
POINT_RATE = 40000.0  # 40.000₫ = 1 Sao


class PosOrder(models.Model):
    _inherit = "pos.order"

    def action_pos_order_paid(self):
        """
        Khi hóa đơn POS được thanh toán → cộng điểm cho khách hàng.
        Quy tắc:
          - raw_points = amount_total / 40000
          - chỉ lấy PHẦN NGUYÊN (floor), không làm tròn lên
        """
        res = super(PosOrder, self).action_pos_order_paid()

        for order in self:
            partner = order.partner_id
            if not partner:
                _logger.info(
                    "⚠ POS Order %s không có khách hàng, bỏ qua tích điểm.",
                    order.name,
                )
                continue

            amount = order.amount_total or 0.0
            raw_points = amount / POINT_RATE
            delta_points = int(raw_points)  # lấy phần nguyên, không làm tròn

            if delta_points <= 0:
                _logger.info(
                    "ℹ POS %s: số tiền %s chưa đủ 1 Sao, không cộng điểm.",
                    order.name,
                    amount,
                )
                continue

            old_points = partner.star_points or 0
            new_points = old_points + delta_points

            # Cập nhật điểm
            partner.write({"star_points": new_points})
            # Tính lại tier
            partner._recompute_loyalty_tier()

            _logger.info(
                "⭐ POS %s: %s₫ -> raw=%.2f Sao -> +%s Sao. %s: %s → %s",
                order.name,
                amount,
                raw_points,
                delta_points,
                partner.name,
                old_points,
                new_points,
            )

        return res
