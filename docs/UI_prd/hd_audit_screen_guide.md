# HD Màn Hình Nhật Ký Kiểm Toán

## Mục đích

Màn hình `Nhật ký kiểm toán` dùng để theo dõi và truy vết các thay đổi quan trọng trong hệ thống vận hành doanh thu đường sắt. Đây là nơi giúp đội IT, quản trị hoặc vận hành kiểm tra:

- ai đã thực hiện thay đổi
- thay đổi gì đã xảy ra
- thay đổi được áp dụng lên thực thể nào
- thay đổi diễn ra vào thời điểm nào
- dữ liệu trước và sau thay đổi khác nhau ra sao

## Đối tượng sử dụng

- Nhóm IT / quản trị hệ thống
- Nhóm vận hành cần đối soát lịch sử thao tác
- Người phụ trách kiểm tra chính sách giá, quota hoặc khóa ghế

## Chức năng chính trên màn hình

### 1. Bộ lọc kiểm toán

Khối đầu màn hình cho phép lọc nhanh dữ liệu theo các tiêu chí:

- `Người thao tác`
- `Hành động`
- `Ngày`

Mục tiêu của bộ lọc là giúp người dùng thu hẹp phạm vi tìm kiếm khi cần rà soát một thay đổi cụ thể.

### 2. Bảng nhật ký kiểm toán

Khối trung tâm của màn hình là bảng log kiểm toán, gồm các cột:

- `Actor`: người thực hiện thao tác
- `Hành động`: loại thay đổi hoặc thao tác đã thực hiện
- `Thực thể`: đối tượng bị tác động, ví dụ policy giá hoặc nhóm ghế
- `Thời gian`: thời điểm thay đổi xảy ra

Bảng này hỗ trợ người dùng quét nhanh toàn bộ lịch sử thay đổi theo dạng dòng thời gian và đối chiếu theo từng bản ghi.

### 3. Dữ liệu trước thay đổi

Khối này hiển thị trạng thái dữ liệu trước khi cập nhật. Mục đích là để kiểm tra hệ thống đang ở cấu hình nào trước khi thao tác được áp dụng.

Ví dụ:

- mức `discount_cap`
- tỷ lệ `quota_mid_stop`
- trạng thái ghế hoặc policy đang active

### 4. Dữ liệu sau thay đổi

Khối này hiển thị giá trị mới sau khi thao tác hoàn tất. Người dùng có thể so sánh trực tiếp với khối `Dữ liệu trước thay đổi` để xác nhận thay đổi đã được áp dụng đúng.

## Giá trị sử dụng

Màn hình này đặc biệt hữu ích trong các tình huống:

- cần truy vết lỗi do thay đổi cấu hình
- cần kiểm tra ai đã phê duyệt một chính sách giá
- cần đối soát việc khóa / mở ghế vận hành
- cần rollback hoặc xác nhận thay đổi trong ca trực
- cần cung cấp log để giải trình nội bộ

## Trạng thái UI hiện tại

Màn hình hiện tại đã có các thành phần UI chính:

- header chung của hệ thống
- bộ lọc kiểm toán
- bảng nhật ký kiểm toán dạng `table`
- hai khối đối chiếu `trước thay đổi` và `sau thay đổi`

## Gợi ý nâng cấp sau này

- thêm phân trang hoặc infinite scroll cho log dài
- thêm bộ lọc theo loại thực thể
- thêm tìm kiếm theo từ khóa
- thêm export CSV / Excel
- thêm xem chi tiết từng log trong drawer hoặc modal
- thêm diff highlight để làm nổi bật trường nào đã thay đổi
