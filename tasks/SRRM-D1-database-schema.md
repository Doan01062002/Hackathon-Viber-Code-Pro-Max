# Task — SRRM-D1: Cấu hình PostgreSQL Schema, Indexes & Triggers

## 1. Mục tiêu
Thiết lập toàn bộ cấu trúc cơ sở dữ liệu vật lý PostgreSQL bao gồm 21 bảng vận hành, các chỉ mục tối ưu tìm kiếm và trigger tự động cập nhật trường thời gian chỉnh sửa.

---

## 2. Mô tả Kỹ thuật

### 2.1. Cài đặt các bảng dữ liệu
Nạp tệp cấu trúc [`schema.sql`](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/schema.sql) vào PostgreSQL để tạo lập 21 bảng thuộc các nhóm chức năng chính:
* **Danh mục:** `stations`, `trains`, `seat_types`, `fare_classes`.
* **Hành trình & Sức chứa:** `trips`, `segments`, `seats`, `segment_capacities`.
* **Tồn kho & Vé đặt:** `segment_inventory`, `bookings`, `od_products`, `od_product_segments`.
* **Nhu cầu & Gợi ý:** `search_logs`, `gap_combinations`.
* **Đầu ra AI & Tối ưu:** `demand_forecasts`, `bid_prices`, `quotas`.
* **Chính sách & Định giá:** `price_policies`, `price_quotes`.
* **Kiểm toán:** `audit_logs`.

### 2.2. Chỉ mục Tối ưu hóa (Indexes)
Thiết lập 5 index để tăng tốc độ truy vấn:
1. `ux_bid_prices_active` (Partial Unique Index trên `bid_prices(segment_id, seat_type)` khi `is_active = TRUE`).
2. `ux_quotas_active` (Partial Unique Index trên `quotas(od_product_id)` khi `is_active = TRUE`).
3. `ix_search_logs_demand` (Index trên `search_logs(service_date, origin_station_id, destination_station_id, seat_type, searched_at)` để gom tải nhu cầu nhanh chóng).
4. `ix_od_product_segments_segment` (Index trên `od_product_segments(segment_id, od_product_id)` để tra chặng đi qua nhanh).
5. `ix_gap_combinations_lookup` (Index trên `gap_combinations(from_station_id, to_station_id, is_active)`).

### 2.3. Trigger tự động cập nhật `updated_at`
* Viết hàm PL/pgSQL `set_updated_at()` để tự động gán giá trị thời gian hiện tại (`CURRENT_TIMESTAMP`) cho trường `updated_at`.
* Đăng ký trigger `BEFORE UPDATE` cho 7 bảng vận hành chính: `calendar_features`, `trips`, `segment_capacities`, `segment_inventory`, `od_products`, `bookings`, `price_policies`.

---

## 3. Tiêu chí Chấp nhận (Acceptance Criteria)
* **AC1:** Toàn bộ 21 bảng được khởi tạo thành công trong cơ sở dữ liệu PostgreSQL mà không gặp lỗi cú pháp SQL.
* **AC2:** 5 index được đăng ký và hoạt động chính xác (thử nghiệm chèn bản ghi trùng lặp trên partial index `ux_bid_prices_active` sẽ bị DB chặn lại).
* **AC3:** Thử nghiệm cập nhật thông tin trong bảng `trips` hoặc `segment_inventory` làm thay đổi trường `updated_at` tự động mà không cần ứng dụng truyền tham số.
