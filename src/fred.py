"""Henter prisserier fra FRED.

Alle serier her er offentlige og siterbare. API-nøkkel er valgfri — CSV-endepunktet
krever den ikke — men settes den, brukes den offisielle API-en, som gir vintages
og bedre feilmeldinger. Legg nøkkelen i miljøvariabelen FRED_API_KEY.

Serier:
    WTISPLC        WTI spot, månedlig fra 1946. Lengste brukbare oljeprisserie.
    DCOILBRENTEU   Brent spot, daglig fra 1987. Kryssjekk.
    CPIAUCSL       US KPI, til deflatering.
    OVXCLS         CBOE oljevolatilitetsindeks, daglig fra 2007.
    DHHNGSP        Henry Hub gasspris. Kun kryssjekk — TTF er den relevante for
                   norsk gass og må hentes fra Macrobond.
"""

from __future__ import annotations

import os
import numpy as np
import pandas as pd

CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
API = "https://api.stlouisfed.org/fred/series/observations"

SERIER = {
    "wti": "WTISPLC",
    "brent": "DCOILBRENTEU",
    "kpi": "CPIAUCSL",
    "ovx": "OVXCLS",
    "henry_hub": "DHHNGSP",
}


def hent(serie_id: str) -> pd.Series:
    """Henter én FRED-serie som en pandas Series indeksert på dato."""
    nokkel = os.environ.get("FRED_API_KEY")
    if nokkel:
        params = {
            "series_id": serie_id,
            "api_key": nokkel,
            "file_type": "json",
        }
        import requests

        svar = requests.get(API, params=params, timeout=30)
        svar.raise_for_status()
        obs = pd.DataFrame(svar.json()["observations"])
        s = pd.Series(
            pd.to_numeric(obs["value"], errors="coerce").values,
            index=pd.to_datetime(obs["date"]),
            name=serie_id,
        )
    else:
        df = pd.read_csv(CSV.format(serie_id), parse_dates=[0], index_col=0)
        s = df.iloc[:, 0]
        s.name = serie_id
    return s.dropna()


def realpris_arlig(serie_id: str = "WTISPLC", basisar: int | None = None) -> pd.Series:
    """Årlig gjennomsnittlig realpris, indeksert på årstall.

    Deflatert med CPIAUCSL. Uten basisår brukes siste observasjon av KPI.
    """
    pris = hent(serie_id)
    kpi = hent("CPIAUCSL")
    d = pd.concat([pris.rename("p"), kpi.rename("kpi")], axis=1).dropna()
    ref = d.kpi.iloc[-1] if basisar is None else d.kpi[d.index.year == basisar].mean()
    real = d.p / d.kpi * ref
    ut = real.resample("YE").mean()
    ut.index = ut.index.year
    return ut


def sigma_fra_ovx(vindu_dager: int = 365) -> dict[str, float]:
    """σ for prisprosessen, utledet av OVX.

    OVX er annualisert implisitt volatilitet for SPOT-prisen. Modellen bruker
    årsgjennomsnitt. Variansen til gjennomsnittet av en brownsk bane over et år
    er σ²/3, så standardavviket i årsgjennomsnittet er σ/√3. Uten denne
    korreksjonen overvurderes σ med om lag 70 pst.
    """
    ovx = hent("OVXCLS")
    nylig = ovx[ovx.index >= ovx.index[-1] - pd.Timedelta(days=vindu_dager)]
    return {
        "spot_median_hele": ovx.median() / 100,
        "spot_median_nylig": nylig.median() / 100,
        "arsgjennomsnitt_hele": ovx.median() / 100 / np.sqrt(3),
        "arsgjennomsnitt_nylig": nylig.median() / 100 / np.sqrt(3),
    }
