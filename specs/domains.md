# Specs — Phân tích Miền Nghiệp vụ (Domains)

Hệ thống **Smart Rail Revenue Management (SRRM)** được chia thành 4 miền nghiệp vụ chính. Tài liệu này đặc tả thuật ngữ, thực thể dữ liệu và mô hình thuật toán tương ứng cho từng miền.

---

## 1. Các Thực thể & Thuật ngữ Chung

* **Ga (Station):** Các điểm dừng đỗ của tàu dọc hành trình. Ký hiệu danh sách ga là $S_1, S_2, ..., S_N$.
* **Chặng (Leg - $\ell$):** Đoạn đường nối giữa hai ga dừng liên tiếp của tàu. Một hành trình tàu có $N$ ga sẽ có $N-1$ chặng.
* **Luồng OD (Origin - Destination):** Cặp ga đi ($O$) và ga đến ($D$) cụ thể của hành khách. Một luồng OD $j$ sẽ đi qua một tập hợp các chặng liên tiếp.
* **Ma trận Chặng-OD ($a_{\ell j}$):** Nhận giá trị $1$ nếu luồng OD $j$ đi qua chặng $\ell$, ngược lại nhận giá trị $0$.
* **Bid Price ($\pi_\ell$):** Chi phí cơ hội của một chỗ ngồi trên chặng $\ell$. Nó thể hiện doanh thu kỳ vọng lớn nhất bị mất đi nếu ta bán một chỗ trên chặng $\ell$ cho một yêu cầu vé chặng ngắn giá rẻ khác. Đây là mắt xích liên kết giữa miền Tối ưu hóa chỗ ngồi và miền Định giá động.

---

## 2. Miền 1: Dự báo & Phân tích Nhu cầu (Forecasting & Analytics)

Nhiệm vụ của miền này là ước lượng nhu cầu đi lại tiềm năng của hành khách cho từng luồng OD theo thời gian thực.

### Mô hình hóa và thuật toán:
* **Giải kiểm duyệt nhu cầu (Unconstraining):** 
  * *Vấn đề:* Dữ liệu bán vé lịch sử chỉ ghi lại số vé **đã bán**, không ghi lại nhu cầu thực tế nếu vé đã bị bán hết sớm hoặc bị chặn bán do chính sách hạn ngạch.
  * *Thuật toán:* Áp dụng thuật toán **Expectation-Maximization (EM)** hoặc **Double Exponential** để khôi phục phân phối nhu cầu thực tế (latent demand).
* **Mô hình Dự báo Điểm & Khoảng (Forecasting Model):**
  * *Phương pháp:* Sử dụng mô hình **Gradient Boosting (LightGBM/XGBoost)** hồi quy Poisson (vì dữ liệu mua vé là dữ liệu đếm) hoặc Negative Binomial để xuất ra phân phối nhu cầu tiềm năng cùng khoảng tin cậy.
* **Đường cong đặt vé (Booking Curve / Pickup):**
  * Ước lượng tiến độ đặt vé tích lũy theo số ngày đặt trước (lead time) nhằm dự báo lượng cầu cuối cùng (final demand).

---

## 3. Miền 2: Tối ưu Phân bổ Chỗ ngồi (Inventory Optimization)

Miền này giải bài toán phân phối chỗ ngồi hữu hạn của tàu cho các luồng OD khác nhau nhằm tối đa hóa tổng doanh thu toàn chuyến.

### Mô hình hóa và thuật toán:
* **Quy hoạch Tuyến tính Tất định (Deterministic Linear Program - DLP):**
  * *Hàm mục tiêu:* Tối đa hóa tổng doanh thu mong đợi từ tất cả các luồng OD:
    $$\max \sum_{j} f_j \cdot x_j$$
    Trong đó $f_j$ là giá vé của luồng OD $j$, và $x_j$ là số lượng vé đề xuất bán cho luồng $j$.
  * *Ràng buộc:* Sức chứa của từng chặng $\ell$ không được vượt quá giới hạn $c_\ell$:
    $$\sum_{j} a_{\ell j} \cdot x_j \le c_\ell \quad \forall \ell$$
  * *Xuất Bid Price:* Giá trị đối ngẫu (dual values) thu được từ các ràng buộc sức chứa chính là **Bid Price ($\pi_\ell$)** của chặng $\ell$.
* **Ghép đoạn trống (Gap Combining) & Tách đoạn (Segmenting):**
  * Phát hiện và ghép các đoạn trống xen kẽ của cùng một ghế vật lý để tạo thành một hành trình dài hơn có giá trị cao.
* **Gán ghế vật lý giảm phân mảnh (Physical Seat Assignment):**
  * Sử dụng thuật toán **Interval Partitioning** (Greedy hoặc tối ưu hóa CP-SAT) sắp xếp các booking không chồng lấn lên cùng một ghế vật lý thực tế, giảm thiểu tối đa số lượng ghế bị phân mảnh.

---

## 4. Miền 3: Định giá Động (Dynamic Pricing)

Dựa trên chi phí cơ hội thực tế thu được từ miền tối ưu, miền định giá thực hiện điều chỉnh mức giá vé phù hợp với quan hệ cung cầu tại thời điểm bán.

### Mô hình hóa và thuật toán:
* **Tính toán giá trị cơ sở (Opportunity Cost):**
  * Giá vốn cơ hội $c_j$ của luồng OD $j$ bằng tổng Bid Price của toàn bộ các chặng mà luồng này đi qua:
    $$c_j = \sum_{\ell} a_{\ell j} \cdot \pi_\ell$$
* **Công thức Markup tối ưu:**
  * *Với cầu co giãn hằng số $\epsilon$ ($\epsilon > 1$):* Áp dụng Markup Nhân:
    $$p_j^* = \frac{\epsilon}{\epsilon - 1} \cdot c_j$$
  * *Với cầu dạng mũ $\lambda(p) = \lambda_0 e^{-\alpha p}$:* Áp dụng Markup Cộng:
    $$p_j^* = c_j + \frac{1}{\alpha}$$
* **Ràng buộc kiểm soát (Ceiling & Floor Pricing):**
  * Áp cứng khoảng giá quy định: $p_{\min} \le p_j^* \le p_{\max}$.
  * Giới hạn bước nhảy biến động giá giữa hai lần cập nhật liên tiếp không vượt quá $\Delta_{\max}$ để bảo vệ trải nghiệm của hành khách.

---

## 5. Miền 4: Mô phỏng & Phê duyệt (Simulation & Auditing)

Cung cấp khả năng vận hành thử nghiệm trước khi áp dụng thực tế và ghi nhật ký kiểm toán.

### Phương pháp vận hành:
* **Phase 1: Backtesting (Kiểm thử lịch sử):** Mô phỏng lại chính sách AI trên tập dữ liệu lịch sử để so sánh trực quan các chỉ số doanh thu và hệ số sử dụng ghế với thực tế đã bán.
* **Phase 2: Shadow Mode (Chạy song song):** Nhận luồng yêu cầu vé thực tế từ hệ thống bán vé hiện tại, đưa ra khuyến nghị hạn ngạch và giá vé trên dashboard quản trị để kiểm tra độ ổn định và chính xác mà không tác động tới hệ thống thật.
* **Phê duyệt thủ công (Manual Override):** Cho phép Revenue Manager điều chỉnh tăng/giảm hạn ngạch hoặc ép một mức giá cụ thể khi có biến động bất thường ngoài phạm vi học của mô hình AI.
