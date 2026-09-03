"""Tofaktor prisprosess. Brukes KUN i steg 3, og KUN på Basis-banen.

    d[t] = chi[t] + xi[t]
    chi[t] = a*chi[t-1] + sqrt(1-omega)*sigma*eps[t]     transitorisk
    xi[t]  = xi[t-1]    + sqrt(omega)  *sigma*eta[t]     varig
    d[0] = 0
    pris[t] = basispris[t] * exp(d[t])

d[0] = 0 er hele rettelsen av termstrukturen: viften starter smal og bygger
seg opp. Den forrige modellen trakk ETT sjokk per simulering og påla den
stasjonære fordelingen fra år 1, slik at 2026 fikk et 80 pst.-intervall på
41-112 USD/fat i et år der terminkurven er kjent.

MEDIANFORANKRING: exp(d) har median 1. Ingen -0.5*V-korreksjon skal legges inn.
Middelverdien ligger over basis fordi fordelingen er høyreskjev; det hører
hjemme i én fotnote, ikke i et eget persentilsett.

sigma settes fra implisitt volatilitet, KORRIGERT til årsgjennomsnitt ved å
dele på sqrt(3). Se src/fred.sigma_fra_ovx().

omega og a kalibreres mot den empiriske impulsresponsen. Se src/persistens.py.

NGL følger oljesjokket fullt ut (korrelasjon 0,945 i årlige logendringer).
Korrelasjonen olje-gass settes til det estimerte, ikke til et rundt tall.

TODO (CC).
"""

from __future__ import annotations

import numpy as np


def simuler(n_sim, ar, sigma, omega, a, rho=None, frø=None):
    raise NotImplementedError
