# Specs — Phân tích Miền Nghiệp vụ (Domains)

Hệ thống **Smart Rail Revenue Management (SRRM)** được xây dựng xung quanh thiết kế cơ sở dữ liệu PostgreSQL gồm 21 bảng. Tài liệu này đặc tả chi tiết thuật ngữ nghiệp vụ và cách ánh xạ sang mô hình dữ liệu thực tế.

---

## 1. Mô hình hóa Chặng và Luồng đi lại (Topology & OD Matrix)

* **Ga (Station):** Lưu tại bảng `stations` (mã ga duy nhất `code`, thứ tự hiển thị `display_order`).
* **Chuyến tàu theo ngày (Trip):** Lưu tại bảng `trips` (mã tàu `train_id`, ngày chạy `service_date`).
* **Chặng liên tiếp (Segment - $\ell$):** Lưu tại bảng `segments`. Một hành trình tàu được chia thành các chặng nhỏ nối giữa hai ga dừng liên tiếp (được đánh số thứ tự `sequence_no` tăng dần).
* **Sản phẩm chặng đi–đến (Origin-Destination Product - $j$):** Lưu tại bảng `od_products`. Định nghĩa các cặp ga lên/xuống, loại chỗ (`seat_type`) và hạng giá (`fare_class`).
* **Ma trận Chặng-OD ($a_{\ell j}$):** Được materialize (lưu trữ vật lý) tại bảng nối nhiều-nhiều `od_product_segments`. Nếu sản phẩm OD $j$ đi qua chặng $\ell$, một bản ghi tương ứng sẽ được lưu tại đây. Giúp tính toán chi phí cơ hội nhanh chóng mà không cần suy luận lại lộ trình trên mỗi request.

---

## 2. Miền 1: Dự báo & Phân tích Nhu cầu (Forecasting & Analytics)

Nhiệm vụ của miền này là ước lượng nhu cầu đặt vé tiềm năng từ phía hành khách.

```
[search_logs] + [bookings] (Lịch sử) ──> [EM Algorithm] ──> [LightGBM] ──> [demand_forecasts]
```

### Mô hình hóa và bảng liên quan:
* **Giải kiểm duyệt nhu cầu (Unconstraining):** Sử dụng thuật toán **Expectation-Maximization (EM)**. Nhu cầu thực tế được khôi phục bằng cách kết hợp số vé bán thành công (`bookings`) và số lượt tìm kiếm thất bại do hết chỗ (`search_logs` với `result = 'sold_out'`).
* **Đặc trưng lịch:** Bảng `calendar_features` cung cấp thông tin theo ngày (`service_date`): lễ tết (`is_holiday`, `is_tet`), mùa vụ (`season`), thời tiết (`weather`), sự kiện (`local_event`) để làm đặc trưng cho mô hình.
* **Đầu ra dự báo:** Lưu tại bảng `demand_forecasts`. Dự báo được tính theo phiên (`forecast_at`) và số ngày đặt trước (`lead_days`), chứa cả dự báo điểm (`demand_point`) và các phân vị phân phối (`demand_p10`, `demand_p50`, `demand_p90`).

---

## 3. Miền 2: Tối ưu Phân bổ Chỗ ngồi (Inventory Optimization)

Nhiệm vụ của miền này là kiểm soát số lượng ghế khả dụng để tối đa hóa doanh thu chặng dài và hạn chế ghế trống cục bộ chặng ngắn.

```
[segment_capacities] 
[segment_inventory]   ──> [DLP Optimizer (OR-Tools)] ──> [bid_prices] + [quotas] (run_version)
[demand_forecasts]
```

### Mô hình hóa và bảng liên quan:
* **Quy hoạch Tuyến tính DLP:** Tối đa hóa doanh thu dựa trên sức chứa của `segment_capacities` và nhu cầu từ `demand_forecasts`.
* **Quản lý Phiên bản (Snapshot Management):** 
  * Kết quả tối ưu được ghi vào `bid_prices` (chi phí cơ hội của chặng $\pi_\ell$) và `quotas` (hạn ngạch chỗ được phân bổ cho luồng OD) kèm theo mã phiên tính toán `run_version`.
  * Tránh xung đột ghi dở dang bằng cách lưu phiên mới với `is_active = FALSE`, sau đó thực hiện hoán đổi nguyên tử (`is_active = TRUE`) trong một transaction.
* **Gán ghế vật lý & Tránh phân mảnh:**
  * Khách đặt vé được gán ghế thực tế tại bảng `seats`.
  * Bộ quét chạy batch phát hiện các chặng trống liền kề của cùng một ghế để tạo gợi ý bán vé bù tại bảng `gap_combinations`, giúp tối ưu hóa hệ số lấp đầy.

---

## 4. Miền 3: Định giá Động (Dynamic Pricing)

Tính toán mức giá bán vé tối ưu cho từng yêu cầu tìm kiếm, bảo đảm các điều kiện trần/sàn pháp lý.

```
[bid_prices] (active) ──> Tính Opportunity Cost ──> Markup tối ưu ──> [price_policies] (Guard) ──> [price_quotes]
```

### Mô hình hóa và bảng liên quan:
* **Chi phí cơ hội (Opportunity Cost - $c_j$):** Được tính bằng cách sum các `bid_price` hiện hành (`is_active = TRUE`) của các chặng cấu thành nên lộ trình OD:
  $$c_j = \sum_{\ell \in \text{od\_product\_segments}} \pi_\ell$$
* **Policy Guard (Bộ lọc chính sách):** Tra cứu từ bảng `price_policies` để đảm bảo giá vé nằm trong khung `min_price` và `max_price`, đồng thời bước tăng giá so với lịch sử không vượt quá `max_step_change`.
* **Nhật ký báo giá:** Mỗi lượt báo giá được ghi nhận tại bảng `price_quotes` (lưu proposed price, final price, decision và JSON giải trình `explanation`). Khi khách hàng thanh toán mua vé, booking tại `bookings` sẽ liên kết trực tiếp với báo giá này để chốt giá vé không đổi.

---

## 5. Miền 4: Mô phỏng, Phê duyệt & Kiểm toán (Simulation & Auditing)

Phục vụ việc chạy thử nghiệm, shadow mode và lưu vết hoạt động can thiệp thủ công.

### Mô hình hóa và bảng liên quan:
* **Shadow Mode:** Hệ thống lấy luồng tìm kiếm thực tế lưu vào `search_logs`, gọi AI tính toán giá vé tối ưu, sau đó lưu báo giá vào `price_quotes` với trạng thái `decision = 'accepted'` hoặc `'blocked'` để Revenue Manager kiểm tra độ ổn định mà không làm thay đổi giá bán thật.
* **Kiểm toán (Auditing):** 
  * Toàn bộ thao tác điều chỉnh hạn ngạch thủ công, thay đổi cấu hình toa tàu, hoặc thay đổi chính sách giá trần/sàn của `price_policies` phải được ghi nhận tại bảng `audit_logs`.
  * Lưu trữ dữ liệu dạng JSONB (`before_data`, `after_data`) để dễ dàng so sánh cấu hình trước và sau khi thay đổi.
