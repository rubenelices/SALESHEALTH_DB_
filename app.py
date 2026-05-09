"""
SalesHealth Analytics — Dashboard principal (Fase 7).

Entry point del dashboard Streamlit.
Ejecutar con:
    streamlit run app.py
"""

import streamlit as st

from utils.styles import (
    inject_global_css, render_header, section_divider, section_title,
    kpi_row, info_box,
    DS1, DS2, DS3, DS5, DS6, DS7,
)
from utils.formats import fmt_eur, fmt_int, fmt_pct, fmt_millones
from utils.data_loader import load_all, kpis_globales, data_status

# ═══════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title='SalesHealth Analytics',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='collapsed',
)
inject_global_css()


# ═══════════════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════
#  ESTADO DE LOS DATOS — chequeo previo al header para evitar render con errores
# ═══════════════════════════════════════════════════════════════════════
status = data_status()

if not status['cltv']['exists']:
    render_header(active_page='home',
                  eyebrow='PROYECTO FINAL · GESTIÓN DE DATOS · RUBEN ELICES RODRIGUEZ',
                  title='SalesHealth Analytics',
                  subtitle='Dashboard del proyecto.')
    st.error(
        f'❌ No se encuentra `{status["cltv"]["path"]}`.\n\n'
        'Ejecuta primero **04_cltv.ipynb** para generar `cltv_resultados.csv`.'
    )
    st.stop()

df = load_all()
if df.empty:
    st.error('❌ El CSV de CLTV existe pero está vacío. Revisa la ejecución del notebook 04.')
    st.stop()

kpis = kpis_globales(df)
n_clientes      = kpis['n_clientes']
ingresos_total  = kpis['ingresos_total']

# Subtítulo dinámico (los números se leen del CSV, no se hardcodean)
render_header(
    active_page='home',
    eyebrow='PROYECTO FINAL · GESTIÓN DE DATOS · RUBEN ELICES RODRIGUEZ',
    title='SalesHealth Analytics',
    subtitle=(f'Entorno analítico para una empresa de productos de salud con '
              f'20 tiendas en Madrid, 50 productos, '
              f'{fmt_int(n_clientes)} clientes y {fmt_millones(ingresos_total)} '
              f'de ingresos entre 2020 y 2025. Construido sobre PostgreSQL '
              f'(OLTP + Data Warehouse) y enriquecido con CLTV y clustering.'),
)

if not status['clustering']['exists']:
    info_box(
        '⚠️ <strong>Atención:</strong> aún no se ha generado '
        '<code>clustering_resultados.csv</code>. Algunas páginas '
        '(Clustering, Cliente) tendrán funcionalidad limitada hasta '
        'que ejecutes <code>05_pca_clustering.ipynb</code>.',
        kind='warning',
    )


# ═══════════════════════════════════════════════════════════════════════
#  KPIs RÁPIDOS DE BIENVENIDA
# ═══════════════════════════════════════════════════════════════════════
kpi_row([
    {'value': fmt_int(kpis['n_clientes']),       'label': 'Clientes',           'color': 'primary'},
    {'value': fmt_millones(kpis['ingresos_total']), 'label': 'Ingresos totales','color': 'ocean'},
    {'value': fmt_eur(kpis['cltv_medio']),       'label': 'CLTV medio',         'color': 'cyan'},
    {'value': fmt_eur(kpis['ticket_medio']),     'label': 'Ticket medio',       'color': 'gold'},
    {'value': fmt_pct(kpis.get('pct_churn', 0)), 'label': 'Clientes en riesgo', 'color': 'coral'},
    {'value': fmt_pct(kpis.get('pct_ingresos_alto', 0)),
     'label': 'Ingresos seg. Alto', 'color': 'green'},
])


# ═══════════════════════════════════════════════════════════════════════
#  NAVIGATION CARDS
# ═══════════════════════════════════════════════════════════════════════
section_divider('NAVEGACIÓN')

n_clusters = kpis.get('n_clusters', '—')

CARDS = [
    {
        'page': '/KPIs',
        'icon': '📈',
        'title': 'KPIs',
        'desc': 'Resumen ejecutivo con KPIs principales, evolución temporal '
                'de ingresos y treemap por segmento.',
        'kpi':  f"{fmt_int(kpis['n_clientes'])} clientes · {fmt_millones(kpis['ingresos_total'])}",
    },
    {
        'page': '/CLTV',
        'icon': '💰',
        'title': 'Análisis CLTV',
        'desc': 'Distribución del Customer Lifetime Value, segmentación '
                'Alto/Medio/Bajo y clientes top.',
        'kpi':  f"CLTV medio: {fmt_eur(kpis['cltv_medio'])}",
    },
    {
        'page': '/RFM',
        'icon': '🎯',
        'title': 'Segmentación RFM',
        'desc': 'Clasificación por Recency, Frequency y Monetary. Sankey '
                'diagram de flujos y alertas de churn.',
        'kpi':  f"{fmt_int(kpis.get('n_churn', 0))} clientes en riesgo",
    },
    {
        'page': '/Clustering',
        'icon': '🔮',
        'title': 'PCA + Clustering',
        'desc': 'Segmentación automática por Machine Learning. PCA, '
                'K-Means y perfiles de comportamiento.',
        'kpi':  f"{n_clusters} clusters identificados",
    },
    {
        'page': '/Cliente',
        'icon': '👤',
        'title': 'Exploración individual',
        'desc': 'Búsqueda por ID, nombre o email. Ficha completa con gauge '
                'de percentil y clientes similares.',
        'kpi':  'Buscar cliente concreto',
    },
]

# Renderizar cards en columnas
nav_cols = st.columns(len(CARDS))
for col, c in zip(nav_cols, CARDS):
    with col:
        st.markdown(f"""
            <a href="{c['page']}" target="_self" class="nav-card">
                <div class="nav-card-icon">{c['icon']}</div>
                <div class="nav-card-title">{c['title']}</div>
                <div class="nav-card-desc">{c['desc']}</div>
                <div class="nav-card-kpi">{c['kpi']} →</div>
            </a>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
#  ARQUITECTURA DEL PROYECTO
# ═══════════════════════════════════════════════════════════════════════
section_divider('ARQUITECTURA DEL PROYECTO')

ARQ_STEPS = [
    ('📁',  '17 ficheros JSON',   'Datos fuente'),
    ('🗄️',  'PostgreSQL OLTP',    '17 tablas (public)'),
    ('⚙️',  'ETL',                '03_etl.ipynb'),
    ('⭐',  'Data Warehouse',     'Modelo dimensional (dwh)'),
    ('💎',  'CLTV + Clustering',  '04 + 05 .ipynb'),
    ('📊',  'Dashboard',          'Streamlit (este)'),
]

# Columnas: 6 bloques + 5 flechas intercaladas → 11 columnas
arq_cols = st.columns([3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3])
step_indices = [0, 2, 4, 6, 8, 10]
arrow_indices = [1, 3, 5, 7, 9]

for i, (icon, title, sub) in zip(step_indices, ARQ_STEPS):
    with arq_cols[i]:
        st.markdown(f"""
            <div style="background:white; border-radius:14px; padding:20px 14px;
                        box-shadow:0 2px 10px rgba(0,0,0,0.05); text-align:center;">
                <div style="font-size:32px; margin-bottom:8px;">{icon}</div>
                <div style="font-weight:700; color:{DS1}; font-size:13px;">{title}</div>
                <div style="color:{DS2}; font-size:11px; margin-top:3px;">{sub}</div>
            </div>
        """, unsafe_allow_html=True)

for i in arrow_indices:
    with arq_cols[i]:
        st.markdown(
            f'<div style="text-align:center; font-size:22px; color:{DS3}; '
            f'padding-top:28px;">→</div>',
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════
#  ESTADO DE LOS DATOS (footer técnico)
# ═══════════════════════════════════════════════════════════════════════
section_divider('ESTADO DE LOS DATOS', thin=True)

c1, c2 = st.columns(2)

def _render_status_card(s: dict, fname: str) -> str:
    """Renderiza una tarjeta de estado de CSV (existe o no)."""
    if s['exists']:
        return f"""
        <div style="background:white; border-radius:12px; padding:16px 20px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.05);
                    border-left:4px solid {DS7};">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                <span style="font-size:20px;">✅</span>
                <strong style="color:{DS1}; font-size:14px;">{fname}</strong>
            </div>
            <div style="font-size:12.5px; color:{DS2}; line-height:1.7;">
                <div>Filas: <strong>{fmt_int(s['rows'])}</strong></div>
                <div>Tamaño: <strong>{s['size_kb']:.1f} KB</strong></div>
                <div>Modificado: <strong>{s['modified']}</strong></div>
            </div>
        </div>
        """
    return f"""
    <div style="background:white; border-radius:12px; padding:16px 20px;
                box-shadow:0 2px 8px rgba(0,0,0,0.05);
                border-left:4px solid {DS5};">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
            <span style="font-size:20px;">⚠️</span>
            <strong style="color:{DS1}; font-size:14px;">{fname}</strong>
        </div>
        <div style="font-size:12.5px; color:{DS5};">
            Aún no generado.
        </div>
    </div>
    """


with c1:
    st.markdown(_render_status_card(status['cltv'], 'cltv_resultados.csv'),
                unsafe_allow_html=True)

with c2:
    st.markdown(_render_status_card(status['clustering'], 'clustering_resultados.csv'),
                unsafe_allow_html=True)


# Footer
st.markdown(f"""
    <div style="text-align:center; padding:32px 0 8px 0; color:{DS2}; font-size:12px;">
        Proyecto Final · Gestión de Datos · UAX 3º Ingeniería Matemática<br>
        <span style="opacity:0.7;">Construido con Streamlit + Plotly</span>
    </div>
""", unsafe_allow_html=True)
