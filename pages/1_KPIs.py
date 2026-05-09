"""
Página: KPIs — resumen ejecutivo del negocio.

Visualizaciones:
  - 6 KPI cards principales
  - Area chart de ingresos por año
  - Distribución de clientes por cluster
  - Top 10 clientes (tabla showcase)
"""

import streamlit as st
import pandas as pd

from utils.styles import (
    inject_global_css, render_header, section_divider, section_title,
    kpi_row, info_box, showcase_table, badge,
    fmt_eur, fmt_int, fmt_pct,
    DS1, DS2, DS3, DS5, DS6, DS7,
)
from utils.data_loader import load_all, kpis_globales

# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(page_title='KPIs · SalesHealth',
                   page_icon='📈', layout='wide',
                   initial_sidebar_state='collapsed')
inject_global_css()

df = load_all()
if df.empty:
    render_header(active_page='kpis', eyebrow='RESUMEN EJECUTIVO',
                  title='KPIs principales', subtitle='')
    info_box('❌ <strong>No hay datos.</strong> Ejecuta primero <code>04_cltv.ipynb</code> '
             'para generar <code>cltv_resultados.csv</code>.', kind='danger')
    st.stop()
kpis = kpis_globales(df)

render_header(
    active_page='kpis',
    eyebrow='RESUMEN EJECUTIVO',
    title='KPIs principales',
    subtitle=(f'Indicadores clave del negocio: {fmt_int(kpis["n_clientes"])} clientes, '
              f'{kpis["ingresos_total"]/1e6:.2f} M€ de ingresos, '
              f'evolución temporal y distribución por segmentos.'),
)

# ═══════════════════════════════════════════════════════════════════════
#  KPI CARDS PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════
# Calcular deltas comparando con la media
cltv_alto_medio = df.loc[df['segmento_cltv'] == 'Alto', 'cltv'].mean() \
                  if 'segmento_cltv' in df.columns else None
delta_cltv = ''
if cltv_alto_medio:
    delta_cltv = f'Alto: {fmt_eur(cltv_alto_medio)}'

kpi_row([
    {'value': fmt_int(kpis['n_clientes']),
     'label': 'Clientes totales', 'color': 'primary'},
    {'value': f"{kpis['ingresos_total']/1e6:.2f}M€",
     'label': 'Ingresos totales', 'color': 'ocean'},
    {'value': fmt_eur(kpis['cltv_medio']),
     'label': 'CLTV medio', 'color': 'cyan',
     'delta': delta_cltv, 'delta_dir': 'up'},
    {'value': fmt_eur(kpis['ticket_medio']),
     'label': 'Ticket medio', 'color': 'gold'},
    {'value': fmt_pct(kpis.get('tasa_dev_global', 0)),
     'label': 'Tasa devolución global', 'color': 'coral'},
    {'value': fmt_pct(kpis.get('pct_churn', 0)),
     'label': 'Clientes en riesgo', 'color': 'green'
     if kpis.get('pct_churn', 100) < 30 else 'coral'},
])


# ═══════════════════════════════════════════════════════════════════════
#  TOP 3 DESTACADO — PODIO
# ═══════════════════════════════════════════════════════════════════════
section_divider('LOS 3 PILARES DEL NEGOCIO')

top3 = df.nlargest(3, 'cltv').reset_index(drop=True)

MEDALS = [
    ('🥇', '#FFD700'),
    ('🥈', '#C0C0C0'),
    ('🥉', '#CD7F32'),
]

# CLTV medio del segmento Alto como referencia para contextualizar
cltv_alto = df.loc[df['segmento_cltv'] == 'Alto', 'cltv'].mean() \
    if 'segmento_cltv' in df.columns else df['cltv'].mean()

cols = st.columns(3)
for i, (col, (medal, accent)) in enumerate(zip(cols, MEDALS)):
    if i >= len(top3):
        break
    r = top3.iloc[i]
    nombre = str(r.get('full_name', f'Cliente {int(r["customer_id"])}'))
    seg = r.get('segmento_cltv', '—')
    veces_alto = r['cltv'] / cltv_alto if cltv_alto else 0
    estado_html = ('<span style="color:#DC2626;font-weight:600;">🔴 En riesgo</span>'
                   if r.get('churn_proxy', False) else
                   '<span style="color:#16A34A;font-weight:600;">🟢 Activo</span>')

    with col:
        st.markdown(f"""
        <div style="
            background: linear-gradient(160deg, white 0%, #F8FAFC 100%);
            border: 1px solid #E5E7EB;
            border-top: 4px solid {accent};
            border-radius: 14px;
            padding: 22px 24px;
            box-shadow: 0 2px 8px rgba(15,23,42,0.06);
            height: 100%;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
                <span style="font-size:38px;line-height:1;">{medal}</span>
                <div>
                    <div style="font-size:11px;color:{DS2};letter-spacing:0.08em;
                                text-transform:uppercase;font-weight:700;">
                        Puesto #{i+1} · {seg}
                    </div>
                    <div style="font-size:16px;color:{DS1};font-weight:700;
                                line-height:1.2;margin-top:2px;">
                        {nombre}
                    </div>
                    <div style="font-size:11px;color:{DS2};">
                        ID: {int(r['customer_id'])}
                    </div>
                </div>
            </div>
            <div style="margin:18px 0 4px 0;">
                <div style="font-size:11px;color:{DS2};letter-spacing:0.08em;
                            text-transform:uppercase;font-weight:600;">CLTV</div>
                <div style="font-size:30px;color:{DS1};font-weight:800;
                            line-height:1.1;">{fmt_eur(r['cltv'])}</div>
                <div style="font-size:11px;color:{DS2};margin-top:2px;">
                    {veces_alto:.1f}× la media del segmento Alto
                </div>
            </div>
            <div style="border-top:1px solid #F1F5F9;padding-top:12px;margin-top:14px;
                        display:grid;grid-template-columns:1fr 1fr;gap:10px 14px;">
                <div>
                    <div style="font-size:10px;color:{DS2};letter-spacing:0.06em;
                                text-transform:uppercase;font-weight:600;">Ingresos</div>
                    <div style="font-size:14px;color:{DS1};font-weight:700;">
                        {fmt_eur(r['ingresos_t'])}
                    </div>
                </div>
                <div>
                    <div style="font-size:10px;color:{DS2};letter-spacing:0.06em;
                                text-transform:uppercase;font-weight:600;">Compras</div>
                    <div style="font-size:14px;color:{DS1};font-weight:700;">
                        {int(r['num_ventas'])}
                    </div>
                </div>
                <div>
                    <div style="font-size:10px;color:{DS2};letter-spacing:0.06em;
                                text-transform:uppercase;font-weight:600;">Ticket medio</div>
                    <div style="font-size:14px;color:{DS1};font-weight:700;">
                        {fmt_eur(r['ticket_medio'])}
                    </div>
                </div>
                <div>
                    <div style="font-size:10px;color:{DS2};letter-spacing:0.06em;
                                text-transform:uppercase;font-weight:600;">Frecuencia</div>
                    <div style="font-size:14px;color:{DS1};font-weight:700;">
                        {r['frecuencia_t']:.2f} v/mes
                    </div>
                </div>
            </div>
            <div style="margin-top:14px;font-size:12px;">{estado_html}</div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
#  TOP 10 CLIENTES
# ═══════════════════════════════════════════════════════════════════════
section_divider('TOP 10 CLIENTES POR CLTV')

top10 = df.nlargest(10, 'cltv').copy()

headers = ['#', 'Cliente', 'CLTV', 'Ingresos', 'Frecuencia',
           'Segmento CLTV', 'Estado']
rows = []
for i, (_, r) in enumerate(top10.iterrows(), 1):
    nombre = str(r.get('full_name', f'Cliente {r["customer_id"]}'))
    if len(nombre) > 30:
        nombre = nombre[:27] + '…'

    seg = r.get('segmento_cltv', '—')
    seg_badge = badge(seg, seg.lower()) if seg in ('Alto', 'Medio', 'Bajo') else seg

    if r.get('churn_proxy', False):
        estado_html = badge('🔴 En riesgo', 'churn')
    else:
        estado_html = badge('🟢 Activo', 'active')

    # Top 3 destacar con corona
    rank_html = (f'<span style="font-size:18px;">🥇</span>' if i == 1 else
                 f'<span style="font-size:18px;">🥈</span>' if i == 2 else
                 f'<span style="font-size:18px;">🥉</span>' if i == 3 else
                 f'<span style="color:{DS2};font-weight:700;">{i}</span>')

    rows.append([
        rank_html,
        f'<strong>{nombre}</strong><br>'
        f'<span style="font-size:11px;color:{DS2};">ID: {int(r["customer_id"])}</span>',
        f'<strong style="color:{DS1};">{fmt_eur(r["cltv"])}</strong>',
        fmt_eur(r['ingresos_t']),
        f'{r["frecuencia_t"]:.2f} v/mes',
        seg_badge,
        estado_html,
    ])
showcase_table(headers, rows)


# ═══════════════════════════════════════════════════════════════════════
#  INSIGHTS AUTOMÁTICOS
# ═══════════════════════════════════════════════════════════════════════
section_divider('INSIGHTS AUTOMÁTICOS', thin=True)

# Calcular insights
top10_pct_ing = top10['ingresos_t'].sum() / kpis['ingresos_total'] * 100

if 'segmento_cltv' in df.columns:
    n_alto = (df['segmento_cltv'] == 'Alto').sum()
    pct_alto_clientes = n_alto / len(df) * 100
    pct_alto_ingresos = kpis.get('pct_ingresos_alto', 0)

c1, c2, c3 = st.columns(3)

with c1:
    info_box(
        f'💎 <strong>Concentración Pareto:</strong> los <strong>10 mejores '
        f'clientes</strong> generan el <strong>{top10_pct_ing:.1f}%</strong> '
        f'de los ingresos totales. Cuidarlos es prioritario.',
        kind='info',
    )

with c2:
    if 'segmento_cltv' in df.columns:
        info_box(
            f'🎯 <strong>Segmento Alto:</strong> {pct_alto_clientes:.0f}% de '
            f'los clientes generan el <strong>{pct_alto_ingresos:.1f}%</strong> '
            f'de los ingresos. Foco de fidelización.',
            kind='success',
        )

with c3:
    n_riesgo = kpis.get('n_churn', 0)
    info_box(
        f'⚠️ <strong>Clientes en riesgo:</strong> {fmt_int(n_riesgo)} '
        f'clientes ({kpis.get("pct_churn", 0):.0f}%) llevan más de 180 días '
        f'sin comprar. Acción de reactivación recomendada.',
        kind='warning' if kpis.get('pct_churn', 0) > 30 else 'info',
    )
