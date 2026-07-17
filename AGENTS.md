# AGENTS.md — Quy tắc Hợp tác & Ràng buộc Kỹ thuật (AI & Team)

Tài liệu này định nghĩa "luật chơi" khi làm việc với AI và phát triển mã nguồn trong dự án **Smart Rail Revenue Management (SRRM)**. Cả con người và AI đều phải tuân thủ nghiêm ngặt để đảm bảo chất lượng codebase.

---

## 1. Ràng buộc Kiến trúc (Module Boundaries)

Dự án sử dụng cấu trúc Monorepo phân tách thành 3 module độc lập: `frontend/` (Next.js), `backend/` (FastAPI), và `ai/` (LangGraph). Ranh giới giữa các module được kiểm tra tự động và **cấm vi phạm**:

1. **`ai/` không được import `backend/`**:
   * Agent phải hoàn toàn độc lập với giao thức truyền thông (HTTP/REST) để có thể chạy trong CLI, Notebook hoặc batch job.
   * Lớp lõi agent chỉ trao đổi dữ liệu qua Python primitives và Dataclasses.
2. **Chỉ `backend/services/` được phép import `ai`**:
   * Không import `ai` trực tiếp từ Controller hoặc Model của Backend.
   * Lớp Service đóng vai trò là adapter/wrapper để chuyển đổi giữa mô hình nghiệp vụ của Backend và kết quả đầu ra của Agent.
3. **Frontend chỉ gọi API qua `lib/api/`**:
   * Không dùng `fetch()` hoặc thư viện HTTP client rải rác trong các component giao diện.
   * Mọi API call phải được định nghĩa trong `frontend/src/lib/api/` hoặc trong lớp API của từng feature tương ứng.

*Kiểm tra tự động bằng lệnh:* `make boundaries` (hoặc `bash scripts/check_boundaries.sh`).

---

## 2. Quy chuẩn Phát triển Code (Development Rules)

* **Không sử dụng code mẫu / placeholder**: Khi viết tính năng, đặc biệt là các thuật toán (như DLP, gán ghế, định giá), phải viết logic xử lý thật, có xử lý lỗi đầy đủ, không dùng comment kiểu `// TODO: implement later` hoặc `pass`.
* **Ràng buộc Kiểu dữ liệu (Type Safety)**:
  * Backend: Sử dụng Type Hints và validate input/output bằng Pydantic.
  * Frontend: Sử dụng TypeScript nghiêm ngặt, định nghĩa rõ ràng `interface` và `type`, không lạm dụng `any`.
  * AI: Định nghĩa chặt chẽ `AgentState` và kiểu dữ liệu trả về `AgentResult`.
* **Viết Test trước/song song**: Khi thêm controller hay thuật toán mới, bắt buộc phải viết Unit Test tương ứng trong thư mục `tests/`.

---

## 3. Quy trình Kiểm thử & Commit

Trước khi đề xuất commit hoặc hoàn thành một tác vụ, bắt buộc phải thực hiện kiểm tra chất lượng bằng bộ lệnh sau:

```bash
make check
```

Lệnh này chạy tự động ba bước:
1. `make test` — Đảm bảo tất cả unit tests của `ai/` và `backend/` đều pass.
2. `make lint` — Chạy `ruff` kiểm tra chất lượng python code và `eslint` cho frontend.
3. `make boundaries` — Đảm bảo không vi phạm ranh giới module.

---

## 4. Quản lý Tài liệu & Đồng bộ Context

* Mọi tài liệu nghiệp vụ tại `/specs` và các quyết định kiến trúc tại `/adrs` là nguồn sự thật duy nhất (Single Source of Truth).
* Khi thay đổi logic hoặc cấu trúc code, phải cập nhật lại tài liệu tương ứng để đảm bảo AI và con người luôn đọc cùng một context.
