# -*- coding: utf-8 -*-
{
    'name': "quan_ly_du_an",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Quản Lý dự án
    """,

    'author': "phuccthuan",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    # nhan_su (HRM) là nguồn dữ liệu gốc nhân sự - đồng bộ theo yêu cầu tích hợp hệ thống
    'depends': ['base', 'nhan_su'],

    # always loaded
    'data': [
        'security/security_groups.xml', # FILE NÀY PHẢI NẰM TRÊN CSV
        'security/ir.model.access.csv',
        'views/du_an.xml',
        'views/dashboard.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
