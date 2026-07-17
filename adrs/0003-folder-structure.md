# ADR 0003 — Quy chuẩn Tổ chức Thư mục Workspace Context-Centric

## 1. Trạng thái
**ĐÃ ĐƯỢC PHÊ DUYỆT (APPROVED)**

---

## 2. Bối cảnh (Context)
Trong một dự án monorepo có sự tham gia sâu sắc của các AI Coding Agent, việc sắp xếp tài liệu và mã nguồn một cách khoa học giúp:
1. AI dễ dàng tìm kiếm và đọc hiểu ngữ cảnh (context) dự án mà không cần quét toàn bộ repository.
2. Bản đồ hóa các tài liệu nghiệp vụ đi kèm với các mã hóa tác vụ cụ thể để dễ dàng quản lý tiến độ.
3. Người dùng mới tham gia dự án có thể nắm bắt nhanh cấu trúc mà không phải đọc rời rạc từng file.

---

## 3. Quyết định (Decision)
Thống nhất cấu hình thư mục workspace theo mô hình **Context-Centric** (như mô tả trong hình vẽ hướng dẫn):

```
├── /specs                  # Đặc tả sản phẩm & Nghiệp vụ (Single Source of Truth)
├── /adrs                   # Tài liệu ghi nhận các Quyết định Kiến trúc (ADRs)
├── /planning               # Kế hoạch phát triển, Product Backlog & Sprints
│   └── /sprints            # Chi tiết từng Sprint
├── /tasks                  # Các file đặc tả chi tiết từng tác vụ (User Stories)
├── /src                    # Mã nguồn chính (chia thành frontend/, backend/, ai/)
├── /docs                   # Tài liệu bổ sung, sơ đồ kiến trúc vật lý, runbooks
├── AGENTS.md               # Quy tắc phối hợp giữa lập trình viên & AI
├── README.md               # Giới thiệu dự án và hướng dẫn chạy nhanh
└── .gitignore              # Quy tắc loại trừ tệp tin của Git
```

### Nguyên tắc quản lý:
1. **Liên kết vết (Traceability):** Mỗi file tác vụ trong `/tasks` phải trỏ ngược về một yêu cầu chức năng (FR) cụ thể trong `/specs/features.md`.
2. **Quy tắc đặt tên:** 
  * Các file ADR đặt tên theo thứ tự tăng dần: `0001-...md`, `0002-...md`.
  * Các file Sprint đặt tên theo số hiệu: `sprint-01.md`, `sprint-02.md`.
  * Các file tác vụ đặt tên theo mã tác vụ dự án: `SRRM-[ID]-[tên_tác_vụ].md`.

---

## 4. Hệ quả (Consequences)
* **Tích cực:**
  * Giảm đáng kể số lượng token AI phải đọc do cấu trúc thư mục phân tách rõ rệt.
  * Tăng tính minh bạch và khả năng kiểm toán quy trình phát triển.
* **Tiêu cực:**
  * Đội ngũ phát triển phải duy trì thói quen viết cập nhật tài liệu khi có thay đổi kiến trúc hoặc nghiệp vụ.
