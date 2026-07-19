# Vé ghép chặng — API và hướng dẫn migration

Cập nhật: 2026-07-19

## 1. Migration

`booking_groups` và `booking_group_items` đã có sẵn trong `schema.sql:160-191`, nên
DB tạo mới từ `schema.sql` không cần làm gì thêm. Script
`scripts/migrate_booking_groups.sql` chỉ dành cho DB đã provision từ trước (ví dụ RDS).

Script chỉ gồm `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`,
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS` và một trigger có guard. Nó **không**
đụng tới bảng nào đang có dữ liệu.

### Điều kiện tiên quyết

Các thứ sau phải tồn tại trước khi chạy: bảng `bookings`, `gap_combinations`,
`trips`, `stations`, và hàm `set_updated_at()`.

### Cách chạy

Máy dev hiện không có `psql`. Chạy bằng Python (driver `psycopg` v3 đã có trong `.venv`):

```bash
.venv/bin/python - <<'PY'
import re
from pathlib import Path
import psycopg

url = next(l.split('=',1)[1].strip() for l in Path('.env').read_text().splitlines()
           if l.startswith('DATABASE_URL='))
url = url.strip().strip('"').strip("'")               # .env bọc giá trị trong dấu nháy
url = re.sub(r'^postgresql\+\w+://', 'postgresql://', url)   # bỏ driver của SQLAlchemy

with psycopg.connect(url, autocommit=True) as conn, conn.cursor() as cur:
    cur.execute(Path('scripts/migrate_booking_groups.sql').read_text())
PY
```

Nếu có `psql` thì tương đương:

```bash
psql "$DATABASE_URL" -f scripts/migrate_booking_groups.sql
```

### Kiểm tra sau khi chạy

```sql
select table_name from information_schema.tables
where table_schema='public' and table_name in ('booking_groups','booking_group_items');

select indexname from pg_indexes
where tablename in ('booking_groups','booking_group_items');

select tgname from pg_trigger where tgname='trg_booking_groups_updated_at';
```

Kỳ vọng: 2 bảng, 7 index, 1 trigger.

### Trạng thái AWS RDS

Đã chạy trên `viber_coding_pro_max` ngày 2026-07-19. Trước đó hai bảng chưa tồn tại.
Sau migration: 2 bảng + 7 index + trigger `trg_booking_groups_updated_at`.
`demand_forecasts` (48.312 dòng) và `bookings` (470.488 dòng) giữ nguyên.

> **Không chạy test suite backend trên RDS dùng chung.** Test tích hợp xóa dữ liệu
> `demand_forecasts` và sẽ làm hỏng Khối 1. Test chạy trên Postgres local/Docker.

## 2. API

Tất cả đường dẫn có tiền tố `/api/v1`. Định nghĩa schema ở
`backend/src/backend/views/combined_booking_view.py`.

### GET /booking/combined-options

Tìm các phương án ghép chặng.

| Tham số | Bắt buộc | Mặc định | Ghi chú |
|---|---|---|---|
| `origin` | có | | mã ga đi |
| `destination` | có | | mã ga đến |
| `service_date` | có | | `YYYY-MM-DD` |
| `seat_type` | không | | lọc theo loại chỗ |
| `max_transfers` | không | 2 | 1–3 |

Trả về `{ origin_code, destination_code, service_date, options[] }`. Mỗi option có
`option_key`, `transfer_count`, `seat_change_count`, `estimated_total_price`, và `legs[]`.

**`transfer_count` là số lần CHUYỂN, không phải số chặng.** Số chặng là `legs.length`.
Một phương án 2 chặng có `transfer_count = 1`.

**`keep_previous_seat` của chặng đầu luôn là `false`** vì không có chặng trước để giữ chỗ.
Đừng coi đó là một lần đổi chỗ — dùng helper `isSeatChange()` ở
`frontend/src/features/booking/hooks/combinedState.ts`.

### POST /booking/combined

Giữ chỗ cả nhóm. Body: `{ gap_combination_ids: number[] (2–4), channel?: string }`.

Trả 201 kèm `group_code`, `total_price`, `expires_at`, và `legs[]` (mỗi chặng có
`booking_code` riêng). Trả 400 nếu chỗ đã bị người khác đặt hoặc vượt quota.

`expires_at` do server tính bằng `MIN(booking.expires_at)`. Client phải hiển thị lại
giá trị này, **không** tự đếm ngược 15:00 — nếu không hai bên sẽ lệch.

### GET /booking/combined/{group_code}

Tra cứu nhóm vé. Trả 404 nếu không tồn tại.

### POST /booking/combined/{group_code}/confirm

Xác nhận nhóm vé đang giữ. Trả 400 nếu đã quá `expires_at`.

Nguyên tử: `get_db` commit một lần ở cuối request và rollback khi có exception
(`backend/src/backend/database.py:27`), nên nếu một chặng hỏng thì cả nhóm rollback —
không có chuyện đặt thành công một phần.

### POST /booking/combined/{group_code}/cancel

Hủy toàn bộ nhóm. Mỗi chặng được chuyển sang `cancelled`, tồn kho chặng cộng lại,
và `gap_combinations` bật lại để thuật toán ghép chặng tái sử dụng.

Trả về tiền hoàn từng chặng kèm bậc áp dụng. Trả 400 nếu nhóm đã `cancelled`/`refunded`.

### POST /booking/combined/{group_code}/legs/{sequence_no}/refund

Hoàn một chặng. Các chặng còn lại giữ nguyên hiệu lực và nhóm vẫn `confirmed`;
nhóm chỉ đóng khi không còn chặng nào hiệu lực.

### Chính sách hoàn tiền

Định nghĩa ở `backend/src/backend/services/refund_policy.py`, tính theo giờ khởi hành
của **từng chặng** (chặng cuối hành trình dài có thể còn xa giờ chạy trong khi chặng
đầu đã sát giờ).

| Thời điểm hủy | Hoàn |
|---|---|
| Trước giờ chạy > 24h | 90% |
| Trước giờ chạy 4–24h | 70% |
| Trước giờ chạy < 4h | 50% |
| Sau giờ chạy | 0% |

Vé mới giữ chỗ chưa thanh toán thì hủy không phát sinh hoàn.

PRD không quy định các con số này — chúng là giá trị tạm theo thông lệ đường sắt VN,
sửa ở `REFUND_TIERS` khi có quyết định chính thức.

### Tự động giải phóng chỗ quá hạn

`backend/src/backend/services/expiry_task.py` chạy vòng lặp asyncio gọi
`release_expired_bookings` mỗi 60 giây, khởi động cùng app qua lifespan.

| Config | Mặc định | Ý nghĩa |
|---|---|---|
| `RELEASE_EXPIRED_ENABLED` | `true` | Tắt trong test và môi trường serverless |
| `RELEASE_EXPIRED_INTERVAL_SECONDS` | `60` | 10–3600 |

Service đồng bộ nên vòng lặp gọi qua `asyncio.to_thread` để không chặn event loop.
Lỗi DB một chu kỳ được log và bỏ qua, vòng lặp không chết.

Trên Vercel (serverless, mỗi request một tiến trình) vòng lặp nền không sống đủ lâu —
đặt `RELEASE_EXPIRED_ENABLED=false` và dùng cron gọi
`POST /api/v1/booking/release-expired`.

## 3. Luồng frontend

```
BookingScreen
  └── useCombinedBooking()          state machine + đếm ngược
        ├── CombinedJourneyMap      sơ đồ hành trình (khu vực chính)
        └── CombinedBookingPanel    cột phải
              ├── CombinedOptionList   chọn phương án
              └── CombinedHoldPanel    đếm ngược + xác nhận
```

Trạng thái: `idle → searching → options → holding → held → confirming → confirmed`,
cộng `expired` và lỗi. Logic thuần nằm ở `combinedState.ts`, có test ở
`combinedState.test.ts` (22 test).

Sau khi xác nhận, chuyển tới `/ticket-details?groupCode=...`.
Trang chi tiết phân biệt `?code=` (vé thường) và `?groupCode=` (vé ghép).

## 4. Ghi chú kiểm thử

### Đã chạy thật trên RDS (2026-07-19)

Luồng đầy đủ `tìm → giữ chỗ → xác nhận → chi tiết → hủy` chạy thông với nhóm 3 chặng
`Da Nang → Quang Ngai → Nha Trang → Sai Gon`. Sau khi hủy: cả 3 vé `cancelled`,
`gap_combinations` đã bật lại, `demand_forecasts` giữ nguyên 48.312 dòng.

### Lỗi quota đã sửa

Trước đó `combined-options` trả về phương án mà `POST /booking/combined` từ chối bằng
`400 ... đã vượt quá hạn ngạch (quota) tối đa là 0 vé`, vì truy vấn tìm kiếm không lọc
theo `quotas`. Đã thêm điều kiện soi đúng luật của `BookingService.create_hold`
(lấy dòng quota active mới nhất, so với số vé `held`/`confirmed`; không có dòng quota
nghĩa là không giới hạn). Đây là thứ chặn toàn bộ luồng đặt vé gộp.

### Chưa kiểm chứng được

**Bậc hoàn tiền chưa chạy với số tiền khác 0.** Toàn bộ `service_date` trong seed data
là năm 2024, tức đã quá giờ chạy, nên mọi lần hủy đều rơi vào bậc "không hoàn". Các mốc
90/70/50% chỉ được phủ bởi unit test (`tests/test_refund_policy.py`), chưa quan sát
end-to-end. Muốn kiểm thật thì cần seed một chuyến có `service_date` ở tương lai.

**Test backend có DB chưa chạy được ở máy dev.** Docker không chạy nên không có
Postgres local. `test_refund_policy.py` và `test_expiry_task.py` là logic thuần nên
chạy được (16 test pass); các test còn lại cần CI hoặc `docker compose up db`.
