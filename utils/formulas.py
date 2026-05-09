"""
Fórmulas y métricas de cliente reutilizables.

Centralizan la lógica que estaba duplicada entre los notebooks (04_cltv,
05_pca_clustering) y las páginas del dashboard.

Funciones puras: reciben DataFrames/Series y devuelven nuevos objetos sin
mutar la entrada.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ═══════════════════════════════════════════════════════════════════════
#  CONSTANTES (parámetros que se documentan en la memoria técnica)
# ═══════════════════════════════════════════════════════════════════════
CHURN_DAYS_THRESHOLD = 180        # umbral de días sin compra para flag churn
R_T_MIN_MONTHS       = 1.0        # piso de meses activos (R_t) para evitar /0
SEGMENT_LOW_PCTL     = 0.25       # P25 → frontera Bajo / Medio
SEGMENT_HIGH_PCTL    = 0.75       # P75 → frontera Medio / Alto


# ═══════════════════════════════════════════════════════════════════════
#  CLTV
# ═══════════════════════════════════════════════════════════════════════
def compute_cltv(
    ingresos_t: pd.Series,
    margen_t: pd.Series,
    frecuencia_t: pd.Series,
    r_t: pd.Series,
) -> pd.Series:
    """Calcula el CLTV con la fórmula del enunciado del proyecto.

    CLTV = Ingresos_t * Margen_t * Frecuencia_t * R_t
    """
    cltv = (
        ingresos_t.fillna(0) *
        margen_t.fillna(0) *
        frecuencia_t.fillna(0) *
        r_t.fillna(0)
    )
    return cltv.clip(lower=0).round(2)


def cltv_segment_thresholds(cltv: pd.Series) -> dict:
    """Calcula los umbrales P25 / P75 para segmentación CLTV.

    Útil para guardar en JSON y reutilizar en dashboard.
    """
    return {
        'p25':  float(cltv.quantile(SEGMENT_LOW_PCTL)),
        'p75':  float(cltv.quantile(SEGMENT_HIGH_PCTL)),
        'mean': float(cltv.mean()),
        'median': float(cltv.median()),
        'low_pctl':  SEGMENT_LOW_PCTL,
        'high_pctl': SEGMENT_HIGH_PCTL,
    }


def apply_cltv_segments(cltv: pd.Series, thresholds: dict | None = None) -> pd.Series:
    """Asigna 'Alto'/'Medio'/'Bajo' según percentiles.

    Si no se pasan thresholds, los calcula sobre la propia serie.
    """
    th = thresholds or cltv_segment_thresholds(cltv)
    return pd.cut(
        cltv,
        bins=[-np.inf, th['p25'], th['p75'], np.inf],
        labels=['Bajo', 'Medio', 'Alto'],
    ).astype(str)


# ═══════════════════════════════════════════════════════════════════════
#  CHURN PROXY
# ═══════════════════════════════════════════════════════════════════════
def compute_churn_proxy(
    dias_sin_compra: pd.Series,
    threshold_days: int = CHURN_DAYS_THRESHOLD,
) -> pd.Series:
    """Marca clientes en riesgo: > threshold_days desde la última compra."""
    return (dias_sin_compra.fillna(0) > threshold_days).astype(bool)


# ═══════════════════════════════════════════════════════════════════════
#  RFM
# ═══════════════════════════════════════════════════════════════════════
def compute_rfm_scores(
    df: pd.DataFrame,
    recency_col:   str = 'dias_sin_compra',
    frequency_col: str = 'num_ventas',
    monetary_col:  str = 'ingresos_t',
    n_bins: int = 5,
) -> pd.DataFrame:
    """Devuelve un DataFrame con columnas R_score, F_score, M_score (1..n_bins)
    y una columna rfm_score concatenada."""
    out = pd.DataFrame(index=df.index)

    # Recency: menos días = mejor → invertir
    out['R_score'] = pd.qcut(
        df[recency_col].rank(method='first', ascending=False),
        n_bins, labels=range(1, n_bins + 1),
    ).astype(int)

    out['F_score'] = pd.qcut(
        df[frequency_col].rank(method='first'),
        n_bins, labels=range(1, n_bins + 1),
    ).astype(int)

    out['M_score'] = pd.qcut(
        df[monetary_col].rank(method='first'),
        n_bins, labels=range(1, n_bins + 1),
    ).astype(int)

    out['rfm_score'] = (
        out['R_score'].astype(str) +
        out['F_score'].astype(str) +
        out['M_score'].astype(str)
    )
    return out


def rfm_segment_label(R: int, F: int, M: int) -> str:
    """Etiqueta de segmento RFM clásico (Champions, At Risk, etc.).

    R/F/M se asumen en escala 1..5. Reglas siguiendo la convención de
    Hughes (1996) adaptada al e-commerce.
    """
    s = R + F + M
    if R >= 4 and F >= 4 and M >= 4:
        return 'Champions'
    if F >= 4 and M >= 4:
        return 'Leales'
    if R >= 4 and F <= 2:
        return 'Nuevos'
    if R >= 3 and F >= 3:
        return 'Potenciales'
    if R <= 2 and F >= 4 and M >= 4:
        return 'En riesgo'
    if R <= 2 and F <= 2 and M <= 2:
        return 'Hibernando'
    if R <= 2:
        return 'A reactivar'
    if s >= 9:
        return 'Prometedores'
    return 'Estándar'


def apply_rfm_segments(rfm: pd.DataFrame) -> pd.Series:
    """Aplica rfm_segment_label a un DataFrame con R/F/M_score."""
    return rfm.apply(
        lambda r: rfm_segment_label(r['R_score'], r['F_score'], r['M_score']),
        axis=1,
    )


# ═══════════════════════════════════════════════════════════════════════
#  ANÁLISIS DE SENSIBILIDAD CLTV
# ═══════════════════════════════════════════════════════════════════════
def cltv_sensitivity(
    df: pd.DataFrame,
    deltas: tuple = (-0.10, -0.05, 0.05, 0.10),
) -> pd.DataFrame:
    """Escenarios simples sobre los componentes de la fórmula CLTV."""
    required = {'ingresos_t', 'margen_t', 'frecuencia_t', 'r_t'}
    if not required.issubset(df.columns):
        return pd.DataFrame()

    base = compute_cltv(
        df['ingresos_t'],
        df['margen_t'],
        df['frecuencia_t'],
        df['r_t'],
    ).sum()
    rows = []
    for factor in ('ingresos_t', 'margen_t', 'frecuencia_t', 'r_t'):
        for d in deltas:
            mod = df.copy()
            mod[factor] = mod[factor] * (1 + d)
            new = compute_cltv(
                mod['ingresos_t'],
                mod['margen_t'],
                mod['frecuencia_t'],
                mod['r_t'],
            ).sum()
            rows.append({
                'factor': factor,
                'delta': d,
                'cltv_total': new,
                'variacion_abs': new - base,
                'variacion_pct': (new - base) / base * 100 if base else 0,
            })
    return pd.DataFrame(rows)
