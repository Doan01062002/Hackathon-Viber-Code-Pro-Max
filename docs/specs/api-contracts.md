# Specs — Thiết kế Hợp đồng API & Giao diện Module (API Contracts)

Hệ thống **SRRM** thực hiện giao tiếp giữa Frontend, Backend và AI thông qua các interface được chuẩn hóa theo kiểu dữ liệu của cơ sở dữ liệu PostgreSQL.

---

## 1. Giao diện Python nội bộ (Backend Service $\leftrightarrow$ AI Module)

Lớp `ai/` được import và chạy trong cùng tiến trình của `backend/`. 

### Hàm Interface chính:
```python
def run_agent(query: str, session_id: str = None) -> AgentResult:
    """
    Điểm tiếp nhận truy vấn ngôn ngữ tự nhiên từ Backend.
    Duyệt qua LangGraph agent để phân tích ý định và gọi các tools tương ứng.
    """
```

### Kiểu dữ liệu đầu ra `AgentResult`:
```python
@dataclass
class AgentResult:
    status: str          # "success" | "error"
    response: str        # Câu trả lời dạng văn bản (Markdown) cho người dùng
    action_type: str     # "forecast_query" | "optimize_trigger" | "pricing_adjust" | "chat"
    data: dict           # Dữ liệu trả về (cấu trúc khớp với snapshot DB)
    error_message: str = None
```

---

## 2. API REST (Frontend $\leftrightarrow$ Backend)

Các REST API được cung cấp tại base URL `/api/v1`. Kiểu dữ liệu số học phản ánh đúng thiết kế trong `schema.sql` (sử dụng kiểu float/decimal cho giá trị tiền và khoảng cách).

### 2.1. API Chat chính (Tương tác Trợ lý AI)
* **Endpoint:** `POST /api/v1/chat`
* **Request Body:**
  ```json
  {
    "message": "Hiển thị heatmap tải chặng của chuyến tàu ID 1 ngày 20/07/2026",
    "session_id": "session-123456"
  }
  ```
* **Response Body (Success 200):**
  ```json
  {
    "message_id": "msg-789",
    "role": "assistant",
    "content": "Đây là heatmap tải chặng của chuyến tàu...",
    "action_type": "forecast_query",
    "payload": {
      "trip_id": 1,
      "legs": [
        {
          "segment_id": 101,
          "sequence_no": 1,
          "origin_station_id": 1,
          "destination_station_id": 2,
          "capacity": 120,
          "remaining": 15,
          "bid_price": 150000.00
        }
      ]
    }
  }
  ```

---

### 2.2. API Biểu đồ nhiệt tải chặng (Legs Heatmap)
* **Endpoint:** `GET /api/v1/analytics/legs-heatmap`
* **Query Parameters:**
  * `trip_id` (integer, required): ID của chuyến tàu (tham chiếu `trips.id`).
* **Response Body (Success 200):**
  ```json
  {
    "trip_id": 1,
    "legs": [
      {
        "segment_id": 101,
        "sequence_no": 1,
        "origin_station_code": "HN",
        "destination_station_code": "Vinh",
        "capacity": 120,
        "remaining": 98,
        "seat_type": "soft_seat",
        "bid_price": 50000.00,
        "is_bottleneck": false
      }
    ]
  }
  ```

---

### 2.3. API Đề xuất giá vé động (Pricing Quote)
* **Endpoint:** `GET /api/v1/pricing/quote`
* **Query Parameters:**
  * `od_product_id` (integer, required): ID của sản phẩm OD (tham chiếu `od_products.id`).
* **Response Body (Success 200):**
  ```json
  {
    "quote_id": 2048,
    "od_product_id": 15,
    "policy_id": 3,
    "opportunity_cost": 350000.00,
    "proposed_price": 420000.00,
    "final_price": 420000.00,
    "decision": "accepted",
    "explanation": {
      "base_opportunity_cost": 350000.00,
      "markup_factor": 1.2,
      "triggered_policies": ["STANDARD_MARKUP"]
    },
    "expires_at": "2026-07-17T19:00:00Z"
  }
  ```

---

### 2.4. API Chạy tối ưu hóa DLP (Trigger Optimization)
* **Endpoint:** `POST /api/v1/optimize/resolve`
* **Request Body:**
  ```json
  {
    "trip_id": 1
  }
  ```
* **Response Body (Success 200):**
  ```json
  {
    "status": "success",
    "resolved_at": "2026-07-17T18:48:00Z",
    "run_version": "ver-20260717-1848",
    "quotas_updated_count": 10,
    "bid_prices_updated_count": 5,
    "message": "Đã chạy tối ưu hóa DLP và swap phiên bản active thành công."
  }
  ```

---

### 2.5. API So sánh chính sách mô phỏng (Policy Comparison)
* **Endpoint:** `GET /api/v1/simulation/compare`
* **Query Parameters:**
  * `trip_id` (integer, required): ID của chuyến tàu.
  * `policy_id` (integer, optional): ID chính sách giá để so sánh.
* **Response Body (Success 200):**
  ```json
  {
    "trip_id": 1,
    "historical_revenue": 158000000.00,
    "simulated_revenue": 169860000.00,
    "revenue_lift_pct": 7.5,
    "historical_passenger_km": 12500.00,
    "simulated_passenger_km": 13100.00,
    "passenger_km_lift_pct": 4.8
  }
  ```

---

## 3. Quote OD integration (BE-07.1 - BE-07.3)

* **Endpoint:** `POST /api/v1/quote`
* **Request Body:**
  ```json
  {
    "origin": "HN",
    "destination": "DAN",
    "service_date": "2026-07-19",
    "seat_type": "giuong_nam_k6"
  }
  ```
* Backend maps the OD product to `od_product_segments`, sums active bid prices,
  calls `POST /internal/price` on ai-service, applies the active pricing policy,
  and accepts only when inventory is available and `final_price >= opportunity_cost`.
* `origin` and `destination` accept either a station code or its exact name.
  `trip_id` is optional; when omitted, the earliest matching trip is selected.
* The legacy `GET /api/v1/quote?od_product_id=...` contract remains available.

### 3.1. Response Body (BE-07.4)

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
    "segment_bid_prices": {"100": 100000.0, "101": 250000.0}
  },
  "expires_at": "2026-07-18T12:15:00+00:00",
  "origin": "Ha Noi",
  "destination": "Da Nang",
  "service_date": "2026-07-19",
  "seat_type": "giuong_nam_k6",
  "availability": 18
}
```

Error responses use FastAPI's `detail` envelope:

- `404`: OD cannot be mapped to an active product.
- `422`: request body validation failed.
- `502`: ai-service `/internal/price` is unavailable or returned an invalid payload.
