# Thiết kế — Ghép API Khối 1 (Dự báo)

Ngày: 2026-07-17
Phạm vi: Khối 1 - Dự báo, 2 endpoint:
- `GET /api/v1/forecast` → block "Đường cong đặt vé" (đã ghép).
- `GET /api/v1/segments/load` → block "Heatmap tải chặng" (đã ghép, xem mục cuối).

## Mục tiêu

Thay dữ liệu mock của block **"Đường cong đặt vé"** trên Dashboard tải chặng
bằng dữ liệu thật từ backend, theo đúng chuẩn feature-folder của hệ thống
(mẫu: feature `chat`).

## Endpoint backend (đã có sẵn)

`GET /api/v1/forecast?trip_id={int, required}&seat_type={str|null}`
→ `ForecastResponse` (backend/src/backend/views/analytics_view.py):

- `trip_id: int`
- `service_date: str` (YYYY-MM-DD)
- `forecasts: ForecastItem[]` — `od_product_id, origin_station_code,
  destination_station_code, seat_type, lead_days, demand_point,
  demand_p10?, demand_p50?, demand_p90?`
- `booking_curve: BookingCurvePoint[]` — `lead_days, cumulative_bookings,
  forecast_demand_point`

Lỗi: 404 (ValueError → không tìm thấy trip), 500 (lỗi hệ thống). Client đã
map `detail` của FastAPI qua `ApiError` sẵn trong `lib/api/client.ts`.

## Kiến trúc frontend

Module mới `frontend/src/features/forecast/`:

```
features/forecast/
  types.ts               # DTO khớp 1-1 với analytics_view.py
  api/forecastApi.ts     # getForecast(tripId, seatType?, signal?)
  hooks/useForecast.ts   # "use client"; fetch theo tripId; AsyncStatus + ApiError
  index.ts               # interface công khai
```

- **types.ts**: `ForecastItemDto`, `BookingCurvePointDto`, `ForecastResponseDto`.
- **forecastApi.ts**: dùng `apiClient.get` (không gọi `fetch` trực tiếp).
- **useForecast(tripId, seatType?)**: state `data | status | error`, tự fetch
  khi `tripId`/`seatType` đổi, có `refetch`, huỷ request cũ bằng `AbortController`.
- **index.ts**: export `useForecast`, các type DTO cần cho consumer.

## Điểm ghép

`frontend/src/features/rail-ui/screens/DashboardScreen.tsx`:

- Thêm `"use client"`, gọi `useForecast(1)`.
- Block "Đường cong đặt vé":
  - Trục X = `D-${lead_days}` (sắp theo `lead_days` giảm dần → gần ngày chạy ở cuối).
  - Đường thực tế = `cumulative_bookings`; đường dự báo = `forecast_demand_point`.
  - Chuẩn hoá cả 2 chuỗi theo `max` toàn bộ điểm để vẽ trên khung 0–100%.
  - Trạng thái: **loading** (skeleton/spinner), **error** (message + nút thử lại),
    **empty** (booking_curve rỗng).
- Heatmap, Ma trận OD, các block khác: **giữ mock** lần này.

## Mặc định (hackathon)

- `trip_id = 1`, `seat_type = null`. Selector tàu/ngày để sprint sau.

## Kiểm thử

- Khởi động backend `localhost:8000` có seed data; xác minh
  `curl "/api/v1/forecast?trip_id=1"` trả JSON hợp lệ.
- Chạy FE, mở `/dashboard`, xác nhận đường cong render từ dữ liệu thật,
  và các trạng thái loading/error/empty hoạt động.
- `npm run typecheck` sạch.

## Bổ sung — endpoint `/segments/load` (Heatmap tải chặng)

`GET /api/v1/segments/load?trip_id={int}` → `LegHeatmapResponse`
(alias của `/analytics/legs-heatmap`): `legs[]` với `sequence_no,
origin/destination_station_code, capacity, remaining, seat_type,
bid_price, is_bottleneck`.

Module mới `frontend/src/features/segments/` (cùng khuôn với `forecast`):
`types.ts`, `api/segmentsApi.ts` (`getSegmentsLoad`), `hooks/useSegmentsLoad.ts`,
`index.ts`.

Điểm ghép — block "Heatmap tải chặng" của DashboardScreen:

- Backend **không có chiều thời gian** (khác mock 06h/09h/…). Dữ liệu thật là
  tải theo *loại chỗ* của từng chặng, nên heatmap đổi thành lưới
  **chặng (hàng) × loại chỗ (cột)**.
- Ô = `(capacity - remaining) / capacity`, tô màu bằng `heatClass`.
- Cột "Nút cổ chai": đánh dấu chặng có `is_bottleneck = true`.
- Trạng thái loading / error (+ nút Thử lại) / empty như block forecast.
- Nhãn loại chỗ: `giuong_nam_k6 → "Giường nằm K6"`, `ngoi_mem → "Ngồi mềm"`.
