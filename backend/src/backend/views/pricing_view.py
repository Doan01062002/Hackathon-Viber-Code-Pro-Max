from pydantic import BaseModel, Field


class PricingExplanation(BaseModel):
    base_opportunity_cost: float = Field(..., description="Tổng chi phí cơ hội cơ sở")
    markup_factor: float = Field(..., description="Hệ số markup được áp dụng")
    applied_policies: list[str] = Field(..., description="Danh sách các chính sách được áp dụng")


class PricingQuoteResponse(BaseModel):
    quote_id: int = Field(..., description="ID của báo giá được lưu")
    od_product_id: int = Field(..., description="ID của sản phẩm OD")
    policy_id: int | None = Field(None, description="ID của chính sách được áp dụng (nếu có)")
    opportunity_cost: float = Field(..., description="Tổng chi phí cơ hội")
    proposed_price: float = Field(..., description="Mức giá đề xuất ban đầu")
    final_price: float = Field(..., description="Mức giá cuối cùng sau safeguards")
    decision: str = Field(..., description="Trạng thái quyết định (accepted, rejected, blocked)")
    explanation: PricingExplanation = Field(..., description="Giải trình cơ cấu giá chi tiết")
    expires_at: str = Field(..., description="Thời điểm hết hạn báo giá (ISO format)")
