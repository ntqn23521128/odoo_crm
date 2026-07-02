# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class StarbucksRewardsPortal(http.Controller):

    @http.route('/my/rewards', type='http', auth='user', website=True)
    def my_rewards(self, **kw):
        """Trang xem điểm thưởng cho user đang đăng nhập."""
        user = request.env.user
        partner = user.partner_id

        values = {
            "user": user,
            "partner": partner,
            "star_points": partner.star_points or 0,
            "loyalty_tier": partner.loyalty_tier or "member",
        }
        return request.render("starbucks_rewards_portal.my_rewards_template", values)
