"""Akseptansetester for steg 1 — Sokkeldirektoratets forutsetninger.

Låser resultatene fra gjenutledningen, slik at en ny årgang eller en endret
figuravlesning gir rødt i stedet for å drive stille.

    pytest -v
"""

from __future__ import annotations

import os

import pytest

INNDATA = "data/inndata.csv"


@pytest.fixture(scope="module")
def d():
    if not os.path.exists(INNDATA):
        pytest.skip("data/inndata.csv finnes ikke ennå — kjør steg 0 først")
    from src import steg1
    return steg1.last()


def test_marginalrate_er_strukturell(d):
    """NB26s marginalrate skal ligge på 0,80-0,84, ikke på gjennomsnittsandelen.

    Marginalraten er 0,78 marginalskatt pluss SDØEs direkte eierandel av
    produksjonen. Gjennomsnittsandelen SNKS/(inntekt−kostnad) ligger på
    0,87-1,01 og inneholder utbytte og periodisering som ikke skalerer med
    prisen. Blandes de sammen, overdrives priselastisiteten med 8-20 pst.
    """
    from src import modell

    m = modell.marginalrate(d).loc[2026:2050]
    assert m.min() > 0.80 and m.max() < 0.84

    snitt = (d["snks"] / (modell.inntekt(d)["sum"]
                          - modell.realkostnader(d)["sum"])).loc[2026:2050]
    assert snitt.max() > 1.0          # over 100 pst. — kan ikke være en andel
    assert (snitt - m).abs().mean() > 0.05


def test_ngl_bruker_oljens_sdoe_andel(d):
    """SDØEs NGL-andel i kilden passerer 1 i 2055-2058 og skal ikke brukes."""
    from src import modell

    assert d["sdoe_andel_ngl"].max() > 1.0        # kilden er slik
    m = modell.marginalrate(d, sdoe_ngl_som_olje=True).loc[2026:2090]
    assert m.max() < 0.84
    raa = modell.marginalrate(d, sdoe_ngl_som_olje=False).loc[2026:2090]
    assert (raa - m).abs().max() < 0.01           # liten effekt, men reell


def test_sodir_m_matcher_nb26(d):
    """Sokkeldirektoratets impliserte uttaksrate skal falle sammen med NB26s.

    Er den om lag 1,00, gjelder Sokkeldirektoratets tall sektorens
    verdiskaping og ikke statens, og hele sammenligningen i steg 2 faller.
    """
    from src import modell, sodir, steg1

    u = steg1.volumer(d)
    m_sodir = sodir.avled()["mR_hoy"] / steg1.bruttoinntekt(u["hoy"], d)
    vekt = modell.inntekt(d)["sum"].loc[2026:2050]
    m_nb = float((modell.marginalrate(d).loc[2026:2050] * vekt).sum() / vekt.sum())
    assert m_sodir == pytest.approx(m_nb, rel=0.05)
    assert 0.75 < m_sodir < 0.90


def test_volumforhold_diskontert(d):
    """Figur 2.6 impliserer Høy/Lav = 1,55 diskontert med 4 pst.

    Strengere enn den udiskonterte kontrollen, fordi den også tester NÅR
    volumet kommer. Slår den feil mens den udiskonterte holder, er
    tidsprofilen i banene gal.
    """
    from src import steg1

    n = steg1.volumer(d, steg1.RENTE)
    ventet = steg1._avled_nnv()["volumforhold_hoy_lav"]
    assert n["hoy"] / n["lav"] == pytest.approx(ventet, rel=0.10)
