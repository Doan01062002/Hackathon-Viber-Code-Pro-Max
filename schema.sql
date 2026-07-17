-- SRRM MVP database schema (PostgreSQL)
-- Scope: tables and in-table constraints only. No seed data, views, functions, or triggers.

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
    seat_type       VARCHAR(30) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'available',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (trip_id, coach_no, seat_no),
    CHECK (status IN ('available', 'locked', 'maintenance'))
);

CREATE TABLE od_products (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trip_id             BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    origin_station_id   BIGINT NOT NULL REFERENCES stations(id),
    destination_station_id BIGINT NOT NULL REFERENCES stations(id),
    seat_type           VARCHAR(30) NOT NULL,
    fare_class          VARCHAR(30) NOT NULL DEFAULT 'standard',
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

CREATE TABLE bookings (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_code    VARCHAR(50) NOT NULL UNIQUE,
    od_product_id   BIGINT NOT NULL REFERENCES od_products(id),
    seat_id         BIGINT REFERENCES seats(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'confirmed',
    channel         VARCHAR(30),
    booked_price    NUMERIC(14,2) NOT NULL,
    booked_at       TIMESTAMPTZ NOT NULL,
    cancelled_at    TIMESTAMPTZ,
    refunded_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (status IN ('held', 'confirmed', 'cancelled', 'refunded')),
    CHECK (booked_price >= 0),
    CHECK (cancelled_at IS NULL OR cancelled_at >= booked_at),
    CHECK (refunded_at IS NULL OR refunded_at >= booked_at)
);

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
    seat_type       VARCHAR(30) NOT NULL,
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
