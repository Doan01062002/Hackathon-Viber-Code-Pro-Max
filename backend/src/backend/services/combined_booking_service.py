import secrets
from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.booking_service import BookingService
from backend.services.refund_policy import compute_refund
from backend.views.booking_view import BookingCreateRequest
from backend.views.combined_booking_view import (
    CombinedBookingCreateRequest,
    CombinedBookingResponse,
    CombinedCancelResponse,
    CombinedJourneyOption,
    CombinedJourneyOptionsResponse,
    CombinedRefundLeg,
)


def generate_group_code() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"CMB-{timestamp}-{secrets.token_hex(3).upper()}"


class CombinedBookingService:
    def __init__(self) -> None:
        self.booking_service = BookingService()

    def search_options(
        self,
        origin: str,
        destination: str,
        service_date: date,
        seat_type: str | None,
        max_transfers: int,
        db: Session,
    ) -> CombinedJourneyOptionsResponse:
        origin_code = origin.strip().upper()
        destination_code = destination.strip().upper()
        if origin_code == destination_code:
            raise ValueError("Ga đi và ga đến phải khác nhau")

        trip_rows = db.execute(
            text("""
                SELECT trip.id AS trip_id, train.code AS train_code, trip.service_date
                FROM trips trip
                JOIN trains train ON train.id = trip.train_id
                WHERE trip.service_date = :service_date
                  AND trip.status <> 'cancelled'
                ORDER BY train.code, trip.id
            """),
            {"service_date": service_date},
        ).mappings().all()

        options: list[CombinedJourneyOption] = []
        for trip in trip_rows:
            route = self._load_route(int(trip["trip_id"]), db)
            station_index = {station["code"]: index for index, station in enumerate(route)}
            if origin_code not in station_index or destination_code not in station_index:
                continue
            origin_index = station_index[origin_code]
            destination_index = station_index[destination_code]
            if origin_index >= destination_index:
                continue

            candidates = self._load_gap_candidates(int(trip["trip_id"]), seat_type, db)
            route_index_by_id = {int(station["id"]): index for index, station in enumerate(route)}
            edges: dict[int, list[dict[str, Any]]] = defaultdict(list)
            for candidate in candidates:
                from_index = route_index_by_id.get(int(candidate["from_station_id"]))
                to_index = route_index_by_id.get(int(candidate["to_station_id"]))
                if (
                    from_index is None
                    or to_index is None
                    or from_index < origin_index
                    or to_index > destination_index
                    or from_index >= to_index
                ):
                    continue
                edges[int(candidate["from_station_id"])].append(dict(candidate))

            for outgoing in edges.values():
                outgoing.sort(key=lambda item: (float(item["base_price"]), item["coach_no"], item["seat_no"]))
                del outgoing[12:]

            completed: list[list[dict[str, Any]]] = []
            self._walk_paths(
                current_station_id=int(route[origin_index]["id"]),
                destination_station_id=int(route[destination_index]["id"]),
                edges=edges,
                path=[],
                max_legs=max_transfers + 1,
                completed=completed,
            )

            for path in completed:
                if len(path) < 2:
                    continue
                legs = []
                seat_changes = 0
                for index, leg in enumerate(path):
                    keep_seat = index > 0 and int(path[index - 1]["seat_id"]) == int(leg["seat_id"])
                    if index > 0 and not keep_seat:
                        seat_changes += 1
                    legs.append(
                        {
                            "sequence_no": index + 1,
                            "gap_combination_id": int(leg["gap_combination_id"]),
                            "od_product_id": int(leg["od_product_id"]),
                            "origin_code": str(leg["origin_code"]),
                            "origin_name": str(leg["origin_name"]),
                            "destination_code": str(leg["destination_code"]),
                            "destination_name": str(leg["destination_name"]),
                            "departure_at": leg["departure_at"],
                            "arrival_at": leg["arrival_at"],
                            "seat_id": int(leg["seat_id"]),
                            "coach_no": str(leg["coach_no"]),
                            "seat_no": str(leg["seat_no"]),
                            "seat_type": str(leg["seat_type"]),
                            "seat_type_name": str(leg["seat_type_name"]),
                            "estimated_price": float(leg["base_price"]),
                            "keep_previous_seat": keep_seat,
                        }
                    )
                options.append(
                    CombinedJourneyOption(
                        option_key="-".join(str(leg["gap_combination_id"]) for leg in path),
                        trip_id=int(trip["trip_id"]),
                        train_code=str(trip["train_code"]),
                        service_date=trip["service_date"],
                        origin_code=origin_code,
                        origin_name=str(route[origin_index]["name"]),
                        destination_code=destination_code,
                        destination_name=str(route[destination_index]["name"]),
                        transfer_count=len(path) - 1,
                        seat_change_count=seat_changes,
                        estimated_total_price=sum(float(leg["base_price"]) for leg in path),
                        legs=legs,
                    )
                )

        options.sort(key=lambda option: (option.transfer_count, option.seat_change_count, option.estimated_total_price))
        return CombinedJourneyOptionsResponse(
            origin_code=origin_code,
            destination_code=destination_code,
            service_date=service_date,
            options=options[:10],
        )

    def create_hold(self, request: CombinedBookingCreateRequest, db: Session) -> CombinedBookingResponse:
        gap_ids = request.gap_combination_ids
        if len(set(gap_ids)) != len(gap_ids):
            raise ValueError("Các chặng ghép không được trùng nhau")

        gaps = self._lock_gaps(gap_ids, db)
        self._validate_gap_chain(gaps)

        group_code = generate_group_code()
        first = gaps[0]
        last = gaps[-1]
        group_row = db.execute(
            text("""
                INSERT INTO booking_groups (
                    group_code, trip_id, origin_station_id, destination_station_id,
                    status, channel, total_price, transfer_count, booked_at
                ) VALUES (
                    :group_code, :trip_id, :origin_station_id, :destination_station_id,
                    'held', :channel, 0, :transfer_count, CURRENT_TIMESTAMP
                )
                RETURNING id
            """),
            {
                "group_code": group_code,
                "trip_id": first["trip_id"],
                "origin_station_id": first["origin_station_id"],
                "destination_station_id": last["destination_station_id"],
                "channel": request.channel or "web",
                "transfer_count": len(gaps) - 1,
            },
        ).mappings().one()
        group_id = int(group_row["id"])

        for index, gap in enumerate(gaps, start=1):
            hold = self.booking_service.create_booking_hold(
                BookingCreateRequest(
                    od_product_id=int(gap["od_product_id"]),
                    seat_id=int(gap["seat_id"]),
                    channel=request.channel or "web",
                ),
                db,
            )
            db.execute(
                text("""
                    INSERT INTO booking_group_items (
                        booking_group_id, booking_id, gap_combination_id, sequence_no
                    )
                    VALUES (:group_id, :booking_id, :gap_combination_id, :sequence_no)
                """),
                {
                    "group_id": group_id,
                    "booking_id": hold.booking_id,
                    "gap_combination_id": gap["gap_combination_id"],
                    "sequence_no": index,
                },
            )

        totals = db.execute(
            text("""
                SELECT SUM(booking.booked_price) AS total_price,
                       MIN(booking.expires_at) AS expires_at
                FROM booking_group_items item
                JOIN bookings booking ON booking.id = item.booking_id
                WHERE item.booking_group_id = :group_id
            """),
            {"group_id": group_id},
        ).mappings().one()
        db.execute(
            text("""
                UPDATE bookings
                SET expires_at = :expires_at
                WHERE id IN (
                    SELECT booking_id
                    FROM booking_group_items
                    WHERE booking_group_id = :group_id
                )
            """),
            {"group_id": group_id, "expires_at": totals["expires_at"]},
        )
        db.execute(
            text("""
                UPDATE booking_groups
                SET total_price = :total_price, expires_at = :expires_at
                WHERE id = :group_id
            """),
            {"group_id": group_id, "total_price": totals["total_price"], "expires_at": totals["expires_at"]},
        )
        db.execute(
            text("UPDATE gap_combinations SET is_active = FALSE WHERE id = ANY(:gap_ids)"),
            {"gap_ids": gap_ids},
        )
        return self.get_detail(group_code, db)

    def confirm(self, group_code: str, db: Session) -> CombinedBookingResponse:
        group = db.execute(
            text("""
                SELECT id, status, expires_at
                FROM booking_groups
                WHERE UPPER(group_code) = UPPER(:group_code)
                FOR UPDATE
            """),
            {"group_code": group_code.strip()},
        ).mappings().first()
        if not group:
            raise ValueError(f"Không tìm thấy nhóm vé {group_code}")
        if group["status"] != "held":
            raise ValueError(f"Nhóm vé không ở trạng thái giữ chỗ (đang là '{group['status']}')")
        if group["expires_at"] and datetime.now(UTC) > group["expires_at"]:
            raise ValueError("Giữ chỗ của nhóm vé đã hết hạn")

        booking_ids = db.execute(
            text("""
                SELECT booking_id
                FROM booking_group_items
                WHERE booking_group_id = :group_id
                ORDER BY sequence_no
            """),
            {"group_id": group["id"]},
        ).scalars().all()
        for booking_id in booking_ids:
            self.booking_service.confirm_booking(int(booking_id), db, allow_group=True)

        db.execute(
            text("UPDATE booking_groups SET status = 'confirmed', expires_at = NULL WHERE id = :group_id"),
            {"group_id": group["id"]},
        )
        return self.get_detail(group_code, db)

    def _load_group_for_update(self, group_code: str, db: Session) -> dict[str, Any]:
        group = db.execute(
            text("""
                SELECT id, group_code, status
                FROM booking_groups
                WHERE UPPER(group_code) = UPPER(:group_code)
                FOR UPDATE
            """),
            {"group_code": group_code.strip()},
        ).mappings().first()
        if not group:
            raise ValueError(f"Không tìm thấy nhóm vé {group_code}")
        return dict(group)

    def _load_cancellable_legs(
        self, group_id: int, db: Session, sequence_no: int | None = None
    ) -> list[dict[str, Any]]:
        """Các chặng còn hiệu lực của nhóm, kèm giờ khởi hành để tính bậc hoàn tiền."""
        return [
            dict(row)
            for row in db.execute(
                text("""
                    SELECT
                        item.sequence_no, item.gap_combination_id,
                        booking.id AS booking_id, booking.booking_code,
                        booking.od_product_id, booking.booked_price, booking.status,
                        (SELECT MIN(segment.departure_at)
                         FROM od_product_segments mapping
                         JOIN segments segment ON segment.id = mapping.segment_id
                         WHERE mapping.od_product_id = booking.od_product_id) AS departure_at
                    FROM booking_group_items item
                    JOIN bookings booking ON booking.id = item.booking_id
                    WHERE item.booking_group_id = :group_id
                      AND booking.status IN ('held', 'confirmed')
                      AND (
                          CAST(:sequence_no AS INTEGER) IS NULL
                          OR item.sequence_no = CAST(:sequence_no AS INTEGER)
                      )
                    ORDER BY item.sequence_no
                """),
                {"group_id": group_id, "sequence_no": sequence_no},
            ).mappings()
        ]

    @staticmethod
    def _release_leg(leg: dict[str, Any], db: Session) -> None:
        """Hủy một chặng: đổi trạng thái vé, cộng lại tồn kho, bật lại gap."""
        db.execute(
            text("UPDATE bookings SET status = 'cancelled' WHERE id = :booking_id"),
            {"booking_id": leg["booking_id"]},
        )
        # Cộng lại tồn kho cho mọi chặng mà sản phẩm OD này đi qua.
        db.execute(
            text("""
                UPDATE segment_inventory inventory
                SET remaining = inventory.remaining + 1
                FROM od_product_segments mapping
                JOIN od_products product ON product.id = mapping.od_product_id
                WHERE mapping.od_product_id = :od_product_id
                  AND inventory.segment_id = mapping.segment_id
                  AND inventory.seat_type = product.seat_type
            """),
            {"od_product_id": leg["od_product_id"]},
        )
        # Trả đoạn trống về kho để thuật toán ghép chặng dùng lại được.
        db.execute(
            text("UPDATE gap_combinations SET is_active = TRUE WHERE id = :gap_id"),
            {"gap_id": leg["gap_combination_id"]},
        )

    def cancel_group(
        self,
        group_code: str,
        db: Session,
        sequence_no: int | None = None,
        now: datetime | None = None,
    ) -> CombinedCancelResponse:
        """Hủy cả nhóm vé, hoặc một chặng khi truyền `sequence_no`.

        Tiền hoàn tính theo `refund_policy` dựa trên giờ khởi hành của TỪNG chặng —
        chặng cuối của hành trình dài có thể còn xa giờ chạy trong khi chặng đầu đã
        gần, nên áp một bậc chung cho cả nhóm sẽ tính sai.
        """
        moment = now or datetime.now(UTC)
        group = self._load_group_for_update(group_code, db)

        if group["status"] in {"cancelled", "refunded"}:
            raise ValueError(f"Nhóm vé đã ở trạng thái '{group['status']}'")

        legs = self._load_cancellable_legs(int(group["id"]), db, sequence_no)
        if not legs:
            if sequence_no is not None:
                raise ValueError(f"Chặng {sequence_no} không tồn tại hoặc đã bị hủy")
            raise ValueError("Nhóm vé không còn chặng nào để hủy")

        # Vé mới giữ chỗ thì chưa thu tiền, nên không phát sinh hoàn.
        is_paid = group["status"] == "confirmed"

        refunds: list[CombinedRefundLeg] = []
        total_refund = Decimal("0")
        total_fee = Decimal("0")
        for leg in legs:
            outcome = compute_refund(
                Decimal(str(leg["booked_price"])),
                leg["departure_at"],
                moment,
                is_paid=is_paid,
            )
            self._release_leg(leg, db)
            total_refund += outcome.refund_amount
            total_fee += outcome.fee_amount
            refunds.append(
                CombinedRefundLeg(
                    sequence_no=int(leg["sequence_no"]),
                    booking_code=leg["booking_code"],
                    booked_price=float(leg["booked_price"]),
                    refund_amount=float(outcome.refund_amount),
                    fee_amount=float(outcome.fee_amount),
                    tier_code=outcome.tier_code,
                    tier_label=outcome.label,
                )
            )

        # Nhóm chỉ đóng lại khi không còn chặng nào hiệu lực — hủy lẻ một chặng
        # thì phần còn lại của hành trình vẫn dùng được.
        remaining = self._load_cancellable_legs(int(group["id"]), db)
        if remaining:
            group_status = group["status"]
        else:
            group_status = "refunded" if total_refund > 0 else "cancelled"
            db.execute(
                text("UPDATE booking_groups SET status = :status, expires_at = NULL WHERE id = :group_id"),
                {"status": group_status, "group_id": group["id"]},
            )

        return CombinedCancelResponse(
            group_code=group["group_code"],
            status=group_status,
            cancelled_legs=len(refunds),
            total_refund=float(total_refund),
            total_fee=float(total_fee),
            legs=refunds,
        )

    def get_detail(self, group_code: str, db: Session) -> CombinedBookingResponse:
        group = db.execute(
            text("""
                SELECT
                    booking_group.id AS booking_group_id, booking_group.group_code,
                    booking_group.status, booking_group.channel, booking_group.trip_id,
                    train.code AS train_code, trip.service_date,
                    origin.code AS origin_code, origin.name AS origin_name,
                    destination.code AS destination_code, destination.name AS destination_name,
                    booking_group.transfer_count, booking_group.total_price,
                    booking_group.booked_at, booking_group.expires_at
                FROM booking_groups booking_group
                JOIN trips trip ON trip.id = booking_group.trip_id
                JOIN trains train ON train.id = trip.train_id
                JOIN stations origin ON origin.id = booking_group.origin_station_id
                JOIN stations destination ON destination.id = booking_group.destination_station_id
                WHERE UPPER(booking_group.group_code) = UPPER(:group_code)
            """),
            {"group_code": group_code.strip()},
        ).mappings().first()
        if not group:
            raise ValueError(f"Không tìm thấy nhóm vé {group_code}")

        leg_rows = db.execute(
            text("""
                SELECT
                    item.sequence_no, item.gap_combination_id,
                    booking.id AS booking_id, booking.booking_code,
                    booking.od_product_id, booking.status,
                    origin.code AS origin_code, origin.name AS origin_name,
                    destination.code AS destination_code, destination.name AS destination_name,
                    (SELECT MIN(segment.departure_at)
                     FROM od_product_segments mapping
                     JOIN segments segment ON segment.id = mapping.segment_id
                     WHERE mapping.od_product_id = product.id) AS departure_at,
                    (SELECT MAX(segment.arrival_at)
                     FROM od_product_segments mapping
                     JOIN segments segment ON segment.id = mapping.segment_id
                     WHERE mapping.od_product_id = product.id) AS arrival_at,
                    seat.id AS seat_id, seat.coach_no, seat.seat_no,
                    product.seat_type, seat_type.name AS seat_type_name,
                    booking.booked_price
                FROM booking_group_items item
                JOIN bookings booking ON booking.id = item.booking_id
                JOIN od_products product ON product.id = booking.od_product_id
                JOIN stations origin ON origin.id = product.origin_station_id
                JOIN stations destination ON destination.id = product.destination_station_id
                JOIN seat_types seat_type ON seat_type.code = product.seat_type
                JOIN seats seat ON seat.id = booking.seat_id
                WHERE item.booking_group_id = :group_id
                ORDER BY item.sequence_no
            """),
            {"group_id": group["booking_group_id"]},
        ).mappings().all()
        legs = []
        previous_seat_id: int | None = None
        for leg in leg_rows:
            leg_data = dict(leg)
            seat_id = int(leg_data["seat_id"])
            leg_data["keep_previous_seat"] = previous_seat_id == seat_id
            previous_seat_id = seat_id
            legs.append(leg_data)
        return CombinedBookingResponse(**group, legs=legs)

    @staticmethod
    def _walk_paths(
        current_station_id: int,
        destination_station_id: int,
        edges: dict[int, list[dict[str, Any]]],
        path: list[dict[str, Any]],
        max_legs: int,
        completed: list[list[dict[str, Any]]],
    ) -> None:
        if len(completed) >= 50:
            return
        if current_station_id == destination_station_id:
            completed.append(path.copy())
            return
        if len(path) >= max_legs:
            return
        for edge in edges.get(current_station_id, []):
            next_station_id = int(edge["to_station_id"])
            if any(int(item["from_station_id"]) == next_station_id for item in path):
                continue
            CombinedBookingService._walk_paths(
                next_station_id,
                destination_station_id,
                edges,
                [*path, edge],
                max_legs,
                completed,
            )

    @staticmethod
    def _load_route(trip_id: int, db: Session) -> list[dict[str, Any]]:
        rows = db.execute(
            text("""
                SELECT
                    segment.sequence_no,
                    origin.id AS origin_id, origin.code AS origin_code, origin.name AS origin_name,
                    destination.id AS destination_id, destination.code AS destination_code,
                    destination.name AS destination_name
                FROM segments segment
                JOIN stations origin ON origin.id = segment.origin_station_id
                JOIN stations destination ON destination.id = segment.destination_station_id
                WHERE segment.trip_id = :trip_id
                ORDER BY segment.sequence_no
            """),
            {"trip_id": trip_id},
        ).mappings().all()
        if not rows:
            return []
        route = [{"id": rows[0]["origin_id"], "code": rows[0]["origin_code"], "name": rows[0]["origin_name"]}]
        route.extend(
            {"id": row["destination_id"], "code": row["destination_code"], "name": row["destination_name"]}
            for row in rows
        )
        return route

    @staticmethod
    def _load_gap_candidates(trip_id: int, seat_type: str | None, db: Session) -> list[Any]:
        return db.execute(
            text("""
                SELECT
                    gap.id AS gap_combination_id, gap.from_station_id, gap.to_station_id,
                    product.id AS od_product_id, product.base_price,
                    origin.code AS origin_code, origin.name AS origin_name,
                    destination.code AS destination_code, destination.name AS destination_name,
                    (SELECT MIN(segment.departure_at)
                     FROM od_product_segments mapping
                     JOIN segments segment ON segment.id = mapping.segment_id
                     WHERE mapping.od_product_id = product.id) AS departure_at,
                    (SELECT MAX(segment.arrival_at)
                     FROM od_product_segments mapping
                     JOIN segments segment ON segment.id = mapping.segment_id
                     WHERE mapping.od_product_id = product.id) AS arrival_at,
                    seat.id AS seat_id, seat.coach_no, seat.seat_no,
                    product.seat_type, seat_type.name AS seat_type_name
                FROM gap_combinations gap
                JOIN od_products product ON product.id = gap.suggested_od_product_id
                JOIN seats seat ON seat.id = gap.seat_id
                JOIN stations origin ON origin.id = gap.from_station_id
                JOIN stations destination ON destination.id = gap.to_station_id
                JOIN seat_types seat_type ON seat_type.code = product.seat_type
                WHERE seat.trip_id = :trip_id
                  AND product.trip_id = :trip_id
                  AND gap.from_station_id = product.origin_station_id
                  AND gap.to_station_id = product.destination_station_id
                  AND gap.is_active = TRUE
                  AND product.is_active = TRUE
                  AND seat.status = 'available'
                  AND (
                      CAST(:seat_type AS VARCHAR) IS NULL
                      OR product.seat_type = CAST(:seat_type AS VARCHAR)
                  )
                  AND NOT EXISTS (
                      SELECT 1
                      FROM bookings booking
                      JOIN od_product_segments booked_mapping
                        ON booked_mapping.od_product_id = booking.od_product_id
                      JOIN od_product_segments candidate_mapping
                        ON candidate_mapping.segment_id = booked_mapping.segment_id
                       AND candidate_mapping.od_product_id = product.id
                      WHERE booking.seat_id = seat.id
                        AND booking.status IN ('held', 'confirmed')
                        AND (booking.status = 'confirmed' OR booking.expires_at > CURRENT_TIMESTAMP)
                  )
                  AND NOT EXISTS (
                      SELECT 1
                      FROM od_product_segments mapping
                      JOIN segment_inventory inventory
                        ON inventory.segment_id = mapping.segment_id
                       AND inventory.seat_type = product.seat_type
                      WHERE mapping.od_product_id = product.id
                        AND inventory.remaining <= 0
                  )
                  -- Loại sản phẩm đã hết hạn ngạch. Phải soi cùng một luật với
                  -- BookingService.create_hold, nếu không tìm kiếm sẽ chào những
                  -- phương án mà giữ chỗ chắc chắn từ chối bằng lỗi 400.
                  -- Không có dòng quota nào = không giới hạn, giống create_hold.
                  AND NOT EXISTS (
                      SELECT 1
                      FROM (
                          SELECT quota
                          FROM quotas
                          WHERE od_product_id = product.id AND is_active = TRUE
                          ORDER BY calculated_at DESC, id DESC
                          LIMIT 1
                      ) active_quota
                      WHERE (
                          SELECT COUNT(*)
                          FROM bookings
                          WHERE od_product_id = product.id
                            AND status IN ('held', 'confirmed')
                      ) >= active_quota.quota
                  )
                ORDER BY product.base_price, gap.id
            """),
            {"trip_id": trip_id, "seat_type": seat_type.strip() if seat_type else None},
        ).mappings().all()

    @staticmethod
    def _lock_gaps(gap_ids: list[int], db: Session) -> list[dict[str, Any]]:
        rows_by_id: dict[int, dict[str, Any]] = {}
        for gap_id in sorted(gap_ids):
            row = db.execute(
                text("""
                    SELECT
                        gap.id AS gap_combination_id, gap.is_active,
                        gap.from_station_id AS origin_station_id,
                        gap.to_station_id AS destination_station_id,
                        product.id AS od_product_id, product.trip_id, product.is_active AS product_is_active,
                        seat.id AS seat_id, seat.trip_id AS seat_trip_id, seat.status AS seat_status
                    FROM gap_combinations gap
                    JOIN od_products product ON product.id = gap.suggested_od_product_id
                    JOIN seats seat ON seat.id = gap.seat_id
                    WHERE gap.id = :gap_id
                    FOR UPDATE OF gap, seat
                """),
                {"gap_id": gap_id},
            ).mappings().first()
            if not row:
                raise ValueError(f"Không tìm thấy phương án gap {gap_id}")
            rows_by_id[gap_id] = dict(row)
        return [rows_by_id[gap_id] for gap_id in gap_ids]

    @staticmethod
    def _validate_gap_chain(gaps: list[dict[str, Any]]) -> None:
        trip_id = int(gaps[0]["trip_id"])
        for index, gap in enumerate(gaps):
            if not gap["is_active"]:
                raise ValueError(f"Phương án gap {gap['gap_combination_id']} không còn hiệu lực")
            if not gap["product_is_active"]:
                raise ValueError("Một sản phẩm chặng trong phương án đã ngừng bán")
            if int(gap["seat_trip_id"]) != trip_id or int(gap["trip_id"]) != trip_id:
                raise ValueError("Các chặng ghép phải thuộc cùng một chuyến tàu")
            if gap["seat_status"] != "available":
                raise ValueError("Một chỗ trong phương án đang bị khóa hoặc bảo trì")
            if index > 0 and int(gaps[index - 1]["destination_station_id"]) != int(gap["origin_station_id"]):
                raise ValueError("Các chặng ghép phải liên tục và đúng thứ tự ga")
