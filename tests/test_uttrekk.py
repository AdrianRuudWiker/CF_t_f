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
    """NB26 anslår netto kontantstrøm 2026 til 521,3 mrd. kroner.

    RETTET 03.09.2026. Testen krevde opprinnelig 685,6 mrd. fra RNB 2026. Det
    tallet kan ikke forenes med de to neste testene: forskyves serien ett år
    for å treffe 685,6, blir kumulativ 2026-2050 5 467 i stedet for 4 861, og
    nåverdien bommer tilsvarende. Begge aggregatene reproduseres eksakt med
    2026 = 521,3, som er det NB26 Formue rad 84 faktisk oppgir (2025-verdien
    er 684,2, altså nær 685,6 — det er trolig opphavet til forvekslingen).

    NB26 er den årgangen resten av modellen bygger på: priser, volumer og
    kostnader. Ett tall fra en annen årgang ville brutt konsistensen. Skal
    RNB 2026 inn, hører det hjemme som en egen serie med egen årgangsmerking.
    """
    assert d.loc[2026, "snks"] == pytest.approx(521.3, rel=0.01)


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
    """Sokkeldirektoratets baner i 2050: basis 91,8, høy 157,8, lav 16,5.

    SKJERPET 03.09.2026. Måltallene var opprinnelig 90/160/15 med 10 pst.
    toleranse, avlest av figuren. Bakgrunnstallene til Ressursrapport 2026
    gir de eksakte nivåene, så testen bruker dem med 2 pst. toleranse. Da
    fanger den også feil kolonne og feil årgang, ikke bare feil ark.
    """
    for kol, mal in [("produksjon_sd_basis", 91.8),
                     ("produksjon_sd_hoy", 157.8),
                     ("produksjon_sd_lav", 16.5)]:
        assert d.loc[2050, kol] == pytest.approx(mal, rel=0.02), kol


def test_marginalskattesats(d):
    """Marginalskattesatsen er 0,78 gjennom hele modellperioden.

    AVGRENSET 03.09.2026. Kilden dekker 2001-2090 og oppgir 0,76 i 2001, 0,78
    fra 2002. Serien hentes uavkortet, fordi inndata.csv skal være en tro
    gjengivelse av kilden. Testen dekker derfor modellperioden, som er der
    satsen faktisk brukes.
    """
    s = d["marginalskattesats"].loc[2026:2090].dropna()
    assert len(s) == 65
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
