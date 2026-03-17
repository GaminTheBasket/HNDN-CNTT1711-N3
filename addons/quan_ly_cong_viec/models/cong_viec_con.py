from odoo import models, fields, api

class CongViecCon(models.Model):
    _name = 'cong_viec_con'
    _description = 'Quản lý Công Việc Con'
    
    # Đã thêm ondelete='cascade': Xóa task Cha thì task Con tự động bốc hơi theo
    cong_viec_id = fields.Many2one("cong_viec", string="Công việc", required=True, ondelete='cascade')
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách")
    ten_cong_viec_con = fields.Char("Tên công việc con", required=True)
    han_hoan_thanh = fields.Date("Hạn hoàn thành", required=True)
    
    # ĐÃ SỬA: Bỏ required=True để Sếp tạo task con nhanh gọn lẹ trên giao diện
    mo_ta = fields.Text("Mô tả công việc")
    
    # ĐÃ SỬA: Rút gọn trạng thái, bỏ bớt các trạng thái rườm rà không cần thiết cho task con
    trang_thai = fields.Selection([
        ('moi', 'Mới'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('dang_cho', 'Đang chờ'),
        ('hoan_thanh', 'Hoàn thành'),
        ('da_huy', 'Đã hủy')
    ], string="Trạng thái", default="moi")