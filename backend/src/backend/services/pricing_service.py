import json
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.ai_client import AIClient, SegmentBidPrice
from backend.views.pricing_view import (
    PricingExplanation,
    PricingQuoteODResponse,
    PricingQuoteRequest,
    PricingQuoteResponse,
)


def evaluate_bid_price(fare: float, opportunity_cost: float, availability: int) -> str:
    """Apply the FR2.2 acceptance threshold to a quoted fare."""
    if availability <= 0 or fare < opportunity_cost:
        return "rejected"
    return "accepted"


class PricingService:
    def __init__(self, ai_client: AIClient | None = None) -> None:
        self._ai_client = ai_client or AIClient()

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

    async def create_pricing_quote_from_od(self, request: PricingQuoteRequest, db: Session) -> PricingQuoteODResponse:
        product = self._find_od_product(request, db)
        segments = self._load_segments(product["id"], product["seat_type"], db)
        if not segments:
            raise ValueError("San pham OD chua duoc anh xa vao chang nao")

        opportunity_cost = sum(float(segment["bid_price"]) for segment in segments)
        availability = min(int(segment["remaining"]) for segment in segments)
        ai_result = await self._ai_client.price(
            od_product_id=int(product["id"]),
            service_date=self._as_date(product["service_date"]),
            seat_type=str(product["seat_type"]),
            base_price=float(product["base_price"]),
            segments=[
                SegmentBidPrice(
                    segment_id=int(segment["segment_id"]),
                    bid_price=float(segment["bid_price"]),
                )
                for segment in segments
            ],
        )

        policy = self._load_policy(int(product["id"]), db)
        final_price, policy_id, applied_policies = self._apply_policy(
            proposed_price=ai_result.proposed_price,
            od_product_id=int(product["id"]),
            policy=policy,
            db=db,
        )
        decision = evaluate_bid_price(final_price, opportunity_cost, availability)

        bottleneck = max(segments, key=lambda segment: float(segment["bid_price"]))
        bottleneck_name = f"{bottleneck['origin_name']} -> {bottleneck['destination_name']}"
        segment_bid_prices = {str(segment["segment_id"]): float(segment["bid_price"]) for segment in segments}
        elasticity = float(ai_result.explanation.get("elasticity", 0.0) or 0.0)
        markup_factor = elasticity / (elasticity - 1) if elasticity > 1 else 1.0
        explanation = PricingExplanation(
            base_opportunity_cost=opportunity_cost,
            markup_factor=markup_factor,
            applied_policies=applied_policies,
            bottleneck_segment_id=int(bottleneck["segment_id"]),
            bottleneck_segment=bottleneck_name,
            segment_bid_prices=segment_bid_prices,
        )

        insert_result = db.execute(
            text("""
                INSERT INTO price_quotes (
                    od_product_id, policy_id, opportunity_cost, proposed_price, final_price,
                    decision, explanation, expires_at, run_version
                ) VALUES (
                    :od_product_id, :policy_id, :opportunity_cost, :proposed_price, :final_price,
                    :decision, :explanation, CURRENT_TIMESTAMP + INTERVAL '15 minutes', :run_version
                ) RETURNING id, expires_at
            """),
            {
                "od_product_id": product["id"],
                "policy_id": policy_id,
                "opportunity_cost": opportunity_cost,
                "proposed_price": ai_result.proposed_price,
                "final_price": final_price,
                "decision": decision,
                "explanation": json.dumps(explanation.model_dump()),
                "run_version": next(
                    (segment["run_version"] for segment in segments if segment["run_version"]),
                    None,
                ),
            },
        ).fetchone()
        quote_id, expires_at = insert_result

        return PricingQuoteODResponse(
            quote_id=int(quote_id),
            od_product_id=int(product["id"]),
            policy_id=policy_id,
            opportunity_cost=opportunity_cost,
            proposed_price=ai_result.proposed_price,
            final_price=final_price,
            decision=decision,
            explanation=explanation,
            expires_at=expires_at if isinstance(expires_at, str) else expires_at.isoformat(),
            origin=str(product["origin_name"]),
            destination=str(product["destination_name"]),
            service_date=self._as_date(product["service_date"]),
            seat_type=str(product["seat_type"]),
            availability=availability,
        )

    @staticmethod
    def _find_od_product(request: PricingQuoteRequest, db: Session):
        row = (
            db.execute(
                text("""
                SELECT
                    odp.id, odp.base_price, odp.seat_type, t.service_date,
                    origin.name AS origin_name, destination.name AS destination_name
                FROM od_products odp
                JOIN trips t ON t.id = odp.trip_id
                JOIN stations origin ON origin.id = odp.origin_station_id
                JOIN stations destination ON destination.id = odp.destination_station_id
                WHERE t.service_date = :service_date
                  AND odp.seat_type = :seat_type
                  AND odp.is_active = TRUE
                  AND (CAST(:trip_id AS INTEGER) IS NULL OR t.id = :trip_id)
                  AND (LOWER(origin.code) = LOWER(:origin) OR LOWER(origin.name) = LOWER(:origin))
                  AND (
                      LOWER(destination.code) = LOWER(:destination)
                      OR LOWER(destination.name) = LOWER(:destination)
                  )
                ORDER BY t.departure_at ASC
                LIMIT 1
            """),
                {
                    "origin": request.origin,
                    "destination": request.destination,
                    "service_date": request.service_date,
                    "seat_type": request.seat_type,
                    "trip_id": request.trip_id,
                },
            )
            .mappings()
            .first()
        )
        if not row:
            raise ValueError("Khong tim thay san pham OD phu hop voi yeu cau")
        return row

    @staticmethod
    def _load_segments(od_product_id: int, seat_type: str, db: Session):
        return (
            db.execute(
                text("""
                SELECT
                    segment.id AS segment_id,
                    origin.name AS origin_name,
                    destination.name AS destination_name,
                    COALESCE(inventory.remaining, 0) AS remaining,
                    COALESCE(bid.bid_price, 0) AS bid_price,
                    bid.run_version
                FROM od_product_segments mapping
                JOIN segments segment ON segment.id = mapping.segment_id
                JOIN stations origin ON origin.id = segment.origin_station_id
                JOIN stations destination ON destination.id = segment.destination_station_id
                LEFT JOIN segment_inventory inventory
                  ON inventory.segment_id = segment.id AND inventory.seat_type = :seat_type
                LEFT JOIN bid_prices bid
                  ON bid.segment_id = segment.id
                 AND bid.seat_type = :seat_type
                 AND bid.is_active = TRUE
                WHERE mapping.od_product_id = :od_product_id
                ORDER BY segment.sequence_no ASC
            """),
                {"od_product_id": od_product_id, "seat_type": seat_type},
            )
            .mappings()
            .all()
        )

    @staticmethod
    def _load_policy(od_product_id: int, db: Session):
        return (
            db.execute(
                text("""
                SELECT id, min_price, max_price, max_step_change
                FROM price_policies
                WHERE (od_product_id = :od_product_id OR od_product_id IS NULL)
                  AND status = 'active'
                  AND valid_from <= CURRENT_TIMESTAMP
                  AND (valid_to IS NULL OR valid_to >= CURRENT_TIMESTAMP)
                ORDER BY od_product_id DESC NULLS LAST
                LIMIT 1
            """),
                {"od_product_id": od_product_id},
            )
            .mappings()
            .first()
        )

    @staticmethod
    def _apply_policy(
        *, proposed_price: float, od_product_id: int, policy, db: Session
    ) -> tuple[float, int | None, list[str]]:
        if not policy:
            return proposed_price, None, []

        final_price = proposed_price
        applied: list[str] = []
        min_price = float(policy["min_price"])
        max_price = float(policy["max_price"])
        max_step = float(policy["max_step_change"])
        if final_price < min_price:
            final_price = min_price
            applied.append("MIN_PRICE_ENFORCED")
        if final_price > max_price:
            final_price = max_price
            applied.append("MAX_PRICE_ENFORCED")

        previous = db.execute(
            text("""
                SELECT final_price
                FROM price_quotes
                WHERE od_product_id = :od_product_id AND decision = 'accepted'
                ORDER BY quoted_at DESC
                LIMIT 1
            """),
            {"od_product_id": od_product_id},
        ).fetchone()
        if previous:
            previous_price = float(previous[0])
            if final_price > previous_price + max_step:
                final_price = previous_price + max_step
                applied.append("MAX_STEP_CHANGE_CAPPED")
            elif final_price < previous_price - max_step:
                final_price = previous_price - max_step
                applied.append("MIN_STEP_CHANGE_CAPPED")
        return final_price, int(policy["id"]), applied

    @staticmethod
    def _as_date(value: date | str) -> date:
        return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])
