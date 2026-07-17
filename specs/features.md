# Specs — Danh sách Tính năng & Yêu cầu Chức năng (Features)

Tài liệu này liệt kê chi tiết các tính năng của hệ thống **Smart Rail Revenue Management (SRRM)** được phân nhóm theo 3 khối lõi và các chức năng nền tảng dùng chung của MVP.

---

## 1. KHỐI 1 — Dự báo & Phân tích Nhu cầu (Forecasting & Analytics)

Khối này cung cấp các phân tích dữ liệu lịch sử và đưa ra dự báo nhu cầu đi lại tiềm năng để làm đầu vào cho bài toán tối ưu phân bổ chỗ.

| Mã Tính năng | Tên Yêu cầu | Mô tả Chi tiết & Tiêu chí Chấp nhận |
|---|---|---|
| **FR1.1** | Dự báo nhu cầu OD | Ước lượng nhu cầu đi lại cho từng cặp `(ga đi, ga đến, ngày đi, mã tàu, loại chỗ, số ngày đặt trước)`. Trả về cả trị dự báo điểm và khoảng tin cậy. |
| **FR1.2** | Đặc trưng dự báo | Tích hợp các đặc trưng: ngày trong tuần/tháng, mùa vụ, ngày lễ/Tết, chiều đi–về, thời tiết, sự kiện địa phương, thông tin giá hiện tại và giá đối thủ. |
| **FR1.3** | Giải kiểm duyệt nhu cầu | Áp dụng thuật toán EM để khôi phục nhu cầu tiềm năng thực tế từ các chuyến tàu đã hết vé sớm trong lịch sử. |
| **FR1.4** | Đường cong đặt vé | Mô hình hóa tiến độ mua vé tích lũy theo thời gian đặt trước để cập nhật dự báo nhu cầu cuối cùng liên tục. |
| **FR1.5** | Cập nhật dự báo động | Tính toán lại dự báo nhu cầu khi có lô dữ liệu bán vé mới cập nhật trong thời gian cho phép. |
| **FR1.6** | Phân tích tải chặng | Tính toán sức chứa, số ghế đã bán/giữ/còn trống, tỷ lệ lấp lầy và doanh thu dự kiến cho từng chặng nhỏ liên tiếp dọc hành trình tàu. |
| **FR1.7** | Heatmap tải chặng | Trực quan hóa tải chặng dạng biểu đồ nhiệt theo thời gian, giúp Revenue Manager nhận diện ngay các chặng quá tải hoặc trống nhiều trong 1 thao tác. |

---

## 2. KHỐI 2 — Tối ưu hóa phân bổ chỗ (Inventory Optimization)

Khối này chịu trách nhiệm phân chia ghế hợp lý giữa các chặng ngắn và chặng dài để tối đa hóa doanh thu tổng chuyến.

| Mã Tính năng | Tên Yêu cầu | Mô tả Chi tiết & Tiêu chí Chấp nhận |
|---|---|---|
| **FR2.1** | Xác định hạn ngạch chỗ | Tính toán hạn ngạch vé (quota) bán cho khách toàn tuyến, chặng dài, chặng vừa, chặng ngắn và chỗ giữ cho các ga trung gian. |
| **FR2.2** | Kiểm soát bằng Bid Price | Ra quyết định chấp nhận/từ chối yêu cầu mua vé dựa trên quy tắc: Giá vé đề xuất phải lớn hơn hoặc bằng tổng Bid Price các chặng mà hành trình đi qua: $f_j \ge \sum_{\ell} a_{\ell j} \cdot \pi_\ell$. |
| **FR2.3** | Cập nhật Bid Price động | Tính toán lại Bid Price và hạn ngạch tức thời khi có biến động đặt vé, hủy vé hoặc thay đổi sơ đồ đoàn tàu. |
| **FR2.4** | Đề xuất tách đoạn | Tự động đề xuất thời điểm nhả chỗ giữ chặng dài để chuyển sang bán chặng ngắn hoặc ngược lại theo tiến độ bán thực tế. |
| **FR2.5** | Ghép đoạn trống | Tự động tìm kiếm các đoạn trống xen kẽ của cùng một ghế vật lý và đề xuất tạo thành các vé chặng ngắn liên kết nhằm tận dụng tối đa ghế. |
| **FR2.6** | Gán ghế giảm phân mảnh | Sử dụng thuật toán Interval Partitioning gán ghế vật lý sao cho lượng ghế dùng không vượt tải chồng lấn cực đại và giảm thiểu số ghế trống bị chia cắt. |
| **FR2.7** | Gợi ý ghép đổi chỗ | (Tính năng cơ bản) Đề xuất phương án đổi chỗ dọc đường cho khách khi chặng dài hết ghế liền, nhưng ghép được từ 2 chặng ngắn trống ghế khác nhau của cùng 1 chuyến tàu. |
| **FR2.8** | Tái phân bổ tồn kho | Giải phóng hạn ngạch chặng dài chưa bán được cận ngày đi để mở bán chặng ngắn đang có nhu cầu cao. |

---

## 3. KHỐI 3 — Định giá động (Dynamic Pricing)

Khối này tính toán mức giá bán tối ưu theo chặng và thời điểm mở bán trong khung trần/sàn được phê duyệt.

| Mã Tính năng | Tên Yêu cầu | Mô tả Chi tiết & Tiêu chí Chấp nhận |
|---|---|---|
| **FR3.1** | Đề xuất giá theo Bid Price | Giá vé đề xuất được tính toán dưới dạng markup trên chi phí cơ hội: $p_j^* = \text{Markup}(c_j)$. Luồng đi qua chặng khan hiếm sẽ tự động có giá cao hơn. |
| **FR3.2** | Các yếu tố định giá | Tích hợp các yếu tố: tải chặng, số ngày tới ngày đi, tốc độ bán vé thực tế, loại chỗ, tính chất ngày cuối tuần/lễ tết. |
| **FR3.3** | Phân hạng sản phẩm giá | Hỗ trợ cấu hình các hạng vé: Tiết kiệm (mua sớm, không hoàn hủy), Tiêu chuẩn, Linh hoạt, Phút chót, Nhóm/khứ hồi. |
| **FR3.4** | Định giá theo tải chặng | Hành trình đi qua các chặng "nút cổ chai" gần đầy sẽ tăng giá (trong biên độ trần); hành trình qua các chặng trống được áp dụng giá khuyến mãi chéo. |
| **FR3.5** | Điều tiết cầu liên tàu | Đề xuất điều chỉnh giá để chuyển dịch cầu từ các tàu quá tải sang các tàu thấp điểm chạy gần khung giờ. |
| **FR3.6** | Ràng buộc trần/sàn cứng | Ép cứng giới hạn giá tối đa/tối thiểu ($p_{\min} \le p \le p_{\max}$), giới hạn bước nhảy giá liên tiếp không vượt $\Delta_{\max}$, không định giá dựa trên thông tin cá nhân. |
| **FR3.7** | Giải thích đề xuất giá | Cung cấp phân tích diễn giải lý do đưa ra mức giá cụ thể (ví dụ: do chặng A-B bị quá tải làm bid price tăng $X\%$). |

---

## 4. CHỨC NĂNG NỀN TẢNG (Cross-cutting)

| Mã Tính năng | Tên Yêu cầu | Mô tả Chi tiết & Tiêu chí Chấp nhận |
|---|---|---|
| **FR4.1** | Dashboard Phân tích | Màn hình hiển thị Heatmap chặng, biểu đồ tốc độ bán (booking curve) thực tế so với dự báo, danh sách đoạn trống ghép được. |
| **FR4.2** | Mô phỏng & So sánh | Giao diện chạy thử nghiệm chính sách giá/hạn ngạch mới và so sánh kết quả doanh thu dự kiến với kết quả bán thực tế trong lịch sử. |
| **FR4.3** | Cảnh báo tự động | Phát ra cảnh báo (qua màn hình/email/slack) khi phát hiện chặng sắp cháy vé sớm hoặc chặng có nguy cơ trống ghế cao cận ngày chạy. |
| **FR4.4** | Nhật ký kiểm toán | Ghi nhận chi tiết lịch sử thay đổi hạn ngạch, thay đổi giá, người thực hiện và lý do thay đổi để phục vụ kiểm toán hệ thống. |
| **FR4.5** | Vòng lặp phản hồi khép kín | Thiết lập luồng dữ liệu tự động phản hồi: dữ liệu vé bán thực tế cập nhật lại mô hình dự báo nhu cầu $\rightarrow$ chạy lại tối ưu DLP $\rightarrow$ cập nhật lại bid price và bảng giá động. |
