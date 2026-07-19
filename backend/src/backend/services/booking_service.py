import random
import string
from datetime import UTC, date, datetime

UTC = UTC

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.views.booking_view import (
    BookingCoachItem,
    BookingConfirmResponse,
    BookingCreateRequest,
    BookingDestinationOption,
    BookingDetailResponse,
    BookingOptionsResponse,
    BookingResponse,
    BookingSearchItem,
    BookingSeatItem,
    BookingSeatPlanResponse,
    BookingSegmentItem,
)


def generate_booking_code() -> str:
    return "BK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


class BookingService:
    def get_booking_options(
        self, origin: str, destination: str | None, db: Session
    ) -> BookingOptionsResponse:
        origin_value = origin.strip()
        destination_rows = db.execute(
            text("""
                SELECT DISTINCT destination.code, destination.name, destination.display_order
                FROM od_products product
                JOIN stations origin ON origin.id = product.origin_station_id
                JOIN stations destination ON destination.id = product.destination_station_id
                WHERE product.is_active = TRUE
                  AND (LOWER(origin.code) = LOWER(:origin) OR LOWER(origin.name) = LOWER(:origin))
                ORDER BY destination.display_order NULLS LAST, destination.name
            """),
            {"origin": origin_value},
        ).all()

        departure_dates: list[date] = []
        return_dates: list[date] = []
        if destination:
            destination_value = destination.strip()
            departure_dates = list(
                db.execute(
                    text("""
                        SELECT DISTINCT trip.service_date
                        FROM od_products product
                        JOIN trips trip ON trip.id = product.trip_id
                        JOIN stations origin ON origin.id = product.origin_station_id
                        JOIN stations destination ON destination.id = product.destination_station_id
                        WHERE product.is_active = TRUE
                          AND trip.status <> 'cancelled'
                          AND (LOWER(origin.code) = LOWER(:origin) OR LOWER(origin.name) = LOWER(:origin))
                          AND (
                            LOWER(destination.code) = LOWER(:destination)
                            OR LOWER(destination.name) = LOWER(:destination)
                          )
                        ORDER BY trip.service_date
                    """),
                    {"origin": origin_value, "destination": destination_value},
                ).scalars().all()
            )
            return_dates = list(
                db.execute(
                    text("""
                        SELECT DISTINCT trip.service_date
                        FROM od_products product
                        JOIN trips trip ON trip.id = product.trip_id
                        JOIN stations origin ON origin.id = product.origin_station_id
                        JOIN stations destination ON destination.id = product.destination_station_id
                        WHERE product.is_active = TRUE
                          AND trip.status <> 'cancelled'
                          AND (LOWER(origin.code) = LOWER(:destination) OR LOWER(origin.name) = LOWER(:destination))
                          AND (
                            LOWER(destination.code) = LOWER(:origin)
                            OR LOWER(destination.name) = LOWER(:origin)
                          )
                        ORDER BY trip.service_date
                    """),
                    {"origin": origin_value, "destination": destination_value},
                ).scalars().all()
            )

        return BookingOptionsResponse(
            destinations=[
                BookingDestinationOption(code=str(row[0]), name=str(row[1]))
                for row in destination_rows
            ],
            departure_dates=departure_dates,
            return_dates=return_dates,
        )

    def search_products(
        self,
        origin: str,
        destination: str,
        service_date: date,
        seat_type: str | None,
        db: Session,
    ) -> list[BookingSearchItem]:
        if origin.strip().lower() == destination.strip().lower():
            raise ValueError("Ga di va ga den khong duoc trung nhau")

        rows = db.execute(
            text("""
                SELECT
                    od.id AS od_product_id,
                    od.trip_id,
                    train.code AS train_code,
                    origin.code AS origin_code,
                    origin.name AS origin_name,
                    destination.code AS destination_code,
                    destination.name AS destination_name,
                    trip.service_date,
                    MIN(segment.departure_at) AS departure_at,
                    MAX(segment.arrival_at) AS arrival_at,
                    od.seat_type,
                    seat_type_ref.name AS seat_type_name,
                    od.base_price,
                    COALESCE(MIN(inventory.remaining), 0) AS availability
                FROM od_products od
                JOIN trips trip ON trip.id = od.trip_id
                JOIN trains train ON train.id = trip.train_id
                JOIN stations origin ON origin.id = od.origin_station_id
                JOIN stations destination ON destination.id = od.destination_station_id
                JOIN seat_types seat_type_ref ON seat_type_ref.code = od.seat_type
                JOIN od_product_segments mapping ON mapping.od_product_id = od.id
                JOIN segments segment ON segment.id = mapping.segment_id
                LEFT JOIN segment_inventory inventory
                  ON inventory.segment_id = segment.id
                 AND inventory.seat_type = od.seat_type
                WHERE trip.service_date = :service_date
                  AND trip.status <> 'cancelled'
                  AND od.is_active = TRUE
                  AND (LOWER(origin.code) = LOWER(:origin) OR LOWER(origin.name) = LOWER(:origin))
                  AND (
                    LOWER(destination.code) = LOWER(:destination)
                    OR LOWER(destination.name) = LOWER(:destination)
                  )
                  AND (CAST(:seat_type AS VARCHAR) IS NULL OR od.seat_type = :seat_type)
                GROUP BY
                    od.id, od.trip_id, train.code, origin.code, origin.name,
                    destination.code, destination.name, trip.service_date,
                    od.seat_type, seat_type_ref.name, od.base_price
                ORDER BY departure_at, od.seat_type
            """),
            {
                "origin": origin.strip(),
                "destination": destination.strip(),
                "service_date": service_date,
                "seat_type": seat_type.strip() if seat_type else None,
            },
        ).mappings().all()
        return [BookingSearchItem(**row) for row in rows]

    def get_seat_plan(self, od_product_id: int, db: Session) -> BookingSeatPlanResponse:
        product = db.execute(
            text("""
                SELECT
                    od.id AS od_product_id, od.trip_id, train.code AS train_code,
                    origin.code AS origin_code, origin.name AS origin_name,
                    destination.code AS destination_code, destination.name AS destination_name,
                    trip.service_date, od.seat_type
                FROM od_products od
                JOIN trips trip ON trip.id = od.trip_id
                JOIN trains train ON train.id = trip.train_id
                JOIN stations origin ON origin.id = od.origin_station_id
                JOIN stations destination ON destination.id = od.destination_station_id
                WHERE od.id = :od_product_id AND od.is_active = TRUE
            """),
            {"od_product_id": od_product_id},
        ).mappings().first()
        if not product:
            raise ValueError(f"Khong tim thay san pham OD {od_product_id}")

        seat_rows = db.execute(
            text("""
                SELECT id AS seat_id, coach_no, seat_no, seat_type, status
                FROM seats
                WHERE trip_id = :trip_id AND seat_type = :seat_type
                ORDER BY coach_no, seat_no
            """),
            {"trip_id": product["trip_id"], "seat_type": product["seat_type"]},
        ).mappings().all()

        occupied_rows = db.execute(
            text("""
                SELECT DISTINCT booking.seat_id, booking.status
                FROM bookings booking
                JOIN od_product_segments booked_mapping
                  ON booked_mapping.od_product_id = booking.od_product_id
                JOIN od_product_segments requested_mapping
                  ON requested_mapping.segment_id = booked_mapping.segment_id
                 AND requested_mapping.od_product_id = :od_product_id
                WHERE booking.seat_id IS NOT NULL
                  AND booking.status IN ('held', 'confirmed')
                  AND (booking.status = 'confirmed' OR booking.expires_at > CURRENT_TIMESTAMP)
            """),
            {"od_product_id": od_product_id},
        ).mappings().all()
        occupied: dict[int, str] = {}
        for row in occupied_rows:
            seat_id = int(row["seat_id"])
            if row["status"] == "confirmed" or seat_id not in occupied:
                occupied[seat_id] = str(row["status"])

        grouped: dict[str, list[BookingSeatItem]] = {}
        for row in seat_rows:
            status = "blocked" if row["status"] != "available" else occupied.get(int(row["seat_id"]), "available")
            grouped.setdefault(str(row["coach_no"]), []).append(
                BookingSeatItem(seat_id=int(row["seat_id"]), seat_no=str(row["seat_no"]), status=status)
            )

        coaches = [
            BookingCoachItem(
                coach_no=coach_no,
                seat_type=str(product["seat_type"]),
                total_seats=len(seats),
                available_seats=sum(seat.status == "available" for seat in seats),
                seats=seats,
            )
            for coach_no, seats in grouped.items()
        ]
        segment_rows = db.execute(
            text("""
                SELECT
                    segment.id AS segment_id,
                    segment.sequence_no,
                    origin.code AS origin_code,
                    origin.name AS origin_name,
                    destination.code AS destination_code,
                    destination.name AS destination_name,
                    segment.departure_at,
                    segment.arrival_at,
                    segment.distance_km,
                    capacity.capacity,
                    inventory.remaining,
                    ROUND(
                        (capacity.capacity - inventory.remaining) * 100.0
                        / NULLIF(capacity.capacity, 0),
                        1
                    ) AS load_pct
                FROM segments segment
                JOIN stations origin ON origin.id = segment.origin_station_id
                JOIN stations destination ON destination.id = segment.destination_station_id
                JOIN segment_capacities capacity
                  ON capacity.segment_id = segment.id
                 AND capacity.seat_type = :seat_type
                JOIN segment_inventory inventory
                  ON inventory.segment_id = segment.id
                 AND inventory.seat_type = :seat_type
                WHERE segment.trip_id = :trip_id
                ORDER BY segment.sequence_no
            """),
            {"trip_id": product["trip_id"], "seat_type": product["seat_type"]},
        ).mappings().all()
        segments = [BookingSegmentItem(**row) for row in segment_rows]
        return BookingSeatPlanResponse(**product, coaches=coaches, segments=segments)

    def get_booking_detail(self, booking_code: str, db: Session) -> BookingDetailResponse:
        row = db.execute(
            text("""
                SELECT
                    booking.id AS booking_id, booking.booking_code, booking.status,
                    booking.booked_price, booking.booked_at, booking.expires_at,
                    od.trip_id, train.code AS train_code, trip.service_date,
                    (SELECT MIN(segment.departure_at)
                     FROM od_product_segments mapping
                     JOIN segments segment ON segment.id = mapping.segment_id
                     WHERE mapping.od_product_id = od.id) AS departure_at,
                    (SELECT MAX(segment.arrival_at)
                     FROM od_product_segments mapping
                     JOIN segments segment ON segment.id = mapping.segment_id
                     WHERE mapping.od_product_id = od.id) AS arrival_at,
                    origin.code AS origin_code, origin.name AS origin_name,
                    destination.code AS destination_code, destination.name AS destination_name,
                    od.seat_type, seat.coach_no, seat.seat_no
                FROM bookings booking
                JOIN od_products od ON od.id = booking.od_product_id
                JOIN trips trip ON trip.id = od.trip_id
                JOIN trains train ON train.id = trip.train_id
                JOIN stations origin ON origin.id = od.origin_station_id
                JOIN stations destination ON destination.id = od.destination_station_id
                LEFT JOIN seats seat ON seat.id = booking.seat_id
                WHERE UPPER(booking.booking_code) = UPPER(:booking_code)
            """),
            {"booking_code": booking_code.strip()},
        ).mappings().first()
        if not row:
            raise ValueError(f"Khong tim thay booking {booking_code}")
        return BookingDetailResponse(**row)

    @staticmethod
    def _lock_requested_seat(
        seat_id: int, trip_id: int, seat_type: str, od_product_id: int, db: Session
    ) -> int:
        seat = db.execute(
            text("""
                SELECT id, trip_id, seat_type, status
                FROM seats
                WHERE id = :seat_id
                FOR UPDATE
            """),
            {"seat_id": seat_id},
        ).mappings().first()
        if not seat or int(seat["trip_id"]) != int(trip_id) or seat["seat_type"] != seat_type:
            raise ValueError("Ghe khong thuoc chuyen tau hoac khong dung loai cho")
        if seat["status"] != "available":
            raise ValueError("Ghe dang bi khoa hoac bao tri")

        conflict = db.execute(
            text("""
                SELECT booking.id
                FROM bookings booking
                JOIN od_product_segments booked_mapping
                  ON booked_mapping.od_product_id = booking.od_product_id
                JOIN od_product_segments requested_mapping
                  ON requested_mapping.segment_id = booked_mapping.segment_id
                 AND requested_mapping.od_product_id = :od_product_id
                WHERE booking.seat_id = :seat_id
                  AND booking.status IN ('held', 'confirmed')
                  AND (booking.status = 'confirmed' OR booking.expires_at > CURRENT_TIMESTAMP)
                LIMIT 1
            """),
            {"seat_id": seat_id, "od_product_id": od_product_id},
        ).first()
        if conflict:
            raise ValueError("Ghe da duoc giu hoac ban tren chang nay")
        return seat_id

    def create_booking_hold(self, request: BookingCreateRequest, db: Session) -> BookingResponse:
        od_product_id = request.od_product_id

        # 1. Lấy thông tin cơ bản của sản phẩm OD
        product_row = db.execute(
            text("SELECT trip_id, seat_type, base_price, is_active FROM od_products WHERE id = :od_product_id"),
            {"od_product_id": od_product_id},
        ).fetchone()

        if not product_row:
            raise ValueError(f"Không tìm thấy sản phẩm OD với ID {od_product_id}")

        trip_id, seat_type, base_price, is_active = product_row

        # 2. Kiểm tra hạn ngạch (quota) hoạt động
        # Schema chỉ ràng buộc UNIQUE (od_product_id, run_version), không chặn hai dòng cùng
        # is_active — nên phải chọn dòng mới nhất một cách tường minh. Không có ORDER BY thì
        # Postgres trả dòng tùy ý và hạn mức áp dụng sẽ khác nhau giữa các lần gọi.
        quota_row = db.execute(
            text("""
                SELECT quota FROM quotas
                WHERE od_product_id = :od_product_id AND is_active = TRUE
                ORDER BY calculated_at DESC, id DESC
                LIMIT 1
            """),
            {"od_product_id": od_product_id},
        ).fetchone()

        if quota_row:
            quota_limit = int(quota_row[0])
            # Đếm số lượng đặt vé active (held hoặc confirmed) của sản phẩm này
            booked_count_row = db.execute(
                text(
                    "SELECT COUNT(*) FROM bookings WHERE od_product_id = :od_product_id AND status IN ('held', 'confirmed')"
                ),
                {"od_product_id": od_product_id},
            ).fetchone()
            booked_count = int(booked_count_row[0]) if booked_count_row else 0

            if booked_count >= quota_limit:
                raise ValueError(
                    f"Sản phẩm OD (ID {od_product_id}) đã vượt quá hạn ngạch (quota) tối đa là {quota_limit} vé"
                )

        # 3. Lấy danh sách các chặng đi qua của sản phẩm OD
        segment_rows = db.execute(
            text("SELECT segment_id FROM od_product_segments WHERE od_product_id = :od_product_id"),
            {"od_product_id": od_product_id},
        ).fetchall()

        if not segment_rows:
            raise ValueError(f"Sản phẩm OD (ID {od_product_id}) không liên kết với bất kỳ chặng nào")

        # Sắp xếp segment_ids tăng dần để tránh Deadlock khi khóa dòng bi quan
        segment_ids = sorted([row[0] for row in segment_rows])

        # 4. Khóa dòng bi quan trên bảng segment_inventory theo thứ tự ID tăng dần
        lock_query = text("""
            SELECT segment_id, remaining FROM segment_inventory
            WHERE segment_id = ANY(:segment_ids) AND seat_type = :seat_type
            ORDER BY segment_id ASC
            FOR UPDATE
        """)
        locked_rows = db.execute(lock_query, {"segment_ids": segment_ids, "seat_type": seat_type}).mappings().all()

        # Kiểm tra tồn kho của tất cả các chặng
        if len(locked_rows) != len(segment_ids):
            raise ValueError("Không tìm thấy đủ thông tin tồn kho cho tất cả các chặng")

        for row in locked_rows:
            if row["remaining"] <= 0:
                raise ValueError(f"Chặng {row['segment_id']} đã hết chỗ trống cho loại chỗ '{seat_type}'")

        # 5. Thực hiện trừ tồn kho chặng chặng
        selected_seat_id = None
        if request.seat_id is not None:
            selected_seat_id = self._lock_requested_seat(
                seat_id=request.seat_id,
                trip_id=trip_id,
                seat_type=seat_type,
                od_product_id=od_product_id,
                db=db,
            )

        update_inventory_query = text("""
            UPDATE segment_inventory
            SET remaining = remaining - 1
            WHERE segment_id = :seg_id AND seat_type = :seat_type
        """)
        for seg_id in segment_ids:
            db.execute(update_inventory_query, {"seg_id": seg_id, "seat_type": seat_type})

        # 6. Xác định giá đặt vé (booked_price)
        booked_price = None
        if request.quote_id is not None:
            # Tra cứu báo giá đã có
            quote_row = db.execute(
                text(
                    "SELECT final_price, expires_at, decision FROM price_quotes WHERE id = :quote_id AND od_product_id = :od_product_id"
                ),
                {"quote_id": request.quote_id, "od_product_id": od_product_id},
            ).fetchone()

            if quote_row:
                final_price, expires_at_val, decision = quote_row
                # Kiểm tra xem báo giá đã hết hạn hoặc không được chấp nhận chưa
                is_expired = False
                if expires_at_val:
                    if isinstance(expires_at_val, str):
                        expires_at_dt = datetime.fromisoformat(expires_at_val.replace("Z", "+00:00"))
                    else:
                        expires_at_dt = expires_at_val
                    if datetime.now(UTC) > expires_at_dt:
                        is_expired = True

                if not is_expired and decision == "accepted":
                    booked_price = float(final_price)

        if booked_price is None:
            # Tạo báo giá mới từ PricingService
            from backend.services.pricing_service import PricingService

            new_quote = PricingService().create_pricing_quote(od_product_id=od_product_id, db=db)
            booked_price = new_quote.final_price

        # 7. Lưu booking trạng thái held
        booking_code = generate_booking_code()
        insert_booking_query = text("""
            INSERT INTO bookings (
                booking_code, od_product_id, seat_id, status, channel, booked_price, booked_at, expires_at
            ) VALUES (
                :booking_code, :od_product_id, :seat_id, 'held', :channel, :booked_price, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '15 minutes'
            ) RETURNING id, booked_at, expires_at
        """)

        res = db.execute(
            insert_booking_query,
            {
                "booking_code": booking_code,
                "od_product_id": od_product_id,
                "seat_id": selected_seat_id,
                "channel": request.channel or "web",
                "booked_price": booked_price,
            },
        ).fetchone()

        booking_id, booked_at_val, expires_at_val = res

        booked_at_str = booked_at_val.isoformat() if not isinstance(booked_at_val, str) else booked_at_val
        expires_at_str = expires_at_val.isoformat() if not isinstance(expires_at_val, str) else expires_at_val

        return BookingResponse(
            booking_id=booking_id,
            booking_code=booking_code,
            od_product_id=od_product_id,
            seat_id=selected_seat_id,
            status="held",
            booked_price=booked_price,
            booked_at=booked_at_str,
            expires_at=expires_at_str,
        )

    def confirm_booking(
        self, booking_id: int, db: Session, allow_group: bool = False
    ) -> BookingConfirmResponse:
        """Xác nhận một booking đang giữ chỗ.

        `allow_group` chỉ được bật khi lời gọi đến từ `CombinedBookingService.confirm`,
        nơi cả nhóm vé ghép chặng được xác nhận trong cùng một giao dịch. Xác nhận lẻ
        một chặng của hành trình ghép sẽ để lại nhóm ở trạng thái nửa vời — khách trả
        tiền chặng A->B rồi mới phát hiện chặng B->D đã hết hạn giữ chỗ — nên mặc định
        bị chặn.
        """
        # 1. Truy vấn booking
        booking_row = db.execute(
            text("SELECT od_product_id, status, expires_at, booking_code FROM bookings WHERE id = :booking_id"),
            {"booking_id": booking_id},
        ).fetchone()

        if not booking_row:
            raise ValueError(f"Không tìm thấy booking với ID {booking_id}")

        od_product_id, status, expires_at_val, booking_code = booking_row

        if not allow_group:
            group_code = db.execute(
                text("""
                    SELECT booking_group.group_code
                    FROM booking_group_items item
                    JOIN booking_groups booking_group ON booking_group.id = item.booking_group_id
                    WHERE item.booking_id = :booking_id
                """),
                {"booking_id": booking_id},
            ).scalar()
            if group_code:
                raise ValueError(
                    f"Vé {booking_code} là một chặng của hành trình ghép {group_code}; "
                    f"hãy xác nhận cả nhóm qua POST /booking/combined/{group_code}/confirm"
                )

        if status != "held":
            raise ValueError(f"Booking không ở trạng thái giữ chỗ (đang là '{status}')")

        # Kiểm tra hết hạn giữ chỗ
        if expires_at_val:
            if isinstance(expires_at_val, str):
                expires_at_dt = datetime.fromisoformat(expires_at_val.replace("Z", "+00:00"))
            else:
                expires_at_dt = expires_at_val
            if datetime.now(UTC) > expires_at_dt:
                raise ValueError("Giữ chỗ đã hết hạn và không thể xác nhận")

        # 2. Lấy thông tin chuyến tàu và loại ghế
        prod_row = db.execute(
            text("SELECT trip_id, seat_type FROM od_products WHERE id = :od_product_id"),
            {"od_product_id": od_product_id},
        ).fetchone()
        trip_id, seat_type = prod_row

        selected_seat = db.execute(
            text("""
                SELECT seat.id, seat.coach_no, seat.seat_no
                FROM bookings booking
                JOIN seats seat ON seat.id = booking.seat_id
                WHERE booking.id = :booking_id
            """),
            {"booking_id": booking_id},
        ).mappings().first()
        if selected_seat:
            db.execute(
                text("""
                    UPDATE bookings
                    SET status = 'confirmed', expires_at = NULL
                    WHERE id = :booking_id
                """),
                {"booking_id": booking_id},
            )
            return BookingConfirmResponse(
                booking_id=booking_id,
                booking_code=booking_code,
                status="confirmed",
                seat_id=int(selected_seat["id"]),
                coach_no=str(selected_seat["coach_no"]),
                seat_no=str(selected_seat["seat_no"]),
            )

        # 3. Thuật toán tìm ghế vật lý trống không bị trùng chặng
        seat_query = text("""
            SELECT s.id, s.coach_no, s.seat_no
            FROM seats s
            WHERE s.trip_id = :trip_id
              AND s.seat_type = :seat_type
              AND s.status = 'available'
              AND s.id NOT IN (
                  SELECT b.seat_id
                  FROM bookings b
                  JOIN od_product_segments ops1 ON b.od_product_id = ops1.od_product_id
                  WHERE b.seat_id IS NOT NULL
                    AND b.status IN ('held', 'confirmed')
                    AND ops1.segment_id IN (
                        SELECT ops2.segment_id
                        FROM od_product_segments ops2
                        WHERE ops2.od_product_id = :od_product_id
                    )
              )
            LIMIT 1
        """)

        seat_row = (
            db.execute(seat_query, {"trip_id": trip_id, "seat_type": seat_type, "od_product_id": od_product_id})
            .mappings()
            .first()
        )

        if not seat_row:
            raise ValueError("Không tìm thấy ghế vật lý nào trống và không trùng chặng trên chuyến tàu")

        seat_id = seat_row["id"]
        coach_no = seat_row["coach_no"]
        seat_no = seat_row["seat_no"]

        # 4. Xác nhận đặt vé
        db.execute(
            text("""
                UPDATE bookings
                SET status = 'confirmed', seat_id = :seat_id, expires_at = NULL
                WHERE id = :booking_id
            """),
            {"booking_id": booking_id, "seat_id": seat_id},
        )

        return BookingConfirmResponse(
            booking_id=booking_id,
            booking_code=booking_code,
            status="confirmed",
            seat_id=seat_id,
            coach_no=coach_no,
            seat_no=seat_no,
        )

    def release_expired_bookings(self, db: Session) -> int:
        # 1. Tìm các booking giữ chỗ đã hết hạn
        expired_rows = (
            db.execute(
                text("SELECT id, od_product_id FROM bookings WHERE status = 'held' AND expires_at < CURRENT_TIMESTAMP")
            )
            .mappings()
            .all()
        )

        released_count = 0
        update_inventory_query = text("""
            UPDATE segment_inventory
            SET remaining = remaining + 1
            WHERE segment_id = :seg_id AND seat_type = :seat_type
        """)

        for row in expired_rows:
            bid = row["id"]
            od_product_id = row["od_product_id"]

            # Cập nhật status sang cancelled
            db.execute(text("UPDATE bookings SET status = 'cancelled' WHERE id = :bid"), {"bid": bid})

            # Lấy thông tin loại ghế và các chặng
            prod_row = db.execute(
                text("SELECT seat_type FROM od_products WHERE id = :od_product_id"), {"od_product_id": od_product_id}
            ).fetchone()
            seat_type = prod_row[0]

            segment_rows = db.execute(
                text("SELECT segment_id FROM od_product_segments WHERE od_product_id = :od_product_id"),
                {"od_product_id": od_product_id},
            ).fetchall()

            # Cộng lại tồn kho chặng
            for seg_row in segment_rows:
                seg_id = seg_row[0]
                db.execute(update_inventory_query, {"seg_id": seg_id, "seat_type": seat_type})

            released_count += 1

        return released_count
