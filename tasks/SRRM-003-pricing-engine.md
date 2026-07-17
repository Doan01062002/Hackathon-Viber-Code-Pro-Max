# Task — SRRM-003: Lập trình lõi Định giá Động & Bộ lọc Ràng buộc Trần/Sàn

## 1. Mục tiêu
Xây dựng công thức tính toán giá vé đề xuất động dựa trên chi phí cơ hội chặng (tổng Bid Price) và độ co giãn cầu. Tích hợp lớp kiểm soát cứng (Ceiling/Floor) và giới hạn biến động giá để bảo đảm tuân thủ quy định đường sắt.

---

## 2. Mô tả Nghiệp vụ & Kỹ thuật

### 2.1. Công thức Định giá động
* **Chi phí cơ hội chặng:** Với mỗi luồng OD $j$ đi qua tập hợp chặng $L_j$, chi phí cơ hội là $c_j = \sum_{\ell \in L_j} \pi_\ell$. Đây là mức giá tối thiểu hệ thống chấp nhận bán vé (giá sàn cơ sở để không bị lỗ chi phí cơ hội).
* **Giá đề xuất tối ưu $p_j^*$:**
  * *Mô hình cầu dạng mũ:* $p_j^* = c_j + \frac{1}{\alpha}$, trong đó $\alpha$ là tham số độ nhạy cảm giá của phân khúc khách hàng.
  * Mức giá đề xuất sẽ tự động tăng cao khi tàu đi qua các chặng "cháy vé" (Bid Price $\pi$ cao) và giảm giá về sát giá cơ bản ở chặng thấp điểm ($\pi = 0$).

### 2.2. Bộ lọc Ràng buộc cứng (Price Safeguards)
Để bảo vệ quyền lợi khách hàng và uy tín doanh nghiệp đường sắt, mức giá $p_j^*$ sau khi tính toán tối ưu phải đi qua bộ lọc ràng buộc:
1. **Ràng buộc trần/sàn:** $p_{\min} \le p_j^* \le p_{\max}$. Các giá trị trần và sàn được cấu hình sẵn theo từng chặng và loại chỗ.
2. **Giới hạn tốc độ tăng giá:** Giá vé của cùng một loại chỗ trên cùng một chuyến không được tăng đột ngột quá $\Delta_{\max}$ (ví dụ: tối đa $15\%$ mỗi lần cập nhật).
3. **Chống đầu cơ:** Không tăng giá dựa trên tần suất tìm kiếm của cùng một người dùng (giữ nguyên tắc công bằng xã hội).

### 2.3. Lõi Giải trình (Explainable Pricing)
* Hệ thống sinh ra chuỗi văn bản tiếng Việt giải thích lý do cấu thành mức giá (ví dụ: *"Giá vé đề xuất là 520,000đ, tăng 15% so với giá cơ sở do chặng Vinh - Huế đang có nhu cầu rất cao, chi phí cơ hội chặng tăng lên 120,000đ"*).

---

## 3. Các thành phần mã nguồn liên quan
* `ai/src/ai/nodes/pricing.py` [NEW]: Node định giá trong LangGraph.
* `ai/src/ai/tools/pricing_calculator.py` [NEW]: Hàm tính giá vé động và áp ràng buộc bảo vệ.
* `ai/tests/test_pricing.py` [NEW]: Test kiểm tra công thức định giá và đảm bảo không vi phạm trần/sàn.

---

## 4. Tiêu chí Chấp nhận (Acceptance Criteria)
* **AC1:** Giá vé đề xuất cho các luồng OD qua chặng quá tải tăng tương ứng với mức tăng Bid Price của chặng đó.
* **AC2:** Đạt $100\%$ không vi phạm ràng buộc trần/sàn trong mọi trường hợp thử nghiệm đầu vào (vi phạm KPI K6).
* **AC3:** Hệ thống sinh ra giải trình tiếng Việt rõ ràng, logic cấu trúc dễ hiểu cho Revenue Manager trên dashboard.
