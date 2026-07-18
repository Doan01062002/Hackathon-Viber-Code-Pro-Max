# SRRM `ai-service` — phần AI (Khối 1/2/3)

Bản hiện thực chạy được của **phần AI** cho hệ thống Smart Rail Revenue Management (đường sắt Bắc–Nam, 20 ga). Bao gồm bộ sinh dữ liệu mô phỏng và ba khối AI.

> **Đây là thư viện Python, không phải service.** Trước đây `ai_service` chạy riêng thành một FastAPI microservice (`app.py`, cổng 8100/8001) và backend gọi sang qua HTTP. Giờ backend `pip install -e ./ai` rồi **import thẳng** `ai_service.engine.AIEngine` — không còn HTTP, không còn retry/timeout mạng, không còn container `ai-service` trong docker-compose. Điểm vào duy nhất cho backend là `engine.py`; xem `backend/services/ai_client.py`.

## Cấu trúc

```
ai/
  src/ai_service/
    config.py         # 20 ga, cự ly, sức chứa, giá, hệ số (neo theo số liệu thật)
    datagen.py        # bộ sinh dữ liệu (+ thời tiết, khuyến mãi, chiều đi/về Tết)
    unconstraining.py # KHỐI 1 — EM giải kiểm duyệt cầu (censored Poisson)
    booking_curve.py  # KHỐI 1 — đường cong đặt vé + pickup theo lead time
    forecasting.py    # KHỐI 1 — LightGBM Poisson + quantile + tuning + SHAP + pinball
    optimization.py   # KHỐI 2 — DLP bid price (HiGHS) + gán ghế + ghép đoạn
    pricing.py        # KHỐI 3 — markup trên bid price + co giãn + diễn giải
    adapter.py        # ETL 21 bảng CSV -> history (+ đặc trưng mới)
    schemas.py        # hợp đồng dữ liệu (pydantic) giữa backend và AI
    engine.py         # AIEngine — điểm vào backend import: forecast/optimize/price
  scripts/
    eda.py            # khám phá dữ liệu + kiểm định feature set
    gen_data.py       # xuất 21 bảng seeds (CSV+JSON)
    train.py          # train 1 lần -> models/model.pkl (EM + tuning + booking curve)
    eval.py           # KHỐI 1: WAPE/OD, phủ phân vị, pinball, pickup MAPE
    eval_optimization.py  # KHỐI 2: uplift nền vs bid price
    eval_pricing.py   # KHỐI 3: quét trần surge + uplift định giá (mô phỏng WTP)
    run_pipeline.py   # demo end-to-end
  tests/
    test_unconstraining.py  # EM khôi phục λ trên tập giả lập
    test_booking_curve.py   # pickup MAPE + đơn điệu đường cong
  requirements.txt
```

## Chạy

```bash
pip install -r requirements.txt   # gồm lightgbm, shap (tự fallback nếu thiếu)

# 0) Khám phá dữ liệu + kiểm định feature set
python scripts/eda.py --from-seeds out/seeds

# 1) (Xem thử) sinh 21 bảng seeds (+ thời tiết, khuyến mãi)
python scripts/gen_data.py --days 300 --start 2024-01-01

# 3) HUẤN LUYỆN MỘT LẦN -> lưu model ra models/model.pkl  (MVP: chạy tay, chưa cần định kỳ)
python scripts/train.py                                 # tự sinh data bằng datagen
python scripts/train.py --from-seeds out/seeds --tune   # train trên 21 bảng + tuning LightGBM

# 4) Đánh giá
python scripts/eval.py --from-seeds out/seeds               # KHỐI 1: WAPE theo OD/ngày, phủ phân vị
python scripts/eval_optimization.py --from-seeds out/seeds  # KHỐI 2: uplift nền vs AI (doanh thu, ghế-km)
python scripts/eval_pricing.py                              # KHỐI 3: quét trần surge + uplift định giá (mô phỏng)

# 5) Unit test (EM unconstraining + booking curve)
python tests/test_unconstraining.py && python tests/test_booking_curve.py

# 6) Phục vụ — không chạy service riêng nữa, backend nạp model đã train khi khởi động
pip install -e ./ai -e ./backend
uvicorn backend.main:app --port 8000
#   POST /ai/forecast  {"service_date":"2024-02-11"}
#   POST /ai/optimize  {"service_date":"2024-02-11"}
```

Gọi trực tiếp trong Python (không qua backend):

```python
from ai_service.engine import get_engine
from ai_service.schemas import ForecastRequest

get_engine().forecast(ForecastRequest(service_date="2024-02-11"))
```

`get_engine()` là singleton: `models/model.pkl` chỉ nạp **một lần cho mỗi process**. Các method của `AIEngine` là **đồng bộ và nặng CPU** — backend bọc chúng bằng `asyncio.to_thread` để không chặn event loop; code async nào gọi thẳng engine cũng phải làm vậy.

> **Quy trình MVP:** train **một lần** bằng `scripts/train.py` (lưu `models/model.pkl`) → backend chỉ nạp model để phục vụ. Khi dữ liệu thay đổi thì **chạy lại `train.py`** (thủ công). Chưa đưa train định kỳ/drift vào MVP — bước train đã tách riêng nên sau này chỉ cần bọc bằng scheduler là xong.

## Ba khối AI

**KHỐI 1 — Dự báo (`forecasting.py` + `unconstraining.py` + `booking_curve.py`)**
LightGBM hồi quy **Poisson** cho λ̂ (tự fallback HistGradientBoosting) + 3 mô hình **quantile** cho p10/p50/p90 (ép đơn điệu). Có **random-search tuning** theo time-split, **feature importance bằng SHAP**, và **pinball loss** khi đánh giá.
- *Giải kiểm duyệt (`unconstraining.py`):* **EM cho censored Poisson** — ngày hết chỗ là quan sát bị cắt (cầu thật ≥ số bán); E-step thay bằng `E[D|D≥k,λ]`, M-step cập nhật λ theo nhóm (OD × mùa). Nhãn train = cầu **đã de-censor**, không phải số bán thô.
- *Booking curve (`booking_curve.py`):* fit đường cong đặt vé tích lũy theo **lead time**, mô hình **pickup** dự phóng cầu cuối (`final = b / c(τ)`). Pickup MAPE @14 ngày ~**5%**.
- *Đặc trưng:* lịch (thứ/tháng/mùa), lễ/Tết, **chiều đi/về Tết** (`days_to_tet`, `is_pre_tet`, `is_post_tet`), **thời tiết** (`is_rainy`), **khuyến mãi** (`promo`), cự ly, giá, độ hút ga, hub, nút cổ chai.
- Kết quả backtest tiêu biểu: **WAPE tổng hợp theo OD ~5–7%**, **phủ p10–p90 ~80%**, **corr(λ̂, λ_thật) ~0.98**.

**KHỐI 2 — Tối ưu (`optimization.py`)**
- *Lớp A:* DLP `max Σ f_j x_j` với ràng buộc sức chứa từng (chặng, loại chỗ); giải bằng **scipy HiGHS**; **bid price = biến đối ngẫu**; quy tắc chấp nhận `fare ≥ Σ bid price`. Giải **~5 ms/chuyến**.
- *Lớp B:* gán ghế bằng **interval partitioning** (greedy, tối ưu — số ghế dùng = tải chồng lấn cực đại) và **ghép đoạn trống best-fit**.

**KHỐI 3 — Định giá (`pricing.py`)**
Giá = markup trên chi phí cơ hội `c_j = Σ bid price`; độ co giãn ước lượng từ dữ liệu (khử nhiễu theo OD), có **guardrail** chặn markup nổ và **trần surge** (đại diện Policy Guard). AI chỉ trả **giá thô + diễn giải**; ép trần/sàn cuối là việc của backend.

> **Đánh giá Khối 3 phải trên MÔ PHỎNG (không dùng seed):** định giá làm *thay đổi cầu* nên cần mô hình mức-sẵn-lòng-trả (WTP) để biết đổi giá thì ai còn mua — seed chỉ ghi vé đã bán, không mang WTP. `eval_pricing.py` sinh khách có WTP (nhích theo cao điểm — Tết khách trả cao & phân tán rộng), rồi cho CÙNG tập khách đối mặt 3 chính sách (nền / +Khối 2 / +Khối 3) và **quét trần surge** để lộ đường cong doanh thu hình chuông. Kết quả tiêu biểu: **ngày thường 0%** (không khan hiếm → không surge), **cao điểm doanh thu +~27%** tại trần tối ưu ~1.6× (giá TB/vé +54%, đổi bớt sản lượng lấy doanh thu); vượt ~2× thì doanh thu *tụt* → cho thấy vì sao cần **trần surge hiệu chỉnh** + Policy Guard 2.5× làm rào cứng. **Cầu nạp vào bộ tối ưu = cầu-trả-tiền tại giá gốc (bookings+soldout — đúng đầu ra Khối 1), KHÔNG phải λ đến thô**, nên ngày vắng bid price = 0 và hệ thống không tăng giá bừa.

## Kết quả demo (chuyến cao điểm Tết 2024-02-11)

```
KHỐI 1: WAPE theo OD ~5.5% | corr(λ̂, λ_thật) 0.98
KHỐI 2: DLP giải ~5 ms | bid price nút cổ chai Huế–ĐN: ngồi mềm ~89k, giường ~98k
        24–30/198 OD bị từ chối (giá < chi phí cơ hội)
        gán ghế 192/192 & 252/252 — tối ưu; tìm ~400 khoảng trống ghép được
KHỐI 3: HN→ĐN (giường, qua nút cổ chai) surge 1.55M; HN→Phủ Lý (chặng thường) giữ giá gốc 62k
```

## Ghi chú thiết kế / triển khai thật

- **ai_service stateless về nghiệp vụ.** Thư viện AI **không đọc DB** — backend đọc DB rồi đẩy snapshot vào request (rõ nhất ở `AIClient.price`: bid price lấy từ bảng `bid_prices` rồi truyền xuống). Ranh giới này giữ nguyên sau khi bỏ HTTP; nếu sau này cần tách lại thành service riêng thì chỉ việc bọc `AIEngine` bằng một lớp HTTP.
- **Ground-truth** (λ thật) do `datagen` sinh ra — để ngoài DB vận hành, dùng chấm điểm Phase 1.
- **Có thể thay** `HistGradientBoostingRegressor` bằng **LightGBM** (production); thay `scipy HiGHS` bằng **OR-Tools/Gurobi** nếu cần. Interface không đổi.
- Ánh xạ đầu ra với 21 bảng schema: `demand_forecasts` (Khối 1), `bid_prices`/`quotas` (Khối 2A), `seat`/`gap_combinations` (Khối 2B), `price_quotes` (Khối 3).
- Tham số sinh dữ liệu & mạng 20 ga: xem `Luat_Sinh_Du_Lieu_SRRM.md`.
