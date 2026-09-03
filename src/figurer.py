"""FIN-stil for matplotlib.

Liberation Sans er metrisk identisk med Arial og ligger installert på de fleste
Linux-systemer. Sjekk med:
    fc-list | grep -i liberation
Mangler den:  sudo apt install fonts-liberation
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

MORKEBLA = "#181C62"
MELLOMBLA = "#4156A6"
LYSEBLA = "#5B91CC"
ROD = "#F15D61"
GRA = "#EDEDEE"

SYKLUS = [MORKEBLA, LYSEBLA, ROD, MELLOMBLA]


def sett_stil(dokument: bool = True) -> None:
    """dokument=True gir grå bakgrunn (notat), False gir hvit (presentasjon)."""
    bakgrunn = GRA if dokument else "white"
    mpl.rcParams.update(
        {
            "font.family": "Liberation Sans",
            "font.size": 9,
            "axes.prop_cycle": mpl.cycler(color=SYKLUS),
            "axes.facecolor": bakgrunn,
            "figure.facecolor": bakgrunn,
            "savefig.facecolor": bakgrunn,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": "white" if dokument else "#DDDDDD",
            "grid.linewidth": 0.8,
            "axes.axisbelow": True,
            "legend.frameon": False,
            "figure.dpi": 120,
        }
    )


def lagre(fig, navn: str, mappe: str = "output/figurer") -> None:
    """Lagrer som SVG. Sjekk at skriften faktisk ble Liberation Sans:
    grep -c 'DejaVu' output/figurer/<navn>.svg   # skal gi 0
    """
    fig.savefig(f"{mappe}/{navn}.svg", bbox_inches="tight")
