import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.views.pricing_view import PricingExplanation, PricingQuoteResponse


class PricingService:
    def create_pricing_quote(
        self, od_product_id: int, db: Session, run_version: str | None = None
    ) -> PricingQuoteResponse:
        # 1. Lấy thông tin cơ bản của sản phẩm OD
        product_row = db.execute(
            text("SELECT base_price, seat_type, trip_id FROM od_products WHERE id = :od_product_id"),
            {"od_product_id": od_product_id},
        ).fetchone()

        if not product_row:
            raise ValueError(f"Không tìm thấy sản phẩm OD với ID {od_product_id}")

        base_price_val, seat_type, trip_id = product_row
        base_price = float(base_price_val)

        # 2. Tính toán opportunity_cost bằng tổng bid_price các chặng chặng sản phẩm đi qua
        opp_cost_query = text("""
            SELECT
                COALESCE(SUM(bp.bid_price), 0.0) AS opportunity_cost
            FROM od_product_segments ops
            JOIN od_products odp ON ops.od_product_id = odp.id
            LEFT JOIN bid_prices bp ON (
                ops.segment_id = bp.segment_id
                AND odp.seat_type = bp.seat_type
                AND bp.is_active = TRUE
            )
            WHERE ops.od_product_id = :od_product_id
        """)

        opp_cost_row = db.execute(opp_cost_query, {"od_product_id": od_product_id}).fetchone()
        opportunity_cost = float(opp_cost_row[0]) if opp_cost_row else 0.0

        # 3. Tính toán proposed_price (giá đề xuất tối ưu)
        # Sử dụng hệ số markup 1.2 cho chi phí cơ hội
        proposed_price = base_price + (opportunity_cost * 1.2)

        # 4. Lấy chính sách giá đang hoạt động (price_policies)
        # Ưu tiên chính sách riêng của sản phẩm, sau đó đến chính sách chung (od_product_id IS NULL)
        policy_query = text("""
            SELECT
                id, min_price, max_price, max_step_change
            FROM price_policies
            WHERE (od_product_id = :od_product_id OR od_product_id IS NULL)
              AND status = 'active'
              AND valid_from <= CURRENT_TIMESTAMP
              AND (valid_to IS NULL OR valid_to >= CURRENT_TIMESTAMP)
            ORDER BY od_product_id DESC NULLS LAST
            LIMIT 1
        """)

        policy_row = db.execute(policy_query, {"od_product_id": od_product_id}).mappings().first()

        final_price = proposed_price
        policy_id = None
        applied_policies = []

        if policy_row:
            policy_id = policy_row["id"]
            min_price = float(policy_row["min_price"]) if policy_row["min_price"] is not None else None
            max_price = float(policy_row["max_price"]) if policy_row["max_price"] is not None else None
            max_step = float(policy_row["max_step_change"]) if policy_row["max_step_change"] is not None else None

            # Ràng buộc Trần/Sàn (Policy Guard)
            if min_price is not None and final_price < min_price:
                final_price = min_price
                applied_policies.append("MIN_PRICE_ENFORCED")
            if max_price is not None and final_price > max_price:
                final_price = max_price
                applied_policies.append("MAX_PRICE_ENFORCED")

            # Ràng buộc bước nhảy (Max Step Change) so với báo giá được chấp nhận gần nhất
            if max_step is not None:
                last_quote_query = text("""
                    SELECT final_price FROM price_quotes
                    WHERE od_product_id = :od_product_id AND decision = 'accepted'
                    ORDER BY quoted_at DESC LIMIT 1
                """)
                last_quote_row = db.execute(last_quote_query, {"od_product_id": od_product_id}).fetchone()

                if last_quote_row:
                    prev_price = float(last_quote_row[0])
                    if final_price > prev_price + max_step:
                        final_price = prev_price + max_step
                        applied_policies.append("MAX_STEP_CHANGE_CAPPED")
                    elif final_price < prev_price - max_step:
                        final_price = prev_price - max_step
                        applied_policies.append("MIN_STEP_CHANGE_CAPPED")

        # 5. Lưu bản ghi báo giá vào price_quotes
        explanation_data = {
            "base_opportunity_cost": opportunity_cost,
            "markup_factor": 1.2,
            "applied_policies": applied_policies,
        }

        insert_query = text("""
            INSERT INTO price_quotes (
                od_product_id, policy_id, opportunity_cost, proposed_price, final_price,
                decision, explanation, expires_at, run_version
            ) VALUES (
                :od_product_id, :policy_id, :opportunity_cost, :proposed_price, :final_price,
                'accepted', :explanation, CURRENT_TIMESTAMP + INTERVAL '15 minutes', :run_version
            ) RETURNING id, expires_at
        """)

        insert_result = db.execute(
            insert_query,
            {
                "od_product_id": od_product_id,
                "policy_id": policy_id,
                "opportunity_cost": opportunity_cost,
                "proposed_price": proposed_price,
                "final_price": final_price,
                "explanation": json.dumps(explanation_data),
                "run_version": run_version,
            },
        ).fetchone()

        quote_id, expires_at_val = insert_result

        # Đảm bảo expires_at dạng chuỗi ISO format
        if isinstance(expires_at_val, str):
            expires_at_str = expires_at_val
        else:
            expires_at_str = expires_at_val.isoformat()

        return PricingQuoteResponse(
            quote_id=quote_id,
            od_product_id=od_product_id,
            policy_id=policy_id,
            opportunity_cost=opportunity_cost,
            proposed_price=proposed_price,
            final_price=final_price,
            decision="accepted",
            explanation=PricingExplanation(
                base_opportunity_cost=opportunity_cost, markup_factor=1.2, applied_policies=applied_policies
            ),
            expires_at=expires_at_str,
        )
