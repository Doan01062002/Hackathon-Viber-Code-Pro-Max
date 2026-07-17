# ADR 0004 — Chiến lược Khóa Tồn kho Giao dịch Tránh Deadlock

## 1. Trạng thái
**ĐÃ ĐƯỢC PHÊ DUYỆT (APPROVED)**

---

## 2. Bối cảnh (Context)
Trong hệ thống SRRM, một ghế vật lý có thể được bán dưới dạng nhiều chặng ngắn liên tiếp không chồng lấn. Khi hành khách yêu cầu đặt vé cho luồng OD đi qua nhiều chặng (ví dụ: Hà Nội -> Huế đi qua các chặng HN-Vinh, Vinh-Đồng Hới, Đồng Hới-Huế):
1. Hệ thống Backend phải trừ tồn kho (`segment_inventory.remaining`) trên **tất cả** các chặng này.
2. Nếu có nhiều hành khách cùng thực hiện đặt vé cho các lộ trình khác nhau có chặng giao nhau tại cùng thời điểm, có thể xảy ra tranh chấp ghi (Race Condition) làm âm tồn kho.
3. Nếu các luồng giao dịch khóa các chặng theo các thứ tự khác nhau (ví dụ: Luồng 1 khóa HN-Vinh trước rồi Vinh-Huế; Luồng 2 khóa Vinh-Huế trước rồi HN-Vinh), hệ thống sẽ rơi vào trạng thái **Deadlock** (khóa vòng).

---

## 3. Quyết định (Decision)
Áp dụng chiến lược giao dịch và khóa dòng nghiêm ngặt trong Backend:
1. **Khóa dòng bi quan (Pessimistic Locking):** Sử dụng câu lệnh `SELECT ... FOR UPDATE` của PostgreSQL để khóa các bản ghi tương ứng trong bảng `segment_inventory`.
2. **Khóa theo thứ tự ID tăng dần:** Khi một giao dịch cần khóa nhiều chặng, Backend bắt buộc phải sắp xếp danh sách `segment_id` theo thứ tự tăng dần trước khi thực hiện truy vấn khóa. Điều này đảm bảo mọi luồng xử lý đều khóa theo cùng một chiều vật lý, triệt tiêu hoàn toàn khả năng xảy ra khóa vòng (Deadlock).
3. **Transaction siêu nhỏ (Minimize Transaction Window):** Không thực hiện bất kỳ lệnh gọi API bên ngoài (như cổng thanh toán, gọi LLM) hoặc xử lý CPU nặng bên trong transaction block. Mọi tính toán giá vé và tối ưu đã được chạy và lưu trước đó; transaction chỉ thực hiện đọc-kiểm tra-ghi tồn kho.
4. **Hold với TTL:** Các booking giữ chỗ (`status = 'held'`) bắt buộc phải ghi nhận trường `expires_at`. Tiến trình quét nền (cron worker) chạy mỗi phút sẽ tự động hủy các booking hết hạn và cộng trả lại tồn kho `segment_inventory.remaining`.

---

## 4. Hệ quả (Consequences)
* **Tích cực:**
  * Đảm bảo tính nhất quán tuyệt đối của tồn kho chặng: Đạt tiêu chuẩn an toàn giao dịch đường sắt, không bao giờ xảy ra lỗi âm chỗ hoặc bán trùng (overbooking).
  * Loại bỏ lỗi Deadlock ở mức cơ sở dữ liệu.
* **Tiêu cực:**
  * Yêu cầu các lập trình viên Backend phải tuân thủ nghiêm ngặt quy trình sắp xếp ID chặng khi viết repository.
