# Công cụ AI đã sử dụng

Khai báo theo yêu cầu BTC. Cập nhật khi có công cụ mới hoặc phiên mới.

## Công cụ desktop (kèm file phiên)

| Công cụ | Phiên bản / Model | Dùng vào việc gì | File phiên |
|---|---|---|---|
| Claude Code | Opus 4.8 (1M context) | Cấu hình workspace, viết tài liệu docs/specs, docs/adrs, docs/planning, docs/tasks, script export AI log | [`sessions/2026-07-17-b20a6005.jsonl`](sessions/) |
| Gemini / Antigravity | Gemini 3.5 Flash (High) | Viết lại và đồng bộ tài liệu trong docs theo schema DB mới, viết script export AI log | [`sessions/2026-07-17-gemini-838552a4.jsonl`](sessions/) |

## Công cụ trực tuyến (kèm link phiên chat)

| Công cụ | Dùng vào việc gì | Link phiên |
|---|---|---|
| — | *(chưa dùng — điền vào đây nếu có)* | — |

> **Nếu bạn dùng ChatGPT / Claude.ai / Gemini web:** tạo link chia sẻ phiên chat
> và dán vào bảng trên. Trên ChatGPT: nút Share ở góc trên bên phải. Trên
> Claude.ai: menu ⋯ → Share.

## Ảnh chụp màn hình

Bỏ ảnh vào [`screenshots/`](screenshots/), đặt tên theo dạng
`YYYY-MM-DD-<mô-tả-ngắn>.png` để đọc chỉ mục biết ngay ảnh chụp gì.

| Ảnh | Ngày | Nội dung |
|---|---|---|
| *(chưa có)* | | |

## Phạm vi sử dụng AI trong dự án

Ghi trung thực để BTC đánh giá đúng — phần nào AI làm, phần nào người làm:

| Hạng mục | Mức độ dùng AI |
|---|---|
| PRD (`docs/prd_duong_sat.md`) | *(cần điền)* |
| Tài liệu workspace (`docs/specs`, `docs/adrs`, `docs/planning`, `docs/tasks`) | Claude Code soạn dựa trên PRD, người review |
| Script `export_ai_log.sh`, `scan_secrets.py` | Claude Code viết và kiểm thử |
| Mã nguồn `ai/`, `backend/`, `frontend/` | *(cần điền)* |
| Mô hình dự báo / tối ưu | *(cần điền)* |
