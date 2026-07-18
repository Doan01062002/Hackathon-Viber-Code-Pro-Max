from datetime import date, datetime, timezone
UTC = timezone.utc
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from ai_service import datagen
from ai_service import optimization as opt
from ai_service.engine import MODEL_PATH, feature_rows, get_engine


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

        # Lấy danh sách segments của chuyến tàu (đọc trước OD vì chuỗi ga suy ra từ đây).
        segments_rows = db.execute(
            text("""
                SELECT id, sequence_no, origin_station_id, destination_station_id
                FROM segments
                WHERE trip_id = :trip_id
                ORDER BY sequence_no ASC
            """),
            {"trip_id": trip_id},
        ).fetchall()
        segment_map = {i: row[0] for i, row in enumerate(segments_rows)}
        nseg = len(segments_rows)

        if not segments_rows:
            raise ValueError(f"Chuyến tàu {trip_id} không có chặng nào")

        # Chuỗi ga 0-based của chuyến: idx 0 = ga đi chặng đầu, idx i+1 = ga đến chặng thứ i.
        station_ids = [segments_rows[0][2]] + [row[3] for row in segments_rows]
        idx_of_station = {station_id: i for i, station_id in enumerate(station_ids)}

        # Ánh xạ OD theo VỊ TRÍ ga dọc tuyến, không theo mã ga.
        #
        # Trước đây chỗ này ghép bằng chuỗi (origin_code, dest_code, seat_type). Mã ga của
        # ai_service/config.py và của bảng stations viết khác nhau ở 11/20 ga (HN vs HAN,
        # DNA vs DAN, SGN vs SGO, ...) nên chỉ 16/198 OD khớp được. Hệ quả: DLP chỉ nạp 8%
        # nhu cầu, không chặng nào chạm trần sức chứa, bid price = 0 toàn tuyến và Khối 3
        # không bao giờ surge. Hai bên xếp ga cùng thứ tự Bắc–Nam nên ghép theo chỉ số là
        # đúng và không phụ thuộc cách đặt mã.
        od_product_map = {}
        for r in od_rows:
            origin_idx = idx_of_station.get(r["origin_station_id"])
            dest_idx = idx_of_station.get(r["destination_station_id"])
            if origin_idx is None or dest_idx is None:
                continue
            od_product_map[(origin_idx, dest_idx, r["seat_type"])] = r["od_product_id"]

        # Chuẩn bị run_version duy nhất
        run_version = "ver-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        solved_at = datetime.now(UTC).isoformat()

        # Dùng chung forecaster của engine singleton — trước đây chỗ này tự pickle.load
        # model.pkl lần nữa, khiến model nằm trong RAM hai bản trong cùng process.
        forecaster = get_engine().forecaster
        if forecaster is None:
            raise RuntimeError(f"Không tìm thấy tệp model tại {MODEL_PATH}. Hãy chạy train script trước.")

        # 2. Gọi forecast & lưu (BE-10.2)
        st, segs, ods, bn = datagen.build_network()

        # Mạng lưới AI và chuyến trong DB phải cùng số ga thì chỉ số mới có nghĩa như nhau.
        if len(st.code) != len(station_ids):
            raise ValueError(
                f"Mạng lưới AI có {len(st.code)} ga nhưng chuyến {trip_id} có {len(station_ids)} ga "
                "— không ánh xạ được OD theo vị trí."
            )

        # Ánh xạ OD từ mạng lưới của AI với database
        valid_network_ods = []
        for od in ods:
            if (od["origin_idx"], od["dest_idx"], od["seat_type"]) in od_product_map:
                valid_network_ods.append(od)

        if not valid_network_ods:
            raise ValueError("Không tìm thấy sản phẩm OD khớp giữa cấu hình AI và database")

        # Dự báo nhu cầu GBDT
        feature_df = feature_rows(valid_network_ods, service_date)
        pred_df = forecaster.predict(feature_df)

        weights = self._lead_day_weights(service_date)

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
            db_od_id = od_product_map[(od_meta["origin_idx"], od_meta["dest_idx"], od_meta["seat_type"])]

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
            db_od_id = od_product_map[(od_meta["origin_idx"], od_meta["dest_idx"], od_meta["seat_type"])]
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

        # 3b. Khối 2 Lớp B — gán ghế + ghép đoạn trống (FR2.5)
        gap_count = self._persist_gap_combinations(
            trip_id=trip_id,
            segments_rows=segments_rows,
            run_version=run_version,
            db=db,
        )

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

        # gap_combinations swap
        db.execute(
            text("""
            UPDATE gap_combinations
            SET is_active = FALSE
            WHERE seat_id IN (SELECT id FROM seats WHERE trip_id = :trip_id)
        """),
            {"trip_id": trip_id},
        )

        db.execute(
            text("""
            UPDATE gap_combinations
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
            "gap_combinations_count": gap_count,
            "message": "Đã chạy tối ưu hóa DLP và swap phiên bản active thành công.",
        }

    def _lead_day_weights(self, service_date: date) -> list[float]:
        """Tỉ lệ nhu cầu phát sinh ở từng lead day, chỉ số 0 ứng với lead 60 ... 60 ứng với lead 0.

        Dùng đường cong đặt vé ĐÃ TRAIN (fit từ lead time thật, lưu trong model.pkl). Trước
        đây chỗ này tự viết lại `exp(-lead/15)` — đúng bằng đường LÝ THUYẾT
        `booking_curve.fit_theoretical(60, 15)`, thứ mà module đó ghi rõ là chỉ dùng khi
        chưa có lead time thật. Đường học được lệch đáng kể: ở lead 14 mới đặt ~28.6% chứ
        không phải ~39.3% như đường lý thuyết.

        `curve[τ]` = tỉ lệ vé đã đặt xong khi còn τ ngày (giảm dần theo τ, curve[0] = 1),
        nên phần phát sinh đúng vào ngày còn τ ngày là `curve[τ] - curve[τ+1]`. Tổng 61 mốc
        telescoping về `curve[0] = 1`.
        """
        import numpy as np

        curve = getattr(get_engine(), "booking_curve", None)
        if curve is not None:
            c = np.asarray(curve.curve, dtype=float)[: 60 + 2]
            if len(c) < 62:
                c = np.concatenate([c, np.zeros(62 - len(c))])
            # increments[lead] = c[lead] - c[lead + 1]
            increments = np.clip(c[:61] - c[1:62], 0.0, None)
        else:
            # Chưa có model: quay về đường lý thuyết như cũ.
            increments = np.exp(-np.arange(61, dtype=float) / 15.0)

        # Cao điểm Tết: khách đặt sớm hơn thường lệ. Đường cong trên là trung bình toàn cục
        # nên không bắt được hiệu ứng này — giữ lại phần nhô quanh lead 45 như bản trước.
        for tet_date in (date(2024, 2, 10), date(2025, 1, 29), date(2026, 2, 17)):
            delta_tet = (tet_date - service_date).days
            if 0 < delta_tet <= 60:
                leads = np.arange(61, dtype=float)
                increments = increments + 0.5 * increments.max() * np.exp(-((leads - 45) ** 2) / (2 * 64.0))
                break

        total = increments.sum()
        if total <= 0:
            increments = np.full(61, 1.0 / 61)
        else:
            increments = increments / total

        # Đảo về thứ tự vị trí mà chỗ gọi dùng: index 0 = lead 60, index 60 = lead 0.
        return increments[::-1].tolist()

    def _persist_gap_combinations(
        self, trip_id: int, segments_rows: list, run_version: str, db: Session
    ) -> int:
        """Khối 2 Lớp B — gán ghế (interval partitioning) rồi ghép đoạn trống, ghi gap_combinations.

        Khác Lớp A (chạy trên mạng lưới mô phỏng của AI rồi ánh xạ ngược về DB), Lớp B chạy
        thẳng trên dữ liệu DB: booking thật, ghế thật, OD thật. Nhờ vậy `od_id` truyền cho AI
        chính là `od_products.id`, không cần bảng ánh xạ nào.

        AI đánh số ga theo chỉ số 0-based dọc tuyến; ở đây chỉ số đó được suy ra từ chuỗi
        segments của chuyến (sequence_no tăng dần), nên không phụ thuộc mạng 20 ga cố định
        trong ai_service/config.py.
        """
        if not segments_rows:
            return 0

        # Chuỗi ga của chuyến: idx 0 = ga đi của chặng đầu, idx i+1 = ga đến của chặng thứ i.
        station_ids = [segments_rows[0][2]] + [row[3] for row in segments_rows]
        idx_of_station = {station_id: i for i, station_id in enumerate(station_ids)}
        nstations = len(station_ids)

        # Ghế thật của chuyến. Ghế khóa/bảo trì xếp TRƯỚC để khớp với assign_seats — hàm đó
        # dựng sẵn các ghế locked ở đầu danh sách rồi mới gán booking vào phần còn lại.
        seat_rows = db.execute(
            text("""
                SELECT id, seat_type, status
                FROM seats
                WHERE trip_id = :trip_id
                ORDER BY seat_type, (status <> 'available') DESC, coach_no, seat_no
            """),
            {"trip_id": trip_id},
        ).fetchall()

        seat_ids_by_type: dict[str, list[int]] = {}
        locked_seat_count: dict[str, int] = {}
        for seat_id, seat_type, status in seat_rows:
            seat_ids_by_type.setdefault(seat_type, []).append(seat_id)
            if status != "available":
                locked_seat_count[seat_type] = locked_seat_count.get(seat_type, 0) + 1

        if not seat_ids_by_type:
            return 0

        # Booking đang giữ chỗ -> khoảng [origin_idx, dest_idx) mà AI cần.
        booking_rows = db.execute(
            text("""
                SELECT o.origin_station_id, o.destination_station_id, o.seat_type
                FROM bookings b
                JOIN od_products o ON b.od_product_id = o.id
                WHERE o.trip_id = :trip_id AND b.status IN ('confirmed', 'held')
            """),
            {"trip_id": trip_id},
        ).fetchall()

        bookings = [
            {
                "origin_idx": idx_of_station[origin_id],
                "dest_idx": idx_of_station[dest_id],
                "seat_type": seat_type,
            }
            for origin_id, dest_id, seat_type in booking_rows
            if origin_id in idx_of_station and dest_id in idx_of_station
        ]

        # OD đang mở bán -> ứng viên lấp vào đoạn trống.
        od_rows = db.execute(
            text("""
                SELECT id, origin_station_id, destination_station_id, seat_type
                FROM od_products
                WHERE trip_id = :trip_id AND is_active = TRUE
            """),
            {"trip_id": trip_id},
        ).fetchall()

        sellable_ods = [
            {
                "od_id": od_id,
                "origin_idx": idx_of_station[origin_id],
                "dest_idx": idx_of_station[dest_id],
                "seat_type": seat_type,
            }
            for od_id, origin_id, dest_id, seat_type in od_rows
            if origin_id in idx_of_station and dest_id in idx_of_station
        ]

        seat_plan = opt.assign_seats(bookings, locked_seat_count=locked_seat_count)
        gaps = opt.find_gap_combinations(seat_plan, sellable_ods, nstations)

        # Xóa gợi ý cũ để bảng không phình theo mỗi lần chạy (bid_prices/quotas giữ lịch sử
        # phục vụ rollback, còn gap_combinations chỉ có ý nghĩa với thế trận ghế hiện tại).
        db.execute(
            text("DELETE FROM gap_combinations WHERE seat_id IN (SELECT id FROM seats WHERE trip_id = :trip_id)"),
            {"trip_id": trip_id},
        )

        gap_params = []
        for gap in gaps:
            seat_ids = seat_ids_by_type.get(gap["seat_type"], [])
            # assign_seats có thể cần nhiều ghế hơn số ghế thật khi booking chồng lấn vượt
            # sức chứa; những ghế ảo đó không có hàng trong bảng seats nên bỏ qua.
            if gap["seat_index"] >= len(seat_ids):
                continue
            gap_params.append(
                {
                    "seat_id": seat_ids[gap["seat_index"]],
                    "from_station_id": station_ids[gap["from_idx"]],
                    "to_station_id": station_ids[gap["to_idx"]],
                    "suggested_od_product_id": gap["suggest_od_id"],
                    "run_version": run_version,
                }
            )

        if gap_params:
            db.execute(
                text("""
                    INSERT INTO gap_combinations (
                        seat_id, from_station_id, to_station_id, suggested_od_product_id, run_version, is_active
                    ) VALUES (
                        :seat_id, :from_station_id, :to_station_id, :suggested_od_product_id, :run_version, FALSE
                    )
                """),
                gap_params,
            )

        return len(gap_params)

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
