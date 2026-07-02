{
    "name": "POS Reward Redemption Logger",
    "summary": "Ghi log và gửi email khi khách đổi thưởng trên POS",
    "version": "19.0.1.0.0",
    "category": "Sales/Point of Sale",
    "author": "Your Name",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "mail"],
    "data": [
        "views/reward_redemption_views.xml",
    ],
"assets": {
        "point_of_sale.assets_prod": [
            "pos_reward_redemption/static/src/xml/manual_reward_action.xml",
            "pos_reward_redemption/static/src/js/manual_reward_action.js",
        ],
    },
    "installable": True,
    "application": True,
}
