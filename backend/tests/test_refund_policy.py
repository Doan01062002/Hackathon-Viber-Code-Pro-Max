from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from backend.services.refund_policy import compute_refund, resolve_tier

DEPARTURE = datetime(2026, 8, 1, 20, 0, tzinfo=UTC)


def at(hours_before: float) -> datetime:
    return DEPARTURE - timedelta(hours=hours_before)


class TestResolveTier:
    def test_hon_24_gio_truoc_gio_chay_thi_hoan_90(self):
        assert resolve_tier(DEPARTURE, at(48)).rate == Decimal("0.90")

    def test_dung_moc_24_gio_van_duoc_bac_cao_nhat(self):
        # Biên: >= 24h thuộc bậc 'early', không rơi xuống 'standard'.
        assert resolve_tier(DEPARTURE, at(24)).code == "early"

    def test_giua_4_va_24_gio_thi_hoan_70(self):
        assert resolve_tier(DEPARTURE, at(10)).rate == Decimal("0.70")

    def test_dung_moc_4_gio_thuoc_bac_standard(self):
        assert resolve_tier(DEPARTURE, at(4)).code == "standard"

    def test_duoi_4_gio_thi_hoan_50(self):
        assert resolve_tier(DEPARTURE, at(1)).rate == Decimal("0.50")

    def test_dung_gio_chay_thi_khong_hoan(self):
        assert resolve_tier(DEPARTURE, DEPARTURE).code == "departed"

    def test_sau_gio_chay_thi_khong_hoan(self):
        assert resolve_tier(DEPARTURE, at(-2)).rate == Decimal("0")


class TestComputeRefund:
    def test_hoan_va_phi_cong_lai_bang_so_tien_goc(self):
        out = compute_refund(Decimal("1000000"), DEPARTURE, at(48))
        assert out.refund_amount == Decimal("900000.00")
        assert out.refund_amount + out.fee_amount == Decimal("1000000.00")

    def test_lam_tron_ve_hai_chu_so_thap_phan(self):
        out = compute_refund(Decimal("333333"), DEPARTURE, at(10))
        assert out.refund_amount == Decimal("233333.10")
        assert out.refund_amount + out.fee_amount == Decimal("333333.00")

    def test_ve_giu_cho_chua_thanh_toan_thi_khong_hoan(self):
        out = compute_refund(Decimal("500000"), DEPARTURE, at(48), is_paid=False)
        assert out.refund_amount == Decimal("0.00")
        assert out.tier_code == "held"

    def test_so_tien_am_thi_bao_loi(self):
        with pytest.raises(ValueError):
            compute_refund(Decimal("-1"), DEPARTURE, at(48))
