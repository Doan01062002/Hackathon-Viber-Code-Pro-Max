# Hướng dẫn kết nối dự án với PostgreSQL trên AWS RDS

Tài liệu này mô tả cấu hình PostgreSQL RDS đang dùng cho dự án và cách để một
thành viên mới thiết lập môi trường local. Không đưa mật khẩu thật vào tài liệu
hoặc commit file `.env` lên Git.

## 1. Cấu hình hiện tại

| Thành phần | Giá trị |
|---|---|
| AWS Region | Asia Pacific (Singapore), `ap-southeast-1` |
| Dịch vụ | Amazon RDS for PostgreSQL |
| DB identifier | `viber-coding-pro-max-db` |
| Database | `viber_coding_pro_max` |
| Master user hiện tại | `appadmin` |
| Port | `5432` |
| Instance | `db.t4g.micro` |
| Storage | 20 GiB |
| SSL | Bắt buộc trong connection string bằng `sslmode=require` |
| Schema | 21 bảng trong `schema.sql` |

Endpoint và mật khẩu phải lấy từ chủ dự án hoặc AWS Console. Luôn copy endpoint
trực tiếp từ **RDS > Databases > viber-coding-pro-max-db > Connectivity &
security** để tránh gõ sai ký tự.

## 2. Thiết lập cho thành viên mới

### Bước 1: Clone và mở thư mục dự án

```powershell
git clone <repository-url>
cd Hackathon-Viber-Code-Pro-Max
```

### Bước 2: Tạo Python virtual environment

Dự án được kiểm tra với Python 3.12.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

Nếu PowerShell chặn script activate, có thể chạy Python trong venv trực tiếp:

```powershell
.\.venv\Scripts\python.exe --version
```

Trên macOS/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### Bước 3: Cài dependency

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

`requirements.txt` cài hai module nội bộ `ai` và `backend` ở editable mode.
Dependency PostgreSQL của backend gồm SQLAlchemy 2 và `psycopg` 3.

### Bước 4: Tạo file `.env`

Copy file mẫu:

```powershell
Copy-Item .env.example .env
```

Nhận `DATABASE_URL` từ chủ dự án qua kênh riêng, hoặc tự điền theo mẫu:

```env
DATABASE_URL="postgresql+psycopg://appadmin:<PASSWORD>@<RDS_ENDPOINT>:5432/viber_coding_pro_max?sslmode=require"
```

Lưu ý:

- Không thêm dấu cách trong URL.
- Nếu password chứa ký tự dành riêng trong URL như `#`, `%`, `?`, `:`, `/` hoặc
  `@`, password phải được URL-encode.
- Không commit `.env`. Repo đã ignore `.env` và `.venv`.
- Frontend không kết nối trực tiếp tới PostgreSQL; chỉ backend được dùng
  `DATABASE_URL`.

### Bước 5: Kiểm tra kết nối

```powershell
python -c "from backend.database import get_database_status; print(get_database_status())"
```

Kết quả đúng:

```text
ok
```

### Bước 6: Kiểm tra hoặc khởi tạo schema

```powershell
python scripts/init_db.py
```

Lần đầu trên database trống:

```text
Schema initialized successfully (21 tables).
```

Nếu schema đã tồn tại:

```text
Schema already initialized (21 tables).
```

Script có thể chạy lại an toàn. Nếu chỉ có một phần schema tồn tại, script sẽ
dừng với lỗi `Partial schema detected` thay vì tiếp tục tạo một database không
nhất quán.

### Bước 7: Chạy backend

```powershell
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Mở `http://localhost:8000/health`. Kết quả mong đợi:

```json
{
  "status": "ok",
  "env": "development",
  "database": "ok"
}
```

API documentation: `http://localhost:8000/docs`.

## 3. Cách RDS đã được tạo

Phần này dành cho người cần tái tạo database trên một AWS account khác.

1. Mở **Amazon RDS** và chọn **Create with full configuration**.
2. Chọn engine **PostgreSQL**, không chọn Aurora.
3. Chọn **Full configuration**, template **Free tier** hoặc **Dev/Test**.
4. Chọn `db.t4g.micro`, Single-AZ và 20 GiB General Purpose SSD.
5. Chọn **Password authentication** và **Self managed credentials**.
6. Đặt initial database name là `viber_coding_pro_max`.
7. Giữ port `5432`, Default VPC và DB subnet group `default`.
8. Chọn **Public access: Yes** để máy local có thể kết nối.
9. Tạo security group riêng, ví dụ `viber-postgres-dev-sg`.
10. Không bật RDS Proxy, Enhanced Monitoring hoặc DevOps Guru cho môi trường
    hackathon.
11. Giữ encryption bật và backup retention tối thiểu 1 ngày.

Sau khi DB ở trạng thái **Available**, mở security group và thêm inbound rule:

```text
Type: PostgreSQL
Protocol: TCP
Port: 5432
Source: 0.0.0.0/0
```

Cấu hình `0.0.0.0/0` giúp thành viên chỉ cần `.env` là kết nối được từ mọi mạng,
nhưng đồng thời công khai cổng database ra Internet. Đây chỉ là lựa chọn đơn giản
cho giai đoạn hackathon. Phải dùng password mạnh, SSL, không công khai `.env`, và
nên thay bằng IP allowlist hoặc security-group-to-security-group khi deploy.

## 4. Xử lý lỗi thường gặp

### `getaddrinfo failed` hoặc `DNS name does not exist`

Endpoint bị gõ sai. Copy lại endpoint bằng nút copy trong AWS Console; không đọc
và gõ lại từ ảnh chụp màn hình.

### `connection timed out`

Kiểm tra:

- RDS status là `Available`.
- `Publicly accessible` là `Yes`.
- Security group có inbound PostgreSQL TCP `5432`.
- Firewall hoặc mạng local không chặn outbound port `5432`.

### `password authentication failed`

Kiểm tra username, password và URL encoding. Không gửi toàn bộ `DATABASE_URL`
vào issue, chat công khai hoặc log CI.

### Health endpoint trả `database: unavailable`

Backend vẫn chạy nhưng không thực hiện được `SELECT 1`. Kiểm tra `.env`, endpoint,
security group và trạng thái RDS theo các mục phía trên.

## 5. Kiểm tra code trước khi push

```powershell
python -m ruff check backend scripts/init_db.py
python -m pytest backend/tests -q
```

Kết quả tại thời điểm viết tài liệu: Ruff đạt và `6 passed`.
