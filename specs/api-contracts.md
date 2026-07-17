# Specs — Thiết kế Hợp đồng API & Giao diện Module (API Contracts)

Hệ thống **SRRM** được phát triển theo cấu trúc Monorepo phân ranh giới rõ ràng. Dưới đây là đặc tả các giao thức truyền thông và API giữa các thành phần.

---

## 1. Giao diện Python nội bộ (Backend Service $\leftrightarrow$ AI Module)

AI module (`ai/`) không chạy giao thức mạng (HTTP) mà được Backend (`backend/`) import trực tiếp như một thư viện Python trong cùng process. Giao diện công khai duy nhất nằm ở `ai/src/ai/__init__.py`.

### Hàm Interface chính:
```python
def run_agent(query: str, session_id: str = None) -> AgentResult:
    """
    Điểm tiếp nhận truy vấn ngôn ngữ tự nhiên từ Backend.
    Duyệt qua LangGraph agent để phân tích ý định và gọi các tools tương ứng.
    """
```

### Kiểu dữ liệu đầu ra:
```python
@dataclass
class AgentResult:
    status: str          # "success" | "error"
    response: str        # Câu trả lời dạng văn bản (Markdown) cho người dùng
    action_type: str     # Loại hành động: "forecast_query" | "optimize_trigger" | "pricing_adjust" | "chat"
    data: dict           # Dữ liệu trả về có cấu trúc (ví dụ: danh sách hạn ngạch, bid prices)
    error_message: str = None
```

---

## 2. API REST (Frontend $\leftrightarrow$ Backend)

Tất cả các API HTTP được Backend (`backend/`) cung cấp tại base URL `/api/v1` và được Frontend gọi duy nhất thông qua `frontend/src/lib/api/`.

### 2.1. API Chat chính (Tương tác Trợ lý AI)
* **Endpoint:** `POST /api/v1/chat`
* **Request Body:**
  ```json
  {
    "message": "Hiển thị heatmap tải chặng của tàu SE1 ngày 20/07/2026",
    "session_id": "session-123456"
  }
  ```
* **Response Body (Success 200):**
  ```json
  {
    "message_id": "msg-789",
    "role": "assistant",
    "content": "Đây là heatmap tải chặng của tàu SE1 ngày 20/07/2026...",
    "action_type": "forecast_query",
    "payload": {
      "train_id": "SE1",
      "departure_date": "2026-07-20",
      "legs": [
        {"leg_id": "HN-Vinh", "occupancy": 0.85, "status": "warning"},
        {"leg_id": "Vinh-Hue", "occupancy": 0.40, "status": "normal"},
        {"leg_id": "Hue-DN", "occupancy": 0.95, "status": "critical"}
      ]
    }
  }
  ```

---

### 2.2. API Biểu đồ nhiệt tải chặng (Legs Heatmap)
* **Endpoint:** `GET /api/v1/analytics/legs-heatmap`
* **Query Parameters:**
  * `train_id` (string, required): Mã đoàn tàu (ví dụ: `SE1`).
  * `departure_date` (string, required): Ngày chạy tàu (`YYYY-MM-DD`).
* **Response Body (Success 200):**
  ```json
  {
    "train_id": "SE1",
    "departure_date": "2026-07-20",
    "legs": [
      {
        "sequence": 1,
        "origin": "HN",
        "destination": "Vinh",
        "capacity": 120,
        "sold": 102,
        "allocated_quota": {
          "long_haul": 80,
          "short_haul": 40
        },
        "bid_price": 150000.0
      },
      {
        "sequence": 2,
        "origin": "Vinh",
        "destination": "Hue",
        "capacity": 120,
        "sold": 48,
        "allocated_quota": {
          "long_haul": 80,
          "short_haul": 40
        },
        "bid_price": 50000.0
      }
    ]
  }
  ```

---

### 2.3. API Đề xuất giá vé động (Pricing Quote)
* **Endpoint:** `GET /api/v1/pricing/quote`
* **Query Parameters:**
  * `origin` (string): Ga đi.
  * `destination` (string): Ga đến.
  * `departure_date` (string): Ngày đi.
  * `seat_type` (string): Loại ghế.
* **Response Body (Success 200):**
  ```json
  {
    "origin": "HN",
    "destination": "Hue",
    "base_price": 450000.0,
    "proposed_price": 520000.0,
    "fare_class": "STANDARD",
    "calculation_details": {
      "sum_bid_prices": 370000.0,
      "markup_factor": 1.4,
      "applied_constraints": ["CEILING_LIMIT_ENFORCED"]
    },
    "explanation": "Giá vé tăng 15% do chặng Huế-Đà Nẵng đang cháy vé (Bid Price chặng cao)."
  }
  ```

---

### 2.4. API Chạy tối ưu hóa DLP (Trigger Optimization)
* **Endpoint:** `POST /api/v1/optimize/resolve`
* **Request Body:**
  ```json
  {
    "train_id": "SE1",
    "departure_date": "2026-07-20"
  }
  ```
* **Response Body (Success 200):**
  ```json
  {
    "status": "success",
    "resolved_at": "2026-07-17T18:25:00Z",
    "objective_value": 158000000.0,
    "total_tickets_allocated": 284,
    "message": "Đã tối ưu hóa phân bổ chỗ và cập nhật danh sách Bid Price thành công."
  }
  ```

---

### 2.5. API So sánh chính sách mô phỏng (Policy Comparison)
* **Endpoint:** `GET /api/v1/simulation/compare`
* **Query Parameters:**
  * `train_id` (string): Mã tàu.
  * `start_date` (string): Ngày bắt đầu.
  * `end_date` (string): Ngày kết thúc.
* **Response Body (Success 200):**
  ```json
  {
    "summary": {
      "revenue_lift_pct": 5.4,
      "passenger_km_lift_pct": 3.8,
      "empty_seats_reduction_pct": 22.1
    },
    "daily_data": [
      {
        "date": "2026-07-10",
        "historical_revenue": 120000000.0,
        "simulated_ai_revenue": 126480000.0,
        "historical_occupancy": 0.78,
        "simulated_ai_occupancy": 0.81
      }
    ]
  }
  ```
