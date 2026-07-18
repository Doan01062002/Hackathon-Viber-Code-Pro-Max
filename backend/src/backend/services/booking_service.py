import random
import string
from datetime import datetime, timezone
UTC = timezone.utc

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.views.booking_view import BookingConfirmResponse, BookingCreateRequest, BookingResponse


def generate_booking_code() -> str:
    return "BK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


class BookingService:
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
        quota_row = db.execute(
            text("SELECT quota FROM quotas WHERE od_product_id = :od_product_id AND is_active = TRUE"),
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
                :booking_code, :od_product_id, NULL, 'held', :channel, :booked_price, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '15 minutes'
            ) RETURNING id, booked_at, expires_at
        """)

        res = db.execute(
            insert_booking_query,
            {
                "booking_code": booking_code,
                "od_product_id": od_product_id,
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
            seat_id=None,
            status="held",
            booked_price=booked_price,
            booked_at=booked_at_str,
            expires_at=expires_at_str,
        )

    def confirm_booking(self, booking_id: int, db: Session) -> BookingConfirmResponse:
        # 1. Truy vấn booking
        booking_row = db.execute(
            text("SELECT od_product_id, status, expires_at, booking_code FROM bookings WHERE id = :booking_id"),
            {"booking_id": booking_id},
        ).fetchone()

        if not booking_row:
            raise ValueError(f"Không tìm thấy booking với ID {booking_id}")

        od_product_id, status, expires_at_val, booking_code = booking_row

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
