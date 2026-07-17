# ADR 0002 — Lựa chọn Công nghệ và Thư viện cho Hệ thống SRRM

## 1. Trạng thái
**ĐÃ ĐƯỢC PHÊ DUYỆT (APPROVED)**

---

## 2. Bối cảnh (Context)
Hệ thống SRRM xử lý đồng thời lượng giao dịch lớn bao gồm giữ chỗ, mua vé, tìm kiếm và tối ưu hóa tồn kho chặng đường. Để đảm bảo tính toàn vẹn dữ liệu giao dịch trong môi trường nhiều người dùng đồng thời và tránh các xung đột tranh chấp ghế, chúng ta cần một hệ quản trị cơ sở dữ liệu mạnh mẽ hỗ trợ khóa dòng và xử lý giao dịch ACID nghiêm ngặt.

---

## 3. Quyết định về Công nghệ (Decision)

### 3.1. Cơ sở dữ liệu: PostgreSQL 15+
Thay vì các CSDL nhẹ dạng file như SQLite, hệ thống chọn **PostgreSQL** làm cơ sở dữ liệu vận hành duy nhất của SRRM MVP vì các tính năng sau:
1. **Khóa dòng tồn kho giao dịch (`SELECT FOR UPDATE`):** Phục vụ cơ chế trừ tồn kho chặng (`segment_inventory.remaining`). Lớp Backend khóa các dòng segment theo ID tăng dần để ngăn ngừa deadlock khi có nhiều luồng đặt vé đồng thời trên các chặng giao nhau.
2. **Partial Unique Index:** Sử dụng index có điều kiện (`ux_bid_prices_active` và `ux_quotas_active`) để quản lý snapshot phiên bản tối ưu. Điều này cho phép lưu trữ lịch sử tất cả các phiên `run_version`, nhưng bảo đảm chỉ có duy nhất một phiên hoạt động (`is_active = TRUE`) cho mỗi thực thể tại một thời điểm.
3. **Kiểu dữ liệu JSONB:** Lưu trữ hiệu quả các cấu trúc dữ liệu không cố định như `price_quotes.explanation` (diễn giải định giá của AI) và `audit_logs.before_data`/`after_data` (lịch sử thay đổi cấu hình).
4. **Trigger Function:** Cấu hình function `set_updated_at()` và các trigger `BEFORE UPDATE` chạy trực tiếp ở DB để bảo đảm trường `updated_at` luôn tự động cập nhật chính xác, không phụ thuộc vào ứng dụng.

### 3.2. Frontend: Next.js 14 App Router + React + Tailwind CSS
* Cấu trúc feature-based tách biệt hoàn toàn logic của các tính năng Chat, Dashboard và Simulation.

### 3.3. Backend: FastAPI (Python 3.11) + SQLAlchemy + Uvicorn
* SQLAlchemy làm ORM để giao tiếp với PostgreSQL, hỗ trợ các cơ chế transactional block và row locking (`with_for_update`).

### 3.4. Trợ lý AI (Agent): LangGraph + LangChain + Gemini/GPT-4o-mini
* Cấu hình LangGraph nodes kết nối qua state graph cho agent phân tích ngôn ngữ tự nhiên.

### 3.5. Bộ giải Toán học & Dự báo:
* **Tối ưu hạn ngạch (DLP):** Dùng **Google OR-Tools** (HiGHS solver) để tính toán tối ưu tuyến tính từ ma trận `od_product_segments`.
* **Dự báo nhu cầu:** Sử dụng **LightGBM / XGBoost** Poisson regression để huấn luyện mô hình dự báo phân phối nhu cầu đi lại tiềm năng.

---

## 4. Hệ quả (Consequences)
* Cần cài đặt và cấu hình PostgreSQL server khi chạy thử nghiệm local (được cấu hình sẵn thông qua Docker Compose).
* Backend service phải tuân thủ nghiêm ngặt quy tắc khóa chặng theo thứ tự ID để tránh deadlock.
