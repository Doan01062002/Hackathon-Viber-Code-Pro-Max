from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from backend.database import get_session_factory


def _create_gap_fixture() -> tuple[list[int], datetime]:
    db = get_session_factory()()
    started_at = datetime.now(UTC)
    try:
        seat_id = db.execute(
            text("""
                SELECT id
                FROM seats
                WHERE trip_id = 1
                  AND coach_no = '01'
                  AND seat_type = 'ngoi_mem'
                ORDER BY id
                OFFSET 1 LIMIT 1
            """)
        ).scalar_one()
        gap_ids = db.execute(
            text("""
                INSERT INTO gap_combinations (
                    seat_id, from_station_id, to_station_id,
                    suggested_od_product_id, run_version, is_active
                )
                VALUES
                    (:seat_id, 1, 2, 1, :run_version, TRUE),
                    (:seat_id, 2, 10, 3, :run_version, TRUE)
                RETURNING id
            """),
            {"seat_id": seat_id, "run_version": f"combined-test-{started_at.timestamp()}"},
        ).scalars().all()
        db.commit()
        return [int(gap_id) for gap_id in gap_ids], started_at
    finally:
        db.close()


def _cleanup_combined_booking(gap_ids: list[int], group_code: str | None, started_at: datetime) -> None:
    db = get_session_factory()()
    try:
        if group_code:
            booking_rows = db.execute(
                text("""
                    SELECT booking.id, booking.od_product_id, booking.status, product.seat_type
                    FROM booking_groups booking_group
                    JOIN booking_group_items item ON item.booking_group_id = booking_group.id
                    JOIN bookings booking ON booking.id = item.booking_id
                    JOIN od_products product ON product.id = booking.od_product_id
                    WHERE booking_group.group_code = :group_code
                """),
                {"group_code": group_code},
            ).mappings().all()
            for booking in booking_rows:
                if booking["status"] not in {"held", "confirmed"}:
                    continue
                db.execute(
                    text("""
                        UPDATE segment_inventory inventory
                        SET remaining = remaining + 1
                        FROM od_product_segments mapping
                        WHERE mapping.od_product_id = :od_product_id
                          AND inventory.segment_id = mapping.segment_id
                          AND inventory.seat_type = :seat_type
                    """),
                    {
                        "od_product_id": booking["od_product_id"],
                        "seat_type": booking["seat_type"],
                    },
                )
            db.execute(
                text("""
                    DELETE FROM bookings
                    WHERE id IN (
                        SELECT item.booking_id
                        FROM booking_group_items item
                        JOIN booking_groups booking_group ON booking_group.id = item.booking_group_id
                        WHERE booking_group.group_code = :group_code
                    )
                """),
                {"group_code": group_code},
            )
            db.execute(
                text("DELETE FROM booking_groups WHERE group_code = :group_code"),
                {"group_code": group_code},
            )
        db.execute(text("DELETE FROM gap_combinations WHERE id = ANY(:gap_ids)"), {"gap_ids": gap_ids})
        db.execute(
            text("""
                DELETE FROM price_quotes
                WHERE od_product_id IN (1, 3)
                  AND created_at >= :started_at
            """),
            {"started_at": started_at},
        )
        db.commit()
    finally:
        db.close()


@pytest.mark.asyncio
async def test_combined_booking_search_hold_detail_and_confirm(client):
    gap_ids, started_at = _create_gap_fixture()
    group_code = None
    try:
        search_response = await client.get(
            "/api/v1/booking/combined-options",
            params={
                "origin": "HAN",
                "destination": "DAN",
                "service_date": "2024-01-01",
                "seat_type": "ngoi_mem",
            },
        )
        assert search_response.status_code == 200, search_response.text
        options = search_response.json()["options"]
        option = next(item for item in options if item["option_key"] == "-".join(map(str, gap_ids)))
        assert option["transfer_count"] == 1
        assert option["seat_change_count"] == 0
        assert [leg["origin_code"] for leg in option["legs"]] == ["HAN", "PHL"]
        assert [leg["destination_code"] for leg in option["legs"]] == ["PHL", "DAN"]

        create_response = await client.post(
            "/api/v1/booking/combined",
            json={"gap_combination_ids": gap_ids, "channel": "web"},
        )
        assert create_response.status_code == 201, create_response.text
        combined = create_response.json()
        group_code = combined["group_code"]
        assert group_code.startswith("CMB-")
        assert combined["status"] == "held"
        assert len(combined["legs"]) == 2
        assert all(leg["status"] == "held" for leg in combined["legs"])

        child_confirm_response = await client.post(
            f"/api/v1/booking/{combined['legs'][0]['booking_id']}/confirm"
        )
        assert child_confirm_response.status_code == 400
        assert group_code in child_confirm_response.json()["detail"]

        confirm_response = await client.post(f"/api/v1/booking/combined/{group_code}/confirm")
        assert confirm_response.status_code == 200, confirm_response.text
        confirmed = confirm_response.json()
        assert confirmed["status"] == "confirmed"
        assert confirmed["expires_at"] is None
        assert all(leg["status"] == "confirmed" for leg in confirmed["legs"])

        detail_response = await client.get(f"/api/v1/booking/combined/{group_code}")
        assert detail_response.status_code == 200
        assert detail_response.json() == confirmed
    finally:
        _cleanup_combined_booking(gap_ids, group_code, started_at)


@pytest.mark.asyncio
async def test_combined_booking_rejects_non_contiguous_legs(client):
    gap_ids, started_at = _create_gap_fixture()
    try:
        response = await client.post(
            "/api/v1/booking/combined",
            json={"gap_combination_ids": list(reversed(gap_ids))},
        )
        assert response.status_code == 400
    finally:
        _cleanup_combined_booking(gap_ids, None, started_at)


@pytest.mark.asyncio
async def test_expired_combined_booking_releases_inventory_and_gap_options(client):
    gap_ids, started_at = _create_gap_fixture()
    group_code = None
    try:
        create_response = await client.post(
            "/api/v1/booking/combined",
            json={"gap_combination_ids": gap_ids},
        )
        assert create_response.status_code == 201, create_response.text
        group_code = create_response.json()["group_code"]

        db = get_session_factory()()
        try:
            db.execute(
                text("""
                    UPDATE bookings booking
                    SET booked_at = CURRENT_TIMESTAMP - INTERVAL '2 hours',
                        expires_at = CURRENT_TIMESTAMP - INTERVAL '1 hour'
                    FROM booking_group_items item
                    JOIN booking_groups booking_group ON booking_group.id = item.booking_group_id
                    WHERE item.booking_id = booking.id
                      AND booking_group.group_code = :group_code
                """),
                {"group_code": group_code},
            )
            db.execute(
                text("""
                    UPDATE booking_groups
                    SET booked_at = CURRENT_TIMESTAMP - INTERVAL '2 hours',
                        expires_at = CURRENT_TIMESTAMP - INTERVAL '1 hour'
                    WHERE group_code = :group_code
                """),
                {"group_code": group_code},
            )
            db.commit()
        finally:
            db.close()

        release_response = await client.post("/api/v1/booking/release-expired")
        assert release_response.status_code == 200
        assert release_response.json()["released_count"] == 2

        detail_response = await client.get(f"/api/v1/booking/combined/{group_code}")
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["status"] == "cancelled"
        assert all(leg["status"] == "cancelled" for leg in detail["legs"])

        db = get_session_factory()()
        try:
            active_gap_count = db.execute(
                text("SELECT COUNT(*) FROM gap_combinations WHERE id = ANY(:gap_ids) AND is_active = TRUE"),
                {"gap_ids": gap_ids},
            ).scalar_one()
            assert active_gap_count == 2
        finally:
            db.close()
    finally:
        _cleanup_combined_booking(gap_ids, group_code, started_at)
