from odoo import models, fields, api

class GhiNhanThoiGian(models.Model):
    _name = 'ghi_nhan_thoi_gian'
    _description = 'Quản lý ghi nhận thời gian làm việc'
    
    
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách")
    cong_viec_id = fields.Many2one("cong_viec", string="Công việc", required=True)
    so_gio_lam_viec = fields.Float("Số giờ làm việc", required=True)  
    ngay_ghi_nhan = fields.Date("Ngày ghi nhận", required=True)       
