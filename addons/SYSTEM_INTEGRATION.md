# Tích hợp hệ thống (System Integration)

## Yêu cầu

- **Tính nhất quán dữ liệu**: Các module kết hợp chia sẻ chung một cơ sở dữ liệu (Database), loại bỏ nhập liệu trùng lặp.
- **Dữ liệu gốc**: Dữ liệu nhân sự (Module HRM) là **dữ liệu gốc** để đồng bộ sang các module khác (Dự án, Công việc, Lương...) theo yêu cầu.

---

## Kiến trúc tích hợp

### 1. Nguồn dữ liệu gốc nhân sự (HRM)

| Module   | Tên kỹ thuật  | Vai trò |
|----------|----------------|--------|
| Nhân sự  | **nhan_su**    | Module HRM – **nguồn dữ liệu gốc** nhân viên. Model `nhan_vien` là bảng master duy nhất cho thông tin nhân viên. |

- **Model gốc**: `nhan_vien` (trong addon `nhan_su`).
- Các module khác **không** được tạo bảng/ model nhân viên riêng; chỉ tham chiếu `nhan_vien` qua quan hệ Many2one / Many2many.

### 2. Các module đồng bộ từ HRM (dùng chung database, không trùng lặp)

| Module       | Tên kỹ thuật         | Phụ thuộc   | Cách dùng dữ liệu nhân sự |
|-------------|----------------------|------------|----------------------------|
| Quản lý công việc | **quan_ly_cong_viec** | `base`, **nhan_su**, **quan_ly_du_an** | `cong_viec.du_an_id`, `cong_viec.nhan_vien_id`, ... (Many2one → `nhan_vien`, `du_an`) |
| Quản lý dự án    | **quan_ly_du_an**     | `base`, **nhan_su** | `du_an.nhan_vien_ids`, `nhiem_vu.nguoi_thuc_hien_id` / `nguoi_phu_trach_id`, `rui_ro.nguoi_chiu_trach_nhiem_ids`, `thoi_gian_lam_viec.nhan_vien_id` (Many2many / Many2one → `nhan_vien`) |

- Tất cả đều **depends** `nhan_su` trong `__manifest__.py`.
- Cùng một database: nhân viên được tạo/sửa **chỉ** ở module Nhân sự; Dự án và Công việc chỉ **chọn** từ `nhan_vien`, không nhập lại thông tin nhân viên.

### 3. Module chưa dùng nhân sự

- **quan_ly_van_ban**: Hiện chỉ `depends: ['base']`. Khi cần thêm người ký / người xử lý văn bản, nên thêm `depends: ['nhan_su']` và dùng model `nhan_vien` (Many2one/Many2many), không tạo model nhân viên riêng.

### 4. Module tương lai (ví dụ: Lương)

- Module Lương (nếu có) **bắt buộc**:
  - `depends: ['base', 'nhan_su']`
  - Sử dụng model `nhan_vien` làm dữ liệu gốc (liên kết bảng lương với `nhan_vien`), không nhập lại danh sách nhân viên.

---

## Quy tắc khi phát triển thêm module

1. **Chung database**: Mọi module dùng chung một database Odoo; không tách database theo từng module.
2. **Nhân sự là gốc**: Mọi dữ liệu liên quan đến nhân viên (tên, mã, đơn vị, chức vụ...) lấy từ **nhan_su** (model `nhan_vien` hoặc model liên quan trong nhan_su).
3. **Khai báo phụ thuộc**: Module nào cần dùng nhân viên thì trong `__manifest__.py` phải có `'depends': [..., 'nhan_su']`.
4. **Không trùng lặp**: Không tạo bảng/model “nhân viên” hoặc “employee” riêng trong module khác; chỉ tham chiếu `nhan_vien` qua Many2one / Many2many.

---

## Tóm tắt

- **Một nguồn sự thật**: HRM (`nhan_su`, model `nhan_vien`) là nguồn dữ liệu gốc nhân sự.
- **Một database**: Dự án, Công việc, (và sau này Lương, Văn bản nếu cần) dùng chung database và cùng tham chiếu `nhan_vien`.
- **Không nhập trùng**: Nhân viên được nhập/chỉnh sửa ở Nhân sự; các module khác chỉ gán/đồng bộ theo `nhan_vien`.

---

## Mức 2: Tự động hóa quy trình (Process Automation)

**Yêu cầu**: Hệ thống tự động thực hiện bước tiếp theo theo sự kiện (event-driven), giảm thao tác thủ công.

### Luồng đã triển khai (3 module: Nhân sự, Công việc, Dự án)

| Sự kiện | Hành động tự động |
|--------|---------------------|
| **Tạo Dự án** | Tự động tạo 1 **Công việc** "Khởi tạo dự án: [Tên dự án]", gắn với dự án, ngày bắt đầu/kết thúc từ dự án, gán nhân viên dự án (nếu có). |
| **Công việc chuyển trạng thái "Hoàn thành"** | Tự động tạo 1 **Ghi nhận thời gian** (ngày hôm nay, số giờ = 0, nhân viên = người phụ trách công việc) và 1 **Đánh giá công việc** mẫu (KPI = 0, nhận xét mặc định) để PM cập nhật sau. |

### Vị trí code

- **Dự án → Công việc**: `addons/quan_ly_du_an/models/du_an.py` — override `create()`.
- **Công việc Hoàn thành → Ghi nhận + Đánh giá**: `addons/quan_ly_cong_viec/models/cong_viec.py` — override `write()` khi `trang_thai == 'hoan_thanh'`.
- **Liên kết Dự án – Công việc**: Model `cong_viec` có trường `du_an_id` (Many2one `du_an`).

### Có nên tạo thêm module?

- **Chỉ với 3 module** (Nhân sự, Công việc, Dự án): Đã đủ đạt **Mức 2** nhờ 2 luồng trên, không bắt buộc tạo module mới.
- **Nếu muốn điểm cao và thiết thực hơn** (tùy chọn):
  - **Module Lương**: Khi "Ghi nhận thời gian" được duyệt → tự động cập nhật bảng lương (dữ liệu gốc vẫn là `nhan_vien`).
  - **Thông báo / Hoạt động**: Khi Công việc **Quá hạn** → tạo activity hoặc ghi nhận nhắc việc (có thể dùng Odoo activity hoặc module nhỏ).
  - **Báo cáo tổng hợp**: Module báo cáo đọc dữ liệu từ Dự án + Công việc + Ghi nhận thời gian (không cần tự động hóa thêm, chỉ cần report).
