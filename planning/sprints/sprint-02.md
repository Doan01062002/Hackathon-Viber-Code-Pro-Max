# Sprint 2 — Tích hợp API, Giao diện Dashboard & Vận hành Shadow Mode (Phase 2 & 3)

## 1. Mục tiêu Sprint
Kết nối lõi thuật toán tối ưu từ module AI sang API Backend (FastAPI). Phát triển giao diện quản lý (Next.js) trực quan hóa heatmap tải chặng và màn hình so sánh chính sách bán vé. Thiết lập chế độ chạy thử nghiệm shadow mode để Revenue Manager có thể theo dõi và can thiệp đề xuất.

---

## 2. Chỉ số Cam kết hoàn thành (Sprint KPIs)
* **Thời gian phản hồi API:** $\le 200$ ms đối với API báo cáo tải và báo cáo so sánh chính sách.
* **Thời gian tính toán lại thời gian thực:** $\le 500$ ms khi nhận sự kiện đặt vé mới trong shadow mode.
* **Độ bao phủ Test tự động:** Đạt trên 80% đối với các API controllers và service layers của Backend.
* **Tính tương thích ranh giới module:** Đạt $100\%$ vượt qua kiểm tra của `make boundaries`.

---

## 3. Danh sách Tác vụ (Backlog Items in Sprint)

| Mã tác vụ | Tên Tác vụ | Người thực hiện | Trạng thái |
|---|---|---|---|
| **SRRM-004-P2** | Xây dựng API FastAPI (Heatmap, pricing quote, simulation) | Backend Dev | Sẵn sàng |
| **SRRM-I1-FE** | Phát triển UI Dashboard: Heatmap chặng & Booking Curve | Frontend Dev | Sẵn sàng |
| **SRRM-I2-FE** | Phát triển UI Simulation & So sánh chính sách AI vs Lịch sử | Frontend Dev | Sẵn sàng |
| **SRRM-I4-SEC** | Cấu hình log kiểm toán, lưu lịch sử phê duyệt và phân quyền | Backend Dev | Sẵn sàng |

---

## 4. Kế hoạch chi tiết theo ngày (2 tuần)
* **Ngày 1-3:** Xây dựng các API Endpoint trong `backend/src/backend/controllers/` để xuất heatmap tải chặng, báo cáo so sánh và lấy đề xuất giá vé động.
* **Ngày 4-6:** Thiết kế các Component giao diện Next.js: Biểu đồ nhiệt (Heatmap) chặng × thời gian, biểu đồ tiến độ bán vé (Booking Curve).
* **Ngày 7-9:** Xây dựng màn hình mô phỏng (Simulation Workspace) trên Next.js cho phép thay đổi hệ số markup, trần/sàn giá vé, chạy thử và so sánh biểu đồ tài chính AI đề xuất vs Lịch sử thực tế.
* **Ngày 10-11:** Phát triển cơ chế Shadow Mode: Lắng nghe sự kiện giả lập đặt vé thực tế, đẩy dữ liệu qua module AI tính lại hạn ngạch/giá vé, lưu log đề xuất để Revenue Manager đánh giá.
* **Ngày 12-13:** Viết unit test cho controllers và dịch vụ của Backend. Chạy kiểm tra định dạng và ranh giới (`make check`).
* **Ngày 14:** Đóng gói Docker Compose toàn bộ dự án, kiểm tra độ ổn định khi chạy đồng thời.
