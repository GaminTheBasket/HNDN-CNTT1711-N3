# -*- coding: utf-8 -*-
{
    'name': "nhan_su",

    'summary': """
        Module HRM - Nguồn dữ liệu gốc nhân sự cho toàn hệ thống (Tích hợp hệ thống)
    """,

    'description': """
        Quản lý nhân sự (HRM). Dữ liệu nhân viên (model nhan_vien) là dữ liệu gốc,
        đồng bộ sang các module khác (Dự án, Công việc, Lương...) theo yêu cầu tích hợp.
        Các module khác bắt buộc phụ thuộc nhan_su và sử dụng chung model nhan_vien,
        không nhập liệu trùng lặp.
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/chuc_vu.xml',
        'views/don_vi.xml',
        'views/nhan_vien.xml',
        'views/lich_su_cong_tac.xml',
        'views/chung_chi_bang_cap.xml',
        'views/danh_sach_chung_chi_bang_cap.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
