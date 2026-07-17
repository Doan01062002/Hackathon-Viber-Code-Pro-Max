from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.database import get_db

router = APIRouter()

class CoachResponse(BaseModel):
    name: str = Field(..., description="Tên hiển thị của toa tàu")
    type: str = Field(..., description="Loại chỗ của toa (Ngồi mềm, Giường nằm K6)")
    occupancy: str = Field(..., description="Hệ số tải dưới dạng phần trăm (e.g. 76%)")
    coach_no: str = Field(..., description="Mã số toa tàu")

class SeatLegendItem(BaseModel):
    tone: str
    label: str

class SeatPlanResponse(BaseModel):
    route: str = Field(..., description="Hành trình chuyến tàu (e.g. SE1 · 19/07/2026)")
    coach: str = Field(..., description="Tên toa tàu")
    seat_type: str = Field(..., description="Mã loại chỗ (ngoi_mem, giuong_nam_k6)")
    seats: list[list[str]] = Field(..., description="Ma trận 2D trạng thái các ghế")
    seatLegend: list[SeatLegendItem] = Field(..., description="Chú giải màu sắc trạng thái")

class GapSuggestionResponse(BaseModel):
    route: str = Field(..., description="Tuyến đường trống (e.g. Vinh → Huế)")
    seatType: str = Field(..., description="Loại chỗ tiếng Việt (e.g. Giường nằm K6)")
    benefit: str = Field(..., description="Lợi ích khả dụng (e.g. +17 chỗ khả dụng)")
    priority: str = Field(..., description="Độ ưu tiên (Cao, Trung bình, Theo dõi)")
    reason: str = Field(..., description="Lý do chi tiết gợi ý từ thuật toán")

@router.get("/seats/coaches", response_model=list[CoachResponse])
async def get_coaches(
    trip_id: int = Query(..., description="ID của chuyến tàu"),
    db: Session = Depends(get_db)
) -> list[CoachResponse]:
    """Lấy danh sách các toa tàu kèm theo loại ghế và hệ số tải occupancy."""
    # 1. Kiểm tra sự tồn tại của trip
    trip_row = db.execute(
        text("SELECT id FROM trips WHERE id = :trip_id"),
        {"trip_id": trip_id}
    ).fetchone()
    if not trip_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy chuyến tàu với ID {trip_id}"
        )

    # 2. Lấy cấu hình các toa
    coaches_query = text("""
        SELECT coach_no, seat_type, COUNT(*) as total_seats
        FROM seats
        WHERE trip_id = :trip_id
        GROUP BY coach_no, seat_type
        ORDER BY coach_no;
    """)
    coaches_rows = db.execute(coaches_query, {"trip_id": trip_id}).fetchall()

    # 3. Lấy số ghế có ít nhất một booking active
    occupied_query = text("""
        SELECT s.coach_no, COUNT(DISTINCT s.id) as occupied_seats
        FROM seats s
        JOIN bookings b ON b.seat_id = s.id
        WHERE s.trip_id = :trip_id AND b.status IN ('held', 'confirmed')
        GROUP BY s.coach_no;
    """)
    occupied_rows = db.execute(occupied_query, {"trip_id": trip_id}).fetchall()
    occupied_map = {r[0]: int(r[1]) for r in occupied_rows}

    coaches = []
    for r in coaches_rows:
        coach_no = r[0]
        seat_type = r[1]
        total_seats = int(r[2])
        
        occupied_seats = occupied_map.get(coach_no, 0)
        # Hệ số tải giới hạn từ 0% đến 100%
        pct = min(100, int(round((occupied_seats / total_seats) * 100))) if total_seats > 0 else 0
        
        type_str = "Ngồi mềm" if seat_type == "ngoi_mem" else "Giường nằm K6"
        coaches.append(
            CoachResponse(
                name=f"Toa {coach_no}",
                type=type_str,
                occupancy=f"{pct}%",
                coach_no=coach_no
            )
        )
    return coaches

@router.get("/seats/layout", response_model=SeatPlanResponse)
async def get_seat_layout(
    trip_id: int = Query(..., description="ID của chuyến tàu"),
    coach_no: str = Query(..., description="Mã số toa tàu"),
    db: Session = Depends(get_db)
) -> SeatPlanResponse:
    """Trả về sơ đồ cấu hình ghế 2D của toa tàu kèm trạng thái vật lý của từng ghế."""
    # 1. Kiểm tra sự tồn tại của trip và lấy thông tin cơ bản
    trip_row = db.execute(
        text("""
            SELECT t.service_date, tr.code 
            FROM trips t
            JOIN trains tr ON t.train_id = tr.id
            WHERE t.id = :trip_id
        """),
        {"trip_id": trip_id}
    ).fetchone()
    if not trip_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy chuyến tàu với ID {trip_id}"
        )
    service_date, train_code = trip_row

    # 2. Lấy danh sách tất cả các ghế của toa
    seats_query = text("""
        SELECT id, seat_no, seat_type, status
        FROM seats
        WHERE trip_id = :trip_id AND coach_no = :coach_no
        ORDER BY seat_no;
    """)
    seats_rows = db.execute(seats_query, {"trip_id": trip_id, "coach_no": coach_no}).fetchall()
    if not seats_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy ghế nào thuộc toa {coach_no} trên chuyến tàu {trip_id}"
        )

    seat_type = seats_rows[0][2]

    # 3. Lấy đặt chỗ đang hoạt động cho các ghế trong toa
    bookings_query = text("""
        SELECT seat_id, status
        FROM bookings
        WHERE seat_id IN (
            SELECT id FROM seats
            WHERE trip_id = :trip_id AND coach_no = :coach_no
        ) AND status IN ('held', 'confirmed');
    """)
    bookings_rows = db.execute(bookings_query, {"trip_id": trip_id, "coach_no": coach_no}).fetchall()
    bookings_map = {r[0]: r[1] for r in bookings_rows}

    # 4. Xác định trạng thái của từng ghế
    flat_statuses = []
    for s_row in seats_rows:
        s_id = s_row[0]
        db_status = s_row[3]
        
        if db_status in ("locked", "maintenance"):
            status_str = "blocked"
        elif s_id in bookings_map:
            status_str = bookings_map[s_id]  # 'held' hoặc 'confirmed'
        else:
            status_str = "available"
        flat_statuses.append(status_str)

    # 5. Tổ chức ma trận 2D
    # Ngồi mềm: chia theo hàng 4 ghế
    # Giường nằm K6: chia theo khoang 6 giường (3 tầng mỗi bên)
    chunk_size = 4 if seat_type == "ngoi_mem" else 6
    seats_2d = [
        flat_statuses[i : i + chunk_size]
        for i in range(0, len(flat_statuses), chunk_size)
    ]

    route_str = f"{train_code} · {service_date.strftime('%d/%m/%Y')}" if service_date else f"{train_code}"
    
    legend = [
        SeatLegendItem(tone="available", label="Còn trống"),
        SeatLegendItem(tone="selected", label="Đang chọn"),
        SeatLegendItem(tone="held", label="Đang giữ chỗ"),
        SeatLegendItem(tone="confirmed", label="Đã bán"),
        SeatLegendItem(tone="blocked", label="Khóa vận hành"),
    ]

    return SeatPlanResponse(
        route=route_str,
        coach=f"Toa {coach_no}",
        seat_type=seat_type,
        seats=seats_2d,
        seatLegend=legend
    )

@router.get("/seats/gap-suggestions", response_model=list[GapSuggestionResponse])
async def get_gap_suggestions(
    trip_id: int = Query(..., description="ID của chuyến tàu"),
    db: Session = Depends(get_db)
) -> list[GapSuggestionResponse]:
    """Tổng hợp dữ liệu khoảng trống ghế từ bảng gap_combinations để trả về danh sách gợi ý tối ưu."""
    # 1. Kiểm tra sự tồn tại của trip
    trip_row = db.execute(
        text("SELECT id FROM trips WHERE id = :trip_id"),
        {"trip_id": trip_id}
    ).fetchone()
    if not trip_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy chuyến tàu với ID {trip_id}"
        )

    # 2. Truy vấn khoảng trống
    gap_query = text("""
        SELECT 
            s.coach_no,
            st_from.name AS from_station_name,
            st_to.name AS to_station_name,
            od.seat_type
        FROM gap_combinations gc
        JOIN seats s ON gc.seat_id = s.id
        JOIN stations st_from ON gc.from_station_id = st_from.id
        JOIN stations st_to ON gc.to_station_id = st_to.id
        JOIN od_products od ON gc.suggested_od_product_id = od.id
        WHERE s.trip_id = :trip_id AND gc.is_active = TRUE;
    """)
    rows = db.execute(gap_query, {"trip_id": trip_id}).fetchall()

    # 3. Nhóm và tính toán
    groups = {}
    for r in rows:
        coach_no = r[0]
        from_st = r[1]
        to_st = r[2]
        seat_type = r[3]
        
        key = (from_st, to_st, seat_type)
        if key not in groups:
            groups[key] = {"count": 0, "coaches": set()}
        groups[key]["count"] += 1
        groups[key]["coaches"].add(coach_no)

    suggestions = []
    for key, data in groups.items():
        from_st, to_st, seat_type = key
        count = data["count"]
        coaches_str = ", ".join(sorted(list(data["coaches"])))
        
        seat_type_vn = "Ngồi mềm" if seat_type == "ngoi_mem" else "Giường nằm K6"
        priority = "Cao" if count >= 10 else "Trung bình" if count >= 5 else "Theo dõi"
        
        suggestions.append(
            GapSuggestionResponse(
                route=f"{from_st} → {to_st}",
                seatType=seat_type_vn,
                benefit=f"+{count} chỗ khả dụng",
                priority=priority,
                reason=f"Có {count} khoảng trống liên tiếp trong toa {coaches_str} sau khi mở lại quota ngắn."
            )
        )
        
    # Sắp xếp theo ưu tiên: Cao -> Trung bình -> Theo dõi
    priority_order = {"Cao": 0, "Trung bình": 1, "Theo dõi": 2}
    suggestions.sort(key=lambda x: priority_order.get(x.priority, 3))
    
    return suggestions
