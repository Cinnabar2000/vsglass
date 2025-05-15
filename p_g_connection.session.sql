
ALTER TABLE orders ALTER COLUMN total_amount DROP NOT NULL;
ALTER TABLE orders ALTER COLUMN total_amount SET DEFAULT NULL;

-- Заполняем таблицу типов стекол
INSERT INTO glass_type (type_name, type_weight, type_height, is_mirror, price_per_sqm)
VALUES
    ('Прозрачное', 2100, 1600, FALSE, 1500),
    ('Матовое', 2200, 1600, FALSE, 1800),
    ('Зеркало', 2500, 1600, TRUE, 2200),
    ('Бронза', 2300, 1600, FALSE, 2000),
    ('Тонированное', 2150, 1600, FALSE, 1900),
    ('Сатин', 2250, 1600, FALSE, 2100),
    ('Узорчатое', 2400, 1600, FALSE, 2300),
    ('Закаленное', 2600, 1600, FALSE, 2500),
    ('Триплекс', 2800, 1600, FALSE, 3000),
    ('Энергосберегающее', 2300, 1600, FALSE, 2700);

-- Заполняем таблицу заказов (20 заказов)
INSERT INTO orders (customer_id, order_date, due_date, total_amount)
SELECT 
    (random() * 29 + 1)::int,
    CURRENT_DATE - (random() * 365)::int,
    CURRENT_DATE + (random() * 30 + 5)::int,
    CASE 
        WHEN random() > 0.1 THEN (random() * 50000 + 1000)::numeric(12,2)
        ELSE NULL -- 10% заказов будут с нулевой стоимостью
    END
FROM generate_series(1, 20);

-- Заполняем таблицу деталей (по 2-5 деталей на каждый заказ)
DO $$
DECLARE
    order_rec RECORD;
    detail_count INT;
    glass_type_id INT;
BEGIN
    FOR order_rec IN SELECT order_id FROM orders LOOP
        detail_count := (random() * 3 + 2)::int;
        
        FOR i IN 1..detail_count LOOP
            SELECT type_id INTO glass_type_id 
            FROM glass_type 
            ORDER BY random() 
            LIMIT 1;
            
            INSERT INTO detail (order_id, glass_type_id, width, height, quantity)
            VALUES (
                order_rec.order_id,
                glass_type_id,
                (random() * 1000 + 300)::numeric(8,2),
                (random() * 1000 + 300)::numeric(8,2),
                (random() * 4 + 1)::int
            );
        END LOOP;
    END LOOP;
END $$;

-- Обновляем общую сумму заказов на основе деталей (только для заказов с деталями)
UPDATE orders o
SET total_amount = (
    SELECT SUM(d.width * d.height * gt.price_per_sqm * d.quantity / 1000000)
    FROM detail d
    JOIN glass_type gt ON d.glass_type_id = gt.type_id
    WHERE d.order_id = o.order_id
)
WHERE EXISTS (
    SELECT 1 FROM detail WHERE order_id = o.order_id
);

-- Клиенты с 1 по 10
UPDATE client SET address = 'ул. Роз, д. 15, кв. 42', phone = '+79661112233' WHERE id = 1;
UPDATE client SET address = 'ул. Навагинская, д. 7', phone = '+79662223344' WHERE id = 2;
UPDATE clients SET address = 'ул. Виноградная, д. 25', phone = '+79663334455' WHERE id = 3;
UPDATE clients SET address = 'ул. Чайковского, д. 12', phone = '+79664445566' WHERE id = 4;
UPDATE clients SET address = 'ул. Горького, д. 34', phone = '+79665556677' WHERE id = 5;
UPDATE clients SET address = 'ул. Платановая, д. 8', phone = '+79666667788' WHERE id = 6;
UPDATE clients SET address = 'ул. Московская, д. 21', phone = '+79667778899' WHERE id = 7;
UPDATE clients SET address = 'ул. Юных Ленинцев, д. 3', phone = '+79668889900' WHERE id = 8;
-- У клиента с id=9 уже есть телефон, обновляем только адрес:
UPDATE clients SET address = 'ул. Конституции, д. 44' WHERE id = 9;
UPDATE clients SET address = 'ул. Донская, д. 17', phone = '+79669990011' WHERE id = 10;

-- Клиенты с 11 по 20
UPDATE clients SET address = 'ул. Красноармейская, д. 9', phone = '+79661010101' WHERE id = 11;
UPDATE clients SET address = 'ул. Параллельная, д. 5', phone = '+79662020202' WHERE id = 12;
UPDATE clients SET address = 'ул. Труда, д. 30', phone = '+79663030303' WHERE id = 13;
UPDATE clients SET address = 'ул. Декабристов, д. 11', phone = '+79664040404' WHERE id = 14;
UPDATE clients SET address = 'ул. Пирогова, д. 6', phone = '+79665050505' WHERE id = 15;
UPDATE clients SET address = 'ул. Цветной бульвар, д. 2', phone = '+79666060606' WHERE id = 16;
UPDATE clients SET address = 'ул. Чехова, д. 19', phone = '+79667070707' WHERE id = 17;
UPDATE clients SET address = 'ул. Воровского, д. 13', phone = '+79668080808' WHERE id = 18;
UPDATE clients SET address = 'ул. Пушкинская, д. 7', phone = '+79669090909' WHERE id = 19;
UPDATE clients SET address = 'ул. Нагорная, д. 22', phone = '+79661212121' WHERE id = 20;

-- Клиенты с 21 по 30
UPDATE clients SET address = 'ул. Курортный проспект, д. 72', phone = '+79662323232' WHERE id = 21;
UPDATE clients SET address = 'ул. Орджоникидзе, д. 10', phone = '+79663434343' WHERE id = 22;
UPDATE clients SET address = 'ул. Приморская, д. 15', phone = '+79664545454' WHERE id = 23;
UPDATE clients SET address = 'ул. Ленина, д. 41', phone = '+79665656565' WHERE id = 24;
UPDATE clients SET address = 'ул. Комсомольская, д. 3', phone = '+79666767676' WHERE id = 25;
UPDATE clients SET address = 'ул. Гагарина, д. 18', phone = '+79667878787' WHERE id = 26;
UPDATE clients SET address = 'ул. Садовая, д. 27', phone = '+79668989898' WHERE id = 27;
UPDATE clients SET address = 'ул. Победы, д. 5', phone = '+79669191919' WHERE id = 28;
UPDATE clients SET address = 'ул. Юных Ленинцев, д. 8', phone = '+79668282828' WHERE id = 29;
UPDATE clients SET address = 'ул. Донская, д. 31', phone = '+79667373737' WHERE id = 30;

-- Клиенты с 31 по 40
UPDATE clients SET address = 'ул. Виноградная, д. 14', phone = '+79666464646' WHERE id = 31;
UPDATE clients SET address = 'ул. Навагинская, д. 9', phone = '+79665555555' WHERE id = 32;
UPDATE clients SET address = 'ул. Горького, д. 12', phone = '+79664646464' WHERE id = 33;
UPDATE clients SET address = 'ул. Московская, д. 33', phone = '+79663737373' WHERE id = 34;
UPDATE clients SET address = 'ул. Чайковского, д. 7', phone = '+79662828282' WHERE id = 35;
UPDATE clients SET address = 'ул. Платановая, д. 11', phone = '+79661919191' WHERE id = 36;
UPDATE clients SET address = 'ул. Конституции, д. 22', phone = '+79660101010' WHERE id = 37;
UPDATE clients SET address = 'ул. Пирогова, д. 4', phone = '+79669292929' WHERE id = 38;
UPDATE clients SET address = 'ул. Декабристов, д. 6', phone = '+79668383838' WHERE id = 39;
UPDATE clients SET address = 'ул. Труда, д. 17', phone = '+79667474747' WHERE id = 40;