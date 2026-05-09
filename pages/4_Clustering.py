"""
Página: PCA + Clustering — la pieza central del análisis.

Visualizaciones:
  - Scatter PCA interactivo con selector de coloreado (cluster, segmento, churn)
  - Heatmap de perfiles de cluster (features × clusters)
  - Strip plot de CLTV por cluster
  - Barras de clientes e ingresos por cluster
  - Tabla de perfil + recomendaciones de negocio
"""

import streamlit as st
import pandas as pd

from utils.styles import (
    inject_global_css, render_header, section_divider, section_title,
    kpi_row, info_box, showcase_table, badge,
    fmt_eur, fmt_int, fmt_pct, CLUSTER_PAL,
    DS1, DS2, DS3, DS5, DS6, DS7,
)
from utils.data_loader import load_all
from utils.charts import (
    scatter_pca, heatmap_cluster_features, strip_cltv_cluster, barras_cluster,
    radar_cluster_vs_global,
)

# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(page_title='Clustering · SalesHealth',
                   page_icon='🔮', layout='wide',
                   initial_sidebar_state='collapsed')
inject_global_css()

render_header(
    active_page='clustering',
    eyebrow='FASE 6 · MACHINE LEARNING',
    title='PCA + Clustering',
    subtitle=('Segmentación automática de clientes mediante reducción de '
              'dimensionalidad (PCA) y K-Means. Identificación de perfiles '
              'comerciales sin supervisión.'),
)

df = load_all()
if df.empty:
    info_box('❌ <strong>No hay datos.</strong> Ejecuta primero <code>04_cltv.ipynb</code> '
             'y luego <code>05_pca_clustering.ipynb</code>.', kind='danger')
    st.stop()

if 'cluster_label' not in df.columns:
    info_box(
        '⚠️ <strong>No se ha generado el clustering todavía.</strong> '
        'Ejecuta <code>05_pca_clustering.ipynb</code> para producir '
        '<code>clustering_resultados.csv</code> y vuelve a esta página.',
        kind='warning',
    )
    st.stop()


# ═══════════════════════════════════════════════════════════════════════
#  KPIs DE LA SEGMENTACIÓN
# ═══════════════════════════════════════════════════════════════════════
n_clusters = df['cluster_label'].nunique()
top_label  = df.groupby('cluster_label')['ingresos_t'].sum().idxmax()
top_n      = (df['cluster_label'] == top_label).sum()
top_pct    = top_n / len(df) * 100
top_ing    = df.loc[df['cluster_label'] == top_label, 'ingresos_t'].sum()
pct_ing    = top_ing / df['ingresos_t'].sum() * 100

kpi_row([
    {'value': fmt_int(len(df)),       'label': 'Clientes segmentados', 'color': 'primary'},
    {'value': str(n_clusters),         'label': 'Clusters identificados','color': 'cyan'},
    {'value': top_label,               'label': 'Segmento líder',       'color': 'gold'},
    {'value': f'{top_pct:.0f}%',       'label': f'% clientes en {top_label}', 'color': 'ocean'},
    {'value': f'{pct_ing:.0f}%',       'label': f'% ingresos del segmento líder', 'color': 'green'},
])

features_disponibles = [
    f for f in [
        'ingresos_t', 'margen_t', 'frecuencia_t', 'ticket_medio',
        'tasa_devolucion', 'dias_sin_compra',
    ] if f in df.columns
]
feature_labels = {
    'ingresos_t': 'ingresos',
    'margen_t': 'margen',
    'frecuencia_t': 'frecuencia',
    'ticket_medio': 'ticket',
    'tasa_devolucion': 'devoluciones',
    'dias_sin_compra': 'recency',
}
if features_disponibles:
    resumen_features = ', '.join(feature_labels.get(f, f) for f in features_disponibles)
    info_box(
        'El clustering se interpreta aquí sobre el espacio exportado por la '
        f'fase 6. Variables visibles en el dashboard: <strong>{resumen_features}</strong>.',
        kind='info',
    )


# ═══════════════════════════════════════════════════════════════════════
#  SCATTER PCA INTERACTIVO
# ═══════════════════════════════════════════════════════════════════════
section_divider('VISUALIZACIÓN PCA · 2D')

c_left, c_right = st.columns([3, 1])

with c_right:
    st.markdown(f"""
    <div style="background:white; border-radius:12px; padding:18px;
                box-shadow:0 2px 8px rgba(0,0,0,0.05); margin-top:8px;">
        <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.1em;
                    font-weight:700; color:{DS3}; margin-bottom:10px;">
            CONTROLES
        </div>
        <div style="font-size:13px; color:{DS2}; line-height:1.6; margin-bottom:8px;">
            Cambia el coloreado para ver cómo se distribuyen los clientes
            según diferentes criterios analíticos.
        </div>
    </div>
    """, unsafe_allow_html=True)

    color_options = {'cluster_label': '🔮 Cluster K-Means'}
    if 'segmento_cltv' in df.columns:
        color_options['segmento_cltv'] = '💰 Segmento CLTV'
    if 'segmento_rfm' in df.columns:
        color_options['segmento_rfm'] = '🎯 Segmento RFM'
    if 'churn_proxy' in df.columns:
        color_options['churn_proxy'] = '⚠️ Riesgo de churn'

    color_by = st.selectbox(
        'Colorear por:',
        options=list(color_options.keys()),
        format_func=lambda k: color_options[k],
        index=0,
    )

    info_box(
        f'<strong>{n_clusters} clusters</strong> identificados con K-Means '
        f'sobre un set seleccionado de variables de comportamiento. '
        f'PCA solo se usa para visualización 2D del espacio segmentado.',
        kind='info',
    )

with c_left:
    df_plot = df.copy()
    if color_by == 'churn_proxy':
        df_plot['churn_proxy'] = df_plot['churn_proxy'].map(
            {True: '🔴 En riesgo', False: '🟢 Activo'})
    fig = scatter_pca(df_plot, color_by=color_by)
    st.plotly_chart(fig, use_container_width=True, theme=None)


# ═══════════════════════════════════════════════════════════════════════
#  RADAR + PERFIL POR CLUSTER
# ═══════════════════════════════════════════════════════════════════════
section_divider('PERFIL DE CADA CLUSTER')

c1, c2 = st.columns([1.1, 1])

with c1:
    section_title('Comparativa de features por cluster', label='HEATMAP')
    info_box(
        'Cada fila es un cluster. Cada columna es una métrica clave. '
        'El color indica el nivel relativo (<strong>azul oscuro = más alto</strong>). '
        'La tasa de devolución está invertida: azul oscuro = menos devoluciones.',
        kind='info',
    )
    fig_heatmap = heatmap_cluster_features(df)
    st.plotly_chart(fig_heatmap, use_container_width=True, theme=None)

with c2:
    section_title('Métricas medias por cluster', label='TABLA RESUMEN')
    perfil = df.groupby('cluster_label').agg(
        clientes=('customer_id', 'count'),
        cltv_medio=('cltv', 'mean'),
        ingresos_medio=('ingresos_t', 'mean'),
        ticket_medio=('ticket_medio', 'mean'),
    ).round(0)
    perfil = perfil.sort_values('ingresos_medio', ascending=False)

    headers = ['Segmento', 'Clientes', 'CLTV medio', 'Ing. medio', 'Ticket medio']
    rows = []
    for label, r in perfil.iterrows():
        clu_idx = sorted(df['cluster_label'].unique()).index(label)
        color = CLUSTER_PAL[clu_idx % len(CLUSTER_PAL)]
        rows.append([
            f'<span style="display:inline-flex;align-items:center;gap:6px;">'
            f'<span style="display:inline-block;width:10px;height:10px;'
            f'background:{color};border-radius:50%;"></span>'
            f'<strong>{label}</strong></span>',
            fmt_int(r['clientes']),
            fmt_eur(r['cltv_medio']),
            fmt_eur(r['ingresos_medio']),
            fmt_eur(r['ticket_medio']),
        ])
    showcase_table(headers, rows)


# ═══════════════════════════════════════════════════════════════════════
#  RADAR INDIVIDUAL DE CLUSTER (comparado con la media global)
# ═══════════════════════════════════════════════════════════════════════
section_divider('PERFIL INDIVIDUAL DE UN CLUSTER')

c_sel, c_rad = st.columns([1, 2])

clusters_ordenados = sorted(df['cluster_label'].dropna().unique().tolist())

with c_sel:
    section_title('Selecciona un cluster', label='COMPARATIVA RADAR')
    cluster_sel = st.selectbox(
        'Cluster a analizar',
        options=clusters_ordenados,
        index=0,
        key='cluster_radar_sel',
    )

    sub = df[df['cluster_label'] == cluster_sel]
    n_sub  = len(sub)
    pct    = n_sub / len(df) * 100
    ing_sub = sub['ingresos_t'].sum()
    pct_ing = ing_sub / df['ingresos_t'].sum() * 100 if df['ingresos_t'].sum() else 0
    cltv_med = sub['cltv'].mean() if 'cltv' in sub else 0

    info_box(
        f'<strong>{cluster_sel}</strong><br>'
        f'· {fmt_int(n_sub)} clientes ({pct:.1f}% del total)<br>'
        f'· {fmt_eur(ing_sub)} de ingresos ({pct_ing:.1f}%)<br>'
        f'· CLTV medio: <strong>{fmt_eur(cltv_med)}</strong>',
        kind='info',
    )

with c_rad:
    if n_sub > 0:
        fig_radar_cl = radar_cluster_vs_global(df, cluster_sel)
        st.plotly_chart(fig_radar_cl, use_container_width=True, theme=None)
    else:
        info_box('No hay clientes en este cluster.', kind='warning')


# ═══════════════════════════════════════════════════════════════════════
#  STRIP PLOT + BARRAS
# ═══════════════════════════════════════════════════════════════════════
section_divider('DISTRIBUCIÓN DE VALOR POR CLUSTER')

c1, c2 = st.columns([1, 1])
with c1:
    fig_strip = strip_cltv_cluster(df)
    st.plotly_chart(fig_strip, use_container_width=True, theme=None)
with c2:
    fig_barras = barras_cluster(df)
    st.plotly_chart(fig_barras, use_container_width=True, theme=None)


# ═══════════════════════════════════════════════════════════════════════
#  RECOMENDACIONES DE NEGOCIO
# ═══════════════════════════════════════════════════════════════════════
section_divider('RECOMENDACIONES DE NEGOCIO POR SEGMENTO')

# Mapping label → recomendación
RECOMENDACIONES = {
    'VIP': {
        'icon': '👑',
        'estrategia': 'Programa de fidelización exclusivo',
        'acciones': 'Atención personalizada, eventos privados, descuentos selectos',
        'objetivo': 'Maximizar retención y advocacy',
        'kpi':       'Retention rate ≥ 95%',
        'badge':     'success',
    },
    'Fidelizados': {
        'icon': '🌟',
        'estrategia': 'Cross-selling de productos premium',
        'acciones': 'Recomendaciones personalizadas, early access a nuevos productos',
        'objetivo': 'Incrementar ticket medio',
        'kpi':       '+15% ticket medio',
        'badge':     'info',
    },
    'Alto valor': {
        'icon': '💎',
        'estrategia': 'Up-selling y consolidación',
        'acciones': 'Programa de puntos, ofertas escalonadas, comunicaciones segmentadas',
        'objetivo': 'Subir a Fidelizados/VIP',
        'kpi':       '+20% frecuencia',
        'badge':     'info',
    },
    'Regular': {
        'icon': '⭐',
        'estrategia': 'Activación y crecimiento',
        'acciones': 'Campañas de email marketing, descuentos por volumen',
        'objetivo': 'Aumentar frecuencia de compra',
        'kpi':       '+30% compras/año',
        'badge':     'info',
    },
    'Ocasional': {
        'icon': '🌱',
        'estrategia': 'Engagement y educación',
        'acciones': 'Newsletter educativo, primer descuento, programa de bienvenida',
        'objetivo': 'Convertir en clientes Regulares',
        'kpi':       '+40% retorno',
        'badge':     'warning',
    },
    'Bajo valor': {
        'icon': '🔄',
        'estrategia': 'Reactivación coste-eficiente',
        'acciones': 'Email de reactivación, oferta de comeback, encuesta de motivos',
        'objetivo': 'Recuperar engagement o aceptar churn',
        'kpi':       '20% reactivación',
        'badge':     'warning',
    },
    'Inactivos': {
        'icon': '💤',
        'estrategia': 'Win-back o desinscripción',
        'acciones': 'Última campaña de reactivación, limpieza de base si no responden',
        'objetivo': 'Optimizar costes de marketing',
        'kpi':       'Churn rate aceptable',
        'badge':     'danger',
    },
    'En riesgo': {
        'icon': '⚠️',
        'estrategia': 'Prevención del churn',
        'acciones': 'Encuesta de satisfacción, oferta retention, contacto comercial',
        'objetivo': 'Recuperar antes de que abandonen',
        'kpi':       'Churn < 30%',
        'badge':     'danger',
    },
    'Potenciales': {
        'icon': '🚀',
        'estrategia': 'Aceleración de conversión',
        'acciones': 'Onboarding personalizado, descuentos progresivos',
        'objetivo': 'Subir a Alto valor',
        'kpi':       '+50% gasto/cliente',
        'badge':     'info',
    },
}
DEFAULT_REC = {
    'icon': '🎯',
    'estrategia': 'Análisis específico requerido',
    'acciones': 'Estudio comportamental para definir estrategia',
    'objetivo': 'Caracterizar comportamiento',
    'kpi':       'KPIs por definir',
    'badge':     'info',
}

# Tabla showcase de recomendaciones
labels_unicos = df.groupby('cluster_label')['ingresos_t'].mean()\
                  .sort_values(ascending=False).index.tolist()

headers = ['Segmento', 'Estrategia', 'Acciones recomendadas', 'Objetivo', 'KPI sugerido']
rows = []
for label in labels_unicos:
    r = RECOMENDACIONES.get(label, DEFAULT_REC)
    clu_idx = sorted(df['cluster_label'].unique()).index(label)
    color = CLUSTER_PAL[clu_idx % len(CLUSTER_PAL)]
    n = (df['cluster_label'] == label).sum()
    seg_html = (f'<div style="display:flex;align-items:center;gap:8px;">'
                f'<div style="font-size:22px;">{r["icon"]}</div>'
                f'<div>'
                f'<div style="font-weight:700;color:{DS1};">{label}</div>'
                f'<div style="font-size:11px;color:{DS2};">{n:,} clientes</div>'
                f'</div></div>'.replace(',', '.'))
    rows.append([
        seg_html,
        f'<strong>{r["estrategia"]}</strong>',
        r['acciones'],
        f'<em>{r["objetivo"]}</em>',
        f'<span style="color:{DS2};font-weight:600;">{r["kpi"]}</span>',
    ])
showcase_table(headers, rows)


# ═══════════════════════════════════════════════════════════════════════
#  EXPORTACIÓN
# ═══════════════════════════════════════════════════════════════════════
section_divider('EXPORTACIÓN', thin=True)
c1, _ = st.columns([1, 3])
with c1:
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        '⬇️ Descargar dataset completo (CSV)',
        data=csv_data,
        file_name='clientes_segmentados.csv',
        mime='text/csv',
        use_container_width=True,
    )
