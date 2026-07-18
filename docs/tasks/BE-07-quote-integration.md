# BE-07 — Tích hợp API báo giá từ Frontend đến AI Service

> **⚠️ Bản ghi lịch sử — kiến trúc đã thay đổi.** Tài liệu này mô tả BE-07 tại thời điểm
> AI còn là microservice riêng gọi qua HTTP. Sau đó `ai_service` đã được chuyển thành
> **thư viện Python import thẳng vào backend**: `ai/ai_service/app.py`, `ai/Dockerfile`,
> `backend/services/ai_pricing_client.py` và các biến `AI_SERVICE_URL`/
> `AI_SERVICE_TIMEOUT_SECONDS` đều **không còn tồn tại**. Phần *nghiệp vụ* dưới đây
> (ánh xạ OD, snapshot bid price, policy guard, mã lỗi) vẫn đúng; chỉ phần *vận chuyển*
> là lỗi thời. Xem `ai/README.md` và `backend/services/ai_client.py` cho trạng thái hiện tại.

## 1. Mục tiêu

Tài liệu này ghi lại quá trình thay thế mock data trên màn hình báo giá bằng luồng dữ liệu thật:

```text
Frontend Quote
    -> POST /api/v1/quote
    -> Backend ánh xạ sản phẩm OD và các chặng
    -> Tổng hợp bid price và kiểm tra tồn chỗ
    -> Gọi AI định giá (khi đó: POST ai-service /internal/price;
       nay: AIClient.price -> AIEngine.price, in-process)
    -> Backend áp dụng chính sách giá và quyết định chấp nhận
    -> Lưu price_quotes và trả kết quả cho Frontend
```

Phạm vi triển khai gồm bốn task:

| Task | Nội dung |
|---|---|
| BE-07.1 | Nhận yêu cầu OD và ánh xạ các chặng |
| BE-07.2 | Kiểm tra chấp nhận theo bid price |
| BE-07.3 | Gọi AI để định giá theo snapshot |
| BE-07.4 | Trả kết quả và bổ sung test |

## 2. Trạng thái trước khi tích hợp

Trước BE-07, màn hình `QuoteScreen` đọc trực tiếp `quoteResult` trong
`frontend/src/features/rail-ui/mockData.ts`. Các trường nhập ga đi, ga đến,
loại chỗ và ngày đi không có state, không submit dữ liệu và không gọi API.

Backend đã có endpoint GET `/api/v1/quote?od_product_id=...`, nhưng endpoint
này yêu cầu Frontend biết trước `od_product_id`. Backend có thể cộng các bid
price hiện hành nhưng luôn ghi quyết định `accepted`, đồng thời chưa gọi
ai-service để lấy giá đề xuất.

AI đã có `/internal/price`, nhưng request cũ phụ thuộc `od_id` trong bộ dữ liệu
mô phỏng của AI. ID đó không đảm bảo trùng với `od_products.id` trong PostgreSQL.

## 3. BE-07.1 — Nhận OD và ánh xạ chặng

### 3.1. Request contract

Backend bổ sung endpoint:

```http
POST /api/v1/quote
Content-Type: application/json
```

Request body:

```json
{
  "origin": "HN",
  "destination": "DAN",
  "service_date": "2026-07-19",
  "seat_type": "giuong_nam_k6"
}
```

`origin` và `destination` nhận mã ga hoặc tên ga chính xác. `trip_id` là trường
tùy chọn. Khi không truyền `trip_id`, backend chọn chuyến phù hợp khởi hành sớm
nhất trong ngày.

Schema request được định nghĩa bằng Pydantic trong
`backend/src/backend/views/pricing_view.py`.

### 3.2. Ánh xạ OD

`PricingService` tìm sản phẩm đang hoạt động bằng các điều kiện:

- ngày chạy trong `trips.service_date`;
- ga đi và ga đến trong `stations`;
- loại chỗ trong `od_products.seat_type`;
- `od_products.is_active = TRUE`;
- `trip_id`, nếu request có truyền.

Sau khi tìm được `od_product`, backend đọc `od_product_segments` theo
`segments.sequence_no` để lấy đúng thứ tự các chặng của hành trình.

Mỗi chặng được ghép với:

- `segment_inventory.remaining` theo loại chỗ;
- `bid_prices.bid_price` có `is_active = TRUE`;
- `bid_prices.run_version` để lưu vết phiên tối ưu.

Nếu không tìm thấy sản phẩm OD hoặc sản phẩm chưa được ánh xạ chặng, endpoint
trả về HTTP `404`.

## 4. BE-07.2 — Kiểm tra chấp nhận theo bid price

Chi phí cơ hội của OD được tính bằng:

```text
opportunity_cost = tổng bid_price hiện hành của toàn bộ chặng OD đi qua
```

Tồn chỗ khả dụng của OD là giá trị nhỏ nhất trong tồn kho các chặng:

```text
availability = min(remaining của từng chặng)
```

Quy tắc quyết định:

```text
accepted khi availability > 0 và final_price >= opportunity_cost
rejected khi hết chỗ hoặc final_price < opportunity_cost
```

Logic này nằm trong hàm `evaluate_bid_price()` tại
`backend/src/backend/services/pricing_service.py`.

Sau khi nhận giá đề xuất từ AI, backend tiếp tục áp dụng chính sách đang hoạt
động trong `price_policies`:

- giá sàn `min_price`;
- giá trần `max_price`;
- giới hạn bước thay đổi `max_step_change` so với báo giá accepted gần nhất.

Quyết định cuối cùng sử dụng `final_price` sau policy guard.

## 5. BE-07.3 — Gọi AI để định giá theo snapshot

Backend bổ sung `AIPriceClient` trong
`backend/src/backend/services/ai_pricing_client.py` (nay đã gộp vào `ai_client.py`).

Client gửi snapshot dữ liệu đã lấy từ PostgreSQL sang AI:

```json
{
  "od_id": 15,
  "service_date": "2026-07-19",
  "seat_type": "giuong_nam_k6",
  "base_price": 320000,
  "segments": [
    {"segment_id": 100, "bid_price": 100000},
    {"segment_id": 101, "bid_price": 250000}
  ]
}
```

Việc truyền snapshot giải quyết vấn đề ID mô phỏng của AI không trùng ID trong
PostgreSQL. AI không cần truy cập database và không import backend.

AI tính:

- tổng chi phí cơ hội;
- giá markup theo độ co giãn của loại chỗ;
- giới hạn surge so với giá cơ sở;
- chặng có bid price lớn nhất làm nút cổ chai;
- dữ liệu giải trình gồm elasticity và bid price từng chặng.

Nếu model forecast chưa có, pricing theo snapshot vẫn hoạt động; forecast/optimize sẽ
trả `503` cho đến khi model sẵn sàng.

Lỗi từ AI được chuyển thành `AIServiceError`, và public API trả HTTP `502`.

> **Hiện tại:** `AIPriceClient` đã được gộp vào `AIClient.price` trong
> `backend/services/ai_client.py`, gọi thẳng `ai_service.engine.AIEngine`. Không còn
> biến `AI_SERVICE_URL`/`AI_SERVICE_TIMEOUT_SECONDS`, không còn retry/timeout mạng —
> chỉ còn `AIEngineError` được bọc lại thành `AIServiceError`. Snapshot request giữ
> nguyên cấu trúc như JSON ở trên, nhưng truyền bằng object `PriceRequest` thay vì JSON
> qua mạng. Mã `502` giữ nguyên cho tương thích client.

## 6. BE-07.4 — Trả kết quả và test

### 6.1. Response contract

POST `/api/v1/quote` sử dụng model `PricingQuoteODResponse`. Các trường phục vụ
Frontend như ga đi, ga đến, ngày chạy, loại chỗ và tồn chỗ là bắt buộc.

Ví dụ response thành công:

```json
{
  "quote_id": 2048,
  "od_product_id": 15,
  "policy_id": 3,
  "opportunity_cost": 350000.0,
  "proposed_price": 420000.0,
  "final_price": 420000.0,
  "decision": "accepted",
  "explanation": {
    "base_opportunity_cost": 350000.0,
    "markup_factor": 1.2,
    "applied_policies": ["STANDARD_MARKUP"],
    "bottleneck_segment_id": 101,
    "bottleneck_segment": "Hue -> Da Nang",
    "segment_bid_prices": {
      "100": 100000.0,
      "101": 250000.0
    }
  },
  "expires_at": "2026-07-18T12:15:00+00:00",
  "origin": "Ha Noi",
  "destination": "Da Nang",
  "service_date": "2026-07-19",
  "seat_type": "giuong_nam_k6",
  "availability": 18
}
```

Mỗi báo giá được lưu vào `price_quotes`, bao gồm giá đề xuất, giá cuối cùng,
quyết định, giải trình, phiên bid price và thời điểm hết hạn.

### 6.2. Error contract

| HTTP status | Trường hợp |
|---|---|
| `404` | Không tìm thấy OD phù hợp hoặc OD chưa có ánh xạ chặng |
| `422` | Request thiếu trường hoặc không đúng kiểu dữ liệu |
| `502` | AI service không khả dụng hoặc trả payload không hợp lệ |
| `500` | Lỗi hệ thống hoặc database ngoài dự kiến |

Error body sử dụng envelope chuẩn của FastAPI:

```json
{
  "detail": "Mô tả lỗi"
}
```

### 6.3. Test đã bổ sung

Các test liên quan nằm tại:

- `backend/tests/test_bid_price_acceptance.py`;
- `backend/tests/test_quote_response.py`;
- `backend/tests/test_pricing.py`;
- `ai/tests/test_pricing_api.py`.

Coverage chính:

- accepted khi giá đủ bù chi phí cơ hội và còn chỗ;
- rejected khi giá thấp hơn bid price hoặc hết chỗ;
- backend gửi đúng snapshot bid price sang AI;
- AI nhận snapshot và trả giá;
- response `200` đầy đủ đúng contract;
- error response `404`, `422`, `502`;
- frontend request khớp request contract của backend.

## 7. Thay đổi trên Frontend

`QuoteScreen` được chuyển thành Client Component và quản lý:

- form state;
- loading state;
- error state;
- quote response state.

API call được đặt tại `frontend/src/features/quote/api/quoteApi.ts` và đi qua
`frontend/src/lib/api/client.ts`, đúng ranh giới module của dự án.

TypeScript contract nằm tại `frontend/src/features/quote/types.ts`.

Sau khi tích hợp, `quoteResult` đã được xóa khỏi `mockData.ts`. Màn hình chỉ hiển
thị kết quả sau khi backend trả response thành công.

## 8. Các file chính đã thay đổi

### Frontend

- `frontend/src/features/rail-ui/screens/QuoteScreen.tsx`
- `frontend/src/features/quote/api/quoteApi.ts`
- `frontend/src/features/quote/types.ts`
- `frontend/src/features/rail-ui/mockData.ts`
- `frontend/src/app/globals.css`

### Backend

- `backend/src/backend/controllers/pricing_controller.py`
- `backend/src/backend/services/pricing_service.py`
- `backend/src/backend/services/ai_pricing_client.py` *(đã xóa — gộp vào `ai_client.py`)*
- `backend/src/backend/views/pricing_view.py`
- `backend/src/backend/config.py`

### AI và triển khai

- `ai/ai_service/app.py` *(đã xóa — thay bằng `ai/src/ai_service/engine.py`)*
- `ai/src/ai_service/schemas.py`
- `ai/Dockerfile` *(đã xóa — `ai` cài kèm trong `backend/Dockerfile`)*
- `docker-compose.yml`
- `.env.example`

### Test và tài liệu

- `backend/tests/test_bid_price_acceptance.py`
- `backend/tests/test_quote_response.py`
- `backend/tests/test_pricing.py`
- `ai/tests/test_pricing_api.py`
- `docs/specs/api-contracts.md`

## 9. Cách chạy

Chạy toàn bộ stack:

```bash
docker compose up --build
```

Các địa chỉ mặc định:

| Thành phần | URL |
|---|---|
| Frontend | `http://localhost:3000/quote` |
| Backend | `http://localhost:8000` |
| Backend OpenAPI | `http://localhost:8000/docs` |

AI không còn cổng riêng — chạy in-process trong backend, xem `POST /api/v1/ai/forecast`
và `/api/v1/ai/optimize`.

Chạy kiểm tra chuẩn của dự án:

```bash
make check
```

Nếu chạy trên Windows không có `make`, có thể chạy từng nhóm:

```powershell
.\.venv\Scripts\python.exe -m pytest ai\tests -q
.\.venv\Scripts\python.exe -m pytest backend\tests -q
.\.venv\Scripts\python.exe -m ruff check ai backend
bash scripts/check_boundaries.sh
cd frontend
npm run lint
npm run typecheck
npm run build
```

## 10. Kết quả xác minh khi hoàn thành

- AI full suite: 18 test pass.
- Nhóm test BE-07.4 và acceptance: 9 test pass.
- Ruff trên toàn bộ file thay đổi của BE-07: pass.
- Frontend ESLint: pass.
- Frontend TypeScript: pass.
- Frontend production build: pass.
- Module boundaries: pass.
- Docker Compose config validation: pass.

Full backend integration suite còn phụ thuộc kết nối và dữ liệu PostgreSQL. Khi
không truy cập được database đã cấu hình, các test tích hợp database sẽ thất bại
trước khi chạy logic BE-07; các unit/controller test riêng của BE-07 không phụ
thuộc database bên ngoài và đã pass.
