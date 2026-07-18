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
    transfer_count          INTEGER NOT NULL DEFAULT 1,
    booked_at               TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at              TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (origin_station_id <> destination_station_id),
    CHECK (status IN ('held', 'confirmed', 'cancelled', 'refunded')),
    CHECK (total_price >= 0),
    CHECK (transfer_count >= 1),
    CHECK (expires_at IS NULL OR expires_at > booked_at)
);

CREATE TABLE IF NOT EXISTS booking_group_items (
    booking_group_id    BIGINT NOT NULL REFERENCES booking_groups(id) ON DELETE CASCADE,
    booking_id          BIGINT NOT NULL UNIQUE REFERENCES bookings(id) ON DELETE CASCADE,
    gap_combination_id  BIGINT NOT NULL REFERENCES gap_combinations(id),
    sequence_no         INTEGER NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (booking_group_id, booking_id),
    UNIQUE (booking_group_id, sequence_no),
    CHECK (sequence_no > 0)
);

ALTER TABLE booking_group_items
    ADD COLUMN IF NOT EXISTS gap_combination_id BIGINT REFERENCES gap_combinations(id);

CREATE INDEX IF NOT EXISTS ix_booking_groups_trip_status
    ON booking_groups (trip_id, status, booked_at);

CREATE INDEX IF NOT EXISTS ix_booking_group_items_group
    ON booking_group_items (booking_group_id, sequence_no);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_booking_groups_updated_at'
    ) THEN
        CREATE TRIGGER trg_booking_groups_updated_at
            BEFORE UPDATE ON booking_groups
            FOR EACH ROW
            EXECUTE FUNCTION set_updated_at();
    END IF;
END
$$;

COMMIT;
