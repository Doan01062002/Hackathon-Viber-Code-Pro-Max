# ADR 0001 — Lựa chọn Kiến trúc Hệ thống Monorepo có Ràng buộc Cứng

## 1. Trạng thái
**ĐÃ ĐƯỢC PHÊ DUYỆT (APPROVED)**

---

## 2. Bối cảnh (Context)
Dự án Smart Rail Revenue Management (SRRM) tham gia vòng thi Vietnam Innovation Challenge 2026 yêu cầu:
1. Phát triển nhanh chóng, tích hợp mượt mà giữa Giao diện (Next.js), REST API (FastAPI) và Trợ lý AI tối ưu (LangGraph).
2. Dễ dàng triển khai chạy thử nghiệm trên máy cá nhân hoặc đóng gói Docker Compose mà không mất thời gian cấu hình mạng phức tạp.
3. Đảm bảo mã nguồn không bị "rã" (spaghetti code) khi dự án phình to. Khối AI/Optimization phải độc lập để có thể chạy thử trong môi trường phân tích dữ liệu (Jupyter Notebook, CLI batch job) mà không phụ thuộc vào giao thức HTTP.

---

## 3. Các Phương án Xem xét (Options Considered)

* **Phương án A: Kiến trúc Microservices rời rạc (Decoupled Services)**
  * *Mô tả:* Tách riêng frontend, backend, và AI thành 3 service chạy trên 3 cổng mạng độc lập, giao tiếp qua REST API/gRPC.
  * *Ưu điểm:* Độc lập hoàn toàn, dễ scale riêng biệt.
  * *Nhược điểm:* Phức tạp trong việc setup local, gặp trễ mạng (latency) giữa Backend và AI, khó debug chéo.
* **Phương án B: Monorepo gọi trực tiếp trong Process (Monorepo with In-process Import - Được chọn)**
  * *Mô tả:* Tổ chức mã nguồn trong một repository duy nhất. Module `ai` được viết như một thư viện Python chuẩn, module `backend` import trực tiếp `ai` để gọi hàm. Đồng thời áp dụng script kiểm soát ranh giới phụ thuộc (`check_boundaries.sh`) ở mức CI để ngăn chặn Backend chọc sâu vào cấu trúc nội bộ của AI và ngược lại.

---

## 4. Quyết định (Decision)
**Lựa chọn Phương án B.** 
* Dự án được chia thành 3 thư mục gốc: `/frontend`, `/backend`, và `/ai`.
* `backend` và `ai` chia sẻ chung môi trường virtualenv để đơn giản hóa cài đặt.
* `backend` chỉ import `ai` thông qua interface duy nhất được định nghĩa tại `ai/src/ai/__init__.py` -> `run_agent()`.
* Cấm tuyệt đối `ai` import bất kỳ thứ gì từ `backend`.
* Cấm mọi file của `backend` ngoại trừ lớp nghiệp vụ `services/` import module `ai`.

---

## 5. Hệ quả (Consequences)
* **Tích cực:**
  * Setup môi trường cực kỳ nhanh (chỉ cần chạy một script `setup.sh` là xong toàn bộ).
  * Hiệu năng gọi AI agent tối ưu hóa và dự báo là cực nhanh do chạy trong cùng bộ nhớ RAM, không tốn chi phí kết nối HTTP.
  * Việc bảo trì biên giới phụ thuộc được tự động hóa.
* **Tiêu cực:**
  * Cần cấu hình Dockerfile cẩn thận (vì ảnh Docker của backend cần copy cả mã nguồn của thư mục `ai/` ở bên ngoài để build thư viện).
