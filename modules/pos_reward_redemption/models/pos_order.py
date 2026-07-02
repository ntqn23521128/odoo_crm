# pos_reward_redemption/models/pos_order.py
from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    reward_redeemed = fields.Boolean(
        string="Reward Redeemed",
        help="Đơn hàng này có thực hiện đổi thưởng.",
        default=False,
    )
    reward_points_spent = fields.Float(
        string="Points Spent for Reward",
        help="Số điểm loyalty đã sử dụng để đổi thưởng.",
    )
    reward_description = fields.Char(
        string="Reward Description",
        help="Mô tả phần thưởng: Free Latte, Free Pastry..."
    )

    def action_pos_order_paid(self):
        """Sau khi POS order được thanh toán:
        - Nếu có thông tin đổi thưởng -> đánh dấu
        - Gửi email thông báo cho khách (nếu có email)
        """
        res = super().action_pos_order_paid()

        for order in self:
            # Chỉ xử lý nếu có đổi thưởng (points_spent > 0 hoặc có description)
            if not order.reward_points_spent and not order.reward_description:
                continue

            order.reward_redeemed = True

            # Gửi email nếu khách hàng có email
            if order.partner_id and order.partner_id.email:
                template = self.env.ref(
                    "pos_reward_redemption.mail_template_reward_redeemed",
                    raise_if_not_found=False,
                )
                if template:
                    template.with_context(
                        reward_points=order.reward_points_spent,
                        reward_desc=order.reward_description,
                    ).send_mail(order.id, force_send=True)

        return res
