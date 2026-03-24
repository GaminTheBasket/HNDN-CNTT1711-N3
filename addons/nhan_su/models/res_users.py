from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        # 1. Tạo User trước
        users = super(ResUsers, self).create(vals_list)
        
        for user in users:
            # 2. Tạo nhân viên tương ứng (Sudo để tránh lỗi phân quyền khi tạo)
            if not self.env['nhan_vien'].sudo().search([('user_id', '=', user.id)]):
                self.env['nhan_vien'].sudo().create({
                    'ho_ten_dem': 'Hồ sơ',
                    'ten': user.name,
                    'email': user.login,
                    'user_id': user.id,
                    'ma_dinh_danh': 'ID' + str(user.id),
                })
        return users