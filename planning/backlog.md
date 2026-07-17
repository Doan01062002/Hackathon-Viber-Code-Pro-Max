# Planning — Danh mục Yêu cầu Phát triển (Product Backlog)

Tài liệu này quản lý toàn bộ các hạng mục công việc cần thực hiện để hoàn thiện giải pháp **SRRM**. Các công việc được phân vào 4 Epic lớn tương ứng với 3 Khối logic và phần Nền tảng/Giao diện.

---

## EPIC 1 — Khối Dự báo & Phân tích Nhu cầu (Forecasting)

* **SRRM-F1: Thu thập và Tiền xử lý Dữ liệu Lịch sử**
  * *Mô tả:* Xây dựng pipeline xử lý dữ liệu vé bán, lịch trình tàu, và cơ cấu sơ đồ ghế.
  * *Độ ưu tiên:* Cao (Blocker cho các task sau)
* **SRRM-F2: Giải thuật Khôi phục Nhu cầu (Unconstraining - EM Algorithm)**
  * *Mô tả:* Lập trình thuật toán EM để ước lượng nhu cầu tiềm năng thực tế từ dữ liệu vé bị cắt khi hết chỗ.
  * *Độ ưu tiên:* Cao
* **SRRM-F3: Mô hình Dự báo Nhu cầu OD (LightGBM Regression)**
  * *Mô tả:* Huấn luyện mô hình dự báo điểm và khoảng nhu cầu cho từng cặp ga đi/đến theo ngày và loại chỗ.
  * *Độ ưu tiên:* Cao
* **SRRM-F4: Phân tích và Trực quan hóa Tải chặng**
  * *Mô tả:* Xây dựng logic phân tích tải chặng dọc tuyến đường và API xuất dữ liệu Heatmap.
  * *Độ ưu tiên:* Trung bình

---

## EPIC 2 — Khối Tối ưu Phân bổ Chỗ (Inventory Optimization)

* **SRRM-O1: Xây dựng Lõi tối ưu Tuyến tính DLP (Deterministic Linear Program)**
  * *Mô tả:* Sử dụng Google OR-Tools thiết lập mô hình quy hoạch tuyến tính phân bổ quota chỗ và xuất Bid Price đối ngẫu cho từng chặng.
  * *Độ ưu tiên:* Cao
* **SRRM-O2: Thuật toán Gán ghế Vật lý (Interval Partitioning)**
  * *Mô tả:* Thiết lập thuật toán greedy/tối ưu xếp chồng booking không giao nhau để giảm phân mảnh ghế vật lý.
  * *Độ ưu tiên:* Cao
* **SRRM-O3: Ghép chặng trống (Gap Combining)**
  * *Mô tả:* Phát hiện các chặng trống liền kề của cùng một ghế vật lý và xuất phương án ghép vé chặng ngắn.
  * *Độ ưu tiên:* Trung bình
* **SRRM-O4: Cơ chế Giải phóng & Tái phân bổ Quota cận ngày**
  * *Mô tả:* Tự động nhả hạn ngạch chặng dài chưa bán được để chuyển sang chặng ngắn khi cận giờ tàu chạy.
  * *Độ ưu tiên:* Thấp

---

## EPIC 3 — Khối Định giá Động (Dynamic Pricing)

* **SRRM-P1: Công thức tính Giá động dựa trên Bid Price**
  * *Mô tả:* Cài đặt thuật toán tính toán giá vé tối ưu bằng cách cộng/nhân hệ số markup trên tổng bid price các chặng đi qua.
  * *Độ ưu tiên:* Cao
* **SRRM-P2: Áp đặt Ràng buộc Trần/Sàn & Biến động tối đa ($\Delta_{\max}$)**
  * *Mô tả:* Lớp lọc bảo vệ ép giá vé nằm trong khung quy định và hạn chế tăng/giảm sốc giữa các lần cập nhật.
  * *Độ ưu tiên:* Cao
* **SRRM-P3: Cơ chế Giải thích Đề xuất Giá (Explainable Pricing)**
  * *Mô tả:* Sinh chuỗi diễn giải lý do tăng/giảm giá vé dựa trên mức độ khan hiếm chặng cho Revenue Manager.
  * *Độ ưu tiên:* Trung bình
* **SRRM-P4: Điều tiết Cầu chéo giữa các Tàu**
  * *Mô tả:* Gợi ý giảm giá giờ thấp điểm hoặc tăng giá giờ cao điểm của các tàu chạy gần khung giờ để cân bằng tải.
  * *Độ ưu tiên:* Thấp

---

## EPIC 4 — Tích hợp & Giao diện (Platform & UI)

* **SRRM-I1: Xây dựng Dashboard Quản trị Doanh thu (Next.js)**
  * *Mô tả:* Thiết kế giao diện theo dõi heatmap tải chặng, ma trận nhu cầu OD và biểu đồ đặt vé.
  * *Độ ưu tiên:* Cao
* **SRRM-I2: Giao diện Mô phỏng Chính sách (Simulation & Backtest UI)**
  * *Mô tả:* Màn hình cho phép điều chỉnh tham số tối ưu, chạy mô phỏng trên dữ liệu lịch sử và xuất biểu đồ so sánh doanh thu.
  * *Độ ưu tiên:* Cao
* **SRRM-I3: API Gateway & Định tuyến LangGraph Agent**
  * *Mô tả:* Phát triển các REST API trên FastAPI và cấu hình LangGraph agent để tiếp nhận yêu cầu tự nhiên từ chatbot.
  * *Độ ưu tiên:* Cao
* **SRRM-I4: Ghi log Kiểm toán & Phân quyền RBAC**
  * *Mô tả:* Lưu vết hoạt động điều chỉnh của Revenue Manager và bảo mật phân quyền truy cập.
  * *Độ ưu tiên:* Trung bình
