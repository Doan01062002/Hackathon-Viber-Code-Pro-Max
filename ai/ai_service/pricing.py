"""KHỐI 3 — Định giá động.
Giá = markup trên chi phí cơ hội (bid price). Co giãn ước lượng từ dữ liệu, fallback config.
AI chỉ trả giá thô + diễn giải; ép trần/sàn là việc của backend (Policy Guard).
"""

from __future__ import annotations

import numpy as np

from . import config as C


def estimate_elasticity(history) -> dict:
    """Ước lượng ε per seat_type từ log-log (willing vs giá). Fallback config nếu không ổn."""
    eps = {}
    for stype in C.SEAT_TYPES:
        d = history[(history["seat_type"] == stype) & (history["willing"] > 0)].copy()
        if len(d) > 500:
            # khử nhiễu theo OD: dùng biến thiên giá TRONG từng OD (elasticity thật),
            # tránh nhiễu do OD lớn vừa đắt vừa đông (confound).
            d["lp"] = np.log(d["shown_price"].values)
            d["lq"] = np.log(d["willing"].values)
            d["lp"] -= d.groupby("od_id")["lp"].transform("mean")
            d["lq"] -= d.groupby("od_id")["lq"].transform("mean")
            slope = np.polyfit(d["lp"], d["lq"], 1)[0]
            e = -slope
            e = e if e > 1.05 else C.ELASTICITY[stype]
        else:
            e = C.ELASTICITY[stype]
        eps[stype] = float(np.clip(e, C.ELASTICITY_FLOOR, C.ELASTICITY_CAP))  # chặn markup nổ
    return eps


def price_od(od, bid_prices, eps, policy=None):
    """od: dict (od_id, seat_type, segments, base_price).
    bid_prices: dict (seg,seat_type)->pi. eps: dict seat_type->ε.
    Trả về giá đề xuất + diễn giải."""
    stype = od["seat_type"]
    oc = sum(bid_prices.get((seg, stype), 0.0) for seg in od["segments"])
    e = eps.get(stype, C.ELASTICITY[stype])
    # markup nhân trên chi phí cơ hội; sàn mềm = base_price (không bán dưới giá cơ sở)
    markup_price = oc * e / (e - 1) if oc > 0 else 0.0
    proposed = max(markup_price, od["base_price"])
    proposed = min(proposed, od["base_price"] * C.MAX_SURGE)  # trần surge (Policy Guard)
    # nút cổ chai: chặng có bid price cao nhất
    seg_pis = {seg: bid_prices.get((seg, stype), 0.0) for seg in od["segments"]}
    bottleneck = max(seg_pis, key=seg_pis.get) if seg_pis else None
    final = proposed
    decision = "accepted"
    if policy:  # backend guard (tùy chọn)
        final = min(max(proposed, policy["min_price"]), policy["max_price"])
        if final != proposed:
            decision = "blocked"
    return dict(
        od_id=int(od["od_id"]),
        seat_type=stype,
        opportunity_cost=float(round(oc, 0)),
        proposed_price=float(round(proposed, 0)),
        final_price=float(round(final, 0)),
        decision=decision,
        explanation=dict(
            bottleneck_segment=(int(bottleneck) if bottleneck is not None else None),
            segment_pi={int(k): float(v) for k, v in seg_pis.items()},
            elasticity=float(round(e, 3)),
            base_price=float(od["base_price"]),
        ),
    )
