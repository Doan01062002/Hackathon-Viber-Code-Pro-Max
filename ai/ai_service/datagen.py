"""Bộ sinh dữ liệu mô phỏng theo Luat_Sinh_Du_Lieu_SRRM.md (20 ga).
Sinh: mạng (segments, od_products), lịch sử nhu cầu/vé, và ground-truth (lambda thật).
Cách tiếp cận vectorized theo (trip, od) để chạy nhanh.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import config as C


def build_network():
    """Trả về stations_df, segments (list dict), od_products (list dict)."""
    st = C.station_df()
    n = len(st)
    # 19 chặng giữa các ga liên tiếp
    segments = []
    for i in range(n - 1):
        segments.append(
            dict(
                seg_idx=i,
                from_idx=i,
                to_idx=i + 1,
                from_code=st.code[i],
                to_code=st.code[i + 1],
                distance_km=st.km[i + 1] - st.km[i],
            )
        )
    bottleneck_seg = C.HUE_IDX  # chặng Huế(8)->Đà Nẵng(9) có seg_idx = 8

    # OD products: i<j, mở bán nếu 1 đầu là hub hoặc base_od>=nguong
    od_products = []
    oid = 0
    for i in range(n):
        for j in range(i + 1, n):
            dist = st.km[j] - st.km[i]
            crosses_bottleneck = i <= bottleneck_seg < j
            pair_boost = 1.0
            if st.code[i] == "HN" and st.code[j] == "VIN":
                pair_boost *= C.PAIR_BOOST_HN_VIN
            if crosses_bottleneck:
                pair_boost *= C.BOTTLENECK_BOOST
            geo = st["pop"][i] * st["pop"][j] * np.exp(-dist / C.DISTANCE_DECAY) * pair_boost
            for stype in C.SEAT_TYPES:
                share = _seat_share(dist, stype)
                base_od = geo * share
                is_hub_pair = bool(st.is_hub[i] or st.is_hub[j])
                if not (is_hub_pair or base_od >= C.MIN_BASE_OD):
                    continue
                segs = list(range(i, j))  # seg_idx đi qua
                od_products.append(
                    dict(
                        od_id=oid,
                        origin_idx=i,
                        dest_idx=j,
                        origin=st.code[i],
                        dest=st.code[j],
                        seat_type=stype,
                        distance_km=float(dist),
                        base_price=C.base_price(stype, dist),
                        base_od=float(base_od),
                        segments=segs,
                        crosses_bottleneck=crosses_bottleneck,
                        pop_o=float(st["pop"][i]),
                        pop_d=float(st["pop"][j]),
                        is_hub_o=bool(st.is_hub[i]),
                        is_hub_d=bool(st.is_hub[j]),
                    )
                )
                oid += 1
    return st, segments, od_products, bottleneck_seg


def _seat_share(dist, stype):
    if dist <= 350:  # chặng ngắn nghiêng ngồi mềm
        return 0.70 if stype == "ngoi_mem" else 0.30
    return 0.35 if stype == "ngoi_mem" else 0.65


# ---- lịch: lễ & Tết ----
def _tet_start(year):  # xấp xỉ mùng 1 Tết
    return {2023: date(2023, 1, 22), 2024: date(2024, 2, 10), 2025: date(2025, 1, 29), 2026: date(2026, 2, 17)}.get(
        year, date(year, 2, 1)
    )


def calendar_factor(d: date):
    is_tet = abs((d - _tet_start(d.year)).days) <= 10
    holidays = {(1, 1), (4, 30), (5, 1), (9, 2)}
    is_holiday = (d.month, d.day) in holidays
    if is_tet:
        f = 3.0
    elif is_holiday:
        f = 1.8
    else:
        f = 1.0
    return f, is_holiday, is_tet


def lam_for(od, d: date):
    f_dow = C.DOW_FACTOR[d.weekday()]
    f_season = C.season_factor(d.month, od["dest_idx"])
    f_hol, is_hol, is_tet = calendar_factor(d)
    lam = C.SCALE_K * od["base_od"] * f_dow * f_season * f_hol
    return max(lam, 1e-6), f_dow, f_season, f_hol, is_hol, is_tet


def _nb(rng, mean, r=C.NEGBINOM_R):
    mean = np.asarray(mean, float)
    p = r / (r + mean)
    return rng.negative_binomial(r, p)


def simulate(start: date, days: int, seed: int = 42, focal_offset: int | None = None):
    """Sinh lịch sử. Trả về dict gồm history_df, meta, focal (trip cụ thể)."""
    rng = np.random.default_rng(seed)
    st, segments, ods, bottleneck_seg = build_network()
    nseg = len(segments)
    records = []
    focal = None
    focal_date = start + timedelta(days=focal_offset) if focal_offset is not None else None

    for t in range(days):
        d = start + timedelta(days=t)
        # tồn kho còn lại theo (seg, seat_type)
        remaining = {stype: np.full(nseg, C.CAPACITY[stype], dtype=int) for stype in C.SEAT_TYPES}
        order = rng.permutation(len(ods))  # thứ tự xử lý OD (công bằng)
        focal_bookings = [] if (focal_date and d == focal_date) else None

        for k in order:
            od = ods[k]
            lam, f_dow, f_season, f_hol, is_hol, is_tet = lam_for(od, d)
            demand = int(_nb(rng, lam))
            # giá hiển thị: biến thiên -> nhận diện co giãn
            weekend = 1.0 if d.weekday() >= 4 else 0.0
            price_mult = (1 + 0.10 * weekend) * (1 + rng.uniform(-0.15, 0.20))
            shown_price = od["base_price"] * price_mult
            # WTP
            willing = 0
            if demand > 0:
                med = C.WTP_MEDIAN_MULT * od["base_price"]
                mu = np.log(med)
                w = rng.lognormal(mu, C.WTP_SIGMA_LOG, size=demand)
                willing = int(np.sum(w >= shown_price))
            # cấp chỗ theo capacity chung các chặng của OD
            segs = od["segments"]
            stype = od["seat_type"]
            cap_left = int(remaining[stype][segs].min()) if segs else 0
            booked = min(willing, cap_left)
            if booked > 0:
                remaining[stype][segs] -= booked
            soldout = willing - booked
            browse = int(demand - willing + rng.poisson(C.BROWSE_MULT * max(booked, 1) * 0.3))
            revenue = booked * shown_price
            records.append(
                dict(
                    service_date=d,
                    od_id=od["od_id"],
                    seat_type=stype,
                    dow=d.weekday(),
                    month=d.month,
                    is_holiday=int(is_hol),
                    is_tet=int(is_tet),
                    is_summer=int(d.month in (6, 7, 8)),
                    distance_km=od["distance_km"],
                    base_price=od["base_price"],
                    pop_o=od["pop_o"],
                    pop_d=od["pop_d"],
                    is_hub_o=int(od["is_hub_o"]),
                    is_hub_d=int(od["is_hub_d"]),
                    crosses_bottleneck=int(od["crosses_bottleneck"]),
                    shown_price=shown_price,
                    bookings=booked,
                    soldout=soldout,
                    browse=max(browse, 0),
                    revenue=revenue,
                    true_demand=demand,
                    willing=willing,
                    lambda_true=lam,
                )
            )
            if focal_bookings is not None and booked > 0:
                for _ in range(booked):
                    focal_bookings.append(
                        dict(od_id=od["od_id"], origin_idx=od["origin_idx"], dest_idx=od["dest_idx"], seat_type=stype)
                    )
        if focal_bookings is not None:
            focal = dict(service_date=d, bookings=focal_bookings)

    hist = pd.DataFrame.from_records(records)
    meta = dict(stations=st, segments=segments, od_products=ods, bottleneck_seg=bottleneck_seg)
    return dict(history=hist, meta=meta, focal=focal)
