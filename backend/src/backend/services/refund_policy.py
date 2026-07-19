"""Chính sách hoàn tiền khi hủy vé.

Tách riêng khỏi service để test được mà không cần database, và để sửa mốc/tỉ lệ
ở một chỗ duy nhất khi nghiệp vụ thay đổi.

PRD chưa quy định con số cụ thể; các mốc dưới đây theo thông lệ đường sắt VN và
là giá trị tạm cho tới khi có quyết định chính thức.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class RefundTier:
    """Một bậc hoàn tiền: đặt trước giờ chạy ít nhất `min_lead` thì hoàn `rate`."""

    code: str
    min_lead: timedelta
    rate: Decimal
    label: str


# Xếp từ mốc xa nhất tới gần nhất — tra cứu sẽ lấy bậc đầu tiên khớp.
REFUND_TIERS: tuple[RefundTier, ...] = (
    RefundTier("early", timedelta(hours=24), Decimal("0.90"), "Hủy trước giờ chạy trên 24 giờ"),
    RefundTier("standard", timedelta(hours=4), Decimal("0.70"), "Hủy trước giờ chạy từ 4 đến 24 giờ"),
    RefundTier("late", timedelta(0), Decimal("0.50"), "Hủy trước giờ chạy dưới 4 giờ"),
)

NO_REFUND = RefundTier("departed", timedelta.min, Decimal("0.00"), "Tàu đã khởi hành, không hoàn tiền")

# Vé mới giữ chỗ, chưa thanh toán thì không có gì để hoàn.
HELD_TIER = RefundTier("held", timedelta.min, Decimal("0.00"), "Vé đang giữ chỗ, chưa thanh toán")


@dataclass(frozen=True)
class RefundOutcome:
    tier_code: str
    label: str
    rate: Decimal
    refund_amount: Decimal
    fee_amount: Decimal


def _quantize(value: Decimal) -> Decimal:
    """Làm tròn về đồng, tránh số lẻ khi ghi vào NUMERIC(14,2)."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def resolve_tier(departure_at: datetime, now: datetime) -> RefundTier:
    """Bậc hoàn tiền áp dụng khi hủy tại thời điểm `now`."""
    lead = departure_at - now
    if lead <= timedelta(0):
        return NO_REFUND
    for tier in REFUND_TIERS:
        if lead >= tier.min_lead:
            return tier
    return NO_REFUND


def compute_refund(
    amount: Decimal,
    departure_at: datetime,
    now: datetime,
    *,
    is_paid: bool = True,
) -> RefundOutcome:
    """Số tiền hoàn cho một khoản `amount` của chuyến khởi hành lúc `departure_at`.

    `is_paid=False` dùng cho vé mới giữ chỗ chưa thanh toán — hủy thì không hoàn.
    """
    if amount < 0:
        raise ValueError("Số tiền hoàn không thể tính trên khoản âm")

    tier = HELD_TIER if not is_paid else resolve_tier(departure_at, now)
    refund = _quantize(amount * tier.rate)
    return RefundOutcome(
        tier_code=tier.code,
        label=tier.label,
        rate=tier.rate,
        refund_amount=refund,
        fee_amount=_quantize(amount - refund),
    )
