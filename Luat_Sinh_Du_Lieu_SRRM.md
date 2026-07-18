# Luật sinh dữ liệu mô phỏng — SRRM MVP

**Mục đích:** tạo dữ liệu mô phỏng cho hệ thống Smart Rail Revenue Management, khớp mặt bằng đường sắt Bắc–Nam thật, đủ tín hiệu để mô hình AI học được, và có **ground-truth** để đánh giá Phase 1.
**Phạm vi:** dùng cho bộ sinh dữ liệu (`seed`/generator), xuất ra JSON/CSV khớp 21 bảng của schema + file ground-truth (để ngoài DB vận hành).
**Ngày:** 17/07/2026

> Các số cự ly/giá/cấu hình toa được neo theo dữ liệu đường sắt VN hiện hành (xem Nguồn cuối file); coi là mặt bằng tham chiếu, không phải bảng giá chính thức.

---

## 0. Nguyên tắc

1. **Mô phỏng có tham số, không random.** Định nghĩa nhu cầu ngầm → mô phỏng khách đến → quyết định mua theo giá & chỗ còn → ép sức chứa. Từ đó sinh ra vé, log tìm kiếm, kiểm duyệt.
2. **Hai tầng dữ liệu:**
   - **Quan sát được** (cho mô hình học): `bookings`, `search_logs`, giá đã hiển thị.
   - **Sự thật ngầm** (để chấm điểm): λ thật, mức sẵn lòng trả, số lượt đến thật → lưu ra **file ground-truth**, KHÔNG vào DB vận hành.
3. **"Hơi thiên hướng cho mô hình học":** các yếu tố xác định giải thích ~75–85% biến thiên, nhiễu ~15–25% — mạnh nhưng không sạch tuyệt đối.
4. **Cố định random seed** để tái lập.

---

## 1. Cấu hình mạng — CỐ ĐỊNH 20 GA

Hệ thống dùng **20 ga** → **19 chặng** → **190 cặp OD một chiều** (×2 loại chỗ = tối đa 380 sản phẩm/chuyến). Vì số OD lớn nên **BẮT BUỘC** giới hạn OD mở bán quanh ga hub và dự báo phân cấp để tránh thưa dữ liệu (mục 5.3 và 9) — đây không còn là tùy chọn.

**Danh sách 20 ga (Bắc→Nam), lý trình km từ Hà Nội** (● = ga hub, dùng cho giới hạn OD):

| # | Ga | km | Hub | Nguồn km |
|---|---|---|---|---|
| 1 | Hà Nội | 0 | ● | ✓ xác nhận |
| 2 | Phủ Lý | ~56 | | xấp xỉ |
| 3 | Nam Định | ~87 | | xấp xỉ |
| 4 | Ninh Bình | ~115 | | xấp xỉ |
| 5 | Thanh Hóa | ~175 | | xấp xỉ |
| 6 | Vinh | 319 | ● | ✓ xác nhận |
| 7 | Đồng Hới | 522 | | ✓ xác nhận |
| 8 | Đông Hà | ~622 | | xấp xỉ |
| 9 | Huế | 688 | ● | ✓ xác nhận |
| 10 | Đà Nẵng | 791 | ● | ✓ xác nhận |
| 11 | Tam Kỳ | ~865 | | xấp xỉ |
| 12 | Quảng Ngãi | ~928 | | xấp xỉ |
| 13 | Diêu Trì (Quy Nhơn) | ~1096 | | xấp xỉ |
| 14 | Tuy Hòa | ~1198 | | xấp xỉ |
| 15 | Nha Trang | 1315 | ● | ✓ xác nhận |
| 16 | Tháp Chàm | ~1408 | | xấp xỉ |
| 17 | Bình Thuận (Mương Mán) | ~1551 | | xấp xỉ |
| 18 | Long Khánh | ~1637 | | xấp xỉ |
| 19 | Biên Hòa | ~1694 | | xấp xỉ |
| 20 | Sài Gòn | 1726 | ● | ✓ xác nhận |

**6 ga hub:** Hà Nội, Vinh, Huế, Đà Nẵng, Nha Trang, Sài Gòn.

> Các km "xấp xỉ" nên tra lại từ danh sách ga Thống Nhất trước khi chốt. **Cự ly chặng** = hiệu km hai ga liên tiếp (19 chặng).

**Ví dụ cự ly vài chặng:** HN–Phủ Lý 56 · Thanh Hóa–Vinh 144 · Vinh–Đồng Hới 203 · **Huế–Đà Nẵng 103 (nút cổ chai)** · Đà Nẵng–Tam Kỳ 74 · Quảng Ngãi–Diêu Trì 168 · Nha Trang–Tháp Chàm 93 · Biên Hòa–SG 32.

---

## 2. Tàu, loại chỗ, sức chứa (cấu hình toa thật)

- **Tàu:** 1 mác SE, chạy **hằng ngày**, lịch sử **2–3 năm** (đủ lặp mùa/Tết).
- **Thời gian chạy** (theo SE1 thật): rời HN ~22:20, tới SG ~05:45 (+2 ngày), tổng **~31–32 giờ**. Mốc: Vinh +5h35, Huế +12h40, Đà Nẵng +15h25, Nha Trang +24h, SG +31h25 (Đồng Hới nội suy ~+10h). Dừng ga ~5–15 phút.
- **Loại chỗ & sức chứa mỗi chặng** (số ghế/giường mỗi toa là số thật):

| Loại chỗ (`seat_type`) | Cấu hình | Capacity/chặng |
|---|---|---|
| `ngoi_mem` (ngồi mềm điều hòa) | 3 toa × 64 ghế | **192** |
| `giuong_nam_k6` (giường nằm khoang 6) | 6 toa × 42 giường | **252** |
| **Tổng** | | **444 chỗ** (sát đoàn SE thật ~400–500) |

Sức chứa hằng số qua các chặng (thành phần đoàn tàu cố định). Ghi vào `segment_capacities`; khởi tạo `segment_inventory.remaining = capacity`.

---

## 3. Giá cơ sở (neo theo giá vé SE1 thật)

Đơn giá/km hiệu chỉnh để HN–SG khớp giá thật (ngồi mềm ~1.150.000đ, giường k6 ~1.205.000–1.535.000đ):

| Loại chỗ | Đơn giá/km | HN–SG (1726 km) |
|---|---|---|
| `ngoi_mem` | **670 đ/km** | 1.156.000đ ✓ |
| `giuong_nam_k6` | **760 đ/km** | 1.312.000đ ✓ |

**Công thức `base_price` cho một OD:**
```
base_price = phi_co_dinh + don_gia_km × distance_km        # phi_co_dinh ≈ 20.000đ
```
Tùy chọn sát hơn — **bậc theo tầng giường** (nhân với base): T1 = 1.15, T2 = 1.05, T3 = 0.90.

**Ví dụ base_price** (ngồi mềm / giường k6):

| OD | km | ngồi mềm | giường k6 |
|---|---|---|---|
| HN–Vinh | 319 | ~234.000 | ~262.000 |
| HN–Huế | 688 | ~481.000 | ~543.000 |
| HN–Đà Nẵng | 791 | ~550.000 | ~621.000 |
| Đà Nẵng–Nha Trang | 524 | ~371.000 | ~418.000 |
| HN–Sài Gòn | 1726 | ~1.176.000 | ~1.332.000 |

---

## 4. Nhu cầu ngầm λ theo OD × ngày (công thức lõi)

```
λ_od(d) = K × base_od × f_dow(d) × f_season(d) × f_holiday(d)
```
Rồi lấy **nhu cầu thật**:  `D_od(d) ~ NegativeBinomial(mean = λ, r = 12)`  (r=12 → nhiễu nhẹ, học được; r nhỏ hơn = nhiễu hơn).

**K**: hằng số quy mô, chỉnh sao cho tải trung bình mỗi chặng ≈ **0,65 × capacity** ngày thường (mục 6).

### 4.1. `base_od` — tạo lệch cầu + nút cổ chai
```
base_od = pop_o × pop_d × exp(−distance_od / 800) × pair_boost × seat_share
```

**pop (độ hút) cho cả 20 ga:**

| Ga | pop | Ga | pop |
|---|---|---|---|
| Hà Nội | 1.00 | Quảng Ngãi | 0.35 |
| Phủ Lý | 0.25 | Diêu Trì (Quy Nhơn) | 0.45 |
| Nam Định | 0.40 | Tuy Hòa | 0.30 |
| Ninh Bình | 0.30 | Nha Trang | 0.70 |
| Thanh Hóa | 0.50 | Tháp Chàm | 0.25 |
| Vinh | 0.50 | Bình Thuận | 0.30 |
| Đồng Hới | 0.30 | Long Khánh | 0.20 |
| Đông Hà | 0.25 | Biên Hòa | 0.40 |
| Huế | 0.60 | Sài Gòn | 1.00 |
| Đà Nẵng | 0.90 | | |

- `pair_boost`: HN–Vinh = 1.6 (chặng ngắn đông); **mọi OD đi qua chặng Huế–Đà Nẵng ×1.5** → biến Huế–ĐN thành **nút cổ chai** (tải ≈ capacity khi cao điểm, chặng bên cạnh còn dư).
- `seat_share`: chặng ngắn nghiêng `ngoi_mem` (0.70/0.30), chặng dài nghiêng `giuong_nam_k6` (0.35/0.65).

### 4.2. Hệ số thời gian (tín hiệu mạnh, dễ học)

**f_dow** — ngày trong tuần:

| T2 | T3 | T4 | T5 | T6 | T7 | CN |
|---|---|---|---|---|---|---|
| 0.85 | 0.80 | 0.85 | 1.10 | 1.45 | 1.20 | 1.50 |

**f_season** — theo tháng: hè (6–8) = **1.35** cho OD tới Đà Nẵng/Nha Trang (du lịch), 1.0 phần còn lại; thấp điểm (2–4 sau Tết) = 0.85.

**f_holiday**: ngày thường 1.0; lễ (30/4, 2/9…) **1.8**; **cửa sổ Tết (±10 ngày) 3.0**, kèm **bất đối xứng chiều**: trước Tết HN→SG ×1.4, sau Tết SG→HN ×1.4.

---

## 5. Từ nhu cầu tới giao dịch

### 5.1. Đường cong đặt vé (lead time)
Trải D_od(d) qua **T = 60 ngày** trước ngày chạy:
```
tỉ lệ khách đến ngày t (còn t ngày)  ∝  exp(−t / 15)      # đông dần về sát ngày đi
```
Riêng **Tết**: thêm "bướu mua sớm" ~40–50 ngày trước (một mũi Gaussian tại t≈45). → tín hiệu để booking-curve/pickup học.

### 5.2. Sẵn lòng trả & co giãn giá
Mỗi khách đến có ngưỡng giá:
```
w ~ LogNormal(median = 1.15 × base_price_od, σ_log = 0.25)      # σ=0.25 → co giãn rõ, học được
```
**Mua nếu `giá_hiển_thị ≤ w` và còn chỗ trên MỌI chặng OD đi qua.**

**Giá hiển thị phải BIẾN THIÊN** (nếu cố định → không ước lượng được co giãn):
```
giá_hiển_thị = base_price × (1 + 0.15·[lead<7 ngày] + 0.10·[T6 hoặc CN]) × (1 + U(−0.15, +0.20))
```

### 5.3. Giới hạn OD mở bán (BẮT BUỘC với 20 ga)
KHÔNG mở bán toàn bộ 190 cặp. Chỉ tạo `od_products` cho:
- Mọi OD có **ít nhất một đầu là ga hub** (HN, Vinh, Huế, Đà Nẵng, Nha Trang, SG), **và/hoặc**
- OD có `base_od` vượt ngưỡng tối thiểu (ví dụ ≥ 0,5 khách/ngày).

→ giữ realism 20 ga nhưng số OD hoạt động còn **~60–90** thay vì 190. Các cặp ga nhỏ–ga nhỏ (ví dụ Phủ Lý–Long Khánh) không mở bán. Dự báo **phải phân cấp** (dự báo mức chặng/tàu rồi phân rã xuống OD), không per-OD naive — nếu không sẽ dính bẫy thưa dữ liệu.

### 5.4. Ép sức chứa → kiểm duyệt & log tìm kiếm
- Khách muốn mua nhưng **một chặng bất kỳ trên OD đã đầy** → ghi `search_logs.result = 'sold_out'` (censored demand; KHÔNG thành booking).
- Khách có `w < giá` → ghi `result = 'found'` nhưng không mua (tín hiệu cầu theo giá).
- Mua được → tạo `bookings` (status `confirmed`/`held`), gán ghế, trừ `segment_inventory.remaining` trên **mọi chặng OD đi qua** (dùng `od_product_segments`).
- Thêm ~1.5–2× lượt **browsing** `result='found'` không mua để có dữ liệu **tỉ lệ chuyển đổi** (KPI).
- Sinh một tỉ lệ **hủy vé** thực tế (~5–10%) đặt `status='cancelled'`, `cancelled_at`.

---

## 6. Hiệu chỉnh quy mô theo tải thực tế

Tàu SE ngày thường lấp đầy **~60–75%**, cao điểm gần 100%. Chỉnh **K** sao cho:
- **Ngày thường:** tổng λ qua mỗi chặng ≈ **0,65 × capacity**.
- **Nút cổ chai Huế–Đà Nẵng:** ≈ **0,80 ngày thường**; với f_holiday=3.0 (Tết) **vượt 1,0 → sinh kiểm duyệt** (đúng mục tiêu tạo censoring).
- **Cuối tuần & hè (OD tới ĐN/NT):** đẩy tải lên ~0,85–0,95.

---

## 7. Nút vặn "thiên hướng cho mô hình học"

| Nút | Học DỄ (thiên hướng) | Thực tế/khó |
|---|---|---|
| Nhiễu cầu (r của NegBinom) | **r = 12–15** | r = 3–5 |
| σ của WTP | **0.20–0.25** | 0.40+ |
| Độ lớn hệ số mùa/lễ | giữ như mục 4.2 | san phẳng |
| Độ dài lịch sử | **2–3 năm** | 1 năm |
| Biến thiên giá | **±15–20%** | ±5% |

**Mục tiêu số:** đặt tham số sao cho mô hình dự báo đạt **MAPE ~10–15%** trên tập test — đủ tốt để "khoe" mà vẫn thực tế.

---

## 8. Ground-truth để đánh giá Phase 1 (lưu ra file, ngoài DB)

Với mỗi (od_product, ngày) lưu: **λ thật**, **nhu cầu chưa kiểm duyệt** (tổng lượt muốn mua kể cả bị từ chối), tham số WTP. Giữ luôn **simulator** để có thể **replay cùng nhu cầu dưới hai chính sách** (nền vs AI) → tính uplift KPI (doanh thu, ghế-km). Định dạng: CSV/Parquet trong thư mục `eval/` hoặc schema `eval` riêng.

---

## 9. Cạm bẫy — đừng làm QUÁ sạch

- **Đừng bỏ nhiễu** (dùng thẳng λ làm D): mô hình đạt gần 100% → nhìn giả. Luôn NegBinom/Poisson.
- **Đừng để giá cố định** → mất co giãn.
- **Đừng để cầu đồng đều** → mất nút cổ chai (nhớ pair_boost Huế–ĐN).
- **Đừng forecasting naive per-OD trên 20 ga** → thưa dữ liệu; dùng phân cấp + giới hạn OD hub.
- **Giữ quan hệ ổn định** giữa train/test nhưng thêm **trend nhẹ +3–5%/năm** để không tầm thường.

---

## 10. Ánh xạ đầu ra với schema (21 bảng)

| Sinh ra | Ghi vào bảng |
|---|---|
| Danh mục ga, tàu, loại chỗ, hạng giá | `stations`, `trains`, `seat_types`, `fare_classes` |
| Đặc trưng lịch (lễ/Tết/mùa/thời tiết) | `calendar_features` |
| Chuyến, chặng, ghế | `trips`, `segments`, `seats` |
| Sức chứa & tồn kho theo chặng | `segment_capacities`, `segment_inventory` |
| Sản phẩm OD + ánh xạ chặng | `od_products`, `od_product_segments` |
| Vé đã bán/giữ/hủy | `bookings` |
| Log tìm kiếm (gồm sold_out) | `search_logs` |
| λ thật, nhu cầu chưa kiểm duyệt | **file ground-truth (ngoài DB)** |

Định dạng đầu vào cho AI: **JSON** cho payload API; **CSV/Parquet** (hoặc JSON Lines) cho dữ liệu huấn luyện lớn. Tiền tệ để **số nguyên đồng**; thời gian **ISO 8601**.

---

## 11. Quy trình sinh một chuyến (tóm tắt thuật toán)

1. Tạo `trip` (tàu, ngày) + `segments` (cự ly, giờ) + `seats` (theo cấu hình toa) + `segment_capacities`/`segment_inventory`.
2. Tạo `od_products` (giới hạn theo mục 5.3) + `od_product_segments`.
3. Tính λ_od(d) = K × base_od × f_dow × f_season × f_holiday; lấy D ~ NegBinom(λ, 12).
4. Trải D theo booking curve exp(−t/15) (+bướu Tết) → chuỗi lượt khách đến theo thời gian.
5. Mỗi lượt: sinh WTP; tính giá hiển thị (có biến thiên); nếu `giá ≤ w` và còn chỗ → `booking` + trừ tồn kho theo chặng; nếu hết chỗ → `search_logs(sold_out)`; nếu `w<giá` → `search_logs(found, không mua)`.
6. Thêm browsing searches + tỉ lệ hủy.
7. Ghi λ thật & nhu cầu chưa kiểm duyệt ra file ground-truth.

---

## Nguồn tham chiếu số liệu thực tế

- Cự ly các ga: North–South railway (Vietnam), Wikipedia — https://en.wikipedia.org/wiki/North%E2%80%93South_railway_(Vietnam)
- Giờ chạy & giá vé SE1 (HN–SG theo loại chỗ): vetau.alltours.vn — https://vetau.alltours.vn/ve-tau/tau-se1.html
- Số ghế/giường mỗi toa (ngồi mềm 64, khoang 6, khoang 4): Vexere — https://blog.vexere.com/cac-loai-ghe-tren-tau-hoa-viet-nam/
