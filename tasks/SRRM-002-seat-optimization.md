# Task — SRRM-002: Xây dựng Bộ tối ưu DLP & Gán ghế vật lý

## 1. Mục tiêu
Phát triển lõi tối ưu hóa phân bổ chỗ ngồi sử dụng Quy hoạch tuyến tính tất định (DLP) nhằm tối đa hóa doanh thu toàn chuyến. Đồng thời xây dựng thuật toán gán số ghế vật lý giảm phân mảnh tồn kho chặng nhỏ và hỗ trợ ghép các đoạn trống.

---

## 2. Mô tả Nghiệp vụ & Kỹ thuật

### 2.1. Lập trình Quy hoạch Tuyến tính DLP (Google OR-Tools)
* **Bài toán:** Quyết định số lượng vé $x_j$ bán cho từng luồng OD $j$ trên đoàn tàu có sức chứa chặng $\ell$ là $c_\ell$.
* **Mô hình toán:**
  * *Hàm mục tiêu:* $\max \sum_{j} f_j \cdot x_j$ (với $f_j$ là giá vé luồng $j$, $x_j$ là biến số lượng vé bán).
  * *Ràng buộc sức chứa chặng:* $\sum_{j} a_{\ell j} \cdot x_j \le c_\ell \quad \forall \ell$
  * *Ràng buộc nhu cầu:* $0 \le x_j \le \hat{D}_j$ (với $\hat{D}_j$ là nhu cầu dự báo từ Task SRRM-001).
* **Xuất Bid Price:** Sau khi bộ giải (HiGHS hoặc GLOP qua OR-Tools) giải xong bài toán tuyến tính, ta lấy giá trị đối ngẫu (dual variables) tương ứng với các ràng buộc sức chứa chặng. Giá trị này chính là **Bid Price ($\pi_\ell$)** của chặng $\ell$.

### 2.2. Thuật toán Gán ghế Vật lý (Interval Partitioning)
* **Vấn đề:** Khi hành khách đặt vé chặng ngắn, hệ thống phải chỉ định một số ghế vật lý cụ thể (ví dụ: Toa 2 Ghế 15) sao cho không chồng chéo hành trình với khách khác trên cùng ghế đó, đồng thời không chiếm chỗ của khách đi chặng dài tương lai.
* **Thuật toán:**
  * Sắp xếp các yêu cầu đặt vé theo thứ tự ga đi tăng dần.
  * Với mỗi yêu cầu, duyệt tìm ghế vật lý đầu tiên đang trống trên toàn bộ các chặng thuộc hành trình của yêu cầu đó (Best-Fit hoặc First-Fit trên khoảng ga).
  * Nếu không tìm thấy ghế trống liền mạch, hệ thống sẽ đề xuất đổi ghế giữa chặng (nếu được cấu hình cho phép) hoặc từ chối đặt vé nếu vượt quá sức chứa chặng của DLP.

---

## 3. Các thành phần mã nguồn liên quan
* `ai/src/ai/nodes/optimization.py` [NEW]: Node chạy tối ưu hóa trong LangGraph.
* `ai/src/ai/tools/dlp_solver.py` [NEW]: Thư viện gọi OR-Tools giải DLP và xuất bid price.
* `ai/src/ai/tools/seat_allocator.py` [NEW]: Cài đặt thuật toán gán ghế vật lý (Interval Partitioning).
* `ai/tests/test_optimization.py` [NEW]: Test độ chính xác của bộ giải DLP và bộ gán ghế.

---

## 4. Tiêu chí Chấp nhận (Acceptance Criteria)
* **AC1:** Bộ giải DLP tính toán ra kết quả phân bổ hạn ngạch tối ưu và xuất ra danh sách Bid Price tương ứng cho mỗi chặng.
* **AC2:** Thuật toán gán ghế vật lý hoạt động chính xác $100\%$ không xảy ra chồng lấn ghế (cùng một ghế vật lý bị gán cho 2 hành khách đi chung một chặng).
* **AC3:** Thời gian chạy toàn bộ luồng DLP và gán ghế cho 1 đoàn tàu 10 toa (khoảng 600 ghế) không vượt quá 1 giây trên môi trường kiểm thử.
