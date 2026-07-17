# PRD — Hệ thống AI Tối ưu Chỗ ngồi & Định giá linh hoạt cho Vận tải Hành khách Đường sắt

**Product Requirements Document — Phạm vi MVP (Vòng thi Vietnam Innovation Challenge 2026)**

| | |
|---|---|
| **Tên sản phẩm** | Smart Rail Revenue Management (SRRM) — *tên tạm* |
| **Phiên bản tài liệu** | v1.0 (Draft) |
| **Chủ sở hữu (PM)** | Tuyết Nga |
| **Trạng thái** | Đang review nội bộ |
| **Ngày cập nhật** | 17/07/2026 |
| **Phạm vi bản này** | MVP cho vòng thi — 3 khối: Dự báo & Phân tích, Tối ưu phân bổ chỗ, Định giá động |

---

## 1. Tóm tắt điều hành (Executive Summary)

Hiện nay việc phân bổ chỗ và định giá vé tàu hỏa chủ yếu dựa trên **quy tắc cố định**: mở/giữ chỗ theo luật cứng, dự báo nhu cầu chưa chính xác, và giá vé chưa phản ánh đúng cung–cầu theo từng chặng và từng thời điểm. Hệ quả là ghế trống cục bộ trên một số chặng trong khi chặng khác "cháy vé", hệ thống báo hết chỗ dù tàu vẫn còn năng lực, và doanh thu chưa được tối ưu.

SRRM là hệ thống AI chuyển việc phân bổ chỗ và định giá từ **quy tắc cố định sang vận hành động, dựa trên dữ liệu**. Sản phẩm gồm ba khối gắn kết qua một đại lượng toán học chung là **bid price** (chi phí cơ hội của một ghế trên một chặng):

1. **Dự báo & Phân tích** — ước lượng nhu cầu theo từng luồng ga đi–ga đến, phân tích tải từng chặng.
2. **Tối ưu phân bổ chỗ** — quyết định hạn ngạch bán theo chặng dài/ngắn và gán ghế vật lý để giảm phân mảnh.
3. **Định giá động** — đề xuất mức giá phản ánh khan hiếm theo chặng, trong khuôn khổ trần/sàn và minh bạch.

Bản PRD này giới hạn ở **MVP cho vòng thi**: một số ít mã tàu/tuyến, một số loại chỗ, chạy trên dữ liệu lịch sử và chế độ chạy song song (shadow), nhằm chứng minh hiệu quả trước khi mở rộng.

---

## 2. Bối cảnh & Vấn đề (Background & Problem)

### 2.1. Bối cảnh nghiệp vụ
Mỗi ghế trên một chuyến tàu có thể phục vụ nhiều hành khách trên các chặng liên tiếp không chồng lấn (ví dụ ghế bán A→C, sau đó bán tiếp C→E). Nếu hệ thống quản lý chỗ không tối ưu, cùng một ghế có thể trống trên chặng này trong khi nhu cầu chặng khác lại cao.

### 2.2. Các vấn đề hiện tại (pain points)
- **P1 — Từ chối sai:** Khách cần mua vé chặng ngắn nhưng hệ thống báo hết chỗ vì ghế đang giữ cho hành trình dài hơn.
- **P2 — Ghế trống cục bộ:** Ghế bị bỏ trống trên một hoặc vài chặng nằm giữa hai hành trình đã bán.
- **P3 — Nhu cầu lệch:** Nhu cầu giữa các ga phân bố không đều; có chặng quá tải, có chặng nhiều ghế trống.
- **P4 — Quy tắc cứng:** Mở bán chặng ngắn/dài hay giữ chỗ cho ga trung gian chủ yếu theo luật cố định.
- **P5 — Dự báo yếu:** Dự báo nhu cầu theo ga đi, ga đến, ngày đi, mã tàu, loại chỗ chưa chính xác.
- **P6 — Giá chưa phản ánh cung–cầu:** Giá vé không bám sát cung–cầu theo thời điểm và theo chặng; điều chỉnh giá chưa gắn với mục tiêu tối ưu doanh thu và hệ số sử dụng chỗ.
- **P7 — Khó đánh giá tác động:** Khó đánh giá đồng thời ảnh hưởng của một quyết định bán vé lên toàn bộ các chặng còn lại của hành trình.

### 2.3. Cơ hội
Áp dụng AI kết hợp thuật toán tối ưu để hỗ trợ phân bổ chỗ theo chặng, tách/ghép đoạn, và xây dựng chính sách giá linh hoạt — nâng hệ số sử dụng chỗ, giảm ghế trống cục bộ, tăng doanh thu và khả năng phục vụ khách tại ga trung gian.

---

## 3. Mục tiêu & Phi mục tiêu (Goals & Non-Goals)

### 3.1. Mục tiêu sản phẩm (Product Goals)
- **G1.** Dự báo nhu cầu theo từng luồng ga đi–ga đến, ngày, mã tàu, loại chỗ và thời điểm đặt, cập nhật liên tục theo dữ liệu mới.
- **G2.** Tối ưu phân bổ chỗ giữa chặng dài và ngắn; tự động đề xuất tách đoạn và ghép các đoạn trống để tăng số lần sử dụng mỗi ghế.
- **G3.** Đề xuất mức giá linh hoạt phản ánh cung–cầu theo chặng và thời điểm, trong khuôn khổ trần/sàn được duyệt.
- **G4.** Cung cấp cho quản lý công cụ mô phỏng và đánh giá chính sách bán vé trước khi áp dụng, có giải thích được (explainable) và cho phép can thiệp thủ công.

### 3.2. Mục tiêu vòng thi (MVP Goals)
- Chứng minh trên dữ liệu lịch sử rằng chính sách do AI đề xuất tốt hơn chính sách thực tế đã diễn ra (Phase 1).
- Đạt các chỉ tiêu thử nghiệm định lượng ở Mục 6.

### 3.3. Phi mục tiêu (Non-Goals — nằm ngoài MVP)
- **NG1.** Không triển khai production tích hợp trực tiếp bán vé thời gian thực trong MVP (chỉ chạy lịch sử + shadow).
- **NG2.** Không bao gồm quản lý danh sách chờ thông minh (waiting list) — để pha sau.
- **NG3.** Không bao gồm xếp chỗ nhóm/gia đình tối ưu — để pha sau.
- **NG4.** Không bao gồm ghép hành trình có đổi chỗ/đổi tàu ở mức tối ưu đầy đủ — MVP chỉ hỗ trợ gợi ý cơ bản, cảnh báo rõ.
- **NG5.** Không dùng học tăng cường (RL) cho định giá trong MVP — dùng phương pháp bid-price có công thức, giải thích được.
- **NG6.** Không cá nhân hóa giá theo người dùng; không dùng dữ liệu cá nhân nhạy cảm để định giá.

---

## 4. Phạm vi MVP (Scope)

### 4.1. Trong phạm vi (In-scope)
- **Tuyến & tàu:** 1–3 mã tàu trên một tuyến có nhiều ga trung gian và nhu cầu lệch rõ (ví dụ đề xuất: tuyến Bắc–Nam, tàu Thống Nhất, các ga chính Hà Nội – Vinh – Đồng Hới – Huế – Đà Nẵng – Nha Trang – Sài Gòn). *Danh sách tàu/ga cụ thể chốt với đối tác đường sắt.*
- **Loại chỗ:** 1–2 loại (ví dụ ngồi mềm điều hòa và giường nằm khoang 6) để giới hạn độ phức tạp.
- **Dữ liệu:** 1–3 năm dữ liệu lịch sử; cửa sổ thử nghiệm 1–3 tháng.
- **Chức năng:** Khối 1 (dự báo OD + heatmap tải chặng), Khối 2 (hạn ngạch bid-price + gán ghế/ghép đoạn trống), Khối 3 (định giá bid-price + trần/sàn), dashboard mô phỏng cho quản lý, kế hoạch thử nghiệm 3 pha.

### 4.2. Ngoài phạm vi (Out-of-scope) — xem NG1–NG6.

### 4.3. Giả định phạm vi
- Có quyền truy cập dữ liệu vé, hành trình, đội tàu, và (nếu có) lịch sử tìm kiếm ở mức ẩn danh.
- Có khung trần/sàn giá được cơ quan/doanh nghiệp phê duyệt để đưa vào ràng buộc.

---

## 5. Người dùng & Personas

| Persona | Vai trò | Nhu cầu chính | Cách dùng SRRM |
|---|---|---|---|
| **Quản lý điều vé / Revenue Manager** | Ra quyết định hạn ngạch, giá, chính sách | Nhìn tải chặng, dự báo, doanh thu dự kiến; phê duyệt/điều chỉnh đề xuất | Dashboard, mô phỏng, phê duyệt |
| **Điều độ / Kế hoạch chạy tàu** | Quản lý thành phần đoàn tàu, sức chứa | Cập nhật thay đổi đoàn tàu, ghế khóa/ưu tiên | Nhập cấu hình tàu; nhận cảnh báo |
| **Bộ phận CNTT / Tích hợp** | Vận hành, tích hợp hệ thống bán vé | API ổn định, log kiểm toán, phân quyền, rollback | Quản trị hệ thống, giám sát mô hình |
| **Hành khách** (gián tiếp) | Người mua vé | Có vé chặng cần mua, giá hợp lý, minh bạch, ít phải đổi chỗ | Hưởng lợi qua tính khả dụng & giá |
| **Ban giám khảo / Lãnh đạo** (MVP) | Đánh giá hiệu quả | Bằng chứng định lượng, tính khả thi & minh bạch | Xem báo cáo so sánh AI vs thực tế |

**Persona trọng tâm của MVP:** *Quản lý điều vé* — hệ thống là "trợ lý ra quyết định" cho nhóm này.

---

## 6. Chỉ số thành công & KPI (Success Metrics)

### 6.1. KPI mục tiêu (theo mục tiêu thử nghiệm của đề bài)

| Mã | Chỉ số | Mục tiêu MVP |
|---|---|---|
| K1 | Tăng hệ số sử dụng ghế-km (passenger-km utilization) | **+3% đến +8%** |
| K2 | Tăng doanh thu chuyến thử nghiệm | **+3% đến +10%** |
| K3 | Giảm ghế trống cục bộ trên chặng | **giảm ≥ 20%** |
| K4 | Tăng bán vé tại ga trung gian | **+ ≥ 10%** |
| K5 | Giảm số lượt tìm kiếm không thành công (unfulfilled search) | **giảm ≥ 15%** |
| K6 | Vi phạm chính sách giá & xã hội | **0 vi phạm** |
| K7 | Tốc độ tính lại (recalculation) | **gần thời gian thực** |

### 6.2. Chỉ số phụ trợ (đánh giá chất lượng)
Độ chính xác dự báo (MAE/MAPE, pinball loss cho phân vị), tỉ lệ lấp đầy & ghế-km, số khách phục vụ, doanh thu bình quân/ghế và /chuyến, tỉ lệ chặng trống, số đoạn trống ghép thành công & vé phát sinh, tỉ lệ đổi chỗ, tỉ lệ chuyển đổi tìm-kiếm→mua, tỉ lệ hoàn vé, mức biến động giá & khiếu nại liên quan giá, độ hài lòng, thời gian tính lại.

### 6.3. Định nghĩa "thành công của MVP"
MVP được coi là thành công nếu: (a) ở Phase 1 chính sách AI vượt chính sách lịch sử trên K1–K4 trong khoảng mục tiêu; (b) đạt K6 = 0 vi phạm; (c) đạt K7 gần thời gian thực trên quy mô 1 tàu.

---

## 7. Yêu cầu chức năng (Functional Requirements)

> Ký hiệu dùng chung: **chặng (leg)** = đoạn giữa 2 ga liên tiếp; **luồng OD** = cặp (ga đi, ga đến, loại chỗ); **bid price (π_ℓ)** = chi phí cơ hội của một ghế trên chặng ℓ.

### 7.1. KHỐI 1 — Dự báo & Phân tích (Forecasting & Analytics)

**User stories**
- *US1.1* — Là quản lý điều vé, tôi muốn xem nhu cầu dự báo cho từng luồng ga đi–ga đến (ví dụ Hà Nội–Vinh) theo ngày và loại chỗ, để lên kế hoạch phân bổ.
- *US1.2* — Là quản lý, tôi muốn thấy dự báo được cập nhật khi có dữ liệu bán mới, để điều chỉnh kịp thời.
- *US1.3* — Là quản lý, tôi muốn một heatmap tải theo chặng để nhận diện nhanh chặng sắp cháy vé, chặng trống nhiều, và chặng "nút cổ chai".

**Yêu cầu chức năng**

| Mã | Yêu cầu | Tiêu chí chấp nhận (Acceptance Criteria) |
|---|---|---|
| FR1.1 | Dự báo nhu cầu theo `(ga đi, ga đến, ngày, mã tàu, loại chỗ, số ngày đặt trước)` | Hệ thống xuất dự báo điểm + khoảng tin cậy cho mọi cặp OD trong phạm vi; MAPE báo cáo được theo phân khúc |
| FR1.2 | Dùng đặc trưng: ngày trong tuần/tháng, mùa, lễ/Tết, chiều đi–về, thời tiết, sự kiện địa phương, giá, khuyến mãi, giá đối thủ | Danh mục đặc trưng cấu hình được; thiếu đặc trưng không làm hỏng dự báo (xử lý missing) |
| FR1.3 | Giải kiểm duyệt nhu cầu (unconstrained demand) từ dữ liệu bị cắt do hết chỗ/chặn bán | Có tài liệu phương pháp (ví dụ EM); dự báo phản ánh nhu cầu tiềm năng, không chỉ vé đã bán |
| FR1.4 | Mô hình đường cong đặt vé (booking curve / pickup) theo lead time | Ước lượng nhu cầu cuối từ mức tích lũy hiện tại; cập nhật khi có vé mới |
| FR1.5 | Cập nhật dự báo liên tục | Khi có lô dữ liệu vé mới, dự báo được tính lại trong ngưỡng thời gian cấu hình |
| FR1.6 | Phân tích tải theo chặng: sức chứa, số ghế bán/giữ/trống, tỉ lệ lấp đầy, dự báo, thiếu/thừa ghế, giá TB & doanh thu dự kiến, ghế trống do phân bổ chưa tối ưu | Bảng số liệu đầy đủ theo từng chặng |
| FR1.7 | Trực quan hóa heatmap chặng × thời gian; đánh dấu chặng nguy cơ cháy vé, chặng trống cao, chặng nút cổ chai | Quản lý xác định được nút cổ chai trong ≤ 1 thao tác |

**Hướng tiếp cận kỹ thuật (định hướng cho kỹ sư):** Lõi dự báo dùng Gradient Boosting hồi quy Poisson/Tweedie (dữ liệu đếm); lớp phân phối dùng quantile regression hoặc Negative Binomial để xuất bất định; giải kiểm duyệt bằng EM; hòa hợp phân cấp (hierarchical reconciliation) cho các OD thưa. Deep learning (DeepAR/TFT) để mở rộng, không thuộc lõi MVP.

---

### 7.2. KHỐI 2 — Tối ưu hóa phân bổ chỗ (Inventory Optimization)

**User stories**
- *US2.1* — Là quản lý, tôi muốn hệ thống đề xuất nên giữ bao nhiêu chỗ cho khách chặng dài và bao nhiêu mở cho chặng ngắn, để không bán rẻ chỗ quý.
- *US2.2* — Là quản lý, tôi muốn hệ thống tự tìm và ghép các đoạn ghế trống thành vé mới, để giảm ghế trống cục bộ.
- *US2.3* — Là quản lý, tôi muốn quyết định chấp nhận/từ chối một yêu cầu vé có tính đến tác động lên các chặng còn lại.
- *US2.4* — Là quản lý, tôi muốn hạn ngạch tự điều chỉnh theo tiến độ bán thực tế và khi có hủy vé/thay đổi đoàn tàu.

**Yêu cầu chức năng**

| Mã | Yêu cầu | Tiêu chí chấp nhận |
|---|---|---|
| FR2.1 | Xác định hạn ngạch (quota) cho khách toàn tuyến, chặng dài, chặng vừa, chặng ngắn, và chỗ giữ cho ga trung gian | Xuất bảng hạn ngạch theo loại chặng cho mỗi tàu/ngày |
| FR2.2 | Điều khiển chấp nhận vé theo bid price: chấp nhận OD j khi giá vé f_j ≥ Σ_ℓ a_ℓj · π_ℓ (giá vé ≥ tổng chi phí cơ hội các chặng nó đi qua) | Với mỗi yêu cầu vé, hệ thống trả quyết định chấp nhận/từ chối kèm lý do (chi phí cơ hội) |
| FR2.3 | Tính lại bid price/hạn ngạch định kỳ và theo sự kiện (bán được vé, hủy, đổi đoàn tàu) | Sau sự kiện, giá trị cập nhật trong ngưỡng thời gian cấu hình |
| FR2.4 | Đề xuất tách đoạn (segmenting): mở bán từng chặng thay vì chỉ bán trọn tuyến; xác định thời điểm nhả chỗ giữ hoặc chuyển phân bổ giữa chặng dài/ngắn | Kế hoạch tách đoạn thay đổi động theo tiến độ bán |
| FR2.5 | Tìm & ghép đoạn trống (combining gaps): phát hiện khoảng trống trong từng ghế và tạo phương án vé mới | Ví dụ ghế bán HN–Vinh và Huế–ĐN thì đề xuất bán Vinh–Huế; danh sách đoạn ghép được xuất ra |
| FR2.6 | Gán ghế vật lý giảm phân mảnh | Số ghế dùng không vượt tải chồng lấn cực đại; tối đa hóa tái sử dụng ghế |
| FR2.7 | (Cơ bản) Gợi ý ghép hành trình có đổi chỗ chỉ khi không còn ghế liền, ga chuyển có đủ thời gian dừng, cùng loại chỗ, và khách đồng ý | Chỉ hiển thị khi thỏa điều kiện; giảm thiểu số lần đổi; cảnh báo rõ |
| FR2.8 | Nhả & tái phân bổ chỗ (release/reallocate) theo tiến độ: nhả chỗ giữ chặng dài chưa bán, xử lý tăng đột biến nhu cầu chặng ngắn, xử lý hủy vé/đổi thành phần đoàn tàu | Đề xuất điều chỉnh hạn ngạch theo thời gian, có log |

**Hướng tiếp cận kỹ thuật:** Lớp A (kiểm soát tồn kho) dùng Quy hoạch tuyến tính tất định (DLP): tối đa hóa tổng doanh thu Σ_j f_j·x_j với ràng buộc sức chứa từng chặng Σ_j a_ℓj·x_j ≤ c_ℓ; biến đối ngẫu của ràng buộc sức chứa chính là **bid price π_ℓ**; giải lại (re-solve) định kỳ. Lớp B (gán ghế) mô hình hóa mỗi booking là một khoảng [o_b, d_b) trên trục ga và giải bằng interval partitioning (greedy, tối ưu, độ phức tạp O(n·log n)); ghép đoạn trống bằng truy vấn interval best-fit; đổi chỗ bằng đường đi ít lần chuyển trên đồ thị chuyển tiếp. Hàm mục tiêu tổng đa mục tiêu (doanh thu, ghế-km, khách phục vụ, trừ ghế trống/đổi chỗ/vé từ chối), cài bằng OR-Tools CP-SAT hoặc HiGHS/Gurobi.

---

### 7.3. KHỐI 3 — Định giá động (Dynamic Pricing)

**User stories**
- *US3.1* — Là quản lý, tôi muốn giá phản ánh mức khan hiếm của từng chặng, để chặng nút cổ chai không bị bán rẻ và chặng trống được khuyến mãi.
- *US3.2* — Là quản lý, tôi muốn mọi mức giá luôn nằm trong trần/sàn được duyệt và biến động không quá ngưỡng, để bảo vệ hành khách.
- *US3.3* — Là quản lý, tôi muốn hiểu vì sao hệ thống đề xuất một mức giá, để giải trình.

**Yêu cầu chức năng**

| Mã | Yêu cầu | Tiêu chí chấp nhận |
|---|---|---|
| FR3.1 | Đề xuất giá theo `(OD, thời điểm)` dựa trên chi phí cơ hội theo chặng: c_j = Σ_ℓ a_ℓj · π_ℓ | Giá của OD qua chặng khan hiếm cao hơn; qua chặng trống thấp hơn |
| FR3.2 | Sử dụng các yếu tố: giá cơ sở, cự ly, tải chặng, nhu cầu dự báo, chỗ còn lại, số ngày tới ngày đi, tốc độ bán, loại/vị trí chỗ, thời điểm/ngày/mùa, độ linh hoạt vé, lịch sử hủy, giá đối thủ | Trọng số/yếu tố cấu hình được |
| FR3.3 | Phân hạng sản phẩm giá: tiết kiệm (mua sớm, điều kiện chặt), tiêu chuẩn, linh hoạt, thấp điểm, phút chót, nhóm/gia đình, khứ hồi, đa chặng, ghế liền, đổi chỗ có giảm giá | Danh mục hạng vé cấu hình được |
| FR3.4 | Định giá theo tải từng chặng: hành trình qua chặng gần đầy phải phản ánh khan hiếm; hành trình qua chặng trống được giá khuyến mãi | Kiểm chứng bằng ví dụ chặng đầy vs chặng trống |
| FR3.5 | Điều tiết cầu giữa các tàu: tàu quá cầu → tăng giá (trong giới hạn)/hạn chế khuyến mãi/gợi ý tàu-ngày-chỗ rẻ hơn; tàu ít cầu → giảm giá/kéo dài thời gian giữ/khuyến mãi chéo | Có đề xuất điều tiết cho cặp tàu ví dụ |
| FR3.6 | Ràng buộc kiểm soát biến động: giá trong khoảng trần/sàn (p_min ≤ p_j ≤ p_max); chênh lệch giá giữa hai bước liên tiếp không vượt ngưỡng Δ_max; giá đã xác nhận giữ chỗ không đổi; không cá nhân hóa theo dữ liệu nhạy cảm; không tăng theo số lần tìm kiếm lặp | Vi phạm bị hệ thống chặn; 0 vi phạm (K6) |
| FR3.7 | Giải thích được: mỗi đề xuất giá kèm lý do (chi phí cơ hội chặng, tải, thời điểm) | Quản lý xem được diễn giải cho từng mức giá |

**Hướng tiếp cận kỹ thuật:** Giá tối ưu là markup trên chi phí cơ hội c_j. Với cầu co giãn hằng số ε (ε > 1): giá tối ưu p_j* = [ε / (ε − 1)] · c_j (markup nhân). Với cầu dạng mũ λ(p) = λ₀ · e^(−α·p): giá tối ưu p_j* = c_j + 1/α (markup cộng). Trong đó c_j lấy trực tiếp từ bid price của Khối 2 — đây là mắt xích nối 3 khối. Độ co giãn học từ dữ liệu giá–lượng lịch sử theo phân khúc, hiệu chỉnh nội sinh bằng dữ liệu A/B ở Phase 3. Ràng buộc trần/sàn ép cứng sau bước tối ưu. RL là hướng mở rộng, ngoài MVP.

---

### 7.4. Chức năng nền tảng dùng chung (Cross-cutting)

| Mã | Yêu cầu | Tiêu chí chấp nhận |
|---|---|---|
| FR4.1 | Dashboard cho quản lý: heatmap tải chặng, ma trận ga đi–ga đến, biểu đồ tốc độ bán & dự báo, bảng đoạn trống có thể ghép | Hiển thị đúng cho tàu/ngày chọn |
| FR4.2 | Màn hình mô phỏng & phê duyệt: điều chỉnh hạn ngạch, mô phỏng giá, so sánh doanh thu/sản lượng AI vs chính sách hiện tại trước khi áp dụng | Chạy mô phỏng và xuất so sánh |
| FR4.3 | Cảnh báo chặng sắp cháy vé hoặc trống cao | Cảnh báo hiển thị theo ngưỡng cấu hình |
| FR4.4 | Nhật ký & báo cáo: log thay đổi chính sách, báo cáo hiệu năng | Truy vết được mọi thay đổi |
| FR4.5 | Vòng lặp khép kín: Dự báo → Tối ưu (bid price) → Định giá → Bán → cập nhật Dự báo | Thể hiện được luồng dữ liệu đầu-cuối |

---

## 8. Yêu cầu phi chức năng (Non-Functional Requirements)

| Mã | Yêu cầu |
|---|---|
| NFR1 | Giao diện người dùng bằng **tiếng Việt** |
| NFR2 | Vận hành **gần thời gian thực**; tốc độ tính lại đáp ứng K7 |
| NFR3 | Tích hợp mượt với hệ thống bán vé điện tử hiện có, **không gây gián đoạn/downtime**; cung cấp **API** |
| NFR4 | Hỗ trợ **rollback** (khôi phục về chính sách trước) |
| NFR5 | **Phân quyền theo vai trò (RBAC)** và **nhật ký kiểm toán đầy đủ** |
| NFR6 | **An toàn dữ liệu**; **không dùng dữ liệu cá nhân nhạy cảm** để định giá; dữ liệu tìm kiếm/nhu cầu ẩn danh |
| NFR7 | **Ngăn định giá tự động ngoài giới hạn** được duyệt |
| NFR8 | **AI giải thích được** và **giám sát trôi mô hình (model drift)** |
| NFR9 | Cho phép **can thiệp/ghi đè thủ công** của quản lý |
| NFR10 | **Khả năng mở rộng & ổn định** dưới khối lượng giao dịch cao |

---

## 9. Yêu cầu dữ liệu (Data Requirements)

### 9.1. Dữ liệu đầu vào
- **Dữ liệu vé:** mã vé, ngày bán/đi, mã tàu, ga, chi tiết chỗ, giá, kênh bán, thời điểm thanh toán/hoàn, cơ cấu phí, khuyến mãi.
- **Dữ liệu hành trình:** danh sách ga, giờ đến/đi, cự ly, tổng thời gian, thời gian dừng ga, chặng nhu cầu cao lịch sử.
- **Dữ liệu đoàn tàu:** số toa/loại, sơ đồ chỗ, cấu hình giường/ghế, trạng thái vận hành, chỗ ưu tiên, chỗ khóa, phương án thành phần đoàn tàu.
- **Dữ liệu nhu cầu:** lịch sử tìm kiếm, tìm kiếm không thỏa mãn, danh sách chờ, tỉ lệ chuyển đổi, tỉ lệ hủy, xu hướng theo thời gian/mùa (ẩn danh).
- **Dữ liệu ngoài:** lễ tết, lịch học, sự kiện địa phương, thời tiết, giao thông, lịch chạy đối thủ.

### 9.2. Dữ liệu đầu ra tối thiểu (theo đề bài)
Dự báo theo cặp ga–ngày–tàu–loại chỗ; heatmap tải & tỉ lệ sử dụng theo chặng; danh sách đoạn trống có thể ghép; kế hoạch tách đoạn & hạn ngạch đề xuất; kế hoạch tái phân bổ, ghế liền, ghép đổi chỗ; xếp chỗ nhóm (pha sau); mức giá động đề xuất; dự báo doanh thu/sản lượng & so sánh chính sách; cảnh báo cháy vé/trống cao; báo cáo hiệu năng & log thay đổi; API tích hợp hệ thống bán vé.

---

## 10. Luồng nghiệp vụ chính (Key Flows)

**Luồng lõi — Vòng lặp quản trị doanh thu (khép kín):**
1. Khối 1 ước lượng nhu cầu OD + phân phối + heatmap tải chặng.
2. Khối 2 (Lớp A) giải DLP → sinh **bid price** và hạn ngạch; (Lớp B) gán ghế & ghép đoạn trống.
3. Khối 3 chuyển bid price thành **giá** qua công thức markup + ràng buộc trần/sàn.
4. Khách mua/hủy → dữ liệu mới → quay lại bước 1, tính lại near real-time.

**Luồng phụ — Ra quyết định trên một yêu cầu vé:** nhận yêu cầu OD → so giá vé với tổng bid price các chặng → chấp nhận/từ chối (kèm lý do) → nếu chấp nhận, gán ghế giảm phân mảnh → cập nhật tồn kho.

**Luồng quản lý — Mô phỏng & phê duyệt:** quản lý mở dashboard → chạy mô phỏng chính sách → so sánh AI vs hiện tại → phê duyệt/ghi đè → ghi log.

---

## 11. Kế hoạch thử nghiệm (Testing Plan — 3 Pha)

| Pha | Tên | Nội dung | Tiêu chí ra pha |
|---|---|---|---|
| **Phase 1** | Phân tích dữ liệu lịch sử | AI mô phỏng chính sách trên dữ liệu quá khứ, so với kết quả thực tế đã diễn ra | Chính sách AI vượt thực tế trên K1–K4 |
| **Phase 2** | Shadow Mode | Hệ thống chạy song song vận hành hiện tại; quản lý đánh giá đề xuất, chưa áp dụng công khai | Đề xuất ổn định, được quản lý chấp nhận ở tỉ lệ mục tiêu |
| **Phase 3** | Thử nghiệm có kiểm soát | Áp dụng có chọn lọc (có thể A/B) dưới phê duyệt & giám sát chặt để đảm bảo công bằng | Đạt KPI mục tiêu; 0 vi phạm chính sách |

**Dữ liệu thử nghiệm:** tuyến nhiều ga trung gian, mã tàu nhu cầu cao, loại chỗ chọn lọc; 1–3 năm dữ liệu; cửa sổ 1–3 tháng.

---

## 12. Thách thức & Rủi ro (Challenges & Risks)

| Rủi ro | Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Dự báo cho hàng nghìn cặp OD, nhiều cặp thưa dữ liệu | Sai số cao | Dự báo phân cấp + hòa hợp; gộp phân khúc |
| Cân bằng khách chặng dài vs ngắn | Bán sai chỗ quý | Điều khiển bid price; đánh giá tác động chặng còn lại |
| Không gian tổ hợp ghép đoạn rất lớn | Chậm | Thuật toán interval hiệu quả; giới hạn phạm vi MVP |
| Điều chỉnh giá gây cảm giác bất công | Khiếu nại, uy tín | Trần/sàn, cap biến động, minh bạch, giải thích được |
| Tích hợp không được gây gián đoạn/lạm dụng chính sách | Rủi ro vận hành | Shadow mode, rollback, RBAC, audit, chống đầu cơ |
| Cập nhật tức thì khi hủy vé/đổi đoàn tàu | Lệch kế hoạch | Re-solve theo sự kiện; near real-time |
| Trôi mô hình theo thời gian | Giảm chính xác | Giám sát drift; tái huấn luyện định kỳ |
| Chất lượng/độ sẵn sàng dữ liệu đối tác | Chặn tiến độ | Chốt sớm phạm vi dữ liệu; phương án dữ liệu thay thế |

---

## 13. Sản phẩm bàn giao & Kết quả kỳ vọng (Deliverables & Outcomes)

**Deliverables (MVP):** hệ thống dự báo nhu cầu; công cụ tối ưu hạn ngạch; công cụ tách/ghép đoạn tự động; hệ thống định giá linh hoạt + dashboard doanh thu/hệ số sử dụng; công cụ mô phỏng chính sách giá; API tích hợp; trợ lý vận hành vé cho quản lý. *(Danh sách chờ thông minh — pha sau.)*

**Kết quả kỳ vọng:** chuyển phân bổ chỗ & định giá từ quy tắc cố định sang vận hành động dựa trên dữ liệu; khai thác năng lực hiệu quả hơn; tăng hệ số sử dụng chặng; tăng sản lượng & doanh thu; giảm ghế trống cục bộ; tăng khả năng phục vụ ga trung gian; điều tiết cầu mượt giữa các tàu; tăng khách giờ thấp điểm; đặt nền móng cho hệ thống quản trị doanh thu đường sắt thông minh.

---

## 14. Câu hỏi mở (Open Questions)

1. Chốt danh sách mã tàu/tuyến/loại chỗ cụ thể cho MVP với đối tác đường sắt?
2. Khung trần/sàn giá và mức biến động tối đa mỗi bước (Δ_max) được duyệt là bao nhiêu?
3. Phạm vi và độ sẵn sàng của dữ liệu tìm kiếm/nhu cầu (đặc biệt tìm kiếm không thỏa mãn)?
4. Ràng buộc chính sách xã hội cụ thể (đối tượng ưu tiên, giá trần theo tuyến)?
5. Hệ thống bán vé hiện tại cung cấp API/giao diện tích hợp nào?
6. Tiêu chí ra Phase 3 (ngưỡng chấp nhận đề xuất ở shadow mode)?

---

## Phụ lục A — Thuật ngữ (Glossary)

- **Chặng (leg):** đoạn đường giữa hai ga liên tiếp.
- **Luồng OD (Origin–Destination):** cặp ga đi–ga đến (kèm loại chỗ) mà khách di chuyển.
- **Tách đoạn (segmenting):** chia hành trình tàu thành các chặng nhỏ để mở bán riêng.
- **Ghép đoạn (combining):** gộp các đoạn trống hoặc nhu cầu liên tiếp để tạo phương án vé, tăng số lần dùng ghế.
- **Bid price (π_ℓ):** chi phí cơ hội của một ghế trên chặng ℓ; dùng làm ngưỡng chấp nhận vé và cơ sở định giá.
- **DLP (Deterministic Linear Program):** quy hoạch tuyến tính tối ưu phân bổ chỗ, sinh bid price qua đối ngẫu.
- **Giải kiểm duyệt (unconstraining):** ước lượng nhu cầu thật từ dữ liệu bị cắt do hết chỗ/chặn bán.
- **Đường cong đặt vé (booking curve/pickup):** mẫu tích lũy vé theo thời gian tới ngày đi.
- **Passenger-km / ghế-km:** đơn vị đo sản lượng theo quãng đường; chỉ số hiệu quả sử dụng năng lực.
- **Shadow mode:** chạy song song không áp dụng công khai để đánh giá.
