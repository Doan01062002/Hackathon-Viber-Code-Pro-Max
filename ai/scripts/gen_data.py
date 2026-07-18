"""Sinh dữ liệu mô phỏng và XUẤT RA 21 BẢNG (CSV + JSON) đúng schema SRRM
(giống bộ seeds đã kiểm tra: bookings.csv, search_logs.csv, od_products.csv,
od_product_segments.csv, seats.csv, segments.csv, trips.csv, segment_capacities.csv,
segment_inventory.csv, calendar_features.csv, stations.json, trains.json,
seat_types.json, fare_classes.json).

Chạy:  python scripts/gen_data.py               # mặc định 2 năm
       python scripts/gen_data.py --days 60     # sinh ngắn để xem nhanh
Kết quả ghi vào:  out/seeds/
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import date, datetime, timedelta, timezone

import numpy as np
from ai_service import config as C
from ai_service import datagen

TZ = timezone(timedelta(hours=7))
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "out", "seeds")

# 20 ga (id, code, tên, km) — km khớp cấu hình, code/tên theo bộ seeds
STATIONS_OUT = [
    (1, "HAN", "Ha Noi", 0), (2, "PHL", "Phu Ly", 56), (3, "NDI", "Nam Dinh", 87),
    (4, "NBH", "Ninh Binh", 115), (5, "THH", "Thanh Hoa", 175), (6, "VIH", "Vinh", 319),
    (7, "DHO", "Dong Hoi", 522), (8, "DHA", "Dong Ha", 622), (9, "HUE", "Hue", 688),
    (10, "DAN", "Da Nang", 791), (11, "TAK", "Tam Ky", 865), (12, "QNG", "Quang Ngai", 928),
    (13, "DTR", "Dieu Tri (Quy Nhon)", 1096), (14, "TYH", "Tuy Hoa", 1198), (15, "NTG", "Nha Trang", 1315),
    (16, "TPC", "Thap Cham", 1408), (17, "BTH", "Binh Thuan (Muong Man)", 1551), (18, "LKH", "Long Khanh", 1637),
    (19, "BHO", "Bien Hoa", 1694), (20, "SGO", "Sai Gon", 1726),
]
# thời lượng 19 chặng (phút) — khớp lịch SE1 trong bộ seeds
DUR_MIN = [45, 30, 30, 75, 155, 265, 90, 70, 165, 95, 90, 240, 150, 60, 30, 180, 60, 30, 25]
DEP_HHMM = (22, 20)   # SE1 rời Hà Nội 22:20


def iso(dt):  # datetime -> ISO 8601 +07:00
    return dt.isoformat()


def round1k(x):
    return int(round(x / 1000.0)) * 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=730)
    ap.add_argument("--start", type=str, default="2024-01-01")
    args = ap.parse_args()
    start = date.fromisoformat(args.start)
    DAYS = args.days
    rng = np.random.default_rng(7)
    os.makedirs(OUT, exist_ok=True)

    st, segments_net, ods_net, bn = datagen.build_network()  # mạng tất định
    nseg = len(segments_net)

    # --- JSON danh mục ---
    json.dump([{"id": i, "code": c, "name": n, "display_order": i}
               for i, c, n, _ in STATIONS_OUT],
              open(os.path.join(OUT, "stations.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    json.dump([{"id": 1, "code": "SE1", "name": "Thong Nhat SE1", "is_active": True}],
              open(os.path.join(OUT, "trains.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump([{"code": "ngoi_mem", "name": "Ngoi mem dieu hoa", "is_active": True},
               {"code": "giuong_nam_k6", "name": "Giuong nam khoang 6", "is_active": True}],
              open(os.path.join(OUT, "seat_types.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump([{"code": "standard", "name": "Pho thong", "is_active": True}],
              open(os.path.join(OUT, "fare_classes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # --- mở writer CSV ---
    def w(name, header):
        f = open(os.path.join(OUT, name), "w", newline="", encoding="utf-8")
        wr = csv.writer(f)
        wr.writerow(header)
        return f, wr

    f_trip, wr_trip = w("trips.csv", ["id", "train_id", "service_date", "origin_station_id",
        "destination_station_id", "departure_at", "arrival_at", "status", "created_at", "updated_at"])
    f_seg, wr_seg = w("segments.csv", ["id", "trip_id", "sequence_no", "origin_station_id",
        "destination_station_id", "departure_at", "arrival_at", "distance_km", "created_at"])
    f_seat, wr_seat = w("seats.csv", ["id", "trip_id", "coach_no", "seat_no", "seat_type", "status", "created_at"])
    f_cap, wr_cap = w("segment_capacities.csv", ["segment_id", "seat_type", "capacity", "created_at", "updated_at"])
    f_inv, wr_inv = w("segment_inventory.csv", ["segment_id", "seat_type", "remaining", "updated_at"])
    f_od, wr_od = w("od_products.csv", ["id", "trip_id", "origin_station_id", "destination_station_id",
        "seat_type", "fare_class", "base_price", "distance_km", "is_active", "created_at", "updated_at"])
    f_ods, wr_ods = w("od_product_segments.csv", ["od_product_id", "segment_id"])
    f_bk, wr_bk = w("bookings.csv", ["id", "booking_code", "od_product_id", "seat_id", "status", "channel",
        "booked_price", "booked_at", "expires_at", "cancelled_at", "refunded_at", "created_at", "updated_at"])
    f_srch, wr_srch = w("search_logs.csv", ["id", "searched_at", "origin_station_id", "destination_station_id",
        "seat_type", "service_date", "result", "od_product_id", "channel", "created_at"])
    f_cal, wr_cal = w("calendar_features.csv", ["service_date", "is_holiday", "is_tet", "season",
        "weather", "local_event", "created_at", "updated_at"])

    # id counters
    trip_id = seg_id = seat_id = od_id = bk_id = srch_id = 0
    # thống kê
    tot_bk = tot_sold = 0
    month_demand = {m: [0.0, 0] for m in range(1, 13)}
    bottleneck_full_days = 0

    for t in range(DAYS):
        d = start + timedelta(days=t)
        f_hol, is_hol, is_tet = datagen.calendar_factor(d)
        season = ("spring" if d.month in (2, 3, 4) else "summer" if d.month in (5, 6, 7, 8)
                  else "autumn" if d.month in (9, 10, 11) else "winter")
        promo_day = rng.random() < C.PROMO_PROB
        weather = "rain" if d.month in C.RAINY_MONTHS else "mild"
        local_event = "promo" if promo_day else ""
        wr_cal.writerow([d.isoformat(), is_hol, is_tet, season, weather, local_event,
                         iso(datetime(d.year, d.month, d.day, tzinfo=TZ)),
                         iso(datetime(d.year, d.month, d.day, tzinfo=TZ))])

        # trip + lịch chặng
        trip_id += 1
        dep0 = datetime(d.year, d.month, d.day, DEP_HHMM[0], DEP_HHMM[1], tzinfo=TZ)
        cur = dep0
        seg_times = []
        seg_global = {}   # seg_idx -> global segment id
        for i in range(nseg):
            seg_id += 1
            arr = cur + timedelta(minutes=DUR_MIN[i])
            wr_seg.writerow([seg_id, trip_id, i + 1, i + 1, i + 2, iso(cur), iso(arr),
                             float(segments_net[i]["distance_km"]),
                             iso(dep0)])
            wr_cap.writerow([seg_id, "ngoi_mem", C.CAPACITY["ngoi_mem"], iso(dep0), iso(dep0)])
            wr_cap.writerow([seg_id, "giuong_nam_k6", C.CAPACITY["giuong_nam_k6"], iso(dep0), iso(dep0)])
            seg_global[i] = seg_id
            seg_times.append((cur, arr))
            cur = arr
        arr_final = cur
        wr_trip.writerow([trip_id, 1, d.isoformat(), 1, 20, iso(dep0), iso(arr_final),
                          "completed", iso(dep0), iso(dep0)])

        # seats (192 ngoi + 252 giuong)
        seat_base = {}
        for stype, ncoach, per in [("ngoi_mem", 3, 64), ("giuong_nam_k6", 6, 42)]:
            seat_base[stype] = seat_id + 1
            for k in range(C.CAPACITY[stype]):
                seat_id += 1
                wr_seat.writerow([seat_id, trip_id, f"{k // per + 1:02d}", f"{k % per + 1:02d}",
                                  stype, "available", iso(dep0)])

        # od_products (+ mapping) cho chuyến này
        od_global = {}   # network od index -> global od id
        for k, od in enumerate(ods_net):
            od_id += 1
            od_global[k] = od_id
            bp = round1k(20000 + C.PRICE_PER_KM[od["seat_type"]] * od["distance_km"])
            wr_od.writerow([od_id, trip_id, od["origin_idx"] + 1, od["dest_idx"] + 1,
                            od["seat_type"], "standard", bp, float(od["distance_km"]),
                            True, iso(dep0), iso(dep0)])
            for sidx in od["segments"]:
                wr_ods.writerow([od_id, seg_global[sidx]])

        # ---- mô phỏng nhu cầu -> bookings + search_logs ----
        remaining = {s: np.full(nseg, C.CAPACITY[s], int) for s in C.SEAT_TYPES}
        accepted = {s: [] for s in C.SEAT_TYPES}   # (o,d, od_global, price, is_cancel, booked_dt)
        weekend = 1.0 if d.weekday() >= 4 else 0.0
        promo_lift = C.PROMO_LIFT if promo_day else 1.0
        promo_disc = C.PROMO_DISCOUNT if promo_day else 1.0
        for k in rng.permutation(len(ods_net)):
            od = ods_net[k]
            oid = od_global[k]
            lam, *_ = datagen.lam_for(od, d)          # đã gồm chiều đi/về Tết + mùa mưa
            lam *= promo_lift
            demand = int(datagen._nb(rng, lam))
            month_demand[d.month][0] += demand
            month_demand[d.month][1] += 1
            if demand == 0:
                continue
            bp = round1k(20000 + C.PRICE_PER_KM[od["seat_type"]] * od["distance_km"])
            price = round1k(bp * promo_disc * (1 + 0.10 * weekend) * (1 + rng.uniform(-0.15, 0.20)))
            med = C.WTP_MEDIAN_MULT * bp
            w_ = rng.lognormal(np.log(med), C.WTP_SIGMA_LOG, size=demand)
            segs = od["segments"]
            stype = od["seat_type"]
            for wi in w_:
                # searched_at: theo lead time
                lead = min(int(rng.exponential(12)), 59)
                sdt = datetime(d.year, d.month, d.day, 12, 0, tzinfo=TZ) - timedelta(days=lead)
                cap_ok = remaining[stype][segs].min() > 0 if len(segs) else False
                if not cap_ok:
                    srch_id += 1
                    tot_sold += 1
                    wr_srch.writerow([srch_id, iso(sdt), od["origin_idx"] + 1, od["dest_idx"] + 1,
                                      stype, d.isoformat(), "sold_out", oid, "web", iso(sdt)])
                    continue
                # còn chỗ -> found
                srch_id += 1
                wr_srch.writerow([srch_id, iso(sdt), od["origin_idx"] + 1, od["dest_idx"] + 1,
                                  stype, d.isoformat(), "found", oid, "web", iso(sdt)])
                if wi >= price:   # mua
                    remaining[stype][segs] -= 1
                    is_cancel = rng.random() < C.CANCEL_RATE
                    accepted[stype].append((od["origin_idx"], od["dest_idx"], oid, price, is_cancel, sdt))

        # gán ghế offline (interval partitioning) + ghi bookings
        for stype in C.SEAT_TYPES:
            items = accepted[stype]
            order = sorted(range(len(items)), key=lambda x: (items[x][0], items[x][1]))
            seat_free = []      # free_from cho mỗi ghế đã dùng
            seat_idx_of = [0] * len(items)
            for idx in order:
                o, dd = items[idx][0], items[idx][1]
                placed = False
                for si in range(len(seat_free)):
                    if seat_free[si] <= o:
                        seat_free[si] = dd
                        seat_idx_of[idx] = si
                        placed = True
                        break
                if not placed:
                    seat_free.append(dd)
                    seat_idx_of[idx] = len(seat_free) - 1
            for idx, (o, dd, oid, price, is_cancel, sdt) in enumerate(items):
                bk_id += 1
                tot_bk += 1
                sid = seat_base[stype] + seat_idx_of[idx]
                status = "cancelled" if is_cancel else "confirmed"
                canc = iso(min(sdt + timedelta(days=2), datetime(d.year, d.month, d.day, tzinfo=TZ))) if is_cancel else ""
                wr_bk.writerow([bk_id, f"BK{bk_id:08d}", oid, sid, status, "web", price,
                                iso(sdt), "", canc, "", iso(sdt), iso(sdt)])

        # segment_inventory = còn lại sau mô phỏng
        for i in range(nseg):
            for stype in C.SEAT_TYPES:
                wr_inv.writerow([seg_global[i], stype, int(remaining[stype][i]), iso(arr_final)])
        # thống kê nút cổ chai (chặng bn, ngoi_mem)
        if remaining["ngoi_mem"][bn] == 0:
            bottleneck_full_days += 1

    for f in [f_trip, f_seg, f_seat, f_cap, f_inv, f_od, f_ods, f_bk, f_srch, f_cal]:
        f.close()

    # ---- báo cáo ----
    print(f"Đã sinh {DAYS} ngày (từ {start}) -> {OUT}")
    print("Files: trips, segments, seats, segment_capacities, segment_inventory, od_products,")
    print("       od_product_segments, bookings, search_logs, calendar_features (.csv) +")
    print("       stations, trains, seat_types, fare_classes (.json)")
    print(f"\nTổng bookings: {tot_bk:,} | sold_out searches: {tot_sold:,} "
          f"| sold_out/(bán+sold_out) = {100*tot_sold/max(tot_bk+tot_sold,1):.1f}%")
    print(f"Số ngày nút cổ chai Huế–ĐN cháy vé (ngồi mềm): {bottleneck_full_days}/{DAYS}")
    print("Nhu cầu TB/OD theo tháng (thấy đỉnh Tết tháng 1–2):")
    for m in range(1, 13):
        s, n = month_demand[m]
        if n:
            v = s / n
            print(f"  tháng {m:2d}: {v:5.2f} " + "█" * int(v * 8))


if __name__ == "__main__":
    main()
