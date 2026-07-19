"""Vé ghép chặng: khách đi HAN -> DAN nhưng không ghế nào trống suốt tuyến.

Hạt giống test (postgres_seed.sql) có sẵn các sản phẩm OD cần thiết trên chuyến 1:
sản phẩm 1 = HAN(1) -> PHL(2), sản phẩm 3 = PHL(2) -> DAN(10), sản phẩm 5 = HAN(1) -> DAN(10).
Các test dưới đây dựng `gap_combinations` cho hai sản phẩm đầu trên HAI ghế khác nhau,
đúng tình huống chỉ ghép được chứ không bán thẳng.
"""

import pytest
from sqlalchemy import text

from backend.database import get_session_factory

SERVICE_DATE = "2024-01-01"
TRIP_ID = 1
# Chặng đầu và chặng sau của hành trình ghép, khớp span của sản phẩm OD tương ứng.
LEG_ONE_OD_PRODUCT = 1  # HAN -> PHL
LEG_TWO_OD_PRODUCT = 3  # PHL -> DAN


@pytest.fixture()
def gap_chain():
    """Dựng hai khoảng trống nối tiếp trên hai ghế khác nhau, dọn sạch sau test.

    Ghế được chọn từ cuối danh sách để tránh ghế đầu toa mà booking hạt giống
    BK-SEED-TRIP-1 đã chiếm trên chặng HAN -> PHL.
    """
    db = get_session_factory()()
    try:
        seat_ids = [
            row[0]
            for row in db.execute(
                text("""
                    SELECT id FROM seats
                    WHERE trip_id = :trip_id AND seat_type = 'ngoi_mem'
                    ORDER BY id DESC
                    LIMIT 2
                """),
                {"trip_id": TRIP_ID},
            )
        ]
        assert len(seat_ids) == 2

        gap_ids = [
            db.execute(
                text("""
                    INSERT INTO gap_combinations (
                        seat_id, from_station_id, to_station_id,
                        suggested_od_product_id, run_version, is_active
                    )
                    SELECT :seat_id, product.origin_station_id, product.destination_station_id,
                           product.id, 'test-combined', TRUE
                    FROM od_products product
                    WHERE product.id = :od_product_id
                    RETURNING id
                """),
                {"seat_id": seat_id, "od_product_id": od_product_id},
            ).scalar_one()
            for seat_id, od_product_id in zip(
                seat_ids, [LEG_ONE_OD_PRODUCT, LEG_TWO_OD_PRODUCT], strict=True
            )
        ]
        db.commit()

        yield {"gap_ids": gap_ids, "seat_ids": seat_ids}
    finally:
        # Xóa theo thứ tự phụ thuộc: item -> group -> booking -> gap.
        db.rollback()
        db.execute(
            text("""
                DELETE FROM booking_group_items
                WHERE booking_id IN (SELECT id FROM bookings WHERE channel = 'test-combined')
            """)
        )
        db.execute(text("DELETE FROM booking_groups WHERE channel = 'test-combined'"))
        db.execute(text("DELETE FROM bookings WHERE channel = 'test-combined'"))
        db.execute(text("DELETE FROM gap_combinations WHERE run_version = 'test-combined'"))
        db.commit()
        db.close()


async def _search_options(client, **overrides):
    params = {
        "origin": "HAN",
        "destination": "DAN",
        "service_date": SERVICE_DATE,
        "seat_type": "ngoi_mem",
    }
    params.update(overrides)
    return await client.get("/api/v1/booking/combined-options", params=params)


def _pick_two_leg_option(payload, gap_ids):
    wanted = set(gap_ids)
    for option in payload["options"]:
        if {leg["gap_combination_id"] for leg in option["legs"]} == wanted:
            return option
    return None


@pytest.mark.asyncio
async def test_search_returns_two_leg_option_when_no_through_seat(client, gap_chain):
    response = await _search_options(client)
    assert response.status_code == 200

    option = _pick_two_leg_option(response.json(), gap_chain["gap_ids"])
    assert option is not None, "Phải tìm ra phương án ghép HAN -> PHL -> DAN"
    assert option["transfer_count"] == 1
    assert len(option["legs"]) == 2
    assert option["legs"][0]["origin_code"] == "HAN"
    assert option["legs"][0]["destination_code"] == "PHL"
    assert option["legs"][1]["origin_code"] == "PHL"
    assert option["legs"][1]["destination_code"] == "DAN"
    # Hai chặng nằm trên hai ghế khác nhau nên khách phải đổi chỗ giữa đường.
    assert option["legs"][1]["keep_previous_seat"] is False


@pytest.mark.asyncio
async def test_hold_then_confirm_combined_group(client, gap_chain):
    hold = await client.post(
        "/api/v1/booking/combined",
        json={"gap_combination_ids": gap_chain["gap_ids"], "channel": "test-combined"},
    )
    assert hold.status_code == 201, hold.text
    held = hold.json()
    group_code = held["group_code"]
    assert held["status"] == "held"
    assert held["expires_at"] is not None
    assert len(held["legs"]) == 2

    db = get_session_factory()()
    try:
        # Giữ chỗ cả nhóm phải hết hạn cùng lúc, nếu không khách trả tiền chặng đầu
        # rồi mới phát hiện chặng sau đã rơi mất. Không lộ ra response nên soi thẳng DB.
        distinct_expiries = db.execute(
            text("""
                SELECT COUNT(DISTINCT booking.expires_at)
                FROM booking_group_items item
                JOIN bookings booking ON booking.id = item.booking_id
                JOIN booking_groups booking_group ON booking_group.id = item.booking_group_id
                WHERE booking_group.group_code = :group_code
            """),
            {"group_code": group_code},
        ).scalar_one()
        assert distinct_expiries == 1
    finally:
        db.close()

    # Đây là bước từng luôn trả 500 vì confirm_booking không có tham số allow_group.
    confirmed = await client.post(f"/api/v1/booking/combined/{group_code}/confirm")
    assert confirmed.status_code == 200, confirmed.text
    body = confirmed.json()
    assert body["status"] == "confirmed"
    assert len(body["legs"]) == 2
    assert all(leg["status"] == "confirmed" for leg in body["legs"])

    db = get_session_factory()()
    try:
        statuses = [
            row[0]
            for row in db.execute(
                text("""
                    SELECT booking.status
                    FROM booking_group_items item
                    JOIN bookings booking ON booking.id = item.booking_id
                    JOIN booking_groups booking_group ON booking_group.id = item.booking_group_id
                    WHERE booking_group.group_code = :group_code
                    ORDER BY item.sequence_no
                """),
                {"group_code": group_code},
            )
        ]
        assert statuses == ["confirmed", "confirmed"]
    finally:
        db.close()


@pytest.mark.asyncio
async def test_confirming_a_single_leg_directly_is_rejected(client, gap_chain):
    hold = await client.post(
        "/api/v1/booking/combined",
        json={"gap_combination_ids": gap_chain["gap_ids"], "channel": "test-combined"},
    )
    assert hold.status_code == 201, hold.text
    group_code = hold.json()["group_code"]

    db = get_session_factory()()
    try:
        first_booking_id = db.execute(
            text("""
                SELECT item.booking_id
                FROM booking_group_items item
                JOIN booking_groups booking_group ON booking_group.id = item.booking_group_id
                WHERE booking_group.group_code = :group_code
                ORDER BY item.sequence_no
                LIMIT 1
            """),
            {"group_code": group_code},
        ).scalar_one()
    finally:
        db.close()

    response = await client.post(f"/api/v1/booking/{first_booking_id}/confirm")
    assert response.status_code == 400
    assert group_code in response.json()["detail"]


@pytest.mark.asyncio
async def test_hold_rejects_gaps_that_do_not_join_up(client, gap_chain):
    """Hai chặng rời rạc (bỏ trống PHL -> DAN) không được ghép thành hành trình."""
    db = get_session_factory()()
    try:
        orphan_gap_id = db.execute(
            text("""
                INSERT INTO gap_combinations (
                    seat_id, from_station_id, to_station_id,
                    suggested_od_product_id, run_version, is_active
                )
                SELECT :seat_id, product.origin_station_id, product.destination_station_id,
                       product.id, 'test-combined', TRUE
                FROM od_products product
                WHERE product.id = :od_product_id
                RETURNING id
            """),
            {"seat_id": gap_chain["seat_ids"][1], "od_product_id": 5},  # HAN -> DAN
        ).scalar_one()
        db.commit()
    finally:
        db.close()

    response = await client.post(
        "/api/v1/booking/combined",
        json={
            "gap_combination_ids": [gap_chain["gap_ids"][0], orphan_gap_id],
            "channel": "test-combined",
        },
    )
    assert response.status_code == 400
