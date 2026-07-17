# ADR 0005 — Cô lập Luồng dữ liệu AI và Quản lý Snapshot Tối ưu

## 1. Trạng thái
**ĐÃ ĐƯỢC PHÊ DUYỆT (APPROVED)**

---

## 2. Bối cảnh (Context)
Các thuật toán AI dự báo, tối ưu DLP và định giá động cần đọc lượng lớn dữ liệu (sức chứa chặng, lịch sử booking, đặc trưng lịch) và sinh ra hàng ngàn dòng dữ liệu đầu ra (`demand_forecasts`, `bid_prices`, `quotas`). Nếu cho phép module AI trực tiếp kết nối và ghi dữ liệu vào cơ sở dữ liệu vận hành:
1. Sẽ phá vỡ ranh giới monorepo (AI phụ thuộc vào CSDL và transaction layer của Backend).
2. Dễ gây ra lỗi dữ liệu dở dang (partial write) nếu tiến độ chạy thuật toán bị ngắt quãng giữa chừng hoặc gặp lỗi LLM.
3. Rất khó viết unit test hoặc chạy replay lại thuật toán (backtesting) độc lập mà không cần dựng kết nối DB thật.

---

## 3. Quyết định (Decision)
Thống nhất quy tắc thiết kế cô lập dữ liệu AI:
1. **AI chạy hoàn toàn in-memory:** Module `ai/` nhận đầu vào dưới dạng cấu trúc dữ liệu Python nguyên thủy (dict, list, dataclass) và trả về kết quả tương tự. AI cấm hoàn toàn việc import thư viện DB (`psycopg2`, `SQLAlchemy`) hoặc thực thi câu lệnh SQL trực tiếp.
2. **Backend chuẩn bị dữ liệu đầu vào:** Lớp service của Backend có trách nhiệm truy vấn dữ liệu từ PostgreSQL, đóng gói thành snapshot sạch và truyền cho hàm `run_agent()` hoặc hàm nghiệp vụ tương ứng của AI.
3. **Quản lý phiên bản ghi đè nguyên tử (Atomic Swap):**
   * Kết quả do AI tính toán được Backend ghi vào các bảng `bid_prices` và `quotas` dưới dạng trạng thái không hoạt động (`is_active = FALSE`) kèm mã phiên `run_version`.
   * Khi ghi thành công toàn bộ lô dữ liệu, Backend mở giao dịch chuyển toàn bộ dòng phiên cũ sang `is_active = FALSE` và bật phiên mới thành `is_active = TRUE`. Điều này bảo đảm các request báo giá song song luôn đọc được phiên bản nhất quán, không bao giờ đọc phải trạng thái lai giữa hai phiên bản.

---

## 4. Hệ quả (Consequences)
* **Tích cực:**
  * Thuật toán AI hoàn toàn tách biệt, dễ dàng kiểm thử cô lập bằng mock data hoặc chạy trên file CSV lịch sử trong Jupyter Notebook mà không cần cấu hình PostgreSQL.
  * Đảm bảo tính toàn vẹn dữ liệu: Không bao giờ xảy ra lỗi ghi thiếu bid price hoặc quota của chặng đường do tiến trình AI gặp sự cố.
* **Tiêu cực:**
  * Backend service phải gánh thêm phần logic quản lý transaction swap và đóng gói snapshot đầu vào.
