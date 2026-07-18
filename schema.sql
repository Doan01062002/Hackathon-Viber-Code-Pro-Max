-- SRRM MVP database schema (PostgreSQL)
-- Scope: operational MVP tables, constraints, indexes, and updated_at triggers.
-- No seed data or views.

CREATE TABLE stations (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code            VARCHAR(20) NOT NULL UNIQUE,
    name            VARCHAR(120) NOT NULL,
    display_order   INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (display_order IS NULL OR display_order >= 0)
);

CREATE TABLE trains (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code            VARCHAR(30) NOT NULL UNIQUE,
    name            VARCHAR(120),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE seat_types (
    code            VARCHAR(30) PRIMARY KEY,
    name            VARCHAR(120) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fare_classes (
    code            VARCHAR(30) PRIMARY KEY,
    name            VARCHAR(120) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE calendar_features (
    service_date    DATE PRIMARY KEY,
    is_holiday      BOOLEAN NOT NULL DEFAULT FALSE,
    is_tet          BOOLEAN NOT NULL DEFAULT FALSE,
    season          VARCHAR(20),
    weather         VARCHAR(30),
    local_event     VARCHAR(120),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE trips (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    train_id            BIGINT NOT NULL REFERENCES trains(id),
    service_date        DATE NOT NULL,
    origin_station_id   BIGINT NOT NULL REFERENCES stations(id),
    destination_station_id BIGINT NOT NULL REFERENCES stations(id),
    departure_at        TIMESTAMPTZ NOT NULL,
    arrival_at          TIMESTAMPTZ NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (train_id, service_date),
    CHECK (origin_station_id <> destination_station_id),
    CHECK (arrival_at > departure_at),
    CHECK (status IN ('scheduled', 'boarding', 'departed', 'completed', 'cancelled'))
);

CREATE TABLE segments (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trip_id             BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    sequence_no         INTEGER NOT NULL,
    origin_station_id   BIGINT NOT NULL REFERENCES stations(id),
    destination_station_id BIGINT NOT NULL REFERENCES stations(id),
    departure_at        TIMESTAMPTZ NOT NULL,
    arrival_at          TIMESTAMPTZ NOT NULL,
    distance_km         NUMERIC(8,2) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (trip_id, sequence_no),
    UNIQUE (trip_id, origin_station_id, destination_station_id),
    CHECK (sequence_no > 0),
    CHECK (origin_station_id <> destination_station_id),
    CHECK (arrival_at > departure_at),
    CHECK (distance_km > 0)
);

CREATE TABLE seats (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trip_id         BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    coach_no        VARCHAR(10) NOT NULL,
    seat_no         VARCHAR(10) NOT NULL,
    seat_type       VARCHAR(30) NOT NULL REFERENCES seat_types(code),
    status          VARCHAR(20) NOT NULL DEFAULT 'available',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (trip_id, coach_no, seat_no),
    CHECK (status IN ('available', 'locked', 'maintenance'))
);

CREATE TABLE segment_capacities (
    segment_id      BIGINT NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    seat_type       VARCHAR(30) NOT NULL REFERENCES seat_types(code),
    capacity        INTEGER NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (segment_id, seat_type),
    CHECK (capacity >= 0)
);

CREATE TABLE segment_inventory (
    segment_id      BIGINT NOT NULL,
    seat_type       VARCHAR(30) NOT NULL,
    remaining       INTEGER NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (segment_id, seat_type),
    FOREIGN KEY (segment_id, seat_type)
        REFERENCES segment_capacities(segment_id, seat_type) ON DELETE CASCADE,
    CHECK (remaining >= 0)
);

CREATE TABLE od_products (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trip_id             BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    origin_station_id   BIGINT NOT NULL REFERENCES stations(id),
    destination_station_id BIGINT NOT NULL REFERENCES stations(id),
    seat_type           VARCHAR(30) NOT NULL REFERENCES seat_types(code),
    fare_class          VARCHAR(30) NOT NULL DEFAULT 'standard' REFERENCES fare_classes(code),
    base_price          NUMERIC(14,2) NOT NULL,
    distance_km         NUMERIC(8,2) NOT NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (trip_id, origin_station_id, destination_station_id, seat_type, fare_class),
    CHECK (origin_station_id <> destination_station_id),
    CHECK (base_price >= 0),
    CHECK (distance_km > 0)
);

CREATE TABLE od_product_segments (
    od_product_id   BIGINT NOT NULL REFERENCES od_products(id) ON DELETE CASCADE,
    segment_id      BIGINT NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    PRIMARY KEY (od_product_id, segment_id)
);

CREATE TABLE bookings (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_code    VARCHAR(50) NOT NULL UNIQUE,
    od_product_id   BIGINT NOT NULL REFERENCES od_products(id),
    seat_id         BIGINT REFERENCES seats(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'confirmed',
    channel         VARCHAR(30),
    booked_price    NUMERIC(14,2) NOT NULL,
    booked_at       TIMESTAMPTZ NOT NULL,
    expires_at      TIMESTAMPTZ,
    cancelled_at    TIMESTAMPTZ,
    refunded_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (status IN ('held', 'confirmed', 'cancelled', 'refunded')),
    CHECK (booked_price >= 0),
    CHECK (expires_at IS NULL OR expires_at > booked_at),
    CHECK (cancelled_at IS NULL OR cancelled_at >= booked_at),
    CHECK (refunded_at IS NULL OR refunded_at >= booked_at)
);

CREATE TABLE booking_groups (
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

CREATE TABLE booking_group_items (
    booking_group_id    BIGINT NOT NULL REFERENCES booking_groups(id) ON DELETE CASCADE,
    booking_id          BIGINT NOT NULL UNIQUE REFERENCES bookings(id) ON DELETE CASCADE,
    gap_combination_id  BIGINT NOT NULL,
    sequence_no         INTEGER NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (booking_group_id, booking_id),
    UNIQUE (booking_group_id, sequence_no),
    CHECK (sequence_no > 0)
);

CREATE TABLE search_logs (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    searched_at         TIMESTAMPTZ NOT NULL,
    origin_station_id   BIGINT NOT NULL REFERENCES stations(id),
    destination_station_id BIGINT NOT NULL REFERENCES stations(id),
    seat_type           VARCHAR(30) NOT NULL REFERENCES seat_types(code),
    service_date        DATE NOT NULL,
    result              VARCHAR(20) NOT NULL,
    od_product_id       BIGINT REFERENCES od_products(id) ON DELETE SET NULL,
    channel             VARCHAR(30),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (origin_station_id <> destination_station_id),
    CHECK (result IN ('found', 'sold_out', 'no_result'))
);

CREATE TABLE gap_combinations (
    id                      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seat_id                 BIGINT NOT NULL REFERENCES seats(id) ON DELETE CASCADE,
    from_station_id         BIGINT NOT NULL REFERENCES stations(id),
    to_station_id           BIGINT NOT NULL REFERENCES stations(id),
    suggested_od_product_id BIGINT REFERENCES od_products(id) ON DELETE SET NULL,
    run_version             VARCHAR(80) NOT NULL,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (seat_id, from_station_id, to_station_id, run_version),
    CHECK (from_station_id <> to_station_id)
);

ALTER TABLE booking_group_items
    ADD CONSTRAINT fk_booking_group_items_gap
    FOREIGN KEY (gap_combination_id) REFERENCES gap_combinations(id);

CREATE TABLE demand_forecasts (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    od_product_id       BIGINT NOT NULL REFERENCES od_products(id) ON DELETE CASCADE,
    forecast_at         TIMESTAMPTZ NOT NULL,
    lead_days           INTEGER NOT NULL,
    demand_point        NUMERIC(12,3) NOT NULL,
    demand_p10          NUMERIC(12,3),
    demand_p50          NUMERIC(12,3),
    demand_p90          NUMERIC(12,3),
    model_version       VARCHAR(80),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (od_product_id, forecast_at, lead_days),
    CHECK (lead_days >= 0),
    CHECK (demand_point >= 0),
    CHECK (demand_p10 IS NULL OR demand_p10 >= 0),
    CHECK (demand_p50 IS NULL OR demand_p50 >= 0),
    CHECK (demand_p90 IS NULL OR demand_p90 >= 0),
    CHECK (demand_p10 IS NULL OR demand_p50 IS NULL OR demand_p10 <= demand_p50),
    CHECK (demand_p50 IS NULL OR demand_p90 IS NULL OR demand_p50 <= demand_p90)
);

CREATE TABLE bid_prices (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    segment_id      BIGINT NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    seat_type       VARCHAR(30) NOT NULL REFERENCES seat_types(code),
    bid_price       NUMERIC(14,2) NOT NULL,
    remaining_capacity INTEGER NOT NULL,
    calculated_at   TIMESTAMPTZ NOT NULL,
    run_version     VARCHAR(80) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (segment_id, seat_type, run_version),
    CHECK (bid_price >= 0),
    CHECK (remaining_capacity >= 0)
);

CREATE TABLE quotas (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    od_product_id   BIGINT NOT NULL REFERENCES od_products(id) ON DELETE CASCADE,
    quota           INTEGER NOT NULL,
    calculated_at   TIMESTAMPTZ NOT NULL,
    run_version     VARCHAR(80) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (od_product_id, run_version),
    CHECK (quota >= 0)
);

CREATE TABLE price_policies (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    od_product_id       BIGINT REFERENCES od_products(id) ON DELETE CASCADE,
    name                VARCHAR(120) NOT NULL,
    min_price           NUMERIC(14,2) NOT NULL,
    max_price           NUMERIC(14,2) NOT NULL,
    max_step_change     NUMERIC(14,2) NOT NULL,
    valid_from          TIMESTAMPTZ NOT NULL,
    valid_to            TIMESTAMPTZ,
    status              VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_by          VARCHAR(120),
    approved_by         VARCHAR(120),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (min_price >= 0),
    CHECK (max_price >= min_price),
    CHECK (max_step_change >= 0),
    CHECK (valid_to IS NULL OR valid_to > valid_from),
    CHECK (status IN ('draft', 'active', 'inactive'))
);

CREATE TABLE price_quotes (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    od_product_id       BIGINT NOT NULL REFERENCES od_products(id),
    policy_id           BIGINT REFERENCES price_policies(id),
    opportunity_cost    NUMERIC(14,2) NOT NULL,
    proposed_price      NUMERIC(14,2) NOT NULL,
    final_price         NUMERIC(14,2) NOT NULL,
    decision            VARCHAR(20) NOT NULL,
    explanation         JSONB NOT NULL DEFAULT '{}'::JSONB,
    run_version         VARCHAR(80),
    quoted_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at          TIMESTAMPTZ,
    confirmed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (opportunity_cost >= 0),
    CHECK (proposed_price >= 0),
    CHECK (final_price >= 0),
    CHECK (decision IN ('accepted', 'rejected', 'blocked')),
    CHECK (expires_at IS NULL OR expires_at > quoted_at),
    CHECK (confirmed_at IS NULL OR confirmed_at >= quoted_at)
);

CREATE TABLE audit_logs (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor           VARCHAR(120) NOT NULL,
    action          VARCHAR(60) NOT NULL,
    entity_type     VARCHAR(60) NOT NULL,
    entity_id       VARCHAR(80),
    before_data     JSONB,
    after_data      JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_calendar_features_updated_at
    BEFORE UPDATE ON calendar_features
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_trips_updated_at
    BEFORE UPDATE ON trips
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_segment_capacities_updated_at
    BEFORE UPDATE ON segment_capacities
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_segment_inventory_updated_at
    BEFORE UPDATE ON segment_inventory
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_od_products_updated_at
    BEFORE UPDATE ON od_products
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_bookings_updated_at
    BEFORE UPDATE ON bookings
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_booking_groups_updated_at
    BEFORE UPDATE ON booking_groups
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_price_policies_updated_at
    BEFORE UPDATE ON price_policies
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE UNIQUE INDEX ux_bid_prices_active
    ON bid_prices (segment_id, seat_type)
    WHERE is_active = TRUE;

CREATE UNIQUE INDEX ux_quotas_active
    ON quotas (od_product_id)
    WHERE is_active = TRUE;

CREATE INDEX ix_search_logs_demand
    ON search_logs (service_date, origin_station_id, destination_station_id, seat_type, searched_at);

CREATE INDEX ix_od_product_segments_segment
    ON od_product_segments (segment_id, od_product_id);

CREATE INDEX ix_gap_combinations_lookup
    ON gap_combinations (from_station_id, to_station_id, is_active);

CREATE INDEX ix_booking_groups_trip_status
    ON booking_groups (trip_id, status, booked_at);

CREATE INDEX ix_booking_group_items_group
    ON booking_group_items (booking_group_id, sequence_no);
