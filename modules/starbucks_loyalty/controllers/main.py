# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
from datetime import datetime
import logging
import traceback

_logger = logging.getLogger(__name__)

WELCOME_BONUS = 200   # +200 điểm khi đăng ký lần đầu


class LoyaltyAPI(http.Controller):

    # -------------------- API ĐĂNG KÝ TỪ WORDPRESS -------------------- #
    @http.route('/api/loyalty/register', type='json', auth='public', methods=['POST'], csrf=False)
    def register_customer(self, **kwargs):
        try:
            try:
                data = request.get_json_data()
            except Exception:
                data = request.params or {}

            email = (data.get('email') or '').strip().lower()
            full_name = (data.get('full_name') or '').strip()
            phone = (data.get('phone') or '').strip()
            password = data.get('password') or ''
            confirm_password = data.get('confirm_password') or ''
            dob = (data.get('dob') or '').strip()

            _logger.info("📩 API register: email=%s, name=%s", email, full_name)

            # --- Validate cơ bản ---
            if not email or '@' not in email:
                raise UserError('Email không hợp lệ.')

            if not full_name or len(full_name) < 3:
                raise UserError('Họ tên phải có ít nhất 3 ký tự.')

            if len(password) < 6:
                raise UserError('Mật khẩu phải có ít nhất 6 ký tự.')

            if password != confirm_password:
                raise UserError('Mật khẩu không khớp.')

            if dob:
                try:
                    datetime.strptime(dob, '%Y-%m-%d')
                except ValueError:
                    _logger.warning("❌ Ngày sinh sai định dạng YYYY-MM-DD: %s", dob)

            Partner = request.env['res.partner'].sudo()
            Users = request.env['res.users'].sudo().with_context(active_test=False)

            # --- Lấy group Portal ---
            portal_group = request.env.ref('base.group_portal')

            # --- Tự dò field nhóm của res.users ---
            user_fields = Users._fields
            group_field = None
            for candidate in ('groups_id', 'group_ids', 'groups'):
                if candidate in user_fields:
                    group_field = candidate
                    break

            if not group_field:
                _logger.warning("⚠️ Không tìm thấy field chứa groups trên res.users!")

            # --- Tìm hoặc tạo partner ---
            partner = Partner.search([('email', '=', email)], limit=1)

            if partner:
                vals = {}
                if partner.name != full_name:
                    vals['name'] = full_name
                if phone and partner.phone != phone:
                    vals['phone'] = phone
                if vals:
                    partner.write(vals)
            else:
                partner = Partner.create({
                    'name': full_name,
                    'email': email,
                    'phone': phone or False,
                    'is_company': False,
                    'customer_rank': 1,
                    'star_points': 0,
                    'loyalty_tier': 'green',
                })

            # --- Tìm hoặc tạo user ---
            user = Users.search([('login', '=', email)], limit=1)

            if user:
                if user.active:
                    raise UserError(
                        "Email này đã được đăng ký và kích hoạt tài khoản. "
                        "Vui lòng dùng email khác hoặc đăng nhập."
                    )
                else:
                    write_vals = {
                        'active': True,
                        'password': password,
                        'partner_id': partner.id,
                    }
                    if portal_group and group_field:
                        write_vals[group_field] = [(6, 0, [portal_group.id])]
                    user.write(write_vals)
                    user_id = user.id
            else:
                user_vals = {
                    'name': full_name,
                    'login': email,
                    'email': email,
                    'password': password,
                    'partner_id': partner.id,
                    'active': True,
                }
                if portal_group and group_field:
                    user_vals[group_field] = [(6, 0, [portal_group.id])]

                user = Users.create(user_vals)
                user_id = user.id

            # --- Welcome Bonus ---
            try:
                if partner.star_points == 0:
                    partner.write({'star_points': partner.star_points + WELCOME_BONUS})
                    if hasattr(partner, '_recompute_loyalty_tier'):
                        partner._recompute_loyalty_tier()
            except Exception:
                _logger.warning("⚠️ Lỗi khi cộng điểm Welcome Bonus")

            # --- Gửi email ---
            try:
                mail_values = {
                    'subject': '🎉 Chào mừng đến với Starbucks Rewards',
                    'email_to': email,
                    'email_from': 'noreply@starbucksrewards.vn',
                    'body_html': f"""
                    <html>
                    <body>
                        <h2>☕ Chào mừng, {full_name}!</h2>
                        <p>Tài khoản Starbucks Rewards của bạn đã được tạo thành công.</p>
                        <p><b>Email đăng nhập:</b> {email}</p>
                        <p><b>Điểm hiện tại:</b> {partner.star_points} ⭐</p>
                        <p>
                            <a href="http://localhost:8069/loyalty/activate?email={email}"
                               style="background:#00704A;color:white;padding:12px 25px;border-radius:8px;text-decoration:none;">
                               Kích hoạt & xem điểm thưởng
                            </a>
                        </p>
                    </body>
                    </html>
                    """,
                }
                mail = request.env['mail.mail'].sudo().create(mail_values)
                mail.send()
            except Exception:
                _logger.warning("⚠️ Lỗi gửi email:\n%s", traceback.format_exc())

            return {
                'success': True,
                'message': f'Đăng ký thành công! Bạn có thể đăng nhập bằng email {email}.',
                'partner_id': partner.id,
                'user_id': user_id,
                'email': email,
                'star_points': partner.star_points,
            }

        except UserError as ue:
            return {'success': False, 'message': str(ue)}

        except Exception as e:
            _logger.error("❌ Lỗi register_customer:\n%s", traceback.format_exc())
            return {'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}

    # -------------------- API CỘNG ĐIỂM -------------------- #
    @http.route('/api/loyalty/add_points', type='json', auth='public', methods=['POST'], csrf=False)
    def add_points(self, **kwargs):
        try:
            try:
                data = request.get_json_data()
            except Exception:
                data = request.params or {}

            email = (data.get('email') or '').strip().lower()
            points = int(data.get('points') or 0)

            Partner = request.env['res.partner'].sudo()
            partner = Partner.search([('email', '=', email)], limit=1)

            if not partner:
                raise UserError("Không tìm thấy khách hàng với email này.")

            new_points = partner.star_points + points
            partner.write({'star_points': new_points})

            if hasattr(partner, '_recompute_loyalty_tier'):
                partner._recompute_loyalty_tier()

            return {
                'success': True,
                'message': f"Đã cộng {points} điểm.",
                'email': email,
                'new_points': new_points,
            }

        except Exception as e:
            return {'success': False, 'message': str(e)}

    # -------------------- LINK KÍCH HOẠT EMAIL -------------------- #
    @http.route('/loyalty/activate', type='http', auth='public', website=True)
    def loyalty_activate(self, email='', **kwargs):

        if request.session.uid:
            request.session.logout()

        email = (email or '').strip().lower()

        login_url = f"/web/login?login={email}&redirect=/my/rewards"
        return request.redirect(login_url)
