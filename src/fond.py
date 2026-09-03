"""Fondsregnskap. Steg 3, deterministisk.

Hele netto kontantstrøm overføres til fondet. Det gjøres INGEN fradrag på vei
inn — skattene er selve kontantstrømmen, ikke noe som trekkes fra den. Uttaket
er det oljekorrigerte underskuddet, vedtatt av Stortinget.

    Fond[t] = Fond[t-1] + SNCF[t] - uttak[t] + r*Fond[t-1]

INGEN fordeling på avkastning. Med fondet på om lag 22 500 mrd. kroner er ett
prosentpoeng avkastning om lag 225 mrd. kroner, mot en årlig kontantstrøm på
om lag 686 mrd. kroner. En fordeling ville gjøre viften til en figur om
aksjemarkedet, ikke om petroleum. At den utelates bevisst, med begrunnelsen
oppgitt, er et sterkere poeng enn en dårlig tegnet vifte.

Valutakurs holdes fast, med fotnote.

Hovedfiguren er kryssningspunktet: tilflyt i pst. av fondsverdi mot uttak i
pst. av fondsverdi. Tilflyten var 73,1 pst. i 2000 og er 3,2 pst. i 2026, mot
et uttak på om lag 3 pst. Krysset skjer altså om lag nå.

TODO (CC).
"""

from __future__ import annotations

import pandas as pd


def rull_fram(sncf: pd.Series, uttak: pd.Series, fond_start: float, r: float = 0.03) -> pd.DataFrame:
    raise NotImplementedError
