# Planning — Danh mục Yêu cầu Phát triển (Product Backlog)

Tài liệu này quản lý toàn bộ backlog phát triển của dự án **SRRM**, được cập nhật để bổ sung các tác vụ liên quan đến hạ tầng cơ sở dữ liệu PostgreSQL và quản lý giao dịch.

---

## EPIC 0 — Hạ tầng Cơ sở Dữ liệu & Giao dịch (Database)

* **SRRM-D1: Cấu hình PostgreSQL Schema & Triggers**
  * *Mô tả:* Khởi tạo 21 bảng trong PostgreSQL theo thiết kế [`schema.sql`](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/schema.sql). Cấu hình 5 index tường minh và 7 trigger tự động cập nhật trường `updated_at`.
  * *Độ ưu tiên:* Cao nhất (Blocker cho toàn bộ dự án)
* **SRRM-D2: Thiết lập Repository Layer & Row-Level Locking**
  * *Mô tả:* Lập trình SQLAlchemy Repository. Viết logic khóa dòng tồn kho (`SELECT FOR UPDATE` trên bảng `segment_inventory`) theo thứ tự ID tăng dần khi khách đặt vé. Viết worker giải phóng các booking held đã hết hạn (`expires_at`).
  * *Độ ưu tiên:* Cao nhất

---

## EPIC 1 — Khối Dự báo & Phân tích Nhu cầu (Forecasting)

* **SRRM-F1: Pipeline Tiền xử lý dữ liệu từ Database**
  * *Mô tả:* Đọc dữ liệu lịch sử đặt vé (`bookings`), nhật ký tìm kiếm (`search_logs`), và đặc trưng lịch (`calendar_features`) từ PostgreSQL.
  * *Độ ưu tiên:* Cao
* **SRRM-F2: Giải thuật Khôi phục Nhu cầu EM (Expectation-Maximization)**
  * *Mô tả:* Lập trình thuật toán khôi phục nhu cầu thực tế bằng cách unconstrain số vé bán với số lượt tìm kiếm thất bại (`result = 'sold_out'`).
  * *Độ ưu tiên:* Cao
* **SRRM-F3: Mô hình Dự báo Nhu cầu OD (LightGBM Regression)**
  * *Mô tả:* Huấn luyện mô hình dự báo và ghi kết quả dự báo điểm/phân vị vào bảng `demand_forecasts`.
  * *Độ ưu tiên:* Cao
* **SRRM-F4: Phân tích Tải chặng & Heatmap API**
  * *Mô tả:* Xây dựng API tổng hợp tải chặng từ việc join `segments` và `segment_inventory` để trả về dữ liệu vẽ Heatmap.
  * *Độ ưu tiên:* Trung bình

---

## EPIC 2 — Khối Tối ưu Phân bổ Chỗ (Inventory Optimization)

* **SRRM-O1: Xây dựng Lõi tối ưu Tuyến tính DLP (OR-Tools)**
  * *Mô tả:* Giải bài toán quy hoạch tuyến tính tối đa hóa doanh thu từ ma trận `od_product_segments` và `segment_capacities`.
  * *Độ ưu tiên:* Cao
* **SRRM-O2: Hoán đổi Phiên bản Tối ưu nguyên tử (Atomic Swap)**
  * *Mô tả:* Viết logic transaction ghi kết quả bid price đối ngẫu vào `bid_prices` và quotas vào `quotas` dưới dạng `run_version` mới, sau đó swap cờ `is_active = TRUE` một cách nguyên tử.
  * *Độ ưu tiên:* Cao
* **SRRM-O3: Thuật toán Gán ghế Vật lý (Interval Partitioning)**
  * *Mô tả:* Sắp xếp và gán mã ghế vật lý `seat_id` vào `bookings` khi giao dịch được xác nhận.
  * *Độ ưu tiên:* Cao
* **SRRM-O4: Phát hiện Khoảng trống Ghế (Gap Combinations Cache)**
  * *Mô tả:* Quét tìm các khoảng trống ghế vật lý dọc chặng và ghi gợi ý bán vé chặng ngắn bù vào bảng `gap_combinations` phục vụ tra cứu nhanh khi hết chỗ.
  * *Độ ưu tiên:* Trung bình

---

## EPIC 3 — Khối Định giá Động (Dynamic Pricing)

* **SRRM-P1: Công thức tính Giá động từ Bid Price**
  * *Mô tả:* Tính toán chi phí cơ hội của lộ trình bằng cách sum các `bid_price` hoạt động của các chặng cấu thành. Áp dụng hệ số markup.
  * *Độ ưu tiên:* Cao
* **SRRM-P2: Áp đặt Policy Guard**
  * *Mô tả:* Đọc chính sách từ `price_policies` và ép giá đề xuất nằm trong khoảng trần/sàn và giới hạn bước nhảy giá. Ghi nhật ký vào `price_quotes`.
  * *Độ ưu tiên:* Cao
* **SRRM-P3: Cơ chế Giải thích Đề xuất Giá**
  * *Mô tả:* Sinh JSON giải trình lý do tính giá lưu vào trường `price_quotes.explanation`.
  * *Độ ưu tiên:* Trung bình

---

## EPIC 4 — Tích hợp & Giao diện (Platform & UI)

* **SRRM-I1: Dashboard Quản trị Doanh thu**
  * *Mô tả:* UI hiển thị Heatmap tải chặng, ma trận nhu cầu và các cơ hội lấp khoảng trống từ `gap_combinations`.
  * *Độ ưu tiên:* Cao
* **SRRM-I2: Workspace Mô phỏng & So sánh chính sách**
  * *Mô tả:* Giao diện so sánh doanh thu chính sách giá mới cấu hình tại `price_policies` so với doanh thu lịch sử đã lưu tại `bookings`.
  * *Độ ưu tiên:* Cao
* **SRRM-I3: Nhật ký Kiểm toán (Audit Logs)**
  * *Mô tả:* Lưu vết toàn bộ hoạt động điều chỉnh của Revenue Manager vào bảng `audit_logs` để bảo đảm tính an toàn vận hành.
  * *Độ ưu tiên:* Trung bình
