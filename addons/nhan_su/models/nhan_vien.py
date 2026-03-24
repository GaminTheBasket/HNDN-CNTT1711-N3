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
    _description = 'Bảng nhân viên'
    _rec_name = 'ho_va_ten'

    user_id = fields.Many2one('res.users', string="Tài khoản liên kết", ondelete='cascade')
    ma_dinh_danh = fields.Char("Mã định danh", required=True)
    anh = fields.Binary("Ảnh đại diện")
    ho_ten_dem = fields.Char("Họ tên đệm", required=True)
    ten = fields.Char("Tên", required=True)
    ho_va_ten = fields.Char("Họ và tên", compute="_compute_ho_va_ten", store=True)
    ngay_sinh = fields.Date("Ngày sinh")
    tuoi = fields.Integer("Tuổi", compute="_compute_tuoi", store=True)
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    
    trang_thai_lam_viec = fields.Selection([
        ('thu_viec', 'Thử việc'), ('chinh_thuc', 'Chính thức'), ('da_nghi', 'Đã nghỉ')
    ], string="Trạng thái làm việc", default='thu_viec')

    vai_tro = fields.Selection([
        ('3d_artist', '3D Artist'), ('2d_artist', '2D Artist'),
        ('dev', 'Game Developer'), ('designer', 'Game Designer'),
        ('qa', 'QA/Tester'), ('hr', 'HR (Nhân sự)'), ('manager', 'Manager (Quản lý)')
    ], string="Vai trò", required=True)

    phong_ban = fields.Selection([
        ('art', 'Art Team'), ('code', 'Code Team'), ('design', 'Design Team')
    ], string="Phòng ban")

    ky_nang_ids = fields.Many2many('ky_nang', string="Kỹ năng")
    lich_su_cong_tac_ids = fields.One2many("lich_su_cong_tac", "nhan_vien_id")
    danh_sach_chung_chi_bang_cap_ids = fields.One2many("danh_sach_chung_chi_bang_cap", "nhan_vien_id")

    # Logic cấp quyền tự động cho Manager
    def write(self, vals):
        res = super(NhanVien, self).write(vals)
        if 'vai_tro' in vals:
            for record in self:
                if record.user_id:
                    try:
                        group_mgr = self.env.ref('nhan_su.group_nhan_su_manager')
                        if vals['vai_tro'] == 'manager':
                            record.user_id.sudo().write({'groups_id': [(4, group_mgr.id)]})
                        else:
                            record.user_id.sudo().write({'groups_id': [(3, group_mgr.id)]})
                    except: continue
        return res

    @api.constrains('vai_tro')
    def _check_admin_roles(self):
        for record in self:
            if record.vai_tro in ['hr', 'manager'] and not self.env.user.has_group('base.group_system'):
                raise ValidationError("Lỗi: Chỉ Admin tối cao mới được gán vai trò HR/Manager!")

    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for r in self: r.ho_va_ten = f"{r.ho_ten_dem} {r.ten}" if r.ho_ten_dem and r.ten else r.ten or ""

    @api.onchange("ten", "ho_ten_dem")
    def _default_ma_dinh_danh(self):
        for r in self:
            if r.ho_ten_dem and r.ten:
                chu_cai_dau = ''.join([tu[0][0] for tu in r.ho_ten_dem.lower().split() if tu])
                r.ma_dinh_danh = r.ten.lower() + chu_cai_dau

    @api.depends("ngay_sinh")
    def _compute_tuoi(self):
        for r in self: r.tuoi = date.today().year - r.ngay_sinh.year if r.ngay_sinh else 0