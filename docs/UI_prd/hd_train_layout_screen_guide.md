# HD Màn Hình Toa Tàu Và Sơ Đồ Ghế

## Mục đích

Màn hình `Toa tàu` dùng để chọn toa và xem sơ đồ ghế chi tiết. Đây là nơi phục vụ các thao tác vận hành liên quan đến:

- theo dõi tải theo từng toa
- giữ chỗ
- mở khóa ghế
- ưu tiên nhóm ghế
- can thiệp quota theo chặng

## Đối tượng sử dụng

- Điều độ viên
- Nhóm vận hành ghế / chỗ
- Revenue Manager khi cần can thiệp chi tiết tới mức ghế

## Chức năng chính trên màn hình

### 1. Danh sách toa tàu

Phần đầu màn hình liệt kê các toa hiện có, với thông tin:

- tên toa
- loại chỗ
- tải hiện tại
- nút chọn toa

Mục tiêu là giúp người dùng chọn nhanh đúng toa để thao tác.

### 2. Sơ đồ ghế chi tiết

Sau khi chọn toa, hệ thống hiển thị lưới ghế. Mỗi ghế có trạng thái trực quan:

- còn trống
- đang chọn
- đang giữ chỗ
- khóa vận hành

Mục tiêu là cho phép điều phối tới cấp ghế cụ thể.

### 3. Chú giải và thao tác

Khối bên phải giải thích ý nghĩa màu/trạng thái ghế và cung cấp các hành động:

- `Giữ hoặc mở khóa ghế`
- `Ưu tiên nhóm ghế`
- `Chuyển sang quota chặng`

## Giá trị sử dụng

Màn hình này giúp:

- trực quan hóa năng lực thật ở cấp toa / ghế
- hỗ trợ quyết định can thiệp nhanh
- kết nối logic doanh thu với vận hành thực tế

## Trạng thái UI hiện tại

Màn hình hiện đã có:

- grid danh sách toa
- progress tải theo toa
- sơ đồ ghế dạng lưới
- legend trạng thái ghế
- nhóm action cơ bản

## Gợi ý nâng cấp sau này

- chọn nhiều ghế cùng lúc
- thêm tooltip chi tiết cho từng ghế
- hiển thị hành khách / giữ chỗ theo mã đặt
- thêm lọc theo loại chỗ hoặc trạng thái ghế
- tích hợp thao tác backend thật
