"""Akseptansetester for steg 2 — motoren og broen.

    pytest -v
"""

from __future__ import annotations

import os

import pandas as pd
import pytest

INNDATA = "data/inndata.csv"


@pytest.fixture(scope="module")
def d():
    if not os.path.exists(INNDATA):
        pytest.skip("data/inndata.csv finnes ikke ennå — kjør steg 0 først")
    from src import steg1
    return steg1.last()


def test_basisidentiteten_er_eksakt(d):
    """Motoren uten argumenter SKAL gi NB26s egen bane, på maskinpresisjon.

    Dette er hele poenget med å modellere avvik i stedet for nivåer. Slår den
    feil, er det ikke en unøyaktighet — da er motoren gal.
    """
    from src import modell

    sncf = modell.kontantstrom(d)
    assert (sncf - d["snks"]).loc[2026:2060].abs().max() == 0.0


def test_volumbaner_mot_sodirs_egen_basis(d):
    """f[t] = SD_scenario[t] / SD_basis[t], aldri delt på NB26s basis.

    Regresjonstest mot den forrige modellens feil. Basisbanen skal komme
    uendret ut, og lavbanen skal aldri ligge over den.
    """
    from src import modell

    v = modell.volumbaner(d)
    for r in modell.RESSURSER:
        assert (v["basis"][r].loc[2026:2050]
                - d[f"produksjon_{r}"].loc[2026:2050]).abs().max() < 1e-12
        f = (v["lav"][r] / v["basis"][r]).loc[2026:2050]
        assert (f <= 1.0 + 1e-9).all()
        assert (v["hoy"][r] / v["basis"][r]).loc[2026:2050].min() >= 1.0 - 1e-9


def test_broen_summerer_til_sodir(d):
    """Broen skal lande på Sokkeldirektoratets publiserte 7 500 mrd."""
    from src import sodir, steg2

    b = steg2.broen(d)
    assert b.sum() == pytest.approx(sodir.NNV_4PST[("basis", 80)], abs=0.5)


def test_broen_stemmer_med_motoren(d):
    """Leddene før uttaksrate og avlesning skal gi samme nivå som motoren.

    Broen bygges av lukkede uttrykk, motoren av årlige kontantstrømmer. At de
    møtes er kontrollen på at dekomponeringen ikke har mistet noe underveis.
    """
    from src import modell, steg1, steg2

    b = steg2.broen(d)
    niva = b.drop(["Uttaksrate: 0,824 → 0,780", "Avlesning av figur 2.6"]).sum()

    f = d["produksjon_sd_basis"] / sum(d[f"produksjon_{r}"]
                                       for r in modell.RESSURSER)
    volum = pd.DataFrame({r: d[f"produksjon_{r}"] * f for r in modell.RESSURSER})
    e = steg2.sd_enhetskostnad(d)
    kost = modell.realkostnader(d)["sum"] * f
    kost = kost * (e["basis"] * steg1.volumer(d, steg2.RENTE)["basis"] / 1000
                   / steg2.nnv(kost))
    direkte = steg2.nnv(modell.kontantstrom(
        d, priser=steg2.flate_priser(d), volum=volum, kostnad=kost))
    assert niva == pytest.approx(direkte, rel=0.005)


def test_gassleddet_dominerer(d):
    """Poenget med hele vedlegget: gassprisen bærer forskjellen."""
    from src import steg2

    b = steg2.broen(d)
    gass = b["Pris: gass → 80 USD"]
    andre = b.drop(["NB26, NNV 4 pst. 2026-2060", "Pris: gass → 80 USD"])
    assert gass > 0
    assert gass > andre.abs().max()
    assert gass / b.drop("NB26, NNV 4 pst. 2026-2060").abs().sum() > 0.4


def test_gassprisgjennomslag_halverer_gassleddet(d):
    """Åpent punkt 3. Halvt gjennomslag skal halvere gassbidraget."""
    from src import modell, steg2

    flat = steg2.flate_priser(d)
    helt = steg2.nnv(modell.kontantstrom(d, priser=flat))
    halvt = steg2.nnv(modell.kontantstrom(d, priser=flat,
                                          gassprisgjennomslag=0.5))
    basis = steg2.nnv(modell.kontantstrom(d))
    assert (halvt - basis) == pytest.approx(
        (helt - basis) - 0.5 * steg2.broen(d)["Pris: gass → 80 USD"], rel=0.1)
