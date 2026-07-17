# Sprint 2 — Tích hợp API, Giao diện Dashboard & Vận hành Shadow Mode (Phase 2 & 3)

## 1. Mục tiêu Sprint
Kết nối lõi thuật toán tối ưu với API Backend và cơ sở dữ liệu PostgreSQL. Phát triển giao diện quản lý Next.js (Dashboard trực quan heatmap tải chặng, biểu đồ đặt vé, cache ghép khoảng trống). Thiết lập chế độ chạy thử nghiệm shadow mode lưu kết quả báo giá và ghi nhận đầy đủ nhật ký kiểm toán.

---

## 2. Chỉ số Cam kết hoàn thành (Sprint KPIs)
* **Thời gian phản hồi API:** $\le 200$ ms đối với API báo cáo tải và báo cáo so sánh chính sách.
* **Thời gian ghi nhận đặt vé (Hold/Confirm):** $\le 100$ ms khi chạy transaction khóa tồn kho chặng.
* **Độ bao phủ Test tự động:** Đạt trên 80% đối với các API controllers và service layers của Backend.
* **Tính tương thích ranh giới module:** Đạt $100\%$ vượt qua kiểm tra của `make boundaries`.

---

## 3. Danh sách Tác vụ (Backlog Items in Sprint)

| Mã tác vụ | Tên Tác vụ | Người thực hiện | Trạng thái |
|---|---|---|---|
| **SRRM-004-P2** | Xây dựng REST API Backend (Heatmap, Pricing, Simulation) | Backend Dev | Sẵn sàng |
| **SRRM-I1-FE** | Phát triển UI Dashboard: Heatmap chặng & Booking Curve | Frontend Dev | Sẵn sàng |
| **SRRM-I2-FE** | Phát triển UI Simulation & So sánh chính sách AI vs Lịch sử | Frontend Dev | Sẵn sàng |
| **SRRM-I4-SEC** | Cấu hình lưu trữ Audit Logs & Quản lý phân quyền RBAC | Backend Dev | Sẵn sàng |

---

## 4. Kế hoạch chi tiết theo ngày (2 tuần)
* **Ngày 1-3:** Xây dựng các API FastAPI: `/api/v1/analytics/legs-heatmap` (join `segments` & `segment_inventory`), `/api/v1/pricing/quote` (truy vấn `price_quotes`), `/api/v1/optimize/resolve` (trigger DLP và atomic swap).
* **Ngày 4-6:** Thiết kế các Component giao diện Next.js: Biểu đồ nhiệt (Heatmap) chặng × thời gian (lấy từ tồn kho thực tế), biểu đồ tiến độ đặt vé (Booking Curve).
* **Ngày 7-9:** Xây dựng màn hình mô phỏng (Simulation Workspace) trên Next.js cho phép thay đổi hệ số trong `price_policies`, chạy giả lập và so sánh biểu đồ tài chính `price_quotes` vs `bookings` thực tế.
* **Ngày 10-11:** Phát triển cơ chế Shadow Mode: Nhận sự kiện tìm vé, gọi AI báo giá và lưu log báo giá vào `price_quotes` với trạng thái phù hợp.
* **Ngày 12-13:** Lập trình cơ chế ghi nhật ký kiểm toán tự động vào bảng `audit_logs` khi có bất kỳ hành động thay đổi cấu hình hoặc override hạn ngạch nào của Revenue Manager. Viết Unit Tests.
* **Ngày 14:** Đóng gói Docker Compose toàn bộ dự án (FE + BE + PostgreSQL) và kiểm tra tích hợp.
