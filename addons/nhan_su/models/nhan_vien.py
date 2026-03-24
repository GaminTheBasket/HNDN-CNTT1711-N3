from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError

class KyNang(models.Model):
    _name = 'ky_nang'
    _description = 'Danh mục Kỹ năng'
    name = fields.Char(string="Tên kỹ năng", required=True)
    color = fields.Integer(string="Màu sắc")

class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_va_ten'
    _order = 'ten asc, tuoi desc'

    # --- CẦU NỐI VỚI TÀI KHOẢN ---
    user_id = fields.Many2one('res.users', string="Tài khoản liên kết", ondelete='cascade')

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

    # --- THÔNG TIN CÔNG VIỆC ---
    trang_thai_lam_viec = fields.Selection([
        ('thu_viec', 'Thử việc'),
        ('chinh_thuc', 'Chính thức'),
        ('da_nghi', 'Đã nghỉ')
    ], string="Trạng thái làm việc", default='thu_viec')

    vai_tro = fields.Selection([
        ('3d_artist', '3D Artist'),
        ('2d_artist', '2D Artist'),
        ('dev', 'Game Developer'),
        ('designer', 'Game Designer'),
        ('qa', 'QA/Tester'),
        ('hr', 'HR (Nhân sự)'),
        ('manager', 'Manager (Quản lý)')
    ], string="Vai trò")

    phong_ban = fields.Selection([
        ('art', 'Art Team'),
        ('code', 'Code Team'),
        ('design', 'Design Team')
    ], string="Phòng ban")

    ky_nang_ids = fields.Many2many('ky_nang', string="Kỹ năng")
    lich_su_cong_tac_ids = fields.One2many("lich_su_cong_tac", "nhan_vien_id", string="Lịch sử công tác")
    danh_sach_chung_chi_bang_cap_ids = fields.One2many("danh_sach_chung_chi_bang_cap", "nhan_vien_id", string="Chứng chỉ bằng cấp")

    # SQL Constraint
    _sql_constraints = [('ma_dinh_danh_unique', 'unique(ma_dinh_danh)', 'Mã định danh phải là duy nhất')]

    # CHẶN QUYỀN: CHỈ ADMIN (ID=1) MỚI ĐƯỢC CHỌN HR/MANAGER
    @api.constrains('vai_tro')
    def _check_admin_roles(self):
        for record in self:
            if record.vai_tro in ['hr', 'manager'] and self.env.user.id != 1:
                raise ValidationError("Cảnh báo: Chỉ Admin tối cao mới có quyền gán vai trò HR hoặc Manager!")

    # CÁC HÀM TỰ ĐỘNG CỦA BẠN
    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for record in self:
            record.ho_va_ten = f"{record.ho_ten_dem} {record.ten}" if record.ho_ten_dem and record.ten else record.ten or ""

    @api.onchange("ten", "ho_ten_dem")
    def _default_ma_dinh_danh(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                chu_cai_dau = ''.join([tu[0][0] for tu in record.ho_ten_dem.lower().split() if tu])
                ma_goc = record.ten.lower() + chu_cai_dau
                ma_moi = ma_goc
                so_dem = 1
                while self.env['nhan_vien'].search([('ma_dinh_danh', '=', ma_moi)]):
                    ma_moi = f"{ma_goc}{so_dem}"
                    so_dem += 1
                record.ma_dinh_danh = ma_moi

    @api.depends("ngay_sinh")
    def _compute_tuoi(self):
        for record in self:
            record.tuoi = date.today().year - record.ngay_sinh.year if record.ngay_sinh else 0