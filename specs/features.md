# Specs — Danh sách Tính năng & Yêu cầu Chức năng (Features)

Tài liệu này đặc tả chi tiết danh mục tính năng của hệ thống **SRRM**, được cập nhật để chỉ rõ cơ chế tương tác với cơ sở dữ liệu PostgreSQL.

---

## 1. KHỐI 1 — Dự báo & Phân tích Nhu cầu (Forecasting)

Phân hệ dự báo sử dụng dữ liệu lịch sử để dự kiến lượng cầu đi lại tiềm năng.

| Mã | Tên Yêu cầu | Tương tác Cơ sở Dữ liệu & Tiêu chí Nghiệm thu |
|---|---|---|
| **FR1.1** | Dự báo nhu cầu OD | Đọc dữ liệu lịch sử từ `bookings` và ghi nhận kết quả dự báo điểm/phân vị vào bảng `demand_forecasts` (`demand_point`, `demand_p10`, `demand_p50`, `demand_p90`). |
| **FR1.2** | Đặc trưng dự báo | Kết hợp thông tin từ bảng danh mục `stations`, `trains` và bảng đặc trưng lịch `calendar_features` (lễ, tết, thời tiết, sự kiện) làm đầu vào huấn luyện. |
| **FR1.3** | Giải kiểm duyệt nhu cầu | Sử dụng dữ liệu tìm kiếm từ `search_logs` với các bản ghi có trạng thái `result = 'sold_out'` hoặc `'no_result'` làm đầu vào cho thuật toán EM để khôi phục nhu cầu ẩn. |
| **FR1.4** | Đường cong đặt vé | Tính toán lượng vé đặt tích lũy theo thời gian đặt trước dựa trên trường `booked_at` của bảng `bookings`. |
| **FR1.5** | Cập nhật dự báo động | Tự động chạy lại quy trình dự báo theo lô (batch job) khi có thêm bản ghi mới trong `bookings` và `search_logs`. |
| **FR1.6** | Phân tích tải chặng | Truy vấn và tổng hợp chênh lệch giữa sức chứa gốc (`segment_capacities.capacity`) và tồn kho thực tế (`segment_inventory.remaining`) để tính toán lượng ghế đang sử dụng. |
| **FR1.7** | Trực quan heatmap tải | Sử dụng dữ liệu chặng liên tiếp từ `segments` và tồn kho thực tế từ `segment_inventory` để vẽ biểu đồ lưới màu sắc theo thời gian. |

---

## 2. KHỐI 2 — Tối ưu hóa phân bổ chỗ (Inventory Optimization)

Phân hệ tối ưu thực hiện bài toán DLP để phân bổ hạn ngạch bán vé hợp lý.

| Mã | Tên Yêu cầu | Tương tác Cơ sở Dữ liệu & Tiêu chí Nghiệm thu |
|---|---|---|
| **FR2.1** | Xác định hạn ngạch chỗ | Ghi đề xuất hạn ngạch vào bảng `quotas` dưới dạng `run_version` mới với cờ `is_active = FALSE`. |
| **FR2.2** | Kiểm soát bằng Bid Price | Khi có yêu cầu vé, Backend kiểm tra `bid_prices` hoạt động (`is_active = TRUE`) của toàn bộ các chặng đi qua (`od_product_segments`) để so sánh tổng chi phí cơ hội với giá vé. |
| **FR2.3** | Cập nhật Bid Price động | Khi chạy lại tối ưu hóa, thực hiện swap trạng thái nguyên tử: chuyển các bản ghi `bid_prices` và `quotas` của `run_version` cũ sang `is_active = FALSE` và set `is_active = TRUE` cho `run_version` mới trong 1 transaction. |
| **FR2.4** | Đề xuất tách đoạn | Đề xuất nhả/giữ chỗ được cập nhật qua việc thay đổi giá trị trong `quotas` hiện hành. |
| **FR2.5** | Ghép đoạn trống | Chạy thuật toán phát hiện khoảng trống vật lý trên ghế và ghi các phương án vé khuyến khích có thể bán bù vào bảng `gap_combinations`. |
| **FR2.6** | Gán ghế vật lý | Khi xác nhận đặt vé, gán khóa ngoại `seat_id` (trỏ đến bảng `seats`) vào bản ghi của khách trong bảng `bookings`, đảm bảo trạng thái ghế là `available`. |
| **FR2.7** | Gợi ý ghép đổi chỗ | Đọc sơ đồ chỗ trống chặng ngắn từ `segment_inventory` kết hợp với `seats` để gợi ý chuyển ghế dọc đường. |
| **FR2.8** | Trừ tồn kho & Giữ chỗ | **Quy trình Core Transaction:** Khi khách yêu cầu giữ chỗ (`status = 'held'`), Backend khóa dòng (`SELECT FOR UPDATE`) trên bảng `segment_inventory` của các chặng liên quan theo thứ tự ID tăng dần (tránh deadlock). Thực hiện trừ tồn kho nguyên tử (`remaining = remaining - 1`) và thêm bản ghi vào `bookings`. Hủy hold sau TTL (`expires_at`) sẽ cộng trả lại tồn kho. |

---

## 3. KHỐI 3 — Định giá động (Dynamic Pricing)

Tính toán mức giá bán tối ưu dựa trên chi phí cơ hội và độ co giãn nhu cầu.

| Mã | Tên Yêu cầu | Tương tác Cơ sở Dữ liệu & Tiêu chí Nghiệm thu |
|---|---|---|
| **FR3.1** | Đề xuất giá theo Bid Price | Tổng hợp chi phí cơ hội từ tổng các `bid_price` hiện hành của các chặng mà sản phẩm đi qua để làm cơ sở định giá. |
| **FR3.2** | Yếu tố định giá | Sử dụng thêm dữ liệu cự ly `distance_km` từ `od_products` và đặc trưng lịch từ `calendar_features`. |
| **FR3.3** | Phân hạng sản phẩm giá | Ánh xạ và cấu hình các hạng vé tương ứng với trường `fare_class` (FK trỏ tới `fare_classes.code`). |
| **FR3.4** | Giá phản ánh khan hiếm | Tự động tăng giá vé của luồng OD nếu một trong các chặng đi qua có `bid_prices.bid_price` tăng cao. |
| **FR3.5** | Điều tiết cầu liên tàu | Đề xuất điều chỉnh giá vé chéo giữa các chuyến tàu chạy cùng ngày (`trips`) để cân bằng tải. |
| **FR3.6** | Price Safeguards | Tra cứu chính sách từ `price_policies` để ép cứng trần/sàn (`min_price`, `max_price`, `max_step_change`). Ghi kết quả tính toán cuối cùng vào `price_quotes.final_price`. |
| **FR3.7** | Giải thích đề xuất giá | Ghi cấu trúc giải thích chi tiết dưới dạng JSON vào cột `price_quotes.explanation` để kết xuất trực quan trên UI. |

---

## 4. CHỨC NĂNG NỀN TẢNG (Cross-cutting)

| Mã | Tên Yêu cầu | Tương tác Cơ sở Dữ liệu & Tiêu chí Nghiệm thu |
|---|---|---|
| **FR4.1** | Dashboard Phân tích | Kết xuất giao diện từ việc join các bảng `trips`, `segments`, `segment_inventory`, `gap_combinations` và `search_logs`. |
| **FR4.2** | Mô phỏng chính sách | Cho phép Revenue Manager điều chỉnh các hệ số trong `price_policies`, chạy giả lập và so sánh sự thay đổi doanh thu dự kiến của `price_quotes` so với doanh thu thực tế ghi nhận tại `bookings`. |
| **FR4.3** | Cảnh báo tự động | Phát cảnh báo khi tồn kho `segment_inventory.remaining` tiệm cận mức 0 trước ngày đi quá nhanh. |
| **FR4.4** | Nhật ký kiểm toán | Mọi hoạt động can thiệp ghi đè của con người đều được lưu trữ đầy đủ tại `audit_logs` (ghi actor, action, trước/sau dạng JSON). |
| **FR4.5** | Vòng lặp phản hồi | Thiết lập chu kỳ tự động cập nhật: Dữ liệu mua bán mới (`bookings`) $\rightarrow$ Cập nhật dự báo (`demand_forecasts`) $\rightarrow$ Giải tối ưu DLP (`bid_prices` & `quotas`) $\rightarrow$ Cập nhật báo giá (`price_quotes`). |
