"""Đánh giá KHỐI 2 (tối ưu) — replay CÙNG luồng nhu cầu (từ seeds) qua 2 chính sách:
  • NỀN  : đến trước phục vụ trước (FCFS) — còn chỗ thì bán, không chặn.
  • AI   : chấp nhận vé nếu giá ≥ Σ bid price (bid price tính từ dự báo Khối 1 qua DLP).
So KPI: doanh thu, passenger-km (ghế-km), khách phục vụ, vé từ chối -> Δ% uplift.
Giá GIỮ NGUYÊN cho cả hai (base_price) để cô lập giá trị của TỐI ƯU (không lẫn định giá).

Chạy:  python scripts/eval_optimization.py --from-seeds out/seeds
"""
from __future__ import annotations

import argparse
import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from ai_service import adapter
from ai_service import config as C
from ai_service import optimization as opt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(REPO, "models", "model.pkl")
KM = [s[2] for s in C.STATIONS]                     # km lũy kế mỗi ga (0-based)
SEG_DIST = [KM[i + 1] - KM[i] for i in range(len(KM) - 1)]
NSEG = len(SEG_DIST)
CAP_KM = sum(C.CAPACITY[st] * SEG_DIST[i] for i in range(NSEG) for st in C.SEAT_TYPES)


def replay(reqs, bid=None):
    """reqs: list (o_idx, d_idx, seat_type, fare, dist). bid=None -> nền; dict -> AI."""
    rem = {st: [C.CAPACITY[st]] * NSEG for st in C.SEAT_TYPES}
    rev = paxkm = served = rejected = 0.0
    for o, d, st, fare, dist in reqs:
        segs = range(o, d)
        has_cap = all(rem[st][s] > 0 for s in segs)
        ok = has_cap
        if bid is not None and has_cap:               # AI: thêm điều kiện bid price
            oc = sum(bid.get((s, st), 0.0) for s in segs)
            ok = fare >= oc
        if ok:
            for s in segs:
                rem[st][s] -= 1
            rev += fare; paxkm += dist; served += 1
        else:
            rejected += 1
    return dict(revenue=rev, paxkm=paxkm, served=served, rejected=rejected)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-seeds", type=str, required=True)
    args = ap.parse_args()
    seeds = args.from_seeds

    fc = pickle.load(open(MODEL_PATH, "rb"))["forecaster"]

    # --- tải bảng seeds ---
    od = pd.read_csv(os.path.join(seeds, "od_products.csv"))
    trips = pd.read_csv(os.path.join(seeds, "trips.csv"))[["id", "service_date"]].rename(columns={"id": "trip_id"})
    od = od.merge(trips, on="trip_id")
    od["service_date"] = pd.to_datetime(od["service_date"])
    odm = od.set_index("id")   # od_product_id -> thuộc tính
    bk = pd.read_csv(os.path.join(seeds, "bookings.csv"))
    sl = pd.read_csv(os.path.join(seeds, "search_logs.csv"))
    cal = pd.read_csv(os.path.join(seeds, "calendar_features.csv"))
    cal["service_date"] = pd.to_datetime(cal["service_date"])
    def _b(s): return s.astype(str).str.lower().isin(["true", "1"])
    peak_dates = set(cal.loc[_b(cal.is_tet) | _b(cal.is_holiday), "service_date"])

    # --- dự báo λ̂ (Khối 1) cho mọi (OD, ngày) qua adapter ---
    hist = adapter.load_history(seeds)
    hist["lam"] = fc.predict(hist)["lambda_hat"].values
    lam = {(r.service_date, r.origin_station_id, r.destination_station_id, r.seat_type): r.lam
           for r in hist.itertuples()}

    # --- dựng luồng nhu cầu (bookings + sold_out) theo ngày ---
    reqs_by_date = {}
    def add(opid, fare_hint=None):
        a = odm.loc[opid]
        o, d = int(a.origin_station_id) - 1, int(a.destination_station_id) - 1
        dist = KM[d] - KM[o]
        reqs_by_date.setdefault(a.service_date, []).append(
            (o, d, a.seat_type, float(a.base_price), dist))
    for opid in bk["od_product_id"].values:
        add(opid)
    for opid in sl.loc[sl["result"] == "sold_out", "od_product_id"].dropna().astype(int).values:
        add(opid)

    # --- chạy replay từng ngày, cộng KPI (tổng / cao điểm / thường) ---
    buckets = {"all": {}, "peak": {}, "normal": {}}
    for b in buckets.values():
        b["nen"] = dict(revenue=0, paxkm=0, served=0, rejected=0)
        b["ai"] = dict(revenue=0, paxkm=0, served=0, rejected=0)
        b["days"] = 0; b["capkm"] = 0.0

    for sd, reqs in reqs_by_date.items():
        # bid price cho ngày này
        ods_day, lamd = [], {}
        seen = set()
        for (o, d, st, fare, dist) in reqs:
            key = (o, d, st)
            if key in seen:
                continue
            seen.add(key)
            oid = len(ods_day)
            ods_day.append(dict(od_id=oid, seat_type=st, segments=list(range(o, d)), base_price=fare))
            lamd[oid] = lam.get((sd, o + 1, d + 1, st), 0.0)
        try:
            bid = opt.solve_bid_prices(ods_day, lamd, NSEG)["bid_prices"]
        except Exception:
            bid = {}
        rn = replay(reqs, None)
        ra = replay(reqs, bid)
        tag = "peak" if sd in peak_dates else "normal"
        for grp in ("all", tag):
            for k in rn: buckets[grp]["nen"][k] += rn[k]
            for k in ra: buckets[grp]["ai"][k] += ra[k]
            buckets[grp]["days"] += 1; buckets[grp]["capkm"] += CAP_KM

    # --- in báo cáo ---
    def pct(a, n): return (a - n) / n * 100 if n else 0.0
    for grp, title in [("all", "TỔNG THỂ"), ("peak", "CAO ĐIỂM (lễ/Tết)"), ("normal", "NGÀY THƯỜNG")]:
        b = buckets[grp]
        if b["days"] == 0:
            continue
        n, a, capkm = b["nen"], b["ai"], b["capkm"]
        print(f"\n===== {title}  ({b['days']} chuyến) =====")
        print(f"{'Chỉ số':22s}{'Nền (FCFS)':>16s}{'AI (bid price)':>18s}{'Δ%':>9s}")
        print(f"{'Doanh thu (đ)':22s}{n['revenue']:>16,.0f}{a['revenue']:>18,.0f}{pct(a['revenue'],n['revenue']):>8.1f}%")
        print(f"{'Passenger-km':22s}{n['paxkm']:>16,.0f}{a['paxkm']:>18,.0f}{pct(a['paxkm'],n['paxkm']):>8.1f}%")
        print(f"{'Khách phục vụ':22s}{n['served']:>16,.0f}{a['served']:>18,.0f}{pct(a['served'],n['served']):>8.1f}%")
        print(f"{'Vé từ chối':22s}{n['rejected']:>16,.0f}{a['rejected']:>18,.0f}{pct(a['rejected'],n['rejected']):>8.1f}%")
        print(f"{'Hệ số dùng ghế-km':22s}{n['paxkm']/capkm*100:>15.1f}%{a['paxkm']/capkm*100:>17.1f}%")


if __name__ == "__main__":
    main()
