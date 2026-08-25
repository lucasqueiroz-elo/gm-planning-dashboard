"""Componentes visuais renderizados como HTML customizado (fiel ao dashboard
original): cards de KPI, tabela de ranking e footer."""
from __future__ import annotations

import datetime as dt
import html

import pandas as pd
import streamlit as st

from data_loader import MESES_ABREV_PT
from formatting import badge_class, fmt_brl, fmt_int, fmt_pct, fmt_pp, fmt_signed_pct


def _hero_class(v, good_th: float = 1.0, mid_th: float = 0.8) -> str:
    if v is None or pd.isna(v):
        return "tag-bad"
    if v >= good_th:
        return "tag-good"
    if v >= mid_th:
        return "tag-mid"
    return "tag-bad"


def render_kpi_cards(k: dict) -> None:
    gm_delta_arrow = "▲" if (k["gm_delta"] is not None and not pd.isna(k["gm_delta"]) and k["gm_delta"] >= 0) else "▼"
    gm_delta_cls = "tag-good" if (k["gm_delta"] is not None and not pd.isna(k["gm_delta"]) and k["gm_delta"] >= 0) else "tag-bad"

    sp_favoravel = k["sp_favoravel"]
    sp_status_text = ("ABAIXO DO LIMITE · " if sp_favoravel else "ACIMA DO LIMITE · ") + fmt_pp(k["sp_real"] - k["sp_meta"], 1)
    sp_status_cls = "tag-good" if sp_favoravel else "tag-bad"
    sp_hero_cls = "tag-good" if sp_favoravel else "tag-bad"
    spread_warn_border = " warn-border" if not sp_favoravel else ""

    html_block = f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Meta Lucro · % Atingimento</div>
        <div class="kpi-hero {_hero_class(k['lucro_pct'])}">{fmt_pct(k['lucro_pct'], 0)}</div>
        <div class="kpi-sub">Real: <b>{fmt_brl(k['real_lucro'])}</b> &nbsp;·&nbsp; Meta: <b>{fmt_brl(k['meta_lucro'])}</b></div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Meta Faturamento · % Atingimento</div>
        <div class="kpi-hero {_hero_class(k['fat_pct'])}">{fmt_pct(k['fat_pct'], 0)}</div>
        <div class="kpi-sub">Real: <b>{fmt_brl(k['real_fat'])}</b> &nbsp;·&nbsp; Meta: <b>{fmt_brl(k['meta_fat'])}</b></div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">GM Partidor</div>
        <div class="kpi-hero" style="color:#4fc3f7;">{fmt_pct(k['gm_real'], 1)}</div>
        <div class="kpi-sub">Meta: <b>{fmt_pct(k['gm_meta'], 1)}</b> &nbsp;·&nbsp; <span class="{gm_delta_cls}">{gm_delta_arrow} {fmt_pp(k['gm_delta'], 1)} vs meta</span></div>
      </div>
      <div class="kpi-card{spread_warn_border}">
        <div class="kpi-label">SPREAD - REAL vs. LIMITE</div>
        <div class="kpi-hero {sp_hero_cls}">{fmt_pct(k['sp_real'], 1)}</div>
        <div class="kpi-sub">Meta: <b>{fmt_pct(k['sp_meta'], 1)}</b> &nbsp;·&nbsp; <span class="{sp_status_cls}">{sp_status_text}</span></div>
      </div>
    </div>
    """
    st.markdown(html_block, unsafe_allow_html=True)


def render_ranking_table(groups: pd.DataFrame, tall: bool = False) -> None:
    rows_html = []
    for _, g in groups.iterrows():
        rows_html.append(
            "<tr>"
            f"<td>{html.escape(str(g['name']))}</td>"
            f"<td>{fmt_int(g['pdvs'])}</td>"
            f"<td>{fmt_brl(g['real_fat'])}</td>"
            f"<td>{fmt_brl(g['meta_fat'])}</td>"
            f"<td><span class=\"cell-badge {badge_class('fat', g['fat_gap'])}\">{fmt_signed_pct(g['fat_gap'], 0)}</span></td>"
            f"<td>{fmt_pct(g['real_spread'], 1)}</td>"
            f"<td>{fmt_pct(g['meta_spread'], 1)}</td>"
            f"<td><span class=\"cell-badge {badge_class('spread', g['spread_gap'])}\">{fmt_pp(g['spread_gap'], 1)}</span></td>"
            f"<td>{fmt_brl(g['real_lucro'])}</td>"
            f"<td>{fmt_brl(g['meta_lucro'])}</td>"
            f"<td><span class=\"cell-badge {badge_class('lucro', g['lucro_pct'])}\">{fmt_pct(g['lucro_pct'], 0)}</span></td>"
            "</tr>"
        )

    if not rows_html:
        body = ('<tr><td colspan="11" style="text-align:center; color:#a9b3de; padding:24px;">'
                'Nenhum território com dado real para os filtros selecionados.</td></tr>')
    else:
        body = "".join(rows_html)

    scroll_class = "table-scroll tall" if tall else "table-scroll"
    table_html = f"""
    <div class="{scroll_class}">
      <table class="gm-table">
        <thead>
          <tr>
            <th>Nome</th><th>PDVs</th><th>Faturamento</th><th>Meta Faturamento</th>
            <th>Ating. Fat</th><th>Spread</th><th>Teto Spread</th><th>Δ Spread</th>
            <th>Lucro</th><th>Meta Lucro</th><th>Ating. Lucro</th>
          </tr>
        </thead>
        <tbody>{body}</tbody>
      </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


_FAT_HIST_COLORS = ["var(--red)", "var(--red)", "var(--yellow)", "var(--green)"]
_SPREAD_HIST_COLORS = [
    "var(--green)",
    "color-mix(in srgb, var(--green) 40%, var(--yellow) 60%)",
    "color-mix(in srgb, var(--yellow) 50%, var(--red) 50%)",
    "var(--red)",
]
_HIST_BAR_MAX_PX = 110


def _render_histogram_card(title: str, bins: list[tuple[str, int]], colors: list[str]) -> str:
    max_count = max((count for _, count in bins), default=0)
    cols = []
    for (label, count), color in zip(bins, colors):
        bar_h = _HIST_BAR_MAX_PX if max_count == 0 else max(6, round(count / max_count * _HIST_BAR_MAX_PX))
        cols.append(
            '<div class="hist-bar-col">'
            f'<div class="hist-count">{count}</div>'
            f'<div class="hist-bar" style="height:{bar_h}px; background:{color};"></div>'
            f'<div class="hist-bar-label">{html.escape(label)}</div>'
            '</div>'
        )
    return (
        '<div class="hist-card">'
        f'<div class="hist-title">{html.escape(title)}</div>'
        f'<div class="hist-bars">{"".join(cols)}</div>'
        '</div>'
    )


def render_distribution_histograms(
    fat_bins: list[tuple[str, int]], spread_bins: list[tuple[str, int]]
) -> None:
    """Dois histogramas lado a lado (HTML/CSS puro, sem lib de gráfico) com a
    distribuição de territórios com_real por faixa de atingimento de Faturamento
    e por faixa de status de Spread."""
    fat_card = _render_histogram_card("% Atingimento Faturamento", fat_bins, _FAT_HIST_COLORS)
    spread_card = _render_histogram_card("SPREAD", spread_bins, _SPREAD_HIST_COLORS)
    st.markdown(f'<div class="hist-grid">{fat_card}{spread_card}</div>', unsafe_allow_html=True)


def render_ytd_kpi_cards(k: dict) -> None:
    """3 kpi-cards do 'Acumulado do Ano' (YTD) — mesmo componente visual do topo,
    numa grade de 3 colunas."""
    spread_diff_cls = "tag-bad" if k["spread_diff"] > 0 else "tag-good"

    html_block = f"""
    <div class="kpi-grid kpi-grid-3">
      <div class="kpi-card">
        <div class="kpi-label">Meta Lucro · % Realizado YTD</div>
        <div class="kpi-hero {_hero_class(k['lucro_pct'])}">{fmt_pct(k['lucro_pct'], 0)}</div>
        <div class="kpi-sub">Real: <b>{fmt_brl(k['real_lucro'])}</b> &nbsp;·&nbsp; Meta: <b>{fmt_brl(k['meta_lucro'])}</b></div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Meta Faturamento · % Realizado YTD</div>
        <div class="kpi-hero {_hero_class(k['fat_pct'])}">{fmt_pct(k['fat_pct'], 0)}</div>
        <div class="kpi-sub">Real: <b>{fmt_brl(k['real_fat'])}</b> &nbsp;·&nbsp; Meta: <b>{fmt_brl(k['meta_fat'])}</b></div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Spread · Diferença Real vs. Planejado (ano)</div>
        <div class="kpi-hero {spread_diff_cls}">{fmt_pp(k['spread_diff'], 1)}</div>
        <div class="kpi-sub">Real: <b>{fmt_pct(k['sp_real'], 1)}</b> &nbsp;·&nbsp; Meta: <b>{fmt_pct(k['sp_meta'], 1)}</b></div>
      </div>
    </div>
    """
    st.markdown(html_block, unsafe_allow_html=True)


def _fmt_brl_compact(v) -> str:
    """Formato compacto de R$ para caber como data label ao lado dos pontos do
    gráfico (ex: 'R$ 3,6mi'), sem disputar espaço horizontal entre meses."""
    if v is None or pd.isna(v):
        return "—"
    sign = "-" if v < 0 else ""
    av = abs(v)
    if av >= 1_000_000:
        return f"R$ {sign}{f'{av / 1_000_000:.1f}'.replace('.', ',')}mi"
    if av >= 1_000:
        return f"R$ {sign}{av / 1_000:.0f}k"
    return f"R$ {sign}{av:.0f}"


def _ytd_marker_color(pct) -> str:
    if pct is None or pd.isna(pct):
        return "var(--red)"
    if pct >= 1.0:
        return "var(--green)"
    if pct >= 0.8:
        return "var(--yellow)"
    return "var(--red)"


def _render_ytd_line_chart_svg(monthly: pd.DataFrame, current_month: dt.date) -> str:
    n = len(monthly)
    if n == 0:
        return '<div class="chart-fallback">Sem dados no ano corrente.</div>'

    width, height = 800, 260
    pad_l, pad_r, pad_t, pad_b = 34, 34, 40, 30
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    values = list(monthly["meta"]) + [v for v in monthly["real"] if pd.notna(v)]
    max_v = max(values) if values else 1.0
    min_v = min(0.0, min(values) if values else 0.0)
    span = max_v - min_v if max_v != min_v else 1.0
    max_v_padded = max_v + span * 0.12
    min_v_padded = min_v - span * 0.05
    span_padded = (max_v_padded - min_v_padded) or 1.0

    def x_at(i: int) -> float:
        return pad_l + plot_w / 2 if n == 1 else pad_l + i * (plot_w / (n - 1))

    def y_at(v: float) -> float:
        return pad_t + (max_v_padded - v) / span_padded * plot_h

    svg_parts = [
        f'<svg viewBox="0 0 {width} {height}" class="ytd-chart-svg" preserveAspectRatio="xMidYMid meet">',
        f'<line x1="{pad_l}" y1="{y_at(0):.1f}" x2="{width - pad_r}" y2="{y_at(0):.1f}" class="ytd-zero-line" />',
    ]

    if n > 1:
        meta_pts = " ".join(f"{x_at(i):.1f},{y_at(v):.1f}" for i, v in enumerate(monthly["meta"]))
        svg_parts.append(f'<polyline points="{meta_pts}" class="ytd-meta-line" />')

    # linha Real sólida, quebrada (sem interpolar) nos meses sem dado real
    seg: list[tuple[float, float]] = []
    real_values = list(monthly["real"])
    for i, v in enumerate(real_values):
        if pd.notna(v):
            seg.append((x_at(i), y_at(v)))
        else:
            if len(seg) > 1:
                pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in seg)
                svg_parts.append(f'<polyline points="{pts}" class="ytd-real-line" />')
            seg = []
    if len(seg) > 1:
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in seg)
        svg_parts.append(f'<polyline points="{pts}" class="ytd-real-line" />')

    last_idx = n - 1
    for i, row in enumerate(monthly.itertuples()):
        x = x_at(i)
        svg_parts.append(f'<text x="{x:.1f}" y="{height - 8}" class="ytd-axis-label">{MESES_ABREV_PT[row.month.month]}</text>')

        # rótulo da Meta (sempre presente — todo mês da base tem meta cadastrada)
        meta_y = y_at(row.meta)
        meta_label_y = meta_y - 10

        real_label_y = None
        if pd.notna(row.real):
            color = _ytd_marker_color(row.pct)
            y = y_at(row.real)
            is_partial_current_month = (
                i == last_idx and row.month.year == current_month.year and row.month.month == current_month.month
            )
            if is_partial_current_month:
                s = 6.5
                pts = f"{x:.1f},{y - s:.1f} {x - s:.1f},{y + s:.1f} {x + s:.1f},{y + s:.1f}"
                svg_parts.append(f'<polygon points="{pts}" fill="{color}" class="ytd-marker" />')
                real_label_y = y - s - 6
            else:
                svg_parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" class="ytd-marker" />')
                real_label_y = y - 12
            # evita colisão vertical entre o rótulo da Meta e o rótulo do Real
            # quando as duas linhas estão próximas naquele mês
            if abs(meta_label_y - real_label_y) < 16:
                meta_label_y = min(meta_label_y, real_label_y - 16)

        meta_label_y = max(meta_label_y, 11)
        svg_parts.append(f'<text x="{x:.1f}" y="{meta_label_y:.1f}" class="ytd-meta-value-label">{_fmt_brl_compact(row.meta)}</text>')
        if real_label_y is not None:
            real_label_y = max(real_label_y, 11)
            svg_parts.append(f'<text x="{x:.1f}" y="{real_label_y:.1f}" class="ytd-value-label">{_fmt_brl_compact(row.real)}</text>')

    svg_parts.append("</svg>")
    return "".join(svg_parts)


def _render_ytd_legend() -> str:
    """Legenda do gráfico YTD: significado dos formatos de marcador (mês fechado
    vs. em aberto) e das cores dos marcadores (% atingimento da meta)."""
    return (
        '<div class="ytd-legend-row">'
        '<span><svg width="12" height="12" viewBox="0 0 12 12" class="ytd-legend-icon">'
        '<circle cx="6" cy="6" r="5" fill="#ffffff" /></svg>Mês fechado</span>'
        '<span><svg width="12" height="12" viewBox="0 0 12 12" class="ytd-legend-icon">'
        '<polygon points="6,1 11,10.5 1,10.5" fill="#ffffff" /></svg>Mês em aberto</span>'
        '<span class="ytd-legend-sep"></span>'
        '<span><span class="legend-dot" style="background:var(--green);"></span>≥ 100% da meta</span>'
        '<span><span class="legend-dot" style="background:var(--yellow);"></span>80% a 99% da meta</span>'
        '<span><span class="legend-dot" style="background:var(--red);"></span>&lt; 80% da meta</span>'
        '</div>'
    )


def render_ytd_chart(monthly: pd.DataFrame, year: int, current_month: dt.date) -> None:
    """Chart-card com o gráfico de linhas Meta vs. Real do ano corrente."""
    chart_html = _render_ytd_line_chart_svg(monthly, current_month)
    st.markdown(
        f"""
        <div class="chart-card">
          <div class="chart-card-title">ATINGIMENTO DA META DE LUCRO POR MÊS — {year}</div>
          {chart_html}
          {_render_ytd_legend()}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer(mes_label: str) -> None:
    st.markdown(f"""
    <footer class="gm-footer">
      Painel construído a partir de dados reais de {html.escape(mes_label)} (<b>tb_resultado</b>) comparados
      à meta calculada pela metodologia <b>GM Planning</b> (<b>tb_meta_sop</b> + clusterização por território).
      Dados lidos diretamente da pasta <b>Modelo/Input</b>.
    </footer>
    """, unsafe_allow_html=True)
