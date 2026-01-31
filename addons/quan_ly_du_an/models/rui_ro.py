from odoo import models, fields, api

class RuiRo(models.Model):
    _name = "rui_ro"
    _description = "Quản lý Rủi Ro Dự Án"

    ten_rui_ro = fields.Char(string="Tên Rủi Ro", required=True)
    mo_ta = fields.Text(string="Mô Tả Chi Tiết")
    du_an_id = fields.Many2one("du_an", string="Dự Án", required=True, ondelete="cascade")
    muc_do_anh_huong = fields.Selection([
        ("Thấp", "Thấp"),
        ("Trung bình", "Trung Bình"),
        ("Cao", "Cao"),
        ("Nghiêm trọng", "Nghiêm Trọng")
    ], string="Mức Độ Ảnh Hưởng", required=True, default="Thấp")

    khac_phuc = fields.Text(string="Giải Pháp Khắc Phục")

    trang_thai = fields.Selection([
        ("Mới", "Mới"),
        ("Đang xử lý", "Đang Xử Lý"),
        ("Đã giải quyết", "Đã Giải Quyết")
    ], string="Trạng Thái", required=True, default="Mới")

    nguoi_chiu_trach_nhiem_ids = fields.Many2many(
        "nhan_vien",  
        "rui_ro_nhan_vien_rel",
        "rui_ro_id",
        "nhan_vien_id",
        string="Người Chịu Trách Nhiệm"
    )

    so_luong_nguoi_chiu_trach_nhiem = fields.Integer(
        string="Số Lượng Người Chịu Trách Nhiệm",
        compute="_compute_so_luong_nguoi_chiu_trach_nhiem",
        store=True
    )

    @api.depends("nguoi_chiu_trach_nhiem_ids")
    def _compute_so_luong_nguoi_chiu_trach_nhiem(self):
        for record in self:
            record.so_luong_nguoi_chiu_trach_nhiem = len(record.nguoi_chiu_trach_nhiem_ids)
            
    @api.onchange("du_an_id")
    def _onchange_du_an_id(self):
        """ Tự động lấy tất cả nhân viên của dự án làm người chịu trách nhiệm rủi ro """
        if self.du_an_id:
            self.nguoi_chiu_trach_nhiem_ids = [(6, 0, self.du_an_id.nhan_vien_ids.ids)]  
        else:
            self.nguoi_chiu_trach_nhiem_ids = [(5, 0, 0)] 
