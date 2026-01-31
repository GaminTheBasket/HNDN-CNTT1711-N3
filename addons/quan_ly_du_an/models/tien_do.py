from odoo import models, fields, api
from datetime import datetime

class TienDo(models.Model):
    _name = "tien_do"
    _description = "Tiến Độ Công Việc"

    du_an_id = fields.Many2one('du_an', string="Dự Án", ondelete='cascade', required=True)
    nhiem_vu_id = fields.Many2one('nhiem_vu', string="Nhiệm Vụ", ondelete='cascade', required=True)
    phan_tram_hoan_thanh = fields.Float(string="Phần Trăm Hoàn Thành", compute="_compute_phan_tram_hoan_thanh", store=True)
    trang_thai_du_an = fields.Selection([
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('hoan_thanh', 'Hoàn thành'),
        ('tam_dung', 'Tạm dừng'),
        ('huy_bo', 'Hủy bỏ')
    ], string="Trạng Thái Dự Án", compute="_compute_trang_thai_du_an", store=True)
    ghi_chu = fields.Text(string="Ghi Chú")
    ngay_cap_nhat = fields.Datetime(string="Ngày Cập Nhật", default=fields.Datetime.now)
    nguoi_cap_nhat_id = fields.Many2one('res.users', string="Người Cập Nhật", ondelete='set null', default=lambda self: self.env.user)

    @api.depends('du_an_id.tien_do_du_an')
    def _compute_phan_tram_hoan_thanh(self):
        for record in self:
            record.phan_tram_hoan_thanh = round(record.du_an_id.tien_do_du_an, 2) if record.du_an_id else 0.0

    @api.depends('du_an_id.trang_thai')
    def _compute_trang_thai_du_an(self):
        for record in self:
            record.trang_thai_du_an = record.du_an_id.trang_thai if record.du_an_id else 'dang_thuc_hien'
