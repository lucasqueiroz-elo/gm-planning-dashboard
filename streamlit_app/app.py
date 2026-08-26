"""GM Planning — Dashboard Streamlit
Lê diretamente os 3 Excel de Modelo\\ (tb_resultado, tb_territorios, tb_meta_sop) e
replica o design/lógica do GM_Planning_Dashboard.html, com um seletor de mês adicional.
"""
from __future__ import annotations

import datetime as dt

import streamlit as st

from data_loader import (
    LEVEL_OPTIONS,
    SORT_OPTIONS,
    aggregate_groups,
    apply_territory_filters,
    build_long_dataset,
    compute_fat_histogram,
    compute_kpis,
    compute_spread_histogram,
    compute_ytd_kpis,
    compute_ytd_monthly_series,
    file_mtimes,
    get_available_months,
    mes_label,
    sort_groups,
)
from theme import get_logo_data_uri, inject_css
from components import (
    render_distribution_histograms,
    render_footer,
    render_kpi_cards,
    render_ranking_table,
    render_ytd_chart,
    render_ytd_kpi_cards,
)

st.set_page_config(
    page_title="GM Planning & Sales Opportunities",
    page_icon="📊",
    layout="wide",
)

inject_css()

# ---------------------------------------------------------------- dados ----
try:
    df = build_long_dataset(file_mtimes())
except FileNotFoundError as exc:
    st.error(f"Não foi possível carregar os dados: {exc}")
    st.stop()

months = get_available_months(df)
if not months:
    st.error("Nenhum mês disponível em tb_meta_sop.")
    st.stop()

month_labels = {m: mes_label(m) for m in months}

header_container = st.container()

# ------------------------------------------------------------- filtros -----
def _sanitize(key: str, options: list[str]) -> None:
    current = st.session_state.get(key, "")
    if current != "" and current not in options:
        st.session_state[key] = ""


def _reset_area():
    st.session_state["f_area"] = ""


with st.container(key="filters_panel"):
    st.markdown('<div class="panel-title">Filtros</div>', unsafe_allow_html=True)
    c_mes, c_tipo, c_cluster, c_rv, c_tv, c_dig = st.columns(6)

    with c_mes:
        month = st.selectbox(
            "Mês", months, index=len(months) - 1,
            format_func=lambda m: month_labels[m], key="f_month",
        )

    df_month = df[df["month"] == month]

    type_options = sorted(v for v in df_month["territory_type"].dropna().unique() if v != "")
    cluster_options = sorted(v for v in df_month["cluster"].dropna().unique() if v != "")
    region_options = sorted(v for v in df_month["region"].dropna().unique() if v != "")
    digital_options = sorted(v for v in df_month["full_digital"].dropna().unique() if v != "")

    _sanitize("f_territory_type", type_options)
    _sanitize("f_cluster", cluster_options)
    _sanitize("f_region", region_options)
    _sanitize("f_digital", digital_options)

    with c_tipo:
        territory_type = st.selectbox(
            "Tipo", [""] + type_options, key="f_territory_type",
            format_func=lambda v: "Todos" if v == "" else v,
        )
    with c_cluster:
        cluster = st.selectbox(
            "Cluster Regional", [""] + cluster_options, key="f_cluster",
            format_func=lambda v: "Todos" if v == "" else v,
        )
    with c_rv:
        region = st.selectbox(
            "RV", [""] + region_options, key="f_region", on_change=_reset_area,
            format_func=lambda v: "Todos" if v == "" else v,
        )

    area_pool = df_month if not region else df_month[df_month["region"] == region]
    area_options = sorted(v for v in area_pool["area"].dropna().unique() if v != "")
    _sanitize("f_area", area_options)

    with c_tv:
        area = st.selectbox(
            "TV", [""] + area_options, key="f_area",
            format_func=lambda v: "Todos" if v == "" else v,
        )
    with c_dig:
        full_digital = st.selectbox(
            "100% Digital", [""] + digital_options, key="f_digital",
            format_func=lambda v: "Todos" if v == "" else v,
        )

filtered = apply_territory_filters(
    df_month, territory_type=territory_type, cluster=cluster,
    region=region, area=area, full_digital=full_digital,
)

# --------------------------------------------------------------- header ----
with header_container:
    st.markdown(
        f"""
        <div class="header-flex">
          <div>
            <div class="eyebrow-bar"></div>
            <h1 class="gm-title">GM Planning</h1>
            <div class="subtitle">Meta de Lucro por Zona De Venda</div>
            <div class="header-warning">
              <svg width="18" height="18" viewBox="0 0 24 24" class="header-warning-icon">
                <path d="M12 2 L23 21 H1 Z" fill="currentColor"/>
                <rect x="11" y="8" width="2" height="7" fill="var(--bg-mid)"/>
                <rect x="11" y="17" width="2" height="2" fill="var(--bg-mid)"/>
              </svg>
              <div>As metas de Lucro, Faturamento e Spread mostradas abaixo são ilustrativas.<br>Os demais valores (Faturamento Real, Lucro Real, % Atingimento etc.) refletem os valores reais da operação.</div>
            <br>
            </div>
          </div>
          <img src="{get_logo_data_uri()}" class="header-logo" alt="BAT Brasil" />
        </div>
        <div class="subtitle">ILUSTRATIVO</div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------------------------------------------- KPIs ----
st.markdown('<h2 class="drill-title">Resumo</h2><br>', unsafe_allow_html=True)

kpis = compute_kpis(filtered)
render_kpi_cards(kpis)

# ------------------------------------------------------------ drilldown ----
st.markdown('<br><h2 class="drill-title">Detalhamento</h2>', unsafe_allow_html=True)

col_level, col_sort = st.columns([2, 1])
with col_level:
    level_label = st.segmented_control(
        "Nível de detalhamento",
        options=[lbl for _, lbl in LEVEL_OPTIONS],
        default=[lbl for key, lbl in LEVEL_OPTIONS if key == "area"][0],
        key="f_level",
        label_visibility="collapsed",
    )
with col_sort:
    sort_label = st.selectbox(
        "Ordenar por", options=[lbl for _, lbl in SORT_OPTIONS], key="f_sort",
    )

level_by_label = {lbl: key for key, lbl in LEVEL_OPTIONS}
sort_by_label = {lbl: key for key, lbl in SORT_OPTIONS}
level = level_by_label.get(level_label, "area")
sort_key = sort_by_label.get(sort_label, "fat_gap_asc")

groups = aggregate_groups(filtered, level)
groups = sort_groups(groups, sort_key)

# tabela ganha mais altura no nível mais granular (Zona), que tem muito mais linhas
with st.container(key="table_panel"):
    render_ranking_table(groups, tall=(level == "territory"))

# -------------------------------------------------------- distribuição -----
# st.markdown('<br><h2 class="drill-title">Distribuição - Zonas</h2>', unsafe_allow_html=True)

# # histogramas por território com_real, independentes do nível de drilldown acima
# fat_bins = compute_fat_histogram(filtered)
# spread_bins = compute_spread_histogram(filtered)
# render_distribution_histograms(fat_bins, spread_bins)

# -------------------------------------------------------- acumulado do ano -
# YTD: sempre o ano corrente inteiro (não reage ao mês de análise selecionado
# acima), mas respeita os demais filtros de território (Tipo/Cluster/RV/TV/100% Digital)
today = dt.date.today()

st.markdown(f'<br><h2 class="drill-title">ATINGIMENTA META YTD - {today.year}</h2>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="header-warning">
      <svg width="18" height="18" viewBox="0 0 24 24" class="header-warning-icon">
        <path d="M12 2 L23 21 H1 Z" fill="currentColor"/>
        <rect x="11" y="8" width="2" height="7" fill="var(--bg-mid)"/>
        <rect x="11" y="17" width="2" height="2" fill="var(--bg-mid)"/>
      </svg>
      <div>Para fins ilustrativos, a meta mensal foi fixada em R$ 5 milhões para todos os meses do ano.<br>Na versão final do modelo, a meta de lucro vai variar mensalmente.</div>
    <br>
    </div>
    """,
    unsafe_allow_html=True,
)
    
ytd_base = apply_territory_filters(
    df, territory_type=territory_type, cluster=cluster,
    region=region, area=area, full_digital=full_digital,
)

ytd_kpis = compute_ytd_kpis(ytd_base, today.year)
render_ytd_kpi_cards(ytd_kpis)

ytd_monthly = compute_ytd_monthly_series(ytd_base, today.year)
render_ytd_chart(ytd_monthly, today.year, today)

# ---------------------------------------------------------------- footer ---
render_footer(month_labels[month])
