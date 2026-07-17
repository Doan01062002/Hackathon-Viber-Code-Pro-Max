# HD Màn Hình Cảnh Báo

## Mục đích

Màn hình `Cảnh báo` dùng để tập trung vào các vấn đề cần xử lý trong ca trực hiện tại. Đây là nơi giúp người dùng nhìn ngay:

- chặng nào sắp cháy vé
- chặng nào đang trống cao
- quota nào cần xem lại
- cảnh báo nào cần xử lý trước

## Đối tượng sử dụng

- Revenue Manager
- Điều độ viên
- Nhóm vận hành tuyến

## Chức năng chính trên màn hình

### 1. Bộ lọc cảnh báo

Người dùng có thể lọc nhanh theo nhóm:

- `Tất cả`
- `Sắp cháy vé`
- `Trống cao`
- `Quota cần xem lại`

Mục tiêu là phân loại cảnh báo theo vấn đề nghiệp vụ.

### 2. Danh sách cảnh báo

Danh sách cảnh báo hiển thị từng item dưới dạng card, gồm:

- mức độ
- tiêu đề
- mô tả chi tiết
- nút `Xem chi tiết`

Mỗi cảnh báo giúp người dùng hiểu nhanh:

- mức nghiêm trọng
- chặng hoặc vấn đề liên quan
- tác động ngắn hạn

## Giá trị sử dụng

Màn hình này giúp:

- không bỏ sót các tín hiệu nóng
- ưu tiên đúng cảnh báo trong ca trực
- rút ngắn thời gian chuyển từ phát hiện sang xử lý

## Trạng thái UI hiện tại

Màn hình hiện đã có:

- nhóm filter cảnh báo
- danh sách cảnh báo dạng card
- phân tầng severity cơ bản

## Gợi ý nâng cấp sau này

- thêm thời gian phát sinh cảnh báo
- thêm trạng thái đã đọc / chưa đọc
- thêm sắp xếp theo severity hoặc thời gian
- thêm drill-down sang heatmap hoặc chuyến liên quan
- thêm xử lý hàng loạt
