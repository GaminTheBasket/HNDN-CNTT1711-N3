from odoo import models, fields, api
import json

class DuAn(models.Model):
    _name = 'du_an'
    _description = 'Quản lý dự án'

    ten_du_an = fields.Char("Tên dự án", required=True)
    ngan_sach = fields.Float("Ngân sách dự án", required=True)
    ngay_bat_dau = fields.Date("Ngày bắt đầu", required=True)
    ngay_ket_thuc = fields.Date("Ngày kết thúc", required=True)
    mo_ta = fields.Text("Mô tả chi tiết dự án")

    nhiem_vu_ids = fields.One2many("nhiem_vu", "du_an_id", string="Nhiệm vụ dự án")
    tien_do_ids = fields.One2many("tien_do", "du_an_id", string="Tiến Độ Dự Án")

    trang_thai = fields.Selection([
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('hoan_thanh', 'Hoàn thành'),
        ('tam_dung', 'Tạm dừng'),
        ('huy_bo', 'Hủy bỏ')
    ], string="Trạng thái", default="dang_thuc_hien", compute="_compute_trang_thai", store=True)

    @api.depends("nhiem_vu_ids.trang_thai")
    def _compute_trang_thai(self):
        for record in self:
            if not record.nhiem_vu_ids:
                continue

            trang_thai_nhiem_vu = record.nhiem_vu_ids.mapped("trang_thai")

            if all(trang_thai == "hoan_thanh" for trang_thai in trang_thai_nhiem_vu):
                record.trang_thai = "hoan_thanh"
            elif any(trang_thai == "dang_thuc_hien" for trang_thai in trang_thai_nhiem_vu):
                record.trang_thai = "dang_thuc_hien"
            elif all(trang_thai == "huy_bo" for trang_thai in trang_thai_nhiem_vu):
                record.trang_thai = "huy_bo"
            else:
                record.trang_thai = "dang_thuc_hien"

    muc_uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
        ('khan_cap', 'Khẩn cấp')
    ], string="Mức ưu tiên", default="thap")

    nhan_vien_ids = fields.Many2many(
        'nhan_vien',
        'du_an_nhan_vien_rel',
        'du_an_id',
        'nhan_vien_id',
        string="Nhân viên thực hiện"
    )

    so_luong_nhan_vien = fields.Integer(
        "Số người phụ trách", compute="_tinh_so_luong_nhan_vien", store=True
    )

    @api.depends("nhan_vien_ids")
    def _tinh_so_luong_nhan_vien(self):
        for record in self:
            record.so_luong_nhan_vien = len(record.nhan_vien_ids)

    so_luong_nhiem_vu = fields.Integer(
        "Số nhiệm vụ", compute="_compute_so_luong_nhiem_vu", store=True
    )

    @api.depends("nhiem_vu_ids")
    def _compute_so_luong_nhiem_vu(self):
        for record in self:
            record.so_luong_nhiem_vu = len(record.nhiem_vu_ids)

    @api.model_create_multi
    def create(self, vals_list):
        """Tự động hóa Mức 2: Khi tạo Dự án -> tự động tạo Công việc 'Khởi tạo dự án' (event-driven)."""
        records = super().create(vals_list)
        if 'cong_viec' not in self.env:
            return records
        CongViec = self.env['cong_viec']
        for record in records:
            CongViec.create({
                'ten_cong_viec': 'Khởi tạo dự án: %s' % record.ten_du_an,
                'du_an_id': record.id,
                'han_hoan_thanh': record.ngay_ket_thuc,
                'ngay_bat_dau': record.ngay_bat_dau,
                'ngay_ket_thuc': record.ngay_ket_thuc,
                'tien_do': 0.0,
                'mo_ta': 'Công việc tự động tạo khi bắt đầu dự án. Cập nhật tiến độ và mô tả khi cần.',
                'trang_thai': 'moi',
                'nhan_vien_id': record.nhan_vien_ids[0].id if record.nhan_vien_ids else False,
            })
        return records

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.ten_du_an} "
            result.append((record.id, name))
        return result

    tien_do_du_an = fields.Float(string="Tiến Độ Dự Án (%)", compute="_compute_tien_do_du_an", store=True)

    @api.depends('nhiem_vu_ids.trang_thai')
    def _compute_tien_do_du_an(self):
        for record in self:
            nhiem_vu_count = len(record.nhiem_vu_ids)
            if nhiem_vu_count > 0:
                hoan_thanh_count = sum(1 for nv in record.nhiem_vu_ids if nv.trang_thai == 'hoan_thanh')
                record.tien_do_du_an = (hoan_thanh_count / nhiem_vu_count) * 100
            else:
                record.tien_do_du_an = 0.0

    @api.model
    def get_trang_thai_du_an_data(self):
        data = self.read_group([], ['trang_thai'], ['trang_thai'])
        return json.dumps(data)
    
    @api.model
    def get_muc_uu_tien_data(self):
        data = self.read_group([], ['muc_uu_tien'], ['muc_uu_tien'])
        return json.dumps(data)