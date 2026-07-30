-- Sample data so the app's dropdowns aren't empty on first run.

INSERT INTO users (name) VALUES
    ('Aarav Shrestha'),
    ('Priya Gurung'),
    ('Bikash Thapa');

INSERT INTO admin (name) VALUES
    ('Admin One');

INSERT INTO driver (name, driver_status) VALUES
    ('Ramesh KC', 'ready'),
    ('Sita Lama', 'ready'),
    ('Hari Bahadur', 'ready');

INSERT INTO vehicles (driver_id, vec_type, vechile_status) VALUES
    (1, 'bike', 'active'),
    (2, 'car', 'active'),
    (3, 'bus', 'active');
