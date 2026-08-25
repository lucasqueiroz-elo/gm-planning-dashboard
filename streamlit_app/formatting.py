"""Funções de formatação pt-BR, portadas 1:1 das funções JS do GM_Planning_Dashboard.html
(fmtBRL, fmtPct, fmtSignedPct, fmtPP), incluindo o comportamento "bugado" de fmtSignedPct
(nunca prefixa '+'), que foi mantido por decisão de fidelidade ao dashboard original.
"""
from __future__ import annotations

import math

import pandas as pd


def _is_missing(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v)) or pd.isna(v)


def fmt_brl(v) -> str:
    """Réplica de fmtBRL: 'R$ ' + Math.round(v).toLocaleString('pt-BR')."""
    if _is_missing(v):
        return "—"
    n = round(v)
    sign = "-" if n < 0 else ""
    s = f"{abs(n):,}".replace(",", ".")
    return f"R$ {sign}{s}"


def fmt_pct(v, dec: int = 1) -> str:
    """Réplica de fmtPct: (v*100).toFixed(dec) com ',' no lugar de '.'."""
    if _is_missing(v):
        return "—"
    return f"{v * 100:.{dec}f}".replace(".", ",") + "%"


def fmt_signed_pct(v, dec: int = 1) -> str:
    """Réplica de fmtSignedPct do HTML original — a variável de sinal do JS é sempre
    '' (bug), então o comportamento é idêntico a fmt_pct. Mantido por fidelidade."""
    return fmt_pct(v, dec)


def fmt_pp(v, dec: int = 1) -> str:
    """Réplica de fmtPP: prefixa '+' explícito quando v>=0, sufixo ' pp'."""
    if _is_missing(v):
        return "—"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v * 100:.{dec}f}".replace(".", ",") + " pp"


def fmt_int(v) -> str:
    """Réplica de v.toLocaleString('pt-BR') para inteiros (ex: contagem de PDVs)."""
    if _is_missing(v):
        return "—"
    return f"{int(round(v)):,}".replace(",", ".")


def badge_class(kind: str, v) -> str:
    """Réplica de badgeClass(kind, v) do HTML original."""
    if _is_missing(v):
        return "badge-gray"
    if kind == "fat" or kind == "lucro":
        return "badge-green" if v >= 1 else ("badge-yellow" if v >= 0.7 else "badge-red")
    if kind == "spread":
        return "badge-green" if v <= 0 else ("badge-yellow" if v <= 0.01 else "badge-red")
    return "badge-gray"
