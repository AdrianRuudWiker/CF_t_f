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

ENHETER
    inndata.csv har beløp i mrd. kroner, men priser i kr/Sm3 o.e. og volumer i
    mill. Sm3 o.e. Produktet pris * volum er derfor i MILL. kroner og må deles
    på 1 000. `MILL_PER_MRD` gjør den omregningen ett sted.

STATUS
    marginalrate() er implementert (steg 1). kontantstrom() hører til steg 2
    og står fortsatt igjen.
"""

from __future__ import annotations

import pandas as pd

MILL_PER_MRD = 1_000.0
RESSURSER = ("olje", "gass", "ngl")


def realpriser(inndata: pd.DataFrame) -> pd.DataFrame:
    """Prisbanene deflatert til faste 2026-kroner, kr/Sm3 o.e.

    Kilden oppgir prisene i løpende kroner, mens SNKS er i faste 2026-kroner.
    Deflateringen hører hjemme her, ikke i uttrekket, som skal være en tro
    gjengivelse av kilden.
    """
    return pd.DataFrame(
        {r: inndata[f"prisbane_{r}"] / inndata["deflator"] for r in RESSURSER}
    )


def realkostnader(inndata: pd.DataFrame) -> pd.DataFrame:
    """Påløpte utgifter deflatert, mrd. 2026-kroner, drift og investering hver
    for seg. IKKE arbeidsbokens «faste priser»-rader."""
    return pd.DataFrame({
        "drift": inndata["driftsutgifter"] / inndata["deflator"],
        "investering": inndata["investeringsutgifter"] / inndata["deflator"],
    }).assign(sum=lambda d: d["drift"] + d["investering"])


def inntekt(inndata: pd.DataFrame) -> pd.DataFrame:
    """Brutto salgsinntekt per ressurs, mrd. 2026-kroner."""
    p = realpriser(inndata)
    return pd.DataFrame(
        {r: inndata[f"produksjon_{r}"] * p[r] / MILL_PER_MRD for r in RESSURSER}
    ).assign(sum=lambda d: d[list(RESSURSER)].sum(axis=1))


def marginalrate(inndata: pd.DataFrame, sdoe_ngl_som_olje: bool = True) -> pd.Series:
    """Statens MARGINALE uttaksrate m[t] av en endring i salgsinntekten.

    En krone ekstra i salgsinntekt tilfaller staten på to måter: SDØE eier en
    andel av produksjonen direkte, og resten skattlegges med marginalsatsen.
    Per ressurs r:

        m_r[t] = sdoe_r[t] + skatt[t] * (1 - sdoe_r[t])

    Ressursene veies med sin andel av salgsinntekten samme år, siden det er
    inntektsmiksen som avgjør hva en generell prisendring gir.

    Dette er IKKE gjennomsnittsandelen SNKS/(inntekt - kostnad). Den ligger på
    0,87-1,01 i NB26 og inneholder utbytte og periodisering som ikke skalerer
    med prisen. Brukt som marginalrate overdriver den priselastisiteten med
    8-20 pst.; det var feilen i den forrige modellen.

    `sdoe_ngl_som_olje`: SDØEs NGL-andel i kilden er et forholdstall med
    kollapsende nevner og passerer 1 i 2055-2058, jf. src/uttrekk.py valg 3.
    NGL følger oljen ellers i modellen, så oljens andel brukes i stedet.
    Effekten er liten: NGL er 4,1 pst. av inntekten i 2026 og 0,7 pst. i 2050.

    Gassprisgjennomslaget hører IKKE hjemme her. Det handler om hvor mye av en
    markedsprisendring som når realisert inntekt, ikke om statens andel av den
    inntekten, og legges inn i steg 2.
    """
    andel = {r: inndata[f"sdoe_andel_{r}"] for r in RESSURSER}
    if sdoe_ngl_som_olje:
        andel["ngl"] = andel["olje"]
    skatt = inndata["marginalskattesats"]
    vekt = inntekt(inndata)
    m_r = {r: andel[r] + skatt * (1 - andel[r]) for r in RESSURSER}
    return sum(vekt[r] / vekt["sum"] * m_r[r] for r in RESSURSER).rename("m")


def kontantstrom(inndata: pd.DataFrame, priser: pd.DataFrame, volum: pd.DataFrame) -> pd.Series:
    raise NotImplementedError  # steg 2


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
