# Hướng dẫn Ghép API — Khối 1: Dự báo

Tài liệu ghi lại quá trình ghép API Khối 1 (Dự báo) vào frontend, và là
**khuôn mẫu chuẩn** để ghép các API còn lại của hệ thống SRRM.

- Ngày: 2026-07-17
- Phạm vi: 2 endpoint của Khối 1 — `/forecast` và `/segments/load`.
- Thiết kế gốc: [docs/superpowers/specs/2026-07-17-forecast-api-integration-design.md](../superpowers/specs/2026-07-17-forecast-api-integration-design.md)

---

## 1. Kết quả

| Endpoint backend | Block UI (Dashboard) | Trạng thái |
| --- | --- | --- |
| `GET /api/v1/forecast?trip_id=&seat_type=` | Đường cong đặt vé | ✅ Đã ghép |
| `GET /api/v1/segments/load?trip_id=` | Heatmap tải chặng | ✅ Đã ghép |

Backend **không sửa** — endpoint đã có sẵn trong
`backend/src/backend/controllers/analytics_controller.py`. Toàn bộ việc ghép
nằm ở frontend.

---

## 2. Kiến trúc chuẩn (feature-folder)

Mỗi API là một **feature module** độc lập, tách bạch tầng gọi mạng, tầng
biến đổi dữ liệu, và tầng state. Screen chỉ *tiêu thụ* hook, không biết
đường dẫn API hay cách fetch.

```
frontend/src/features/<feature>/
  types.ts             # DTO khớp 1-1 với Pydantic view của backend
  api/<feature>Api.ts  # gọi apiClient (KHÔNG fetch() trực tiếp)
  hooks/use<Feature>.ts# "use client"; quản lý AsyncStatus + ApiError
  transform.ts         # hàm thuần biến DTO → dữ liệu cho UI (có unit test)
  transform.test.ts    # unit test cho transform
  index.ts             # interface công khai — bên ngoài chỉ import từ đây
```

Luồng dữ liệu:

```
Backend API
   │  (HTTP)
apiClient (src/lib/api/client.ts)   ← chỗ DUY NHẤT biết base URL, header, lỗi
   │
api/<feature>Api.ts                 ← biết đường dẫn + query params
   │
hooks/use<Feature>.ts               ← state: data | status | error | refetch
   │
transform.ts                        ← DTO → dữ liệu vẽ (thuần, test được)
   │
Screen/Component                    ← chỉ render
```

Các module đã tạo:

- `frontend/src/features/forecast/` — endpoint `/forecast`.
- `frontend/src/features/segments/` — endpoint `/segments/load`.

Mẫu tham chiếu có sẵn từ trước: `frontend/src/features/chat/`.

---

## 3. Các bước ghép một API (quy trình lặp lại)

### Bước 0 — Đọc hợp đồng & xác minh dữ liệu thật

1. Đọc Pydantic view của backend (vd `backend/src/backend/views/analytics_view.py`)
   để biết đúng shape response.
2. Khởi động backend rồi `curl` endpoint, **xem dữ liệu thật** trước khi code:

   ```bash
   curl -s "http://localhost:8000/api/v1/forecast?trip_id=1" | python -m json.tool | head
   ```

   > Đây là bước quan trọng nhất: dữ liệu thật thường khác mock. Ví dụ
   > `segments/load` **không có chiều thời gian** (mock có cột 06h/09h…), nên
   > heatmap phải đổi thành lưới *chặng × loại chỗ*.

### Bước 1 — `types.ts`

Khai báo DTO khớp **1-1** với view backend (tên trường y hệt, kể cả optional).

### Bước 2 — `api/<feature>Api.ts`

Một hàm cho mỗi endpoint, dùng `apiClient.get/post`. Build query bằng
`URLSearchParams`. Không gọi `fetch()` trực tiếp.

### Bước 3 — `transform.ts`

Các hàm **thuần** biến DTO → dữ liệu UI. Tách khỏi component để test được
và để component gọn. (Ví dụ: `buildCurveChart`, `buildSegmentHeatmap`.)

### Bước 4 — `hooks/use<Feature>.ts`

Hook `"use client"` theo đúng khuôn `useForecast`/`useSegmentsLoad`:

- state `data | status | error`;
- tự fetch khi tham số (vd `tripId`) đổi;
- huỷ request cũ bằng `AbortController`;
- map lỗi qua `ApiError`;
- trả thêm `refetch` và `isLoading`.

### Bước 5 — `index.ts`

Export hook, transform, và các type mà consumer cần. Bên ngoài **chỉ**
import từ `@/features/<feature>`.

### Bước 6 — Ghép vào Screen

Trong screen: gọi hook, `useMemo` chạy transform, render có đủ trạng thái:

- **loading**: `isLoading` → thông báo/skeleton;
- **error**: `status === "error"` → hiện `error` + nút **Thử lại** (`refetch`);
- **empty**: `status === "success"` nhưng transform trả `null`/rỗng;
- **success**: render dữ liệu.

### Bước 7 — Kiểm thử

```bash
cd frontend
npm run typecheck   # tsc --noEmit
npm test            # vitest: unit test cho transform
```

Rồi drive thật bằng trình duyệt (Playwright) mở `/dashboard`, xác nhận:
network gọi `200`, dữ liệu render, không lỗi console.

---

## 4. Chi tiết 2 API đã ghép

### 4.1. `/forecast` → Đường cong đặt vé

- Response `ForecastResponse`: `trip_id, service_date, forecasts[],
  booking_curve[]`.
- Dùng `booking_curve[]`: trục X = `D-${lead_days}` (lead_days giảm dần),
  đường thực tế = `cumulative_bookings`, đường dự báo = `forecast_demand_point`.
- **Lưu ý dữ liệu:** `forecast_demand_point` đang ở thang rất nhỏ (0.26–2.5)
  trong khi `cumulative_bookings` là 0–884, dù schema mô tả cả hai là "tích
  lũy". Vì lệch thang, mỗi đường được **chuẩn hoá theo max riêng** để so sánh
  *nhịp* đặt vé. Nếu backend chỉnh forecast về cùng đơn vị số vé, đổi sang
  chuẩn hoá chung (`buildCurveChart` trong `features/forecast/transform.ts`).

### 4.2. `/segments/load` → Heatmap tải chặng

- Response `LegHeatmapResponse`: `trip_id, legs[]` với `sequence_no,
  origin/destination_station_code, capacity, remaining, seat_type,
  bid_price, is_bottleneck`.
- Dữ liệu thật = 19 chặng × 2 loại chỗ (`giuong_nam_k6`, `ngoi_mem`).
- Heatmap = lưới **chặng (hàng) × loại chỗ (cột)**; ô = `(capacity -
  remaining) / capacity`, tô màu bằng `heatClass`.
- Cột "Nút cổ chai": đánh dấu chặng có `is_bottleneck = true`.

---

## 5. Kiểm thử & môi trường

### Frontend

```bash
cd frontend
npm install        # lần đầu
npm run dev        # http://localhost:3000  (.env.local: NEXT_PUBLIC_API_URL)
npm run typecheck
npm test           # vitest run — 15 test cho 2 transform, đều pass
```

Test runner: **vitest** (cấu hình `frontend/vitest.config.ts`, resolve alias
`@/`). File test đặt cạnh nguồn: `*.test.ts`.

### Backend (để test end-to-end)

```bash
# Từ thư mục gốc repo
set -a; source .env; set +a          # DATABASE_URL trỏ AWS RDS
.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --app-dir backend/src
```

> Nếu venv thiếu dependency, cài: `redis`, `numpy`, `pandas`, `scipy`,
> `scikit-learn` (nên bổ sung vào `requirements.txt`/`pyproject.toml`).

### Kết quả kiểm thử đã ghi nhận

- `npm run typecheck`: sạch.
- `npm test`: 15/15 pass.
- Drive `/dashboard` bằng Playwright: 2 API trả `200`, heatmap 19 chặng +
  3 nút cổ chai, đường cong render, 0 lỗi console.

---

## 6. Việc còn lại (gợi ý)

- Thay `trip_id = 1` hardcode bằng selector chọn tàu/ngày trên toolbar.
- Ghép `forecasts[]` (demand + phân vị p10/p50/p90) vào một block riêng nếu cần.
- Áp cùng khuôn cho Khối 2 (Tối ưu) và Khối 3 (Định giá).
- Test đường error/empty end-to-end (hiện mới verify đường success).
