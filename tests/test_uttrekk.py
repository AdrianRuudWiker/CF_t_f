"""Akseptansetester for uttrekket.

Disse skal kjøre grønt FØR det bygges noe som helst modell. Alle måltall er
etablert uavhengig av denne modellen: fra Revidert nasjonalbudsjett 2026, fra
gjennomgangen av den forrige modellen, og fra Ressursrapport 2026.

    pytest -v

Testene hopper over seg selv til data/inndata.csv finnes.
"""

from __future__ import annotations

import os

import pandas as pd
import pytest

INNDATA = "data/inndata.csv"


@pytest.fixture(scope="module")
def d() -> pd.DataFrame:
    if not os.path.exists(INNDATA):
        pytest.skip("data/inndata.csv finnes ikke ennå — kjør steg 0 først")
    df = pd.read_csv(INNDATA)
    kolonne = "ar" if "ar" in df.columns else df.columns[0]
    return df.set_index(kolonne)


def _npv(serie: pd.Series, rente: float, fra: int, til: int, datert: int = 2025) -> float:
    return sum(
        serie[t] / (1 + rente) ** (t - datert)
        for t in range(fra, til + 1)
        if t in serie.index and pd.notna(serie[t])
    )


# --- 1-3: kontantstrømmen ---------------------------------------------------

def test_snks_2026(d):
    """RNB 2026 anslår netto kontantstrøm 2026 til 685,6 mrd. kroner."""
    assert d.loc[2026, "snks"] == pytest.approx(685.6, rel=0.02)


def test_kumulativ_snks(d):
    """Kumulativ SNKS 2026-2050 = 4 861 mrd. kroner."""
    s = d["snks"].loc[2026:2050].sum()
    assert s == pytest.approx(4861, rel=0.01)


def test_nnv_4pst(d):
    """NPV(4 pst.; 2026-2060) datert 2025 = 3 671 mrd. kroner på NB26s bane."""
    assert _npv(d["snks"], 0.04, 2026, 2060) == pytest.approx(3671, rel=0.01)


# --- 4-6: volum og skatt ----------------------------------------------------

def test_produksjon_2026(d):
    """NB26s samlede produksjon i 2026 er om lag 236 mill. Sm³ o.e."""
    tot = d.loc[2026, ["produksjon_olje", "produksjon_gass", "produksjon_ngl"]].sum()
    assert tot == pytest.approx(236, rel=0.03)


def test_sodir_2050(d):
    """Sokkeldirektoratets baner i 2050: basis 90, høy 160, lav 15."""
    for kol, mal in [("produksjon_sd_basis", 90),
                     ("produksjon_sd_hoy", 160),
                     ("produksjon_sd_lav", 15)]:
        assert d.loc[2050, kol] == pytest.approx(mal, rel=0.10), kol


def test_marginalskattesats(d):
    """Marginalskattesatsen er 0,78 gjennom hele perioden."""
    s = d["marginalskattesats"].dropna()
    assert (s.round(3) == 0.78).all()


# --- 7: struktur ------------------------------------------------------------

def test_ingen_nuller_for_hull(d):
    """Hull skal være tomme, ikke null. Sodirs baner starter i 2025."""
    assert pd.isna(d.loc[2020, "produksjon_sd_basis"])


def test_lavbane_aldri_over_basis(d):
    """Regresjonstest. Den forrige modellen delte Sodirs høy/lav på NB26s basis,
    og fikk en lavbane som lå over basisbanen i 2026-2029."""
    f = d["produksjon_sd_lav"] / d["produksjon_sd_basis"]
    assert (f.dropna() <= 1.0 + 1e-9).all()


# --- 8: den parameterfrie kontrollen ---------------------------------------

def test_volumforhold_hoy_lav(d):
    """Sokkeldirektoratets egne priselastisiteter impliserer at kumulativt volum
    i Høy er 1,89 ganger volumet i Lav. Fritt for både m og pris.

    Slår denne feil, er enten avlesningen av figur 2.5 eller forutsetningen om
    én felles pris per fat o.e. gal. Stopp og les figurene på nytt før noe
    annet gjøres.
    """
    from src.sodir import avled

    vh = d["produksjon_sd_hoy"].loc[2026:2050].sum()
    vl = d["produksjon_sd_lav"].loc[2026:2050].sum()
    forventet = avled()["volumforhold_hoy_lav"]
    assert vh / vl == pytest.approx(forventet, rel=0.15), (
        f"volumforhold {vh/vl:.2f}, forventet {forventet:.2f}"
    )
