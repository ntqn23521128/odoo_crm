# -*- coding: utf-8 -*-
{
    'name': 'Starbucks Loyalty Program',
    'version': '1.0.0',
    'category': 'CRM/Loyalty',
    'sequence': 10,
    'author': 'Your Team',
    'website': 'https://starbucksrewards.vn',
    'license': 'LGPL-3',

    'description': """
        Starbucks Loyalty Program - Registration & Activation
        - Customer registration via WordPress API
        - Partner creation in Odoo
        - Portal user creation
        - Email notifications
    """,

    'depends': [
        'base',
        'crm',
        'portal',
        'website',
        'mail',
	'point_of_sale',
    ],

    'data': [
        'security/ir.model.access.csv',   # Giữ cũng được
        'views/res_partner_view.xml',
    ],

    'installable': True,
    'auto_install': False,
}
