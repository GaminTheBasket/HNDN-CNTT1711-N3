from odoo import models, fields, api

class DanhGiaCongViec(models.Model):
    _name = 'danh_gia_cong_viec'
    _description = 'Quản lý đánh giá công việc'
    
    
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách")
    cong_viec_id = fields.Many2one("cong_viec", string="Công việc", required=True)
    kpi = fields.Float("kpi", required=True)  
    nhan_xet = fields.Text("Nhận xét", required=True)       
