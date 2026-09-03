"""Sokkeldirektoratets publiserte tall, og hva som kan utledes av dem.

Nivåene er avlest av figur 2.5 og 2.6 i Ressursrapport 2026. Avlesningen
reproduserer alle fire spennene Sokkeldirektoratet oppgir i teksten (7 400,
15 200, 3 200, 8 300) eksakt, så den er pålitelig.

FORUTSETNINGEN: teksten oppgir bare én pris per fat, ingen gassprisbane. All
produksjon ser derfor ut til å være verdsatt til én felles pris per fat
oljeekvivalent. Det er bekreftet tre veier:
  1. de fire spennene reproduserer fra nivåene
  2. de impliserte kost/inntekt-forholdene (27,5 og 31,5 pst.) er plausible
  3. avviket mot NB26 (7 500 mot 3 671, faktor 2,04) forklares nesten
     nøyaktig av at flat prising verdsetter gass 2,33 ganger høyere enn
     Energidepartementets gassprisbane, ved en gassandel på om lag 50 pst.

KONSEKVENS FOR NOTATET: Sokkeldirektoratets tall er IKKE sammenlignbare med
NB26s. Begge er merket «netto kontantstrøm», mrd. 2026-kroner, 4 pst. realrente.
Forskjellen er over en faktor to og skyldes nesten utelukkende gassprisen.
"""

from __future__ import annotations

FAT_PER_SM3 = 6.29        # væske
MMBTU_PER_SM3 = 37.9      # gass; 1 Sm³ o.e. = 1000 Sm³ gass

# Avlest av figur 2.5 og 2.6, mrd. 2026-kroner
UDISKONTERT = {
    ("hoy", 80): 14800, ("hoy", 100): 19900,
    ("basis", 80): 12400,
    ("lav", 80): 7400, ("lav", 60): 4700,
}
NNV_4PST = {
    ("hoy", 80): 9100, ("hoy", 100): 12200,
    ("basis", 80): 7500,
    ("lav", 80): 5900, ("lav", 60): 3900,
}

# Energidepartementets forutsetninger, jf. decket 19.03.2026 slide 5
ED_OLJE_USD_FAT = 70.0
ED_GASS_USD_MMBTU = 5.7
SODIR_USD_FAT = 80.0


def kontroller_avlesning() -> dict[str, tuple[int, int]]:
    """Avlest spenn mot oppgitt spenn. Alle fire skal stemme eksakt."""
    U, N = UDISKONTERT, NNV_4PST
    return {
        "udiskontert_felles": (U[("hoy", 80)] - U[("lav", 80)], 7400),
        "udiskontert_parret": (U[("hoy", 100)] - U[("lav", 60)], 15200),
        "nnv_felles": (N[("hoy", 80)] - N[("lav", 80)], 3200),
        "nnv_parret": (N[("hoy", 100)] - N[("lav", 60)], 8300),
    }


def avled() -> dict:
    """Utleder m*R og m*C per bane av priselastisiteten.

    Høy: 14 800 ved 80 USD, 19 900 ved 100 USD. Prisen opp 25 pst. gir
    m*0,25*R = 5 100, altså m*R = 20 400. Kostnaden er uendret, så
    m*C = m*R − netto.

    Volumforholdet Høy/Lav = (m*R_Høy)/(m*R_Lav) er fritt for både m og pris,
    og er derfor en parameterfri test mot de faktiske produksjonsbanene.
    """
    U = UDISKONTERT
    mR_hoy = (U[("hoy", 100)] - U[("hoy", 80)]) / 0.25
    mR_lav = (U[("lav", 80)] - U[("lav", 60)]) / 0.25
    return {
        "mR_hoy": mR_hoy,
        "mR_lav": mR_lav,
        "mC_hoy": mR_hoy - U[("hoy", 80)],
        "mC_lav": mR_lav - U[("lav", 80)],
        "kost_andel_hoy": 1 - U[("hoy", 80)] / mR_hoy,
        "kost_andel_lav": 1 - U[("lav", 80)] / mR_lav,
        "volumforhold_hoy_lav": mR_hoy / mR_lav,
    }


def implisert_m(vol_hoy_mill_sm3: float, fx: float = 10.2) -> float:
    """Statens marginale uttaksandel, gitt kumulativt volum i mulighetsbildet Høy.

    m*R_Høy = 20 400 mrd. kroner, og R_Høy = 6,29 · 80 · fx · volum / 1000.
    Referanse: 0,80-0,82 er den strukturelle marginalandelen (78 pst.
    marginalskatt pluss SDØE-andeler). Om lag 1,00 ville betydd at tallet
    gjelder sektorens verdiskaping, ikke statens.
    """
    brutto = FAT_PER_SM3 * SODIR_USD_FAT * fx * vol_hoy_mill_sm3 / 1000
    return avled()["mR_hoy"] / brutto


def implisert_kostnad(vol_mill_sm3: float, bane: str, m: float, fx: float = 10.2) -> float:
    """Sokkeldirektoratets impliserte kumulative kostnad for en bane, mrd. kroner.

    Sammenlign mot NB26s kostnadsbane. Ingen har gjort den sammenligningen.
    """
    return avled()[f"mC_{bane}"] / m


def prisforhold(gassandel: float = 0.50, kost_andel: float = 0.30) -> dict:
    """Hvor mye høyere Sokkeldirektoratets flate prising verdsetter ressursene.

    Én Sm³ o.e. er 6,29 fat væske, men som gass om lag 37,9 MMBtu. Flat prising
    til 80 USD per fat o.e. gir 503 USD per Sm³ o.e. for ALT. Energidepartementet
    gir 440 USD for olje og 216 USD for gass.

    Nettoen er gearet: inntekten opp med faktor R gir netto opp med
    (R − k)/(1 − k) der k er kostnadsandelen.
    """
    sodir = SODIR_USD_FAT * FAT_PER_SM3
    ed_olje = ED_OLJE_USD_FAT * FAT_PER_SM3
    ed_gass = ED_GASS_USD_MMBTU * MMBTU_PER_SM3
    r_olje, r_gass = sodir / ed_olje, sodir / ed_gass
    r_samlet = (1 - gassandel) * r_olje + gassandel * r_gass
    return {
        "usd_per_sm3_sodir": sodir,
        "usd_per_sm3_ed_olje": ed_olje,
        "usd_per_sm3_ed_gass": ed_gass,
        "forhold_olje": r_olje,
        "forhold_gass": r_gass,
        "forhold_inntekt": r_samlet,
        "forhold_netto": (r_samlet - kost_andel) / (1 - kost_andel),
    }


if __name__ == "__main__":
    print("Kontroll av avlesning (avlest, oppgitt):")
    for k, (a, b) in kontroller_avlesning().items():
        print(f"  {k:22s} {a:6.0f}  {b:6.0f}  {'ok' if a == b else 'AVVIK'}")

    d = avled()
    print("\nUtledet av priselastisiteten:")
    print(f"  m*R_hoy {d['mR_hoy']:8.0f}   m*C_hoy {d['mC_hoy']:7.0f}   kost/inntekt {d['kost_andel_hoy']:.1%}")
    print(f"  m*R_lav {d['mR_lav']:8.0f}   m*C_lav {d['mC_lav']:7.0f}   kost/inntekt {d['kost_andel_lav']:.1%}")
    print(f"  implisert volumforhold Hoy/Lav = {d['volumforhold_hoy_lav']:.2f}")

    p = prisforhold()
    print("\nFlat prising mot Energidepartementets baner:")
    print(f"  olje {p['forhold_olje']:.2f}x   gass {p['forhold_gass']:.2f}x")
    print(f"  samlet inntekt {p['forhold_inntekt']:.2f}x  ->  netto {p['forhold_netto']:.2f}x")
    print(f"  faktisk avvik NNV Basis: 7 500 / 3 671 = {7500/3671:.2f}")
