"""
Marché des métaux 1980-2017 (prix mensuels du FMI) et or 1980-2026.

    python src/analyse_metaux.py
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap

RACINE = Path(__file__).resolve().parents[1]
SERIES = {  # colonne FMI -> (nom, unité)
    "China import Iron Ore Fines 62% FE spot": ("Minerai de fer", "$/t sèche"),
    "Copper": ("Cuivre", "$/t"), "Aluminum": ("Aluminium", "$/t"), "Nickel": ("Nickel", "$/t"),
    "Zinc": ("Zinc", "$/t"), "Lead": ("Plomb", "$/t"), "Tin": ("Étain", "$/t"),
    "Uranium": ("Uranium", "$/lb"), "Coal": ("Charbon", "$/t"), "Crude Oil petroleum": ("Pétrole brut", "$/baril"),
}
BLEU, ORANGE, AQUA, JAUNE, MAGENTA = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"
INK, INK2, GRILLE, GRIS = "#0b0b0b", "#52514e", "#e6e5e1", "#a3a29c"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
                     "axes.edgecolor": INK2, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.titleweight": "bold", "axes.titlelocation": "left",
                     "axes.titlesize": 11})


def charger():
    c = pd.read_csv(RACINE / "data/prix_matieres_premieres_fmi.csv", parse_dates=["Date"]).set_index("Date")
    p = c[list(SERIES)].rename(columns={k: v[0] for k, v in SERIES.items()})
    o = pd.read_csv(RACINE / "data/prix_or_mensuel.csv")
    o["Date"] = pd.to_datetime(o.Date + "-01")
    or_ = o.set_index("Date").Price.rename("Or")
    return p, or_[or_.index >= "1980-01-01"]


def rendements(p):
    return np.log(p).diff().dropna(how="all")


def fig_supercycle(p, chemin):
    base = p.loc["2000"].mean()
    idx = p / base * 100
    sel = [("Minerai de fer", BLEU), ("Cuivre", ORANGE), ("Nickel", AQUA), ("Aluminium", JAUNE)]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.axvspan(pd.Timestamp("2003-01-01"), pd.Timestamp("2011-06-30"), color="#f1f0ec", zorder=0)
    ax.text(pd.Timestamp("2003-03-01"), 1060, "Super-cycle\n(demande chinoise)", fontsize=8.5, color=INK2, va="top")
    fin = {nom: idx[nom].iloc[-1] for nom, _ in sel}
    pos = dict(fin)
    ordre = sorted(fin, key=fin.get)
    for a, b in zip(ordre, ordre[1:]):            # écarte les étiquettes trop proches (échelle log)
        if np.log10(pos[b]) - np.log10(pos[a]) < 0.06:
            pos[b] = pos[a] * 10 ** 0.06
    for nom, c in sel:
        ax.plot(idx.index, idx[nom], color=c, lw=1.8)
        ax.text(idx.index[-1] + pd.Timedelta(days=60), pos[nom], f"{nom} ({fin[nom]:.0f})",
                color=INK, fontsize=8.5, va="center")
    ax.axhline(100, color=GRIS, lw=0.8, ls=":")
    ax.set_yscale("log"); ax.set_yticks([25, 50, 100, 200, 400, 800, 1600], ["25", "50", "100", "200", "400", "800", "1600"])
    ax.set_ylabel("Indice (moyenne 2000 = 100, échelle log.)")
    ax.yaxis.grid(True, color=GRILLE); ax.set_axisbelow(True)
    ax.set_xlim(idx.index[0], idx.index[-1] + pd.Timedelta(days=1700))
    ax.set_title("Entre 2000 et 2011, le fer a été multiplié par 13,5 ; le cuivre par 4,9, le nickel par 2,7")
    fig.tight_layout(); fig.savefig(chemin, dpi=170); plt.close(fig)


def fig_fer(p, chemin):
    f = p["Minerai de fer"]
    pic = f.loc["2009":].idxmax(); creux = f.loc[pic:].idxmin()
    fig, ax = plt.subplots(figsize=(10, 4.4))
    ax.plot(f.index, f, color=BLEU, lw=1.8)
    ax.axvline(pd.Timestamp("2009-01-01"), color=GRIS, lw=1, ls="--")
    ax.text(pd.Timestamp("2008-08-01"), 120, "Jusqu'en 2008 :\nprix de contrat annuel", ha="right", fontsize=8.5, color=INK2, va="top")
    ax.text(pd.Timestamp("2009-04-01"), 38, "Depuis 2009 : prix spot\nChine 62 % Fe", ha="left", fontsize=8.5, color=INK2, va="top")
    for d_, txt, dy in [(pic, f"Pic {f[pic]:.0f} $/t\n{pic:%m/%Y}", 8), (creux, f"Creux {f[creux]:.0f} $/t\n{creux:%m/%Y}", -32)]:
        ax.scatter([d_], [f[d_]], color=ORANGE, s=36, zorder=3, edgecolor="white", linewidth=1.5)
        ax.text(d_, f[d_] + dy, txt, ha="center", fontsize=8.5, color=INK)
    ax.set_ylabel("$ par tonne sèche (nominal)")
    ax.yaxis.grid(True, color=GRILLE); ax.set_axisbelow(True)
    chute = 100 * (f[creux] / f[pic] - 1)
    ax.set_title(f"Minerai de fer : {chute:.0f} % entre le pic de 2011 et le creux de 2015")
    fig.tight_layout(); fig.savefig(chemin, dpi=170); plt.close(fig)
    return pic, creux, chute


def fig_volatilite(r, chemin):
    vol = pd.DataFrame({
        "1980-2004": r.loc[:"2004"].std() * np.sqrt(12) * 100,
        "2005-2017": r.loc["2005":].std() * np.sqrt(12) * 100}).drop(index=["Pétrole brut", "Charbon"])
    vol = vol.sort_values("2005-2017")
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    y = np.arange(len(vol))
    ax.barh(y + 0.2, vol["1980-2004"], height=0.38, color=GRIS, label="1980-2004")
    ax.barh(y - 0.2, vol["2005-2017"], height=0.38, color=BLEU, label="2005-2017")
    for i, v in enumerate(vol["2005-2017"]):
        ax.text(v + 0.5, i - 0.2, f"{v:.0f} %", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(y, vol.index)
    ax.set_xlabel("Volatilité annualisée des rendements mensuels (%)")
    ax.xaxis.grid(True, color=GRILLE); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    ax.set_title("Volatilité : le fer passe de 9 % à 35 %, fin des contrats annuels oblige")
    fig.tight_layout(); fig.savefig(chemin, dpi=170); plt.close(fig)
    return vol


def fig_correlations(r, chemin):
    noms = ["Minerai de fer", "Cuivre", "Aluminium", "Nickel", "Zinc", "Plomb", "Étain", "Pétrole brut", "Or"]
    c = r.loc["2005":, noms].corr()
    cmap = LinearSegmentedColormap.from_list("div", ["#e34948", "#f3f2ee", "#2a78d6"])
    fig, ax = plt.subplots(figsize=(7.6, 6.2))
    im = ax.imshow(c.values, cmap=cmap, vmin=-1, vmax=1)
    ax.set_xticks(range(len(noms)), noms, rotation=40, ha="right"); ax.set_yticks(range(len(noms)), noms)
    for s in ax.spines.values():
        s.set_visible(False)
    for i in range(len(noms)):
        for j in range(len(noms)):
            ax.text(j, i, f"{c.values[i, j]:.2f}".replace(".", ","), ha="center", va="center", fontsize=8,
                    color="white" if abs(c.values[i, j]) > 0.6 else INK)
    fig.colorbar(im, ax=ax, shrink=0.75, label="Corrélation des rendements mensuels")
    ax.set_title("Corrélations 2005-2017 : le fer suit sa propre logique")
    fig.tight_layout(); fig.savefig(chemin, dpi=170); plt.close(fig)
    return c


def export_dashboard(p, or_, chemin):
    tout = p.join(or_, how="outer")
    unites = {v[0]: v[1] for v in SERIES.values()} | {"Or": "$/once"}
    data = {"dates": [d.strftime("%Y-%m") for d in tout.index], "unites": unites,
            "series": {c: [None if pd.isna(v) else round(float(v), 2) for v in tout[c]] for c in tout.columns}}
    chemin.write_text("window.METAUX = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")


def main():
    p, or_ = charger()
    r = rendements(p.join(or_, how="left"))
    fig_supercycle(p, RACINE / "figures/01_super_cycle.png")
    pic, creux, chute = fig_fer(p, RACINE / "figures/02_minerai_de_fer.png")
    vol = fig_volatilite(r, RACINE / "figures/03_volatilite.png")
    c = fig_correlations(r, RACINE / "figures/04_correlations.png")
    export_dashboard(p, or_, RACINE / "dashboard/donnees.js")
    f = p["Minerai de fer"]
    spot = f.loc["2010":]
    stats = {
        "fer_moy_2000": round(f.loc["2000"].mean(), 1), "fer_moy_2011": round(f.loc["2011"].mean(), 1),
        "fer_pic": (str(pic.date()), round(f[pic], 1)), "fer_creux": (str(creux.date()), round(f[creux], 1)),
        "fer_chute_pct": round(chute, 1),
        "fer_spot_2010_2017_P10_P50_P90": [round(spot.quantile(q), 1) for q in (.1, .5, .9)],
        "mois_sous_60_depuis_2014": int((f.loc["2014":] < 60).sum()), "mois_depuis_2014": int(len(f.loc["2014":])),
        "or_dernier": (str(or_.index[-1].date()), float(or_.iloc[-1])),
        "or_2017_06": float(or_.loc["2017-06-01"]),
    }
    for k, v in stats.items():
        print(k, v)
    print(vol.round(1))
    print(c.round(2).loc["Minerai de fer"])
    print("Cuivre x2000->2011", round(p.Cuivre.loc['2011'].mean() / p.Cuivre.loc['2000'].mean(), 1),
          "Fer", round(f.loc['2011'].mean() / f.loc['2000'].mean(), 1),
          "Nickel", round(p.Nickel.loc['2011'].mean() / p.Nickel.loc['2000'].mean(), 1),
          "Alu", round(p.Aluminium.loc['2011'].mean() / p.Aluminium.loc['2000'].mean(), 1))
    pd.Series(stats).to_json(RACINE / "resultats/chiffres_cles.json", force_ascii=False, indent=1)
    vol.round(1).to_csv(RACINE / "resultats/volatilite.csv")
    c.round(3).to_csv(RACINE / "resultats/correlations_2005_2017.csv")


if __name__ == "__main__":
    main()
