# Task — SRRM-005: Triển khai Docker Compose & Giám sát Model Drift

## 1. Mục tiêu
Cấu hình đóng gói container hóa toàn bộ ứng dụng (Next.js, FastAPI, PostgreSQL), lập trình cơ chế phát hiện độ lệch của mô hình dự báo học máy (Model Drift) và quản lý phân quyền kiểm toán trên PostgreSQL.

---

## 2. Mô tả Kỹ thuật

### 2.1. Đóng gói Container (Docker Compose)
* **`backend/Dockerfile`:** Build từ gốc dự án, copy mã nguồn `ai/` và `backend/` vào container, chạy dưới quyền `appuser` (non-root) bảo mật.
* **`frontend/Dockerfile`:** Nhúng biến build-arg `NEXT_PUBLIC_API_URL` vào bundle Next.js, chạy server Node.js dưới quyền user `nextjs`.
* **`docker-compose.yml`:** Liên kết 3 container:
  * `db` (PostgreSQL 15+ lưu trữ dữ liệu, expose port 5432).
  * `backend` (FastAPI web server chạy cổng 8000, kết nối tới `db`).
  * `frontend` (Next.js web client chạy cổng 3000, gọi API `/api/v1`).

### 2.2. Tính toán Giám sát Trôi mô hình (Model Drift)
* **Khái niệm:** Mô hình dự báo nhu cầu học máy có thể bị giảm độ chính xác theo thời gian khi hành vi đi lại của hành khách thay đổi (ví dụ: xuất hiện tuyến giao thông mới cạnh tranh).
* **Giải thuật giám sát:**
  * Viết một cron job chạy hàng ngày để tính toán sai số **Mean Absolute Error (MAE)** của dự báo nhu cầu.
  * So sánh giá trị dự báo tích lũy `demand_forecasts.demand_point` (được lưu tại thời điểm $T$ ngày trước ngày chạy) với lượng vé đặt thực tế cuối cùng được ghi nhận trong bảng `bookings` cho cùng một ngày chạy tàu `service_date`.
  * Nếu sai số dự báo MAE hoặc MAPE vượt quá ngưỡng $25\%$ liên tục trên 3 ngày chạy tàu gần nhất, kích hoạt trạng thái cảnh báo **Model Drift Detected** gửi lên dashboard và ghi nhật ký vào `audit_logs` để AI Engineer thực hiện huấn luyện lại (retraining) mô hình.

### 2.3. Nhật ký kiểm toán hành động (Audit Logs)
* Cài đặt API kết xuất bảng `audit_logs` dành cho admin.
* Đảm bảo mọi chỉnh sửa chính sách giá tại `price_policies` hoặc thay đổi cấu hình toa tàu tại `seats` đều được bọc qua middleware/service ghi log audit dạng JSONB, ghi nhận thông tin `before_data` và `after_data`.

---

## 3. Các thành phần mã nguồn liên quan
* `backend/Dockerfile` [MODIFY]: Cấu hình image cho Backend + AI.
* `frontend/Dockerfile` [MODIFY]: Cấu hình image cho Frontend Next.js.
* `docker-compose.yml` [MODIFY]: Liên kết các dịch vụ và biến môi trường.
* `backend/src/backend/services/drift_detector.py` [NEW]: Hàm cron kiểm tra độ lệch mô hình.
* `backend/src/backend/controllers/audit.py` [NEW]: API Gateway xuất nhật ký kiểm toán.

---

## 4. Tiêu chí Chấp nhận (Acceptance Criteria)
* **AC1:** Lệnh `docker compose up --build` chạy thành công toàn bộ các dịch vụ (FE, BE, CSDL) mà không cần cài đặt thêm phần mềm nào trên máy host.
* **AC2:** Hàm kiểm tra Model Drift hoạt động đúng toán học, tính toán ra MAE/MAPE khớp giữa dự báo và bookings thực tế.
* **AC3:** Cảnh báo trôi mô hình được tự động ghi lại tại `audit_logs` khi sai số vượt ngưỡng cấu hình.
* **AC4:** Hệ thống chạy an toàn dưới quyền non-root user bên trong các container Docker.
