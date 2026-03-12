from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, datetime
import requests
import json

class CongViec(models.Model):
    _name = 'cong_viec'
    _description = 'Quản lý Công Việc'
    _rec_name = 'ten_cong_viec'

    ten_cong_viec = fields.Char("Tên công việc", required=True)
    du_an_id = fields.Many2one('du_an', string="Dự án", ondelete='set null')
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách")

    loai_task = fields.Selection([
        ('code', 'Code / Lập trình'),
        ('art', 'Art / Thiết kế 2D-3D'),
        ('bug', 'Fix Bug / Sửa lỗi'),
        ('khac', 'Khác')
    ], string="Loại công việc", default='code')

    trang_thai = fields.Selection([
        ('moi', 'Mới'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('dang_cho', 'Đang chờ'),
        ('tam_hoan', 'Tạm hoãn'),
        ('hoan_thanh', 'Hoàn thành'),
        ('da_huy', 'Đã hủy'),
        ('qua_han', 'Quá hạn'),
        ('da_duyet', 'Đã duyệt'),
        ('can_sua_doi', 'Cần sửa đổi'),
    ], string="Trạng thái", default="moi")

    ngay_bat_dau = fields.Date("Ngày bắt đầu", required=True)
    han_hoan_thanh = fields.Date("Hạn hoàn thành", required=True)
    
    # ĐÃ CẬP NHẬT: Bỏ required=True để việc tạo task dễ thở hơn
    ngay_ket_thuc = fields.Date("Ngày kết thúc")

    # Giữ nguyên kiểu nhập tay linh hoạt của bạn, không dùng compute cứng nhắc
    tien_do = fields.Float("Tiến độ %", default=0.0)

    mo_ta = fields.Text("Mô tả công việc (Dán yêu cầu dài vào đây)")
    tom_tat_ai = fields.Text("Tóm tắt từ AI (Gemini)")

    # --- CÁC BIẾN CHO ĐỒNG HỒ NGẦM (CHỐNG GIAN LẬN) ---
    thoi_gian_bat_dau_chay = fields.Datetime("Bắt đầu đếm giờ lúc", readonly=True, copy=False)
    tong_thoi_gian_luy_ke = fields.Float("Tổng giờ làm (Hệ thống tính)", default=0.0, readonly=True, copy=False)

    cong_viec_con_ids = fields.One2many("cong_viec_con", inverse_name="cong_viec_id", string="Công việc con")
    ghi_nhan_thoi_gian_ids = fields.One2many("ghi_nhan_thoi_gian", inverse_name="cong_viec_id", string="Ghi nhận thời gian")
    danh_gia_cong_viec_ids = fields.One2many("danh_gia_cong_viec", inverse_name="cong_viec_id", string="Đánh giá công việc")

    # =========================================================
    # TÍNH NĂNG MỚI: LỌC NHÂN VIÊN THEO DỰ ÁN (DYNAMIC DOMAIN)
    # =========================================================
    @api.onchange('du_an_id')
    def _loc_nhan_vien_theo_du_an(self):
        if self.du_an_id:
            # Xóa nhân viên nếu họ không thuộc dự án mới chọn
            if self.nhan_vien_id and self.nhan_vien_id not in self.du_an_id.nhan_vien_ids:
                self.nhan_vien_id = False
            
            # Chỉ hiển thị nhân viên thuộc dự án này
            return {'domain': {'nhan_vien_id': [('id', 'in', self.du_an_id.nhan_vien_ids.ids)]}}
        else:
            return {'domain': {'nhan_vien_id': []}}

    # =================================================================
    # MỨC 3: TÍCH HỢP AI GEMINI TÓM TẮT YÊU CẦU CÔNG VIỆC
    # =================================================================
    def action_tom_tat_ai(self):
        for record in self:
            if not record.mo_ta:
                raise ValidationError("Bạn phải nhập 'Mô tả công việc' thì AI mới có cái để đọc và tóm tắt chứ!")
            
            api_key = 'AIzaSyB_xzZ3EkaMuOt9g99N14yQsE2XqNKbQ0s' 
            url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
            headers = {'Content-Type': 'application/json'}
            
            prompt = f"Bạn là một trợ lý quản lý dự án xuất sắc. Hãy đọc kỹ đoạn mô tả công việc sau và tóm tắt nó lại thành các gạch đầu dòng ngắn gọn, súc tích, dễ hiểu nhất cho lập trình viên:\n\n{record.mo_ta}"
            data = {"contents": [{"parts": [{"text": prompt}]}]}
            
            try:
                response = requests.post(url, headers=headers, json=data)
                if response.status_code != 200:
                    chi_tiet_loi = response.json()
                    loi_hien_thi = json.dumps(chi_tiet_loi, indent=2, ensure_ascii=False)
                    raise ValidationError(f"Google AI từ chối phục vụ! Chi tiết:\n{loi_hien_thi}")

                result = response.json()
                text_ai = result['candidates'][0]['content']['parts'][0]['text']
                record.tom_tat_ai = text_ai
                
            except requests.exceptions.RequestException as e:
                raise ValidationError(f"Lỗi mạng khi gọi điện cho Google: {str(e)}")
            except Exception as e:
                if isinstance(e, ValidationError):
                    raise e
                raise ValidationError(f"Lỗi khi xử lý dữ liệu AI: {str(e)}")

    # =================================================================
    # MỨC 2: CẢNH BÁO TRÙNG LỊCH THÔNG MINH (GIỮ NGUYÊN BẢN GỐC XỊN)
    # =================================================================
    @api.onchange('nhan_vien_id', 'ngay_bat_dau', 'ngay_ket_thuc')
    def _check_trung_lich_nhan_vien(self):
        if self.nhan_vien_id and self.ngay_bat_dau and self.ngay_ket_thuc:
            domain = [
                ('nhan_vien_id', '=', self.nhan_vien_id.id),
                ('id', '!=', self._origin.id if self._origin else False),
                ('trang_thai', 'not in', ['hoan_thanh', 'da_huy', 'tam_hoan']),
                ('ngay_bat_dau', '<=', self.ngay_ket_thuc),
                ('ngay_ket_thuc', '>=', self.ngay_bat_dau)
            ]
            cac_task_trung = self.env['cong_viec'].search(domain)
            
            if cac_task_trung:
                danh_sach_ten_task = "\n- ".join(cac_task_trung.mapped('ten_cong_viec'))
                return {
                    'warning': {
                        'title': '⚠️ LƯU Ý: Nhân sự đang bận rộn!',
                        'message': f'Nhân viên {self.nhan_vien_id.ho_va_ten} đang có các task khác trong khoảng thời gian này:\n{danh_sach_ten_task}\n\nBạn có chắc chắn muốn ép thêm việc không?'
                    }
                }

    # =================================================================
    # MỨC 2: TỰ ĐỘNG HÓA CHẠY ĐỒNG HỒ NGẦM & TẠO ĐÁNH GIÁ
    # =================================================================
    def write(self, vals):
        # 1. Logic Đồng hồ ngầm khi đổi trạng thái làm việc
        if 'trang_thai' in vals:
            trang_thai_moi = vals['trang_thai']
            for record in self:
                trang_thai_cu = record.trang_thai
                
                if trang_thai_moi == 'dang_thuc_hien' and trang_thai_cu != 'dang_thuc_hien':
                    vals['thoi_gian_bat_dau_chay'] = fields.Datetime.now()
                
                elif trang_thai_cu == 'dang_thuc_hien' and trang_thai_moi != 'dang_thuc_hien':
                    if record.thoi_gian_bat_dau_chay:
                        thoi_gian_dung = fields.Datetime.now()
                        so_giay_da_lam = (thoi_gian_dung - record.thoi_gian_bat_dau_chay).total_seconds()
                        so_gio = so_giay_da_lam / 3600.0
                        vals['tong_thoi_gian_luy_ke'] = record.tong_thoi_gian_luy_ke + so_gio
                        vals['thoi_gian_bat_dau_chay'] = False

        res = super().write(vals)

        # 2. Logic tự động chốt timesheet và đánh giá khi "Hoàn thành"
        if vals.get('trang_thai') == 'hoan_thanh':
            today = date.today()
            for record in self:
                gio_thuc_te = record.tong_thoi_gian_luy_ke
                if not record.ghi_nhan_thoi_gian_ids.filtered(lambda g: g.ngay_ghi_nhan == today):
                    self.env['ghi_nhan_thoi_gian'].create({
                        'cong_viec_id': record.id,
                        'nhan_vien_id': record.nhan_vien_id.id if record.nhan_vien_id else False,
                        'so_gio_lam_viec': gio_thuc_te,
                        'ngay_ghi_nhan': today,
                    })
                if not record.danh_gia_cong_viec_ids:
                    self.env['danh_gia_cong_viec'].create({
                        'cong_viec_id': record.id,
                        'nhan_vien_id': record.nhan_vien_id.id if record.nhan_vien_id else False,
                        'kpi': 0.0,
                        'nhan_xet': f'Hệ thống tự động chốt: Task hoàn thành trong {round(gio_thuc_te, 2)} giờ.',
                    })
        return res