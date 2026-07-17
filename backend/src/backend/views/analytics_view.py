from pydantic import BaseModel, Field


class LegHeatmapItem(BaseModel):
    segment_id: int = Field(..., description="ID của chặng")
    sequence_no: int = Field(..., description="Thứ tự chặng trong chuyến")
    origin_station_code: str = Field(..., description="Mã ga đi chặng")
    destination_station_code: str = Field(..., description="Mã ga đến chặng")
    capacity: int = Field(..., description="Sức chứa gốc")
    remaining: int = Field(..., description="Tồn kho còn lại")
    seat_type: str = Field(..., description="Loại chỗ")
    bid_price: float = Field(..., description="Chi phí cơ hội hoạt động")
    is_bottleneck: bool = Field(..., description="Chặng này có phải nút cổ chai không")


class LegHeatmapResponse(BaseModel):
    trip_id: int = Field(..., description="ID của chuyến tàu")
    legs: list[LegHeatmapItem] = Field(..., description="Danh sách các chặng và tỷ lệ lấp đầy")


class ForecastItem(BaseModel):
    od_product_id: int = Field(..., description="ID của sản phẩm OD")
    origin_station_code: str = Field(..., description="Mã ga lên tàu")
    destination_station_code: str = Field(..., description="Mã ga xuống tàu")
    seat_type: str = Field(..., description="Loại chỗ")
    lead_days: int = Field(..., description="Số ngày trước ngày khởi hành")
    demand_point: float = Field(..., description="Dự báo điểm nhu cầu")
    demand_p10: float | None = Field(None, description="Phân vị nhu cầu 10%")
    demand_p50: float | None = Field(None, description="Phân vị nhu cầu 50%")
    demand_p90: float | None = Field(None, description="Phân vị nhu cầu 90%")


class BookingCurvePoint(BaseModel):
    lead_days: int = Field(..., description="Số ngày trước ngày khởi hành")
    cumulative_bookings: int = Field(..., description="Số lượng đặt vé lũy kế thực tế")
    forecast_demand_point: float = Field(..., description="Dự báo nhu cầu tích lũy")


class ForecastResponse(BaseModel):
    trip_id: int = Field(..., description="ID của chuyến tàu")
    service_date: str = Field(..., description="Ngày chạy tàu (YYYY-MM-DD)")
    forecasts: list[ForecastItem] = Field(..., description="Danh sách chi tiết dự báo nhu cầu")
    booking_curve: list[BookingCurvePoint] = Field(..., description="Đường cong đặt vé lũy kế")
