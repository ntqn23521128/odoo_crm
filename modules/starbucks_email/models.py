from odoo import models, api, fields
import requests
import json
import datetime
import calendar

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Cấu hình SendGrid
    API_KEY = "" 
    FROM_EMAIL = "nguyenthiquynhnhu26092005@gmail.com"

    # Hàm hỗ trợ gửi API (Dùng chung)
    def _send_sendgrid_api(self, to_email, to_name, subject, html_content):
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "personalizations": [{"to": [{"email": to_email, "name": to_name}], "subject": subject}],
            "from": {"email": self.FROM_EMAIL, "name": "Starbucks Vietnam"},
            "content": [{"type": "text/html", "value": html_content}]
        }
        try:
            return requests.post(url, headers=headers, json=payload)
        except Exception as e:
            return None

    # 1. CRON JOB: Gửi Voucher Đầu Tháng (sinh mã tự động)
    @api.model
    def cron_send_birthday_voucher(self):
        today = datetime.date.today()
        current_month = today.month
        current_year = today.year
        
        # --- LOGIC MỚI: TÍNH NGÀY CUỐI THÁNG ---
        # calendar.monthrange trả về (thứ đầu tuần, số ngày trong tháng)
        # Lấy phần tử [1] để lấy số ngày (ví dụ tháng 2 năm nhuận là 29)
        last_day = calendar.monthrange(current_year, current_month)[1]
        
        # Tạo ngày hết hạn: Năm nay - Tháng này - Ngày cuối cùng
        end_of_month_date = datetime.date(current_year, current_month, last_day)
        # ---------------------------------------

        # Tên chương trình khuyến mãi đã tạo trong Odoo
        PROGRAM_NAME = "Voucher Sinh Nhật Tự Động" 

        # 1. Tìm chương trình khuyến mãi trong DB
        loyalty_program = self.env['loyalty.program'].search([('name', '=', PROGRAM_NAME)], limit=1)
        
        if not loyalty_program:
            # Tự động tạo chương trình nếu chưa có (tránh lỗi code)
            loyalty_program = self.env['loyalty.program'].create({
                'name': PROGRAM_NAME,
                'program_type': 'coupon',
                'trigger': 'auto',
                'applies_on': 'future',
                'rule_ids': [(0, 0, {'reward_point_mode': 'order', 'reward_point_amount': 1})],
                'reward_ids': [(0, 0, {'reward_type': 'discount', 'discount': 50, 'discount_mode': 'percent'})]
            })

        # 2. Tìm khách hàng có sinh nhật trong tháng
        partners = self.search([('birthday', '!=', False), ('email', '!=', False)])
        
        for record in partners:
            if record.birthday.month == current_month:
                
                # 3. Tạo mã coupon độc nhất cho khách hàng
                coupon = self.env['loyalty.card'].create({
                    'program_id': loyalty_program.id,
                    'partner_id': record.id,
                    'points': 0, 
                    'expiration_date': end_of_month_date # <--- SỬ DỤNG NGÀY ĐÃ TÍNH Ở TRÊN
                })
                
                # Lấy mã code vừa sinh ra
                unique_code = coupon.code

                # 4. Soạn nội dung email
                subject = f"🎂 Chào tháng sinh nhật của {record.name}!"
                
                # Format lại ngày cho đẹp (VD: 30/11/2025)
                expiry_str = end_of_month_date.strftime('%d/%m/%Y')
                
                html_content = f"""
                <div style="font-family: Arial; text-align: center; padding: 20px;">
                    <h2 style="color: #d63384;">HELLO {today.strftime('%B').upper()} BABY!</h2>
                    <p>Tháng này là tháng của bạn. Starbucks gửi tặng bạn món quà nhỏ:</p>
                    <div style="border: 2px dashed #d63384; padding: 15px; display: inline-block; margin: 15px 0; background-color: #fff0f5;">
                        <span style="display:block; font-size:12px; color:#666;">Mã ưu đãi riêng của bạn:</span>
                        <strong style="font-size: 24px; color: #d63384;">{unique_code}</strong>
                        <br/>
                        <span style="font-size: 11px; color: red;">HSD: {expiry_str}</span>
                    </div>
                    <p>Giảm 50% hoặc Tặng 1 bánh (Chỉ áp dụng cho tài khoản của bạn)</p>
                </div>
                """
                
                # 5. Gửi qua SendGrid
                response = self._send_sendgrid_api(record.email, record.name, subject, html_content)
                
                if response and response.status_code == 202:
                    record.message_post(body=f"🎁 [AUTO] Đã gửi mã {unique_code}, HSD: {expiry_str}")

    # 2. CRON JOB: Gửi Lời Chúc Đúng Ngày (Chạy hàng ngày)
    @api.model
    def cron_send_birthday_wishes(self):
        today = datetime.date.today()
        current_day = today.day
        current_month = today.month
        
        partners = self.search([('birthday', '!=', False), ('email', '!=', False)])
        
        for record in partners:
            if record.birthday.day == current_day and record.birthday.month == current_month:
                subject = f"🎉 Happy Birthday {record.name}!"
                html_content = f"""
                <div style="font-family: Arial; text-align: center; padding: 20px; background-color: #fff8e1;">
                    <h1 style="color: #ff9800;">CHÚC MỪNG SINH NHẬT!</h1>
                    <p>Hôm nay là một ngày thật đặc biệt.</p>
                    <p>Starbucks chúc <strong>{record.name}</strong> tuổi mới rực rỡ! ☕</p>
                    <p><i>Đừng quên ghé cửa hàng để dùng mã ưu đãi chúng tôi đã gửi đầu tháng nhé!</i></p>
                </div>
                """
                response = self._send_sendgrid_api(record.email, record.name, subject, html_content)
                if response and response.status_code == 202:
                    record.message_post(body="🎂 [AUTO] Đã gửi lời chúc đúng ngày sinh nhật.")