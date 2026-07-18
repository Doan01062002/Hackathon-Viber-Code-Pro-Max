import os
import pickle
import sys
from datetime import date, datetime, timezone
UTC = timezone.utc
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

# Thêm thư mục ai vào sys.path để import ai_service
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
ai_path = os.path.join(root_dir, "ai")
if ai_path not in sys.path:
    sys.path.append(ai_path)

from ai_service import datagen
from ai_service import optimization as opt


class OptimizeService:
    def run_optimization_batch(self, trip_id: int, db: Session) -> dict[str, Any]:
        # 1. Job đọc dữ liệu đầu vào (BE-10.1)
        trip_row = db.execute(
            text("SELECT id, service_date FROM trips WHERE id = :trip_id"), {"trip_id": trip_id}
        ).fetchone()

        if not trip_row:
            raise ValueError(f"Không tìm thấy chuyến tàu với ID {trip_id}")

        trip_id_db, service_date_val = trip_row

        # Chuẩn hóa service_date
        if isinstance(service_date_val, str):
            service_date_str = service_date_val[:10]
            service_date = date.fromisoformat(service_date_str)
        elif isinstance(service_date_val, date):
            service_date = service_date_val
            service_date_str = service_date.isoformat()
        else:
            service_date_str = str(service_date_val)[:10]
            service_date = date.fromisoformat(service_date_str)

        # Đọc danh sách od_products của chuyến tàu từ database
        query_ods = text("""
            SELECT
                odp.id AS od_product_id,
                st_orig.code AS origin_code,
                st_dest.code AS dest_code,
                odp.seat_type,
                odp.base_price,
                odp.distance_km,
                odp.origin_station_id,
                odp.destination_station_id
            FROM od_products odp
            JOIN stations st_orig ON odp.origin_station_id = st_orig.id
            JOIN stations st_dest ON odp.destination_station_id = st_dest.id
            WHERE odp.trip_id = :trip_id AND odp.is_active = TRUE
        """)
        od_rows = db.execute(query_ods, {"trip_id": trip_id}).mappings().all()

        if not od_rows:
            raise ValueError(f"Không tìm thấy sản phẩm OD nào cho chuyến tàu {trip_id}")

        od_product_map = {}
        for r in od_rows:
            key = (r["origin_code"].upper(), r["dest_code"].upper(), r["seat_type"])
            od_product_map[key] = r["od_product_id"]

        # Lấy danh sách segments của chuyến tàu
        segments_rows = db.execute(
            text("SELECT id, sequence_no FROM segments WHERE trip_id = :trip_id ORDER BY sequence_no ASC"),
            {"trip_id": trip_id},
        ).fetchall()
        segment_map = {i: row[0] for i, row in enumerate(segments_rows)}
        nseg = len(segments_rows)

        # Chuẩn bị run_version duy nhất
        run_version = "ver-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        solved_at = datetime.now(UTC).isoformat()

        # Tải Forecaster model
        model_path = os.path.join(ai_path, "models", "model.pkl")
        if not os.path.exists(model_path):
            raise RuntimeError(f"Không tìm thấy tệp model tại {model_path}. Hãy chạy train script trước.")

        with open(model_path, "rb") as f:
            bundle = pickle.load(f)
        forecaster = bundle["forecaster"]

        # 2. Gọi forecast & lưu (BE-10.2)
        st, segs, ods, bn = datagen.build_network()

        # Ánh xạ OD từ mạng lưới của AI với database
        valid_network_ods = []
        for od in ods:
            db_key = (od["origin"].upper(), od["dest"].upper(), od["seat_type"])
            if db_key in od_product_map:
                valid_network_ods.append(od)

        if not valid_network_ods:
            raise ValueError("Không tìm thấy sản phẩm OD khớp giữa cấu hình AI và database")

        # Dự báo nhu cầu GBDT
        from ai_service.app import _feature_rows

        feature_df = _feature_rows(valid_network_ods, service_date)
        pred_df = forecaster.predict(feature_df)

        # Phân phối point forecast qua 61 lead days (60 về 0)
        import numpy as np

        t = np.arange(60, -1, -1, dtype=float)
        w = np.exp(-t / 15.0)
        # Tet features check
        for yr, tet_date in {2024: date(2024, 2, 10), 2025: date(2025, 1, 29), 2026: date(2026, 2, 17)}.items():
            delta_tet = (tet_date - service_date).days
            if 0 < delta_tet <= 60:
                w += 0.5 * np.exp(-((t - 45) ** 2) / (2 * 64.0))
        w /= w.sum()
        weights = w.tolist()

        # Xóa các dự báo cũ của chuyến tàu này
        db.execute(
            text("""
            DELETE FROM demand_forecasts
            WHERE od_product_id IN (SELECT id FROM od_products WHERE trip_id = :trip_id)
        """),
            {"trip_id": trip_id},
        )

        # Tạo thời điểm forecast duy nhất
        forecast_at_dt = datetime.now(UTC)

        # Chuẩn bị danh sách tham số để bulk insert forecast
        forecast_params = []
        for r in pred_df.itertuples():
            od_id_val = r.od_id
            od_meta = next(x for x in valid_network_ods if x["od_id"] == od_id_val)
            db_key = (od_meta["origin"].upper(), od_meta["dest"].upper(), od_meta["seat_type"])
            db_od_id = od_product_map[db_key]

            lambda_hat = float(r.lambda_hat)
            p10 = float(r.p10)
            p50 = float(r.p50)
            p90 = float(r.p90)

            for lead in range(60, -1, -1):
                wt = weights[60 - lead]
                forecast_params.append(
                    {
                        "od_product_id": db_od_id,
                        "lead_days": lead,
                        "demand_point": lambda_hat * wt,
                        "demand_p10": p10 * wt,
                        "demand_p50": p50 * wt,
                        "demand_p90": p90 * wt,
                        "model_version": forecaster.version,
                        "forecast_at": forecast_at_dt,
                    }
                )

        if forecast_params:
            insert_forecast_query = text("""
                INSERT INTO demand_forecasts (
                    od_product_id, lead_days, demand_point, demand_p10, demand_p50, demand_p90, model_version, forecast_at
                ) VALUES (
                    :od_product_id, :lead_days, :demand_point, :demand_p10, :demand_p50, :demand_p90, :model_version, :forecast_at
                )
            """)
            db.execute(insert_forecast_query, forecast_params)

        # 3. Gọi optimize & lưu bid price/quota (BE-10.3)
        lam_dict = dict(zip(pred_df["od_id"], pred_df["lambda_hat"]))
        sol = opt.solve_bid_prices(valid_network_ods, lam_dict, nseg)

        # Tra cứu tồn kho chặng hiện hành
        inventory_rows = db.execute(
            text("SELECT segment_id, seat_type, remaining FROM segment_inventory WHERE segment_id = ANY(:seg_ids)"),
            {"seg_ids": list(segment_map.values())},
        ).fetchall()
        inventory_map = {(row[0], row[1]): int(row[2]) for row in inventory_rows}

        # Chuẩn bị danh sách tham số để bulk insert bid_prices
        bid_price_params = []
        bid_prices_count = 0
        for (seg_idx, seat_type), v in sol["bid_prices"].items():
            if seg_idx in segment_map:
                seg_id = segment_map[seg_idx]
                rem = inventory_map.get((seg_id, seat_type), 0)
                bid_price_params.append(
                    {
                        "segment_id": seg_id,
                        "seat_type": seat_type,
                        "bid_price": v,
                        "remaining_capacity": rem,
                        "run_version": run_version,
                    }
                )
                bid_prices_count += 1

        if bid_price_params:
            insert_bp_query = text("""
                INSERT INTO bid_prices (
                    segment_id, seat_type, bid_price, remaining_capacity, run_version, is_active, calculated_at
                ) VALUES (
                    :segment_id, :seat_type, :bid_price, :remaining_capacity, :run_version, FALSE, CURRENT_TIMESTAMP
                )
            """)
            db.execute(insert_bp_query, bid_price_params)

        # Chuẩn bị danh sách tham số để bulk insert quotas
        quota_params = []
        quotas_count = 0
        for od_id_val, q_val in sol["quotas"].items():
            od_meta = next(x for x in valid_network_ods if x["od_id"] == od_id_val)
            db_key = (od_meta["origin"].upper(), od_meta["dest"].upper(), od_meta["seat_type"])
            db_od_id = od_product_map[db_key]
            quota_params.append({"od_product_id": db_od_id, "quota": int(round(q_val)), "run_version": run_version})
            quotas_count += 1

        if quota_params:
            insert_quota_query = text("""
                INSERT INTO quotas (
                    od_product_id, quota, run_version, is_active, calculated_at
                ) VALUES (
                    :od_product_id, :quota, :run_version, FALSE, CURRENT_TIMESTAMP
                )
            """)
            db.execute(insert_quota_query, quota_params)

        # 4. HOÁN ĐỔI (SWAP) phiên bản active atomically (BE-10.5)
        # (demand_forecasts không cần update is_active do quản lý bằng cách delete-insert trực tiếp)

        # bid_prices swap
        db.execute(
            text("""
            UPDATE bid_prices
            SET is_active = FALSE
            WHERE segment_id IN (SELECT id FROM segments WHERE trip_id = :trip_id)
        """),
            {"trip_id": trip_id},
        )

        db.execute(
            text("""
            UPDATE bid_prices
            SET is_active = TRUE
            WHERE run_version = :run_version
        """),
            {"run_version": run_version},
        )

        # quotas swap
        db.execute(
            text("""
            UPDATE quotas
            SET is_active = FALSE
            WHERE od_product_id IN (SELECT id FROM od_products WHERE trip_id = :trip_id)
        """),
            {"trip_id": trip_id},
        )

        db.execute(
            text("""
            UPDATE quotas
            SET is_active = TRUE
            WHERE run_version = :run_version
        """),
            {"run_version": run_version},
        )

        # 5. Gọi price & lưu price_quote cho tất cả OD (BE-10.4)
        from backend.services.pricing_service import PricingService

        pricing_service = PricingService()
        for db_id in od_product_map.values():
            pricing_service.create_pricing_quote(od_product_id=db_id, db=db, run_version=run_version)

        # 6. Commit toàn bộ thay đổi thành công
        db.commit()

        return {
            "status": "success",
            "resolved_at": solved_at,
            "run_version": run_version,
            "quotas_updated_count": quotas_count,
            "bid_prices_updated_count": bid_prices_count,
            "message": "Đã chạy tối ưu hóa DLP và swap phiên bản active thành công.",
        }

    def get_run_versions(self, trip_id: int, db: Session) -> list[dict[str, Any]]:
        """Lấy danh sách các phiên bản chạy (run_version) của chuyến tàu."""
        # 1. Kiểm tra sự tồn tại của trip
        trip_exists = db.execute(text("SELECT id FROM trips WHERE id = :trip_id"), {"trip_id": trip_id}).fetchone()
        if not trip_exists:
            raise ValueError(f"Không tìm thấy chuyến tàu với ID {trip_id}")

        # 2. Truy vấn các run_version duy nhất trong bảng bid_prices cho chuyến tàu này
        query = text("""
            SELECT DISTINCT bp.run_version, MAX(bp.calculated_at) as calculated_at, bp.is_active
            FROM bid_prices bp
            JOIN segments s ON bp.segment_id = s.id
            WHERE s.trip_id = :trip_id
            GROUP BY bp.run_version, bp.is_active
            ORDER BY calculated_at DESC
        """)
        rows = db.execute(query, {"trip_id": trip_id}).fetchall()

        # Nhóm lại để tránh trùng lặp do is_active
        versions_map = {}
        for r in rows:
            version = r[0]
            calc_at = r[1].isoformat() if r[1] else None
            is_active = bool(r[2])

            if version not in versions_map:
                versions_map[version] = {"run_version": version, "calculated_at": calc_at, "is_active": is_active}
            elif is_active:
                versions_map[version]["is_active"] = True

        return sorted(list(versions_map.values()), key=lambda x: x["calculated_at"] or "", reverse=True)

    def rollback_to_version(self, trip_id: int, target_version: str, db: Session) -> dict[str, Any]:
        """Khôi phục (rollback) cấu hình tối ưu của chuyến tàu về một phiên bản trước đó."""
        # 1. Kiểm tra sự tồn tại của trip
        trip_exists = db.execute(text("SELECT id FROM trips WHERE id = :trip_id"), {"trip_id": trip_id}).fetchone()
        if not trip_exists:
            raise ValueError(f"Không tìm thấy chuyến tàu với ID {trip_id}")

        # 2. Xác minh xem target_version có tồn tại cho trip này không
        ver_check = db.execute(
            text("""
                SELECT COUNT(*) FROM bid_prices bp
                JOIN segments s ON bp.segment_id = s.id
                WHERE s.trip_id = :trip_id AND bp.run_version = :ver
            """),
            {"trip_id": trip_id, "ver": target_version},
        ).fetchone()

        if ver_check[0] == 0:
            raise ValueError(f"Không tìm thấy phiên bản tối ưu '{target_version}' cho chuyến tàu {trip_id}")

        # 3. Thực hiện hoán đổi (swap) phiên bản hoạt động trong một transaction
        # Deactivate all bid_prices of this trip
        db.execute(
            text("""
                UPDATE bid_prices
                SET is_active = FALSE
                WHERE segment_id IN (SELECT id FROM segments WHERE trip_id = :trip_id)
            """),
            {"trip_id": trip_id},
        )

        # Activate target version in bid_prices
        db.execute(
            text("""
                UPDATE bid_prices
                SET is_active = TRUE
                WHERE run_version = :ver
            """),
            {"ver": target_version},
        )

        # Deactivate all quotas of this trip
        db.execute(
            text("""
                UPDATE quotas
                SET is_active = FALSE
                WHERE od_product_id IN (SELECT id FROM od_products WHERE trip_id = :trip_id)
            """),
            {"trip_id": trip_id},
        )

        # Activate target version in quotas
        db.execute(
            text("""
                UPDATE quotas
                SET is_active = TRUE
                WHERE run_version = :ver
            """),
            {"ver": target_version},
        )

        db.commit()

        return {
            "status": "success",
            "trip_id": trip_id,
            "rolled_back_to": target_version,
            "message": f"Đã khôi phục thành công cấu hình tối ưu của chuyến tàu {trip_id} về phiên bản '{target_version}'.",
        }
