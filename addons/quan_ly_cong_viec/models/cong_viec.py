from odoo import models, fields, api
from datetime import date


class CongViec(models.Model):
    _name = 'cong_viec'
    _description = 'Quản lý Công Việc'

    ten_cong_viec = fields.Char("Tên công việc", required=True)
    du_an_id = fields.Many2one(
        'du_an',
        string="Dự án",
        ondelete='set null',
        help="Liên kết với dự án (tự động tạo công việc khi bắt đầu dự án)."
    )
    han_hoan_thanh = fields.Date("Hạn hoàn thành", required=True)
    tien_do = fields.Float("Tiến độ %", required=True)
    ngay_bat_dau = fields.Date("Ngày bắt đầu", required=True)
    ngay_ket_thuc = fields.Date("Ngày kết thúc", required=True)
    mo_ta = fields.Text("Mô tả công việc", required=True)
    trang_thai = fields.Selection(
        [
            ('moi', 'Mới'),
            ('dang_thuc_hien', 'Đang thực hiện'),
            ('dang_cho', 'Đang chờ '),
            ('tam_hoan', 'Tạm hoãn'),
            ('hoan_thanh', 'Hoàn thành'),
            ('da_huy', 'Đã hủy'),
            ('qua_han', 'Quá hạn'),
            ('da_duyet', 'Đã duyệt'),
            ('can_sua_doi', 'Cần sửa đổi'),
            
        ],
        string= "Trạng thái", default="moi"
    )
    cong_viec_con_ids = fields.One2many ("cong_viec_con", inverse_name="cong_viec_id", string="Công việc con")
    nhan_vien_id = fields.Many2one('nhan_vien',string="Nhân viên phụ trách")
    ghi_nhan_thoi_gian_ids = fields.One2many ("ghi_nhan_thoi_gian", inverse_name="cong_viec_id", string="Ghi nhận thời gian")
    danh_gia_cong_viec_ids = fields.One2many ("danh_gia_cong_viec", inverse_name="cong_viec_id", string="Đánh giá công việc")

    def write(self, vals):
        """Tự động hóa Mức 2: Khi Công việc chuyển 'Hoàn thành' -> tự động tạo Ghi nhận thời gian + Đánh giá mẫu."""
        res = super().write(vals)
        if vals.get('trang_thai') == 'hoan_thanh':
            today = date.today()
            for record in self:
                if not record.ghi_nhan_thoi_gian_ids.filtered(lambda g: g.ngay_ghi_nhan == today):
                    self.env['ghi_nhan_thoi_gian'].create({
                        'cong_viec_id': record.id,
                        'nhan_vien_id': record.nhan_vien_id.id if record.nhan_vien_id else False,
                        'so_gio_lam_viec': 0.0,
                        'ngay_ghi_nhan': today,
                    })
                if not record.danh_gia_cong_viec_ids:
                    self.env['danh_gia_cong_viec'].create({
                        'cong_viec_id': record.id,
                        'nhan_vien_id': record.nhan_vien_id.id if record.nhan_vien_id else False,
                        'kpi': 0.0,
                        'nhan_xet': 'Tự động tạo khi hoàn thành - cập nhật sau.',
                    })
        return res
