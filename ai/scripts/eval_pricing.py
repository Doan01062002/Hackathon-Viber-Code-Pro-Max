"""Đánh giá KHỐI 3 — ĐỊNH GIÁ ĐỘNG.

VÌ SAO KHÔNG DÙNG SEED:
  Định giá làm THAY ĐỔI cầu — đổi giá thì đổi luôn ai còn mua. Muốn đo được điều đó
  phải biết mức-sẵn-lòng-trả (WTP) của từng khách. Seed chỉ ghi vé ĐÃ bán tại một mức
  giá, không mang WTP -> không đánh giá định giá được. Nên khối này đánh giá trên BỘ
  MÔ PHỎNG (datagen), nơi ta biết WTP thật của từng khách.

CÁCH ĐO — phản thực có kiểm soát (paired counterfactual):
  Sinh MỘT tập khách (mỗi khách 1 WTP cố định) + MỘT thứ tự đến cố định, rồi cho CÙNG
  tập khách đó đối mặt các chính sách khác nhau. Chênh lệch KPI chỉ do CHÍNH SÁCH.

BA CHÍNH SÁCH (tách để cô lập đúng phần đóng góp của Khối 3):
  • NỀN      : giá cố định = base_price, nhận theo FCFS (không AI).
  • +KHỐI 2  : giá cố định = base_price, nhận/từ chối theo bid price (tối ưu chỗ).
  • +KHỐI 3  : giá ĐỘNG = markup trên bid price, chặn bởi trần surge — trên nền Khối 2.
  => Giá trị RIÊNG của Khối 3 = (+KHỐI 3) − (+KHỐI 2).

QUÉT TRẦN SURGE:
  Doanh thu định giá có dạng "chuông" theo trần surge (nâng ít thì bỏ lỡ; nâng nhiều
  thì mất khách). Script quét trần, in đường cong, chỉ ra điểm tối ưu, rồi in bảng
  3 chính sách chi tiết tại điểm đó.

HAI GIẢ ĐỊNH QUAN TRỌNG (ghi rõ để minh bạch):
  1. Cầu nạp vào bộ tối ưu = CẦU-TRẢ-TIỀN tại giá gốc (số khách WTP ≥ base) — đúng thứ
     Khối 1 dự báo (target = bookings + soldout), KHÔNG phải λ đến thô. Nhờ đó ngày vắng
     bid price = 0, hệ thống không tăng giá bừa.
  2. WTP nhích theo cao điểm (Tết khách trả cao hơn & phân tán rộng) — phản ánh thực tế,
     là điều kiện để định giá động có giá trị. Dùng λ_true cho bid price (giả định dự báo
     hoàn hảo) để cô lập giá trị ĐỊNH GIÁ khỏi sai số dự báo (sai số đo riêng bằng eval.py).

Chạy:  python scripts/eval_pricing.py --days 120 --start 2024-02-01 --seed 202
"""
from __future__ import annotations
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import date, timedelta
import numpy as np
from ai_service import datagen, optimization as opt, pricing, config as C

# ---- hằng số mạng ----
KM = [s[2] for s in C.STATIONS]
SEG_DIST = [KM[i + 1] - KM[i] for i in range(len(KM) - 1)]
NSEG = len(SEG_DIST)
CAP_KM = sum(C.CAPACITY[st] * SEG_DIST[i] for i in range(NSEG) for st in C.SEAT_TYPES)

# ---- WTP theo mùa (median so với giá gốc, sigma log) ----
#   Ngày thường: giá gốc ĐÃ gần tối ưu -> định giá khó thêm.
#   Lễ/Tết     : khách trả cao hơn & PHÂN TÁN RỘNG (có nhóm WTP cao), sức chứa ràng buộc
#                -> đây là lúc định giá động có giá trị.
WTP = {"normal": (1.05, 0.30), "peak": (1.45, 0.50)}
SURGE_GRID = [1.10, 1.20, 1.30, 1.40, 1.50, 1.60, 1.75, 2.00, 2.50]


def gen_day(rng, ods, d):
    """Sinh một ngày: khách rời rạc [(od_idx, wtp)], cầu-trả-tiền mỗi OD, cờ cao điểm."""
    _, is_hol, is_tet = datagen.calendar_factor(d)
    is_peak = is_hol or is_tet
    med_mult, sig = WTP["peak"] if is_peak else WTP["normal"]
    custs, demand_paid = [], {}
    for k, od in enumerate(ods):
        lam = datagen.lam_for(od, d)[0]
        n = int(datagen._nb(rng, lam))
        if n <= 0:
            demand_paid[k] = 0.0
            continue
        w = rng.lognormal(np.log(med_mult * od["base_price"]), sig, size=n)
        demand_paid[k] = float(np.sum(w >= od["base_price"]))   # cầu Khối 1 dự báo
        custs.extend((k, float(wi)) for wi in w)
    return custs, demand_paid, is_peak


def opp_cost(od, bid):
    """Chi phí cơ hội = Σ bid price các chặng OD đi qua."""
    return sum(bid.get((s, od["seat_type"]), 0.0) for s in od["segments"])


def dyn_price(od, bid, eps, cap):
    """Giá động = markup ε/(ε−1)·oc; sàn = base; trần = base × cap."""
    oc = opp_cost(od, bid)
    e = eps.get(od["seat_type"], C.ELASTICITY[od["seat_type"]])
    markup = oc * e / (e - 1) if oc > 0 else 0.0
    return min(max(markup, od["base_price"]), od["base_price"] * cap)


def replay(order, ods, decide):
    """Chạy CÙNG luồng khách qua một chính sách.
    decide(k, wtp, bid) -> (book: bool, price: float). Trả KPI (doanh thu, vé, ghế-km)."""
    rem = {st: [C.CAPACITY[st]] * NSEG for st in C.SEAT_TYPES}
    rev = vol = paxkm = 0.0
    for k, wtp in order:
        od = ods[k]; stype = od["seat_type"]; segs = od["segments"]
        if not all(rem[stype][s] > 0 for s in segs):     # hết chỗ -> mất khách
            continue
        book, price = decide(k, wtp)
        if book:
            for s in segs:
                rem[stype][s] -= 1
            rev += price; vol += 1; paxkm += od["distance_km"]
    return dict(revenue=rev, vol=vol, paxkm=paxkm)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=120)
    ap.add_argument("--start", type=str, default="2024-02-01")   # gồm cao điểm Tết 2024-02-10
    ap.add_argument("--seed", type=int, default=202)
    args = ap.parse_args()
    start = date.fromisoformat(args.start)

    _, _, ods, _ = datagen.build_network()
    eps = pricing.estimate_elasticity(datagen.simulate(date(2023, 1, 1), 365, seed=7)["history"])
    print(f"[eval-price] ε ước lượng: { {k: round(v, 2) for k, v in eps.items()} }  "
          f"(markup thô = ε/(ε−1) ≈ {eps['ngoi_mem'] / (eps['ngoi_mem'] - 1):.1f}× oc)")
    print("[eval-price] Cầu->bid price: λ_true (dự báo hoàn hảo; sai số dự báo đo riêng eval.py)")

    # --- tiền xử lý từng ngày: khách + thứ tự đến + bid price (độc lập với trần surge) ---
    rng = np.random.default_rng(args.seed)
    org = np.random.default_rng(args.seed + 1)
    days = []
    for t in range(args.days):
        d = start + timedelta(days=t)
        custs, demand_paid, is_peak = gen_day(rng, ods, d)
        if not custs:
            continue
        ods_day = [dict(od_id=k, seat_type=od["seat_type"], segments=od["segments"],
                        base_price=od["base_price"]) for k, od in enumerate(ods)]
        try:
            bid = opt.solve_bid_prices(ods_day, demand_paid, NSEG)["bid_prices"]
        except Exception:
            bid = {}
        order = list(custs); org.shuffle(order)                  # CÙNG thứ tự cho mọi chính sách
        days.append(dict(order=order, bid=bid, peak=is_peak))
    npk = sum(x["peak"] for x in days); nnm = len(days) - npk
    print(f"[eval-price] {len(days)} chuyến ({npk} cao điểm / {nnm} thường)\n")

    # --- các hàm quyết định của 3 chính sách ---
    def d_base(day):
        return lambda k, wtp: (wtp >= ods[k]["base_price"], ods[k]["base_price"])

    def d_k2(day):
        def f(k, wtp):
            base = ods[k]["base_price"]
            accept = base >= opp_cost(ods[k], day["bid"])        # bid price từ chối vé rẻ qua nút cổ chai
            return (wtp >= base and accept, base)
        return f

    def d_k3(day, cap):
        def f(k, wtp):
            p = dyn_price(ods[k], day["bid"], eps, cap)          # giá đã ≥ oc nên rào bid price luôn thỏa
            return (wtp >= p, p)
        return f

    def run(decide_factory):
        """Cộng KPI qua mọi ngày, tách all/peak/normal."""
        out = {g: dict(revenue=0.0, vol=0.0, paxkm=0.0) for g in ("all", "peak", "normal")}
        for day in days:
            r = replay(day["order"], ods, decide_factory(day))
            for g in ("all", "peak" if day["peak"] else "normal"):
                for kk in r:
                    out[g][kk] += r[kk]
        return out

    def pct(a, n):
        return (a - n) / n * 100 if n else 0.0

    base = run(d_base)
    k2 = run(d_k2)

    # --- QUÉT trần surge: đường cong doanh thu định giá động (Δ% so với NỀN) ---
    sweep = {cap: run(lambda day, cap=cap: d_k3(day, cap)) for cap in SURGE_GRID}
    best_cap = max(SURGE_GRID, key=lambda c: sweep[c]["all"]["revenue"])
    print("=== QUÉT TRẦN SURGE — Δ% doanh thu định giá động so với NỀN ===")
    print(f"{'trần surge':>11s}{'Δ% tổng':>10s}{'Δ% cao điểm':>13s}{'Δ% thường':>12s}")
    for cap in SURGE_GRID:
        dp = sweep[cap]
        mark = " <= tối ưu" if cap == best_cap else ""
        print(f"{cap:>10.2f}×{pct(dp['all']['revenue'], base['all']['revenue']):>9.1f}%"
              f"{pct(dp['peak']['revenue'], base['peak']['revenue']):>12.1f}%"
              f"{pct(dp['normal']['revenue'], base['normal']['revenue']):>11.1f}%{mark}")
    print(f"\n>>> Trần surge TỐI ƯU (theo doanh thu tổng): {best_cap:.2f}×   "
          f"(trần cứng Policy Guard {C.MAX_SURGE:.1f}× chỉ là rào an toàn, không phải điểm vận hành)")

    # --- bảng 3 chính sách chi tiết tại trần tối ưu ---
    dp = sweep[best_cap]
    for g, title in [("all", "TỔNG THỂ"), ("peak", "CAO ĐIỂM (lễ/Tết)"), ("normal", "NGÀY THƯỜNG")]:
        b, k, p = base[g], k2[g], dp[g]
        ndays = len(days) if g == "all" else (npk if g == "peak" else nnm)
        capkm = ndays * CAP_KM
        print(f"\n===== {title}  ({ndays} chuyến · trần {best_cap:.2f}×) =====")
        print(f"{'Chỉ số':20s}{'NỀN':>14s}{'+KHỐI 2':>14s}{'+KHỐI 3':>14s}"
              f"{'Δ K3/Nền':>12s}{'Δ K3/K2':>11s}")
        for name, key in [("Doanh thu (đ)", "revenue"), ("Vé bán", "vol"), ("Passenger-km", "paxkm")]:
            print(f"{name:20s}{b[key]:>14,.0f}{k[key]:>14,.0f}{p[key]:>14,.0f}"
                  f"{pct(p[key], b[key]):>11.1f}%{pct(p[key], k[key]):>10.1f}%")
        avg = lambda m: (m["revenue"] / m["vol"]) if m["vol"] else 0.0
        print(f"{'Giá TB/vé (đ)':20s}{avg(b):>14,.0f}{avg(k):>14,.0f}{avg(p):>14,.0f}"
              f"{pct(avg(p), avg(b)):>11.1f}%{pct(avg(p), avg(k)):>10.1f}%")
        print(f"{'Lấp đầy ghế-km':20s}{b['paxkm'] / capkm * 100:>13.1f}%"
              f"{k['paxkm'] / capkm * 100:>13.1f}%{p['paxkm'] / capkm * 100:>13.1f}%")

    print("\n(Δ K3/K2 = giá trị RIÊNG của định giá động; Δ K3/Nền = giá trị cả tối ưu + định giá.)")
    print("(Ngày thường ~0% là ĐÚNG: không khan hiếm -> bid price = 0 -> không surge.)")


if __name__ == "__main__":
    main()
