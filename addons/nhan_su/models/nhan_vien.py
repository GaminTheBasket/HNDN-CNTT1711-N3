from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError

class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_va_ten'
    _order = 'ten asc, tuoi desc'

    # --- THÔNG TIN ĐỊNH DANH ---
    ma_dinh_danh = fields.Char("Mã định danh", required=True)
    anh = fields.Binary("Ảnh đại diện")
    ho_ten_dem = fields.Char("Họ tên đệm", required=True)
    ten = fields.Char("Tên", required=True)
    ho_va_ten = fields.Char("Họ và tên", compute="_compute_ho_va_ten", store=True)

    # --- THÔNG TIN CÁ NHÂN ---
    ngay_sinh = fields.Date("Ngày sinh")
    tuoi = fields.Integer("Tuổi", compute="_compute_tuoi", store=True)
    que_quan = fields.Char("Quê quán")
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")

    # --- THÔNG TIN CÔNG VIÊC (Cho Studio Game) ---
    trang_thai_lam_viec = fields.Selection([
        ('thu_viec', 'Thử việc'),
        ('chinh_thuc', 'Chính thức'),
        ('nghi_phep', 'Nghỉ phép'),
        ('nghi_viec', 'Nghỉ việc')
    ], string="Trạng thái làm việc", default='thu_viec')

    vai_tro = fields.Selection([
        ('3d_artist', '3D Artist'),
        ('2d_artist', '2D Artist'),
        ('dev', 'Game Developer'),
        ('designer', 'Game Designer'),
        ('qa', 'QA/Tester')
    ], string="Vai trò")

    phong_ban = fields.Selection([
        ('art', 'Art Team'),
        ('code', 'Code Team'),
        ('design', 'Design Team')
    ], string="Phòng ban")

    ky_nang = fields.Char(string="Kỹ năng (VD: Unity, Blender...)")

    # --- LIÊN KẾT MODULE KHÁC ---
    lich_su_cong_tac_ids = fields.One2many(
        "lich_su_cong_tac", 
        inverse_name="nhan_vien_id", 
        string="Danh sách lịch sử công tác"
    )
    danh_sach_chung_chi_bang_cap_ids = fields.One2many(
        "danh_sach_chung_chi_bang_cap", 
        inverse_name="nhan_vien_id", 
        string="Danh sách chứng chỉ bằng cấp"
    )

    # LƯU Ý: Tạm ẩn 2 trường này để tránh lỗi 500 khi chưa cài module khác
    # cong_viec_ids = fields.One2many("quan.ly.cong.viec", "nhan_vien_id", string="Công việc đang làm")
    # tai_san_ids = fields.One2many("quan.ly.tai.san", "nhan_vien_id", string="Tài sản đang giữ")

    _sql_constraints = [
        ('ma_dinh_danh_unique', 'unique(ma_dinh_danh)', 'Mã định danh phải là duy nhất')
    ]

    # --- CÁC HÀM XỬ LÝ (TỰ ĐỘNG) ---
    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                record.ho_va_ten = f"{record.ho_ten_dem} {record.ten}"
            else:
                record.ho_va_ten = ""
                
    @api.onchange("ten", "ho_ten_dem")
    def _default_ma_dinh_danh(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                # 1. Tạo mã gốc
                chu_cai_dau = ''.join([tu[0][0] for tu in record.ho_ten_dem.lower().split() if tu])
                ma_goc = record.ten.lower() + chu_cai_dau
                
                # 2. Thuật toán dò trùng và nhảy số (Ví dụ: testh -> testh1 -> testh2)
                ma_moi = ma_goc
                so_dem = 1
                
                while self.env['nhan_vien'].search([('ma_dinh_danh', '=', ma_moi)]):
                    ma_moi = f"{ma_goc}{so_dem}"
                    so_dem += 1
                
                # 3. Gán mã không trùng
                record.ma_dinh_danh = ma_moi

    @api.depends("ngay_sinh")
    def _compute_tuoi(self):
        for record in self:
            if record.ngay_sinh:
                year_now = date.today().year
                record.tuoi = year_now - record.ngay_sinh.year
            else:
                record.tuoi = 0

    @api.constrains('tuoi')
    def _check_tuoi(self):
        for record in self:
            if record.tuoi and record.tuoi < 18:
                raise ValidationError("Tuổi không được bé hơn 18")