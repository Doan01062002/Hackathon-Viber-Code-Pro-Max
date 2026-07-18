-- Deterministic PostgreSQL fixture for the backend integration suite.
-- This file is loaded only when SRRM_BOOTSTRAP_TEST_DB=1 and the database
-- passes the localhost + *_test safety guard in tests/conftest.py.

INSERT INTO stations (code, name, display_order)
VALUES
    ('HAN', 'Ha Noi', 1),
    ('PHL', 'Phu Ly', 2),
    ('NDI', 'Nam Dinh', 3),
    ('NBH', 'Ninh Binh', 4),
    ('THH', 'Thanh Hoa', 5),
    ('VIH', 'Vinh', 6),
    ('DHO', 'Dong Hoi', 7),
    ('DHA', 'Dong Ha', 8),
    ('HUE', 'Hue', 9),
    ('DAN', 'Da Nang', 10),
    ('TAK', 'Tam Ky', 11),
    ('QNG', 'Quang Ngai', 12),
    ('DTR', 'Dieu Tri', 13),
    ('TYH', 'Tuy Hoa', 14),
    ('NTG', 'Nha Trang', 15),
    ('TPC', 'Thap Cham', 16),
    ('BTH', 'Binh Thuan', 17),
    ('LKH', 'Long Khanh', 18),
    ('BHO', 'Bien Hoa', 19),
    ('SGO', 'Sai Gon', 20);

INSERT INTO trains (code, name)
VALUES ('SE1', 'Thong Nhat SE1');

INSERT INTO seat_types (code, name)
VALUES
    ('ngoi_mem', 'Ngoi mem dieu hoa'),
    ('giuong_nam_k6', 'Giuong nam khoang 6');

INSERT INTO fare_classes (code, name)
VALUES ('standard', 'Pho thong');

INSERT INTO calendar_features (service_date, season, weather)
VALUES
    ('2024-01-01', 'winter', 'mild'),
    ('2025-12-30', 'winter', 'mild');

INSERT INTO trips (
    train_id,
    service_date,
    origin_station_id,
    destination_station_id,
    departure_at,
    arrival_at
)
VALUES
    (1, '2024-01-01', 1, 20, '2024-01-01 08:00:00+07', '2024-01-02 14:00:00+07'),
    (1, '2025-12-30', 1, 20, '2025-12-30 08:00:00+07', '2025-12-31 14:00:00+07');

INSERT INTO segments (
    trip_id,
    sequence_no,
    origin_station_id,
    destination_station_id,
    departure_at,
    arrival_at,
    distance_km
)
SELECT
    trip.id,
    route.sequence_no,
    route.origin_station_id,
    route.destination_station_id,
    trip.departure_at + (route.sequence_no - 1) * INTERVAL '90 minutes',
    trip.departure_at + route.sequence_no * INTERVAL '90 minutes',
    route.distance_km
FROM trips AS trip
CROSS JOIN (
    VALUES
        (1, 1, 2, 56.0),
        (2, 2, 3, 31.0),
        (3, 3, 4, 28.0),
        (4, 4, 5, 60.0),
        (5, 5, 6, 144.0),
        (6, 6, 7, 203.0),
        (7, 7, 8, 100.0),
        (8, 8, 9, 66.0),
        (9, 9, 10, 103.0),
        (10, 10, 11, 74.0),
        (11, 11, 12, 63.0),
        (12, 12, 13, 168.0),
        (13, 13, 14, 102.0),
        (14, 14, 15, 117.0),
        (15, 15, 16, 93.0),
        (16, 16, 17, 143.0),
        (17, 17, 18, 86.0),
        (18, 18, 19, 57.0),
        (19, 19, 20, 32.0)
) AS route(sequence_no, origin_station_id, destination_station_id, distance_km)
ORDER BY trip.id, route.sequence_no;

INSERT INTO seats (trip_id, coach_no, seat_no, seat_type)
SELECT
    trip.id,
    '01',
    LPAD(seat_number::TEXT, 2, '0'),
    'ngoi_mem'
FROM trips AS trip
CROSS JOIN generate_series(1, 64) AS seat_number
ORDER BY trip.id, seat_number;

INSERT INTO seats (trip_id, coach_no, seat_no, seat_type)
SELECT
    trip.id,
    '02',
    LPAD(seat_number::TEXT, 2, '0'),
    'giuong_nam_k6'
FROM trips AS trip
CROSS JOIN generate_series(1, 42) AS seat_number
ORDER BY trip.id, seat_number;

INSERT INTO segment_capacities (segment_id, seat_type, capacity)
SELECT
    segment.id,
    seat_type.code,
    CASE seat_type.code WHEN 'ngoi_mem' THEN 64 ELSE 42 END
FROM segments AS segment
CROSS JOIN seat_types AS seat_type
ORDER BY segment.id, seat_type.code;

INSERT INTO segment_inventory (segment_id, seat_type, remaining)
SELECT
    capacity.segment_id,
    capacity.seat_type,
    capacity.capacity - CASE
        WHEN segment.sequence_no = 1 AND capacity.seat_type = 'ngoi_mem' THEN 1
        ELSE 0
    END
FROM segment_capacities AS capacity
JOIN segments AS segment ON segment.id = capacity.segment_id
ORDER BY capacity.segment_id, capacity.seat_type;

-- Keep product ids deterministic. Tests intentionally use product 1.
INSERT INTO od_products (
    trip_id,
    origin_station_id,
    destination_station_id,
    seat_type,
    base_price,
    distance_km
)
VALUES
    (1, 1, 2, 'ngoi_mem', 58000.0, 56.0),
    (1, 1, 2, 'giuong_nam_k6', 63000.0, 56.0),
    (1, 2, 10, 'ngoi_mem', 512000.0, 735.0),
    (1, 2, 10, 'giuong_nam_k6', 579000.0, 735.0),
    (1, 1, 10, 'ngoi_mem', 550000.0, 791.0),
    (1, 1, 10, 'giuong_nam_k6', 621000.0, 791.0),
    (2, 1, 2, 'ngoi_mem', 58000.0, 56.0),
    (2, 1, 2, 'giuong_nam_k6', 63000.0, 56.0),
    (2, 2, 10, 'ngoi_mem', 512000.0, 735.0),
    (2, 2, 10, 'giuong_nam_k6', 579000.0, 735.0),
    (2, 1, 10, 'ngoi_mem', 550000.0, 791.0),
    (2, 1, 10, 'giuong_nam_k6', 621000.0, 791.0);

INSERT INTO od_product_segments (od_product_id, segment_id)
SELECT product.id, segment.id
FROM od_products AS product
JOIN segments AS segment
  ON segment.trip_id = product.trip_id
 AND segment.sequence_no >= product.origin_station_id
 AND segment.sequence_no < product.destination_station_id
ORDER BY product.id, segment.sequence_no;

INSERT INTO bookings (
    booking_code,
    od_product_id,
    seat_id,
    status,
    channel,
    booked_price,
    booked_at
)
VALUES
    (
        'BK-SEED-TRIP-1',
        1,
        (SELECT id FROM seats WHERE trip_id = 1 AND coach_no = '01' ORDER BY id LIMIT 1),
        'confirmed',
        'web',
        58000.0,
        '2023-12-15 08:00:00+07'
    ),
    (
        'BK-SEED-TRIP-2',
        7,
        (SELECT id FROM seats WHERE trip_id = 2 AND coach_no = '01' ORDER BY id LIMIT 1),
        'confirmed',
        'web',
        58000.0,
        '2025-12-01 08:00:00+07'
    );
