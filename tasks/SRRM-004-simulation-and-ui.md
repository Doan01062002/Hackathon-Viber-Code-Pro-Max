# Task — SRRM-004: Xây dựng Giao diện Dashboard & API Mô phỏng

## 1. Mục tiêu
Phát triển các API REST Backend kết nối PostgreSQL phục vụ truyền tải dữ liệu và xây dựng các trang giao diện Next.js cho Dashboard quản lý điều vé (Heatmap chặng, biểu đồ đặt vé, cache ghép khoảng trống) và Workspace mô phỏng chính sách bán vé (so sánh AI vs Lịch sử).

---

## 2. Mô tả Nghiệp vụ & Kỹ thuật

### 2.1. Thiết kế Giao diện UI/UX (Next.js 14)
Tuân thủ chỉ dẫn về thiết kế cao cấp (Premium Aesthetics):
* **Heatmap tải chặng:** Sử dụng dữ liệu từ `segments` join với `segment_inventory` để lấy tồn kho thực tế (`remaining`) và sức chứa gốc (`capacity`). Hiển thị màu sắc trực quan (đỏ, vàng, xanh ngọc) theo tỷ lệ lấp đầy.
* **Biểu đồ tiến độ đặt vé (Booking Curve):** Sử dụng thư viện **Recharts** vẽ đường tích lũy vé bán từ `bookings.booked_at` so sánh song song với đường dự báo nhu cầu trong `demand_forecasts`.
* **Gợi ý lấp khoảng trống:** Hiển thị danh sách các đề xuất lấp khoảng trống ghế đang hoạt động từ bảng `gap_combinations` để gợi ý bán vé chặng ngắn bù đắp cho chặng trống.
* **Workspace mô phỏng chính sách:** Giao diện so sánh doanh thu giả lập của chính sách giá cấu hình tại `price_policies` (được chạy thử nghiệm trên dữ liệu lịch sử) với doanh thu thực tế ghi nhận tại bảng `bookings`.

### 2.2. FastAPI REST Controllers & Services
* **`analytics_controller.py`:** API xuất ma trận heatmap tải chặng (`segments` + `segment_inventory` + active `bid_prices`).
* **`pricing_controller.py`:** API báo giá cho hành khách, truy vấn và ghi nhận vào `price_quotes`.
* **`optimize_controller.py`:** API trigger chạy lại tối ưu hóa DLP và swap cờ `is_active` cho `bid_prices` và `quotas`.
* **`simulation_controller.py`:** API chạy giả lập trên dữ liệu lịch sử của `bookings`.
* **`audit_controller.py` [NEW]:** API hiển thị nhật ký thay đổi của hệ thống từ bảng `audit_logs`.

### 2.3. Nhật ký Kiểm toán (Audit Logging)
* Khi Revenue Manager thực hiện các hành động can thiệp (điều chỉnh hạn ngạch, khóa ghế, kích hoạt chính sách giá trần/sàn mới), Backend phải tự động thêm một bản ghi vào bảng `audit_logs` lưu thông tin người dùng (`actor`), hành động (`action`), loại thực thể (`entity_type`), ID thực thể (`entity_id`), và trạng thái dữ liệu trước/sau thay đổi dạng JSONB (`before_data`, `after_data`).

---

## 3. Các thành phần mã nguồn liên quan
* `backend/src/backend/controllers/analytics.py` [MODIFY]: API báo cáo tải chặng.
* `backend/src/backend/controllers/simulation.py` [MODIFY]: API điều phối mô phỏng chính sách.
* `backend/src/backend/controllers/audit.py` [NEW]: API kết xuất nhật ký kiểm toán.
* `frontend/src/features/dashboard/` [MODIFY]: Components heatmap, booking curve, gap suggestions.
* `frontend/src/features/simulation/` [MODIFY]: Workspace so sánh chính sách.
* `frontend/src/features/audit/` [NEW]: Màn hình hiển thị nhật ký kiểm toán hệ thống.

---

## 4. Tiêu chí Chấp nhận (Acceptance Criteria)
* **AC1:** Heatmap hiển thị đúng thông số tồn kho thực tế (`remaining`) lấy từ bảng `segment_inventory`.
* **AC2:** Báo cáo so sánh chính sách hiển thị biểu đồ trực quan, tính toán chính xác chỉ số doanh thu tăng trưởng so với dữ liệu thực tế lịch sử của `bookings`.
* **AC3:** Tốc độ phản hồi của các API báo cáo và simulation $\le 200$ ms.
* **AC4:** Toàn bộ hoạt động can thiệp cấu hình chính sách giá được lưu vết đầy đủ trong bảng `audit_logs` và hiển thị chính xác trên màn hình kiểm toán.
