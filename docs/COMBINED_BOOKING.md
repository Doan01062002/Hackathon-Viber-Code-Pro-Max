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

## 4. Vấn đề đã biết

**`combined-options` trả về phương án mà `POST /booking/combined` từ chối.**

Trên dữ liệu RDS hiện tại, `DAN → SGO` ngày `2024-01-02` trả 10 phương án, nhưng cả 10
đều bị từ chối khi giữ chỗ:

```
400 Sản phẩm OD (ID 344) đã vượt quá hạn ngạch (quota) tối đa là 0 vé
```

`search_options` không lọc theo `quotas.quota`, nên nó chào những phương án không thể
đặt được. Có 104 quota đang active bằng 0.

Cách sửa: thêm điều kiện `quota > 0` vào truy vấn trong
`backend/src/backend/services/combined_booking_service.py`. Thuộc phạm vi backend
(sub-project B), chưa làm trong đợt này.

Frontend đã xử lý đúng lỗi này: `HOLD_FAILURE` đưa user về danh sách phương án kèm
thông báo, danh sách không bị mất.
