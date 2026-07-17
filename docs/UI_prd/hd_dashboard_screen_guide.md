# HD Màn Hình Tổng Quan

## Mục đích

Màn hình `Tổng quan` là dashboard trung tâm của hệ thống SRRM. Mục tiêu của màn hình này là giúp người dùng nắm rất nhanh:

- hôm nay hệ thống đang gặp vấn đề gì
- chặng nào cần can thiệp ngay
- tác động doanh thu hoặc tải đang ở mức nào
- hành động đề xuất tiếp theo là gì

Đây là màn hình ưu tiên cao nhất cho persona `Revenue Manager`.

## Đối tượng sử dụng

- Revenue Manager
- Điều độ viên cần theo dõi tình trạng tải chặng
- Quản lý vận hành muốn xem nhanh chỉ số trong ngày

## Chức năng chính trên màn hình

### 1. Thanh tìm kiếm và bộ lọc nhanh

Phần đầu màn hình có:

- ô tìm kiếm tàu, ga, chính sách hoặc mã chạy
- chip lọc nhanh như `Toàn tuyến SE3`, `Khởi hành hôm nay`, `Chỉ xem chặng rủi ro cao`

Mục tiêu là giúp người dùng thu hẹp phạm vi theo dõi ngay từ đầu.

### 2. Thẻ quyết định ưu tiên

Đây là khối quan trọng nhất của dashboard. Nội dung khối này gồm:

- cảnh báo chính cần xử lý ngay
- mức tải hiện tại
- mức tăng dự báo
- tác động doanh thu
- danh sách khuyến nghị hành động
- nút CTA để sang mô phỏng hoặc báo giá

Khối này trả lời câu hỏi: `nên xử lý gì trước`.

### 3. Cảnh báo nhanh và chế độ xem đã lưu

Cột phụ ở phần trên phải hiển thị:

- các cảnh báo nóng
- các chế độ xem đã lưu
- trạng thái sử dụng mô phỏng

Mục tiêu là hỗ trợ ra quyết định mà không chiếm toàn bộ chiều dài trang.

### 4. Cụm KPI

Dashboard hiển thị các KPI nhanh:

- `Tải trung bình`
- `Doanh thu dự kiến`
- `Chặng rủi ro`
- `Cảnh báo mở`

Các KPI này giúp người dùng nhìn được sức khỏe tổng thể của hệ thống trong ngày.

### 5. Heatmap tải chặng

Heatmap cho phép theo dõi tải theo chặng và theo khung giờ. Thành phần này giúp người dùng nhận ra:

- chặng nào đang nóng lên
- thời điểm nào có nguy cơ sold-out
- khu vực nào cần điều chỉnh quota hoặc bid price

Ngoài bảng heatmap còn có:

- chú giải màu
- nút lọc tàu và ngày

### 6. Đường cong đặt vé

Khối này thể hiện:

- doanh số thực tế theo mốc thời gian trước ngày chạy
- nhu cầu dự báo trên cùng biểu đồ

Mục tiêu là nhìn ra độ lệch giữa thực tế và forecast.

### 7. Ma trận OD

Ma trận OD hiển thị lượng vé theo cặp ga để hỗ trợ:

- điều chỉnh quota
- xem luồng nào đang hút nhu cầu
- cân bằng giữa ga dài và ga trung gian

### 8. Gợi ý lấp khoảng trống

Khối này đưa ra các action có thể làm ngay để tận dụng tồn kho bị bỏ phí. Mỗi item thường có:

- chặng
- loại chỗ
- số chỗ khả dụng có thể mở thêm
- mức ưu tiên
- nút xem chi tiết

### 9. Trạng thái dữ liệu và điều phối

Khối cuối trang dùng để:

- xác nhận dữ liệu đã đồng bộ tới đâu
- nhắc tín hiệu theo dõi cuối ngày
- tạo điểm kết thúc rõ ràng cho dashboard

## Giá trị sử dụng

Màn hình này giúp người dùng:

- ưu tiên đúng vấn đề cần xử lý
- giảm thời gian đọc nhiều màn hình khác nhau
- kết nối insight với hành động thực tế
- nhìn nhanh AI gợi ý gì trước khi chuyển sang thao tác chi tiết

## Trạng thái UI hiện tại

Màn hình đã có đầy đủ:

- search và quick filters
- decision card chính
- KPI cards
- heatmap dạng bảng
- booking curve
- OD matrix
- action suggestions
- quick alert widgets

## Gợi ý nâng cấp sau này

- thêm drill-down từ heatmap sang từng chuyến
- thêm tooltip chi tiết theo cell
- thêm filter theo loại chỗ
- thêm realtime refresh
- thêm sparkline cho KPI
