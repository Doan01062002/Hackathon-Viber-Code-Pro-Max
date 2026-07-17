# Task — SRRM-004: Xây dựng Giao diện Dashboard & API Mô phỏng

## 1. Mục tiêu
Phát triển các API REST Backend phục vụ truyền tải dữ liệu và xây dựng các trang giao diện Next.js cho Dashboard quản lý điều vé (Heatmap chặng, biểu đồ đặt vé) và Workspace mô phỏng chính sách bán vé (so sánh AI vs Lịch sử).

---

## 2. Mô tả Nghiệp vụ & Kỹ thuật

### 2.1. Thiết kế Giao diện UI/UX (Next.js 14)
Tuân thủ chỉ dẫn về thiết kế cao cấp (Premium Aesthetics):
* **Trực quan hóa Heatmap chặng:** Thiết kế bảng lưới (Grid) hiển thị các toa xe và chặng đường. Sử dụng màu sắc tinh tế để chỉ thị trạng thái tải (ví dụ: đỏ sẫm cho quá tải/cháy vé, xanh ngọc dịu cho trạng thái bình thường, xám bạc cho chặng trống nhiều).
* **Biểu đồ tiến độ đặt vé (Booking Curve):** Sử dụng thư viện **Recharts** vẽ đường tích lũy vé bán theo thời gian đặt trước (lead time), so sánh giữa đường thực tế và đường dự báo nhu cầu.
* **Workspace so sánh chính sách:** Giao diện chia làm 2 cột hoặc dạng so sánh song song (Side-by-Side). Một bên hiển thị kết quả tài chính của chính sách lịch sử, một bên hiển thị kết quả giả lập tối ưu của AI (Doanh thu tăng $X\%$, Ghế-km tăng $Y\%$).

### 2.2. FastAPI REST Controllers & Services
* **`analytics_controller.py`:** Tiếp nhận yêu cầu từ Frontend, gọi `AnalyticsService` để lấy dữ liệu tải chặng và chuẩn bị ma trận hiển thị Heatmap.
* **`pricing_controller.py`:** Cung cấp API tính toán giá vé nhanh cho hành khách (Passenger quote).
* **`optimize_controller.py`:** API trigger chạy lại DLP tối ưu hóa phân bổ hạn ngạch thủ công hoặc theo lịch trình.
* **`simulation_controller.py`:** API thực hiện chạy mô phỏng lịch sử (Backtest) trên tập dữ liệu được chọn và trả về kết quả so sánh dạng JSON.

---

## 3. Các thành phần mã nguồn liên quan
* `backend/src/backend/controllers/analytics.py` [NEW]: API báo cáo và trực quan tải chặng.
* `backend/src/backend/controllers/simulation.py` [NEW]: API điều phối mô phỏng chính sách.
* `frontend/src/features/dashboard/` [NEW]: Components heatmap, booking curve.
* `frontend/src/features/simulation/` [NEW]: Workspace so sánh chính sách giá.
* `frontend/src/lib/api/` [MODIFY]: Thêm các hàm call API mới.

---

## 4. Tiêu chí Chấp nhận (Acceptance Criteria)
* **AC1:** Heatmap hiển thị đúng thông số tải chặng của đoàn tàu được chọn và thay đổi trạng thái màu sắc mượt mà khi lọc ngày chạy.
* **AC2:** Báo cáo so sánh chính sách hiển thị rõ ràng chỉ số doanh thu tăng trưởng (%) dạng biểu đồ trực quan, giúp ban giám khảo dễ dàng đối chiếu.
* **AC3:** Tốc độ phản hồi của API báo cáo tải chặng $\le 200$ ms khi truy vấn trên dữ liệu MVP (1-3 tàu).
