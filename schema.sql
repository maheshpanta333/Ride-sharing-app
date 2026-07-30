-- eJatra Ride-Sharing schema
-- Reverse-engineered from the queries in app.py — column names (including
-- the typos "vechile_status", "transcation_code", "paidd_from") match
-- exactly what app.py expects, so don't "fix" them without updating app.py too.

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE admin (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE driver (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    driver_status VARCHAR(20) NOT NULL DEFAULT 'offline'
        CHECK (driver_status IN ('ready', 'busy', 'offline', 'driving'))
);

CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    driver_id INTEGER NOT NULL REFERENCES driver(id) ON DELETE CASCADE,
    vec_type VARCHAR(20) NOT NULL CHECK (vec_type IN ('bike', 'car', 'bus')),
    vechile_status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (vechile_status IN ('active', 'inactive'))
);

CREATE TABLE trip (
    trip_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    driver_id INTEGER NOT NULL REFERENCES driver(id),
    pickup_address VARCHAR(255) NOT NULL,
    drop_off VARCHAR(255) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    vehicle_used INTEGER REFERENCES vehicles(id),
    status VARCHAR(20) NOT NULL DEFAULT 'ongoing'
        CHECK (status IN ('ongoing', 'completed', 'cancelled'))
);

CREATE TABLE payment (
    id SERIAL PRIMARY KEY,
    trip_instance INTEGER NOT NULL REFERENCES trip(trip_id),
    transcation_code VARCHAR(50) NOT NULL,
    paidd_from VARCHAR(20) NOT NULL CHECK (paidd_from IN ('esewa', 'khalti')),
    paid_at TIMESTAMP NOT NULL
);

CREATE TABLE complaints (
    id SERIAL PRIMARY KEY,
    complaint_by VARCHAR(20) NOT NULL CHECK (complaint_by IN ('passenger', 'rider')),
    trip_id INTEGER NOT NULL REFERENCES trip(trip_id),
    complaint TEXT NOT NULL,
    response TEXT,
    admin_assigned INTEGER REFERENCES admin(id)
);
