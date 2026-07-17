"""AI-11 + AI-16.1 + AI-16.2 — Markup trên chi phí cơ hội + diễn giải."""

from __future__ import annotations


def compute_opportunity_cost(od: dict, bid_prices: dict[tuple[int, str], float]) -> float:
    """c_j = Σ_ℓ a_ℓj·π_ℓ — tổng bid price các chặng mà OD j đi qua (chi phí cơ hội
    của việc bán 1 vé cho luồng OD j)."""
    stype = od["seat_type"]
    return sum(bid_prices.get((seg, stype), 0.0) for seg in od["segments"])


def markup_multiplicative(opportunity_cost: float, epsilon: float) -> float:
    """Công thức markup nhân cho cầu co giãn hằng số (constant elasticity demand):
    p* = c_j · ε/(ε−1). Chỉ có nghĩa khi ε > 1 (cầu co giãn đủ mạnh để tồn tại mức giá
    tối đa hóa lợi nhuận hữu hạn) — `config.ELASTICITY_FLOOR` đã đảm bảo ε ước lượng
    được luôn > 1, nhưng vẫn kiểm tra ở đây để an toàn khi hàm được gọi trực tiếp với
    giá trị ε tùy ý."""
    if opportunity_cost <= 0:
        return 0.0
    if epsilon <= 1.0:
        raise ValueError(f"epsilon phải > 1 để công thức markup nhân có nghĩa, nhận {epsilon}")
    return opportunity_cost * epsilon / (epsilon - 1)


def build_explanation(
    od: dict,
    bid_prices: dict[tuple[int, str], float],
    epsilon: float,
    segment_load: dict[tuple[int, str], float] | None = None,
) -> dict:
    """Sinh diễn giải cho một mức giá đề xuất: chặng nút cổ chai (bid price cao nhất
    trong các chặng OD đi qua), bid price từng chặng, và tải (% sức chứa đã phân bổ)
    tại chặng nút cổ chai đó — giúp người dùng hiểu VÌ SAO giá cao/thấp."""
    stype = od["seat_type"]
    seg_pis = {seg: bid_prices.get((seg, stype), 0.0) for seg in od["segments"]}
    bottleneck = max(seg_pis, key=seg_pis.get) if seg_pis else None

    bottleneck_load_pct = None
    if segment_load is not None and bottleneck is not None:
        load = segment_load.get((bottleneck, stype))
        if load is not None:
            bottleneck_load_pct = round(float(load) * 100, 1)

    return dict(
        bottleneck_segment=(int(bottleneck) if bottleneck is not None else None),
        segment_pi={int(k): float(v) for k, v in seg_pis.items()},
        bottleneck_load_pct=bottleneck_load_pct,
        elasticity=float(round(epsilon, 3)),
        base_price=float(od["base_price"]),
    )
