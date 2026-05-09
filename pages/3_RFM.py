"""
Página: Segmentación RFM — Recency, Frequency, Monetary.

Visualizaciones:
  - Heatmap R×F con métrica seleccionable
  - Sankey diagram CLTV → RFM
  - Tabla de recomendaciones por segmento RFM
  - Alerta de churn en clientes Champions/Leales
"""

import streamlit as st
import pandas as pd

from utils.styles import (
    inject_global_css, render_header, section_divider, section_title,
    kpi_row, info_box, showcase_table, badge,
    fmt_eur, fmt_int, fmt_pct,
    DS1, DS2, DS3, DS5, DS6, DS7,
)
from utils.data_loader import load_all
from utils.charts import heatmap_rf, sankey_segmentos, rfm_ingresos_bar, rfm_rm_scatter

# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(page_title='RFM · SalesHealth',
                   page_icon='🎯', layout='wide',
                   initial_sidebar_state='collapsed')
inject_global_css()

render_header(
    active_page='rfm',
    eyebrow='FASE 5 · CRM ANALYTICS',
    title='Segmentación RFM',
    subtitle=('Clasificación CRM clásica por <strong>R</strong>ecency '
              '(días sin compra), <strong>F</strong>requency (nº de compras) '
              'y <strong>M</strong>onetary (ingresos totales). 6 segmentos '
              'accionables.'),
)

df = load_all()
if df.empty:
    info_box('❌ <strong>No hay datos.</strong> Ejecuta primero <code>04_cltv.ipynb</code>.',
             kind='danger')
    st.stop()

if 'segmento_rfm' not in df.columns:
    info_box('⚠️ No se encuentra la segmentación RFM en los datos. '
             'Ejecuta primero <code>04_cltv.ipynb</code>.',
             kind='warning')
    st.stop()


# ═══════════════════════════════════════════════════════════════════════
#  KPIs RFM
# ═══════════════════════════════════════════════════════════════════════
n_champions  = (df['segmento_rfm'] == 'Champions').sum()
n_leales     = (df['segmento_rfm'] == 'Leales').sum()
n_riesgo     = (df['segmento_rfm'] == 'En riesgo').sum()
n_perdidos   = (df['segmento_rfm'] == 'Perdidos').sum()

ing_champions = df.loc[df['segmento_rfm'] == 'Champions', 'ingresos_t'].sum()
pct_ing_champs = ing_champions / df['ingresos_t'].sum() * 100

kpi_row([
    {'value': fmt_int(n_champions),  'label': 'Champions',         'color': 'green'},
    {'value': fmt_int(n_leales),     'label': 'Leales',            'color': 'cyan'},
    {'value': fmt_int(n_riesgo),     'label': 'En riesgo',         'color': 'coral'},
    {'value': fmt_int(n_perdidos),   'label': 'Perdidos',          'color': 'primary'},
    {'value': f'{pct_ing_champs:.1f}%',
     'label': '% ingresos · Champions', 'color': 'gold'},
])


# ═══════════════════════════════════════════════════════════════════════
#  HEATMAP R×F INTERACTIVO
# ═══════════════════════════════════════════════════════════════════════
section_divider('MAPA DE CALOR R × F')

c_left, c_right = st.columns([3, 1])

with c_right:
    metricas = {
        'count': '👥 Número de clientes',
        'M_score': '💰 M_score medio',
        'cltv': '💎 CLTV medio',
        'tasa_devolucion': '📦 Tasa devolución',
        'ingresos_t': '💵 Ingresos medios',
    }
    metricas = {k: v for k, v in metricas.items()
                if k == 'count' or k in df.columns}

    metrica_color = st.selectbox(
        'Métrica de coloreado:',
        options=list(metricas.keys()),
        format_func=lambda k: metricas[k],
        index=0,
    )

    info_box(
        'El heatmap muestra la distribución de clientes por su nivel de '
        '<strong>Recency</strong> (vertical) y <strong>Frequency</strong> '
        '(horizontal). Cambia la métrica para colorear las celdas con '
        'distinta información.',
        kind='info',
    )

with c_left:
    fig_heat = heatmap_rf(df, metrica_color=metrica_color)
    st.plotly_chart(fig_heat, use_container_width=True, theme=None)


# ═══════════════════════════════════════════════════════════════════════
#  SEGMENTACIÓN ESPACIAL RFM
# ═══════════════════════════════════════════════════════════════════════
section_divider('INGRESOS Y DISTRIBUCIÓN ESPACIAL RFM')

info_box(
    'Vista ejecutiva del RFM: qué segmentos generan más ingresos y cómo se '
    'ocupan las combinaciones de recencia y gasto. Es la lectura más directa '
    'para pasar de scoring a acción comercial.',
    kind='info',
)

c1, c2 = st.columns([1, 1])
with c1:
    fig_bar = rfm_ingresos_bar(df)
    st.plotly_chart(fig_bar, use_container_width=True, theme=None)
with c2:
    fig_rm = rfm_rm_scatter(df)
    st.plotly_chart(fig_rm, use_container_width=True, theme=None)


# ═══════════════════════════════════════════════════════════════════════
#  SANKEY CLTV → RFM
# ═══════════════════════════════════════════════════════════════════════
section_divider('FLUJO DE CLIENTES · CLTV → RFM')

info_box(
    'El Sankey diagram muestra cómo se distribuyen los clientes de cada '
    'segmento CLTV (izquierda) entre los segmentos RFM (derecha). Permite '
    'ver si las dos segmentaciones coinciden o aportan información complementaria.',
    kind='info',
)
fig_sankey = sankey_segmentos(df)
st.plotly_chart(fig_sankey, use_container_width=True, theme=None)


# ═══════════════════════════════════════════════════════════════════════
#  RECOMENDACIONES DE NEGOCIO POR SEGMENTO RFM
# ═══════════════════════════════════════════════════════════════════════
section_divider('RECOMENDACIONES DE NEGOCIO')

RECS_RFM = {
    'Champions': {
        'icon': '👑', 'color': '#16A34A',
        'desc': 'Clientes recientes, frecuentes y de alto gasto',
        'estrategia': 'Programa de fidelización VIP',
        'acciones': 'Atención exclusiva, regalos, embajadores de marca',
        'kpi': 'Retention ≥ 95%',
    },
    'Leales': {
        'icon': '⭐', 'color': '#22C55E',
        'desc': 'Compran a menudo, valor sólido',
        'estrategia': 'Cross-selling y up-selling',
        'acciones': 'Recomendaciones personalizadas, productos premium',
        'kpi': '+15% ticket medio',
    },
    'Potenciales': {
        'icon': '🌱', 'color': DS6,
        'desc': 'Recientes pero compran poco',
        'estrategia': 'Aceleración de conversión',
        'acciones': 'Onboarding educativo, descuentos progresivos',
        'kpi': '+50% frecuencia',
    },
    'Necesitan atencion': {
        'icon': '🤝', 'color': DS3,
        'desc': 'Score medio en todas las dimensiones',
        'estrategia': 'Activación general',
        'acciones': 'Campañas estacionales, promociones segmentadas',
        'kpi': '+25% engagement',
    },
    'En riesgo': {
        'icon': '⚠️', 'color': DS5,
        'desc': 'Antes valiosos, ahora inactivos',
        'estrategia': 'Recuperación de churn',
        'acciones': 'Encuesta NPS, oferta retention, contacto comercial',
        'kpi': 'Reactivar ≥ 30%',
    },
    'Perdidos': {
        'icon': '💔', 'color': '#7C2D12',
        'desc': 'Inactivos hace tiempo, baja recuperabilidad',
        'estrategia': 'Última campaña o desinscripción',
        'acciones': 'Win-back final con oferta agresiva',
        'kpi': 'Optimizar coste',
    },
}

# Tabla showcase con recomendaciones
seg_counts = df['segmento_rfm'].value_counts()
orden_rfm = ['Champions', 'Leales', 'Potenciales',
             'Necesitan atencion', 'En riesgo', 'Perdidos']
orden_rfm = [s for s in orden_rfm if s in seg_counts.index]

headers = ['Segmento', 'Clientes', 'Estrategia', 'Acciones',
           'KPI objetivo', 'Ingresos generados']
rows = []
for seg in orden_rfm:
    r = RECS_RFM.get(seg, {})
    n = seg_counts[seg]
    pct = n / len(df) * 100
    ing = df.loc[df['segmento_rfm'] == seg, 'ingresos_t'].sum()
    pct_ing = ing / df['ingresos_t'].sum() * 100

    seg_html = (f'<div style="display:flex;align-items:center;gap:8px;">'
                f'<div style="font-size:24px;">{r.get("icon", "")}</div>'
                f'<div>'
                f'<div style="font-weight:700;color:{r.get("color", DS1)};">{seg}</div>'
                f'<div style="font-size:11px;color:{DS2};">{r.get("desc", "")}</div>'
                f'</div></div>')
    cli_html = f'<strong>{fmt_int(n)}</strong><br><span style="font-size:11px;color:{DS2};">{pct:.1f}%</span>'
    ing_html = (f'<strong style="color:{DS1};">{fmt_eur(ing)}</strong><br>'
                f'<span style="font-size:11px;color:{DS2};">{pct_ing:.1f}% del total</span>')
    rows.append([
        seg_html, cli_html,
        f'<strong>{r.get("estrategia", "—")}</strong>',
        r.get('acciones', '—'),
        f'<span style="color:{r.get("color", DS2)};font-weight:600;">{r.get("kpi", "—")}</span>',
        ing_html,
    ])
showcase_table(headers, rows)


# ═══════════════════════════════════════════════════════════════════════
#  ALERTA DE CHURN EN VALIOSOS
# ═══════════════════════════════════════════════════════════════════════
section_divider('🚨 ALERTA · CLIENTES VALIOSOS EN RIESGO')

if 'churn_proxy' in df.columns:
    valiosos_riesgo = df[
        df['churn_proxy'] &
        df['segmento_rfm'].isin(['Champions', 'Leales'])
    ]
    n_alerta = len(valiosos_riesgo)
    ing_alerta = valiosos_riesgo['ingresos_t'].sum()
    cltv_alerta = valiosos_riesgo['cltv'].sum()

    if n_alerta > 0:
        info_box(
            f'🚨 <strong>{n_alerta} clientes Champions/Leales</strong> '
            f'no han comprado en más de 180 días. Generan '
            f'<strong>{fmt_eur(ing_alerta)}</strong> de ingresos históricos '
            f'y <strong>{fmt_eur(cltv_alerta)}</strong> de CLTV acumulado. '
            f'Acción urgente recomendada.',
            kind='danger',
        )

        # Top 10 más valiosos en riesgo
        top_alerta = valiosos_riesgo.nlargest(10, 'cltv')
        headers = ['Cliente', 'Segmento RFM', 'CLTV', 'Ingresos',
                   'Días sin comprar', 'Recomendación']
        rows = []
        for _, r in top_alerta.iterrows():
            nombre = str(r.get('full_name', f'Cliente {r["customer_id"]}'))
            if len(nombre) > 30:
                nombre = nombre[:27] + '…'
            seg = r.get('segmento_rfm', '—')
            seg_color = '#16A34A' if seg == 'Champions' else '#22C55E'
            seg_html = (f'<span style="background:{seg_color}20;color:{seg_color};'
                        f'padding:4px 10px;border-radius:12px;font-weight:700;'
                        f'font-size:11px;">{seg}</span>')

            dias = int(r.get('dias_sin_compra', 0))
            dias_html = (f'<strong style="color:{DS5};">{dias}</strong>'
                         f' <span style="font-size:11px;color:{DS2};">días</span>')

            rec = ('Contacto comercial inmediato' if dias > 365
                   else 'Email de retención + descuento')

            rows.append([
                f'<strong>{nombre}</strong><br>'
                f'<span style="font-size:11px;color:{DS2};">ID: {int(r["customer_id"])}</span>',
                seg_html,
                f'<strong>{fmt_eur(r["cltv"])}</strong>',
                fmt_eur(r['ingresos_t']),
                dias_html,
                f'<em style="color:{DS5};">{rec}</em>',
            ])
        showcase_table(headers, rows)

        # Botón descarga
        c1, _ = st.columns([1, 3])
        with c1:
            csv = valiosos_riesgo.to_csv(index=False).encode('utf-8')
            st.download_button(
                f'⬇️ Descargar lista completa ({n_alerta} clientes)',
                data=csv,
                file_name='clientes_valiosos_en_riesgo.csv',
                mime='text/csv',
                use_container_width=True,
            )
    else:
        info_box(
            '✅ Ningún cliente Champion o Leal está en riesgo de churn. '
            'Excelente situación de fidelización.',
            kind='success',
        )
