# Đặt vé ghép chặng — nối frontend vào backend

Ngày: 2026-07-19
Trạng thái: đã duyệt, đang triển khai

## Bối cảnh

Backend cho vé ghép chặng đã hoàn thành ở commit `b2c3b37`. Bốn endpoint đã chạy
trong `booking_controller.py`, dựa trên `combined_booking_service.py` (496 dòng)
và có test ở `tests/test_combined_booking_api.py`.

Frontend thì chưa nối. `BookingScreen.triggerCombinedMode()` bịa ra 4 chặng cứng
và nút đặt vé bị `disabled` với nhãn "Đặt vé ghép chưa được backend hỗ trợ".

Spec này chỉ xử lý phần nối frontend.

## Phạm vi

Hai mảng còn lại được tách thành sub-project riêng, **không** nằm trong spec này:

- **B — nghiệp vụ backend:** hủy cả nhóm vé, refund toàn bộ/từng chặng, job tự
  động giải phóng vé hết hạn.
- **C — auth & ownership:** repo hiện **không có** bảng `users` trong `schema.sql`
  và không có code auth/JWT/session ở cả backend lẫn frontend. Việc gắn
  `user_id` vào booking và chặn user xem vé người khác là một hệ thống mới, không
  phải một task nhỏ.

## Quyết định về AWS RDS

`booking_groups` và `booking_group_items` đã có sẵn trong `schema.sql:160-191`,
nên `scripts/migrate_booking_groups.sql` chỉ cần cho DB đã provision từ trước.

- Chạy migration trên RDS: **có**. Script toàn bộ là `CREATE TABLE IF NOT EXISTS`
  và `CREATE INDEX IF NOT EXISTS`, không xóa dữ liệu.
- Chạy test suite trên RDS: **không**. Test tích hợp backend xóa dữ liệu
  `demand_forecasts` và sẽ làm hỏng Khối 1. Test chạy trên Postgres local/Docker.

## Kiến trúc

Tách thành module có ranh giới rõ, theo đúng convention `features/<name>/{api,hooks,components}`
đang dùng trong repo. `BookingScreen.tsx` hiện đã 829 dòng và đang gánh quá nhiều
việc; thêm option list + countdown vào thẳng file đó sẽ đẩy nó qua 1100 dòng.

```
features/booking/
  types.ts                          (thêm type cho vé ghép)
  api/combinedBookingApi.ts         4 hàm gọi API
  hooks/combinedState.ts            reducer thuần — test được, không cần DOM
  hooks/combinedState.test.ts
  hooks/useCombinedBooking.ts       nối reducer với API
  components/CombinedOptionList.tsx
  components/CombinedHoldPanel.tsx
```

`BookingScreen` giữ nguyên nút hiện có, chỉ render `<CombinedBookingPanel/>` thay
cho phần mock. Diff ở file đó là một khối xóa cộng một component.

### Type

Chép đúng theo `backend/src/backend/views/combined_booking_view.py`, không tự
nghĩ ra shape mới.

### Máy trạng thái

`idle → searching → options → holding → held → confirming → confirmed`, cộng
`expired` và `error`. Viết dưới dạng reducer thuần trong `combinedState.ts` để
test bằng vitest mà không cần React Testing Library (repo chưa cài RTL).

### Đếm ngược giữ chỗ

Lấy mốc từ `expires_at` server trả về, **không** tự đếm 15:00 ở client. Backend
tính hạn giữ chỗ bằng `MIN(booking.expires_at)` (`combined_booking_service.py:209`),
nên client chỉ được phép hiển thị lại con số đó. Hết giờ thì chuyển sang trạng
thái `expired` và mời tìm lại.

### Hiển thị

`CombinedOptionList` render mỗi phương án thành một card chọn được: số lần
chuyển, số lần đổi chỗ, tổng giá, và từng chặng (ga đi → ga đến, giờ, toa/ghế).
Cờ `keep_previous_seat` sinh ra ghi chú "đổi chỗ tại ga X" — thứ hiện đang hardcode.

Bắt buộc có ba trạng thái: `loading` skeleton, `empty` ("không tìm được phương án
ghép chặng"), và `error` kèm nút thử lại.

### Trang chi tiết vé

`TicketDetailsScreen` thêm nhánh theo query param:

- `?code=` → vé thường, một chặng (giữ nguyên).
- `?groupCode=` → `GET /booking/combined/{group_code}`, hiện tất cả chặng, ga
  chuyển, ghế từng chặng, tổng tiền.

Màn hình này **đã** không còn fallback hardcode khi API lỗi — mục đó trong yêu
cầu ban đầu đã xong từ trước.

## Không có bước thanh toán

Repo không có màn hình thanh toán nào. Luồng: giữ chỗ → hiện countdown và tổng
tiền → nút "Xác nhận thanh toán" gọi thẳng `confirm`, giống luồng vé thường.

## Test

- `combinedState.test.ts`: các bước chuyển trạng thái, tính giờ còn lại, xử lý lỗi.
- Backend đã có `test_combined_booking_api.py`.
- `npm run typecheck` và `npm run lint` trước khi tạo PR.
