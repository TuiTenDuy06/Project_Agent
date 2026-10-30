CREATE TABLE stores (
    id          SERIAL PRIMARY KEY,
    code        TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    address     TEXT NOT NULL,
    district    TEXT NOT NULL,
    city        TEXT NOT NULL,
    open_time   TIME NOT NULL,
    close_time  TIME NOT NULL,
    phone       TEXT
);

CREATE TABLE products (
    id        SERIAL PRIMARY KEY,
    sku       TEXT UNIQUE NOT NULL,
    name      TEXT NOT NULL,
    category  TEXT NOT NULL,
    price     INTEGER NOT NULL CHECK (price >= 0)  -- đơn vị: đồng
);

CREATE TABLE inventory (
    store_id    INTEGER NOT NULL REFERENCES stores(id),
    product_id  INTEGER NOT NULL REFERENCES products(id),
    quantity    INTEGER NOT NULL CHECK (quantity >= 0),
    PRIMARY KEY (store_id, product_id)
);

CREATE TABLE promotions (
    id           SERIAL PRIMARY KEY,
    title        TEXT NOT NULL,
    description  TEXT NOT NULL,
    start_date   DATE NOT NULL,
    end_date     DATE NOT NULL CHECK (end_date >= start_date)
);
