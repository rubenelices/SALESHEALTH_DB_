![SalesHealth Analytics](sales_health.png)

# SalesHealth Analytics

Proyecto final de **Gestión de Datos** (3º Ingeniería Matemática · UAX) centrado en la construcción de un entorno analítico completo sobre una empresa ficticia de productos de salud: desde datos fuente en JSON y un modelo OLTP en PostgreSQL hasta un **Data Warehouse**, métricas de cliente (**CLTV**), segmentación **RFM**, **PCA + clustering** y un **dashboard interactivo en Streamlit**.

## Dashboard en vivo

**[https://saleshealthdb-rubenelices.streamlit.app/](https://saleshealthdb-rubenelices.streamlit.app/)**

El dashboard está desplegado en Streamlit Cloud y es navegable sin necesidad de instalar nada. Incluye KPIs ejecutivos, análisis CLTV, RFM, clustering y ficha individual de cliente.

---

## Qué hace el proyecto

- Modela y documenta la base de datos operacional de ventas.
- Diseña un **esquema estrella** para análisis.
- Implementa un proceso **ETL OLTP → DWH**.
- Calcula el **CLTV** por cliente y lo segmenta por valor.
- Genera segmentación **RFM** y perfiles de negocio.
- Aplica **PCA + K-Means** para descubrir segmentos automáticos.
- Expone los resultados en un **dashboard** navegable.

## Dataset y contexto

| Concepto | Valor |
|---|---|
| Archivos fuente | 17 JSON |
| Tablas OLTP (schema `public`) | 17 |
| Tablas DWH (schema `dwh`) | 7 (1 fact + 6 dims) |
| Clientes | 5.750 |
| Ventas (cabeceras) | 20.000 |
| Líneas de venta | 42.555 |
| Productos | 50 |
| Tiendas | 20 (todas en Madrid) |
| Período analizado | 2020-01-01 a 2025-12-30 |
| Ingresos totales | 9.678.678,67 € |

## Arquitectura del pipeline

```text
JSON fuente
   →
PostgreSQL OLTP  (schema public — 17 tablas)
   →
ETL  (03_etl.ipynb)
   →
Data Warehouse  (schema dwh — modelo estrella)
   →
CLTV + RFM + PCA/Clustering
   →
Dashboard Streamlit
```

## Modelo de datos

El proyecto incluye **dos modelos** documentados como diagramas ER:

- **OLTP normalizado (3FN)** — [`saleshealth_schema.dbml`](saleshealth_schema.dbml) — 17 tablas que reflejan los JSON originales.
- **Data Warehouse en estrella** — [`saleshealth_dwh_schema.dbml`](saleshealth_dwh_schema.dbml) — 1 tabla de hechos (`fact_sales`) + 6 dimensiones.

Granularidad de `fact_sales`: **una fila por línea de venta** (42.555 filas).

Dimensiones:
- `dim_date` (2.191 filas) · `dim_customer` (5.750) · `dim_product` (50) · `dim_store` (20) · `dim_offer` · `dim_return_reason`

## Estructura del repositorio

```text
.
├── JSON/                          # Datos fuente originales (17 archivos)
├── 01_eda.ipynb                   # Fase 1 — Exploración y calidad de datos
├── 02_ddl_dwh.sql                 # Fase 2 — DDL del Data Warehouse
├── 03_etl.ipynb                   # Fase 4 — ETL OLTP → DWH
├── 04_cltv.ipynb                  # Fase 5 — Cálculo y análisis de CLTV
├── 04b_features_diversidad.ipynb  # Features adicionales para clustering
├── 05_pca_clustering.ipynb        # Fase 6 — PCA + K-Means
├── app.py                         # Fase 7 — Dashboard Streamlit (entry point)
├── pages/                         # Páginas del dashboard
│   ├── 1_KPIs.py · 2_CLTV.py · 3_RFM.py
│   └── 4_Clustering.py · 5_Cliente.py · 6_Ventas.py
├── utils/                         # Lógica común del dashboard
│   ├── data_loader.py · charts.py · formats.py · formulas.py · styles.py
├── saleshealth_schema.dbml        # Diagrama ER — modelo OLTP
├── saleshealth_dwh_schema.dbml    # Diagrama ER — modelo DWH (estrella)
├── diagrama_er.png                # Render del ER OLTP
├── diagrama_dimensional.png       # Render del ER DWH
├── cltv_resultados.csv            # Output Fase 5
├── clustering_resultados.csv      # Output Fase 6
├── ventas_detalle.csv             # Vista plana de ventas (para dashboard)
├── 06_documento_tecnico.pdf       # Memoria técnica
├── requirements.txt               # Dependencias Python
└── README.md
```

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Base de datos | PostgreSQL 16 |
| Cliente SQL | DBeaver |
| Entorno BD (local) | Docker (contenedor Postgres) |
| Lenguaje | Python 3.11+ |
| Análisis | pandas, NumPy, scikit-learn |
| Conexión BD | SQLAlchemy + psycopg2 |
| Visualización (notebooks) | matplotlib, seaborn |
| Dashboard | Streamlit + Plotly |
| Modelado ER | dbdiagram.io (formato DBML) |

---

## Cómo ejecutar el proyecto

El dashboard está **desplegado online** ([enlace arriba](#dashboard-en-vivo)), así que para *consultarlo* no hace falta instalar nada. Las instrucciones siguientes son solo para **reproducir el pipeline completo en local**.

### Requisitos previos

1. **Python 3.11 o superior** con `pip`.
2. **PostgreSQL** corriendo en `localhost:5432` (cualquiera de estas opciones vale):
   - PostgreSQL instalado nativamente (Postgres.app en Mac, instalador EnterpriseDB en Windows, paquetes apt/brew, etc.).
   - **PostgreSQL en Docker** — opción usada durante el desarrollo:
     ```bash
     docker run -d \
       --name saleshealth-pg \
       -e POSTGRES_DB=saleshealth \
       -e POSTGRES_PASSWORD=tu_password \
       -p 5432:5432 \
       postgres:16
     ```
3. **Cliente SQL** (opcional pero recomendado): DBeaver, pgAdmin o psql.

> El proyecto no depende de Docker: funciona igual con un Postgres instalado de forma nativa. Docker se documenta porque es la forma en la que se desarrolló y simplifica la puesta en marcha.

### Paso a paso

**1. Clonar el repositorio e instalar dependencias**

```bash
git clone https://github.com/rubenelices/SALESHEALTH_DB_
cd SALESHEALTH_DB_
pip install -r requirements.txt
```

**2. Crear la base de datos**

Si no la has creado al levantar Postgres, hazlo desde DBeaver o psql:

```sql
CREATE DATABASE saleshealth;
```

**3. Configurar la conexión**

En los notebooks la cadena de conexión es:

```python
engine = create_engine("postgresql+psycopg2://postgres:CONTRASEÑA@localhost:5432/saleshealth")
```

Sustituye `CONTRASEÑA` por la tuya. Los notebooks crearán el schema `public` (OLTP) automáticamente al cargar los JSON.

**4. Aplicar el DDL del Data Warehouse**

Ejecuta [`02_ddl_dwh.sql`](02_ddl_dwh.sql) en DBeaver (o `psql -f 02_ddl_dwh.sql`). Esto crea el schema `dwh` y sus 7 tablas vacías.

**5. Ejecutar los notebooks en orden**

```text
01_eda.ipynb                  → exploración y calidad
03_etl.ipynb                  → carga OLTP → DWH
04_cltv.ipynb                 → cálculo CLTV
04b_features_diversidad.ipynb → features adicionales
05_pca_clustering.ipynb       → PCA + K-Means
```

**6. Lanzar el dashboard localmente** (opcional — está desplegado online)

```bash
streamlit run app.py
```

---

## Fases del trabajo

### 1. EDA y calidad de datos

[`01_eda.ipynb`](01_eda.ipynb) inspecciona las 17 tablas del OLTP, detecta problemas de calidad y documenta decisiones de imputación.

Hallazgos relevantes:
- clientes con nulos en email, nombre o teléfono → imputación, **nunca eliminación**
- discrepancias puntuales entre ventas y líneas de venta
- 1 producto sin coste conocido → imputado con la mediana
- `offer_id` nulo en prácticamente todas las ventas → fila `-1` en `dim_offer`
- devoluciones integrables a nivel de línea

### 2. Diseño del Data Warehouse

Modelo **estrella** con `fact_sales` como tabla central y seis dimensiones conformadas. Ver [`saleshealth_dwh_schema.dbml`](saleshealth_dwh_schema.dbml) y [`02_ddl_dwh.sql`](02_ddl_dwh.sql).

### 3. ETL

[`03_etl.ipynb`](03_etl.ipynb) implementa una carga **idempotente** (TRUNCATE + INSERT en orden de FK):
- extracción desde OLTP
- limpieza e imputación
- enriquecimiento de dimensiones
- cálculo de métricas de venta y margen
- validaciones de integridad
- carga final en `dwh`

### 4. CLTV y segmentación de valor

[`04_cltv.ipynb`](04_cltv.ipynb) — fórmula utilizada:

> **CLTV = Ingresos_t × Margen_t × Frecuencia_t × R_t**

donde `R_t` es la antigüedad del cliente en meses. Segmentación por percentiles:
- **Alto** (> P75): ~1.526 clientes → ~94.7 % de los ingresos
- **Medio** (P25–P75): ~2.791 clientes
- **Bajo** (< P25): ~1.433 clientes

### 5. Segmentación RFM

Segmentos de marketing: *Champions*, *Leales*, *Potenciales*, *Necesitan atención*, *En riesgo*, *Perdidos*.

### 6. PCA + K-Means

[`05_pca_clustering.ipynb`](05_pca_clustering.ipynb) reduce dimensionalidad sobre features de comportamiento y aplica K-Means (k=3) → clusters **VIP**, **Regular**, **Bajo valor**.

### 7. Dashboard

[`app.py`](app.py) + [`pages/`](pages/). Páginas:
- **KPIs** — indicadores ejecutivos
- **CLTV** — distribución y segmentación de valor
- **RFM** — visuales y segmentos
- **Clustering** — espacio PCA y perfiles
- **Cliente** — ficha individual
- **Ventas** — exploración detallada

---

## Decisiones de diseño relevantes

- **No eliminar clientes nunca**: los problemas de calidad se resuelven con imputación o transformación. Mantener la base completa es prioritario para los análisis CRM.
- **ETL idempotente**: cada ejecución borra y recarga las tablas DWH en orden de FK, garantizando reproducibilidad.
- **Filas especiales `id = -1`** en `dim_offer` y `dim_return_reason`: representan "sin oferta" y "sin devolución". Se reinsertan tras cada TRUNCATE para preservar la integridad referencial.
- **CSVs versionados** (`cltv_resultados.csv`, `clustering_resultados.csv`, `ventas_detalle.csv`): forman parte del flujo del dashboard desplegado en Streamlit Cloud, donde no hay acceso a Postgres local.
- **Dos diagramas ER** (OLTP y DWH): documentan explícitamente el paso de modelo normalizado a modelo dimensional.

---

## Documentación

- [`06_documento_tecnico.pdf`](06_documento_tecnico.pdf) — Memoria técnica completa del proyecto.
- [`saleshealth_schema.dbml`](saleshealth_schema.dbml) / [`saleshealth_dwh_schema.dbml`](saleshealth_dwh_schema.dbml) — Diagramas ER editables (formato DBML, abribles en [dbdiagram.io](https://dbdiagram.io)).
- [`diagrama_er.png`](diagrama_er.png) / [`diagrama_dimensional.png`](diagrama_dimensional.png) — Renders visuales.

## Autor

**Rubén Elices Rodríguez**
Proyecto Final · Gestión de Datos · 3º Ingeniería Matemática · UAX
