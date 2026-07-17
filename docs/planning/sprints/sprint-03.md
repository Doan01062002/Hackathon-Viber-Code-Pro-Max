# Sprint 3 — Thử nghiệm Thực tế, Giám sát Mô hình & Triển khai (Phase 3)

## 1. Mục tiêu Sprint
Áp dụng có chọn lọc chính sách tối ưu giá động và phân bổ hạn ngạch lên môi trường chạy thực tế có kiểm soát (Phase 3 - Controlled Live Trial / A/B Testing). Đóng gói Docker Compose toàn bộ các dịch vụ để triển khai thử nghiệm. Thiết lập cơ chế giám sát độ lệch mô hình (Model Drift) và tự động phát cảnh báo khi hệ thống có nguy cơ cháy vé hoặc trống chặng cao cận ngày đi.

---

## 2. Chỉ số Cam kết hoàn thành (Sprint KPIs)
* **Tần suất giám sát trôi mô hình (Drift detection):** Chạy kiểm tra MAE hàng ngày; phát hiện ngay nếu sai số dự báo nhu cầu vượt quá $25\%$ trong 3 ngày liên tiếp.
* **Thời gian kích hoạt cảnh báo:** $\le 5$ giây từ lúc phát hiện tồn kho chạm ngưỡng cảnh báo.
* **Mức độ an toàn hệ thống:** 0 sự cố gián đoạn dịch vụ khi thực hiện nâng cấp hoặc cập nhật tham số.
* **Bảo mật:** Đạt $100\%$ tuân thủ phân quyền RBAC và ghi nhận đầy đủ nhật ký kiểm toán vào `audit_logs`.

---

## 3. Danh sách Tác vụ (Backlog Items in Sprint)

| Mã tác vụ | Tên Tác vụ | Người thực hiện | Trạng thái |
|---|---|---|---|
| **SRRM-005** | Triển khai Docker Compose & Giám sát Model Drift | DevOps / AI Eng | Sẵn sàng |
| **SRRM-I3-ALERT** | Lập trình module tự động gửi cảnh báo cháy vé / trống chặng | Backend Dev | Sẵn sàng |
| **SRRM-I4-AUDIT** | Hoàn thiện UI tra cứu nhật ký kiểm toán dành cho admin | Frontend Dev | Sẵn sàng |
| **SRRM-I5-TEST** | Triển khai A/B Testing và đối chiếu hiệu năng thực tế | Data Scientist | Sẵn sàng |

---

## 4. Kế hoạch chi tiết theo ngày (2 tuần)
* **Ngày 1-3:** Viết cấu hình `Dockerfile` cho frontend, backend, và tệp `docker-compose.yml` liên kết PostgreSQL. Phân quyền non-root user cho các container.
* **Ngày 4-6:** Lập trình hàm tính toán độ lệch phân phối nhu cầu (Model Drift) trong Backend bằng cách so sánh dữ liệu dự báo tại `demand_forecasts` với lượng vé thực tế chốt tại `bookings`.
* **Ngày 7-9:** Xây dựng module tự động gửi cảnh báo. Quét bảng `segment_inventory` để phát hiện chặng có `remaining` dưới $10\%$ sức chứa hoặc quét `gap_combinations` để phát hiện ghế trống chặng ngắn chưa bán được sát ngày chạy.
* **Ngày 10-11:** Phát triển giao diện tra cứu lịch sử thay đổi `audit_logs` trên Next.js cho Admin ( Revenue Manager có thể xem ai đã thay đổi trần/sàn giá vé của `price_policies`).
* **Ngày 12-13:** Thực hiện chạy kiểm thử tích hợp cuối cùng, giả lập tải cao để bảo đảm cơ chế khóa dòng tồn kho (`SELECT FOR UPDATE`) hoạt động ổn định và không làm chậm quá trình thanh toán của khách.
* **Ngày 14:** Đóng gói toàn bộ sản phẩm bàn giao của giải pháp SRRM (mã nguồn, tài liệu trong `docs/`, AI logs) sẵn sàng nộp bài.
