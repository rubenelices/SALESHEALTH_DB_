"""
Funciones Plotly reutilizables para el dashboard.
Todas devuelven un objeto plotly.graph_objects.Figure listo para st.plotly_chart.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .styles import (
    DS1, DS2, DS3, DS4, DS5, DS6, DS7, GRAY,
    CLUSTER_PAL, PAL_SEG,
)

# ═══════════════════════════════════════════════════════════════════════
#  TEMA / LAYOUT POR DEFECTO
# ═══════════════════════════════════════════════════════════════════════
def _apply_theme(fig: go.Figure, height: int = 420, title: str = '',
                 showlegend: bool = True) -> go.Figure:
    """Aplica el tema Deep Sky a cualquier figura Plotly."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=DS1, family='Inter',
                                          weight=700)) if title else None,
        font=dict(family='Inter', size=12, color='#1F2937'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=height,
        margin=dict(l=40, r=20, t=50 if title else 30, b=40),
        showlegend=showlegend,
        legend=dict(
            bgcolor='rgba(255,255,255,0.85)',
            bordercolor='#E5E7EB',
            borderwidth=1,
            font=dict(size=11),
        ),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor=DS3,
            font=dict(family='Inter', size=12, color=DS1),
        ),
    )
    fig.update_xaxes(
        showgrid=True, gridcolor='#F1F5F9', zeroline=False,
        tickfont=dict(size=11, color=GRAY),
        title_font=dict(size=12, color=DS1, weight=600),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor='#F1F5F9', zeroline=False,
        tickfont=dict(size=11, color=GRAY),
        title_font=dict(size=12, color=DS1, weight=600),
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  GRÁFICOS PARA PÁGINA KPIs
# ═══════════════════════════════════════════════════════════════════════
def area_ingresos_anio(df: pd.DataFrame) -> go.Figure:
    """Área chart de ingresos totales por año (basado en first_purchase_date)."""
    if 'anio_primera_compra' not in df.columns:
        return go.Figure()

    s = df.groupby('anio_primera_compra')['ingresos_t'].sum().reset_index()
    s = s.dropna()
    s['anio_primera_compra'] = s['anio_primera_compra'].astype(int)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=s['anio_primera_compra'],
        y=s['ingresos_t'],
        mode='lines+markers',
        line=dict(color=DS2, width=3),
        marker=dict(size=10, color=DS3, line=dict(color='white', width=2)),
        fill='tozeroy',
        fillcolor='rgba(0, 180, 216, 0.18)',
        hovertemplate='<b>%{x}</b><br>Ingresos: %{y:,.0f} €<extra></extra>',
    ))
    fig = _apply_theme(fig, height=380, showlegend=False)
    fig.update_xaxes(title='Año primera compra', dtick=1)
    fig.update_yaxes(title='Ingresos (€)', tickformat=',.0f')
    return fig


def treemap_segmento_cluster(df: pd.DataFrame) -> go.Figure:
    """Barras horizontales apiladas: ingresos por cluster y segmento CLTV."""
    if 'cluster_label' not in df.columns or 'segmento_cltv' not in df.columns:
        agg = df.groupby('segmento_cltv', as_index=False)['ingresos_t'].sum()
        agg = agg.sort_values('ingresos_t', ascending=True)
        fig = go.Figure(go.Bar(
            x=agg['ingresos_t'],
            y=agg['segmento_cltv'],
            orientation='h',
            marker=dict(
                color=[PAL_SEG.get(seg, DS3) for seg in agg['segmento_cltv']],
                line=dict(color='white', width=1.2),
            ),
            text=agg['ingresos_t'].map(lambda v: f'{v/1e6:.2f}M€'),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Ingresos: %{x:,.0f} €<extra></extra>',
        ))
        fig = _apply_theme(fig, height=420, showlegend=False,
                           title='Ingresos por segmento CLTV')
        fig.update_xaxes(title='Ingresos (€)', tickformat=',.0f')
        fig.update_yaxes(title='')
        fig.update_layout(margin=dict(l=80, r=40, t=50, b=40))
        return fig

    agg = df.groupby(['cluster_label', 'segmento_cltv'], as_index=False)['ingresos_t'].sum()
    totals = agg.groupby('cluster_label', as_index=False)['ingresos_t'].sum() \
                .sort_values('ingresos_t', ascending=True)
    orden_clusters = totals['cluster_label'].tolist()
    orden_seg = [s for s in ['Alto', 'Medio', 'Bajo'] if s in agg['segmento_cltv'].unique()]

    fig = px.bar(
        agg,
        x='ingresos_t',
        y='cluster_label',
        color='segmento_cltv',
        orientation='h',
        category_orders={
            'cluster_label': orden_clusters,
            'segmento_cltv': orden_seg,
        },
        color_discrete_map=PAL_SEG,
        text=agg['ingresos_t'].map(lambda v: f'{v/1e6:.2f}M€' if v >= 1e6 else ''),
    )
    fig.update_traces(
        marker_line=dict(color='white', width=1),
        textposition='inside',
        hovertemplate='<b>%{y}</b><br>Segmento CLTV: %{fullData.name}<br>'
                      'Ingresos: %{x:,.0f} €<extra></extra>',
    )
    fig = _apply_theme(fig, height=420,
                       title='Ingresos por cluster y composición CLTV')
    fig.update_xaxes(title='Ingresos totales (€)', tickformat=',.0f')
    fig.update_yaxes(title='Cluster')
    fig.update_layout(
        barmode='stack',
        legend=dict(title='Segmento CLTV', orientation='h', y=1.12, x=0),
        margin=dict(l=90, r=30, t=60, b=40),
    )
    return fig


def distribucion_clientes_cluster(df: pd.DataFrame) -> go.Figure:
    """Distribución de clientes por cluster en formato barra horizontal."""
    if 'cluster_label' not in df.columns:
        return go.Figure()

    agg = df.groupby('cluster_label', as_index=False).agg(
        clientes=('customer_id', 'count'),
    ).sort_values('clientes', ascending=True)
    total = agg['clientes'].sum()
    agg['pct'] = np.where(total > 0, agg['clientes'] / total * 100, 0)

    color_map = {
        label: CLUSTER_PAL[i % len(CLUSTER_PAL)]
        for i, label in enumerate(agg['cluster_label'].tolist())
    }

    fig = go.Figure(go.Bar(
        x=agg['clientes'],
        y=agg['cluster_label'],
        orientation='h',
        marker=dict(
            color=[color_map[label] for label in agg['cluster_label']],
            line=dict(color='white', width=1.2),
        ),
        text=[
            f'{int(n):,} clientes · {pct:.1f}%'.replace(',', '.')
            for n, pct in zip(agg['clientes'], agg['pct'])
        ],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Clientes: %{x:,}<extra></extra>',
    ))
    fig = _apply_theme(fig, height=360, showlegend=False,
                       title='Distribución de clientes por cluster')
    fig.update_xaxes(title='Número de clientes', separatethousands=True)
    fig.update_yaxes(title='Cluster')
    fig.update_layout(margin=dict(l=80, r=90, t=55, b=40))
    return fig


def donut_segmento(df: pd.DataFrame, columna: str = 'segmento_cltv') -> go.Figure:
    """Donut de ingresos por segmento."""
    if columna not in df.columns:
        return go.Figure()
    agg = df.groupby(columna)['ingresos_t'].sum().reset_index()
    if columna == 'segmento_cltv':
        orden = ['Alto', 'Medio', 'Bajo']
        agg = agg.set_index(columna).reindex(orden).reset_index()
        colores = [PAL_SEG[s] for s in agg[columna]]
    else:
        colores = CLUSTER_PAL[:len(agg)]

    fig = go.Figure(go.Pie(
        labels=agg[columna],
        values=agg['ingresos_t'],
        hole=0.55,
        marker=dict(colors=colores, line=dict(color='white', width=3)),
        textinfo='label+percent',
        textfont=dict(family='Inter', size=13, color='white', weight=600),
        hovertemplate='<b>%{label}</b><br>Ingresos: %{value:,.0f} €<br>'
                      '%{percent}<extra></extra>',
    ))
    total = agg['ingresos_t'].sum() / 1e6
    fig.add_annotation(
        text=f'<b>{total:.2f}M€</b><br><span style="font-size:11px;color:#64748B">'
             f'Total ingresos</span>',
        showarrow=False, font=dict(family='Inter', size=20, color=DS1),
    )
    fig = _apply_theme(fig, height=380, showlegend=False)
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  GRÁFICOS PARA PÁGINA CLTV
# ═══════════════════════════════════════════════════════════════════════
def histograma_cltv(df: pd.DataFrame, log_scale: bool = False) -> go.Figure:
    """Histograma CLTV con líneas P25/P75.

    Si `log_scale=True`, representa log1p(CLTV) para comprimir la cola alta
    y hacer más legible la masa central de clientes.
    """
    p25 = df['cltv'].quantile(0.25)
    p75 = df['cltv'].quantile(0.75)
    clip = df['cltv'].quantile(0.97)
    cltv_clip = df['cltv'].clip(upper=clip)
    x_vals = np.log1p(cltv_clip) if log_scale else cltv_clip

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=x_vals, nbinsx=50,
        marker=dict(color=DS3, line=dict(color='white', width=0.5)),
        opacity=0.85,
        hovertemplate=('log1p(CLTV): %{x:.2f}<br>Clientes: %{y}<extra></extra>'
                       if log_scale else
                       'CLTV: %{x:,.0f} €<br>Clientes: %{y}<extra></extra>'),
    ))
    # Líneas de percentiles
    for x_val, color, label in [(p25, DS5, f'P25 = {p25:,.0f} €'),
                                 (p75, DS7, f'P75 = {p75:,.0f} €')]:
        x_line = np.log1p(x_val) if log_scale else x_val
        fig.add_vline(x=x_line, line=dict(color=color, width=2, dash='dash'),
                      annotation_text=label,
                      annotation_position='top',
                      annotation_font=dict(family='Inter', size=11, color=color))

    fig = _apply_theme(fig, height=380, showlegend=False,
                       title=('Distribución de CLTV (escala log · clip P97)'
                              if log_scale else
                              'Distribución de CLTV (clip P97)'))
    if log_scale:
        tick_vals = [0, np.log1p(100), np.log1p(500), np.log1p(1000),
                     np.log1p(2500), np.log1p(5000), np.log1p(float(clip))]
        tick_text = ['0 €', '100 €', '500 €', '1k €', '2.5k €', '5k €',
                     f'{clip/1e3:.1f}k €']
        fig.update_xaxes(title='CLTV (€) · escala log', tickmode='array',
                         tickvals=tick_vals, ticktext=tick_text)
    else:
        fig.update_xaxes(title='CLTV (€)', tickformat=',.0f')
    fig.update_yaxes(title='Número de clientes')
    return fig


def violin_cltv_segmento(df: pd.DataFrame) -> go.Figure:
    """Violin plot de CLTV por segmento."""
    clip = df['cltv'].quantile(0.97)
    df_clip = df.copy()
    df_clip['cltv_clip'] = df_clip['cltv'].clip(upper=clip)
    orden = ['Alto', 'Medio', 'Bajo']

    fig = go.Figure()
    for seg in orden:
        sub = df_clip[df_clip['segmento_cltv'] == seg]
        fig.add_trace(go.Violin(
            y=sub['cltv_clip'], name=seg,
            box=dict(visible=True, fillcolor='white', line=dict(color=DS1, width=1.5)),
            meanline=dict(visible=True),
            line=dict(color=PAL_SEG[seg]),
            fillcolor=PAL_SEG[seg],
            opacity=0.65,
            points=False,
            hovertemplate=f'<b>{seg}</b><br>CLTV: %{{y:,.0f}} €<extra></extra>',
        ))
    fig = _apply_theme(fig, height=400, showlegend=False,
                       title='Distribución de CLTV por segmento (clip P97)')
    fig.update_yaxes(title='CLTV (€)', tickformat=',.0f')
    fig.update_xaxes(title='Segmento CLTV')
    return fig


def bubble_ingresos_frecuencia(df: pd.DataFrame) -> go.Figure:
    """Bubble chart: ingresos vs frecuencia, size=ticket, color=segmento."""
    df_plot = df.copy()
    # Clip outliers para legibilidad
    df_plot['ingresos_clip'] = df_plot['ingresos_t'].clip(
        upper=df_plot['ingresos_t'].quantile(0.98))
    df_plot['ticket_clip'] = df_plot['ticket_medio'].clip(
        upper=df_plot['ticket_medio'].quantile(0.98))

    fig = px.scatter(
        df_plot, x='frecuencia_t', y='ingresos_clip',
        color='segmento_cltv',
        color_discrete_map=PAL_SEG,
        size='ticket_clip', size_max=22,
        opacity=0.55,
        category_orders={'segmento_cltv': ['Alto', 'Medio', 'Bajo']},
        hover_data={'full_name': True, 'cltv': ':,.0f',
                    'ingresos_clip': False, 'ticket_clip': False,
                    'ticket_medio': ':,.0f'},
    )
    fig.update_traces(marker=dict(line=dict(color='white', width=0.5)))
    fig = _apply_theme(fig, height=460,
                       title='Clientes: frecuencia vs ingresos · tamaño = ticket medio')
    fig.update_xaxes(title='Frecuencia (compras/mes)')
    fig.update_yaxes(title='Ingresos totales (€)', tickformat=',.0f')
    return fig


def rfm_ingresos_bar(df: pd.DataFrame) -> go.Figure:
    """Barras horizontales de ingresos por segmento RFM."""
    if 'segmento_rfm' not in df.columns:
        return go.Figure()

    orden = ['Champions', 'Leales', 'En riesgo',
             'Necesitan atencion', 'Potenciales', 'Perdidos']
    pal = {
        'Champions': '#166534',
        'Leales': '#2B8A4B',
        'Potenciales': '#F28E2B',
        'Necesitan atencion': '#B35A00',
        'En riesgo': '#CC3D2B',
        'Perdidos': '#8C3B2A',
    }
    agg = df.groupby('segmento_rfm')['ingresos_t'].sum().reindex(orden).dropna().reset_index()
    total = agg['ingresos_t'].sum()
    agg['miles_eur'] = agg['ingresos_t'] / 1e3
    agg['pct'] = np.where(total > 0, agg['ingresos_t'] / total * 100, 0)
    agg['texto'] = agg.apply(
        lambda r: f"{r['miles_eur']:,.0f}k ({r['pct']:.1f}%)".replace(',', '.'),
        axis=1,
    )

    fig = go.Figure(go.Bar(
        x=agg['miles_eur'],
        y=agg['segmento_rfm'],
        orientation='h',
        marker=dict(
            color=[pal.get(seg, DS2) for seg in agg['segmento_rfm']],
            line=dict(color='white', width=1.2),
        ),
        text=agg['texto'],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Ingresos: %{x:,.0f}k €<extra></extra>',
    ))
    fig = _apply_theme(fig, height=420, showlegend=False,
                       title='Ingresos totales por segmento RFM')
    fig.update_xaxes(title='Ingresos (miles €)')
    fig.update_yaxes(title='')
    fig.update_layout(margin=dict(l=120, r=70, t=50, b=40))
    return fig


def rfm_rm_scatter(df: pd.DataFrame) -> go.Figure:
    """Scatter R vs M con jitter para visualizar la ocupación del espacio RFM."""
    required = {'R_score', 'M_score', 'segmento_rfm'}
    if not required.issubset(df.columns):
        return go.Figure()

    df_plot = df.copy()
    rng = np.random.default_rng(42)
    df_plot['R_jitter'] = df_plot['R_score'] + rng.uniform(-0.33, 0.33, len(df_plot))
    df_plot['M_jitter'] = df_plot['M_score'] + rng.uniform(-0.28, 0.28, len(df_plot))

    pal = {
        'Champions': '#2D6A4F',
        'Leales': '#40916C',
        'Potenciales': '#F4A261',
        'Necesitan atencion': '#E9C46A',
        'En riesgo': '#C94C3B',
        'Perdidos': '#9C3D3D',
    }
    orden = ['Champions', 'Leales', 'Potenciales',
             'Necesitan atencion', 'En riesgo', 'Perdidos']

    fig = px.scatter(
        df_plot,
        x='R_jitter',
        y='M_jitter',
        color='segmento_rfm',
        color_discrete_map=pal,
        category_orders={'segmento_rfm': orden},
        opacity=0.42,
        hover_data={
            'full_name': True,
            'R_score': True,
            'M_score': True,
            'ingresos_t': ':,.0f',
            'R_jitter': False,
            'M_jitter': False,
        },
    )
    fig.update_traces(marker=dict(size=5, line=dict(color='white', width=0.3)))
    fig = _apply_theme(fig, height=420, title='Distribución RFM en el plano R vs M')
    fig.update_xaxes(
        title='R_score (1=antiguo, 4=reciente)',
        tickmode='array',
        tickvals=[1, 2, 3, 4],
        range=[0.5, 4.5],
    )
    fig.update_yaxes(
        title='M_score (1=bajo gasto, 4=alto gasto)',
        tickmode='array',
        tickvals=[1, 2, 3, 4],
        range=[0.5, 4.5],
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  GRÁFICOS PARA PÁGINA RFM
# ═══════════════════════════════════════════════════════════════════════
def heatmap_rf(df: pd.DataFrame, metrica_color: str = 'count') -> go.Figure:
    """Heatmap R×F coloreado por métrica seleccionada."""
    if metrica_color == 'count':
        pivot = df.groupby(['R_score', 'F_score']).size().unstack(fill_value=0)
        cbar_title = 'Nº clientes'
        fmt = ',d'
    else:
        pivot = df.groupby(['R_score', 'F_score'])[metrica_color]\
                  .mean().unstack(fill_value=0)
        cbar_title = f'{metrica_color} (media)'
        fmt = ',.2f'

    pivot = pivot.reindex(index=[4, 3, 2, 1], columns=[1, 2, 3, 4],
                          fill_value=0)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[f'F={c}' for c in pivot.columns],
        y=[f'R={r}' for r in pivot.index],
        colorscale='YlGnBu',
        text=pivot.values,
        texttemplate=f'%{{text:{fmt}}}',
        textfont=dict(family='Inter', size=13, color='white'),
        colorbar=dict(title=cbar_title, thickness=14, len=0.85),
        hovertemplate='R: %{y}<br>F: %{x}<br>'
                      f'{cbar_title}: %{{z:{fmt}}}<extra></extra>',
    ))
    fig = _apply_theme(fig, height=420, showlegend=False,
                       title=f'Heatmap RFM — color = {cbar_title}')
    fig.update_xaxes(title='F_score (frecuencia: 1=poca, 4=mucha)')
    fig.update_yaxes(title='R_score (recencia: 1=antigua, 4=reciente)')
    return fig


def sankey_segmentos(df: pd.DataFrame) -> go.Figure:
    """Sankey segmento_cltv → segmento_rfm."""
    if 'segmento_cltv' not in df or 'segmento_rfm' not in df:
        return go.Figure()

    flujos = df.groupby(['segmento_cltv', 'segmento_rfm'])\
               .size().reset_index(name='n')

    cltv_segs = ['Alto', 'Medio', 'Bajo']
    rfm_segs  = sorted(df['segmento_rfm'].unique().tolist())
    nodos = cltv_segs + rfm_segs
    nodo_idx = {n: i for i, n in enumerate(nodos)}

    color_nodo = []
    for n in nodos:
        if n in cltv_segs:
            color_nodo.append(PAL_SEG.get(n, DS3))
        else:
            color_nodo.append({
                'Champions':         '#16A34A',
                'Leales':            '#22C55E',
                'Potenciales':       DS6,
                'Necesitan atencion': DS3,
                'En riesgo':         DS5,
                'Perdidos':          '#7C2D12',
            }.get(n, DS2))

    sources = [nodo_idx[r['segmento_cltv']] for _, r in flujos.iterrows()]
    targets = [nodo_idx[r['segmento_rfm']]  for _, r in flujos.iterrows()]
    valores = flujos['n'].tolist()
    colores_link = [
        f"rgba({int(PAL_SEG.get(flujos.iloc[i]['segmento_cltv'], DS3)[1:3], 16)},"
        f"{int(PAL_SEG.get(flujos.iloc[i]['segmento_cltv'], DS3)[3:5], 16)},"
        f"{int(PAL_SEG.get(flujos.iloc[i]['segmento_cltv'], DS3)[5:7], 16)},0.35)"
        for i in range(len(flujos))
    ]

    fig = go.Figure(go.Sankey(
        node=dict(
            pad=20, thickness=22,
            line=dict(color='white', width=0.5),
            label=nodos, color=color_nodo,
        ),
        link=dict(source=sources, target=targets, value=valores,
                  color=colores_link,
                  hovertemplate='<b>%{source.label}</b> → <b>%{target.label}</b>'
                                '<br>%{value} clientes<extra></extra>'),
    ))
    fig.update_layout(
        font=dict(family='Inter', size=12, color=DS1),
        height=480,
        margin=dict(l=20, r=20, t=40, b=20),
        title=dict(text='Flujo de clientes: CLTV → RFM',
                   font=dict(size=16, color=DS1, family='Inter')),
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  GRÁFICOS PARA PÁGINA CLUSTERING
# ═══════════════════════════════════════════════════════════════════════
def scatter_pca(df: pd.DataFrame, color_by: str = 'cluster_label') -> go.Figure:
    """Scatter PCA interactivo coloreado por la columna indicada."""
    if 'pc1' not in df or 'pc2' not in df:
        return go.Figure()

    if color_by == 'cluster_label':
        labels_unicos = sorted(df['cluster_label'].dropna().unique().tolist())
        color_map = {lab: CLUSTER_PAL[i % len(CLUSTER_PAL)]
                     for i, lab in enumerate(labels_unicos)}
    elif color_by == 'segmento_cltv':
        color_map = PAL_SEG
    elif color_by == 'segmento_rfm':
        color_map = None
    else:
        color_map = None

    hover_cols = {'pc1': False, 'pc2': False, 'cltv': ':,.0f',
                  'ingresos_t': ':,.0f'}
    if 'full_name' in df.columns:
        hover_cols['full_name'] = True

    fig = px.scatter(
        df, x='pc1', y='pc2', color=color_by,
        color_discrete_map=color_map,
        opacity=0.55,
        hover_data=hover_cols,
    )
    fig.update_traces(marker=dict(size=7, line=dict(color='white', width=0.4)))
    fig = _apply_theme(fig, height=520,
                       title=f'Espacio PCA — color: {color_by}')
    fig.update_xaxes(title='PC1', zeroline=True, zerolinecolor='#E5E7EB')
    fig.update_yaxes(title='PC2', zeroline=True, zerolinecolor='#E5E7EB')
    return fig


def heatmap_cluster_features(df: pd.DataFrame, features: list = None) -> go.Figure:
    """
    Heatmap de perfiles de cluster.
    Filas = clusters, columnas = features.
    Color = valor normalizado (azul oscuro = alto). Texto = valor real.
    El color del texto se adapta automáticamente (blanco sobre oscuro, marino sobre claro).
    """
    if features is None:
        features = ['ingresos_t', 'margen_t', 'frecuencia_t',
                    'ticket_medio', 'tasa_devolucion']
    features = [f for f in features if f in df.columns]

    labels_col = {
        'ingresos_t':      'Ingresos medios',
        'margen_t':        'Margen ratio',
        'frecuencia_t':    'Frecuencia',
        'ticket_medio':    'Ticket medio',
        'tasa_devolucion': 'Tasa devolución',
    }

    perfil = df.groupby('cluster_label')[features].mean()
    orden  = perfil['ingresos_t'].sort_values(ascending=False).index.tolist()
    perfil = perfil.loc[orden]

    # Normalización min-max por columna para el color
    perfil_norm = (perfil - perfil.min()) / (perfil.max() - perfil.min() + 1e-9)
    if 'tasa_devolucion' in features:
        perfil_norm['tasa_devolucion'] = 1 - perfil_norm['tasa_devolucion']

    def _fmt(col, val):
        if col == 'ingresos_t':      return f'{val:,.0f} €'.replace(',', '.')
        if col == 'margen_t':        return f'{val*100:.1f} %'
        if col == 'frecuencia_t':    return f'{val:.2f} /mes'
        if col == 'ticket_medio':    return f'{val:,.0f} €'.replace(',', '.')
        if col == 'tasa_devolucion': return f'{val*100:.1f} %'
        return f'{val:.2f}'

    col_labels = [labels_col.get(f, f) for f in features]

    # Heatmap sin texto (el texto lo ponemos como anotaciones para poder colorear por celda)
    fig = go.Figure(go.Heatmap(
        z=perfil_norm.values,
        x=col_labels,
        y=orden,
        colorscale=[
            [0.0, '#EFF6FF'],
            [0.4, '#60A5FA'],
            [0.7, '#1D4ED8'],
            [1.0, '#03045E'],
        ],
        showscale=False,
        hoverinfo='skip',
        xgap=5, ygap=5,
    ))

    # Anotaciones por celda con color de texto adaptativo
    for i, row in enumerate(orden):
        for j, col in enumerate(features):
            norm_val = perfil_norm.loc[row, col]
            # Texto blanco si fondo oscuro, marino si fondo claro
            txt_color = 'white' if norm_val >= 0.42 else DS1
            txt = _fmt(col, perfil.loc[row, col])
            fig.add_annotation(
                x=col_labels[j],
                y=row,
                text=f'<b>{txt}</b>',
                showarrow=False,
                font=dict(family='Inter', size=15, color=txt_color),
                xref='x', yref='y',
            )

    n_clusters = len(orden)
    fig.update_layout(
        font=dict(family='Inter'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=n_clusters * 100 + 80,
        margin=dict(l=110, r=20, t=20, b=20),
        xaxis=dict(
            side='top',
            tickfont=dict(size=12, color=DS1, family='Inter'),
            tickangle=0,
            ticklen=0,
        ),
        yaxis=dict(
            tickfont=dict(size=14, color=DS1, family='Inter'),
            autorange='reversed',
            ticklen=0,
        ),
    )
    return fig


def strip_cltv_cluster(df: pd.DataFrame) -> go.Figure:
    """Strip plot de CLTV por cluster con jitter."""
    clip = df['cltv'].quantile(0.97)
    df_plot = df.copy()
    df_plot['cltv_clip'] = df_plot['cltv'].clip(upper=clip)
    orden = df_plot.groupby('cluster_label')['ingresos_t']\
                   .mean().sort_values(ascending=False).index.tolist()

    fig = go.Figure()
    for i, label in enumerate(orden):
        sub = df_plot[df_plot['cluster_label'] == label]
        fig.add_trace(go.Box(
            y=sub['cltv_clip'], name=label,
            boxpoints='all', jitter=0.6, pointpos=0,
            marker=dict(color=CLUSTER_PAL[i % len(CLUSTER_PAL)],
                        size=4, opacity=0.4,
                        line=dict(color='white', width=0.3)),
            line=dict(color=CLUSTER_PAL[i % len(CLUSTER_PAL)], width=2),
            fillcolor='rgba(255,255,255,0.5)',
            hovertemplate=f'<b>{label}</b><br>CLTV: %{{y:,.0f}} €<extra></extra>',
        ))
    fig = _apply_theme(fig, height=480, showlegend=False,
                       title='Distribución de CLTV por cluster (clip P97)')
    fig.update_yaxes(title='CLTV (€)', tickformat=',.0f')
    fig.update_xaxes(title='Cluster')
    return fig


def barras_cluster(df: pd.DataFrame) -> go.Figure:
    """Barras dobles: clientes e ingresos por cluster."""
    agg = df.groupby('cluster_label').agg(
        n_clientes=('customer_id', 'count'),
        ingresos=('ingresos_t', 'sum'),
    ).reset_index()
    agg = agg.sort_values('ingresos', ascending=False)
    colores = [CLUSTER_PAL[i % len(CLUSTER_PAL)] for i in range(len(agg))]

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=('Clientes por cluster',
                                        'Ingresos totales por cluster'),
                        horizontal_spacing=0.15)
    fig.add_trace(go.Bar(
        x=agg['cluster_label'], y=agg['n_clientes'],
        marker=dict(color=colores, line=dict(color='white', width=1)),
        text=agg['n_clientes'].apply(lambda v: f'{v:,}'.replace(',', '.')),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>%{y} clientes<extra></extra>',
        showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=agg['cluster_label'], y=agg['ingresos']/1e6,
        marker=dict(color=colores, line=dict(color='white', width=1)),
        text=agg['ingresos'].apply(lambda v: f'{v/1e6:.2f}M€'),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>%{y:.2f}M€<extra></extra>',
        showlegend=False,
    ), row=1, col=2)
    fig.update_layout(
        font=dict(family='Inter'),
        plot_bgcolor='white', paper_bgcolor='white',
        height=400, margin=dict(l=40, r=20, t=60, b=60),
    )
    fig.update_xaxes(tickangle=-20, tickfont=dict(size=10))
    fig.update_yaxes(showgrid=True, gridcolor='#F1F5F9')
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  GRÁFICOS PARA PÁGINA CLIENTE
# ═══════════════════════════════════════════════════════════════════════
def gauge_percentil(percentil: float, label: str = 'Percentil CLTV en su cluster') -> go.Figure:
    """Gauge chart para mostrar la posición percentil de un cliente."""
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=percentil,
        number=dict(suffix='%', font=dict(family='Inter', size=36, color=DS1)),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor=GRAY,
                      tickfont=dict(family='Inter', size=10)),
            bar=dict(color=DS2, thickness=0.7),
            bgcolor='white',
            borderwidth=2, bordercolor='#E5E7EB',
            steps=[
                dict(range=[0, 25],   color='#FEE2E2'),
                dict(range=[25, 50],  color='#FEF3C7'),
                dict(range=[50, 75],  color='#DBEAFE'),
                dict(range=[75, 100], color='#DCFCE7'),
            ],
            threshold=dict(line=dict(color=DS5, width=4), thickness=0.85,
                           value=percentil),
        ),
        title=dict(text=f'<span style="font-size:13px;color:#64748B">{label}</span>',
                   font=dict(family='Inter')),
    ))
    fig.update_layout(
        font=dict(family='Inter'),
        paper_bgcolor='white',
        height=280, margin=dict(l=30, r=30, t=60, b=20),
    )
    return fig


def radar_cluster_vs_global(df: pd.DataFrame, cluster_label: str,
                             features: list = None) -> go.Figure:
    """Radar comparando el perfil medio de un cluster con la media global."""
    if features is None:
        features = ['ingresos_t', 'margen_t', 'frecuencia_t',
                    'ticket_medio', 'tasa_devolucion']
    labels = ['Ingresos', 'Margen', 'Frecuencia', 'Ticket', 'Devolución'][:len(features)]

    cluster_medio = df[df['cluster_label'] == cluster_label][features].mean()
    global_medio  = df[features].mean()

    valores_cl, valores_gl = [], []
    for f in features:
        ref = max(cluster_medio[f], global_medio[f]) * 1.05
        if ref == 0:
            ref = 1
        valores_cl.append(cluster_medio[f] / ref)
        valores_gl.append(global_medio[f] / ref)

    valores_cl += valores_cl[:1]
    valores_gl += valores_gl[:1]
    labs_loop = labels + [labels[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valores_gl, theta=labs_loop, name='Media global',
        line=dict(color=GRAY, width=2, dash='dash'),
        fill='toself', fillcolor='rgba(100,116,139,0.10)',
    ))
    fig.add_trace(go.Scatterpolar(
        r=valores_cl, theta=labs_loop, name=f'Cluster {cluster_label}',
        line=dict(color=DS3, width=3),
        fill='toself', fillcolor='rgba(0,180,216,0.25)',
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1.05], showticklabels=False,
                            gridcolor='#E5E7EB'),
            angularaxis=dict(tickfont=dict(family='Inter', size=12,
                                            color=DS1, weight=600)),
            bgcolor='#F8FAFC',
        ),
        font=dict(family='Inter'),
        height=380, margin=dict(l=50, r=50, t=40, b=40),
        legend=dict(orientation='h', yanchor='bottom', y=-0.1,
                    xanchor='center', x=0.5),
    )
    return fig


def radar_cliente_vs_cluster(cliente: pd.Series, cluster_medio: pd.Series,
                              features: list = None) -> go.Figure:
    """Radar individual: cliente vs media de su cluster."""
    if features is None:
        features = ['ingresos_t', 'margen_t', 'frecuencia_t',
                    'ticket_medio', 'tasa_devolucion']
    labels = ['Ingresos', 'Margen', 'Frecuencia', 'Ticket', 'Devolución'][:len(features)]

    # Normalización: usamos el cluster medio como referencia (1.0)
    valores_cl = []
    valores_me = []
    for f in features:
        ref = max(cluster_medio[f], cliente[f]) * 1.05
        if ref == 0:
            ref = 1
        valores_cl.append(cliente[f] / ref)
        valores_me.append(cluster_medio[f] / ref)

    valores_cl += valores_cl[:1]
    valores_me += valores_me[:1]
    labs_loop = labels + [labels[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valores_me, theta=labs_loop, name='Media del cluster',
        line=dict(color=GRAY, width=2, dash='dash'),
        fill='toself', fillcolor='rgba(100,116,139,0.10)',
    ))
    fig.add_trace(go.Scatterpolar(
        r=valores_cl, theta=labs_loop, name='Cliente',
        line=dict(color=DS2, width=3),
        fill='toself', fillcolor='rgba(0,119,182,0.22)',
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1.05], showticklabels=False,
                            gridcolor='#E5E7EB'),
            angularaxis=dict(tickfont=dict(family='Inter', size=12,
                                            color=DS1, weight=600)),
            bgcolor='#F8FAFC',
        ),
        font=dict(family='Inter'),
        height=380, margin=dict(l=50, r=50, t=40, b=40),
        legend=dict(orientation='h', yanchor='bottom', y=-0.1,
                    xanchor='center', x=0.5),
    )
    return fig
