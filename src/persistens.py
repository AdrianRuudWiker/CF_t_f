"""Estimerer hvor mye av et prissjokk som varer.

Sentralt begrep: φ, andelen av et års prisbevegelse som fortsatt er der ti år
senere. φ = 0 er ren gjennomsnittsreversjon, φ = 1 er en tilfeldig gange.
Parameteren er valgt fordi den kan forsvares muntlig; κ og σ_ξ kan ikke.

To uavhengige estimatorer, begge på realpris:

    lokal_projeksjon   regresserer den kumulative bevegelsen fra t−1 til t+h på
                       bevegelsen i år t. Koeffisienten ER φ ved h = 10.
    variansforhold     Var(Δ_k x) / (k · Var(Δ_1 x)). Konvergerer mot den varige
                       andelen av sjokkvariansen.

På WTI 1947–2025 gir de henholdsvis 0,73 (markedsperioden) til 0,82 (hele
utvalget), og 0,66–0,79 i variansandel. Sentralanslag φ = 0,75, følsomhet 0,5
og 1,0.

FORBEHOLD SOM SKAL STÅ I METODE.md:
  - Standardfeilene er om lag 0,18. 79 årsobservasjoner rommer seks–sju
    uavhengige tiårsepisoder, og vinduene overlapper.
  - Ikke-monotoni rundt h = 5 er småutvalgsstøy, ikke et trekk ved prosessen.
  - Estimatorer av denne typen er nedadbiaserte i små utvalg. 0,75 er trolig
    et gulv.
  - Estimatet gjelder WTI i faste dollar. Reestimer på KVARTS-serien i kroner
    som kryssjekk, men behold dollarserien som primært grunnlag: 79 år slår
    28 år for en strukturell parameter.
  - Gass kan ikke estimeres troverdig. Hubprising har eksistert siden om lag
    1997. Sett gass lik olje med eksplisitt forbehold, eller lavere på
    strukturelt grunnlag. Uansett: antakelse, ikke anslag.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def lokal_projeksjon(logpris: pd.Series, hmax: int = 15, fra: int | None = None) -> pd.DataFrame:
    """β[h] = andelen av ett års prisbevegelse som gjenstår h år senere.

    logpris: Series indeksert på årstall, log av realpris.
    Returnerer DataFrame med kolonnene beta, std_feil og n.
    """
    x = logpris if fra is None else logpris[logpris.index >= fra]
    sjokk = x.diff()
    rader = []
    for h in range(hmax + 1):
        y = x.shift(-h) - x.shift(1)
        df = pd.concat([y.rename("y"), sjokk.rename("s")], axis=1).dropna()
        m = sm.OLS(df.y, sm.add_constant(df.s)).fit(
            cov_type="HAC", cov_kwds={"maxlags": h + 1}
        )
        rader.append({"h": h, "beta": m.params["s"], "std_feil": m.bse["s"], "n": len(df)})
    return pd.DataFrame(rader).set_index("h")


def variansforhold(logpris: pd.Series, k: int) -> float:
    """Lo–MacKinlay variansforhold med overlappende vinduer, forventningsrett."""
    r = logpris.diff().dropna()
    n = len(r)
    rk = (logpris - logpris.shift(k)).dropna()
    m = k * (n - k + 1) * (1 - k / n)
    mu = r.mean()
    return (((rk - k * mu) ** 2).sum() / m) / (((r - mu) ** 2).sum() / (n - 1))


def kalibrer(beta_mal: pd.Series, sigma: float, horisonter=(1, 3, 5, 10), n_sim: int = 20000):
    """Finner ω og a slik at modellens egen impulsrespons matcher den empiriske.

    Kalibreringsmålet er dermed nøyaktig det samme objektet som er estimert —
    ingen oversettelse mellom halveringstider og varige andeler underveis.

    TODO (CC): rutenettsøk over ω ∈ [0, 1] og a ∈ [0, 1). For hvert par,
    simuler serier med prisprosess.simuler(), kjør lokal_projeksjon() på dem,
    og minimer kvadratavviket mot beta_mal på de oppgitte horisontene.
    Returner (omega, a) og avviket.
    """
    raise NotImplementedError("Se docstring — implementeres i steg 3.")
