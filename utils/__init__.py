"""Utilidades del dashboard SalesHealth Analytics."""
from .formats import (
    fmt_eur, fmt_int, fmt_pct, fmt_num, fmt_millones,
    badge, segmento_badge, estado_badge,
)
from .styles import (
    DS1, DS2, DS3, DS4, DS5, DS6, DS7, GRAY, BG,
    CLUSTER_PAL, PAL_SEG,
    inject_global_css,
    render_header,
    section_divider,
    section_title,
    kpi_card,
    kpi_row,
    showcase_table,
    info_box,
)
from .data_loader import (
    load_cltv, load_clustering, load_all,
    kpis_globales, data_status, clientes_similares, buscar_clientes,
)
from .formulas import (
    compute_cltv, compute_churn_proxy,
    compute_rfm_scores, apply_rfm_segments,
    apply_cltv_segments, cltv_segment_thresholds,
    cltv_sensitivity,
    CHURN_DAYS_THRESHOLD, R_T_MIN_MONTHS,
)
