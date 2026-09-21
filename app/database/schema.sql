-- Analytics schema for the AI Data Analyst Agent.
-- Dropped and recreated every time the seed script runs.

DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE categories (
    category_id   SERIAL PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE products (
    product_id   SERIAL PRIMARY KEY,
    product_name TEXT NOT NULL,
    category_id  INTEGER NOT NULL REFERENCES categories (category_id),
    unit_price   NUMERIC(10, 2) NOT NULL CHECK (unit_price > 0)
);

CREATE TABLE customers (
    customer_id   SERIAL PRIMARY KEY,
    customer_name TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    region        TEXT NOT NULL CHECK (region IN ('North', 'South', 'East', 'West')),
    signup_date   DATE NOT NULL
);

CREATE TABLE orders (
    order_id    SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (customer_id),
    order_date  DATE NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('completed', 'cancelled', 'refunded'))
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id      INTEGER NOT NULL REFERENCES orders (order_id),
    product_id    INTEGER NOT NULL REFERENCES products (product_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    NUMERIC(10, 2) NOT NULL,
    discount_pct  NUMERIC(4, 3) NOT NULL DEFAULT 0 CHECK (discount_pct >= 0 AND discount_pct < 1)
);

-- Indexes on the columns an analyst filters, groups and joins on most.
CREATE INDEX idx_orders_order_date ON orders (order_date);
CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_order_items_order ON order_items (order_id);
CREATE INDEX idx_order_items_product ON order_items (product_id);
CREATE INDEX idx_products_category ON products (category_id);

-- Comments are documentation the agent can read through the schema tool.
COMMENT ON TABLE orders IS 'One row per customer order.';
COMMENT ON COLUMN orders.status IS 'completed, cancelled or refunded. Revenue analysis must filter on status = ''completed''.';
COMMENT ON COLUMN order_items.unit_price IS 'Price per unit paid at order time; can differ from products.unit_price.';
COMMENT ON COLUMN order_items.discount_pct IS 'Line discount as a fraction (0.05 = 5 percent). Line revenue = quantity * unit_price * (1 - discount_pct).';
COMMENT ON COLUMN customers.region IS 'Sales region: North, South, East or West.';