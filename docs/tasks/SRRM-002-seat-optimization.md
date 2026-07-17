# Task — SRRM-002: Xây dựng Bộ tối ưu DLP & Gán ghế vật lý

## 1. Mục tiêu
Phát triển lõi tối ưu hóa phân bổ chỗ ngồi sử dụng Quy hoạch tuyến tính tất định (DLP) dựa trên cơ sở dữ liệu PostgreSQL. Đồng thời xây dựng thuật toán gán số ghế vật lý giảm phân mảnh tồn kho và ghi nhận các phương án ghép khoảng trống ghế.

---

## 2. Mô tả Nghiệp vụ & Kỹ thuật

### 2.1. Lập trình Quy hoạch Tuyến tính DLP (Google OR-Tools)
* **Bài toán:** Quyết định số lượng vé $x_j$ bán cho từng luồng OD $j$ trên đoàn tàu có sức chứa chặng $\ell$ là $c_\ell$.
* **Mô hình toán:**
  * *Hàm mục tiêu:* $\max \sum_{j} f_j \cdot x_j$ (với $f_j$ là giá vé luồng $j$, $x_j$ là biến số lượng vé bán).
  * *Ràng buộc sức chứa chặng:* $\sum_{j} a_{\ell j} \cdot x_j \le c_\ell \quad \forall \ell$
    * Sức chứa chặng $c_\ell$ được lấy từ bảng `segment_capacities.capacity`.
    * Ma trận hệ số chặng-OD $a_{\ell j}$ được đọc trực tiếp từ bảng liên kết `od_product_segments`.
  * *Ràng buộc nhu cầu:* $0 \le x_j \le \hat{D}_j$ (với $\hat{D}_j$ là nhu cầu dự báo từ bảng `demand_forecasts.demand_point`).
* **Xuất Bid Price & Quotas:**
  * Giá trị đối ngẫu thu được từ các ràng buộc sức chứa là **Bid Price ($\pi_\ell$)** của chặng $\ell$.
  * Số lượng vé tối ưu $x_j$ chính là hạn ngạch chỗ (**Quota**) của sản phẩm OD $j$.
* **Lưu kết quả (Transaction Swap):**
  * Ghi kết quả mới vào `bid_prices` và `quotas` kèm theo mã phiên `run_version` với `is_active = FALSE`.
  * Mở một transaction, cập nhật toàn bộ các bản ghi của phiên cũ thành `is_active = FALSE`, cập nhật phiên mới thành `is_active = TRUE` (được bảo vệ bởi partial unique index `ux_bid_prices_active` và `ux_quotas_active`), sau đó commit.

### 2.2. Thuật toán Gán ghế Vật lý & Ghép chặng trống
* **Gán ghế vật lý:** Khi khách mua vé thành công, chạy thuật toán gán ghế thực tế tại bảng `seats` để liên kết `bookings.seat_id`, đảm bảo không chồng lấn chặng (`od_product_segments`) với các khách hàng khác trên cùng ghế đó.
* **Ghép chặng trống (Gap Combinations):**
  * Chạy tiến trình quét tìm các khoảng trống ghế vật lý của từng ghế trong chuyến tàu.
  * Nếu phát hiện ghế có khoảng trống giữa hai ga (không chồng lấn với booking nào khác), ghi gợi ý bán vé chặng ngắn bù vào bảng `gap_combinations` kèm `suggested_od_product_id` để tối ưu hóa việc lấp đầy.

---

## 3. Các thành phần mã nguồn liên quan
* `ai/src/ai/nodes/optimization.py` [MODIFY]: Node tối ưu trong LangGraph.
* `ai/src/ai/tools/dlp_solver.py` [MODIFY]: Thư viện gọi OR-Tools giải DLP và xuất bid price.
* `backend/src/backend/services/optimize_service.py` [NEW]: Lớp service điều phối transaction lưu trữ kết quả và swap trạng thái `is_active`.
* `ai/tests/test_optimization.py` [MODIFY]: Test bộ giải DLP và bộ gán ghế.

---

## 4. Tiêu chí Chấp nhận (Acceptance Criteria)
* **AC1:** Bộ giải DLP tính toán chính xác và xuất ra danh sách Bid Price cùng Quotas.
* **AC2:** Quy trình swap phiên hoạt động `is_active = TRUE` trong transaction chạy an toàn, rollback toàn bộ nếu có bất kỳ lỗi ghi DB nào xảy ra.
* **AC3:** Thuật toán gán ghế vật lý hoạt động chính xác $100\%$ không xảy ra chồng lấn ghế vật lý trên các chặng giao nhau.
* **AC4:** Các cơ hội lấp chỗ trống được quét đầy đủ và lưu chính xác vào bảng `gap_combinations`.
