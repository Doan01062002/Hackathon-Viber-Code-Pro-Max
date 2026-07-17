# Sprint 1 — Thiết lập Database, Lõi Thuật toán & Backtesting (Phase 1)

## 1. Mục tiêu Sprint
Khởi tạo cơ sở dữ liệu PostgreSQL với toàn bộ 21 bảng vận hành, chỉ mục và trigger tự động. Xây dựng và kiểm thử lõi thuật toán của 3 phân hệ (Dự báo nhu cầu, Tối ưu DLP và Định giá động) trên môi trường Python và thực hiện chạy giả lập (backtest) trên dữ liệu lịch sử để chứng minh hiệu quả tăng trưởng doanh thu.

---

## 2. Chỉ số Cam kết hoàn thành (Sprint KPIs)
* **Khởi tạo Database:** 21 bảng, 5 index và 7 trigger hoạt động chính xác $100\%$ theo đúng thiết kế `schema.sql`.
* **MAPE dự báo nhu cầu:** $\le 15\%$ đối với các cặp OD chính (lưu kết quả vào `demand_forecasts`).
* **Thời gian giải DLP:** $\le 2$ giây cho một chuyến tàu (lưu vào `bid_prices` và `quotas`).
* **Doanh thu mô phỏng:** Doanh thu giả lập của AI vượt doanh thu lịch sử thực tế trong `bookings` từ **3% đến 8%**.

---

## 3. Danh sách Tác vụ (Backlog Items in Sprint)

| Mã tác vụ | Tên Tác vụ | Người thực hiện | Trạng thái |
|---|---|---|---|
| **SRRM-D1** | Cấu hình PostgreSQL Schema, Indexes & Triggers | Database Eng | Sẵn sàng |
| **SRRM-D2** | Thiết lập Repository Layer & Row-Level Locking | Backend Dev | Sẵn sàng |
| **SRRM-001** | Phát triển mô hình dự báo nhu cầu OD & EM algorithm | AI Engineer | Sẵn sàng |
| **SRRM-002** | Xây dựng bộ tối ưu DLP (OR-Tools) & Atomic Swap | AI Engineer | Sẵn sàng |
| **SRRM-003** | Lập trình lõi định giá động và Price Safeguards | AI/BE Dev | Sẵn sàng |

---

## 4. Kế hoạch chi tiết theo ngày (2 tuần)
* **Ngày 1-2:** Cài đặt PostgreSQL, nạp tệp `schema.sql`, kiểm tra hoạt động của trigger `updated_at`.
* **Ngày 3-5:** Viết repository SQLAlchemy. Triển khai logic khóa hàng tồn kho chặng (`segment_inventory` FOR UPDATE) và rollback khi hết chỗ.
* **Ngày 6-8:** Viết thuật toán EM unconstraining trên dữ liệu `search_logs` và `bookings`. Huấn luyện mô hình dự báo ghi kết quả vào `demand_forecasts`.
* **Ngày 9-11:** Thiết lập mô hình quy hoạch tuyến tính DLP. Lưu kết quả đối ngẫu vào `bid_prices` và quotas vào `quotas` dưới dạng `run_version` mới, thực hiện atomic swap.
* **Ngày 12-13:** Kết nối đầu ra Bid Price hoạt động sang module định giá. Áp dụng công thức markup và ràng buộc từ `price_policies`, lưu nhật ký vào `price_quotes`.
* **Ngày 14:** Chạy backtest mô phỏng trên 1 tháng dữ liệu lịch sử và xuất báo cáo so sánh KPI.
