-- Создаем таблицу клиентов
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    address TEXT,
    phone_number VARCHAR(20)
);

-- Создаем таблицу типов стекол
CREATE TABLE glass_type (
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(30) NOT NULL DEFAULT 'NEW TYPE',
    type_weight NUMERIC(8, 2) NOT NULL DEFAULT 2100,
    type_height NUMERIC(8, 2) NOT NULL DEFAULT 1600,
    is_mirror BOOLEAN,
    price_per_sqm NUMERIC(10, 2) NOT NULL DEFAULT 0
);

-- Создаем таблицу заказов
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_orders_customers FOREIGN KEY (customer_id) 
        REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- Создаем таблицу деталей заказов
CREATE TABLE detail (
    detail_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    glass_type_id INTEGER NOT NULL,
    width NUMERIC(8, 2) NOT NULL,
    height NUMERIC(8, 2) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_detail_orders FOREIGN KEY (order_id) 
        REFERENCES orders(order_id) ON DELETE CASCADE,
    CONSTRAINT fk_detail_glass_type FOREIGN KEY (glass_type_id) 
        REFERENCES glass_type(type_id)
);

-- Создаем индексы для ускорения запросов
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_detail_order_id ON detail(order_id);
CREATE INDEX idx_detail_glass_type_id ON detail(glass_type_id);