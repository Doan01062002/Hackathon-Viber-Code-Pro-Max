# HD Màn Hình Đăng Nhập

## Mục đích

Màn hình `Đăng nhập` là điểm vào của hệ thống SRRM. Mục tiêu của màn hình này là:

- xác thực người dùng
- đưa người dùng vào workspace phù hợp
- hỗ trợ vào nhanh trong môi trường demo hoặc vận hành thử

## Đối tượng sử dụng

- Revenue Manager
- Điều độ viên
- Nhóm quản trị hoặc IT

## Chức năng chính trên màn hình

### 1. Trường nhập thông tin đăng nhập

Màn hình có hai trường cơ bản:

- `Email`
- `Mật khẩu`

Đây là nền tảng cho auth flow chính thức trong tương lai.

### 2. Nút đăng nhập

Nút `Đăng nhập` đưa người dùng vào dashboard chính sau khi xác thực.

### 3. Vào nhanh với vai trò điều độ

Nút phụ `Vào nhanh với vai trò điều độ` phục vụ:

- demo
- kiểm thử nhanh
- môi trường giả lập chưa tích hợp auth đầy đủ

## Giá trị sử dụng

Màn hình này giúp:

- tạo điểm bắt đầu rõ ràng cho hệ thống
- phân biệt ngữ cảnh truy cập
- hỗ trợ luồng demo nhanh cho hackathon hoặc review nội bộ

## Trạng thái UI hiện tại

Màn hình hiện đã có:

- phần giới thiệu hệ thống
- form email / mật khẩu
- CTA đăng nhập
- CTA vào nhanh

## Gợi ý nâng cấp sau này

- tích hợp JWT thực
- validation lỗi đăng nhập
- quên mật khẩu
- guard route theo vai trò
- nhớ phiên làm việc
