# Specs — Yêu cầu Dữ liệu (Data Requirements)

Tài liệu này đặc tả chi tiết các yêu cầu về dữ liệu đầu vào và đầu ra của hệ thống **SRRM**, đồng thời ánh xạ trực tiếp sang các bảng PostgreSQL tương ứng.

---

## 1. Dữ liệu Đầu vào (Input Data Requirements)

Để các mô hình AI dự báo và tối ưu hoạt động chính xác, Backend cần chuẩn bị các nguồn dữ liệu đầu vào sau:

### 1.1. Lịch sử giao dịch đặt vé (Booking History)
* **Mục đích:** Huấn luyện mô hình dự báo lượng cầu tích lũy (Booking Curve) và khôi phục nhu cầu thật.
* **Bảng tương ứng:** `bookings`
* **Thông tin yêu cầu:** 
  * `booking_code` (Mã đặt vé duy nhất).
  * `booked_price` (Giá vé đã thanh toán thực tế).
  * `booked_at` (Thời điểm thực hiện đặt vé).
  * `status` (Trạng thái giao dịch: `confirmed` cho vé thành công, `cancelled` cho vé đã hủy).
  * `seat_id` (Liên kết với ghế vật lý cụ thể tại bảng `seats` để phân tích phân mảnh chặng).

### 1.2. Nhật ký tìm kiếm của khách hàng (Search Logs/Demand)
* **Mục đích:** Phân tích nhu cầu tiềm năng chưa chuyển đổi (phục vụ thuật toán unconstraining EM).
* **Bảng tương ứng:** `search_logs`
* **Thông tin yêu cầu:**
  * `searched_at` (Thời điểm khách tìm kiếm).
  * `origin_station_id`, `destination_station_id` (Cặp ga đi/đến tìm kiếm).
  * `seat_type` (Loại chỗ yêu cầu).
  * `service_date` (Ngày đi mong muốn).
  * `result` (Kết quả tìm kiếm: `found` - tìm thấy chỗ, `sold_out` - hết chỗ chặng, `no_result` - không có tàu chạy).

### 1.3. Đặc trưng Lịch & Sự kiện ngoài (Contextual Features)
* **Mục đích:** Cung cấp đặc trưng ngữ cảnh cho mô hình dự báo nhu cầu học máy.
* **Bảng tương ứng:** `calendar_features`
* **Thông tin yêu cầu:**
  * `service_date` (Ngày chạy tàu).
  * `is_holiday` / `is_tet` (Biến boolean xác định ngày lễ lớn, Tết Nguyên Đán).
  * `season` (Mùa cao điểm/thấp điểm du lịch).
  * `weather` (Thông tin thời tiết: mưa, nắng, bão).
  * `local_event` (Sự kiện văn hóa/thể thao tại địa phương có ga dừng).

### 1.4. Sơ đồ chỗ & Sức chứa vật lý (Capacity & Seats)
* **Mục đích:** Đặt ràng buộc sức chứa cho bài toán tối ưu DLP và gán ghế vật lý.
* **Bảng tương ứng:** `seats`, `segment_capacities`, `segment_inventory`
* **Thông tin yêu cầu:**
  * `capacity` (Tổng số ghế vật lý khả dụng theo chặng × loại chỗ).
  * `remaining` (Số ghế còn trống sống tại thời điểm giao dịch).
  * `coach_no`, `seat_no` (Ký hiệu toa và số ghế vật lý cụ thể trong bảng `seats`).

---

## 2. Dữ liệu Đầu ra (Output Data Requirements)

Các module AI và bộ tối ưu tính toán và xuất ra các kết quả sau để lưu trữ có phiên bản vào PostgreSQL:

### 2.1. Kết quả Dự báo Nhu cầu (Demand Forecasts)
* **Bảng tương ứng:** `demand_forecasts`
* **Thông tin yêu cầu:**
  * `demand_point` (Nhu cầu điểm trung bình dự báo cho luồng OD).
  * `demand_p10`, `demand_p50`, `demand_p90` (Ước lượng phân vị để tính toán an toàn tồn kho).
  * `forecast_at` (Thời điểm chạy mô hình).
  * `lead_days` (Số ngày đặt trước ngày chạy tàu).

### 2.2. Chi phí Cơ hội & Hạn ngạch Tối ưu (Bid Prices & Quotas)
* **Bảng tương ứng:** `bid_prices`, `quotas`
* **Thông tin yêu cầu:**
  * `bid_price` (Chi phí cơ hội $\pi_\ell$ của từng chặng nhỏ liên tiếp).
  * `quota` (Số lượng vé tối đa khuyến nghị bán cho luồng OD cụ thể).
  * `run_version` (Phiên bản chạy tối ưu DLP).
  * `is_active` (Cờ boolean đánh dấu phiên hoạt động hiện hành).

### 2.3. Báo giá Động đề xuất (Price Quotes)
* **Bảng tương ứng:** `price_quotes`
* **Thông tin yêu cầu:**
  * `opportunity_cost` (Tổng chi phí cơ hội của lộ trình bằng sum active `bid_prices`).
  * `proposed_price` (Mức giá tối ưu do thuật toán đề xuất).
  * `final_price` (Mức giá cuối cùng sau khi đi qua bộ lọc trần/sàn của `price_policies`).
  * `explanation` (Dữ liệu giải trình JSONB chứa cấu trúc markup và chính sách được áp dụng).

### 2.4. Gợi ý lấp khoảng trống (Gap Combinations Cache)
* **Bảng tương ứng:** `gap_combinations`
* **Thông tin yêu cầu:**
  * `seat_id` (Ghế vật lý phát hiện khoảng trống).
  * `from_station_id`, `to_station_id` (Ga bắt đầu và kết thúc khoảng trống).
  * `suggested_od_product_id` (Mã sản phẩm OD khuyến nghị bán khuyến mại để lấp đầy).
