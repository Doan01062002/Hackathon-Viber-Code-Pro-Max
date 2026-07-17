# HD Màn Hình Báo Giá Và Phương Án Thay Thế

## Mục đích

Màn hình `Báo giá và phương án thay thế` dùng để nhập yêu cầu OD và xem giá đề xuất từ hệ thống. Đây là nơi giúp người dùng hiểu:

- tuyến đi đang được định giá như thế nào
- còn bao nhiêu chỗ
- chi phí cơ hội là bao nhiêu
- có phương án thay thế nào nếu chặng chính quá nóng

## Đối tượng sử dụng

- Revenue Manager
- Nhóm kinh doanh cần tham chiếu logic giá
- Điều độ hoặc người giám sát giá theo chặng

## Chức năng chính trên màn hình

### 1. Biểu mẫu báo giá

Phần đầu màn hình có form nhập:

- `Ga đi`
- `Ga đến`
- `Loại chỗ`
- `Ngày đi`

Mục tiêu là tạo ngữ cảnh báo giá trước khi hệ thống trả về kết quả.

### 2. Kết quả báo giá

Khối kết quả hiển thị:

- giá đề xuất cuối cùng
- khả dụng
- chi phí cơ hội
- nút cổ chai

Khối này cho người dùng câu trả lời nhanh nhất về mức giá AI đang đề xuất.

### 3. Thẻ diễn giải giá

Phần diễn giải giúp người dùng hiểu lý do đằng sau giá:

- bid price đang cao hay thấp
- nhu cầu có vượt tồn kho không
- hệ thống có đang ưu tiên luồng dài không

Mục tiêu là tăng tính minh bạch khi áp dụng giá đề xuất.

### 4. Lựa chọn thay thế

Khối cuối màn hình hiển thị các phương án khác nếu tuyến chính đang quá nóng hoặc không tối ưu, ví dụ:

- tàu khác
- khung giờ thấp điểm
- loại chỗ khác
- phương án nối chuyến

Mỗi lựa chọn gồm:

- tên phương án
- giá
- ghi chú khả dụng
- nút chọn phương án

## Giá trị sử dụng

Màn hình này giúp:

- đưa ra giá nhanh và có giải thích
- hỗ trợ quyết định giữa các tuyến hoặc loại chỗ
- giữ tỷ lệ chuyển đổi khi luồng chính đã quá tải

## Trạng thái UI hiện tại

Màn hình hiện đã có:

- form báo giá
- khối kết quả
- card diễn giải
- danh sách phương án thay thế

## Gợi ý nâng cấp sau này

- gọi API thực từ `/v1/quote`
- thêm validation form
- thêm chọn ngày bằng date picker
- thêm lịch sử báo giá gần nhất
- thêm so sánh giá với baseline hiện tại
