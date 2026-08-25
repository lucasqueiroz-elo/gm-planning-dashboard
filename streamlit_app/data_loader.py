"""Pipeline de dados: lê os 3 Excel de origem em `Modelo\\Input\\`, junta por TERRITORY e
expõe um dataset "long" (todos os meses) pronto para ser filtrado/agregado pela UI.

Fontes:
- Modelo/Input/[input] tb_resultado.xlsx   (sheet 'tb_resultado')  -> resultado real por TERRITORY x mês
- Modelo/Input/[input] tb_territorios.xlsx (sheet 'tb_territorios') -> cadastro de territórios (sem tempo)
- Modelo/Input/[output] tb_meta_sop.xlsx   (sheet 'Meta de Lucro')  -> meta por TERRITORY x mês
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

MODELO_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = MODELO_DIR / "Input"

RESULTADO_FILE = INPUT_DIR / "[input] tb_resultado.xlsx"
TERRITORIOS_FILE = INPUT_DIR / "[input] tb_territorios.xlsx"
META_FILE = INPUT_DIR / "[output] tb_meta_sop.xlsx"

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}
MESES_ABREV_PT = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}

SORT_OPTIONS = [
    ("fat_gap_asc", "Menor % Meta Faturamento"),
    ("spread_gap_desc", "Mais Acima do Spread Limite"),
    ("lucro_pct_asc", "Menor % Meta Lucro"),
    ("lucro_abs_desc", "Maior Lucro Absoluto"),
]

LEVEL_OPTIONS = [
    # (chave interna de agregação, rótulo exibido) — as chaves internas continuam
    # region/area/territory (mesmas colunas de agrupamento), só os rótulos de negócio mudaram.
    ("region", "1 · Região"),
    ("area", "2 · Território"),
    ("territory", "3 · Zona"),
]


def mes_label(ts: pd.Timestamp) -> str:
    ts = pd.Timestamp(ts)
    return f"{MESES_PT[ts.month]}/{ts.year}"


def file_mtimes() -> tuple:
    """Chave de cache: muda automaticamente se algum dos 3 xlsx for atualizado."""
    files = [RESULTADO_FILE, TERRITORIOS_FILE, META_FILE]
    return tuple(f.stat().st_mtime if f.exists() else 0.0 for f in files)


def _read_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    try:
        return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
    except ValueError:
        # fallback defensivo: nome de aba diferente do esperado -> usa a primeira aba
        return pd.read_excel(path, sheet_name=0, engine="openpyxl")


@st.cache_data(show_spinner="Carregando planilhas...")
def _load_raw(_mtime_key: tuple):
    missing = [str(f) for f in (RESULTADO_FILE, TERRITORIOS_FILE, META_FILE) if not f.exists()]
    if missing:
        raise FileNotFoundError(
            "Arquivo(s) não encontrado(s) na pasta 'Modelo/Input': " + "; ".join(missing)
        )
    resultado = _read_sheet(RESULTADO_FILE, "tb_resultado")
    territorios = _read_sheet(TERRITORIOS_FILE, "tb_territorios")
    meta = _read_sheet(META_FILE, "Meta de Lucro")
    return resultado, territorios, meta


@st.cache_data(show_spinner="Processando dados...")
def build_long_dataset(_mtime_key: tuple) -> pd.DataFrame:
    resultado, territorios, meta = _load_raw(_mtime_key)

    # ---- tb_resultado ----
    resultado = resultado.rename(columns={
        "PRICE_MONTH": "month", "TERRITORY": "territory", "PDVs": "real_pdvs",
        "FATURAMENTO": "real_fat", "GM_PARTIDOR": "real_gm", "SPREAD": "real_spread",
        "LUCRO": "real_lucro",
    })
    resultado = resultado[["month", "territory", "real_pdvs", "real_fat", "real_gm", "real_spread", "real_lucro"]].copy()
    resultado["month"] = pd.to_datetime(resultado["month"]).dt.to_period("M").dt.to_timestamp()
    resultado["territory"] = resultado["territory"].astype(str).str.strip()
    # defensivo: garante grão único TERRITORY x mês
    resultado = resultado.groupby(["territory", "month"], as_index=False).agg(
        real_pdvs=("real_pdvs", "sum"),
        real_fat=("real_fat", "sum"),
        real_gm=("real_gm", "mean"),
        real_spread=("real_spread", "mean"),
        real_lucro=("real_lucro", "sum"),
    )

    # ---- tb_meta_sop ----
    meta = meta.rename(columns={
        "MÊS": "month", "TERRITORY": "territory", "META LUCRO": "meta_lucro",
        "META FATURAMENTO": "meta_fat", "GM PARTIDOR": "meta_gm", "TETO SPREAD": "meta_spread",
    })
    meta = meta[["month", "territory", "meta_lucro", "meta_fat", "meta_gm", "meta_spread"]].copy()
    meta["month"] = pd.to_datetime(meta["month"]).dt.to_period("M").dt.to_timestamp()
    meta["territory"] = meta["territory"].astype(str).str.strip()

    # ---- tb_territorios (cadastro, 1 linha por TERRITORY) ----
    territorios = territorios.rename(columns={
        "TERRITORY": "territory", "TERRITORY_TYPE": "territory_type",
        "TERRITORY_DESCRIPTION": "territory_desc", "SALES_REGIONAL_CLUSTER": "cluster",
        "REGION_NAME": "region", "AREA_DESCRIPTION": "area", "FULL_DIGITAL": "full_digital",
        "LOAD_DATE": "load_date",
    })
    territorios = territorios[[
        "territory", "territory_type", "territory_desc", "cluster", "region", "area",
        "full_digital", "load_date",
    ]].copy()
    territorios["territory"] = territorios["territory"].astype(str).str.strip()
    territorios["load_date"] = pd.to_datetime(territorios["load_date"], errors="coerce")
    territorios = territorios.sort_values("load_date").drop_duplicates("territory", keep="last")

    # ---- join: universo = tb_meta_sop do mês; has_real via merge indicator ----
    merged = meta.merge(resultado, on=["territory", "month"], how="left", indicator=True)
    merged["has_real"] = merged["_merge"] == "both"
    merged = merged.drop(columns=["_merge"])

    merged = merged.merge(territorios.drop(columns=["load_date"]), on="territory", how="left")
    for col in ("territory_type", "cluster", "region", "area", "full_digital"):
        merged[col] = merged[col].fillna("NOT AVAILABLE")
    merged["territory_desc"] = merged["territory_desc"].fillna("")

    return merged.reset_index(drop=True)


def get_available_months(df: pd.DataFrame) -> list[pd.Timestamp]:
    return sorted(pd.Timestamp(m) for m in df["month"].dropna().unique())


def apply_territory_filters(
    df: pd.DataFrame,
    *,
    territory_type: str = "",
    cluster: str = "",
    region: str = "",
    area: str = "",
    full_digital: str = "",
) -> pd.DataFrame:
    """Aplica os filtros de território (Tipo/Cluster/RV/TV/100% Digital) — usada
    tanto no dataframe do mês de análise quanto no dataframe YTD (que ignora o
    filtro de mês, mas deve respeitar os demais filtros)."""
    out = df
    if territory_type:
        out = out[out["territory_type"] == territory_type]
    if cluster:
        out = out[out["cluster"] == cluster]
    if region:
        out = out[out["region"] == region]
    if area:
        out = out[out["area"] == area]
    if full_digital:
        out = out[out["full_digital"] == full_digital]
    return out


def compute_kpis(filtered: pd.DataFrame) -> dict:
    """Réplica de renderKPIs(): soma valores absolutos, calcula razões/ponderações depois.
    Só linhas com has_real=True entram nos cálculos."""
    with_real = filtered[filtered["has_real"]]

    meta_lucro = with_real["meta_lucro"].sum()
    real_lucro = with_real["real_lucro"].sum()
    meta_fat = with_real["meta_fat"].sum()
    real_fat = with_real["real_fat"].sum()
    gmw_real = (with_real["real_gm"] * with_real["real_fat"]).sum()
    gmw_meta = (with_real["meta_gm"] * with_real["meta_fat"]).sum()
    spw_real = (with_real["real_spread"] * with_real["real_fat"]).sum()
    spw_meta = (with_real["meta_spread"] * with_real["meta_fat"]).sum()

    lucro_pct = real_lucro / meta_lucro if meta_lucro > 0 else float("nan")
    fat_pct = real_fat / meta_fat if meta_fat > 0 else float("nan")
    gm_real = gmw_real / real_fat if real_fat > 0 else float("nan")
    gm_meta = gmw_meta / meta_fat if meta_fat > 0 else float("nan")
    sp_real = spw_real / real_fat if real_fat > 0 else float("nan")
    sp_meta = spw_meta / meta_fat if meta_fat > 0 else float("nan")

    return dict(
        lucro_pct=lucro_pct, real_lucro=real_lucro, meta_lucro=meta_lucro,
        fat_pct=fat_pct, real_fat=real_fat, meta_fat=meta_fat,
        gm_real=gm_real, gm_meta=gm_meta, gm_delta=gm_real - gm_meta,
        sp_real=sp_real, sp_meta=sp_meta,
        sp_favoravel=sp_real <= sp_meta,  # NaN <= NaN é False, replicando o JS
        coverage_total=len(filtered), coverage_real=len(with_real),
    )


_GROUP_COLS = [
    "name", "pdvs", "real_fat", "meta_fat", "real_lucro", "meta_lucro",
    "real_spread", "meta_spread", "real_gm", "meta_gm", "fat_gap", "spread_gap", "lucro_pct",
]


def aggregate_groups(filtered: pd.DataFrame, level: str) -> pd.DataFrame:
    """Réplica de aggregate(): agrega por região / região+área / território, somando
    valores absolutos e recompondo spread/GM/percentuais depois (ponderado por faturamento)."""
    with_real = filtered[filtered["has_real"]].copy()
    if with_real.empty:
        return pd.DataFrame(columns=_GROUP_COLS)

    with_real["_gmw_real"] = with_real["real_gm"] * with_real["real_fat"]
    with_real["_gmw_meta"] = with_real["meta_gm"] * with_real["meta_fat"]
    with_real["_spw_real"] = with_real["real_spread"] * with_real["real_fat"]
    with_real["_spw_meta"] = with_real["meta_spread"] * with_real["meta_fat"]

    if level == "region":
        group_keys, name_col = ["region"], "region"
    elif level == "territory":
        group_keys, name_col = ["territory"], "territory"
    else:  # area -> agrupa por region+area (chave composta), nome exibido = só área
        group_keys, name_col = ["region", "area"], "area"

    g = with_real.groupby(group_keys, dropna=False).agg(
        name=(name_col, "first"),
        pdvs=("real_pdvs", "sum"),
        real_fat=("real_fat", "sum"), meta_fat=("meta_fat", "sum"),
        real_lucro=("real_lucro", "sum"), meta_lucro=("meta_lucro", "sum"),
        gmw_real=("_gmw_real", "sum"), gmw_meta=("_gmw_meta", "sum"),
        spw_real=("_spw_real", "sum"), spw_meta=("_spw_meta", "sum"),
    ).reset_index(drop=True)

    g["real_spread"] = (g["spw_real"] / g["real_fat"]).where(g["real_fat"] > 0, 0.0)
    g["meta_spread"] = (g["spw_meta"] / g["meta_fat"]).where(g["meta_fat"] > 0, 0.0)
    g["real_gm"] = (g["gmw_real"] / g["real_fat"]).where(g["real_fat"] > 0, 0.0)
    g["meta_gm"] = (g["gmw_meta"] / g["meta_fat"]).where(g["meta_fat"] > 0, 0.0)
    g["fat_gap"] = (g["real_fat"] / g["meta_fat"]).where(g["meta_fat"] > 0, 0.0)
    g["spread_gap"] = g["real_spread"] - g["meta_spread"]
    g["lucro_pct"] = (g["real_lucro"] / g["meta_lucro"]).where(g["meta_lucro"] > 0, 0.0)

    return g[_GROUP_COLS].reset_index(drop=True)


def sort_groups(groups: pd.DataFrame, sort_key: str) -> pd.DataFrame:
    if groups.empty:
        return groups
    if sort_key == "fat_gap_asc":
        return groups.sort_values("fat_gap", ascending=True).reset_index(drop=True)
    if sort_key == "spread_gap_desc":
        return groups.sort_values("spread_gap", ascending=False).reset_index(drop=True)
    if sort_key == "lucro_pct_asc":
        return groups.sort_values("lucro_pct", ascending=True).reset_index(drop=True)
    if sort_key == "lucro_abs_desc":
        return groups.sort_values("real_lucro", ascending=False).reset_index(drop=True)
    return groups


def compute_fat_histogram(filtered: pd.DataFrame) -> list[tuple[str, int]]:
    """Conta territórios com_real (has_real=True) por faixa de % atingimento de
    Faturamento (REAL_FAT / META_FATURAMENTO), independente do nível de drilldown
    selecionado — mesmos limiares de 70%/100% usados em badge_class('fat', ...)."""
    with_real = filtered[filtered["has_real"]]
    ratio = (with_real["real_fat"] / with_real["meta_fat"]).where(with_real["meta_fat"] > 0, 0.0)
    bins = [
        ("<50%", (ratio < 0.5).sum()),
        ("50-70%", ((ratio >= 0.5) & (ratio < 0.7)).sum()),
        ("70-100%", ((ratio >= 0.7) & (ratio < 1.0)).sum()),
        ("+100%", (ratio >= 1.0).sum()),
    ]
    return [(label, int(count)) for label, count in bins]


def compute_ytd_kpis(df: pd.DataFrame, year: int) -> dict:
    """Métricas 'Acumulado do Ano' (YTD): sempre sobre a base completa (não reage
    aos filtros de território nem ao mês de análise selecionado no topo), somando
    todos os meses do `year` presentes na base. Só linhas com has_real=True entram
    (mesma regra de denominador usada nos outros KPIs do app)."""
    year_df = df[df["month"].dt.year == year]
    with_real = year_df[year_df["has_real"]]

    meta_lucro = with_real["meta_lucro"].sum()
    real_lucro = with_real["real_lucro"].sum()
    meta_fat = with_real["meta_fat"].sum()
    real_fat = with_real["real_fat"].sum()
    spw_real = (with_real["real_spread"] * with_real["real_fat"]).sum()
    spw_meta = (with_real["meta_spread"] * with_real["meta_fat"]).sum()

    lucro_pct = real_lucro / meta_lucro if meta_lucro > 0 else float("nan")
    fat_pct = real_fat / meta_fat if meta_fat > 0 else float("nan")
    sp_real = spw_real / real_fat if real_fat > 0 else float("nan")
    sp_meta = spw_meta / meta_fat if meta_fat > 0 else float("nan")

    return dict(
        lucro_pct=lucro_pct, real_lucro=real_lucro, meta_lucro=meta_lucro,
        fat_pct=fat_pct, real_fat=real_fat, meta_fat=meta_fat,
        sp_real=sp_real, sp_meta=sp_meta, spread_diff=sp_real - sp_meta,
    )


def compute_ytd_monthly_series(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Série mensal (Jan. em diante) do ano corrente para o gráfico Meta vs. Real.
    'meta' soma META_LUCRO de todos os territórios com meta cadastrada no mês
    (sem filtrar por has_real); 'real' soma REAL_LUCRO só de has_real=True — meses
    sem nenhum dado real ficam com 'real' = NaN (vão na linha, sem interpolação)."""
    year_df = df[df["month"].dt.year == year]
    if year_df.empty:
        return pd.DataFrame(columns=["month", "meta", "real", "pct"])

    meta_by_month = year_df.groupby("month")["meta_lucro"].sum()
    real_df = year_df[year_df["has_real"]]
    real_by_month = real_df.groupby("month")["real_lucro"].sum()

    months = sorted(year_df["month"].dropna().unique())
    rows = []
    for m in months:
        m = pd.Timestamp(m)
        meta_v = float(meta_by_month.get(m, 0.0))
        real_v = float(real_by_month[m]) if m in real_by_month.index else float("nan")
        pct = (real_v / meta_v) if (not pd.isna(real_v) and meta_v > 0) else float("nan")
        rows.append({"month": m, "meta": meta_v, "real": real_v, "pct": pct})
    return pd.DataFrame(rows)


def compute_spread_histogram(filtered: pd.DataFrame) -> list[tuple[str, int]]:
    """Conta territórios com_real (has_real=True) por faixa de status de Spread
    (REAL_SPREAD - META_SPREAD), independente do nível de drilldown selecionado."""
    with_real = filtered[filtered["has_real"]]
    diff = with_real["real_spread"] - with_real["meta_spread"]
    bins = [
        ("≤ limite", (diff <= 0).sum()),
        ("+0 a 1pp", ((diff > 0) & (diff <= 0.01)).sum()),
        ("+1 a 3pp", ((diff > 0.01) & (diff <= 0.03)).sum()),
        ("> +3pp", (diff > 0.03).sum()),
    ]
    return [(label, int(count)) for label, count in bins]
