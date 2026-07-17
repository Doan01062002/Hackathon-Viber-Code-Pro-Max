# Specs — Phân quyền & Vai trò Người dùng (User Roles)

Hệ thống **Smart Rail Revenue Management (SRRM)** phục vụ nhiều nhóm đối tượng sử dụng khác nhau trong quy trình vận hành và kiểm chứng mô hình. Dưới đây là mô tả chi tiết quyền hạn, trách nhiệm và hành động của từng vai trò trên hệ thống.

---

## 1. Quản lý Điều vé (Revenue Manager) - Persona Trọng tâm

Đây là người dùng chính của hệ thống SRRM trong giai đoạn MVP và vận hành thực tế.

* **Trách nhiệm:** 
  * Quản trị doanh thu và tối ưu hóa hệ số lấp đầy của các chuyến tàu được phân công.
  * Phê duyệt các chính sách phân bổ chỗ và đề xuất điều chỉnh giá vé từ hệ thống AI.
* **Quyền hạn & Hành động trên hệ thống:**
  * **Xem Dashboard:** Theo dõi heatmap tải của từng chặng theo thời gian, tiến độ đặt vé thực tế so với dự báo nhu cầu.
  * **Mô phỏng Chính sách:** Chạy thử nghiệm các phương án giá hoặc hạn ngạch để xem dự báo doanh thu thay đổi như thế nào trước khi áp dụng chính thức.
  * **Ghi đè thủ công (Manual Override):** Can thiệp điều chỉnh tăng/giảm hạn ngạch chỗ cho các ga trung gian, cố định mức giá vé trong các trường hợp khẩn cấp hoặc các dịp lễ đặc biệt.
  * **Phê duyệt Đề xuất:** Xác nhận áp dụng các đề xuất tối ưu hóa giá/hạn ngạch do AI đưa ra.

---

## 2. Điều độ / Kế hoạch Chạy tàu (Dispatcher)

Đối tượng quản lý trực tiếp năng lực vận tải vật lý của các đoàn tàu.

* **Trách nhiệm:** 
  * Bảo đảm thông tin cấu hình đoàn tàu (số toa, loại chỗ, số lượng ghế vật lý khả dụng) luôn chính xác trên hệ thống.
* **Quyền hạn & Hành động trên hệ thống:**
  * **Cấu hình Toa & Ghế:** Nhập và cập nhật sơ đồ toa tàu, phân loại chỗ ngồi (ngồi mềm điều hòa, giường nằm khoang 6...).
  * **Khóa/Ưu tiên Ghế:** Khóa các chỗ ngồi phục vụ mục đích kỹ thuật, công vụ hoặc các nhóm đối tượng ưu tiên (người khuyết tật, lực lượng vũ trang) ra khỏi phạm vi phân bổ tự động của AI.
  * **Cập nhật Sự cố:** Khai báo các sự cố bất thường về toa xe dẫn đến giảm sức chứa đột xuất để hệ thống chạy lại bài toán tối ưu DLP.

---

## 3. Bộ phận CNTT / Tích hợp (IT Integrator)

Nhóm kỹ sư vận hành hệ thống và bảo đảm tích hợp thông suốt giữa SRRM với hệ thống bán vé điện tử hiện hành.

* **Trách nhiệm:** 
  * Giám sát tính ổn định của hệ thống, hiệu năng API và quản lý dữ liệu đầu vào/đầu ra.
* **Quyền hạn & Hành động trên hệ thống:**
  * **Giám sát Mô hình (Model Drift):** Theo dõi độ lệch của dự báo nhu cầu và hiệu năng của mô hình AI theo thời gian.
  * **Cấu hình Tích hợp:** Thiết lập các endpoint kết nối API, phân quyền người dùng (RBAC - Role-Based Access Control) cho Revenue Manager và Dispatcher.
  * **Khôi phục (Rollback):** Thực hiện rollback nhanh về chính sách bán vé và bảng giá truyền thống khi phát hiện lỗi hệ thống nghiêm trọng.

---

## 4. Ban Giám khảo / Lãnh đạo (Evaluators - Dành riêng cho MVP)

Nhóm người dùng đánh giá tính hiệu quả thực tế của giải pháp tại cuộc thi.

* **Trách nhiệm:** 
  * Đánh giá tính khả thi, hiệu quả kinh tế và mức độ đổi mới sáng tạo của thuật toán SRRM.
* **Quyền hạn & Hành động trên hệ thống:**
  * **Xem báo cáo Backtesting (Phase 1):** So sánh trực quan các chỉ số KPI then chốt (doanh thu chuyến, hệ số sử dụng ghế-km, tỷ lệ chặng trống) giữa phương án AI đề xuất và phương án thực tế lịch sử đã diễn ra.
  * **Đánh giá Tính minh bạch:** Xem chi tiết giải trình (explainable) của AI cho từng quyết định giá vé và quyết định từ chối/chấp nhận đặt chỗ.
