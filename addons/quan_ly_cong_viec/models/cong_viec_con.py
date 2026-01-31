from odoo import models, fields, api


class CongViecCon(models.Model):
    _name = 'cong_viec_con'
    _description = 'Quản lý Công Việc Con'
    
    cong_viec_id = fields.Many2one("cong_viec", string="Công việc", required=True)
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách")
    ten_cong_viec_con = fields.Char("Tên công việc con", required=True)
    han_hoan_thanh = fields.Date("Hạn hoàn thành", required=True)
    tien_do = fields.Float("Tiến độ %", required=True)
    
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
    