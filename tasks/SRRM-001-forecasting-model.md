# Task — SRRM-001: Phát triển Mô hình Dự báo Nhu cầu OD & EM Algorithm

## 1. Mục tiêu
Thiết lập module dự báo nhu cầu đi lại tiềm năng của hành khách giữa các ga đi - ga đến (Origin-Destination - OD) từ dữ liệu lịch sử. Tích hợp thuật toán EM (Expectation-Maximization) để loại bỏ sai lệch dữ liệu do tình trạng hết chỗ (censored data/unconstraining).

---

## 2. Mô tả Nghiệp vụ & Kỹ thuật

### 2.1. Giải thuật Unconstraining (Thuật toán EM)
* **Vấn đề:** Khi một chuyến tàu đã bán hết vé chặng A-B trước ngày đi 5 ngày, dữ liệu bán vé lịch sử ghi nhận lượng vé bán đứng yên (bằng sức chứa). Nhu cầu thực tế sau thời điểm đó bị ẩn đi (censoring). Nếu dùng trực tiếp dữ liệu này để dự báo, mô hình sẽ dự báo thấp hơn nhu cầu thực tế.
* **Giải pháp:** 
  1. Giả định nhu cầu đặt vé hàng ngày tuân theo phân phối Poisson với tham số $\lambda$.
  2. Bước **E-step**: Tính kỳ vọng của lượng đặt vé bị ẩn đi dựa trên tham số $\lambda$ hiện tại và điều kiện lượng đặt vé $\ge$ sức chứa còn lại.
  3. Bước **M-step**: Cập nhật lại tham số $\lambda$ tối đa hóa hàm hợp lý. Lặp lại cho đến khi hội tụ.

### 2.2. Mô hình dự báo Poisson Regression
* Sử dụng mô hình Gradient Boosting (LightGBM) với objective Poisson.
* **Đầu vào đặc trưng (Features):**
  * Ngày đi, thứ trong tuần, tháng, mùa vụ, ngày lễ Tết.
  * Khoảng thời gian từ lúc đặt vé đến ngày đi (Lead time).
  * Chiều chạy tàu (Nam - Bắc / Bắc - Nam).
  * Giá vé lịch sử.
* **Đầu ra:** Dự báo nhu cầu trung bình $\hat{D}_{j}$ và phương sai/khoảng tin cậy cho luồng OD $j$ tại ngày đi dự kiến.

---

## 3. Các thành phần mã nguồn liên quan
* `ai/src/ai/nodes/forecasting.py` [NEW]: Node xử lý dự báo trong LangGraph.
* `ai/src/ai/tools/demand_unconstraining.py` [NEW]: Hàm thuật toán EM cho dữ liệu lịch sử.
* `ai/tests/test_forecasting.py` [NEW]: Unit tests cho thuật toán EM và mô hình dự báo.

---

## 4. Tiêu chí Chấp nhận (Acceptance Criteria)
* **AC1:** Hàm EM unconstraining chạy ổn định, khôi phục lượng cầu tăng sau khi đạt điểm hết vé (kiểm tra qua unit test với dữ liệu giả lập bị cắt).
* **AC2:** Mô hình LightGBM dự báo nhu cầu OD trên tập test lịch sử đạt sai số MAPE trung bình $\le 15\%$ đối với các cặp OD có lượng khách lớn.
* **AC3:** API dự báo trả về phân phối xác suất nhu cầu (trị trung bình và khoảng tin cậy 95%) để cung cấp tham số cho bài toán tối ưu DLP.
