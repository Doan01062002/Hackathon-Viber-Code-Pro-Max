# Task — SRRM-D2: Thiết lập Repository Layer & Row-Level Locking

## 1. Mục tiêu
Xây dựng lớp Repository và logic xử lý giao dịch Backend (FastAPI + SQLAlchemy) để quản lý tồn kho chặng ngồi, trừ tồn kho an toàn dưới tải cao, khóa dòng chống deadlock và giải phóng tự động khi hết hạn.

---

## 2. Mô tả Kỹ thuật

### 2.1. Logic Khóa dòng chặng ngồi (Row-Level Locking)
* **Vấn đề tranh chấp chỗ:** Một giao dịch mua vé cho lộ trình OD đi qua danh sách chặng $L$ cần giảm số chỗ trống `remaining` của bảng `segment_inventory`.
* **Cài đặt trong SQLAlchemy:**
  1. Nhận yêu cầu đặt vé, lấy danh sách `segment_id` đi qua từ bảng `od_product_segments`.
  2. Sắp xếp danh sách `segment_id` theo thứ tự tăng dần để phòng tránh Deadlock:
     ```python
     sorted_segment_ids = sorted(segment_ids)
     ```
  3. Mở một transaction, thực hiện truy vấn khóa dòng bi quan:
     ```python
     # SQL: SELECT * FROM segment_inventory WHERE segment_id IN (...) FOR UPDATE
     query = session.query(SegmentInventory).filter(
         SegmentInventory.segment_id.in_(sorted_segment_ids)
     ).with_for_update()
     ```
  4. Duyệt qua kết quả, kiểm tra điều kiện `remaining > 0` cho mỗi chặng.
  5. Nếu bất kỳ chặng nào có `remaining = 0`, thực hiện `ROLLBACK` transaction ngay lập tức và trả về lỗi hết vé (không thực hiện trừ dở dang).
  6. Nếu đủ chỗ trên toàn bộ các chặng, cập nhật: `remaining = remaining - 1` cho từng dòng, chèn bản ghi vào bảng `bookings` với trạng thái `held` (giữ chỗ) hoặc `confirmed` (đã mua), sau đó `COMMIT`.

### 2.2. Tiến trình Giải phóng Hold quá hạn (TTL Worker)
* Khi khách hàng chọn giữ chỗ, bản ghi `bookings` được lưu với trạng thái `held` kèm hạn thời gian `expires_at` (ví dụ: +15 phút từ lúc đặt).
* Viết một background worker định kỳ quét PostgreSQL tìm các bản ghi `bookings` có `status = 'held'` và `expires_at < CURRENT_TIMESTAMP`.
* Với mỗi booking hết hạn, thực hiện mở transaction, khóa dòng `segment_inventory` của các chặng tương ứng, cộng trả lại tồn kho (`remaining = remaining + 1`), cập nhật trạng thái booking thành `cancelled`, sau đó commit.

---

## 3. Các thành phần mã nguồn liên quan
* `backend/src/backend/services/booking_service.py` [NEW]: Lớp service quản lý giao dịch đặt vé và trừ tồn kho chặng.
* `backend/src/backend/services/release_worker.py` [NEW]: Background worker quét giải phóng hold.
* `backend/tests/test_locking.py` [NEW]: Unit test giả lập đa luồng tranh chấp để kiểm tra chống deadlock và kiểm tra rollback khi hết chỗ.

---

## 4. Tiêu chí Chấp nhận (Acceptance Criteria)
* **AC1:** Toàn bộ tiến trình giữ chỗ và trừ tồn kho chạy trong một transaction nguyên thủy độc lập.
* **AC2:** Chèn dữ liệu thử nghiệm tranh chấp đồng thời (ví dụ: 10 luồng cùng đặt chặng trùng lấn nhau trong khi tồn kho chỉ còn 5 chỗ) phải đảm bảo chỉ có tối đa 5 vé được xác nhận thành công, 5 vé còn lại bị rollback và không có lỗi deadlock xảy ra.
* **AC3:** Worker quét và giải phóng tồn kho chính xác cho các booking held quá hạn, khôi phục lại trường `remaining` của các chặng liên quan.
