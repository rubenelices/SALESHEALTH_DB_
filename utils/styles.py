"""
Sistema visual del dashboard SalesHealth Analytics.

Contiene:
  - Paleta Deep Sky
  - inject_global_css(): CSS global (fuente Inter, oculta sidebar, estilos custom)
  - render_header(page, title, subtitle): top bar + título + subtítulo + separador
  - section_divider(label): separador con gradiente brillante
  - kpi_card / kpi_row: tarjetas KPI con sombra y hover
  - showcase_table: tabla HTML estilizada
  - info_box: caja de aviso/insight
"""

import streamlit as st

# ═══════════════════════════════════════════════════════════════════════
#  PALETA DEEP SKY
# ═══════════════════════════════════════════════════════════════════════
DS1 = '#03045E'   # azul marino — header bg, títulos
DS2 = '#0077B6'   # océano       — secundario
DS3 = '#00B4D8'   # cian         — acento principal
DS4 = '#90E0EF'   # cian claro   — fondos suaves
DS5 = '#FF6B6B'   # coral        — alertas, churn
DS6 = '#FFD93D'   # dorado       — highlights
DS7 = '#6BCB77'   # verde        — alto valor
GRAY = '#64748B'  # subtítulos
BG   = '#F8FAFC'  # fondo general

# Paleta para clusters (hasta 7 grupos)
CLUSTER_PAL = ['#FF6B6B', '#4D96FF', '#6BCB77', '#FFD93D',
               '#A29BFE', '#FF9F43', '#00B4D8']

# Paleta segmentos CLTV
PAL_SEG = {'Alto': DS7, 'Medio': DS6, 'Bajo': DS5}


# ═══════════════════════════════════════════════════════════════════════
#  CSS GLOBAL
# ═══════════════════════════════════════════════════════════════════════
_GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Ocultar elementos por defecto de Streamlit ── */
#MainMenu { visibility: hidden; }
header[data-testid="stHeader"] { display: none; }
footer { visibility: hidden; }
[data-testid="stSidebar"],
[data-testid="stSidebarNav"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }

/* ── Tipografía global ── */
html, body, [class*="css"], .stMarkdown, .stText {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.main .block-container {
    padding-top: 1.2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
    padding-left: 2rem;
    padding-right: 2rem;
}

.stApp {
    background: linear-gradient(180deg, #ffffff 0%, #E0F2FE 35%, #F0F9FF 70%, #F8FAFC 100%);
    min-height: 100vh;
}

/* ── Top navigation bar — sin caja, sobre degradado ── */
.top-nav {
    background: transparent;
    padding: 52px 32px 36px;
    text-align: center;
    margin: 0;
}
.top-nav .top-nav-eyebrow {
    color: #00B4D8;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.26em;
    margin-bottom: 18px;
}
.top-nav .top-nav-brand {
    font-size: 92px;
    font-weight: 800;
    letter-spacing: -0.04em;
    line-height: 1.0;
    margin-bottom: 32px;
    background: linear-gradient(135deg, #03045E 0%, #0077B6 55%, #00B4D8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.top-nav .nav-links {
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
}
.top-nav .nav-link {
    color: #0077B6;
    text-decoration: none;
    padding: 12px 28px;
    border-radius: 50px;
    font-size: 15px;
    font-weight: 600;
    transition: all 0.25s ease;
    letter-spacing: 0.01em;
    background: rgba(0, 180, 216, 0.07);
    border: 1.5px solid rgba(0, 180, 216, 0.28);
}
.top-nav .nav-link:hover {
    background: rgba(0, 180, 216, 0.14);
    color: #03045E;
    border-color: #00B4D8;
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(0, 180, 216, 0.2);
}
.top-nav .nav-link.active {
    background: #03045E;
    color: white;
    border-color: transparent;
    box-shadow: 0 6px 22px rgba(3, 4, 94, 0.28);
    font-weight: 700;
}

/* ── Page header ── */
.page-header { padding: 18px 4px 4px 4px; }
.page-header .eyebrow {
    text-transform: uppercase;
    font-size: 11px;
    font-weight: 700;
    color: #00B4D8;
    letter-spacing: 0.16em;
    margin-bottom: 6px;
}
.page-header h1 {
    font-size: 54px;
    font-weight: 800;
    color: #03045E;
    letter-spacing: -0.035em;
    margin: 0;
    line-height: 1.05;
    background: linear-gradient(135deg, #03045E 0%, #0077B6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.page-header p.subtitle {
    font-size: 17px;
    color: #64748B;
    margin: 10px 0 0 0;
    font-weight: 400;
    max-width: 800px;
    line-height: 1.5;
}

/* ── Separators ── */
.separator-bright {
    height: 4px;
    background: linear-gradient(90deg, #00B4D8 0%, #FFD93D 50%, #FF6B6B 100%);
    border-radius: 2px;
    margin: 26px 0 18px 0;
    box-shadow: 0 2px 8px rgba(0,180,216,0.25);
}
.separator-thin {
    height: 1px;
    background: linear-gradient(90deg, transparent, #CBD5E1, transparent);
    margin: 20px 0;
}
.section-label {
    text-transform: uppercase;
    font-size: 11px;
    font-weight: 700;
    color: #0077B6;
    letter-spacing: 0.16em;
    margin-bottom: 6px;
    margin-top: 8px;
}
.section-title {
    font-size: 22px;
    font-weight: 700;
    color: #03045E;
    letter-spacing: -0.015em;
    margin: 0 0 14px 0;
}

/* ── KPI cards ── */
.kpi-grid {
    display: grid;
    gap: 16px;
    margin: 8px 0 4px 0;
}
.kpi-grid.cols-2 { grid-template-columns: repeat(2, 1fr); }
.kpi-grid.cols-3 { grid-template-columns: repeat(3, 1fr); }
.kpi-grid.cols-4 { grid-template-columns: repeat(4, 1fr); }
.kpi-grid.cols-5 { grid-template-columns: repeat(5, 1fr); }
.kpi-grid.cols-6 { grid-template-columns: repeat(6, 1fr); }

.kpi-card {
    background: white;
    border-radius: 16px;
    padding: 22px 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    transition: all 0.25s ease;
    border-left: 4px solid #00B4D8;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 70px; height: 70px;
    background: radial-gradient(circle, rgba(0,180,216,0.08) 0%, transparent 70%);
    border-radius: 50%;
    transform: translate(20px, -20px);
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.10);
}
.kpi-card .kpi-value {
    font-size: 30px;
    font-weight: 800;
    color: #03045E;
    line-height: 1.1;
    letter-spacing: -0.025em;
    margin: 0;
}
.kpi-card .kpi-label {
    font-size: 12px;
    color: #64748B;
    margin-top: 8px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    line-height: 1.3;
}
.kpi-card .kpi-delta {
    font-size: 12px;
    margin-top: 6px;
    font-weight: 600;
}
.kpi-card .kpi-delta.up { color: #16A34A; }
.kpi-card .kpi-delta.down { color: #DC2626; }
.kpi-card .kpi-delta.neutral { color: #64748B; }

/* Variantes de color de KPI card (border-left) */
.kpi-card.c-primary { border-left-color: #03045E; }
.kpi-card.c-ocean   { border-left-color: #0077B6; }
.kpi-card.c-cyan    { border-left-color: #00B4D8; }
.kpi-card.c-coral   { border-left-color: #FF6B6B; }
.kpi-card.c-gold    { border-left-color: #FFD93D; }
.kpi-card.c-green   { border-left-color: #6BCB77; }

/* ── Showcase table ── */
.showcase-wrap {
    overflow-x: auto;
    border-radius: 14px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    background: white;
    margin: 8px 0;
}
.showcase-table {
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
    font-size: 13.5px;
}
.showcase-table thead th {
    background: linear-gradient(135deg, #03045E 0%, #0077B6 100%);
    color: white;
    padding: 14px 16px;
    text-align: left;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11.5px;
    letter-spacing: 0.08em;
    white-space: nowrap;
}
.showcase-table thead th:first-child { border-top-left-radius: 14px; }
.showcase-table thead th:last-child  { border-top-right-radius: 14px; }
.showcase-table tbody tr { transition: background 0.15s ease; }
.showcase-table tbody tr:nth-child(even) { background: #F8FAFC; }
.showcase-table tbody tr:hover { background: #E0F7FA; }
.showcase-table tbody td {
    padding: 12px 16px;
    border-bottom: 1px solid #E5E7EB;
    color: #1F2937;
}
.showcase-table tbody tr:last-child td { border-bottom: none; }

/* Badges */
.badge {
    display: inline-block;
    padding: 4px 11px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.badge-alto    { background: #DCFCE7; color: #166534; }
.badge-medio   { background: #FEF3C7; color: #92400E; }
.badge-bajo    { background: #FEE2E2; color: #991B1B; }
.badge-churn   { background: #FEE2E2; color: #991B1B; }
.badge-active  { background: #DCFCE7; color: #166534; }
.badge-vip     { background: #FEF3C7; color: #78350F; border: 1px solid #FDE68A; }

/* ── Info box ── */
.info-box {
    background: linear-gradient(135deg, #E0F7FA 0%, #F0F9FF 100%);
    border-left: 4px solid #00B4D8;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 14px 0;
    color: #0F172A;
    font-size: 14px;
    line-height: 1.55;
}
.info-box.warning {
    background: linear-gradient(135deg, #FEF3C7 0%, #FFFBEB 100%);
    border-left-color: #F59E0B;
}
.info-box.danger {
    background: linear-gradient(135deg, #FEE2E2 0%, #FEF2F2 100%);
    border-left-color: #EF4444;
}
.info-box.success {
    background: linear-gradient(135deg, #DCFCE7 0%, #F0FDF4 100%);
    border-left-color: #16A34A;
}
.info-box strong { color: #03045E; }

/* ── Streamlit element overrides ── */
.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    border: 1.5px solid #E5E7EB;
    padding: 8px 18px;
    transition: all 0.2s;
}
.stButton > button:hover {
    border-color: #00B4D8;
    color: #0077B6;
    transform: translateY(-1px);
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #03045E 0%, #0077B6 100%);
    color: white;
    border-radius: 10px;
    border: none;
    font-weight: 600;
    padding: 9px 22px;
}
.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #023E8A 0%, #00B4D8 100%);
    color: white;
}

/* DataFrames */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* Inputs */
.stTextInput input, .stNumberInput input, .stSelectbox > div > div {
    border-radius: 10px !important;
}

/* Selectbox — fondo blanco, texto oscuro (tema claro consistente) */
.stSelectbox > div > div,
.stSelectbox div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #03045E !important;
    border: 1px solid #E2E8F0 !important;
}
.stSelectbox div[data-baseweb="select"] svg {
    fill: #03045E !important;
    color: #03045E !important;
}
/* Texto del valor seleccionado dentro del selectbox */
.stSelectbox div[data-baseweb="select"] [data-baseweb="tag"],
.stSelectbox div[data-baseweb="select"] span,
.stSelectbox div[data-baseweb="select"] input {
    color: #03045E !important;
    background-color: transparent !important;
}
/* Dropdown desplegado (popover con las opciones) */
[data-baseweb="popover"] ul,
[data-baseweb="popover"] [role="listbox"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    box-shadow: 0 6px 24px rgba(15,23,42,0.10) !important;
}
[data-baseweb="popover"] li {
    background-color: #FFFFFF !important;
    color: #1F2937 !important;
}
[data-baseweb="popover"] li:hover,
[data-baseweb="popover"] li[aria-selected="true"] {
    background-color: #F0F9FF !important;
    color: #03045E !important;
}

/* Labels de widgets — visibles sobre cualquier fondo */
.stTextInput label, .stSelectbox label, .stNumberInput label,
.stMultiSelect label, .stSlider label, .stToggle label,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p {
    color: #1E3A5F !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 0.01em;
}

/* Metric cards (st.metric) */
[data-testid="stMetric"] {
    background: white;
    border-radius: 14px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border-left: 3px solid #00B4D8;
}
[data-testid="stMetricValue"] {
    font-size: 28px !important;
    font-weight: 800 !important;
    color: #03045E !important;
}
[data-testid="stMetricLabel"] {
    font-size: 12px !important;
    color: #64748B !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
}

/* Tabs — pill style con buen contraste */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background: transparent;
    border-bottom: none !important;
    padding: 4px 0 10px 0;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 12px !important;
    padding: 12px 28px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    letter-spacing: 0.01em;
    background: #FFFFFF !important;
    color: #475569 !important;
    border: 1.5px solid #CBD5E1 !important;
    transition: all 0.18s ease;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}
.stTabs [data-baseweb="tab"]:hover {
    background: #F0F9FF !important;
    color: #03045E !important;
    border-color: #00B4D8 !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #03045E 0%, #023E8A 100%) !important;
    color: #FFFFFF !important;
    border-color: #03045E !important;
    box-shadow: 0 4px 12px rgba(3,4,94,0.25);
    border-bottom: none !important;
}
/* Quitar la línea de subrayado por defecto de BaseWeb */
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"]    { display: none !important; }

/* Hide pages list in sidebar nav */
[data-testid="stSidebarNavItems"] { display: none; }

/* Welcome cards (used in 07_dashboard.py) */
.nav-card {
    background: white;
    border-radius: 18px;
    padding: 26px 24px;
    box-shadow: 0 2px 14px rgba(0,0,0,0.06);
    transition: all 0.3s ease;
    border-top: 4px solid #00B4D8;
    text-decoration: none;
    color: inherit;
    display: block;
    height: 100%;
}
.nav-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(3,4,94,0.15);
    border-top-color: #FFD93D;
}
.nav-card .nav-card-icon {
    font-size: 36px;
    margin-bottom: 12px;
    line-height: 1;
}
.nav-card .nav-card-title {
    font-size: 19px;
    font-weight: 700;
    color: #03045E;
    margin-bottom: 6px;
    letter-spacing: -0.015em;
}
.nav-card .nav-card-desc {
    font-size: 13px;
    color: #64748B;
    line-height: 1.5;
    margin-bottom: 12px;
}
.nav-card .nav-card-kpi {
    font-size: 13px;
    color: #00B4D8;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Hide "Made with Streamlit" badge */
.stDeployButton { display: none !important; }
</style>
"""


# ═══════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE PÁGINAS
# ═══════════════════════════════════════════════════════════════════════
PAGES_NAV = [
    ('home',        'Inicio',      '📊', '07_dashboard.py'),
    ('kpis',        'KPIs',        '📈', 'pages/1_KPIs.py'),
    ('cltv',        'CLTV',        '💰', 'pages/2_CLTV.py'),
    ('rfm',         'RFM',         '🎯', 'pages/3_RFM.py'),
    ('clustering',  'Clustering',  '🔮', 'pages/4_Clustering.py'),
    ('cliente',     'Cliente',     '👤', 'pages/5_Cliente.py'),
    ('ventas',      'Ventas',      '🛒', 'pages/6_Ventas.py'),
]

TOP_NAV_EYEBROW = 'PROYECTO FINAL · GESTIÓN DE DATOS · RUBEN ELICES RODRIGUEZ'


# ═══════════════════════════════════════════════════════════════════════
#  FUNCIONES PÚBLICAS
# ═══════════════════════════════════════════════════════════════════════
def inject_global_css():
    """Inyecta el CSS global. Llamar al inicio de cada página."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


def render_header(active_page: str, title: str, subtitle: str, eyebrow: str = ''):
    """
    Renderiza:
      1. Top navigation bar centrado (título grande + nav pills)
      2. Page header (eyebrow + h1 + subtítulo) — solo en sub-páginas
      3. Separador con gradiente brillante

    active_page: 'home' | 'kpis' | 'cltv' | 'rfm' | 'clustering' | 'cliente'
    """
    nav_links_html = ''
    for key, label, icon, _path in PAGES_NAV:
        if key == 'home':
            continue   # El botón Inicio solo aparece en sub-páginas
        page_url = f"/{label}"
        active_cls = ' active' if key == active_page else ''
        nav_links_html += (
            f'<a href="{page_url}" target="_self" '
            f'class="nav-link{active_cls}">{icon} {label}</a>'
        )

    # En home añadir el botón Inicio como primero
    if active_page == 'home':
        inicio_btn = '<a href="/" target="_self" class="nav-link active">📊 Inicio</a>'
        nav_links_html = inicio_btn + nav_links_html
    else:
        inicio_btn = '<a href="/" target="_self" class="nav-link">📊 Inicio</a>'
        nav_links_html = inicio_btn + nav_links_html

    st.markdown(f"""
        <div class="top-nav">
            <div class="top-nav-eyebrow">{TOP_NAV_EYEBROW}</div>
            <div class="top-nav-brand">SalesHealth Analytics</div>
            <div class="nav-links">{nav_links_html}</div>
        </div>
        <div class="separator-bright"></div>
    """, unsafe_allow_html=True)

    # Header de página (solo en sub-páginas; home ya tiene el título en el nav)
    if active_page != 'home':
        eyebrow_html = f'<div class="eyebrow">{eyebrow}</div>' if eyebrow else ''
        st.markdown(f"""
            <div class="page-header">
                {eyebrow_html}
                <h1>{title}</h1>
                <p class="subtitle">{subtitle}</p>
            </div>
            <div class="separator-bright"></div>
        """, unsafe_allow_html=True)


def section_divider(label: str = '', thin: bool = False):
    """Separador visual entre secciones de una página."""
    label_html = f'<div class="section-label">{label}</div>' if label else ''
    cls = 'separator-thin' if thin else 'separator-bright'
    st.markdown(f'{label_html}<div class="{cls}"></div>', unsafe_allow_html=True)


def section_title(text: str, label: str = ''):
    """Título de sección con eyebrow opcional."""
    label_html = f'<div class="section-label">{label}</div>' if label else ''
    st.markdown(
        f'{label_html}<div class="section-title">{text}</div>',
        unsafe_allow_html=True
    )


def kpi_card(value: str, label: str, color: str = 'cyan',
             delta: str = '', delta_dir: str = 'neutral') -> str:
    """
    Devuelve el HTML de una KPI card.
    color    : primary | ocean | cyan | coral | gold | green
    delta_dir: up | down | neutral
    """
    delta_html = ''
    if delta:
        arrow = '↑' if delta_dir == 'up' else ('↓' if delta_dir == 'down' else '→')
        delta_html = f'<div class="kpi-delta {delta_dir}">{arrow} {delta}</div>'
    return f"""
        <div class="kpi-card c-{color}">
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
            {delta_html}
        </div>
    """


def kpi_row(cards: list, cols: int = None):
    """Renderiza una fila de KPI cards.
    cards: lista de dicts {value, label, color, delta?, delta_dir?} o strings HTML.
    """
    if cols is None:
        cols = len(cards)
    columns = st.columns(cols)
    for col, c in zip(columns, cards):
        with col:
            html = c if isinstance(c, str) else kpi_card(**c)
            st.markdown(html, unsafe_allow_html=True)


def showcase_table(headers: list, rows: list):
    """
    Tabla HTML estilizada.
    headers: ['Nombre', 'CLTV', 'Segmento', ...]
    rows   : [[v1, v2, badge_html, ...], ...]
    Cada celda se renderiza tal cual (acepta HTML).
    """
    head_html = ''.join(f'<th>{h}</th>' for h in headers)
    body_html = ''
    for row in rows:
        cells = ''.join(f'<td>{c}</td>' for c in row)
        body_html += f'<tr>{cells}</tr>'
    st.markdown(f"""
        <div class="showcase-wrap">
            <table class="showcase-table">
                <thead><tr>{head_html}</tr></thead>
                <tbody>{body_html}</tbody>
            </table>
        </div>
    """, unsafe_allow_html=True)


def info_box(text: str, kind: str = 'info'):
    """
    kind: info | warning | danger | success
    """
    cls = '' if kind == 'info' else f' {kind}'
    st.markdown(
        f'<div class="info-box{cls}">{text}</div>',
        unsafe_allow_html=True
    )


# ═══════════════════════════════════════════════════════════════════════
#  RE-EXPORTS — formatters están en utils/formats.py
#  Se mantienen aquí para compatibilidad con código existente.
# ═══════════════════════════════════════════════════════════════════════
from .formats import fmt_eur, fmt_int, fmt_pct, fmt_num, fmt_millones, badge  # noqa: E402,F401
