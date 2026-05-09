-- ============================================================
-- DDL del Data Warehouse (modelo dimensional)
-- Proyecto Final – Gestión de Datos (UAX)
--
-- Ejecutar en DBeaver contra la BD: Proyecto_final
-- Crea un schema "dwh" con las tablas de hechos y dimensiones
-- ============================================================

-- Crear el schema si no existe
CREATE SCHEMA IF NOT EXISTS dwh;

-- ============================================================
-- DIMENSIONES
-- ============================================================

-- ------------------------------------------------------------
-- dim_date: Dimensión tiempo (generada, no viene del OLTP)
-- Cubre todo el rango de ventas: 2020-01-01 a 2025-12-31
-- ------------------------------------------------------------
DROP TABLE IF EXISTS dwh.dim_date CASCADE;
CREATE TABLE dwh.dim_date (
    date_id        integer     PRIMARY KEY,  -- formato YYYYMMDD (ej: 20230415)
    date           date        NOT NULL,
    year           smallint    NOT NULL,
    quarter        smallint    NOT NULL,     -- 1 a 4
    month          smallint    NOT NULL,     -- 1 a 12
    month_name     varchar(20) NOT NULL,     -- Enero, Febrero...
    week           smallint    NOT NULL,     -- semana del año (1-53)
    day_of_month   smallint    NOT NULL,     -- 1 a 31
    day_of_week    smallint    NOT NULL,     -- 1=Lunes, 7=Domingo
    day_name       varchar(20) NOT NULL,     -- Lunes, Martes...
    is_weekend     boolean     NOT NULL,
    is_month_end   boolean     NOT NULL
);

-- ------------------------------------------------------------
-- dim_customer: Dimensión cliente
-- ------------------------------------------------------------
DROP TABLE IF EXISTS dwh.dim_customer CASCADE;
CREATE TABLE dwh.dim_customer (
    customer_id         integer      PRIMARY KEY,
    first_name          varchar(100) NOT NULL,
    last_name           varchar(100) NOT NULL,
    last_name2          varchar(100),
    full_name           varchar(320) NOT NULL,  -- nombre completo concatenado
    email               varchar(150),
    phone               varchar(20),
    created_at          timestamp,
    first_purchase_date date,                   -- calculado desde sale
    last_purchase_date  date,                   -- calculado desde sale
    customer_age_days   integer   -- días desde primera compra hasta 2025-12-30 (R_t del CLTV)
);

-- ------------------------------------------------------------
-- dim_product: Dimensión producto
-- Enriquecida con unit_cost desde central_product
-- ------------------------------------------------------------
DROP TABLE IF EXISTS dwh.dim_product CASCADE;
CREATE TABLE dwh.dim_product (
    product_id   integer       PRIMARY KEY,
    name         varchar(200)  NOT NULL,
    category     varchar(100),
    manufacturer varchar(150),
    price        numeric(10,2) NOT NULL,   -- precio de venta en tienda
    unit_cost    numeric(10,2),            -- coste (de central_product, imputado si falta)
    margin_pct   numeric(6,2),             -- (price - unit_cost) / price * 100
    cost_imputed boolean DEFAULT false     -- true si el coste fue imputado
);

-- ------------------------------------------------------------
-- dim_store: Dimensión tienda
-- Enriquecida con zona geográfica desde city_zone
-- ------------------------------------------------------------
DROP TABLE IF EXISTS dwh.dim_store CASCADE;
CREATE TABLE dwh.dim_store (
    store_id         integer      PRIMARY KEY,
    name             varchar(100) NOT NULL,
    address          varchar(200),
    city             varchar(100),
    postal_code      varchar(10),
    district         varchar(100),          -- de city_zone
    area_type        varchar(20),           -- Céntrica / Periférica
    zone_orientation varchar(20),           -- Norte / Sur / Centro...
    latitude         numeric(9,6),
    longitude        numeric(9,6),
    opened_date      date
);

-- ------------------------------------------------------------
-- dim_offer: Dimensión oferta
-- Incluye fila especial offer_id = -1 para "sin oferta"
-- ------------------------------------------------------------
DROP TABLE IF EXISTS dwh.dim_offer CASCADE;
CREATE TABLE dwh.dim_offer (
    offer_id         integer       PRIMARY KEY,
    name             varchar(150)  NOT NULL,
    description      text,
    discount_percent numeric(5,2)  DEFAULT 0,
    start_date       date,
    end_date         date
);

-- Fila especial: "sin oferta"
INSERT INTO dwh.dim_offer (offer_id, name, discount_percent)
VALUES (-1, 'Sin oferta', 0.00);

-- ------------------------------------------------------------
-- dim_return_reason: Dimensión motivo de devolución
-- Incluye fila especial reason_id = -1 para "sin devolución"
-- ------------------------------------------------------------
DROP TABLE IF EXISTS dwh.dim_return_reason CASCADE;
CREATE TABLE dwh.dim_return_reason (
    reason_id integer     PRIMARY KEY,
    reason    text        NOT NULL,
    active    boolean     DEFAULT true
);

-- Fila especial: "sin devolución"
INSERT INTO dwh.dim_return_reason (reason_id, reason)
VALUES (-1, 'Sin devolución');

-- ============================================================
-- TABLA DE HECHOS
-- ============================================================

-- ------------------------------------------------------------
-- fact_sales: Tabla de hechos principal
-- Granularidad: una fila por línea de venta (sale_item)
-- ------------------------------------------------------------
DROP TABLE IF EXISTS dwh.fact_sales CASCADE;
CREATE TABLE dwh.fact_sales (
    -- Clave primaria
    sale_item_id    integer       PRIMARY KEY,

    -- Claves foráneas a dimensiones
    sale_id         integer       NOT NULL,
    customer_id     integer       NOT NULL REFERENCES dwh.dim_customer(customer_id),
    product_id      integer       NOT NULL REFERENCES dwh.dim_product(product_id),
    store_id        integer       NOT NULL REFERENCES dwh.dim_store(store_id),
    date_id         integer       NOT NULL REFERENCES dwh.dim_date(date_id),
    offer_id        integer       NOT NULL DEFAULT -1 REFERENCES dwh.dim_offer(offer_id),
    reason_id       integer       NOT NULL DEFAULT -1 REFERENCES dwh.dim_return_reason(reason_id),

    -- Métricas
    quantity        integer       NOT NULL,
    unit_price      numeric(10,2) NOT NULL,   -- precio pagado por unidad
    unit_cost       numeric(10,2),            -- coste unitario (de dim_product)
    subtotal        numeric(10,2) NOT NULL,   -- ingresos brutos (quantity * unit_price)
    discount_amount numeric(10,2) DEFAULT 0, -- descuento aplicado por oferta
    net_revenue     numeric(10,2),           -- subtotal - discount_amount
    margin          numeric(10,2),           -- net_revenue - (quantity * unit_cost)
    margin_pct      numeric(6,2),            -- margin / net_revenue * 100

    -- Flags de calidad
    has_return      boolean       DEFAULT false,
    total_corrected boolean       DEFAULT false  -- true si sale.total fue corregido
);

-- ============================================================
-- ÍNDICES para mejorar rendimiento de consultas analíticas
-- ============================================================
CREATE INDEX idx_fact_customer  ON dwh.fact_sales(customer_id);
CREATE INDEX idx_fact_product   ON dwh.fact_sales(product_id);
CREATE INDEX idx_fact_store     ON dwh.fact_sales(store_id);
CREATE INDEX idx_fact_date      ON dwh.fact_sales(date_id);
CREATE INDEX idx_fact_sale      ON dwh.fact_sales(sale_id);
CREATE INDEX idx_fact_offer     ON dwh.fact_sales(offer_id);
CREATE INDEX idx_fact_reason    ON dwh.fact_sales(reason_id);

-- ============================================================
-- VERIFICACIÓN: listar las tablas creadas
-- ============================================================
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'dwh'
ORDER BY table_name;
