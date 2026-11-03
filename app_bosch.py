# -*- coding: utf-8 -*-
"""
Application interactive – Prédiction des pièces défectueuses (données Bosch)
8INF700 – Forage de données – UQAC – Diabate Vamoussa

Lancement :  streamlit run app_bosch.py
Les fichiers CSV exportés par les carnets doivent se trouver dans un dossier
« bosch_export » placé à côté de ce fichier.

Direction visuelle : style « Minimalism & Swiss » pour tableau de bord dense
(fond blanc, données en bleu #1E40AF, accent orange #D97706, alerte rouge #DC2626, police Fira Sans).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ---------------------------------------------------------------------------
# Jetons de design
# ---------------------------------------------------------------------------
# Thème clair : fond blanc, données en bleu, rouge réservé au risque
PRIMAIRE = "#1E40AF"      # bleu : données
SECONDAIRE = "#3B82F6"
ACCENT = "#D97706"        # orange : mise en évidence
ALERTE = "#DC2626"        # rouge : défaut / risque
SUCCES = "#15803D"
FOND = "#FFFFFF"
CARTE = "#FFFFFF"
TEXTE = "#0F172A"
TEXTE_DOUX = "#475569"
BORDURE = "#E2E8F0"
GRILLE = "#EEF2F7"
BLEU_PALE = "#BFD4F6"     # barres secondaires
COUL_LIGNES = {"L0": "#94A3B8", "L1": ACCENT, "L2": "#7C3AED", "L3": PRIMAIRE}
NOMS_FAMILLES = {0: "Ligne 0 – branche S12-S20", 1: "Lignes 1 et 2 (S24, S26)",
                 2: "Ligne 0 – variante A", 3: "Ligne 0 – variante B"}
SEUIL_DEFAUT = 0.69
TAUX_MOYEN = 100 * 6879 / 1183747

st.set_page_config(page_title="Bosch – Pièces défectueuses", page_icon=":material/precision_manufacturing:",
                   layout="wide", initial_sidebar_state="expanded")

# Thème Streamlit (curseurs, boutons) : écrit une fois à côté de l'application,
# pris en compte au prochain lancement.
_cfg = Path(__file__).resolve().parent / ".streamlit" / "config.toml"
_theme = (f'[theme]\nbase = "light"\nprimaryColor = "#1E40AF"\nbackgroundColor = "{FOND}"\n'
          f'secondaryBackgroundColor = "#F1F5F9"\ntextColor = "{TEXTE}"\nfont = "sans serif"\n')
try:
    if not _cfg.exists() or _cfg.read_text(encoding="utf-8") != _theme:
        _cfg.parent.mkdir(exist_ok=True)
        _cfg.write_text(_theme, encoding="utf-8")
except OSError:
    pass

# Graphiques : même style partout
pio.templates["bosch"] = go.layout.Template(layout=dict(
    font=dict(family="Fira Sans, Segoe UI, sans-serif", size=13, color=TEXTE),
    paper_bgcolor=CARTE, plot_bgcolor=CARTE, separators=", ",
    colorway=[PRIMAIRE, ACCENT, ALERTE, "#7C3AED", SECONDAIRE, SUCCES],
    xaxis=dict(gridcolor=GRILLE, zerolinecolor=BORDURE, linecolor=BORDURE, ticks="", title_font_color=TEXTE_DOUX),
    yaxis=dict(gridcolor=GRILLE, zerolinecolor=BORDURE, linecolor=BORDURE, ticks="", title_font_color=TEXTE_DOUX),
    hoverlabel=dict(bgcolor=CARTE, bordercolor=BORDURE, font=dict(family="Fira Sans, sans-serif", color=TEXTE)),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
    margin=dict(l=8, r=8, t=16, b=8),
))
pio.templates.default = "plotly_white+bosch"
CFG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@400;500;600;700&family=Fira+Code:wght@500;600&display=swap');
html, body, [class*="css"], .stMarkdown, .stText, p, label, button, input {{ font-family: 'Fira Sans', 'Segoe UI', sans-serif; }}
.stApp {{ background: {FOND}; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 3.6rem; padding-bottom: 3rem; max-width: 1400px; }}
h1, h2, h3 {{ font-family: 'Fira Sans', sans-serif; color: {TEXTE}; letter-spacing: -0.01em; }}
section[data-testid="stSidebar"] {{ background: #FFFFFF; border-right: 1px solid {BORDURE}; }}
div[data-testid="stVerticalBlockBorderWrapper"] {{ background: {CARTE}; border-radius: 10px; border-color: {BORDURE} !important; }}
.eyebrow {{ font-size: .78rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: {PRIMAIRE}; margin-bottom: .2rem; }}
.titre {{ font-size: 2rem; font-weight: 700; color: {TEXTE}; line-height: 1.15; margin: 0 0 .35rem 0; }}
.sous-titre {{ font-size: 1rem; color: {TEXTE_DOUX}; margin-bottom: 1.3rem; max-width: 880px; }}
.kpi {{ background: {CARTE}; border: 1px solid {BORDURE}; border-radius: 10px; padding: 14px 16px; height: 100%;
        border-top: 3px solid var(--c); }}
.kpi .lbl {{ font-size: .8rem; color: {TEXTE_DOUX}; font-weight: 500; text-transform: uppercase; letter-spacing: .04em; }}
.kpi .val {{ font-family: 'Fira Sans', sans-serif; font-size: 1.85rem; font-weight: 600; color: {TEXTE}; margin-top: 4px;
             font-variant-numeric: tabular-nums; }}
.kpi .sub {{ font-size: .82rem; color: {TEXTE_DOUX}; margin-top: 2px; }}
.section {{ font-size: 1.05rem; font-weight: 600; color: {TEXTE}; margin: .2rem 0 .1rem 0; }}
.note {{ font-size: .85rem; color: {TEXTE_DOUX}; }}
.badge {{ display: inline-block; padding: 4px 12px; border-radius: 999px; font-weight: 600; font-size: .95rem; }}
.badge.alerte {{ background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; }}
.badge.ok {{ background: #DCFCE7; color: #166534; border: 1px solid #BBF7D0; }}
.badge.neutre {{ background: #EFF6FF; color: {TEXTE}; border: 1px solid {BORDURE}; }}
.encadre {{ background: #EFF6FF; border-left: 4px solid {PRIMAIRE}; padding: 12px 16px; border-radius: 6px;
            color: {TEXTE}; font-size: .93rem; }}
.kpi {{ box-shadow: 0 1px 2px rgba(15,23,42,0.04); }}
div[data-testid="stSidebarNav"] a span {{ font-weight: 500; }}
button, a, [role="tab"], [data-baseweb="select"] {{ cursor: pointer; }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; animation: none !important; }} }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Composants
# ---------------------------------------------------------------------------
def entete(eyebrow, titre, sous_titre):
    st.markdown(f'<div class="eyebrow">{eyebrow}</div><div class="titre">{titre}</div>'
                f'<div class="sous-titre">{sous_titre}</div>', unsafe_allow_html=True)


def kpi(col, label, valeur, sous="", couleur=PRIMAIRE):
    col.markdown(f'<div class="kpi" style="--c:{couleur}"><div class="lbl">{label}</div>'
                 f'<div class="val">{valeur}</div><div class="sub">{sous}</div></div>', unsafe_allow_html=True)


def section(titre, note=None):
    st.markdown(f'<div class="section">{titre}</div>' + (f'<div class="note">{note}</div>' if note else ""),
                unsafe_allow_html=True)


def fr(x, d=0):
    return f"{x:,.{d}f}".replace(",", "\u202f").replace(".", ",")


def pct(x, d=1):
    return fr(x, d) + " %"


# ---------------------------------------------------------------------------
# Données
# ---------------------------------------------------------------------------
def dossier_donnees() -> Path:
    ici = Path(__file__).resolve().parent
    for d in (ici / "bosch_export", ici / "export", ici):
        if (d / "agregat_stations.csv").exists():
            return d
    st.error("Dossier de données introuvable. Placez le dossier **bosch_export** (avec les fichiers CSV) "
             "à côté du fichier app_bosch.py, puis relancez l'application.")
    st.stop()


DATA = dossier_donnees()


@st.cache_data(show_spinner="Chargement des données…")
def lire(nom):
    return pd.read_csv(DATA / nom)


def trouver(df, *candidats):
    bas = {c.lower(): c for c in df.columns}
    for c in candidats:
        if c.lower() in bas:
            return bas[c.lower()]
    return None


@st.cache_data(show_spinner="Chargement des prédictions…")
def predictions():
    df = lire("predictions_test.csv")
    c_y, c_p, c_id = trouver(df, "Response", "label"), trouver(df, "p", "proba", "probability", "score"), trouver(df, "Id")
    out = pd.DataFrame({"y": df[c_y].astype(int), "p": df[c_p].astype(float)})
    if c_id:
        out.insert(0, "Id", df[c_id].astype(int))
    return out


@st.cache_data(show_spinner="Chargement des pièces…")
def pieces():
    df = lire("kmeans_pieces.csv")
    out = pd.DataFrame({"groupe": df[trouver(df, "groupe", "prediction", "cluster")].astype(int)})
    if trouver(df, "Id"):
        out["Id"] = df[trouver(df, "Id")].astype(int)
    return out


def metriques(y, p, seuil):
    pred = p >= seuil
    vp = int(np.sum(pred & (y == 1))); fp = int(np.sum(pred & (y == 0)))
    fn = int(np.sum(~pred & (y == 1))); vn = int(np.sum(~pred & (y == 0)))
    prec = vp / (vp + fp) if vp + fp else 0.0
    rap = vp / (vp + fn) if vp + fn else 0.0
    den = np.sqrt(float(vp + fp) * (vp + fn) * (vn + fp) * (vn + fn))
    mcc = (float(vp) * vn - float(fp) * fn) / den if den else 0.0
    return dict(VP=vp, FP=fp, FN=fn, VN=vn, precision=prec, rappel=rap, mcc=mcc)


@st.cache_data
def courbe_seuils(y, p):
    return pd.DataFrame([dict(seuil=s, **metriques(y, p, s)) for s in np.round(np.arange(0.05, 0.96, 0.01), 2)])


if "seuil" not in st.session_state:
    st.session_state.seuil = SEUIL_DEFAUT


# ---------------------------------------------------------------------------
# Page 1 – Vue d'ensemble
# ---------------------------------------------------------------------------
def page_ensemble():
    entete("Vue d'ensemble", "La production en un coup d'œil",
           "Combien de pièces sont défectueuses, dans quelles familles de parcours, et à quels moments ?")
    fam = lire("kmeans_groupes.csv")
    fam["famille"] = fam["groupe"].map(NOMS_FAMILLES).fillna("Groupe " + fam["groupe"].astype(str))
    test = lire("resultats_test.csv").iloc[0]

    choix = st.multiselect("Familles de parcours (K-means)", fam["famille"].tolist(), default=fam["famille"].tolist())
    sel = fam[fam["famille"].isin(choix)]
    n, d = int(sel["pieces"].sum()), int(sel["defauts"].sum())
    taux = 100 * d / n if n else 0

    c = st.columns(4)
    kpi(c[0], "Pièces", fr(n), f"{len(sel)} famille(s) sur 4")
    kpi(c[1], "Pièces défectueuses", fr(d), f"environ 1 sur {fr(n / d) if d else '–'}", ALERTE)
    kpi(c[2], "Taux de défauts", pct(taux, 2), f"moyenne de l'usine : {pct(TAUX_MOYEN, 2)}", ACCENT)
    kpi(c[3], "MCC du modèle (test)", fr(test["mcc"], 3), f"précision {pct(100 * test['precision'], 0)} · "
                                                         f"rappel {pct(100 * test['rappel'], 1)}", SUCCES)
    st.write("")

    g1, g2 = st.columns([1, 1.45], gap="medium")
    with g1.container(border=True):
        section("Taux de défauts par famille", "La famille des lignes 1 et 2 dépasse nettement les autres.")
        s = sel.sort_values("taux_defaut_%")
        couleurs = [ALERTE if v == s["taux_defaut_%"].max() else BLEU_PALE for v in s["taux_defaut_%"]]
        fig = go.Figure(go.Bar(x=s["taux_defaut_%"], y=s["famille"], orientation="h", marker_color=couleurs,
                               text=s["taux_defaut_%"].map(lambda v: pct(v, 2)), textposition="outside",
                               customdata=s[["pieces", "defauts"]],
                               hovertemplate="%{y}<br>%{customdata[0]:,} pièces · %{customdata[1]:,} défauts<extra></extra>"))
        fig.update_layout(height=300, xaxis_title="Taux de défauts (%)", xaxis_range=[0, s["taux_defaut_%"].max() * 1.25])
        st.plotly_chart(fig, use_container_width=True, config=CFG)
        tab = sel[["famille", "pieces", "defauts", "stations_typiques"]].copy()
        tab["pieces"] = tab["pieces"].map(fr)
        tab["defauts"] = tab["defauts"].map(fr)
        st.dataframe(tab, hide_index=True, use_container_width=True,
                     column_config={"famille": "Famille", "pieces": "Pièces", "defauts": "Défauts",
                                    "stations_typiques": "Stations typiques"})
    with g2.container(border=True):
        section("Évolution du taux de défauts", "Les défauts arrivent par séries : certaines périodes dépassent 1,5 %.")
        mini = st.slider("Ignorer les périodes de moins de … pièces", 0, 2000, 500, 100)
        per = lire("agregat_periodes.csv")
        per = per[per["pieces"] >= mini]
        fig = go.Figure()
        fig.add_scatter(x=per["periode"], y=per["taux_%"], mode="lines", line=dict(color=PRIMAIRE, width=2),
                        fill="tozeroy", fillcolor="rgba(30,64,175,0.08)", name="Taux",
                        customdata=per[["pieces", "defauts"]],
                        hovertemplate="Période %{x}<br>Taux %{y:.2f} %<br>%{customdata[0]:,} pièces<extra></extra>")
        pics = per[per["taux_%"] >= 1.5]
        fig.add_scatter(x=pics["periode"], y=pics["taux_%"], mode="markers", name="Pic (≥ 1,5 %)",
                        marker=dict(color=ALERTE, size=8), hoverinfo="skip")
        fig.add_hline(y=TAUX_MOYEN, line_dash="dot", line_color=TEXTE_DOUX,
                      annotation_text=f"moyenne {pct(TAUX_MOYEN, 2)}", annotation_font_color=TEXTE_DOUX)
        fig.update_layout(height=420, xaxis_title="Période de production", yaxis_title="Taux de défauts (%)")
        st.plotly_chart(fig, use_container_width=True, config=CFG)


# ---------------------------------------------------------------------------
# Page 2 – Stations
# ---------------------------------------------------------------------------
def page_stations():
    entete("Stations", "Où les défauts se concentrent-ils ?",
           "Taux de défauts des pièces passées par chaque station, comparé à la moyenne de l'usine.")
    stn = lire("agregat_stations.csv")
    with st.container(border=True):
        c1, c2 = st.columns([1, 1])
        lignes = c1.multiselect("Lignes", sorted(stn["ligne"].unique()), default=sorted(stn["ligne"].unique()))
        mini = c2.slider("Ignorer les stations de moins de … pièces", 0, 50000, 1000, 1000)
        vue = stn[stn["ligne"].isin(lignes) & (stn["pieces"] >= mini)].copy()
        vue["num"] = vue["station"].str[1:].astype(int)
        vue = vue.sort_values("num")
        fig = px.bar(vue, x="station", y="taux_%", color="ligne", color_discrete_map=COUL_LIGNES,
                     custom_data=["pieces", "defauts"])
        fig.update_traces(hovertemplate="%{x}<br>Taux %{y:.2f} %<br>%{customdata[0]:,} pièces · "
                                        "%{customdata[1]:,} défauts<extra></extra>")
        fig.add_hline(y=TAUX_MOYEN, line_dash="dot", line_color=ALERTE,
                      annotation_text=f"moyenne {pct(TAUX_MOYEN, 2)}", annotation_font_color=ALERTE)
        fig.update_layout(height=400, xaxis_title="", yaxis_title="Taux de défauts (%)", bargap=0.25,
                          xaxis_tickangle=-90, legend_title_text="")
        st.plotly_chart(fig, use_container_width=True, config=CFG)
        st.markdown('<div class="note">Couleur = ligne de production. S32 (ligne 3) est près de 8 fois au-dessus '
                    'de la moyenne.</div>', unsafe_allow_html=True)

    st.write("")
    with st.container(border=True):
        section("Détail d'une station")
        options = vue["station"].tolist()
        s = st.selectbox("Station", options, index=options.index("S32") if "S32" in options else 0,
                         label_visibility="collapsed")
        r = stn[stn["station"] == s].iloc[0]
        ratio = r["taux_%"] / TAUX_MOYEN
        c = st.columns(4)
        kpi(c[0], "Ligne", r["ligne"])
        kpi(c[1], "Pièces passées", fr(r["pieces"]), f"{fr(r['defauts'])} défectueuses")
        kpi(c[2], "Taux de défauts", pct(r["taux_%"], 2), f"moyenne : {pct(TAUX_MOYEN, 2)}",
            ALERTE if ratio >= 1.5 else PRIMAIRE)
        kpi(c[3], "Par rapport à la moyenne", f"× {fr(ratio, 1)}",
            "nettement plus risquée" if ratio >= 1.5 else ("dans la moyenne" if ratio >= 0.8 else "moins risquée"),
            ALERTE if ratio >= 1.5 else (SUCCES if ratio < 0.8 else PRIMAIRE))
        imp = lire("importance_variables.csv")
        imp_s = imp[imp["station"] == s]
        st.write("")
        st.markdown('<div class="note">' + (
            f"Dans le modèle GBT, les {len(imp_s)} variables de {s} représentent "
            f"{pct(100 * imp_s['importance'].sum(), 1)} de l'importance totale." if len(imp_s) else
            f"Aucune variable de {s} ne fait partie des 150 variables retenues par le modèle.") + "</div>",
            unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page 3 – Parcours à risque
# ---------------------------------------------------------------------------
def page_parcours():
    entete("Parcours à risque", "Quelles combinaisons de stations surveiller ?",
           "Règles d'association (FP-Growth) et importance des variables dans le modèle GBT.")
    tab1, tab2 = st.tabs(["Combinaisons de stations (FP-Growth)", "Importance dans le modèle (GBT)"])

    with tab1:
        r = lire("regles_fpgrowth.csv")
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1, 1.2, 1, 1])
            tailles = c1.multiselect("Nombre de stations", sorted(r["taille"].unique()),
                                     default=sorted(r["taille"].unique()))
            lift_min = c2.slider("Lift minimum", 0.0, float(np.ceil(r["lift"].max())), 2.0, 0.5,
                                 help="Combien de fois le taux de défauts dépasse la moyenne de l'usine.")
            pieces_min = c3.number_input("Pièces minimum", 0, 1_000_000, 1000, 500)
            inclure = c4.text_input("Contient la station", "", placeholder="ex. S32").strip().upper()
        v = r[r["taille"].isin(tailles) & (r["lift"] >= lift_min) & (r["pieces"] >= pieces_min)]
        if inclure:
            v = v[v["combinaison"].str.split(" + ", regex=False).apply(lambda l: inclure in l)]
        v = v.sort_values("lift", ascending=False)

        st.write("")
        g1, g2 = st.columns([1.3, 1], gap="medium")
        with g1.container(border=True):
            section(f"Les combinaisons au lift le plus élevé", f"{fr(len(v))} combinaisons correspondent aux filtres.")
            top = v.head(12).iloc[::-1]
            if len(top):
                fig = go.Figure(go.Bar(x=top["lift"], y=top["combinaison"], orientation="h",
                                       marker_color=[ALERTE if x >= 10 else (ACCENT if x >= 5 else BLEU_PALE)
                                                     for x in top["lift"]],
                                       text=top["taux_defaut_%"].map(lambda x: pct(x, 2)), textposition="outside",
                                       customdata=top[["pieces", "part_des_defauts_%"]],
                                       hovertemplate="%{y}<br>Lift %{x:.1f}<br>%{customdata[0]:,} pièces · "
                                                     "%{customdata[1]} % des défauts<extra></extra>"))
                fig.update_layout(height=max(320, 32 * len(top)), xaxis_title="Lift",
                                  xaxis_range=[0, top["lift"].max() * 1.2])
                st.plotly_chart(fig, use_container_width=True, config=CFG)
                st.markdown('<div class="note">Étiquette = taux de défauts. Rouge : lift ≥ 10 · ambre : lift ≥ 5.</div>',
                            unsafe_allow_html=True)
            else:
                st.info("Aucune combinaison ne correspond aux filtres.")
        with g2.container(border=True):
            section("Toutes les combinaisons filtrées")
            st.dataframe(v, hide_index=True, use_container_width=True, height=470,
                         column_config={
                             "combinaison": "Combinaison", "taille": st.column_config.NumberColumn("Stations", width="small"),
                             "part_des_defauts_%": st.column_config.NumberColumn("Part des défauts", format="%.1f %%"),
                             "pieces": st.column_config.NumberColumn("Pièces", format="%d"),
                             "taux_defaut_%": st.column_config.NumberColumn("Taux", format="%.2f %%"),
                             "lift": st.column_config.ProgressColumn("Lift", format="%.1f", min_value=0,
                                                                     max_value=float(r["lift"].max()))})

    with tab2:
        imp = lire("importance_variables.csv")
        g1, g2 = st.columns(2, gap="medium")
        with g1.container(border=True):
            section("Par famille de variables", "Les mesures brutes portent près des deux tiers de l'importance.")
            pf = imp.groupby("famille", as_index=False)["importance"].sum().sort_values("importance")
            fig = go.Figure(go.Bar(x=pf["importance"], y=pf["famille"], orientation="h", marker_color=PRIMAIRE,
                                   text=(100 * pf["importance"]).map(lambda x: pct(x, 1)), textposition="outside",
                                   hovertemplate="%{y} : %{x:.1%}<extra></extra>"))
            fig.update_layout(height=300, xaxis_tickformat=".0%", xaxis_range=[0, pf["importance"].max() * 1.25])
            st.plotly_chart(fig, use_container_width=True, config=CFG)
        with g2.container(border=True):
            section("Les 10 stations les plus importantes", "S24, S29, S30 et S33 dominent.")
            ps = (imp[imp["station"] != "Aucune"].groupby("station", as_index=False)["importance"].sum()
                  .sort_values("importance").tail(10))
            fig = go.Figure(go.Bar(x=ps["importance"], y=ps["station"], orientation="h",
                                   marker_color=[ALERTE if s in ("S24", "S32") else BLEU_PALE for s in ps["station"]],
                                   text=(100 * ps["importance"]).map(lambda x: pct(x, 1)), textposition="outside",
                                   hovertemplate="%{y} : %{x:.1%}<extra></extra>"))
            fig.update_layout(height=300, xaxis_tickformat=".0%", xaxis_range=[0, ps["importance"].max() * 1.25])
            st.plotly_chart(fig, use_container_width=True, config=CFG)
        with st.container(border=True):
            section("Variables les plus importantes")
            n = st.slider("Nombre de variables", 5, 50, 15)
            st.dataframe(imp.head(n), hide_index=True, use_container_width=True, column_config={
                "variable": "Variable", "famille": "Famille", "station": "Station",
                "importance": st.column_config.ProgressColumn("Importance", format="percent", min_value=0,
                                                              max_value=float(imp["importance"].max()))})


# ---------------------------------------------------------------------------
# Page 4 – Modèle et seuil
# ---------------------------------------------------------------------------
def page_modele():
    entete("Modèle et seuil", "Quel seuil d'alerte choisir ?",
           "Une pièce est signalée si sa probabilité de défaut atteint le seuil. Déplacez le curseur : "
           "toutes les mesures sont recalculées sur les 177\u202f318 pièces du jeu de test.")
    pr = predictions()
    y, p = pr["y"].to_numpy(), pr["p"].to_numpy()

    with st.container(border=True):
        def maj_seuil():
            st.session_state.seuil = st.session_state.curseur

        seuil = st.slider("Seuil d'alerte", 0.05, 0.95, float(st.session_state.seuil), 0.01, key="curseur",
                          on_change=maj_seuil)
        m = metriques(y, p, seuil)
        ref = metriques(y, p, SEUIL_DEFAUT)

        def delta(cle, d=3, facteur=1, unite=""):
            ecart = (m[cle] - ref[cle]) * facteur
            if abs(ecart) < 1e-9:
                return "identique au seuil 0,69"
            return f"{'+' if ecart > 0 else '−'}{fr(abs(ecart), d)}{unite} vs seuil 0,69"

        c = st.columns(5)
        kpi(c[0], "MCC", fr(m["mcc"], 3), delta("mcc"), PRIMAIRE)
        kpi(c[1], "Précision", pct(100 * m["precision"]), "part des alertes justifiées", SUCCES)
        kpi(c[2], "Rappel", pct(100 * m["rappel"]), "part des défauts détectés", ACCENT)
        kpi(c[3], "Défauts détectés", fr(m["VP"]), f"sur {fr(m['VP'] + m['FN'])} défauts", SUCCES)
        kpi(c[4], "Fausses alertes", fr(m["FP"]), "pièces conformes signalées", ALERTE)

    st.write("")
    g1, g2 = st.columns([1, 1.5], gap="medium")
    with g1.container(border=True):
        section("Matrice de confusion")
        z = np.array([[m["VN"], m["FP"]], [m["FN"], m["VP"]]])
        txt = [[f"<b>{fr(m['VN'])}</b><br>conformes bien classées", f"<b>{fr(m['FP'])}</b><br>fausses alertes"],
               [f"<b>{fr(m['FN'])}</b><br>défauts manqués", f"<b>{fr(m['VP'])}</b><br>défauts détectés"]]
        coul = [["#EFF6FF", "#FEE2E2"], ["#FEF3C7", "#DCFCE7"]]
        fig = go.Figure()
        for i in range(2):
            for j in range(2):
                fig.add_shape(type="rect", x0=j, x1=j + 1, y0=1 - i, y1=2 - i, fillcolor=coul[i][j],
                              line=dict(color=CARTE, width=4), layer="below")
                fig.add_annotation(x=j + 0.5, y=1.5 - i, text=txt[i][j], showarrow=False,
                                   font=dict(size=15, color=TEXTE))
        fig.update_xaxes(range=[0, 2], tickvals=[0.5, 1.5], ticktext=["Prédit conforme", "Prédit défectueux"],
                         showgrid=False, zeroline=False, side="top")
        fig.update_yaxes(range=[0, 2], tickvals=[1.5, 0.5], ticktext=["Réellement<br>conforme", "Réellement<br>défectueux"],
                         showgrid=False, zeroline=False)
        fig.update_layout(height=360)
        st.plotly_chart(fig, use_container_width=True, config=CFG)
    with g2.container(border=True):
        section("Effet du seuil sur les mesures", "Plus le seuil monte, plus les alertes sont fiables, mais plus "
                                                 "de défauts passent inaperçus.")
        cs = courbe_seuils(y, p)
        fig = go.Figure()
        fig.add_scatter(x=cs["seuil"], y=cs["mcc"], name="MCC", line=dict(color=PRIMAIRE, width=3))
        fig.add_scatter(x=cs["seuil"], y=cs["precision"], name="Précision", line=dict(color=SUCCES, width=2, dash="dash"))
        fig.add_scatter(x=cs["seuil"], y=cs["rappel"], name="Rappel", line=dict(color=ACCENT, width=2, dash="dot"))
        fig.add_vline(x=seuil, line_color=ALERTE, line_width=2)
        fig.add_annotation(x=seuil, y=1.02, yref="paper", text=f"seuil {fr(seuil, 2)}", showarrow=False,
                           font=dict(color=ALERTE), yanchor="bottom")
        fig.update_layout(height=360, xaxis_title="Seuil", yaxis_title="Valeur", hovermode="x unified",
                          yaxis_range=[0, 1])
        st.plotly_chart(fig, use_container_width=True, config=CFG)

    meilleur = cs.loc[cs["mcc"].idxmax()]
    st.markdown(f'<div class="encadre">Sur le jeu de test, le MCC est le plus élevé autour de '
                f'{fr(meilleur["seuil"], 2)} ({fr(meilleur["mcc"], 3)}). Le seuil retenu dans le rapport, '
                f'{fr(SEUIL_DEFAUT, 2)}, a été choisi sur le jeu de validation, sans regarder le jeu de test : '
                f"c'est ce qui rend l'évaluation honnête.</div>", unsafe_allow_html=True)
    st.write("")

    with st.expander("Comparaison des modèles et des réglages (jeu de validation)"):
        cc = {"modele": "Modèle", "seuil": "Seuil", "exactitude_%": "Exactitude (%)", "precision": "Précision",
              "rappel": "Rappel", "f1": "F1", "auc_pr": "AUC-PR", "temps_s": "Temps (s)", "pieces": "Pièces",
              "mcc": st.column_config.ProgressColumn("MCC", format="%.3f", min_value=0, max_value=0.35)}
        onglets = st.tabs(["Modèles", "Déséquilibre", "Quantité de données", "Hyperparamètres", "Test final"])
        for t, f in zip(onglets, ["resultats_modeles.csv", "resultats_desequilibre.csv", "resultats_fraction.csv",
                                  "resultats_grille.csv", "resultats_test.csv"]):
            t.dataframe(lire(f), hide_index=True, use_container_width=True, column_config=cc)
    with st.expander("Analyse des erreurs (seuil 0,69)"):
        st.dataframe(lire("analyse_erreurs.csv"), hide_index=True, use_container_width=True)
        st.caption("Les fausses alertes passent surtout par S32 (visite_S32_moy), comme les vrais défauts détectés.")


# ---------------------------------------------------------------------------
# Page 5 – Rechercher une pièce
# ---------------------------------------------------------------------------
def page_piece():
    entete("Rechercher une pièce", "Que dit le modèle pour une pièce précise ?",
           "Entrez le numéro d'une pièce du jeu de test pour voir sa probabilité de défaut et la décision du modèle.")
    pr = predictions()
    seuil = st.session_state.seuil
    if "Id" not in pr.columns:
        st.warning("Le fichier predictions_test.csv ne contient pas la colonne Id : la recherche est impossible.")
        return
    if "pid" not in st.session_state:
        st.session_state.pid = int(pr.sort_values("p", ascending=False)["Id"].iloc[0])

    def hasard():
        st.session_state.pid = int(pr["Id"].sample(1).iloc[0])

    g1, g2 = st.columns([1, 2], gap="medium")
    with g1.container(border=True):
        section("Choisir une pièce")
        pid = st.number_input("Numéro de la pièce (Id)", min_value=0, step=1, key="pid")
        st.button("Choisir une pièce au hasard", on_click=hasard, icon=":material/shuffle:", use_container_width=True)
        st.markdown(f'<div class="note">Seuil d\'alerte utilisé : <b>{fr(seuil, 2)}</b> '
                    f'(modifiable dans la page « Modèle et seuil »).</div>', unsafe_allow_html=True)
    ligne = pr[pr["Id"] == pid]
    with g2.container(border=True):
        if ligne.empty:
            st.warning(f"La pièce {pid} n'est pas dans le jeu de test.")
        else:
            r = ligne.iloc[0]
            alerte = r["p"] >= seuil
            ok = alerte == (r["y"] == 1)
            fam = ""
            try:
                pc = pieces()
                if "Id" in pc.columns:
                    g = pc.loc[pc["Id"] == pid, "groupe"]
                    if len(g):
                        fam = NOMS_FAMILLES.get(int(g.iloc[0]), str(g.iloc[0]))
            except Exception:
                pass
            a, b = st.columns([1, 1.1])
            with a:
                section(f"Pièce n° {pid}", f"Famille de parcours : {fam}" if fam else None)
                st.write("")
                st.markdown(
                    f'<div class="note">Décision du modèle</div>'
                    f'<span class="badge {"alerte" if alerte else "ok"}">{"Alerte : défaut probable" if alerte else "Conforme"}</span>'
                    f'<div class="note" style="margin-top:12px">Réalité</div>'
                    f'<span class="badge neutre">{"Défectueuse" if r["y"] == 1 else "Conforme"}</span>'
                    f'<div class="note" style="margin-top:12px">Verdict</div>'
                    f'<span class="badge {"ok" if ok else "alerte"}">{"Le modèle a raison" if ok else "Le modèle se trompe"}</span>',
                    unsafe_allow_html=True)
            with b:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=100 * r["p"], number={"suffix": " %", "font": {"size": 40, "color": TEXTE}},
                    title={"text": "Probabilité de défaut", "font": {"size": 14, "color": TEXTE_DOUX}},
                    gauge={"axis": {"range": [0, 100], "tickvals": [0, 25, 50, 75, 100]},
                           "bar": {"color": ALERTE if alerte else PRIMAIRE, "thickness": 0.35},
                           "steps": [{"range": [0, 100 * seuil], "color": "#EFF6FF"},
                                     {"range": [100 * seuil, 100], "color": "#FEE2E2"}],
                           "threshold": {"line": {"color": TEXTE, "width": 3}, "value": 100 * seuil}}))
                fig.update_layout(height=250, margin=dict(l=45, r=45, t=40, b=0))
                st.plotly_chart(fig, use_container_width=True, config=CFG)
                st.markdown(f'<div class="note" style="text-align:center">Zone rouge = au-dessus du seuil '
                            f'({fr(100 * seuil, 0)} %)</div>', unsafe_allow_html=True)

    st.write("")
    with st.container(border=True):
        section("Les pièces les plus à risque", "Classées par probabilité de défaut décroissante.")
        n = st.slider("Nombre de pièces", 10, 200, 20, 10)
        top = pr.sort_values("p", ascending=False).head(n).copy()
        top["Décision"] = np.where(top["p"] >= seuil, "Alerte", "Conforme")
        top["Réalité"] = np.where(top["y"] == 1, "Défectueuse", "Conforme")
        st.dataframe(top[["Id", "p", "Décision", "Réalité"]], hide_index=True, use_container_width=True,
                     column_config={"Id": st.column_config.NumberColumn("Id", format="%d"),
                                    "p": st.column_config.ProgressColumn("Probabilité de défaut", format="percent",
                                                                         min_value=0, max_value=1)})
        st.download_button("Télécharger cette liste (CSV)", top.to_csv(index=False).encode("utf-8"),
                           "pieces_a_risque.csv", "text/csv", icon=":material/download:")


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f'<div class="eyebrow" style="margin-top:4px">8INF700 · Forage de données</div>'
                f'<div style="font-size:1.25rem;font-weight:700;color:{TEXTE};line-height:1.2">Ligne de production Bosch</div>'
                f'<div class="note" style="margin-bottom:8px">Prédiction des pièces défectueuses</div>',
                unsafe_allow_html=True)

nav = st.navigation([
    st.Page(page_ensemble, title="Vue d'ensemble", icon=":material/dashboard:", url_path="ensemble", default=True),
    st.Page(page_stations, title="Stations", icon=":material/factory:", url_path="stations"),
    st.Page(page_parcours, title="Parcours à risque", icon=":material/route:", url_path="parcours"),
    st.Page(page_modele, title="Modèle et seuil", icon=":material/tune:", url_path="modele"),
    st.Page(page_piece, title="Rechercher une pièce", icon=":material/search:", url_path="piece"),
])

with st.sidebar:
    st.divider()
    st.markdown(f'<div class="kpi" style="--c:{ALERTE}"><div class="lbl">Seuil d\'alerte actuel</div>'
                f'<div class="val">{fr(st.session_state.seuil, 2)}</div>'
                f'<div class="sub">Réglable dans « Modèle et seuil ». Utilisé dans toutes les pages.</div></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="note" style="margin-top:14px">UQAC · Diabate Vamoussa · Automne 2026</div>',
                unsafe_allow_html=True)

nav.run()
