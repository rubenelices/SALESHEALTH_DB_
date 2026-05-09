"""
Página: Análisis CLTV — distribución, segmentación y bubble chart.

Visualizaciones:
  - Histograma CLTV con líneas P25/P75
  - Violin plot por segmento
  - Bubble chart (frecuencia vs ingresos, size=ticket, color=segmento)
  - Tabla resumen de segmentos
"""

import streamlit as st
import pandas as pd

from utils.styles import (
    inject_global_css, render_header, section_divider, section_title,
    kpi_row, info_box, showcase_table, badge,
    fmt_eur, fmt_int, fmt_pct, PAL_SEG,
    DS1, DS2, DS3, DS5, DS6, DS7,
)
from utils.data_loader import load_all
from utils.charts import (
    histograma_cltv, violin_cltv_segmento, bubble_ingresos_frecuencia,
    rfm_ingresos_bar, rfm_rm_scatter,
)

# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(page_title='CLTV · SalesHealth',
                   page_icon='💰', layout='wide',
                   initial_sidebar_state='collapsed')
inject_global_css()

render_header(
    active_page='cltv',
    eyebrow='FASE 5 · CUSTOMER LIFETIME VALUE',
    title='Análisis CLTV',
    subtitle=('Customer Lifetime Value calculado con la fórmula del enunciado: '
              'Ingresos_t × Margen_t × Frecuencia_t × R_t. '
              'Se segmenta con percentiles P25/P75.'),
)

df = load_all()
if df.empty:
    info_box('❌ <strong>No hay datos.</strong> Ejecuta primero <code>04_cltv.ipynb</code>.',
             kind='danger')
    st.stop()


# ═══════════════════════════════════════════════════════════════════════
#  FILTROS (en la propia página, sin sidebar)
# ═══════════════════════════════════════════════════════════════════════
section_title('Filtros', label='CONTROLES')

c1, c2, c3, c4 = st.columns([1.4, 1.6, 1, 1])

with c1:
    segs_disponibles = sorted(df['segmento_cltv'].unique().tolist()) \
        if 'segmento_cltv' in df else []
    segmentos = st.multiselect(
        'Segmentos CLTV',
        options=segs_disponibles,
        default=segs_disponibles,
    )

with c2:
    cltv_max = float(df['cltv'].quantile(0.97))
    rango_cltv = st.slider(
        'Rango CLTV (€)',
        min_value=0.0, max_value=cltv_max,
        value=(0.0, cltv_max), step=100.0,
    )

with c3:
    solo_riesgo = st.toggle('🔴 Solo en riesgo', value=False)

with c4:
    solo_top = st.toggle('💎 Solo top 25%', value=False)

# Aplicar filtros
df_f = df.copy()
if segmentos:
    df_f = df_f[df_f['segmento_cltv'].isin(segmentos)]
df_f = df_f[(df_f['cltv'] >= rango_cltv[0]) & (df_f['cltv'] <= rango_cltv[1])]
if solo_riesgo and 'churn_proxy' in df_f.columns:
    df_f = df_f[df_f['churn_proxy']]
if solo_top:
    p75 = df['cltv'].quantile(0.75)
    df_f = df_f[df_f['cltv'] >= p75]


# ═══════════════════════════════════════════════════════════════════════
#  KPI CARDS DEL FILTRO
# ═══════════════════════════════════════════════════════════════════════
n_filtrado = len(df_f)
ing_filtrado = df_f['ingresos_t'].sum() if n_filtrado else 0
cltv_med_f = df_f['cltv'].mean() if n_filtrado else 0
pct_filtrado = (n_filtrado / len(df) * 100) if len(df) else 0

kpi_row([
    {'value': fmt_int(n_filtrado), 'label': 'Clientes filtrados', 'color': 'primary'},
    {'value': f'{pct_filtrado:.1f}%', 'label': '% del total', 'color': 'cyan'},
    {'value': fmt_eur(cltv_med_f), 'label': 'CLTV medio (filtro)', 'color': 'gold'},
    {'value': f'{ing_filtrado/1e6:.2f}M€', 'label': 'Ingresos (filtro)', 'color': 'ocean'},
])

if n_filtrado == 0:
    info_box('⚠️ No hay clientes que cumplan los filtros seleccionados.',
             kind='warning')
    st.stop()


# ═══════════════════════════════════════════════════════════════════════
#  DISTRIBUCIÓN CLTV
# ═══════════════════════════════════════════════════════════════════════
section_divider('DISTRIBUCIÓN DE CLTV')

c1, c2 = st.columns([1.2, 1])
with c1:
    vista_log = st.toggle(
        'Usar escala logarítmica en el histograma',
        value=True,
        help='Comprime la cola alta de CLTV y hace más legible la masa central.',
    )
    fig_hist = histograma_cltv(df_f, log_scale=vista_log)
    st.plotly_chart(fig_hist, use_container_width=True, theme=None)

with c2:
    fig_violin = violin_cltv_segmento(df_f)
    st.plotly_chart(fig_violin, use_container_width=True, theme=None)


# ═══════════════════════════════════════════════════════════════════════
#  BUBBLE CHART
# ═══════════════════════════════════════════════════════════════════════
section_divider('RELACIÓN FRECUENCIA · INGRESOS · TICKET')

info_box(
    'Cada punto es un cliente: <strong>posición horizontal</strong> = '
    'frecuencia de compra, <strong>posición vertical</strong> = ingresos '
    'totales, <strong>tamaño</strong> = ticket medio, <strong>color</strong> '
    '= segmento CLTV. Pasa el cursor para ver el nombre del cliente.',
    kind='info',
)
fig_bubble = bubble_ingresos_frecuencia(df_f)
st.plotly_chart(fig_bubble, use_container_width=True, theme=None)


# ═══════════════════════════════════════════════════════════════════════
#  PUENTE CLTV → CRM
# ═══════════════════════════════════════════════════════════════════════
section_divider('PUENTE ENTRE CLTV Y SEGMENTACIÓN RFM')

info_box(
    'Este bloque conecta el valor económico con la accionabilidad CRM. '
    'A la izquierda se ve qué segmentos RFM concentran más ingresos; '
    'a la derecha, cómo se distribuyen los clientes en el plano '
    '<strong>R</strong>ecency vs <strong>M</strong>onetary.',
    kind='info',
)

c1, c2 = st.columns([1, 1])
with c1:
    fig_rfm_bar = rfm_ingresos_bar(df_f)
    st.plotly_chart(fig_rfm_bar, use_container_width=True, theme=None)
with c2:
    fig_rfm_rm = rfm_rm_scatter(df_f)
    st.plotly_chart(fig_rfm_rm, use_container_width=True, theme=None)


# ═══════════════════════════════════════════════════════════════════════
#  TABLA RESUMEN DE SEGMENTOS
# ═══════════════════════════════════════════════════════════════════════
section_divider('RESUMEN POR SEGMENTO')

if 'segmento_cltv' in df_f.columns:
    resumen = df_f.groupby('segmento_cltv').agg(
        n=('customer_id', 'count'),
        cltv_medio=('cltv', 'mean'),
        cltv_mediano=('cltv', 'median'),
        ingresos=('ingresos_t', 'sum'),
        ticket=('ticket_medio', 'mean'),
        frec=('frecuencia_t', 'mean'),
    ).round(2)

    orden = [s for s in ['Alto', 'Medio', 'Bajo']
             if s in resumen.index]
    resumen = resumen.loc[orden]
    total_ing = df_f['ingresos_t'].sum()

    headers = ['Segmento', 'Clientes', '% del filtro', 'CLTV medio',
               'CLTV mediano', 'Ingresos totales', '% ingresos',
               'Ticket medio', 'Frecuencia']
    rows = []
    for seg, r in resumen.iterrows():
        pct_clientes = r['n'] / n_filtrado * 100
        pct_ing = r['ingresos'] / total_ing * 100 if total_ing else 0
        rows.append([
            badge(seg, seg.lower()),
            fmt_int(r['n']),
            f'{pct_clientes:.1f}%',
            fmt_eur(r['cltv_medio']),
            fmt_eur(r['cltv_mediano']),
            fmt_eur(r['ingresos']),
            f'<strong style="color:{DS1};">{pct_ing:.1f}%</strong>',
            fmt_eur(r['ticket']),
            f'{r["frec"]:.2f} v/mes',
        ])
    showcase_table(headers, rows)


# ═══════════════════════════════════════════════════════════════════════
#  EXPORTACIÓN
# ═══════════════════════════════════════════════════════════════════════
section_divider('EXPORTACIÓN', thin=True)

c1, _ = st.columns([1, 3])
with c1:
    csv = df_f.to_csv(index=False).encode('utf-8')
    st.download_button(
        f'⬇️ Descargar selección filtrada ({n_filtrado:,} filas)'.replace(',', '.'),
        data=csv,
        file_name='cltv_filtrado.csv',
        mime='text/csv',
        use_container_width=True,
    )
