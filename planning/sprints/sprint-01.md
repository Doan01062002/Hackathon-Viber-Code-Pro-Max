# Sprint 1 — Xây dựng Lõi Thuật toán & Kiểm chứng Lịch sử (Phase 1)

## 1. Mục tiêu Sprint
Xây dựng và hoàn thiện lõi thuật toán của 3 phân hệ (Dự báo nhu cầu, Tối ưu DLP sinh Bid Price, và Định giá động). Thực hiện chạy thử nghiệm (Backtesting) trên dữ liệu lịch sử của 1-3 mã tàu để chứng minh hiệu quả tăng doanh thu và tỷ lệ lấp đầy ghế-km so với thực tế bán trước đó.

---

## 2. Chỉ số Cam kết hoàn thành (Sprint KPIs)
* **MAPE dự báo nhu cầu:** $\le 15\%$ đối với các luồng OD chính.
* **Độ co giãn cầu:** Học được hệ số co giãn $\epsilon$ hoặc $\alpha$ hợp lý từ dữ liệu lịch sử.
* **Thời gian giải bài toán tối ưu DLP:** $\le 2$ giây cho một chuyến tàu (dưới 10 ga).
* **Kết quả so sánh doanh thu:** Doanh thu mô phỏng của AI vượt doanh thu lịch sử thực tế từ **3% đến 8%**.

---

## 3. Danh sách Tác vụ (Backlog Items in Sprint)

| Mã tác vụ | Tên Tác vụ | Người thực hiện | Trạng thái |
|---|---|---|---|
| **SRRM-001** | Phát triển mô hình dự báo nhu cầu OD & EM algorithm | AI Engineer | Sẵn sàng |
| **SRRM-002** | Xây dựng bộ tối ưu DLP (OR-Tools) & gán ghế vật lý | AI Engineer | Sẵn sàng |
| **SRRM-003** | Lập trình lõi định giá động và bộ lọc ràng buộc trần/sàn | AI/BE Dev | Sẵn sàng |
| **SRRM-004-Part1** | Xây dựng engine mô phỏng & chạy backtest dữ liệu lịch sử | Data Scientist | Sẵn sàng |

---

## 4. Kế hoạch chi tiết theo ngày (2 tuần)
* **Ngày 1-3:** Làm sạch dữ liệu, xử lý dữ liệu vé bán trống chặng. Viết giải thuật khôi phục nhu cầu EM.
* **Ngày 4-6:** Huấn luyện mô hình dự báo Poisson cho các luồng OD. Định nghĩa `AgentState` và LangGraph nodes trong thư mục `ai/`.
* **Ngày 7-9:** Thiết lập mô hình tuyến tính DLP trong OR-Tools/HiGHS. Xuất giá trị đối ngẫu làm Bid Price. Lập trình thuật toán Interval Partitioning gán ghế.
* **Ngày 10-12:** Kết nối đầu ra Bid Price sang module định giá. Áp dụng công thức markup và ràng buộc trần/sàn cứng.
* **Ngày 13-14:** Chạy thử nghiệm giả lập (backtest) trên 1 tháng dữ liệu lịch sử của tàu SE1/SE2. Xuất báo cáo so sánh KPI dạng JSON gửi về Backend.
