from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        users = super(ResUsers, self).create(vals_list)
        for user in users:
            # 1. Tự động cấp Group Nhân viên để vào được Project/Task
            try:
                group_game = self.env.ref('quan_ly_du_an.group_game_user')
                user.sudo().write({'groups_id': [(4, group_game.id)]})
            except: pass

            # 2. Tự động đẻ ra hồ sơ Nhân sự
            if not self.env['nhan_vien'].sudo().search([('user_id', '=', user.id)]):
                self.env['nhan_vien'].sudo().create({
                    'ho_ten_dem': 'Hồ sơ',
                    'ten': user.name,
                    'email': user.login,
                    'user_id': user.id,
                    'ma_dinh_danh': 'ID' + str(user.id),
                    'vai_tro': '3d_artist', 
                })
        return users