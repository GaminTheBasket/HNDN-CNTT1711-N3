from odoo import models, fields, api

class ThoiGianLamViec(models.Model):
    _name = "thoi_gian_lam_viec"
    _description = "Thời Gian Làm Việc"

    nhiem_vu_id = fields.Many2one('nhiem_vu', string="Nhiệm Vụ", ondelete='cascade', required=True)
    nhan_vien_id = fields.Many2many('nhan_vien', string="Nhân Viên", compute="_compute_nhan_vien_id", store=False)
    so_gio = fields.Float(string="Số Giờ", required=True)
    ngay_lam_viec = fields.Datetime(string="Ngày Làm Việc", default=fields.Datetime.now)

    so_luong_nhan_vien = fields.Integer(string="Số Lượng Nhân Viên", compute="_compute_so_luong_nhan_vien", store=True)

    @api.depends('nhiem_vu_id')
    def _compute_nhan_vien_id(self):
        for record in self:
            if record.nhiem_vu_id:
                record.nhan_vien_id = record.nhiem_vu_id.nguoi_thuc_hien_id
            else:
                record.nhan_vien_id = []

    @api.depends('nhan_vien_id')
    def _compute_so_luong_nhan_vien(self):
        for record in self:
            record.so_luong_nhan_vien = len(record.nhan_vien_id)
