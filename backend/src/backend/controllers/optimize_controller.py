import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import get_db, get_session_factory
from backend.services.optimize_service import OptimizeService

router = APIRouter()

# Lưu trữ in-memory trạng thái các jobs chạy tối ưu hóa
JOBS: dict[str, dict[str, Any]] = {}


class OptimizeRequest(BaseModel):
    trip_id: int = Field(..., description="ID của chuyến tàu cần chạy tối ưu hóa")


class OptimizeResponse(BaseModel):
    status: str = Field(..., description="Trạng thái xử lý (success / error)")
    resolved_at: str = Field(..., description="Thời điểm hoàn thành giải tối ưu")
    run_version: str = Field(..., description="Phiên bản chạy (run_version) mới được kích hoạt")
    quotas_updated_count: int = Field(..., description="Số lượng bản ghi quotas đã được tạo mới")
    bid_prices_updated_count: int = Field(..., description="Số lượng bản ghi bid_prices đã được tạo mới")
    message: str = Field(..., description="Thông điệp kết quả")


class OptimizeSubmitResponse(BaseModel):
    job_id: str = Field(..., description="ID của job chạy tối ưu hóa")
    status: str = Field(..., description="Trạng thái của job (pending / running / completed / failed)")
    message: str = Field(..., description="Thông điệp kết quả")


class OptimizeJobStatusResponse(BaseModel):
    job_id: str = Field(..., description="ID của job")
    status: str = Field(..., description="Trạng thái của job")
    result: OptimizeResponse | None = Field(None, description="Kết quả giải tối ưu (nếu đã hoàn thành)")
    error: str | None = Field(None, description="Chi tiết lỗi nếu job thất bại")


def get_optimize_service() -> OptimizeService:
    return OptimizeService()


def run_optimize_task(job_id: str, trip_id: int):
    """Background task chạy tối ưu hóa bất đồng bộ."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        service = OptimizeService()
        res = service.run_optimization_batch(trip_id=trip_id, db=db)
        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["result"] = res
    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)
    finally:
        db.close()


@router.post("/optimize/resolve", response_model=OptimizeSubmitResponse)
async def resolve_optimization_batch(
    request: OptimizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> OptimizeSubmitResponse:
    """Chạy quy trình dự báo -> tối ưu phân bổ -> định giá động bất đồng bộ dưới dạng background job."""
    # 1. Xác thực nhanh sự tồn tại của trip trước khi đẩy job chạy ngầm
    trip_row = db.execute(
        text("SELECT id FROM trips WHERE id = :trip_id"),
        {"trip_id": request.trip_id}
    ).fetchone()
    if not trip_row:
        raise HTTPException(
            status_code=400,
            detail=f"Không tìm thấy chuyến tàu với ID {request.trip_id}"
        )

    # 2. Tạo job chạy nền
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "job_id": job_id,
        "status": "running",
        "result": None,
        "error": None
    }

    background_tasks.add_task(run_optimize_task, job_id, request.trip_id)

    return OptimizeSubmitResponse(
        job_id=job_id,
        status="running",
        message="Yêu cầu chạy tối ưu hóa đã được đưa vào hàng đợi xử lý nền."
    )


@router.get("/optimize/resolve/jobs/{job_id}", response_model=OptimizeJobStatusResponse)
async def get_optimize_job_status(job_id: str) -> OptimizeJobStatusResponse:
    """Truy vấn trạng thái và kết quả của job chạy tối ưu hóa."""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin job với ID yêu cầu.")

    return OptimizeJobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        result=OptimizeResponse(**job["result"]) if job["result"] else None,
        error=job["error"]
    )



from fastapi import Query


class OptimizeVersionResponse(BaseModel):
    run_version: str = Field(..., description="Tên phiên bản chạy")
    calculated_at: str | None = Field(None, description="Thời điểm tạo phiên bản")
    is_active: bool = Field(..., description="Cờ trạng thái hoạt động")

class OptimizeRollbackRequest(BaseModel):
    trip_id: int = Field(..., description="ID của chuyến tàu")
    target_version: str = Field(..., description="Phiên bản muốn khôi phục về")

class OptimizeRollbackResponse(BaseModel):
    status: str = Field(..., description="Trạng thái (success/error)")
    trip_id: int = Field(..., description="ID của chuyến tàu")
    rolled_back_to: str = Field(..., description="Phiên bản đã rollback về")
    message: str = Field(..., description="Thông điệp kết quả")


@router.get("/optimize/resolve/versions", response_model=list[OptimizeVersionResponse])
async def get_optimize_versions(
    trip_id: int = Query(..., description="ID của chuyến tàu"),
    service: OptimizeService = Depends(get_optimize_service),
    db: Session = Depends(get_db)
) -> list[OptimizeVersionResponse]:
    """Lấy danh sách các phiên bản tối ưu đã chạy của chuyến tàu."""
    try:
        versions = service.get_run_versions(trip_id=trip_id, db=db)
        return [OptimizeVersionResponse(**v) for v in versions]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


@router.post("/optimize/resolve/rollback", response_model=OptimizeRollbackResponse)
async def rollback_optimize_version(
    request: OptimizeRollbackRequest,
    service: OptimizeService = Depends(get_optimize_service),
    db: Session = Depends(get_db)
) -> OptimizeRollbackResponse:
    """Khôi phục cấu hình tối ưu của chuyến tàu về phiên bản trước đó (Rollback)."""
    try:
        res = service.rollback_to_version(db=db, trip_id=request.trip_id, target_version=request.target_version)
        return OptimizeRollbackResponse(**res)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
