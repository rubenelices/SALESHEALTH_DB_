"""
Página: Ventas — análisis por producto, marca y tienda.

Lee ventas_detalle.csv (42.555 líneas de venta enriquecidas con dimensiones)
y permite explorar las ventas desde tres ángulos: producto, marca y tienda.

Visualizaciones:
  - KPIs globales del módulo de ventas
  - Tendencia mensual de ingresos
  - Tabs Productos / Marcas / Tiendas con:
      · Top N por ingresos (bar chart con colores distintos)
      · Selector individual
      · KPIs y serie temporal del item elegido
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.styles import (
    inject_global_css, render_header, section_divider, section_title,
    kpi_row, info_box,
    DS1, DS2, DS3, DS5, DS6, DS7,
)
from utils.formats import fmt_eur, fmt_int
from utils.data_loader import load_ventas


# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(page_title='Ventas · SalesHealth',
                   page_icon='🛒', layout='wide',
                   initial_sidebar_state='collapsed')
inject_global_css()


def _theme(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        font=dict(family='Inter', size=12, color='#1F2937'),
        plot_bgcolor='white', paper_bgcolor='white',
        height=height,
        margin=dict(l=40, r=20, t=20, b=40),
        hoverlabel=dict(bgcolor='white', bordercolor=DS3,
                        font=dict(family='Inter', size=12, color=DS1)),
    )
    fig.update_xaxes(showgrid=True, gridcolor='#F1F5F9', zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor='#F1F5F9', zeroline=False)
    return fig


# Paleta diversa para los rankings (colores distintos por barra)
PALETA = [
    '#0077B6', '#00B4D8', '#48CAE4', '#90E0EF', '#0096C7',
    '#023E8A', '#F4A261', '#E76F51', '#2A9D8F', '#E9C46A',
    '#8338EC', '#FB5607', '#FFBE0B', '#3A86FF', '#06A77D',
    '#D62828', '#A663CC', '#1B998B', '#FF6B6B', '#264653',
]


df = load_ventas()
if df.empty:
    render_header(active_page='ventas', eyebrow='ANÁLISIS DE VENTAS',
                  title='Ventas', subtitle='')
    info_box(
        '❌ <strong>No hay datos.</strong> Genera primero '
        '<code>ventas_detalle.csv</code> ejecutando '
        '<code>python3 _docs/export_ventas.py</code> con Postgres en marcha.',
        kind='danger',
    )
    st.stop()


render_header(
    active_page='ventas',
    eyebrow='ANÁLISIS DE VENTAS',
    title='Productos, marcas y tiendas',
    subtitle=(f'Análisis detallado sobre {fmt_int(len(df))} líneas de venta '
              f'entre {df["sale_date"].min().date()} y {df["sale_date"].max().date()}. '
              'Explora los productos más vendidos, las marcas con más peso '
              'y el rendimiento de cada tienda.'),
)


# ═══════════════════════════════════════════════════════════════════════
#  KPIs GLOBALES DEL MÓDULO
# ═══════════════════════════════════════════════════════════════════════
ingresos_tot = df['net_revenue'].sum()
margen_tot = df['margin'].sum()
n_ventas = df['sale_id'].nunique()
ticket_medio = df.groupby('sale_id')['net_revenue'].sum().mean()
n_unidades = int(df['quantity'].sum())

kpi_row([
    {'value': fmt_int(n_ventas),
     'label': 'Ventas (tickets)', 'color': 'primary'},
    {'value': f'{ingresos_tot/1e6:.2f}M€',
     'label': 'Ingresos totales', 'color': 'ocean'},
    {'value': f'{margen_tot/1e6:.2f}M€',
     'label': 'Margen total', 'color': 'cyan'},
    {'value': fmt_int(n_unidades),
     'label': 'Unidades vendidas', 'color': 'gold'},
    {'value': fmt_eur(ticket_medio),
     'label': 'Ticket medio', 'color': 'green'},
])


# ═══════════════════════════════════════════════════════════════════════
#  TENDENCIA MENSUAL GLOBAL
# ═══════════════════════════════════════════════════════════════════════
section_divider('TENDENCIA MENSUAL DE INGRESOS')

tendencia = df.groupby('year_month', as_index=False).agg(
    ingresos=('net_revenue', 'sum'),
    ventas=('sale_id', 'nunique'),
)
fig_t = go.Figure()
fig_t.add_trace(go.Scatter(
    x=tendencia['year_month'], y=tendencia['ingresos'],
    mode='lines+markers',
    line=dict(color=DS2, width=2.5),
    marker=dict(size=6, color=DS3, line=dict(color='white', width=1.5)),
    fill='tozeroy', fillcolor='rgba(0,180,216,0.14)',
    hovertemplate='<b>%{x|%b %Y}</b><br>Ingresos: %{y:,.0f} €<extra></extra>',
))
fig_t = _theme(fig_t, height=320)
fig_t.update_xaxes(title='', dtick='M6', tickformat='%b %Y')
fig_t.update_yaxes(title='Ingresos (€)', tickformat=',.0f')
st.plotly_chart(fig_t, use_container_width=True, theme=None)


# ═══════════════════════════════════════════════════════════════════════
#  TABS: PRODUCTOS / MARCAS / TIENDAS
# ═══════════════════════════════════════════════════════════════════════
section_divider('EXPLORAR POR DIMENSIÓN')

tab_prod, tab_marca, tab_tienda = st.tabs(
    ['🛍️ Productos', '🏷️ Marcas', '🏬 Tiendas']
)


def render_dimension(df: pd.DataFrame, dim_col: str, dim_label: str,
                     cross_dim: tuple[str, str] = None,
                     extra_info: list[str] = None):
    """Renderiza el bloque común para una dimensión (producto/marca/tienda)."""

    # Top N por ingresos
    top = (df.groupby(dim_col, as_index=False)
             .agg(ingresos=('net_revenue', 'sum'),
                  unidades=('quantity', 'sum'),
                  ventas=('sale_id', 'nunique'),
                  margen=('margin', 'sum'))
             .sort_values('ingresos', ascending=False))

    n_total = len(top)
    top_n = top.head(min(15, n_total)).reset_index(drop=True)

    c1, c2 = st.columns([1.4, 1])

    with c1:
        section_title(f'Top {len(top_n)} {dim_label.lower()}s por ingresos',
                      label='RANKING')
        info_box(
            f'Ranking de los <strong>{len(top_n)} {dim_label.lower()}s</strong> '
            f'que más facturan en el periodo completo. El color de cada barra '
            f'es solo identificativo: facilita seguir un mismo '
            f'{dim_label.lower()} en otras gráficas de la página.',
            kind='info',
        )
        colores = [PALETA[i % len(PALETA)] for i in range(len(top_n))]
        fig_top = go.Figure()
        fig_top.add_trace(go.Bar(
            x=top_n['ingresos'],
            y=top_n[dim_col],
            orientation='h',
            marker=dict(color=colores, line=dict(color='white', width=1)),
            text=[fmt_eur(v) for v in top_n['ingresos']],
            textposition='outside',
            textfont=dict(size=11, color=DS1),
            hovertemplate='<b>%{y}</b><br>Ingresos: %{x:,.0f} €<extra></extra>',
        ))
        fig_top = _theme(fig_top, height=max(360, len(top_n) * 28))
        fig_top.update_yaxes(autorange='reversed', title='', automargin=True)
        fig_top.update_xaxes(title='Ingresos (€)', tickformat=',.0f')
        # margen para que el texto exterior no se corte
        max_x = top_n['ingresos'].max()
        fig_top.update_xaxes(range=[0, max_x * 1.15])
        fig_top.update_layout(margin=dict(l=10, r=30, t=20, b=40))
        st.plotly_chart(fig_top, use_container_width=True, theme=None)

    with c2:
        section_title(f'Estadísticas de un {dim_label.lower()} concreto',
                      label='SELECTOR')
        sel = st.selectbox(
            f'Elige {dim_label.lower()}',
            options=top[dim_col].tolist(),
            key=f'sel_{dim_col}',
        )
        sub = df[df[dim_col] == sel]
        sel_ingresos = sub['net_revenue'].sum()
        sel_margen = sub['margin'].sum()
        sel_unidades = int(sub['quantity'].sum())
        sel_ventas = sub['sale_id'].nunique()
        pct = sel_ingresos / df['net_revenue'].sum() * 100

        kpi_row([
            {'value': fmt_eur(sel_ingresos),
             'label': 'Ingresos', 'color': 'primary'},
            {'value': fmt_int(sel_unidades),
             'label': 'Unidades', 'color': 'ocean'},
            {'value': fmt_int(sel_ventas),
             'label': 'Tickets', 'color': 'cyan'},
            {'value': f'{pct:.1f}%',
             'label': 'Cuota total', 'color': 'gold'},
        ], cols=2)

        if extra_info:
            for line in extra_info:
                if callable(line):
                    line = line(sub, sel)
                if line:
                    st.markdown(
                        f'<div style="font-size:12px;color:{DS2};'
                        f'margin-top:10px;line-height:1.5;">{line}</div>',
                        unsafe_allow_html=True,
                    )

        # Mini bar chart cruzado: distribución del item por otra dimensión
        if cross_dim is not None:
            cross_col, cross_label = cross_dim
            cross = (sub.groupby(cross_col, as_index=False)['net_revenue']
                        .sum()
                        .sort_values('net_revenue', ascending=False)
                        .head(5))
            if not cross.empty:
                section_title(f'Top 5 {cross_label} para "{sel}"',
                              label='DISTRIBUCIÓN')
                colores_x = [PALETA[i % len(PALETA)] for i in range(len(cross))]
                fig_cross = go.Figure()
                fig_cross.add_trace(go.Bar(
                    x=cross['net_revenue'], y=cross[cross_col],
                    orientation='h',
                    marker=dict(color=colores_x,
                                line=dict(color='white', width=1)),
                    text=[fmt_eur(v) for v in cross['net_revenue']],
                    textposition='outside',
                    textfont=dict(size=10, color=DS1),
                    hovertemplate=f'<b>%{{y}}</b><br>'
                                  f'Ingresos: %{{x:,.0f}} €<extra></extra>',
                ))
                fig_cross = _theme(fig_cross, height=230)
                fig_cross.update_yaxes(autorange='reversed', title='',
                                       automargin=True,
                                       tickfont=dict(size=10))
                fig_cross.update_xaxes(title='', tickformat=',.0f',
                                       range=[0, cross['net_revenue'].max() * 1.20])
                fig_cross.update_layout(margin=dict(l=10, r=20, t=10, b=30))
                st.plotly_chart(fig_cross, use_container_width=True, theme=None)

    # Evolución mensual del item seleccionado vs total
    section_title(f'Evolución mensual de "{sel}" vs total',
                  label='TENDENCIA')
    sub_t = sub.groupby('year_month', as_index=False)['net_revenue'].sum()
    sub_t = sub_t.rename(columns={'net_revenue': 'ingresos_sel'})
    tot_t = df.groupby('year_month', as_index=False)['net_revenue'].sum()
    tot_t = tot_t.rename(columns={'net_revenue': 'ingresos_tot'})
    merged = tot_t.merge(sub_t, on='year_month', how='left').fillna(0)

    fig_dual = go.Figure()
    fig_dual.add_trace(go.Scatter(
        x=merged['year_month'], y=merged['ingresos_tot'],
        mode='lines', name='Total',
        line=dict(color='#CBD5E1', width=2),
        hovertemplate='<b>%{x|%b %Y}</b><br>Total: %{y:,.0f} €<extra></extra>',
    ))
    fig_dual.add_trace(go.Scatter(
        x=merged['year_month'], y=merged['ingresos_sel'],
        mode='lines+markers', name=sel,
        line=dict(color=DS1, width=3),
        marker=dict(size=6, color=DS2, line=dict(color='white', width=1.5)),
        fill='tozeroy', fillcolor='rgba(3,4,94,0.10)',
        hovertemplate=f'<b>%{{x|%b %Y}}</b><br>{sel}: %{{y:,.0f}} €<extra></extra>',
    ))
    fig_dual = _theme(fig_dual, height=320)
    fig_dual.update_xaxes(title='', dtick='M6', tickformat='%b %Y')
    fig_dual.update_yaxes(title='Ingresos (€)', tickformat=',.0f')
    fig_dual.update_layout(
        legend=dict(orientation='h', y=1.10, x=0,
                    bgcolor='rgba(255,255,255,0.85)',
                    bordercolor='#E5E7EB', borderwidth=1),
    )
    st.plotly_chart(fig_dual, use_container_width=True, theme=None)


# ── TAB PRODUCTOS ─────────────────────────────────────────────────────
with tab_prod:
    def _info_producto(sub, sel):
        marca = sub['brand'].mode().iloc[0] if not sub.empty else '—'
        cat = sub['product_category'].mode().iloc[0] if not sub.empty else '—'
        return (f'🏷️ Marca: <strong>{marca}</strong> &nbsp;·&nbsp; '
                f'📂 Categoría: <strong>{cat}</strong>')
    render_dimension(df, 'product_name', 'Producto',
                     cross_dim=('store_name', 'tiendas'),
                     extra_info=[_info_producto])


# ── TAB MARCAS ────────────────────────────────────────────────────────
with tab_marca:
    def _info_marca(sub, sel):
        n_prods = sub['product_name'].nunique()
        return f'🛍️ Productos distintos: <strong>{n_prods}</strong>'
    render_dimension(df, 'brand', 'Marca',
                     cross_dim=('product_name', 'productos'),
                     extra_info=[_info_marca])


# ── TAB TIENDAS ───────────────────────────────────────────────────────
with tab_tienda:
    def _info_tienda(sub, sel):
        if sub.empty:
            return ''
        district = sub['district'].mode().iloc[0]
        area = sub['area_type'].mode().iloc[0]
        return (f'📍 Distrito: <strong>{district}</strong> &nbsp;·&nbsp; '
                f'🗺️ Zona: <strong>{area}</strong>')
    render_dimension(df, 'store_name', 'Tienda',
                     cross_dim=('product_name', 'productos'),
                     extra_info=[_info_tienda])


# ═══════════════════════════════════════════════════════════════════════
#  RESUMEN POR CATEGORÍA (panel inferior — visión transversal)
# ═══════════════════════════════════════════════════════════════════════
section_divider('MIX POR CATEGORÍA', thin=True)

cat = (df.groupby('product_category', as_index=False)
         .agg(ingresos=('net_revenue', 'sum'),
              unidades=('quantity', 'sum'))
         .sort_values('ingresos', ascending=False))
cat['pct'] = cat['ingresos'] / cat['ingresos'].sum() * 100

fig_cat = go.Figure()
fig_cat.add_trace(go.Bar(
    x=cat['product_category'], y=cat['ingresos'],
    marker=dict(color=[PALETA[i] for i in range(len(cat))],
                line=dict(color='white', width=1)),
    text=[f'{p:.1f}%' for p in cat['pct']],
    textposition='outside',
    textfont=dict(size=12, color=DS1, family='Inter'),
    hovertemplate='<b>%{x}</b><br>Ingresos: %{y:,.0f} €<extra></extra>',
))
fig_cat = _theme(fig_cat, height=320)
fig_cat.update_xaxes(title='', tickangle=-15)
fig_cat.update_yaxes(title='Ingresos (€)', tickformat=',.0f')
st.plotly_chart(fig_cat, use_container_width=True, theme=None)
