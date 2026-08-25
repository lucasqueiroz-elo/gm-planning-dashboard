"""Paleta e CSS global, portados 1:1 das variáveis :root e classes do
GM_Planning_Dashboard.html, adaptados para o DOM do Streamlit (containers com
`key=` viram classes `.st-key-<key>`, usadas para estilizar os "painéis" que
hospedam widgets nativos)."""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

LOGO_PATH = Path(__file__).parent / "Logos" / "Simbolo_BAT.png"


@st.cache_data(show_spinner=False)
def get_logo_data_uri() -> str:
    """Logo BAT Brasil (Logos/Simbolo_BAT.png) como data URI base64, para
    embutir via <img> no header (CSS/HTML injetado por st.markdown)."""
    encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap');

:root{
  --bg-deep:#070c30;
  --bg-mid:#0E2B63;
  --card-bg:#101f5f;
  --card-bg-2:#132569;
  --border-blue:#3556c9;
  --border-cyan:#2fb6e0;
  --accent-pink:#ec1a78;
  --accent-pink-soft:#f6c3dd;
  --green:#6fcf5c;
  --cyan:#4fc3f7;
  --yellow:#ffb020;
  --yellow-dark:#b8860b;
  --red:#ff5c73;
  --text:#ffffff;
  --text-muted:#a9b3de;
  --radius-lg:18px;
  --radius-md:12px;
}

html, body, [class*="css"]{ font-family:'Montserrat',Arial,'Helvetica Neue',Helvetica,sans-serif; }

/* fundo geral */
.stApp{ background:var(--bg-mid); color:var(--text); }
[data-testid="stHeader"]{ background:transparent; }
.block-container{ max-width:1440px; padding-top:28px; padding-bottom:60px; }
#MainMenu{ visibility:hidden; }
/* listra de Pantones BAT, fixa no topo da janela (independe de markup do
   Streamlit — [data-testid="stDecoration"] não existe mais nesta versão) */
body::before{
  content:"";
  position:fixed; top:0; left:0; width:100%; height:7px;
  z-index:1000000;
  background:linear-gradient(to right,
    #004F9F 0%, #004F9F 31.19%,
    #00B1EB 31.19%, #00B1EB 49.27%,
    #EF7D00 49.27%, #EF7D00 61.52%,
    #FBBA00 61.52%, #FBBA00 70.75%,
    #50AF47 70.75%, #50AF47 81.12%,
    #AFCA0B 81.12%, #AFCA0B 88.78%,
    #5A328A 88.78%, #5A328A 95.98%,
    #E72582 95.98%, #E72582 100%
  );
}

/* HEADER */
.header-flex{ display:flex; justify-content:space-between; align-items:flex-start; gap:24px; }
.header-logo{ height:56px; width:auto; flex:none; margin-top:6px; }
.eyebrow-bar{ width:74px; height:6px; background:var(--accent-pink); border-radius:3px; margin-bottom:14px; }
h1.gm-title{
  font-size:46px; font-weight:900; letter-spacing:-0.5px; line-height:1.02;
  margin:0; text-transform:uppercase; color:#fff;
}
.subtitle{
  font-size:18px; font-weight:800; font-style:italic; color:var(--accent-pink);
  margin:6px 0 20px; text-transform:uppercase; letter-spacing:0.2px;
}
.header-warning{
  display:flex; align-items:flex-start; gap:9px;
  color:var(--yellow-dark); font-size:12.5px; font-weight:600; line-height:1.5;
  margin:0 0 18px;
}
.header-warning-icon{ flex:none; margin-top:1px; color:var(--yellow-dark); }

/* PANELS (filtros / tabela) via st.container(key=...) -> classe .st-key-<key> */
.st-key-filters_panel, .st-key-table_panel{
  background:linear-gradient(180deg, var(--card-bg) 0%, var(--card-bg-2) 100%);
  border:1px solid var(--border-blue);
  border-radius:var(--radius-lg);
  padding:20px 24px;
  margin-bottom:22px;
}
.st-key-table_panel{ padding:0; overflow:hidden; }

.panel-title{
  font-size:13px; font-weight:800; text-transform:uppercase; letter-spacing:0.5px;
  color:var(--text-muted); margin:0 0 14px;
}

/* widgets nativos (selectbox, segmented control) */
div[data-baseweb="select"] > div{
  background:#0c1748 !important; border:1.5px solid var(--border-cyan) !important;
  border-radius:22px !important; color:#fff !important;
}
div[data-baseweb="select"] span{ color:#fff !important; }
.stSelectbox label, .stSelectbox p{
  font-size:11px !important; font-weight:800 !important; text-transform:uppercase;
  letter-spacing:0.4px; color:#fff !important;
}
ul[data-baseweb="menu"]{ background:#0c1748 !important; }
ul[data-baseweb="menu"] li{ color:#fff !important; }

div[data-testid="stSegmentedControl"] button{
  border-radius:20px !important; font-weight:800 !important; font-size:12.5px !important;
}

/* KPI CARDS (HTML custom) */
.kpi-grid{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:10px; }
.kpi-grid-3{ grid-template-columns:repeat(3,1fr); }
.kpi-card{
  background:linear-gradient(180deg, var(--card-bg) 0%, var(--card-bg-2) 100%);
  border:1.5px solid var(--border-blue);
  border-radius:var(--radius-lg);
  padding:18px 20px; min-height:132px;
  display:flex; flex-direction:column; justify-content:space-between;
}
.kpi-card.warn-border{ border-color:var(--accent-pink-soft); }
.kpi-label{ font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:0.4px; color:#fff; }
.kpi-hero{ font-size:34px; font-weight:900; line-height:1; margin:10px 0 8px; }
.kpi-sub{ font-size:12.5px; color:var(--text-muted); font-weight:600; line-height:1.5; }
.kpi-sub b{ color:#fff; }
.tag-good{ color:var(--green); }
.tag-mid{ color:var(--yellow); }
.tag-bad{ color:var(--red); }

/* DRILLDOWN */
.drill-title{ font-size:22px; font-weight:900; margin:16px 0 6px; text-transform:uppercase; letter-spacing:-0.3px; color:#fff; }

.table-scroll{ max-height:560px; overflow:auto; border-radius:var(--radius-md); }
.table-scroll.tall{ max-height:900px; }
table.gm-table{ width:100%; border-collapse:separate; border-spacing:0; font-size:12.5px; }
table.gm-table thead th{
  position:sticky; top:0; background:#0c3a86; color:#fff; text-align:right;
  padding:10px 10px; font-size:11px; text-transform:uppercase; letter-spacing:0.3px; z-index:2;
}
table.gm-table thead th:first-child{ text-align:left; border-top-left-radius:8px; }
table.gm-table thead th:last-child{ border-top-right-radius:8px; }
table.gm-table tbody td{ padding:9px 10px; text-align:right; border-bottom:1px solid rgba(255,255,255,0.07); white-space:nowrap; }
table.gm-table tbody td:first-child{ text-align:left; font-weight:700; white-space:normal; max-width:190px; }
table.gm-table tbody tr:hover{ background:rgba(255,255,255,0.05); }
.cell-badge{ display:inline-block; padding:3px 9px; border-radius:12px; font-weight:800; font-size:11.5px; }
.badge-red{ background:rgba(255,92,115,0.18); color:#ff8a9c; }
.badge-yellow{ background:rgba(255,176,32,0.18); color:#ffc766; }
.badge-green{ background:rgba(111,207,92,0.18); color:#8fe07d; }
.badge-gray{ background:rgba(255,255,255,0.08); color:var(--text-muted); font-weight:600; }

/* DISTRIBUIÇÃO (histogramas HTML/CSS, sem lib de gráfico) */
.hist-grid{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:18px; }
.hist-card{
  background:linear-gradient(180deg, var(--card-bg) 0%, var(--card-bg-2) 100%);
  border:1.5px solid var(--border-blue); border-radius:var(--radius-lg);
  padding:18px 20px 14px;
}
.hist-title{ font-size:13px; font-weight:800; text-transform:uppercase; letter-spacing:0.4px; color:#fff; margin:0 0 16px; }
.hist-bars{
  display:flex; align-items:flex-end; gap:14px; height:170px;
  border-bottom:1.5px solid rgba(255,255,255,0.7);
}
.hist-bar-col{ flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100%; }
.hist-count{ font-size:13px; font-weight:800; color:#fff; margin-bottom:6px; }
.hist-bar{ width:100%; max-width:64px; border-radius:6px 6px 0 0; min-height:6px; }
.hist-bar-label{
  font-size:10.5px; font-weight:700; color:#ffffff; margin-top:8px;
  text-align:center; text-transform:uppercase; letter-spacing:0.3px;
}

.legend-dot{ display:inline-block; width:9px; height:9px; border-radius:50%; }

/* ACUMULADO DO ANO (YTD) — chart-card reaproveitado do mesmo estilo dos outros cards */
.chart-card{
  background:linear-gradient(180deg, var(--card-bg) 0%, var(--card-bg-2) 100%);
  border:1.5px solid var(--border-blue); border-radius:var(--radius-lg);
  padding:18px 20px 14px; margin-top:18px;
}
.chart-card-title{ font-size:13px; font-weight:800; text-transform:uppercase; letter-spacing:0.4px; color:#fff; margin:0 0 14px; }
.chart-fallback{ color:var(--text-muted); font-size:13px; text-align:center; padding:40px 10px; }

.ytd-chart-svg{ width:100%; height:auto; display:block; }
.ytd-zero-line{ stroke:rgba(255,255,255,0.7); stroke-width:1; }
.ytd-meta-line{ fill:none; stroke:var(--text-muted); stroke-width:2; stroke-dasharray:6 5; }
.ytd-real-line{ fill:none; stroke:var(--cyan); stroke-width:2.5; stroke-linecap:round; stroke-linejoin:round; }
.ytd-marker{ stroke:var(--card-bg); stroke-width:1.5; }
.ytd-axis-label{
  font-family:'Montserrat',Arial,'Helvetica Neue',Helvetica,sans-serif;
  font-size:11px; font-weight:600; fill:#ffffff; text-anchor:middle;
}
.ytd-value-label{
  font-family:'Montserrat',Arial,'Helvetica Neue',Helvetica,sans-serif;
  font-size:10.5px; font-weight:500; fill:#ffffff; text-anchor:middle;
}
.ytd-meta-value-label{
  font-family:'Montserrat',Arial,'Helvetica Neue',Helvetica,sans-serif;
  font-size:10.5px; font-weight:500; fill:var(--text-muted); text-anchor:middle;
}

.ytd-legend-row{
  display:flex; gap:16px; flex-wrap:wrap; align-items:center;
  margin-top:12px; font-size:11.5px; color:var(--text-muted);
}
.ytd-legend-row span{ display:inline-flex; align-items:center; gap:5px; }
.ytd-legend-icon{ display:inline-block; vertical-align:middle; flex:none; }
.ytd-legend-sep{ width:1px; height:14px; background:rgba(255,255,255,0.18); }

footer.gm-footer{ margin-top:34px; text-align:center; color:var(--text-muted); font-size:11.5px; }
footer.gm-footer b{ color:#fff; }

@media (max-width:900px){
  .kpi-grid{ grid-template-columns:repeat(2,1fr); }
  .kpi-grid-3{ grid-template-columns:1fr; }
  .hist-grid{ grid-template-columns:1fr; }
  h1.gm-title{ font-size:34px; }
  .header-logo{ height:38px; }
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
