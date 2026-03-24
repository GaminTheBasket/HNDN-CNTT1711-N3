# -*- coding: utf-8 -*-
{
    'name': "nhan_su",
    'summary': "Module HRM - Nguồn dữ liệu gốc nhân sự",
    'version': '0.1',
    'author': "My Company",
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml', # THÊM DÒNG NÀY
        'views/chuc_vu.xml',
        'views/don_vi.xml',
        'views/nhan_vien.xml',
        'views/lich_su_cong_tac.xml',
        'views/chung_chi_bang_cap.xml',
        'views/danh_sach_chung_chi_bang_cap.xml',
        'views/menu.xml',
    ],
}