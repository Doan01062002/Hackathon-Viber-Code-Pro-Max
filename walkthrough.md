# Báo cáo kết quả hoàn thành Sprint 2, Sprint 3 & Sprint 4: Booking Engine, Rollback, OpenAPI & Frontend UI Integration

Tài liệu này tổng hợp toàn bộ các kết quả phát triển nghiệp vụ, tích hợp và kiểm định chất lượng trong Sprint 2, Sprint 3 và Sprint 4 cho dự án **Smart Rail Revenue Management (SRRM)**.

---

## 🛠️ Các thay đổi đã thực hiện trong Sprint 2

### 1. Booking Engine & Gán ghế vật lý
* **[booking_view.py](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/backend/src/backend/views/booking_view.py)**: Định nghĩa các schema Pydantic giao tiếp gồm tạo giữ chỗ (`BookingCreateRequest`), giữ chỗ thành công (`BookingResponse`), và xác nhận chỗ thành công (`BookingConfirmResponse`).
* **[booking_service.py](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/backend/src/backend/services/booking_service.py)**:
  * **Tránh Deadlock khóa dòng:** Trích xuất danh sách chặng và áp dụng `SELECT ... FOR UPDATE` sắp xếp tăng dần theo `segment_id`.
  * **Gán ghế vật lý không giao lộ:** Giải thuật gán ghế trống đảm bảo không trùng chặng (không giao nhau về mặt lộ trình) giữa các khách hàng đi cùng chuyến tàu.
  * **Hủy giữ chỗ hết hạn:** Tự động quy đổi trạng thái giữ chỗ hết hạn sau 15 phút về `cancelled` và hoàn trả tồn kho chặng.
* **[booking_controller.py](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/backend/src/backend/controllers/booking_controller.py)**: Phơi các endpoint `/api/v1/booking` (POST giữ chỗ, POST xác nhận gán ghế, POST dọn dẹp giữ chỗ hết hạn).

---

## 🛠️ Các thay đổi đã thực hiện trong Sprint 3

### 1. Redis Stream & Event Queue Integration
* **[redis_client.py](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/backend/src/backend/redis/redis_client.py)**: Tích hợp Redis Stream thực tế, tự động fallback sang `MockRedis` trong bộ nhớ phục vụ chạy kiểm thử độc lập.
* **[events_controller.py](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/backend/src/backend/controllers/events_controller.py)**: Phơi endpoint `/api/v1/events` để đẩy các sự kiện nghiệp vụ vào Redis Stream `srrm:event_stream`.

### 2. Background Worker & Debounce Re-solve
* **[worker.py](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/backend/src/backend/worker.py)**: Thiết lập Worker nền chạy hai luồng song song: StreamConsumer nhận sự kiện mới và DebounceProcessor gom sự kiện của cùng chuyến tàu trong 1.0 giây để tránh re-solve liên tục. Khi debounce xong, kích hoạt giải tối ưu DLP tính toán lại hạn ngạch ghế và giá cơ hội.

### 3. Cơ chế phục hồi tối ưu (Rollback) (BE-17)
* **[optimize_service.py](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/backend/src/backend/services/optimize_service.py)**: Triển khai hàm nghiệp vụ `get_run_versions` truy vấn tất cả run_versions của chuyến tàu và `rollback_to_version` thực hiện swap active version an toàn.
* **[optimize_controller.py](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/backend/src/backend/controllers/optimize_controller.py)**: Cung cấp 2 route:
  * `GET /api/v1/optimize/resolve/versions`: Tra cứu danh sách các phiên bản chạy tối ưu.
  * `POST /api/v1/optimize/resolve/rollback`: Khôi phục cấu hình tối ưu về phiên bản trước.

### 4. Client gọi AI-Service với Retry & Caching (BE-18)
* **[ai_client.py](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/backend/src/backend/services/ai_client.py)**: Phát triển `AIClient` sử dụng `httpx.AsyncClient` để giao tiếp với `ai-service`:
  * **Exponential Backoff Retry:** Tự động thử lại cuộc gọi khi gặp lỗi kết nối hoặc HTTP 5xx tối đa 3 lần.
  * **In-Memory Cache:** Tự động lưu trữ (cache) kết quả bid prices tối ưu của từng ngày chạy (`service_date`).

### 5. Đặc tả OpenAPI Contracts (BE-19)
* **[openapi.yaml](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/contracts/openapi.yaml)**: Soạn thảo cấu trúc tài liệu OpenAPI 3.0.3 thống nhất lưu trong `contracts/` định nghĩa chi tiết URL, HTTP verb, query params, request body payload và response schema cho cả 3 dịch vụ.

---

## 🛠️ Các thay đổi đã thực hiện trong Sprint 4 (Frontend UI Integration)

### 1. Tải và Ràng buộc Dữ liệu thực tế cho Dashboard (FE-04 & FE-05)
* **[DashboardScreen.tsx](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/frontend/src/features/rail-ui/screens/DashboardScreen.tsx)**:
  * Tích hợp `apiClient.get` để lấy dữ liệu heatmap tải chặng thực tế từ `/api/v1/analytics/legs-heatmap?trip_id=1` và booking curve từ `/api/v1/forecast?trip_id=1`.
  * Tính toán trung bình tải chặng động và đếm số lượng chặng nghẽn (bottleneck) trực tiếp từ database.
  * Hỗ trợ tự động fallback sang dữ liệu mô phỏng cục bộ nếu API backend offline hoặc chưa có dữ liệu seed.

### 2. Biểu mẫu Báo giá & Bảo vệ bằng Hạn ngạch (FE-07 & FE-08)
* **[QuoteScreen.tsx](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/frontend/src/features/rail-ui/screens/QuoteScreen.tsx)**:
  * Tải danh sách sản phẩm hành trình (OD Products) từ `/api/v1/pricing/products` (đã thêm mới controller hỗ trợ).
  * Gọi API báo giá động `/api/v1/pricing/quote?od_product_id={id}` để hiển thị đề xuất giá vé thời gian thực.
  * Ràng buộc và hiển thị rõ ràng các chính sách giới hạn sàn/trần/max step change được kích hoạt bởi Policy Guard.

### 3. Mô phỏng Kịch bản & So sánh Chỉ số AI (FE-10 & FE-11)
* **[SimulationScreen.tsx](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/frontend/src/features/rail-ui/screens/SimulationScreen.tsx)**:
  * Kết nối trực tiếp với API `/api/v1/simulation/compare?trip_id=1` của backend.
  * Đối chiếu tổng doanh thu và sản lượng luân chuyển (Khách-km) lịch sử so với thuật toán tối ưu AI.
  * Dựng biểu đồ so sánh tỉ lệ động theo kết quả giả lập từ DB.

### 4. Hệ thống Cảnh báo Vận hành & Nhật ký Kiểm toán (FE-12 & FE-08)
* **[AlertsScreen.tsx](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/frontend/src/features/rail-ui/screens/AlertsScreen.tsx)**:
  * Tự động phân tích năng lực chuyên chở từ `/api/v1/analytics/legs-heatmap` để phát hiện chặng sắp sold-out (tải >= 85%) và chặng trống cao (tải <= 40%) để đề xuất điều độ giá vé tức thời.
* **[AuditScreen.tsx](file:///c:/Users/vando/OneDrive/Desktop/Hackathon-Viber-Code-Pro-Max/frontend/src/features/rail-ui/screens/AuditScreen.tsx)**:
  * Tải dữ liệu từ `/api/v1/audit/logs` sử dụng `X-User-Role: revenue_manager` để truy vết vết thay đổi cấu hình.
  * Cho phép bấm chọn từng dòng nhật ký để xem chi tiết đối chiếu JSON `before_data` và `after_data`.

---

## 🧪 Kết quả kiểm thử & Xác minh chất lượng

### 1. Kết quả chạy toàn bộ unit tests (47/47 tests passed):
```bash
.\.venv\Scripts\python run_tests.py backend/tests/ -v
```
```text
backend\tests\test_ai_client.py::test_ai_client_success PASSED           [  2%]
backend\tests\test_ai_client.py::test_ai_client_caching PASSED           [  4%]
backend\tests\test_ai_client.py::test_ai_client_retries_and_fails PASSED [  6%]
backend\tests\test_ai_client.py::test_ai_client_retries_then_succeeds PASSED [  8%]
backend\tests\test_analytics.py::test_legs_heatmap_success PASSED        [ 10%]
backend\tests\test_analytics.py::test_legs_heatmap_alias_success PASSED  [ 12%]
backend\tests\test_analytics.py::test_legs_heatmap_not_found PASSED      [ 14%]
backend\tests\test_analytics.py::test_forecast_success PASSED            [ 17%]
backend\tests\test_analytics.py::test_forecast_alias_success PASSED      [ 19%]
backend\tests\test_analytics.py::test_forecast_with_seat_type_filter PASSED [ 21%]
backend\tests\test_analytics.py::test_forecast_not_found PASSED          [ 23%]
backend\tests\test_audit.py::test_get_audit_logs_rbac_success PASSED     [ 25%]
backend\tests\test_audit.py::test_get_audit_logs_rbac_denied PASSED      [ 27%]
backend\tests\test_audit.py::test_get_audit_logs_filtering PASSED        [ 29%]
backend\tests\test_booking.py::test_create_booking_hold_success PASSED   [ 31%]
backend\tests\test_booking.py::test_confirm_booking_success PASSED       [ 34%]
backend\tests\test_booking.py::test_booking_quota_exceeded PASSED        [ 36%]
backend\tests\test_booking.py::test_release_expired_bookings PASSED      [ 38%]
backend\tests\test_controllers.py::test_health PASSED                    [ 40%]
backend\tests\test_controllers.py::test_chat_empty_message PASSED        [ 42%]
backend\tests\test_controllers.py::test_chat_returns_agent_response PASSED [ 44%]
backend\tests\test_controllers.py::test_agent_status PASSED              [ 46%]
backend\tests\test_events.py::test_publish_event_success PASSED          [ 48%]
backend\tests\test_events.py::test_worker_debounce_re_solve PASSED       [ 51%]
backend\tests\test_integration_flows.py::test_end_to_end_integration_flow PASSED [ 53%]
backend\tests\test_optimize.py::test_optimize_resolve_success PASSED     [ 55%]
backend\tests\test_optimize.py::test_optimize_resolve_invalid_trip PASSED [ 57%]
backend\tests\test_policy.py::test_get_policies_rbac_success PASSED      [ 59%]
backend\tests\test_policy.py::test_get_policies_rbac_denied PASSED       [ 61%]
backend\tests\test_policy.py::test_update_policy_rbac_success PASSED     [ 63%]
backend\tests\test_policy.py::test_update_policy_rbac_denied PASSED      [ 65%]
backend\tests\test_policy.py::test_update_policy_invalid_constraints PASSED [ 68%]
backend\tests\test_pricing.py::test_pricing_quote_success PASSED         [ 70%]
backend\tests\test_pricing.py::test_pricing_quote_alias_success PASSED   [ 72%]
backend\tests\test_pricing.py::test_pricing_quote_not_found PASSED       [ 74%]
backend\tests\test_pricing.py::test_policy_guard_min_price PASSED        [ 76%]
backend\tests\test_pricing.py::test_policy_guard_max_price PASSED        [ 78%]
backend\tests\test_pricing.py::test_policy_guard_max_step_change PASSED  [ 80%]
backend\tests\test_pricing.py::test_get_all_products_success PASSED      [ 82%]
backend\tests\test_rollback.py::test_get_versions_success PASSED         [ 85%]
backend\tests\test_rollback.py::test_rollback_success PASSED             [ 87%]
backend\tests\test_rollback.py::test_rollback_invalid_version PASSED     [ 89%]
backend\tests\test_services.py::test_send_message_returns_domain_model PASSED [ 91%]
backend\tests\test_services.py::test_send_message_wraps_agent_failure PASSED [ 93%]
backend\tests\test_simulation.py::test_simulation_compare_success PASSED [ 95%]
backend\tests\test_simulation.py::test_simulation_compare_invalid_trip PASSED [ 97%]
backend\tests\test_simulation.py::test_simulation_compare_with_policy PASSED [100%]

======================= 47 passed in 251.05s (0:04:11) ========================
```

### 2. Kiểm tra ranh giới Module (check_boundaries.py):
```text
Checking Rule 1: ai/ does not import backend...
[PASS] Rule 1: ai/ does not import backend.

Checking Rule 2: only backend/services/ imports ai...
[PASS] Rule 2: only backend/services/ imports ai.

Checking Rule 3: FE only calls fetch() inside lib/api/...
[PASS] Rule 3: FE only calls fetch() inside lib/api/.

All boundary checks passed successfully!
```

### 3. TypeScript Type-Checking:
```text
cmd.exe /c "frontend\node_modules\.bin\tsc.cmd --noEmit --project frontend/tsconfig.json"
Completed successfully. (0 errors found)
```
