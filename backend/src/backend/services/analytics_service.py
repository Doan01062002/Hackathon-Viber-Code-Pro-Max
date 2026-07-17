from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.views.analytics_view import (
    BookingCurvePoint,
    ForecastItem,
    ForecastResponse,
    LegHeatmapItem,
    LegHeatmapResponse,
)


class AnalyticsService:
    def get_legs_heatmap(self, trip_id: int, db: Session) -> LegHeatmapResponse:
        # 1. Kiểm tra trip_id tồn tại
        trip_check = db.execute(text("SELECT id FROM trips WHERE id = :trip_id"), {"trip_id": trip_id}).fetchone()

        if not trip_check:
            raise ValueError(f"Không tìm thấy chuyến tàu với ID {trip_id}")

        # 2. Truy vấn thông tin các chặng, sức chứa, tồn kho và giá vé cơ hội hoạt động
        query = text("""
            SELECT
                seg.id AS segment_id,
                seg.sequence_no,
                st_orig.code AS origin_station_code,
                st_dest.code AS destination_station_code,
                sc.capacity,
                si.remaining,
                sc.seat_type,
                COALESCE(bp.bid_price, 0.0) AS bid_price
            FROM segments seg
            JOIN stations st_orig ON seg.origin_station_id = st_orig.id
            JOIN stations st_dest ON seg.destination_station_id = st_dest.id
            JOIN segment_capacities sc ON seg.id = sc.segment_id
            JOIN segment_inventory si ON (sc.segment_id = si.segment_id AND sc.seat_type = si.seat_type)
            LEFT JOIN bid_prices bp ON (
                seg.id = bp.segment_id
                AND sc.seat_type = bp.seat_type
                AND bp.is_active = TRUE
            )
            WHERE seg.trip_id = :trip_id
            ORDER BY seg.sequence_no ASC, sc.seat_type ASC
        """)

        rows = db.execute(query, {"trip_id": trip_id}).mappings().all()

        legs = []
        for row in rows:
            capacity = row["capacity"]
            remaining = row["remaining"]
            orig_code = row["origin_station_code"]
            dest_code = row["destination_station_code"]

            # Định nghĩa nút cổ chai:
            # 1. Chặng Huế - Đà Nẵng
            # 2. Hoặc tỷ lệ lấp đầy >= 85%
            is_bottleneck = False
            if orig_code.upper() == "HUE" and dest_code.upper() == "DAN":
                is_bottleneck = True
            elif capacity > 0:
                fill_rate = (capacity - remaining) / capacity
                if fill_rate >= 0.85:
                    is_bottleneck = True

            legs.append(
                LegHeatmapItem(
                    segment_id=row["segment_id"],
                    sequence_no=row["sequence_no"],
                    origin_station_code=orig_code,
                    destination_station_code=dest_code,
                    capacity=capacity,
                    remaining=remaining,
                    seat_type=row["seat_type"],
                    bid_price=float(row["bid_price"]),
                    is_bottleneck=is_bottleneck,
                )
            )

        return LegHeatmapResponse(trip_id=trip_id, legs=legs)

    def get_forecast_data(self, trip_id: int, seat_type: str | None, db: Session) -> ForecastResponse:
        # 1. Lấy thông tin trip & service_date
        trip_row = db.execute(
            text("SELECT id, service_date FROM trips WHERE id = :trip_id"), {"trip_id": trip_id}
        ).fetchone()

        if not trip_row:
            raise ValueError(f"Không tìm thấy chuyến tàu với ID {trip_id}")

        trip_id_db, service_date_val = trip_row

        # Đảm bảo service_date là kiểu datetime.date
        if isinstance(service_date_val, str):
            service_date = datetime.strptime(service_date_val, "%Y-%m-%d").date()
        elif isinstance(service_date_val, date):
            service_date = service_date_val
        else:
            # Fallback nếu là datetime hoặc định dạng khác
            service_date = datetime.strptime(str(service_date_val)[:10], "%Y-%m-%d").date()

        # 2. Truy vấn danh sách dự báo (Forecast items) cho các sản phẩm OD của trip
        forecast_query = text("""
            SELECT
                odp.id AS od_product_id,
                st_orig.code AS origin_station_code,
                st_dest.code AS destination_station_code,
                odp.seat_type,
                df.lead_days,
                df.demand_point,
                df.demand_p10,
                df.demand_p50,
                df.demand_p90
            FROM od_products odp
            JOIN stations st_orig ON odp.origin_station_id = st_orig.id
            JOIN stations st_dest ON odp.destination_station_id = st_dest.id
            JOIN demand_forecasts df ON odp.id = df.od_product_id
            WHERE odp.trip_id = :trip_id
              AND (CAST(:seat_type AS VARCHAR) IS NULL OR odp.seat_type = :seat_type)
            ORDER BY odp.id ASC, df.lead_days DESC
        """)

        forecast_rows = db.execute(forecast_query, {"trip_id": trip_id, "seat_type": seat_type}).mappings().all()

        forecasts = []
        forecast_by_lead_day = {}  # lead_days -> sum(demand_point)

        for row in forecast_rows:
            lead = row["lead_days"]
            demand = float(row["demand_point"])
            forecast_by_lead_day[lead] = forecast_by_lead_day.get(lead, 0.0) + demand

            forecasts.append(
                ForecastItem(
                    od_product_id=row["od_product_id"],
                    origin_station_code=row["origin_station_code"],
                    destination_station_code=row["destination_station_code"],
                    seat_type=row["seat_type"],
                    lead_days=lead,
                    demand_point=demand,
                    demand_p10=float(row["demand_p10"]) if row["demand_p10"] is not None else None,
                    demand_p50=float(row["demand_p50"]) if row["demand_p50"] is not None else None,
                    demand_p90=float(row["demand_p90"]) if row["demand_p90"] is not None else None,
                )
            )

        # 3. Truy vấn các bookings đã xác nhận (confirmed)
        booking_query = text("""
            SELECT
                b.id,
                b.booked_at
            FROM bookings b
            JOIN od_products odp ON b.od_product_id = odp.id
            WHERE odp.trip_id = :trip_id
              AND b.status = 'confirmed'
              AND (CAST(:seat_type AS VARCHAR) IS NULL OR odp.seat_type = :seat_type)
        """)

        booking_rows = db.execute(booking_query, {"trip_id": trip_id, "seat_type": seat_type}).mappings().all()

        # Tính lead day cho từng booking
        booking_lead_days = []
        for r in booking_rows:
            booked_at_val = r["booked_at"]
            if isinstance(booked_at_val, str):
                # Loại bỏ timezone offset đơn giản để parse
                # Ví dụ: 2026-07-17T12:00:00+07:00 -> 2026-07-17
                booked_date = datetime.strptime(booked_at_val[:10], "%Y-%m-%d").date()
            elif isinstance(booked_at_val, datetime):
                booked_date = booked_at_val.date()
            elif isinstance(booked_at_val, date):
                booked_date = booked_at_val
            else:
                booked_date = datetime.strptime(str(booked_at_val)[:10], "%Y-%m-%d").date()

            lead_day = (service_date - booked_date).days
            booking_lead_days.append(lead_day)

        # 4. Tính toán Booking Curve tích lũy từ 60 ngày về 0
        booking_curve = []
        for t in range(60, -1, -1):
            # Số bookings có lead_days >= t (đặt từ trước hoặc đúng ngày t)
            cum_bookings = sum(1 for ld in booking_lead_days if ld >= t)
            # Lấy dự báo nhu cầu tích lũy tại lead_days = t
            fc_demand = float(forecast_by_lead_day.get(t, 0.0))

            booking_curve.append(
                BookingCurvePoint(
                    lead_days=t,
                    cumulative_bookings=cum_bookings,
                    forecast_demand_point=fc_demand,
                )
            )

        return ForecastResponse(
            trip_id=trip_id,
            service_date=service_date.isoformat(),
            forecasts=forecasts,
            booking_curve=booking_curve,
        )
