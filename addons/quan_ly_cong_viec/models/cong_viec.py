from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date
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
        ('hoan_thanh', 'Hoàn thành'),
        ('da_huy', 'Đã hủy')
    ], string="Trạng thái", default="moi")

    ngay_bat_dau = fields.Date("Ngày bắt đầu", required=True)
    han_hoan_thanh = fields.Date("Hạn hoàn thành", required=True)
    ngay_ket_thuc = fields.Date("Ngày kết thúc") 

    tien_do = fields.Float("Tiến độ %", compute="_compute_tien_do", store=True)
    canh_bao_han = fields.Char("Tình trạng Deadline", compute="_compute_canh_bao_han")

    mo_ta = fields.Text("Mô tả công việc")
    tom_tat_ai = fields.Text("Tóm tắt từ AI (Gemini)")

    # Liên kết với bảng Công việc con
    cong_viec_con_ids = fields.One2many("cong_viec_con", inverse_name="cong_viec_id", string="Công việc con")
    
    ghi_nhan_thoi_gian_ids = fields.One2many("ghi_nhan_thoi_gian", inverse_name="cong_viec_id", string="Ghi nhận thời gian")
    danh_gia_cong_viec_ids = fields.One2many("danh_gia_cong_viec", inverse_name="cong_viec_id", string="Đánh giá công việc")

    # =========================================================
    # LỌC NHÂN VIÊN THEO DỰ ÁN
    # =========================================================
    @api.onchange('du_an_id')
    def _loc_nhan_vien_theo_du_an(self):
        if self.du_an_id:
            if self.nhan_vien_id and self.nhan_vien_id not in self.du_an_id.nhan_vien_ids:
                self.nhan_vien_id = False
            return {'domain': {'nhan_vien_id': [('id', 'in', self.du_an_id.nhan_vien_ids.ids)]}}
        else:
            return {'domain': {'nhan_vien_id': []}}

    # =========================================================
    # TÍNH % TIẾN ĐỘ & TỰ ĐỘNG CHUYỂN TRẠNG THÁI TASK CHA
    # =========================================================
    @api.depends('cong_viec_con_ids.trang_thai', 'trang_thai')
    def _compute_tien_do(self):
        for record in self:
            tong_so_viec_con = len(record.cong_viec_con_ids)
            
            if tong_so_viec_con > 0:
                viec_da_xong = len(record.cong_viec_con_ids.filtered(lambda x: x.trang_thai == 'hoan_thanh'))
                record.tien_do = (viec_da_xong / tong_so_viec_con) * 100.0
                
                # --- LOGIC LIÊN KẾT TRẠNG THÁI CHA & CON TỰ ĐỘNG ---
                
                # 1. Nếu việc con xong 100% -> Cha tự động Hoàn thành
                if record.tien_do == 100.0 and record.trang_thai != 'hoan_thanh':
                    record.trang_thai = 'hoan_thanh'
                    
                # 2. Nếu có task con Đang làm HOẶC tiến độ > 0% -> Cha tự động sang Đang thực hiện
                elif (record.tien_do > 0 or any(c.trang_thai == 'dang_thuc_hien' for c in record.cong_viec_con_ids)):
                    if record.trang_thai == 'moi':
                        record.trang_thai = 'dang_thuc_hien'
            else:
                if record.trang_thai == 'hoan_thanh':
                    record.tien_do = 100.0
                else:
                    record.tien_do = 0.0

    # =========================================================
    # CẢNH BÁO QUÁ HẠN DEADLINE ĐẾM NGƯỢC
    # =========================================================
    @api.depends('han_hoan_thanh', 'trang_thai')
    def _compute_canh_bao_han(self):
        today = date.today()
        for record in self:
            if record.trang_thai == 'hoan_thanh':
                record.canh_bao_han = "✅ Đã xong kịp tiến độ"
            elif record.han_hoan_thanh and record.han_hoan_thanh < today:
                record.canh_bao_han = "🚨 QUÁ HẠN DEADLINE!"
            else:
                record.canh_bao_han = "⏳ Đang trong hạn"

    # =========================================================
    # CẢNH BÁO TRÙNG LỊCH (SMART WARNING)
    # =========================================================
    @api.onchange('nhan_vien_id', 'ngay_bat_dau', 'han_hoan_thanh')
    def _check_trung_lich_nhan_vien(self):
        if self.nhan_vien_id and self.ngay_bat_dau and self.han_hoan_thanh:
            domain = [
                ('nhan_vien_id', '=', self.nhan_vien_id.id),
                ('id', '!=', self._origin.id if self._origin else False),
                ('trang_thai', 'not in', ['hoan_thanh', 'da_huy', 'tam_hoan']),
                ('ngay_bat_dau', '<=', self.han_hoan_thanh),
                ('han_hoan_thanh', '>=', self.ngay_bat_dau)
            ]
            cac_task_trung = self.env['cong_viec'].search(domain)
            
            if cac_task_trung:
                danh_sach_ten_task = "\n- ".join(cac_task_trung.mapped('ten_cong_viec'))
                return {
                    'warning': {
                        'title': '⚠️ LƯU Ý: Nhân sự đang bận rộn!',
                        'message': f'Nhân viên {self.nhan_vien_id.ho_va_ten} đang có các task khác:\n{danh_sach_ten_task}\n\nBạn có chắc chắn muốn ép thêm việc không?'
                    }
                }

    # =================================================================
    # TÍCH HỢP AI TÓM TẮT YÊU CẦU
    # =================================================================
    def action_tom_tat_ai(self):
        for record in self:
            if not record.mo_ta:
                raise ValidationError("Bạn phải nhập 'Mô tả công việc' thì AI mới có cái để đọc và tóm tắt chứ!")
            
            api_key = 'KEY_API_CUA_BAN' 
            url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
            headers = {'Content-Type': 'application/json'}
            
            prompt = f"Bạn là một trợ lý quản lý dự án xuất sắc. Hãy đọc kỹ đoạn mô tả công việc sau và tóm tắt nó lại thành các gạch đầu dòng ngắn gọn, súc tích, dễ hiểu nhất cho lập trình viên:\n\n{record.mo_ta}"
            data = {"contents": [{"parts": [{"text": prompt}]}]}
            
            try:
                response = requests.post(url, headers=headers, json=data)
                if response.status_code != 200:
                    raise ValidationError(f"Google AI từ chối phục vụ! Chi tiết:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
                result = response.json()
                record.tom_tat_ai = result['candidates'][0]['content']['parts'][0]['text']
            except Exception as e:
                raise ValidationError(f"Lỗi khi xử lý dữ liệu AI: {str(e)}")