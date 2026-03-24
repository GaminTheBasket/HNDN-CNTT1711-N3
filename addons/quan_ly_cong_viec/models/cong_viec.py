from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date
import requests
import json

# =========================================================
# CÁC BẢNG PHỤ
# =========================================================
class CongViecCon(models.Model):
    _name = 'cong_viec_con'
    _description = 'Công việc con'
    
    ten_cong_viec_con = fields.Char("Tên việc con", required=True)
    cong_viec_id = fields.Many2one('cong_viec', ondelete='cascade')
    nhan_vien_id = fields.Many2one('nhan_vien', string="Người làm")
    han_hoan_thanh = fields.Date("Hạn hoàn thành")
    trang_thai = fields.Selection([('moi', 'Mới'), ('dang_thuc_hien', 'Đang làm'), ('hoan_thanh', 'Hoàn thành')], default='moi')

class GhiNhanThoiGian(models.Model):
    _name = 'ghi_nhan_thoi_gian'
    _description = 'Chi tiết thời gian làm việc'
    
    cong_viec_id = fields.Many2one('cong_viec', string="Công việc", ondelete='cascade')
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên")
    ngay_ghi_nhan = fields.Date("Ngày làm", default=fields.Date.context_today)
    mo_ta = fields.Char("Nội dung đã làm", required=True)
    thoi_gian_lam = fields.Float("Số giờ làm (h)", required=True)

class DanhGiaCongViec(models.Model):
    _name = 'danh_gia_cong_viec'
    _description = 'Đánh giá kết quả công việc'
    
    cong_viec_id = fields.Many2one('cong_viec', string="Công việc", ondelete='cascade')
    nguoi_danh_gia_id = fields.Many2one('nhan_vien', string="Quản lý đánh giá")
    ngay_danh_gia = fields.Date("Ngày đánh giá", default=fields.Date.context_today)
    # Bỏ điểm số trẻ con, tập trung vào nhận xét chuyên môn
    nhan_xet = fields.Text("Nhận xét chi tiết của quản lý", required=True)

# =========================================================
# BẢNG CHÍNH: CÔNG VIỆC
# =========================================================
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

    cong_viec_con_ids = fields.One2many("cong_viec_con", inverse_name="cong_viec_id", string="Công việc con")
    ghi_nhan_thoi_gian_ids = fields.One2many("ghi_nhan_thoi_gian", inverse_name="cong_viec_id", string="Ghi nhận thời gian")
    danh_gia_cong_viec_ids = fields.One2many("danh_gia_cong_viec", inverse_name="cong_viec_id", string="Đánh giá công việc")

    tong_gio_lam_thuc_te = fields.Float("Tổng giờ làm thực tế", compute="_compute_tong_gio_lam", store=True)

    @api.depends('ghi_nhan_thoi_gian_ids.thoi_gian_lam')
    def _compute_tong_gio_lam(self):
        for record in self:
            record.tong_gio_lam_thuc_te = sum(record.ghi_nhan_thoi_gian_ids.mapped('thoi_gian_lam'))

    @api.onchange('du_an_id')
    def _loc_nhan_vien_theo_du_an(self):
        if self.du_an_id:
            if self.nhan_vien_id and self.nhan_vien_id not in self.du_an_id.nhan_vien_ids:
                self.nhan_vien_id = False
            return {'domain': {'nhan_vien_id': [('id', 'in', self.du_an_id.nhan_vien_ids.ids)]}}
        else:
            return {'domain': {'nhan_vien_id': []}}

    @api.depends('cong_viec_con_ids.trang_thai', 'trang_thai')
    def _compute_tien_do(self):
        for record in self:
            tong_so_viec_con = len(record.cong_viec_con_ids)
            if tong_so_viec_con > 0:
                viec_da_xong = len(record.cong_viec_con_ids.filtered(lambda x: x.trang_thai == 'hoan_thanh'))
                record.tien_do = (viec_da_xong / tong_so_viec_con) * 100.0
                if record.tien_do == 100.0 and record.trang_thai != 'hoan_thanh':
                    record.trang_thai = 'hoan_thanh'
                elif (record.tien_do > 0 or any(c.trang_thai == 'dang_thuc_hien' for c in record.cong_viec_con_ids)):
                    if record.trang_thai == 'moi':
                        record.trang_thai = 'dang_thuc_hien'
            else:
                if record.trang_thai == 'hoan_thanh':
                    record.tien_do = 100.0
                else:
                    record.tien_do = 0.0

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

    def action_tom_tat_ai(self):
        for record in self:
            if not record.mo_ta:
                raise ValidationError("Bạn phải nhập 'Mô tả công việc' thì AI mới có cái để đọc và tóm tắt chứ!")
            api_key = '.....'
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

    @api.model_create_multi
    def create(self, vals_list):
        records = super(CongViec, self).create(vals_list)
        for record in records:
            if record.nhan_vien_id:
                record._send_telegram_notification_giao_viec()
        return records

    def write(self, vals):
        res = super(CongViec, self).write(vals)
        for record in self:
            if vals.get('trang_thai') == 'hoan_thanh':
                record._send_telegram_notification_hoan_thanh()
            if 'nhan_vien_id' in vals and record.nhan_vien_id:
                record._send_telegram_notification_giao_viec()
        return res

    def _send_telegram_notification_hoan_thanh(self):
        bot_token = '.....'
        chat_id = '.....'
        ten_nv = self.nhan_vien_id.ho_va_ten if self.nhan_vien_id else 'Chưa phân công'
        ten_da = self.du_an_id.ten_du_an if self.du_an_id else 'Không thuộc dự án nào'
        message = (
            f"🚀 <b>[TIN VUI] HOÀN THÀNH CÔNG VIỆC!</b>\n\n"
            f"👤 <b>Nhân viên:</b> {ten_nv}\n"
            f"🎮 <b>Dự án:</b> {ten_da}\n"
            f"✅ <b>Task:</b> {self.ten_cong_viec}\n"
            f"⏰ <b>Lúc:</b> {fields.Datetime.now()}"
        )
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass

    def _send_telegram_notification_giao_viec(self):
        bot_token = '.......'
        chat_id = '........'
        ten_nv = self.nhan_vien_id.ho_va_ten if self.nhan_vien_id else 'Chưa phân công'
        ten_da = self.du_an_id.ten_du_an if self.du_an_id else 'Không thuộc dự án nào'
        message = (
            f"🎯 <b>[CÓ CÔNG VIỆC MỚI ĐƯỢC GIAO]</b>\n\n"
            f"👤 <b>Người nhận:</b> {ten_nv}\n"
            f"🎮 <b>Dự án:</b> {ten_da}\n"
            f"📝 <b>Task:</b> {self.ten_cong_viec}\n"
            f"⏳ <b>Deadline:</b> {self.han_hoan_thanh}\n"
            f"🔥 <i>Vào Odoo check yêu cầu và chiến đấu ngay nhé!</i>"
        )
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass