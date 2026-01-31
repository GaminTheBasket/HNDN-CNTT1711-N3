from odoo import models, fields, api

class TreHan(models.Model):
    _name = "tre_han"
    _description = "Danh sách nhiệm vụ/dự án trễ hạn"

    nhiem_vu_id = fields.Many2one("nhiem_vu", string="Nhiệm vụ", ondelete="cascade")
    du_an_id = fields.Many2one("du_an", string="Dự án", compute="_compute_du_an_id", store=True)

    han_chot = fields.Date(string="Hạn chót", compute="_compute_han_chot", store=True)
    ngay_hien_tai = fields.Date(string="Ngày hiện tại", default=fields.Date.today)

    so_ngay_tre = fields.Integer(string="Số ngày trễ", compute="_compute_so_ngay_tre", store=True)
    canh_bao = fields.Boolean(string="Cảnh báo", compute="_compute_canh_bao", store=True)

    @api.depends("nhiem_vu_id")
    def _compute_han_chot(self):
        """ Lấy hạn chót từ nhiệm vụ """
        for record in self:
            record.han_chot = record.nhiem_vu_id.han_chot if record.nhiem_vu_id else False

    @api.depends("nhiem_vu_id")
    def _compute_du_an_id(self):
        """ Lấy dự án từ nhiệm vụ """
        for record in self:
            record.du_an_id = record.nhiem_vu_id.du_an_id if record.nhiem_vu_id else False

    @api.depends("han_chot", "ngay_hien_tai")
    def _compute_so_ngay_tre(self):
        """ Tính số ngày trễ """
        for record in self:
            if record.han_chot:
                record.so_ngay_tre = (record.ngay_hien_tai - record.han_chot).days
            else:
                record.so_ngay_tre = 0

    @api.depends("so_ngay_tre")
    def _compute_canh_bao(self):
        """ Đánh dấu cảnh báo nếu trễ hạn """
        for record in self:
            record.canh_bao = record.so_ngay_tre > 0

    