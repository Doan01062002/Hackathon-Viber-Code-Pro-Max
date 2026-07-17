# Task — SRRM-001: Phát triển Mô hình Dự báo Nhu cầu OD & EM Algorithm

## 1. Mục tiêu
Thiết lập module dự báo nhu cầu đi lại tiềm năng của hành khách giữa các ga đi - ga đến (Origin-Destination - OD) từ dữ liệu lịch sử trong PostgreSQL. Tích hợp thuật toán EM (Expectation-Maximization) để loại bỏ sai lệch dữ liệu do tình trạng hết chỗ (censored data/unconstraining).

---

## 2. Mô tả Nghiệp vụ & Kỹ thuật

### 2.1. Giải thuật Unconstraining (Thuật toán EM)
* **Dữ liệu đầu vào:** 
  * Số lượng vé đã bán thực tế từ bảng `bookings` (lọc các giao dịch có trạng thái `confirmed`).
  * Số lượt tìm kiếm không thỏa mãn từ bảng `search_logs` (lọc các bản ghi có `result = 'sold_out'` hoặc `'no_result'`).
* **Thuật toán EM:** 
  * Giả định nhu cầu đặt vé hàng ngày tuân theo phân phối Poisson với tham số đặt vé tích lũy $\lambda$.
  * E-step: Tính kỳ vọng lượng đặt vé tiềm năng bị ẩn đi tại các thời điểm chặng bị hết chỗ (dựa trên tham số $\lambda$ hiện tại và điều kiện lượng đặt vé $\ge$ sức chứa còn lại).
  * M-step: Cập nhật lại tham số $\lambda$ để tối đa hóa hàm hợp lý. Lặp lại cho đến khi hội tụ.

### 2.2. Mô hình dự báo Poisson Regression
* Sử dụng mô hình Gradient Boosting (LightGBM) với objective Poisson.
* **Đầu vào đặc trưng (Features):**
  * Đặc trưng lịch từ bảng `calendar_features` (`is_holiday`, `is_tet`, `season`, `weather`, `local_event`).
  * Số ngày đặt trước (`lead_days`).
  * Chi tiết sản phẩm từ bảng `od_products` (ga đi, ga đến, loại chỗ `seat_type`, giá cơ sở `base_price`).
* **Đầu ra dự báo:** 
  * Lưu trữ kết quả dự báo có phiên bản vào bảng `demand_forecasts`.
  * Các trường lưu trữ gồm: `demand_point` (dự báo điểm), `demand_p10`, `demand_p50`, `demand_p90` (các phân vị của phân phối nhu cầu để làm đầu vào cho tối ưu hóa an toàn tồn kho).

---

## 3. Các thành phần mã nguồn liên quan
* `ai/src/ai/nodes/forecasting.py` [MODIFY]: Node xử lý dự báo trong LangGraph, tiếp nhận snapshot dữ liệu đầu vào.
* `ai/src/ai/tools/demand_unconstraining.py` [MODIFY]: Hàm thuật toán EM cho dữ liệu lịch sử.
* `ai/tests/test_forecasting.py` [MODIFY]: Unit tests cho thuật toán EM và mô hình dự báo.

---

## 4. Tiêu chí Chấp nhận (Acceptance Criteria)
* **AC1:** Hàm EM unconstraining chạy ổn định, khôi phục lượng cầu tiềm năng khi đối chiếu với dữ liệu giả lập bị cắt.
* **AC2:** Mô hình LightGBM dự báo nhu cầu OD trên tập test lịch sử đạt sai số MAPE trung bình $\le 15\%$ đối với các cặp OD chính.
* **AC3:** Dữ liệu dự báo được ghi chính xác vào bảng `demand_forecasts` trong PostgreSQL (tuân thủ ràng buộc `demand_p10 <= demand_p50 <= demand_p90`).
