# Task — SRRM-003: Lập trình lõi Định giá Động & Bộ lọc Ràng buộc Trần/Sàn

## 1. Mục tiêu
Xây dựng công thức tính toán giá vé đề xuất động dựa trên chi phí cơ hội chặng (tổng Bid Price) và độ co giãn cầu. Tích hợp lớp kiểm soát cứng (Ceiling/Floor) từ bảng chính sách của PostgreSQL và lưu nhật ký báo giá chi tiết.

---

## 2. Mô tả Nghiệp vụ & Kỹ thuật

### 2.1. Công thức Định giá động
* **Chi phí cơ hội chặng:** Với mỗi luồng OD $j$ đi qua các chặng $\ell$, Backend tính toán chi phí cơ hội cơ sở $c_j$ bằng cách truy vấn tổng `bid_price` của các chặng đó đang có cờ `is_active = TRUE`:
  $$c_j = \sum_{\ell \in \text{od\_product\_segments}} \pi_\ell$$
* **Giá đề xuất tối ưu $p_j^*$:**
  * Áp dụng markup nhân hoặc markup cộng dựa trên hệ số độ co giãn cầu và chi phí cơ hội chặng.
  * Mức giá đề xuất sẽ tự động tăng cao khi tàu đi qua các chặng đang khan hiếm (Bid Price cao) và giảm giá về sát giá cơ bản ở chặng thấp điểm (Bid Price = 0).

### 2.2. Bộ lọc Ràng buộc cứng (Policy Guard)
Mức giá vé sau khi tối ưu phải được đưa qua lớp bảo vệ lấy cấu hình từ bảng `price_policies` (FK trỏ tới `od_product_id` đang có hiệu lực trong khoảng `valid_from` đến `valid_to` và có trạng thái `status = 'active'`):
1. **Ràng buộc trần/sàn:** Giá vé cuối cùng phải nằm trong khoảng:
   $$\text{price\_policies.min\_price} \le p_{\text{final}} \le \text{price\_policies.max\_price}$$
2. **Giới hạn tốc độ tăng giá:** Giá trị tăng/giảm so với giá bán gần nhất không được vượt quá `price_policies.max_step_change`.
3. **Chống đầu cơ:** Đảm bảo giá vé cố định cho một phiên giữ chỗ và không tăng giá dựa trên tần suất tìm kiếm của cùng một người dùng.

### 2.3. Nhật ký Báo giá & Giải trình (Price Quotes)
* Lưu trữ toàn bộ kết quả tính toán vào bảng `price_quotes`.
* Cột `explanation` kiểu JSONB sẽ chứa thông tin giải trình chi tiết: tổng chi phí cơ hội, hệ số markup được áp dụng, và các chính sách bảo vệ đã được kích hoạt (ví dụ: `{"base_opportunity_cost": 350000.0, "applied_policies": ["MIN_PRICE_ENFORCED"]}`).

---

## 3. Các thành phần mã nguồn liên quan
* `ai/src/ai/nodes/pricing.py` [MODIFY]: Node định giá trong LangGraph, tính toán đề xuất.
* `backend/src/backend/services/pricing_service.py` [NEW]: Lớp service trong Backend thực hiện truy vấn `price_policies`, áp dụng Price Safeguards và ghi nhận bản ghi vào `price_quotes`.
* `ai/tests/test_pricing.py` [MODIFY]: Test kiểm tra công thức định giá và đảm bảo tuân thủ chính sách giá.

---

## 4. Tiêu chí Chấp nhận (Acceptance Criteria)
* **AC1:** Tính toán chi phí cơ hội chính xác dựa trên sum các `bid_price` hoạt động (`is_active = TRUE`).
* **AC2:** Đạt $100\%$ không vi phạm ràng buộc trần/sàn của `price_policies` hoạt động (vi phạm KPI K6).
* **AC3:** Mỗi kết quả báo giá đều được lưu vết chi tiết vào bảng `price_quotes` kèm trường `explanation` JSONB đầy đủ cấu trúc.
