"""Kilder -> data/inndata.csv, med årgangsmerking i data/kilder.csv.

Dette steget finnes fordi NB27 kommer senere i år. Når den gjør det, skal
bytte av tallgrunnlag være én endring her og en ny kjøring — ikke en runde med
innliming. Den forrige modellen limte inn verdier uten kobling til kilde, og
det var årsaken til at Sokkeldirektoratets høy/lav ble delt på NB26s basis i
stedet for Sokkeldirektoratets egen.

KONTRAKT
    inndata.csv:  én rad per år (1971-2090), én kolonne per serie, ingen hull
                  markert som 0 — bruk tom celle.
    kilder.csv:   én rad per serie, med årgang og uttrekksdato utfylt.

REGLER
    - Kostnader = påløpte utgifter delt på deflatoren. IKKE arbeidsbokens
      "faste priser"-rader; de ligger om lag 24 pst. lavere på egen basis.
    - Drifts- og investeringsutgifter hentes hver for seg, ikke som sum.
    - Volumforholdstall regnes mot Sokkeldirektoratets EGEN basis:
          f[t] = SD_scenario[t] / SD_basis[t]
      og anvendes deretter på NB26s basisbane. Aldri SD_scenario / NB26_basis.

TODO (CC): implementer les_mulighetsbilde() og les_ressursrapport().
"""

from __future__ import annotations

import pandas as pd

RAW = "data/raw"
UT = "data/inndata.csv"


def les_mulighetsbilde(sti: str) -> pd.DataFrame:
    raise NotImplementedError


def les_ressursrapport(sti: str) -> pd.DataFrame:
    raise NotImplementedError


def bygg() -> pd.DataFrame:
    raise NotImplementedError
