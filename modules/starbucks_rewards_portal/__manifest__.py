# -*- coding: utf-8 -*-
{
    'name': 'Starbucks Rewards Portal',
    'version': '1.0.0',
    'category': 'Website',
    'summary': 'Trang xem điểm thưởng Starbucks cho portal user',
    'depends': [
        'website',
        'portal',
        'pos_loyalty',          # cần vì dùng loyalty.card, loyalty.program
    ],
    'data': [
        'views/res_partner_view.xml',        # sẽ tạo ở bước 3
        'views/starbucks_rewards_templates.xml',
    ],
    'installable': True,
    'application': False,
}
