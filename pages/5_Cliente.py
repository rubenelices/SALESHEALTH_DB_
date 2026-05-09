"""
Página: Exploración individual de cliente.

Visualizaciones:
  - Búsqueda por ID o nombre parcial
  - Ficha completa del cliente seleccionado
  - Gauge de percentil dentro de su cluster
  - Radar individual: cliente vs media de su cluster
  - Top 5 clientes similares (distancia euclidiana)
"""

import streamlit as st
import pandas as pd
import numpy as np

from utils.styles import (
    inject_global_css, render_header, section_divider, section_title,
    kpi_row, info_box, showcase_table, badge,
    fmt_eur, fmt_int, fmt_pct, CLUSTER_PAL, PAL_SEG,
    DS1, DS2, DS3, DS5, DS6, DS7, GRAY,
)
from utils.data_loader import load_all, clientes_similares, buscar_clientes
from utils.charts import gauge_percentil, radar_cliente_vs_cluster

# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(page_title='Cliente · SalesHealth',
                   page_icon='👤', layout='wide',
                   initial_sidebar_state='collapsed')
inject_global_css()

render_header(
    active_page='cliente',
    eyebrow='EXPLORACIÓN INDIVIDUAL',
    title='Ficha de cliente',
    subtitle=('Buscador por ID, nombre o email. Métricas completas, posición '
              'percentil dentro de su cluster, comparativa con la media '
              'del segmento y top 5 clientes similares.'),
)

df = load_all()
if df.empty:
    info_box('❌ <strong>No hay datos.</strong> Ejecuta primero <code>04_cltv.ipynb</code>.',
             kind='danger')
    st.stop()


# ═══════════════════════════════════════════════════════════════════════
#  BÚSQUEDA
# ═══════════════════════════════════════════════════════════════════════
section_title('Buscar cliente', label='SELECCIÓN')

c0, c1, c2 = st.columns([2, 2, 1])

# Texto libre: ID, nombre o email
with c0:
    texto = st.text_input(
        'Buscar por ID, nombre o email',
        value='',
        placeholder='Ej.: 1234, "García", "@gmail.com"…',
        key='cliente_texto_busqueda',
    )

# Segmento — condiciona las opciones del buscador
with c2:
    if 'segmento_cltv' in df.columns:
        seg_filter = st.selectbox(
            'Filtrar por segmento CLTV',
            options=['Todos', 'Alto', 'Medio', 'Bajo'],
            index=0,
        )
    else:
        seg_filter = 'Todos'

df_busca = df.copy()
if seg_filter != 'Todos':
    df_busca = df_busca[df_busca['segmento_cltv'] == seg_filter]

# Si hay texto, primero filtrar por búsqueda flexible
if texto:
    df_busca = buscar_clientes(df_busca, texto, limit=200)

df_busca_sorted = df_busca.sort_values('full_name') \
    if 'full_name' in df_busca.columns else df_busca

_PLACEHOLDER = '— Selecciona un cliente —'
opciones_map = {
    f"{r.get('full_name', 'Desconocido')}  ·  ID {int(r['customer_id'])}": int(r['customer_id'])
    for _, r in df_busca_sorted.iterrows()
}
opciones_list = [_PLACEHOLDER] + list(opciones_map.keys())

with c1:
    if texto and not opciones_map:
        st.selectbox('Resultados', options=['(sin coincidencias)'], disabled=True)
        seleccion = _PLACEHOLDER
    else:
        label = (f'Resultados ({len(opciones_map)})' if texto
                 else 'Buscar cliente por nombre o ID')
        seleccion = st.selectbox(
            label,
            options=opciones_list,
            index=0,
            key='cliente_selectbox',
        )

# ═══════════════════════════════════════════════════════════════════════
#  ESTADO INICIAL — sin selección
# ═══════════════════════════════════════════════════════════════════════
cliente = None

if seleccion == _PLACEHOLDER:
    info_box(
        '👋 Escribe en el desplegable de arriba para filtrar por <strong>nombre</strong> '
        'o por <strong>ID</strong>. Las opciones se actualizan a medida que escribes.',
        kind='info',
    )
    if 'full_name' in df.columns:
        sample = df.sample(min(5, len(df)), random_state=42)
        section_title('Ejemplos de clientes', label='SUGERENCIAS')
        headers = ['ID', 'Nombre', 'CLTV', 'Segmento', 'Estado']
        rows = []
        for _, r in sample.iterrows():
            seg = r.get('segmento_cltv', '—')
            seg_b = badge(seg, seg.lower()) if seg in ('Alto', 'Medio', 'Bajo') else seg
            estado = badge('🔴 En riesgo', 'churn') if r.get('churn_proxy', False) \
                     else badge('🟢 Activo', 'active')
            rows.append([
                f'<strong>{int(r["customer_id"])}</strong>',
                r.get('full_name', '—'),
                f'<strong style="color:{DS1};">{fmt_eur(r["cltv"])}</strong>',
                seg_b, estado,
            ])
        showcase_table(headers, rows)
    st.stop()

# Obtener el cliente seleccionado
cid = opciones_map.get(seleccion)
if cid is None:
    info_box('❌ No se pudo identificar el cliente seleccionado.', kind='warning')
    st.stop()

cliente = df[df['customer_id'] == cid].iloc[0]


# ═══════════════════════════════════════════════════════════════════════
#  FICHA DEL CLIENTE
# ═══════════════════════════════════════════════════════════════════════
section_divider(f'CLIENTE #{int(cliente["customer_id"])}')

nombre = cliente.get('full_name', f'Cliente {int(cliente["customer_id"])}')
seg_cltv = cliente.get('segmento_cltv', '—')
cluster = cliente.get('cluster_label', '—')
seg_rfm = cliente.get('segmento_rfm', '—')
churn = bool(cliente.get('churn_proxy', False))

# Header del cliente
estado_badge = badge('🔴 En riesgo de churn', 'churn') if churn \
    else badge('🟢 Cliente activo', 'active')

st.markdown(f"""
<div style="background:linear-gradient(135deg, {DS1} 0%, {DS2} 100%);
            color:white; padding:28px 32px; border-radius:18px;
            box-shadow:0 6px 20px rgba(3,4,94,0.25); margin-bottom:18px;">
    <div style="display:flex; align-items:center; justify-content:space-between;
                flex-wrap:wrap; gap:16px;">
        <div>
            <div style="font-size:11px; text-transform:uppercase;
                        letter-spacing:0.16em; opacity:0.8; margin-bottom:4px;">
                Cliente · ID {int(cliente["customer_id"])}
            </div>
            <div style="font-size:36px; font-weight:800; letter-spacing:-0.02em;">
                {nombre}
            </div>
            <div style="margin-top:10px; opacity:0.85; font-size:13px;">
                Segmento CLTV: <strong>{seg_cltv}</strong>  ·
                Cluster: <strong>{cluster}</strong>  ·
                Segmento RFM: <strong>{seg_rfm}</strong>
            </div>
        </div>
        <div>{estado_badge}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# KPIs del cliente
kpi_row([
    {'value': fmt_eur(cliente['cltv']),
     'label': 'CLTV',                 'color': 'primary'},
    {'value': fmt_eur(cliente['ingresos_t']),
     'label': 'Ingresos totales',     'color': 'ocean'},
    {'value': f'{cliente.get("frecuencia_t", 0):.2f}',
     'label': 'Frecuencia (v/mes)',    'color': 'cyan'},
    {'value': fmt_eur(cliente.get('ticket_medio', 0)),
     'label': 'Ticket medio',          'color': 'gold'},
    {'value': fmt_pct(cliente.get('tasa_devolucion', 0) * 100, decimals=2),
     'label': 'Tasa devolución',       'color': 'coral'},
    {'value': fmt_int(cliente.get('dias_sin_compra', 0)),
     'label': 'Días sin comprar',     'color': 'green'
     if cliente.get('dias_sin_compra', 999) <= 180 else 'coral'},
])


# ═══════════════════════════════════════════════════════════════════════
#  GAUGE PERCENTIL + RADAR
# ═══════════════════════════════════════════════════════════════════════
section_divider('POSICIÓN DEL CLIENTE')

c1, c2 = st.columns([1, 1.2])

with c1:
    section_title('Percentil de CLTV en su cluster', label='POSICIÓN')

    if 'cluster' in df.columns and not pd.isna(cliente.get('cluster')):
        cluster_id = cliente['cluster']
        cluster_df = df[df['cluster'] == cluster_id]
        cltv_values = cluster_df['cltv'].sort_values().values
        # Percentil del cliente
        percentil = (cltv_values <= cliente['cltv']).sum() / len(cltv_values) * 100
        fig_gauge = gauge_percentil(percentil,
                                     label=f'Percentil CLTV en cluster "{cluster}"')
        st.plotly_chart(fig_gauge, use_container_width=True, theme=None)

        if percentil >= 75:
            info_box(
                f'💎 Este cliente está en el <strong>top {100-percentil:.0f}%</strong> '
                f'de su cluster <strong>{cluster}</strong>. Es uno de los más '
                f'valiosos de su segmento.',
                kind='success',
            )
        elif percentil >= 50:
            info_box(
                f'⭐ Este cliente está por encima de la mediana en su cluster '
                f'<strong>{cluster}</strong> (percentil {percentil:.0f}).',
                kind='info',
            )
        else:
            info_box(
                f'🌱 Este cliente está en el <strong>{percentil:.0f}%</strong> '
                f'inferior de su cluster <strong>{cluster}</strong>. Hay '
                f'margen de crecimiento.',
                kind='warning',
            )

with c2:
    section_title('Cliente vs media del cluster', label='COMPARATIVA')

    if 'cluster' in df.columns and not pd.isna(cliente.get('cluster')):
        cluster_id = cliente['cluster']
        cluster_df = df[df['cluster'] == cluster_id]
        feats_radar = ['ingresos_t', 'margen_t', 'frecuencia_t',
                       'ticket_medio', 'tasa_devolucion']
        feats_radar = [f for f in feats_radar if f in df.columns]
        cluster_medio = cluster_df[feats_radar].mean()
        fig_radar = radar_cliente_vs_cluster(cliente, cluster_medio, feats_radar)
        st.plotly_chart(fig_radar, use_container_width=True, theme=None)


# ═══════════════════════════════════════════════════════════════════════
#  CLIENTES SIMILARES
# ═══════════════════════════════════════════════════════════════════════
section_divider('CLIENTES SIMILARES')

if 'cluster' in df.columns:
    similares = clientes_similares(df, int(cliente['customer_id']), n=5)

    if not similares.empty:
        section_title(
            f'Top 5 clientes más parecidos en el cluster "{cluster}"',
            label='RECOMENDADOS',
        )
        info_box(
            'Distancia calculada en el espacio analítico disponible del '
            'clustering exportado. Si hay coordenadas PCA, se usan como base '
            'principal y se complementan con variables de comportamiento '
            'comparables.',
            kind='info',
        )

        headers = ['Distancia', 'ID', 'Nombre', 'CLTV', 'Ingresos',
                   'Frecuencia', 'Estado']
        rows = []
        for _, r in similares.iterrows():
            dist = r['distancia']
            # Visual de distancia
            barras_w = max(0.05, 1 - dist/3)
            dist_html = (f'<div style="display:flex;flex-direction:column;'
                         f'align-items:flex-start;gap:2px;">'
                         f'<div style="width:60px;height:6px;background:#E5E7EB;'
                         f'border-radius:3px;overflow:hidden;">'
                         f'<div style="width:{barras_w*100:.0f}%;height:100%;'
                         f'background:linear-gradient(90deg,{DS3},{DS2});"></div>'
                         f'</div>'
                         f'<span style="font-size:10px;color:{DS2};">{dist:.2f}</span>'
                         f'</div>')

            nombre_s = str(r.get('full_name', f'Cliente {int(r["customer_id"])}'))
            if len(nombre_s) > 28:
                nombre_s = nombre_s[:25] + '…'

            estado_html = (badge('🔴 Riesgo', 'churn')
                           if r.get('churn_proxy', False)
                           else badge('🟢 Activo', 'active'))

            rows.append([
                dist_html,
                f'<strong>{int(r["customer_id"])}</strong>',
                f'<strong>{nombre_s}</strong>',
                f'<strong style="color:{DS1};">{fmt_eur(r["cltv"])}</strong>',
                fmt_eur(r['ingresos_t']),
                f'{r["frecuencia_t"]:.2f} v/mes',
                estado_html,
            ])
        showcase_table(headers, rows)
    else:
        info_box('No se han podido calcular clientes similares para este caso.',
                 kind='warning')
else:
    info_box(
        'Se requiere el resultado de clustering para calcular clientes similares. '
        'Ejecuta <code>05_pca_clustering.ipynb</code>.',
        kind='warning',
    )


# ═══════════════════════════════════════════════════════════════════════
#  RECOMENDACIÓN PERSONALIZADA
# ═══════════════════════════════════════════════════════════════════════
section_divider('ACCIÓN RECOMENDADA', thin=True)

if churn and seg_cltv == 'Alto':
    info_box(
        f'🚨 <strong>PRIORIDAD MÁXIMA · Cliente Alto en riesgo de churn.</strong><br>'
        f'CLTV: {fmt_eur(cliente["cltv"])}, lleva '
        f'{int(cliente.get("dias_sin_compra", 0))} días sin comprar.<br>'
        f'<strong>Acción:</strong> contacto comercial inmediato + oferta '
        f'personalizada de retention. Riesgo de pérdida significativa.',
        kind='danger',
    )
elif churn:
    info_box(
        f'⚠️ <strong>Cliente en riesgo de churn.</strong><br>'
        f'Lleva {int(cliente.get("dias_sin_compra", 0))} días sin comprar.<br>'
        f'<strong>Acción:</strong> email de reactivación + oferta de descuento '
        f'segmentada por su perfil de compra histórico.',
        kind='warning',
    )
elif seg_cltv == 'Alto':
    info_box(
        f'💎 <strong>Cliente de alto valor activo.</strong><br>'
        f'<strong>Acción:</strong> mantener calidad del servicio + '
        f'cross-selling de productos premium. Considerar inclusión en '
        f'programa VIP si aún no participa.',
        kind='success',
    )
else:
    info_box(
        f'⭐ <strong>Cliente activo en segmento {seg_cltv}.</strong><br>'
        f'<strong>Acción:</strong> mantener engagement con campañas '
        f'segmentadas y monitorizar evolución del CLTV trimestralmente.',
        kind='info',
    )
