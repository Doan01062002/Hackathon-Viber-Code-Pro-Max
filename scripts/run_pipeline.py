"""Chạy end-to-end phần AI: sinh data -> dự báo (backtest) -> DLP bid price
-> gán ghế -> ghép đoạn -> định giá. Chứng minh cả 3 khối hoạt động."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import date, timedelta
import numpy as np, pandas as pd

from ai_service import datagen, forecasting, optimization as opt, pricing, config as C


def focal_feature_rows(ods, d: date):
    rows = []
    _, is_hol, is_tet = datagen.calendar_factor(d)
    dtt, pre, post, _ = datagen.tet_context(d)
    is_rainy = int(d.month in C.RAINY_MONTHS)
    for od in ods:
        rows.append(dict(od_id=od["od_id"], seat_type=od["seat_type"],
            dow=d.weekday(), month=d.month, is_holiday=int(is_hol), is_tet=int(is_tet),
            is_summer=int(d.month in (6, 7, 8)),
            days_to_tet=dtt, is_pre_tet=pre, is_post_tet=post, is_rainy=is_rainy, promo=0,
            distance_km=od["distance_km"], base_price=od["base_price"],
            pop_o=od["pop_o"], pop_d=od["pop_d"],
            is_hub_o=int(od["is_hub_o"]), is_hub_d=int(od["is_hub_d"]),
            crosses_bottleneck=int(od["crosses_bottleneck"])))
    return pd.DataFrame(rows)


def main():
    start = date(2023, 1, 1)
    DAYS = 730
    focal_off = (date(2024, 2, 11) - start).days   # chuyến cao điểm Tết -> bid price > 0
    print(f"[1] Sinh dữ liệu 20 ga, {DAYS} ngày ...")
    sim = datagen.simulate(start, DAYS, seed=7, focal_offset=focal_off)
    hist, meta, focal = sim["history"], sim["meta"], sim["focal"]
    ods, nseg, nst = meta["od_products"], len(meta["segments"]), len(C.STATIONS)
    hist["service_date"] = pd.to_datetime(hist["service_date"])
    print(f"    -> {len(hist):,} dòng | {len(ods)} OD mở bán | {nseg} chặng | 20 ga")

    # ---- KHỐI 1: dự báo + backtest ----
    split = start + timedelta(days=int(DAYS * 0.8))
    train = hist[hist.service_date < pd.Timestamp(split)]
    test = hist[hist.service_date >= pd.Timestamp(split)]
    print(f"[2] KHỐI 1 — huấn luyện dự báo (train {len(train):,} / test {len(test):,}) ...")
    fc = forecasting.Forecaster().fit(train)
    ev = forecasting.evaluate(fc, test)
    # WAPE tổng hợp theo OD trên toàn cửa sổ test (mức có nghĩa cho lập kế hoạch)
    tp = test.copy(); tp["seat_code"] = 0
    tp["pred"] = fc.point.predict(forecasting._ensure(test)[forecasting.FEATURES].values)
    agg = tp.groupby("od_id").agg(actual=("bookings", lambda s: (s + test.loc[s.index, "soldout"]).sum()),
                                  pred=("pred", "sum"))
    wape_od = float(np.sum(np.abs(agg.pred - agg.actual)) / max(agg.actual.sum(), 1e-9))
    print(f"    -> WAPE dòng={ev['wape']*100:.1f}%  |  WAPE tổng hợp theo OD={wape_od*100:.1f}%  |  "
          f"corr(λ̂, λ_thật)={ev['corr_lambda_true']:.3f}  (mô hình bắt đúng tín hiệu)")

    # ---- dự báo cho chuyến focal ----
    fdate = focal["service_date"]
    fdate = fdate.date() if hasattr(fdate, "date") else fdate
    feats = focal_feature_rows(ods, fdate)
    pred = fc.predict(feats)
    lambda_hat = dict(zip(pred["od_id"], pred["lambda_hat"]))
    print(f"[3] Dự báo cho chuyến {fdate}: tổng λ̂ = {sum(lambda_hat.values()):.0f} khách")

    # ---- KHỐI 2A: DLP bid price ----
    print("[4] KHỐI 2 — giải DLP (bid price + quota) ...")
    import time; t0 = time.time()
    sol = opt.solve_bid_prices(ods, lambda_hat, nseg)
    dt = (time.time() - t0) * 1000
    # bid price nút cổ chai
    bn = meta["bottleneck_seg"]
    pi_bn = {st: sol["bid_prices"][(bn, st)] for st in C.SEAT_TYPES}
    n_reject = sum(1 for a in sol["accept"].values() if not a["accept"])
    print(f"    -> giải {dt:.0f} ms | doanh thu LP={sol['revenue_lp']:,.0f}đ | bid price nút cổ chai (Huế–ĐN): "
          f"ngồi mềm={pi_bn['ngoi_mem']:,.0f}  giường={pi_bn['giuong_nam_k6']:,.0f}")
    print(f"    -> {n_reject}/{len(ods)} OD bị từ chối theo quy tắc bid price (giá < chi phí cơ hội)")

    # ---- KHỐI 2B: gán ghế + ghép đoạn ----
    print("[5] KHỐI 2 — gán ghế (interval packing) + ghép đoạn ...")
    plan = opt.assign_seats(focal["bookings"])
    for st in C.SEAT_TYPES:
        used = len(plan[st]); need = opt.max_overlap(focal["bookings"], st, nseg)
        ok = "✓ tối ưu" if used == need else "✗"
        print(f"    -> {st}: dùng {used} ghế | tải chồng lấn cực đại {need} {ok}")
    gaps = opt.find_gap_combinations(plan, ods, nst)
    print(f"    -> tìm được {len(gaps)} khoảng trống có thể ghép bán bù (ví dụ 3):")
    st_df = meta["stations"]
    for g in gaps[:3]:
        f, t = st_df.code[g["from_idx"]], st_df.code[g["to_idx"]]
        print(f"       ghế {g['seat_type']}#{g['seat_index']} trống {f}->{t}, gợi ý OD #{g['suggest_od_id']}")

    # ---- KHỐI 3: định giá ----
    print("[6] KHỐI 3 — định giá động (markup trên bid price) ...")
    eps = pricing.estimate_elasticity(hist)
    print(f"    -> độ co giãn ước lượng: {{k: round(v,2) for k,v in eps.items()}}".replace("{k: round(v,2) for k,v in eps.items()}", str({k: round(v,2) for k,v in eps.items()})))
    # vài OD tiêu biểu: 1 qua nút cổ chai, 1 không
    samples = [od for od in ods if od["crosses_bottleneck"] and od["seat_type"] == "giuong_nam_k6"][:1] \
            + [od for od in ods if not od["crosses_bottleneck"] and od["seat_type"] == "giuong_nam_k6"][:1]
    for od in samples:
        q = pricing.price_od(od, sol["bid_prices"], eps)
        o, dd = st_df.code[od["origin_idx"]], st_df.code[od["dest_idx"]]
        print(f"    -> {o}->{dd} ({od['seat_type']}): giá cơ sở {od['base_price']:,.0f} | "
              f"chi phí cơ hội {q['opportunity_cost']:,.0f} | giá đề xuất {q['proposed_price']:,.0f}đ "
              f"({'qua nút cổ chai' if od['crosses_bottleneck'] else 'chặng thường'})")

    print("\n✅ Pipeline AI chạy hoàn tất — cả 3 khối hoạt động.")


if __name__ == "__main__":
    main()
