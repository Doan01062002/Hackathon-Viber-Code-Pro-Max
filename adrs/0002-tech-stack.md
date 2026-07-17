# ADR 0002 — Lựa chọn Công nghệ và Thư viện cho Hệ thống SRRM

## 1. Trạng thái
**ĐÃ ĐƯỢC PHÊ DUYỆT (APPROVED)**

---

## 2. Bối cảnh (Context)
Hệ thống SRRM cần tích hợp đa dạng các khối chức năng từ dự báo học máy, tối ưu toán học (quy hoạch tuyến tính), đến tác vụ AI tạo sinh (LLM Agent). Công nghệ được chọn phải:
1. Đảm bảo hiệu năng tính toán số học nhanh.
2. Cung cấp API có tính năng tự động tài liệu hóa (OpenAPI).
3. Giao diện mượt mà, trực quan, tải nhanh để trình diễn tốt trước ban giám khảo.

---

## 3. Quyết định về Công nghệ (Decision)

### 3.1. Frontend: Next.js 14 App Router + React + Tailwind CSS
* **Lý do:** Next.js 14 cung cấp Server-Side Rendering (SSR) giúp tối ưu hóa tải trang. Tailwind CSS cho phép phát triển giao diện hiện đại nhanh chóng. Cấu trúc feature-based giúp chia nhỏ các chức năng (như Chat, Dashboard) độc lập.

### 3.2. Backend: FastAPI (Python 3.11) + Uvicorn
* **Lý do:** FastAPI hỗ trợ cơ chế bất đồng bộ (asyncio) cực tốt, có hiệu năng cao tương đương Node.js/Go. Khả năng tự động sinh tài liệu Swagger UI giúp việc tích hợp API với Frontend rất thuận lợi. Dùng Python 3.11 cho phép gọi trực tiếp các thư viện AI và tối ưu hóa toán học.

### 3.3. Trợ lý AI (Agent): LangGraph + LangChain + Gemini/GPT-4o-mini
* **Lý do:** LangGraph cho phép xây dựng các Agent có trạng thái (stateful) tuần hoàn, phù hợp với các luồng tư duy phức tạp (phân tích, so sánh giá, đề xuất tham số tối ưu). `GPT-4o-mini` hoặc `Gemini` là các mô hình ngôn ngữ lớn có chi phí rẻ, tốc độ phản hồi nhanh.

### 3.4. Lõi Tối ưu hóa & Dự báo:
* **Tối ưu hạn ngạch (DLP):** Sử dụng **Google OR-Tools** (hoặc SciPy kết hợp bộ giải HiGHS). OR-Tools cung cấp các thuật toán giải quy hoạch tuyến tính và quy hoạch nguyên (Integer Programming) cực kỳ mạnh mẽ, ổn định và mã nguồn mở.
* **Gán ghế vật lý:** Cài đặt thuật toán **Interval Partitioning** trực tiếp bằng Python để đạt độ phức tạp tối ưu $O(M \log M)$ (với $M$ là số lượng vé đặt).
* **Dự báo nhu cầu:** Sử dụng **LightGBM / XGBoost** cho hồi quy Poisson (Poisson Regression) kết hợp với **Scikit-learn** để tiền xử lý đặc trưng.

### 3.5. Cơ sở dữ liệu: SQLite (MVP) / PostgreSQL (Production)
* **Lý do:** Dùng SQLite ở local để không yêu cầu cài đặt DB server phức tạp cho người dùng chạy thử. Cấu hình SQLAlchemy sẵn sàng để chuyển đổi sang PostgreSQL chỉ bằng việc thay đổi Connection String trong `.env`.

---

## 4. Hệ quả (Consequences)
* Cần kiểm soát thư viện Python trong `requirements.txt` chặt chẽ để tránh xung đột phiên bản.
* Đội ngũ phát triển cần nắm vững cả kỹ thuật lập trình toán học (Operations Research) lẫn lập trình AI/LLM.
