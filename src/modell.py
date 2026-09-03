"""Deterministisk motor. Brukes i steg 1 og steg 2.

Modellerer AVVIK fra basis, ikke nivåer, slik at basisidentiteten mot NB26
holder eksakt per konstruksjon:

    SNCF[t] = maks( SNKS_basis[t] + m[t] * (d_inntekt[t] - d_kostnad[t]), 0 )

m[t] er MARGINAL statlig uttaksrate, regnet fra marginalskattesats 0,78 og
SDØEs produksjonsandeler. Den ligger på 0,80-0,82 over perioden.

Bruk ALDRI gjennomsnittsandelen SNKS/(inntekt-kostnad) som marginalrate. Det
var feilen i den forrige modellen, og den overdrev priselastisiteten med
8-20 pst.

Gulvet maks(., 0) beholdes, men bindingsraten skal rapporteres per år. Merk at
maks(sum felt, 0) ikke er sum maks(felt, 0): aggregatgulvet undervurderer
tilbudsresponsen. Akseptabelt fordi det binder i år som er verdt lite.

TODO (CC).
"""

from __future__ import annotations

import pandas as pd


def marginalrate(inndata: pd.DataFrame) -> pd.Series:
    raise NotImplementedError


def kontantstrom(inndata: pd.DataFrame, priser: pd.DataFrame, volum: pd.DataFrame) -> pd.Series:
    raise NotImplementedError


def nnv(strom: pd.Series, rente: float, datert: int = 2025) -> float:
    """Nåverdi. Første beløp i 2026 diskonteres én periode -> datert 2025,
    som er samme konvensjon som Perspektivmeldingens 4 800 mrd. kroner."""
    return sum(v / (1 + rente) ** (t - datert) for t, v in strom.items())


def implisert_marginalandel(vol_hoy, vol_lav, pris_usd=80.0, fx=10.2,
                            spenn_felles=7400.0, spenn_parret=15200.0,
                            fat_per_sm3=6.29):
    """Steg 1: identifiserer statens marginale uttaksandel fra Sokkeldirektoratets
    to publiserte spenn. Kostnadene faller ut.

        Spenn(80)     = m*[(R_H - C_H) - (R_L - C_L)]
        Spenn(100/60) = m*[(1,25R_H - C_H) - (0,75R_L - C_L)]
        differanse    = m*0,25*(R_H + R_L)

    vol_hoy, vol_lav: kumulativt volum i mill. Sm3 o.e. Bare SUMMEN inngår.
    Returnerer m. Tolkning: 0,80-0,82 statens andel, ~1,00 sektorens
    verdiskaping, utenfor 0,6-1,2 betyr at forutsetningen om én felles pris
    per fat o.e. ikke holder.
    """
    brutto = fat_per_sm3 * pris_usd * fx * (vol_hoy + vol_lav) / 1000  # mrd. kroner
    return (spenn_parret - spenn_felles) / (0.25 * brutto)
