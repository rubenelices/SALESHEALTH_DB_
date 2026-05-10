"""
Carga de datos para el dashboard. Lee los CSVs producidos por las fases 5 y 6.

Funciones:
  - load_cltv()          : DataFrame de cltv_resultados.csv (5.750 filas)
  - load_clustering()    : DataFrame de clustering_resultados.csv (5.750 filas)
  - load_all()           : DataFrame mergeado con todas las columnas
  - data_status()        : info de existencia y modificación de los CSVs
  - kpis_globales(df)    : dict con KPIs principales
  - clientes_similares() : top-N vecinos en el mismo cluster
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# ═══════════════════════════════════════════════════════════════════════
#  Paths absolutos al proyecto — el dashboard funciona aunque se lance
#  desde otra CWD.
# ═══════════════════════════════════════════════════════════════════════
PROJECT_ROOT    = Path(__file__).resolve().parent.parent
CLTV_PATH       = PROJECT_ROOT / 'cltv_resultados.csv'
CLUSTERING_PATH = PROJECT_ROOT / 'clustering_resultados.csv'
VENTAS_PATH     = PROJECT_ROOT / 'ventas_detalle.csv'

# Columnas que se esperan en los CSVs (validación de schema en runtime).
CLTV_REQUIRED_COLS = {
    'customer_id', 'full_name', 'ingresos_t', 'margen_t',
    'frecuencia_t', 'r_t', 'cltv', 'segmento_cltv',
}
CLUSTERING_REQUIRED_COLS = {
    'customer_id', 'cluster', 'cluster_label', 'pc1', 'pc2',
}


# ═══════════════════════════════════════════════════════════════════════
#  CARGA DE CSVs
# ═══════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def load_cltv() -> pd.DataFrame:
    """Carga cltv_resultados.csv y lo enriquece con columnas derivadas."""
    if not CLTV_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(CLTV_PATH)

    # Validación de schema (no bloqueante: deja al caller decidir)
    missing = CLTV_REQUIRED_COLS - set(df.columns)
    if missing:
        st.warning(f'⚠️ cltv_resultados.csv: faltan columnas {missing}.')

    for col in ('first_purchase_date', 'last_purchase_date'):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    if 'first_purchase_date' in df.columns:
        df['anio_primera_compra'] = df['first_purchase_date'].dt.year
    if 'last_purchase_date' in df.columns:
        df['anio_ultima_compra'] = df['last_purchase_date'].dt.year

    if 'tasa_devolucion' in df.columns:
        df['tramo_dev'] = pd.cut(
            df['tasa_devolucion'],
            bins=[-0.001, 0, 0.05, 0.15, 0.30, 1.01],
            labels=['0%', '0-5%', '5-15%', '15-30%', '>30%'],
        )

    if 'churn_proxy' in df.columns:
        df['churn_proxy'] = df['churn_proxy'].astype(bool)

    return df


@st.cache_data(ttl=3600, show_spinner=False)
def load_clustering() -> pd.DataFrame:
    """Carga clustering_resultados.csv (output de la Fase 6)."""
    if not CLUSTERING_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(CLUSTERING_PATH)

    missing = CLUSTERING_REQUIRED_COLS - set(df.columns)
    if missing:
        st.warning(f'⚠️ clustering_resultados.csv: faltan columnas {missing}.')

    if 'churn_proxy' in df.columns:
        df['churn_proxy'] = df['churn_proxy'].astype(bool)

    return df


@st.cache_data(ttl=3600, show_spinner=False)
def load_all() -> pd.DataFrame:
    """Devuelve el DataFrame consolidado (cltv + clustering vía customer_id)."""
    df_cltv = load_cltv()
    df_clu  = load_clustering()

    if df_cltv.empty:
        return df_cltv

    if df_clu.empty:
        return df_cltv

    cols_extra = [c for c in df_clu.columns
                  if c not in df_cltv.columns and c != 'customer_id']
    cols_extra = ['customer_id'] + cols_extra

    return df_cltv.merge(df_clu[cols_extra], on='customer_id', how='left')


@st.cache_data(ttl=3600, show_spinner=False)
def load_ventas() -> pd.DataFrame:
    """Carga ventas_detalle.csv (fact_sales unido con dim_date/product/store).

    Generado por _docs/export_ventas.py. Son 42.555 filas: una por línea de venta.
    """
    if not VENTAS_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(VENTAS_PATH, parse_dates=['sale_date'])
    df['year_month'] = df['sale_date'].dt.to_period('M').dt.to_timestamp()
    return df


# ═══════════════════════════════════════════════════════════════════════
#  ESTADO Y KPIs
# ═══════════════════════════════════════════════════════════════════════
def data_status() -> dict:
    """Devuelve info sobre los CSVs (existencia + última modificación)."""
    out = {}
    for nombre, path in (('cltv', CLTV_PATH), ('clustering', CLUSTERING_PATH)):
        if path.exists():
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            try:
                with open(path, encoding='utf-8') as f:
                    n_rows = sum(1 for _ in f) - 1
            except Exception:
                n_rows = None
            out[nombre] = {
                'exists': True,
                'modified': mtime.strftime('%Y-%m-%d %H:%M'),
                'rows': n_rows,
                'size_kb': round(path.stat().st_size / 1024, 1),
                'path': str(path),
            }
        else:
            out[nombre] = {
                'exists': False, 'modified': None,
                'rows': None, 'size_kb': None, 'path': str(path),
            }
    return out


def kpis_globales(df: pd.DataFrame) -> dict:
    """KPIs principales calculados una sola vez. Tolerante a columnas ausentes."""
    if df.empty:
        return {
            'n_clientes': 0, 'ingresos_total': 0, 'cltv_medio': 0,
            'cltv_mediano': 0, 'ticket_medio': 0,
        }

    out = {
        'n_clientes':     len(df),
        'ingresos_total': float(df['ingresos_t'].sum()) if 'ingresos_t' in df else 0,
        'cltv_medio':     float(df['cltv'].mean())      if 'cltv' in df else 0,
        'cltv_mediano':   float(df['cltv'].median())    if 'cltv' in df else 0,
        'ticket_medio':   float(df['ticket_medio'].mean()) if 'ticket_medio' in df else 0,
    }
    if 'churn_proxy' in df:
        out['n_churn']  = int(df['churn_proxy'].sum())
        out['pct_churn'] = float(df['churn_proxy'].mean() * 100)
    if 'tasa_devolucion' in df:
        out['tasa_dev_global'] = float(df['tasa_devolucion'].mean() * 100)
    if 'cluster_label' in df:
        out['n_clusters'] = int(df['cluster_label'].nunique())
    if 'segmento_cltv' in df and out['ingresos_total']:
        ing_alto = df.loc[df['segmento_cltv'] == 'Alto', 'ingresos_t'].sum()
        out['pct_ingresos_alto'] = float(ing_alto / out['ingresos_total'] * 100)
    return out


# ═══════════════════════════════════════════════════════════════════════
#  BÚSQUEDA Y SIMILITUD
# ═══════════════════════════════════════════════════════════════════════
def buscar_clientes(df: pd.DataFrame, query: str, limit: int = 50) -> pd.DataFrame:
    """Búsqueda flexible por ID, nombre o email (substring case-insensitive).

    Devuelve hasta `limit` filas ordenadas por relevancia (ingresos descendentes).
    """
    if df.empty or not query:
        return df.head(0)

    q = str(query).strip().lower()
    if not q:
        return df.head(0)

    mask = pd.Series(False, index=df.index)

    # Por ID exacto / parcial (números)
    if q.isdigit():
        mask |= df['customer_id'].astype(str).str.contains(q, na=False)

    # Por nombre
    if 'full_name' in df.columns:
        mask |= df['full_name'].astype(str).str.lower().str.contains(q, na=False)

    # Por email
    if 'email' in df.columns:
        mask |= df['email'].astype(str).str.lower().str.contains(q, na=False)

    res = df[mask]
    if 'ingresos_t' in res.columns:
        res = res.sort_values('ingresos_t', ascending=False)
    return res.head(limit)


def clientes_similares(df: pd.DataFrame, customer_id: int,
                       n: int = 5) -> pd.DataFrame:
    """Top-N clientes más cercanos (distancia euclidiana en features
    normalizadas) al cliente dado, dentro del mismo cluster."""
    if 'cluster' not in df.columns or customer_id not in df['customer_id'].values:
        return pd.DataFrame()

    target = df[df['customer_id'] == customer_id].iloc[0]
    cluster_id = target['cluster']
    candidatos = df[(df['cluster'] == cluster_id) &
                    (df['customer_id'] != customer_id)].copy()

    if candidatos.empty:
        return pd.DataFrame()

    feats = []
    if {'pc1', 'pc2'}.issubset(df.columns):
        feats.extend(['pc1', 'pc2'])

    feats.extend([
        'dias_sin_compra', 'ingresos_t', 'frecuencia_t',
        'ticket_medio', 'tasa_devolucion', 'margen_t',
    ])
    feats = [f for f in feats if f in df.columns]
    feats = list(dict.fromkeys(feats))

    if not feats:
        return pd.DataFrame()

    X = df[feats].copy()
    mu, sd = X.mean(), X.std().replace(0, 1)
    X_norm = (X - mu) / sd

    target_n = X_norm.loc[df['customer_id'] == customer_id].iloc[0].values
    cand_n   = X_norm.loc[candidatos.index].values

    distancias = np.linalg.norm(cand_n - target_n, axis=1)
    candidatos['distancia'] = distancias

    return candidatos.nsmallest(n, 'distancia')
