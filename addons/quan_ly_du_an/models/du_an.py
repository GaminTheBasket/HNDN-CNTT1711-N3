from odoo import models, fields, api
import json

class DuAn(models.Model):
    _name = 'du_an'
    _description = 'Quản lý dự án Game Studio'

    # --- THÔNG TIN CHUNG ---
    ten_du_an = fields.Char("Tên dự án", required=True)
    ngan_sach = fields.Float("Ngân sách dự án", required=True)
    ngay_bat_dau = fields.Date("Ngày bắt đầu", required=True)
    ngay_ket_thuc = fields.Date("Ngày kết thúc", required=True)
    mo_ta = fields.Text("Mô tả chi tiết dự án")

    giai_doan_game = fields.Selection([
        ('concept', 'Lên ý tưởng (Concept)'),
        ('pre_production', 'Tiền kỳ (Pre-production)'),
        ('alpha', 'Alpha Test'),
        ('beta', 'Beta Test'),
        ('early_access', 'Early Access'),
        ('release', 'Phát hành (Release)')
    ], string="Giai đoạn phát triển", default='concept')

    # ĐÃ FIX: Trả về nhiem_vu_ids như bản gốc để không bị lỗi Registry
    nhiem_vu_ids = fields.One2many("nhiem_vu", "du_an_id", string="Nhiệm vụ dự án")
    tien_do_ids = fields.One2many("tien_do", "du_an_id", string="Tiến Độ Dự Án")
    nhan_vien_ids = fields.Many2many('nhan_vien', 'du_an_nhan_vien_rel', 'du_an_id', 'nhan_vien_id', string="Nhân sự tham gia")

    muc_uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
        ('khan_cap', 'Khẩn cấp')
    ], string="Mức ưu tiên", default="thap")

    trang_thai = fields.Selection([
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('hoan_thanh', 'Hoàn thành'),
        ('tam_dung', 'Tạm dừng'),
        ('huy_bo', 'Hủy bỏ')
    ], string="Trạng thái", default="dang_thuc_hien", compute="_compute_trang_thai", store=True)

    so_luong_nhan_vien = fields.Integer("Số người phụ trách", compute="_tinh_so_luong_nhan_vien", store=True)
    tien_do_du_an = fields.Float(string="Tiến Độ Dự Án (%)", compute="_compute_thong_ke_task", store=True)

    # --- CÁC BIẾN CHO NÚT THỐNG KÊ (SMART BUTTONS) ---
    tong_so_nhiem_vu = fields.Integer(string="Tổng số Task", compute="_compute_thong_ke_task")
    tong_nhiem_vu_hoan_thanh = fields.Integer(string="Task Hoàn thành", compute="_compute_thong_ke_task")

    # ==========================================
    # CÁC HÀM XỬ LÝ LOGIC
    # ==========================================
    @api.depends("nhiem_vu_ids.trang_thai")
    def _compute_trang_thai(self):
        """Dự án tự động nhảy trạng thái dựa trên các Task con"""
        for record in self:
            if not record.nhiem_vu_ids:
                record.trang_thai = "dang_thuc_hien"
                continue
            trang_thai_tasks = record.nhiem_vu_ids.mapped("trang_thai")
            if all(tt == "hoan_thanh" for tt in trang_thai_tasks):
                record.trang_thai = "hoan_thanh"
            elif any(tt == "dang_thuc_hien" for tt in trang_thai_tasks):
                record.trang_thai = "dang_thuc_hien"
            elif all(tt == "huy_bo" for tt in trang_thai_tasks):
                record.trang_thai = "huy_bo"
            else:
                record.trang_thai = "dang_thuc_hien"

    @api.depends("nhan_vien_ids")
    def _tinh_so_luong_nhan_vien(self):
        for record in self:
            record.so_luong_nhan_vien = len(record.nhan_vien_ids)

    @api.depends('nhiem_vu_ids', 'nhiem_vu_ids.trang_thai')
    def _compute_thong_ke_task(self):
        """Hàm gộp: Vừa đếm số cho Smart Button, vừa tính % cho Progressbar"""
        for record in self:
            so_luong = len(record.nhiem_vu_ids)
            hoan_thanh = len(record.nhiem_vu_ids.filtered(lambda c: c.trang_thai == 'hoan_thanh'))
            
            record.tong_so_nhiem_vu = so_luong
            record.tong_nhiem_vu_hoan_thanh = hoan_thanh
            
            if so_luong > 0:
                record.tien_do_du_an = (hoan_thanh / so_luong) * 100
            else:
                record.tien_do_du_an = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        """Tự động tạo Task 'Khởi tạo dự án' (Mức 2) mà không gây lỗi Registry"""
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

    @api.model
    def get_trang_thai_du_an_data(self):
        data = self.read_group([], ['trang_thai'], ['trang_thai'])
        return json.dumps(data)
    
    @api.model
    def get_muc_uu_tien_data(self):
        data = self.read_group([], ['muc_uu_tien'], ['muc_uu_tien'])
        return json.dumps(data)

    def action_mo_danh_sach_nhiem_vu(self):
        self.ensure_one()
        return {
            'name': f'Danh sách Nhiệm vụ ({self.ten_du_an})',
            'type': 'ir.actions.act_window',
            'res_model': 'nhiem_vu',
            'view_mode': 'tree,form',
            'domain': [('du_an_id', '=', self.id)],
            'context': {'default_du_an_id': self.id},
        }