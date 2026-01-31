from odoo import models, fields, api

class NhiemVu(models.Model):
    _name = 'nhiem_vu'
    _description = 'Quản lý Nhiệm Vụ'

    ten_nhiem_vu = fields.Char("Tên nhiệm vụ", required=True)
    mo_ta = fields.Text("Mô tả chi tiết")

    du_an_id = fields.Many2one('du_an', string="Dự án", ondelete='cascade')

    ngay_bat_dau = fields.Date("Ngày bắt đầu")
    han_chot = fields.Date("Hạn chót")

    trang_thai = fields.Selection([
        ('chua_bat_dau', 'Chưa bắt đầu'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy_bo', 'Hủy bỏ')
    ], string="Trạng thái", default="chua_bat_dau")

    muc_uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
        ('khan_cap', 'Khẩn cấp')
    ], string="Mức ưu tiên", default="trung_binh")

    so_ngay_thuc_hien = fields.Integer("Số ngày thực hiện", compute="_compute_so_ngay_thuc_hien", store=True)

    @api.depends("ngay_bat_dau", "han_chot")
    def _compute_so_ngay_thuc_hien(self):
        for record in self:
            if record.ngay_bat_dau and record.han_chot:
                delta = record.han_chot - record.ngay_bat_dau
                record.so_ngay_thuc_hien = delta.days
            else:
                record.so_ngay_thuc_hien = 0
    
    nguoi_thuc_hien_id = fields.Many2many(
        'nhan_vien',  
        'nhiem_vu_nhan_vien_rel',  
        'nhiem_vu_id',  
        'nhan_vien_id',  
        string="Người thực hiện"
    )

    nguoi_phu_trach_id = fields.Many2many(
        'nhan_vien',  
        'nhiem_vu_phu_trach_rel',  
        'nhiem_vu_id',  
        'nhan_vien_id',  
        string="Người phụ trách",  
        compute="_compute_nguoi_phu_trach",  
        store=True
    )

    so_luong_nguoi_thuc_hien = fields.Integer("Số người thực hiện", compute="_compute_so_luong", store=True)
    so_luong_nguoi_phu_trach = fields.Integer("Số người phụ trách", compute="_compute_so_luong", store=True)

    @api.depends("nguoi_thuc_hien_id", "nguoi_phu_trach_id")
    def _compute_so_luong(self):
        for record in self:
            record.so_luong_nguoi_thuc_hien = len(record.nguoi_thuc_hien_id)
            record.so_luong_nguoi_phu_trach = len(record.nguoi_phu_trach_id)

    @api.depends("du_an_id")
    def _compute_nguoi_phu_trach(self):
        for record in self:
            if record.du_an_id:
                record.nguoi_phu_trach_id = [(6, 0, record.du_an_id.nhan_vien_ids.ids)]
            else:
                record.nguoi_phu_trach_id = [(5, 0, 0)]
                
    
                
    def name_get(self):
            result = []
            for record in self:
                name = f"{record.ten_nhiem_vu} "
                result.append((record.id, name))
            return result