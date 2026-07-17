# AI Log — Nhật ký sử dụng công cụ AI

Thư mục này lưu bằng chứng sử dụng công cụ AI trong quá trình phát triển dự án,
theo yêu cầu của Ban tổ chức:

> *"Với công cụ AI trực tuyến, hãy chia sẻ link phiên chat. Với công cụ desktop,
> hãy kèm các file phiên như `~/.claude/projects/<project>`, `~/.codex/sessions/`,
> hoặc thư mục tương đương, cùng ảnh chụp màn hình. BTC có thể yêu cầu thêm tài
> liệu nếu cần."*

## Nội dung

| Đường dẫn | Nội dung |
|---|---|
| [`tools-used.md`](tools-used.md) | Danh sách công cụ AI đã dùng + link phiên với công cụ trực tuyến |
| [`sessions/`](sessions/) | File phiên gốc (`.jsonl`) từ công cụ desktop |
| [`screenshots/`](screenshots/) | Ảnh chụp màn hình quá trình làm việc |
| `.secret-allowlist` | Hash các chuỗi đã review, dùng bởi bộ quét secret |

## Chỉ mục phiên

| File | Ngày | Công cụ | Nội dung chính |
|---|---|---|---|
| `2026-07-17-b20a6005.jsonl` | 17/07/2026 | Claude Code (Opus 4.8) | Cấu hình workspace theo chuẩn git repo: specs/, adrs/, planning/, tasks/, docs/ai-log/ dựa trên PRD |
| `2026-07-17-gemini-838552a4.jsonl` | 17/07/2026 | Gemini / Antigravity | Đồng bộ hóa tài liệu Specs, ADRs, Sprints, Tasks theo schema DB PostgreSQL mới |

## Cách xuất phiên

**Tự động.** `.claude/settings.json` khai báo một hook `Stop` chạy
`scripts/export_ai_log.sh` sau mỗi lượt trả lời của Claude Code (~140 ms). Bạn cứ
làm việc bình thường, bản trong repo tự cập nhật theo.

Hook nằm trong `settings.json` (được commit) chứ không phải `settings.local.json`,
để mọi thành viên dùng Claude Code đều tự động xuất phiên của mình — BTC yêu cầu
log của cả nhóm. Ai dùng công cụ khác thì hook thoát êm, không báo lỗi.

**Thủ công**, khi cần chủ động:

```bash
bash scripts/export_ai_log.sh
```

Script tự tìm thư mục phiên của Claude Code, **quét secret trước**, rồi mới copy
vào `sessions/` với tên `YYYY-MM-DD-<8 ký tự đầu id>.jsonl`.

> ⚠️ **Vẫn nên chạy tay một lần trước khi nộp bài.** Hook chạy *sau* mỗi lượt trả
> lời, nên phần cuối cùng của phiên — lượt trả lời chốt hạ — chưa kịp vào bản
> copy. Chạy tay một phát là đủ.

Nếu hook có vẻ không chạy: mở `/hooks` trong Claude Code một lần để nạp lại cấu
hình, hoặc khởi động lại. Claude Code chỉ theo dõi thư mục `.claude/` nếu nó đã
tồn tại lúc phiên bắt đầu.

## Vì sao có bước quét secret

File phiên ghi lại **toàn bộ** những gì diễn ra: mọi tin nhắn, mọi lệnh đã chạy,
mọi nội dung file đã đọc. Nếu trong lúc làm việc có ai dán API key vào chat, hoặc
agent đọc file `.env`, thì key đó nằm trong file phiên. Mà file phiên thì được
commit và gửi cho BTC — tức là key đi ra ngoài.

`scripts/scan_secrets.py` chặn việc đó: phát hiện định dạng key của OpenAI,
Anthropic, GitHub, AWS, Google, Slack, private key, và các dòng gán biến kiểu
`*_API_KEY=`, `*_SECRET=`, `*_TOKEN=`. Có key thì script **dừng, không copy gì cả**.

Hai chi tiết đáng lưu ý trong cách nó hoạt động:

**Ảnh dán vào chat được bóc ra trước khi quét.** Ảnh nằm trong file phiên dưới
dạng base64. Chuỗi base64 đủ dài chắc chắn sẽ tình cờ chứa mọi tiền tố key ta đi
tìm — một ảnh 250 KB là đủ để sinh ra `AIza…` một cách ngẫu nhiên. Quét thẳng
bằng `grep` sẽ báo động giả 100% số lần và nhanh chóng bị bỏ qua như tiếng chuông
báo cháy hỏng. Nên scanner parse JSON, vứt bỏ blob ảnh, chỉ quét phần văn bản.

**Chuỗi vô hại được bỏ qua bằng allowlist SHA-256.** Đôi khi file phiên chứa thứ
đúng định dạng key nhưng thật ra vô hại — key mẫu trong tài liệu, giá trị bịa
trong lúc test. Thay vì nới lỏng mẫu nhận diện (làm vậy là mở đường cho key thật
lọt qua), ta ghi **hash** của đúng chuỗi đó vào `.secret-allowlist`. Lưu hash chứ
không lưu giá trị — file allowlist nằm trong git, chép key thật vào đó thì chính
nó thành chỗ rò rỉ.

Thêm mục vào allowlist:

```bash
python3 scripts/scan_secrets.py <file.jsonl> --print-hashes
```

Review từng dòng. **Là key thật thì đi thu hồi key đó ngay, đừng thêm vào
allowlist.** Chỉ thêm thứ chắc chắn vô hại, kèm comment nói rõ vì sao.

## Riêng tư

File phiên chứa email và đường dẫn tuyệt đối trên máy người dùng. Repo này ở chế
độ nào thì cân nhắc theo chế độ đó — nếu chuyển sang public, đọc lại file phiên
một lượt trước khi đẩy lên.
