-- Migration: bảng vé ghép chặng (booking_groups, booking_group_items).
--
-- Dùng cho các database đã khởi tạo TRƯỚC khi hai bảng này được đưa vào schema.sql.
-- Database tạo mới từ schema.sql đã có sẵn hai bảng, chạy file này là no-op.
--
-- Chạy:  psql "$DATABASE_URL" -f scripts/migrate_booking_groups.sql
-- An toàn khi chạy lại nhiều lần (idempotent).

BEGIN;

CREATE TABLE IF NOT EXISTS booking_groups (
    id                      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    group_code              VARCHAR(50) NOT NULL UNIQUE,
    trip_id                 BIGINT NOT NULL REFERENCES trips(id),
    origin_station_id       BIGINT NOT NULL REFERENCES stations(id),
    destination_station_id  BIGINT NOT NULL REFERENCES stations(id),
    status                  VARCHAR(20) NOT NULL DEFAULT 'held',
    channel                 VARCHAR(30),
    total_price             NUMERIC(14,2) NOT NULL DEFAULT 0,
    transfer_count          SMALLINT NOT NULL,
    booked_at               TIMESTAMPTZ NOT NULL,
    expires_at              TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (status IN ('held', 'confirmed', 'cancelled', 'refunded')),
    CHECK (total_price >= 0),
    CHECK (transfer_count >= 1),
    CHECK (origin_station_id <> destination_station_id)
);

CREATE TABLE IF NOT EXISTS booking_group_items (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_group_id    BIGINT NOT NULL REFERENCES booking_groups(id) ON DELETE CASCADE,
    booking_id          BIGINT NOT NULL REFERENCES bookings(id),
    gap_combination_id  BIGINT REFERENCES gap_combinations(id) ON DELETE SET NULL,
    sequence_no         SMALLINT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (booking_id),
    UNIQUE (booking_group_id, sequence_no),
    CHECK (sequence_no >= 1)
);

CREATE INDEX IF NOT EXISTS ix_booking_group_items_booking
    ON booking_group_items (booking_id);

CREATE INDEX IF NOT EXISTS ix_booking_group_items_group
    ON booking_group_items (booking_group_id, sequence_no);

-- CREATE TRIGGER không có dạng IF NOT EXISTS, nên drop trước cho idempotent.
DROP TRIGGER IF EXISTS trg_booking_groups_updated_at ON booking_groups;
CREATE TRIGGER trg_booking_groups_updated_at
    BEFORE UPDATE ON booking_groups
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

COMMIT;
