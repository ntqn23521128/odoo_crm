{
    'name': 'Starbucks RFM and Dynamic Segmentation',
    'version': '1.0',
    'summary': 'Automated RFM Analysis and Dynamic Customer Segmentation for Starbucks',
    'description': """
        Module to automate RFM analysis and create dynamic segments like Latte Lovers, Matcha Lovers,
        and RFM segments (New Customer, Loyal Customer, Churn Risk) for Starbucks CRM.
    """,
    'author': 'Your Name',
    'depends': ['sale', 'point_of_sale'],
    'data': [
        'views/customer_views.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'auto_install': False,
}