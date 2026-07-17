# HD Màn Hình Mô Phỏng Và Phê Duyệt

## Mục đích

Màn hình `Mô phỏng và phê duyệt` dùng để thử các kịch bản chính sách trước khi áp dụng thật. Đây là nơi người dùng kiểm tra:

- nếu đổi chính sách thì doanh thu tăng hay giảm
- hệ số lấp đầy thay đổi thế nào
- ga trung gian có bị ảnh hưởng không
- nên phê duyệt hay ghi đè thủ công

## Đối tượng sử dụng

- Revenue Manager
- Quản lý vận hành doanh thu
- Người có quyền phê duyệt chính sách

## Chức năng chính trên màn hình

### 1. Chọn kịch bản mô phỏng

Người dùng có thể chọn nhanh các scenario như:

- `Cuối tuần tháng 7`
- `Khung giờ thấp điểm`
- `Cân bằng dịp Tết`

Ngoài ra có CTA để chạy mô phỏng từ API.

### 2. Tóm tắt kết quả

Khối summary trả lời nhanh:

- chính sách nào đang được thử
- tăng doanh thu bao nhiêu
- tăng lấp đầy bao nhiêu
- giảm từ chối chặng ngắn bao nhiêu

### 3. Biểu đồ so sánh

Biểu đồ cột hiển thị doanh thu và sản lượng theo từng kịch bản để người dùng nhìn nhanh xu hướng tổng thể.

### 4. Bảng so sánh AI với hiện tại

Bảng này đối chiếu trực tiếp:

- doanh thu
- hệ số lấp đầy
- vé ga trung gian
- lượt tìm sold-out

Mục tiêu là hỗ trợ quyết định phê duyệt.

### 5. Hành động phê duyệt

Khối cuối màn hình có các hành động:

- `Phê duyệt chính sách`
- `Ghi đè thủ công`
- `Cập nhật giới hạn`

## Giá trị sử dụng

Màn hình này giúp:

- giảm rủi ro trước khi áp dụng policy thật
- cho người dùng so sánh AI với vận hành hiện tại
- hỗ trợ phê duyệt một cách an toàn và có căn cứ

## Trạng thái UI hiện tại

Màn hình hiện đã có:

- chọn scenario
- summary cards
- compare chart
- bảng so sánh
- action phê duyệt

## Gợi ý nâng cấp sau này

- tích hợp API `/v1/simulate`
- thêm trạng thái chạy mô phỏng
- thêm lưu kết quả scenario
- thêm compare chart dạng line hoặc waterfall
- thêm diff highlight giữa hiện tại và AI
