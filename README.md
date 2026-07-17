# SRRM `ai-service` — phần AI (Khối 1/2/3)

Bản hiện thực chạy được của **phần AI** cho hệ thống Smart Rail Revenue Management (đường sắt Bắc–Nam, 20 ga). Bao gồm bộ sinh dữ liệu mô phỏng, ba khối AI, và FastAPI theo hợp đồng `/internal/*`.

## Cấu trúc

```
ai-service/
  ai_service/
    config.py         # 20 ga, cự ly, sức chứa, giá, hệ số (neo theo số liệu thật)
    datagen.py        # bộ sinh dữ liệu theo Luat_Sinh_Du_Lieu_SRRM.md
    forecasting.py    # KHỐI 1 — dự báo GBDT Poisson + quantile + unconstraining
    optimization.py   # KHỐI 2 — DLP bid price (HiGHS) + gán ghế + ghép đoạn
    pricing.py        # KHỐI 3 — markup trên bid price + co giãn + diễn giải
    schemas.py        # hợp đồng JSON (pydantic)
    app.py            # FastAPI /internal/forecast|optimize|price
  scripts/
    run_pipeline.py   # demo end-to-end + backtest (chạy cái này trước)
  requirements.txt
```

## Chạy

```bash
pip install -r requirements.txt

# 1) Demo end-to-end nhanh (sinh data -> dự báo -> bid price -> gán ghế -> định giá)
python scripts/run_pipeline.py

# 2) (Xem thử) sinh data + thống kê độ 'peaky' (Tết, sold_out)
python scripts/gen_data.py

# 3) HUẤN LUYỆN MỘT LẦN -> lưu model ra models/model.pkl  (MVP: chạy tay, chưa cần định kỳ)
python scripts/train.py                         # tự sinh data bằng datagen
python scripts/train.py --from-seeds out/seeds  # HOẶC train thẳng trên 21 bảng đã gen (adapter)

# 4) Chạy API — app NẠP model đã train, KHÔNG train lúc khởi động
uvicorn ai_service.app:app --port 8100
#   POST /internal/forecast  {"service_date":"2024-02-11"}
#   POST /internal/optimize  {"service_date":"2024-02-11"}
#   POST /internal/price     {"od_id": 12, "service_date":"2024-02-11"}
```

> **Quy trình MVP:** train **một lần** bằng `scripts/train.py` (lưu `models/model.pkl`) → app chỉ nạp model để phục vụ. Khi dữ liệu thay đổi thì **chạy lại `train.py`** (thủ công). Chưa đưa train định kỳ/drift vào MVP — bước train đã tách riêng nên sau này chỉ cần bọc bằng scheduler là xong.

## Ba khối AI

**KHỐI 1 — Dự báo (`forecasting.py`)**
GBDT hồi quy Poisson cho λ̂ + 3 mô hình quantile cho p10/p50/p90. Giải kiểm duyệt đơn giản: target = `bookings + soldout` (dùng search log để khôi phục nhu cầu bị cắt). Kết quả backtest tiêu biểu: **WAPE tổng hợp theo OD ~5–6%**, **corr(λ̂, λ_thật) ~0.98**.

**KHỐI 2 — Tối ưu (`optimization.py`)**
- *Lớp A:* DLP `max Σ f_j x_j` với ràng buộc sức chứa từng (chặng, loại chỗ); giải bằng **scipy HiGHS**; **bid price = biến đối ngẫu**; quy tắc chấp nhận `fare ≥ Σ bid price`. Giải **~5 ms/chuyến**.
- *Lớp B:* gán ghế bằng **interval partitioning** (greedy, tối ưu — số ghế dùng = tải chồng lấn cực đại) và **ghép đoạn trống best-fit**.

**KHỐI 3 — Định giá (`pricing.py`)**
Giá = markup trên chi phí cơ hội `c_j = Σ bid price`; độ co giãn ước lượng từ dữ liệu (khử nhiễu theo OD), có **guardrail** chặn markup nổ và **trần surge 2.5×** (đại diện Policy Guard). AI chỉ trả **giá thô + diễn giải**; ép trần/sàn cuối là việc của backend.

## Kết quả demo (chuyến cao điểm Tết 2024-02-11)

```
KHỐI 1: WAPE theo OD ~5.5% | corr(λ̂, λ_thật) 0.98
KHỐI 2: DLP giải ~5 ms | bid price nút cổ chai Huế–ĐN: ngồi mềm ~89k, giường ~98k
        24–30/198 OD bị từ chối (giá < chi phí cơ hội)
        gán ghế 192/192 & 252/252 — tối ưu; tìm ~400 khoảng trống ghép được
KHỐI 3: HN→ĐN (giường, qua nút cổ chai) surge 1.55M; HN→Phủ Lý (chặng thường) giữ giá gốc 62k
```

## Ghi chú thiết kế / triển khai thật

- **ai-service stateless về nghiệp vụ.** Bản demo tự sinh data + train khi khởi động để chạy được ngay. Triển khai thật: **backend đẩy snapshot dữ liệu vào payload**, ai-service không đọc DB.
- **Ground-truth** (λ thật) do `datagen` sinh ra — để ngoài DB vận hành, dùng chấm điểm Phase 1.
- **Có thể thay** `HistGradientBoostingRegressor` bằng **LightGBM** (production); thay `scipy HiGHS` bằng **OR-Tools/Gurobi** nếu cần. Interface không đổi.
- Ánh xạ đầu ra với 21 bảng schema: `demand_forecasts` (Khối 1), `bid_prices`/`quotas` (Khối 2A), `seat`/`gap_combinations` (Khối 2B), `price_quotes` (Khối 3).
- Tham số sinh dữ liệu & mạng 20 ga: xem `Luat_Sinh_Du_Lieu_SRRM.md`.
