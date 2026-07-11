import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata
import numpy as np

# Connexion sécurisée à Supabase
conn = st.connection("supabase", type="sql")

# ---------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE
# ---------------------------------------------------------
st.set_page_config(
    page_title="Archives Parlementaires",
    page_icon="🏛️",
    layout="wide"
)

# ---------------------------------------------------------
# 2. THÈME VISUEL POLITIQUE / RÉPUBLIQUE FRANÇAISE
# ---------------------------------------------------------
BLEU_FR = "#001F5B"
ROUGE_FR = "#E63946"
BLANC_FR = "#F8F9FA"
OR_REP = "#C9A227"
GRIS_TEXTE = "#2B2B2B"

COULEURS_THEMES = {
    "migration": BLEU_FR,
    "etranger": OR_REP,
    "invasion": ROUGE_FR,
    "Migration": BLEU_FR,
    "Etranger": OR_REP,
    "Invasion": ROUGE_FR,
}

st.markdown("""
<style>
/* Cache la barre native Streamlit en haut */
header[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
.stDeployButton { display: none !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }

/* Fond général */
.stApp {
    background: linear-gradient(180deg, #F8F9FA 0%, #EEF1F5 100%);
    color: #2B2B2B;
}

/* Cache totalement la sidebar */
section[data-testid="stSidebar"] { display: none; }

/* Conteneur principal */
.block-container {
    padding-top: 1rem !important;
    padding-left: 3rem;
    padding-right: 3rem;
}

/* Bandeau drapeau */
.republic-header {
    background: linear-gradient(90deg, #001F5B 0%, #001F5B 33%, #FFFFFF 33%, #FFFFFF 66%, #E63946 66%, #E63946 100%);
    height: 9px;
    border-radius: 8px;
    margin-bottom: 22px;
}

/* Bloc titre */
.hero-block {
    background: white;
    border-left: 8px solid #001F5B;
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 22px;
    box-shadow: 0 3px 14px rgba(0,0,0,0.08);
}

.hero-subtitle { color: #555555; font-size: 16px; }

h1, h2, h3 { color: #001F5B; font-family: Georgia, serif; }

/* Zone des onglets */
div[data-baseweb="tab-list"] {
    background: transparent !important;
    gap: 10px;
    border-bottom: 2px solid #001F5B;
    margin-bottom: 24px;
}
button[data-baseweb="tab"] {
    background-color: #EEF1F5 !important;
    color: #001F5B !important;
    border: 1px solid #BFC7D5 !important;
    border-radius: 10px 10px 0 0 !important;
    padding: 12px 22px !important;
    font-weight: 700 !important;
    box-shadow: none !important;
}
button[data-baseweb="tab"] p { color: #001F5B !important; font-weight: 700 !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    background-color: #001F5B !important;
    color: white !important;
    border: 1px solid #001F5B !important;
    border-bottom: 4px solid #E63946 !important;
}
button[data-baseweb="tab"][aria-selected="true"] p { color: white !important; }
button[data-baseweb="tab"]:focus, button[data-baseweb="tab"]:active { outline: none !important; box-shadow: none !important; }
div[data-testid="metric-container"] {
    background-color: white; border-left: 6px solid #001F5B; padding: 18px; border-radius: 13px; box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}
hr { border: none; height: 2px; background: linear-gradient(90deg, #001F5B, #FFFFFF, #E63946); margin: 25px 0; }
[data-testid="stDataFrame"] { border-radius: 10px; border: 1px solid #D0D0D0; }
.stSelectbox, .stSlider { background-color: white; border-radius: 10px; padding: 8px; }
p, li, div { font-family: Arial, sans-serif; }
</style>
""", unsafe_allow_html=True)


def afficher_header(titre: str, sous_titre: str):
    st.markdown('<div class="republic-header"></div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="hero-block">
            <h1>{titre}</h1>
            <p class="hero-subtitle">{sous_titre}</p>
        </div>
        """, unsafe_allow_html=True
    )

def appliquer_theme_plotly(fig, titre=None):
    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=titre if titre else fig.layout.title.text,
            font=dict(size=20, color=BLEU_FR, family="Georgia"),
            x=0.02
        ),
        font=dict(color=GRIS_TEXTE, family="Arial"),
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=40, r=30, t=70, b=40),
        legend=dict(bgcolor="rgba(255,255,255,0.85)", bordercolor="#DDDDDD", borderwidth=1)
    )
    return fig

# ---------------------------------------------------------
# 3. CARTE : COORDONNÉES + NORMALISATION
# ---------------------------------------------------------
COORD_DEPARTEMENTS = {
    "Ain": {"lat": 46.2052, "lon": 5.2255}, "Aisne": {"lat": 49.5597, "lon": 3.6244}, "Allier": {"lat": 46.3400, "lon": 3.1600},
    "Alpes-de-Haute-Provence": {"lat": 44.0920, "lon": 6.2350}, "Hautes-Alpes": {"lat": 44.5586, "lon": 6.0778},
    "Alpes-Maritimes": {"lat": 43.7031, "lon": 7.2661}, "Ardèche": {"lat": 44.7353, "lon": 4.5999}, "Ardennes": {"lat": 49.7621, "lon": 4.6285},
    "Ariège": {"lat": 42.9639, "lon": 1.6052}, "Aube": {"lat": 48.2973, "lon": 4.0744}, "Aude": {"lat": 43.0541, "lon": 2.3491},
    "Aveyron": {"lat": 44.3500, "lon": 2.5750}, "Bouches-du-Rhône": {"lat": 43.5333, "lon": 5.4333}, "Calvados": {"lat": 49.1210, "lon": -0.3650},
    "Cantal": {"lat": 45.0492, "lon": 2.1567}, "Charente": {"lat": 45.6484, "lon": 0.1567}, "Charente-Maritime": {"lat": 45.7463, "lon": -0.6337},
    "Cher": {"lat": 47.0833, "lon": 2.4000}, "Corrèze": {"lat": 45.3720, "lon": 1.8730}, "Corse": {"lat": 42.0396, "lon": 9.0129},
    "Côte-d'Or": {"lat": 47.3167, "lon": 5.0167}, "Côtes-d'Armor": {"lat": 48.5142, "lon": -2.7658}, "Creuse": {"lat": 46.1700, "lon": 2.0200},
    "Dordogne": {"lat": 45.1840, "lon": 0.7210}, "Doubs": {"lat": 47.0667, "lon": 6.2333}, "Drôme": {"lat": 44.7500, "lon": 5.1167},
    "Eure": {"lat": 49.0920, "lon": 1.1520}, "Eure-et-Loir": {"lat": 48.4469, "lon": 1.4890}, "Finistère": {"lat": 48.3000, "lon": -4.0000},
    "Gard": {"lat": 43.9595, "lon": 4.2976}, "Haute-Garonne": {"lat": 43.6047, "lon": 1.4442}, "Gers": {"lat": 43.6460, "lon": 0.5867},
    "Gironde": {"lat": 44.8378, "lon": -0.5792}, "Hérault": {"lat": 43.6119, "lon": 3.8772}, "Ille-et-Vilaine": {"lat": 48.1147, "lon": -1.6794},
    "Indre": {"lat": 46.8114, "lon": 1.6868}, "Indre-et-Loire": {"lat": 47.3941, "lon": 0.6848}, "Isère": {"lat": 45.1667, "lon": 5.4167},
    "Jura": {"lat": 46.6750, "lon": 5.5500}, "Landes": {"lat": 43.8900, "lon": -0.5000}, "Loir-et-Cher": {"lat": 47.5861, "lon": 1.3359},
    "Loire": {"lat": 45.4397, "lon": 4.3872}, "Haute-Loire": {"lat": 45.0437, "lon": 3.8852}, "Loire-Atlantique": {"lat": 47.2184, "lon": -1.5536},
    "Loiret": {"lat": 47.9029, "lon": 1.9093}, "Lot": {"lat": 44.4475, "lon": 1.4419}, "Lot-et-Garonne": {"lat": 44.2031, "lon": 0.6164},
    "Lozère": {"lat": 44.5170, "lon": 3.5000}, "Maine-et-Loire": {"lat": 47.4784, "lon": -0.5632}, "Manche": {"lat": 49.1150, "lon": -1.0900},
    "Marne": {"lat": 48.9567, "lon": 4.3630}, "Haute-Marne": {"lat": 48.1110, "lon": 5.1390}, "Mayenne": {"lat": 48.3067, "lon": -0.6133},
    "Meurthe-et-Moselle": {"lat": 48.6921, "lon": 6.1844}, "Meuse": {"lat": 48.7720, "lon": 5.1610}, "Morbihan": {"lat": 47.6582, "lon": -2.7608},
    "Moselle": {"lat": 49.1191, "lon": 6.1727}, "Nièvre": {"lat": 46.9909, "lon": 3.1628}, "Nord": {"lat": 50.6292, "lon": 3.0573},
    "Oise": {"lat": 49.4300, "lon": 2.0800}, "Orne": {"lat": 48.4300, "lon": 0.0800}, "Paris": {"lat": 48.8566, "lon": 2.3522},
    "Pas-de-Calais": {"lat": 50.4801, "lon": 2.4412}, "Puy-de-Dôme": {"lat": 45.7719, "lon": 3.0870}, "Pyrénées-Atlantiques": {"lat": 43.2951, "lon": -0.3708},
    "Hautes-Pyrénées": {"lat": 43.2329, "lon": 0.0781}, "Pyrénées-Orientales": {"lat": 42.6886, "lon": 2.8948}, "Bas-Rhin": {"lat": 48.5734, "lon": 7.7521},
    "Haut-Rhin": {"lat": 47.7508, "lon": 7.3359}, "Rhône": {"lat": 45.7500, "lon": 4.8500}, "Haute-Saône": {"lat": 47.6220, "lon": 6.1550},
    "Saône-et-Loire": {"lat": 46.6550, "lon": 4.5580}, "Sarthe": {"lat": 48.0061, "lon": 0.1996}, "Savoie": {"lat": 45.5646, "lon": 5.9178},
    "Haute-Savoie": {"lat": 45.8992, "lon": 6.1294}, "Seine-Maritime": {"lat": 49.4431, "lon": 1.0993}, "Seine-et-Marne": {"lat": 48.5400, "lon": 2.6600},
    "Deux-Sèvres": {"lat": 46.3237, "lon": -0.4648}, "Somme": {"lat": 49.8941, "lon": 2.2958}, "Tarn": {"lat": 43.9264, "lon": 2.1480},
    "Tarn-et-Garonne": {"lat": 44.0176, "lon": 1.3550}, "Var": {"lat": 43.5000, "lon": 6.2000}, "Vaucluse": {"lat": 43.9493, "lon": 4.8055},
    "Vendée": {"lat": 46.6700, "lon": -1.4300}, "Vienne": {"lat": 46.5802, "lon": 0.3404}, "Haute-Vienne": {"lat": 45.8354, "lon": 1.2620},
    "Vosges": {"lat": 48.1734, "lon": 6.4500}, "Yonne": {"lat": 47.7982, "lon": 3.5738},
    "Seine": {"lat": 48.8566, "lon": 2.3522}, "Seine-et-Oise": {"lat": 48.8014, "lon": 2.1301}, "Seine-Inférieure": {"lat": 49.4431, "lon": 1.0993},
    "Loire-Inférieure": {"lat": 47.2184, "lon": -1.5536}, "Basses-Pyrénées": {"lat": 43.2951, "lon": -0.3708}, "Basses-Alpes": {"lat": 44.0920, "lon": 6.2350},
    "Côtes-du-Nord": {"lat": 48.5142, "lon": -2.7658}, "Charente-Inférieure": {"lat": 45.7463, "lon": -0.6337},
}

def normaliser_texte(s: str) -> str:
    if pd.isna(s): return ""
    s = str(s).strip().replace("’", "'").replace("`", "'")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = s.replace("œ", "oe").replace(" ", "-").replace("_", "-")
    while "--" in s: s = s.replace("--", "-")
    return s.strip("-")

ALIAS_DEPARTEMENTS = {normaliser_texte(k): k for k in COORD_DEPARTEMENTS.keys()}
ALIAS_DEPARTEMENTS.update({
    "seine-inferieure": "Seine-Inférieure", "seine-maritime": "Seine-Maritime", "loire-inferieure": "Loire-Inférieure",
    "loire-atlantique": "Loire-Atlantique", "basses-pyrenees": "Basses-Pyrénées", "pyrenees-atlantiques": "Pyrénées-Atlantiques",
    "basses-alpes": "Basses-Alpes", "alpes-basses": "Basses-Alpes", "alpes-de-haute-provence": "Alpes-de-Haute-Provence",
    "cotes-du-nord": "Côtes-du-Nord", "cotes-d-armor": "Côtes-d'Armor", "charente-inferieure": "Charente-Inférieure",
    "charente-maritime": "Charente-Maritime", "cote-d-or": "Côte-d'Or", "deux-sevres": "Deux-Sèvres", "puy-de-dome": "Puy-de-Dôme",
    "bouches-du-rhone": "Bouches-du-Rhône", "rhone": "Rhône", "herault": "Hérault", "ardeche": "Ardèche", "correze": "Corrèze",
    "drome": "Drôme", "nievre": "Nièvre", "vendee": "Vendée", "finistere": "Finistère", "isere": "Isère", "ariege": "Ariège",
})

def trouver_coord_departement(dept_raw: str):
    key = normaliser_texte(dept_raw)
    nom_canonique = ALIAS_DEPARTEMENTS.get(key)
    if not nom_canonique: return None
    coord = COORD_DEPARTEMENTS[nom_canonique]
    return nom_canonique, coord["lat"], coord["lon"]


# ---------------------------------------------------------
# 4. LE CŒUR DU RÉACTEUR : L'ASPIRATION NATIVE (SANS CRASH)
# ---------------------------------------------------------
# ---------------------------------------------------------
# 4. LE CŒUR DU RÉACTEUR : L'ASPIRATION NATIVE ET FILTRÉE
# ---------------------------------------------------------
@st.cache_data(ttl="1h") 
def load_all_data():
    # 1. On aspire les données brutes SANS LA LIMITE QUI COUPAIT L'HISTOIRE !
    df_f = conn.query("SELECT * FROM faits_occurrences;", ttl="10m")
    df_o = conn.query("SELECT * FROM dim_orateurs;", ttl="10m")
    df_m = conn.query("SELECT * FROM dim_mandats;", ttl="10m")
    df_t = conn.query("SELECT * FROM dim_temps;", ttl="10m")
    df_th = conn.query("SELECT * FROM dim_theme;", ttl="10m")

    # Fonction de sécurité pour ne jamais crasher
    def get_col(df, candidats):
        for c in candidats:
            if c in df.columns: return c
        return None

    # =================================================================
    # 🛡️ RESTAURATION DES FILTRES IA (Pour nettoyer les graphiques !)
    # =================================================================
    c_statut = get_col(df_f, ["ia_filtre_statut", "filtre_statut", "statut"])
    if c_statut:
        df_f = df_f[df_f[c_statut].fillna('retenu').astype(str).str.lower() == 'retenu']
        
    c_clu = get_col(df_f, ["cluster_id", "ia_cluster_id"])
    if c_clu:
        df_f = df_f[pd.to_numeric(df_f[c_clu], errors='coerce').fillna(0) != -1]
        
    c_rhet = get_col(df_f, ["est_rhetorique_migratoire", "est_rhétorique_migratoire"])
    if c_rhet:
        df_f = df_f[df_f[c_rhet].astype(str).str.lower().isin(['true', '1', 'oui', '1.0', 't'])]
    # =================================================================

    # --- IDENTIFICATION DES CLÉS ---
    c_f_orateur = get_col(df_f, ["id_orateur", "acteur_id"])
    c_f_mandat  = get_col(df_f, ["id_mandat", "mandat_id"])
    c_f_date    = get_col(df_f, ["id_date", "date_id"])
    c_f_theme   = get_col(df_f, ["id_theme", "theme_id"])

    c_o_id = get_col(df_o, ["id_orateur", "id_acteur"])
    c_m_id = get_col(df_m, ["id_mandat", "mandat_id"])
    c_t_id = get_col(df_t, ["id_date", "date_id"])
    c_th_id = get_col(df_th, ["id_theme", "theme_id"])

    # --- JOINTURES ROBUSTES EN PANDAS ---
    df_merged = df_f.copy()

    if c_f_orateur and c_o_id:
        df_merged[c_f_orateur] = df_merged[c_f_orateur].astype(str).str.replace(r'\D', '', regex=True)
        df_o_sub = df_o.copy()
        df_o_sub[c_o_id] = df_o_sub[c_o_id].astype(str).str.replace(r'\D', '', regex=True)
        cols_o = [c for c in [c_o_id, get_col(df_o, ["nom_orateur", "nom"]), get_col(df_o, ["date_naissance"]), get_col(df_o, ["date_deces"])] if c]
        if c_f_orateur == c_o_id:
            df_merged = df_merged.merge(df_o_sub[cols_o], on=c_f_orateur, how="left")
        else:
            df_merged = df_merged.merge(df_o_sub[cols_o], left_on=c_f_orateur, right_on=c_o_id, how="left")

    if c_f_mandat and c_m_id:
        cols_m = [c for c in [c_m_id, get_col(df_m, ["grp_politique", "groupe_politique"]), get_col(df_m, ["famille_politique"]), get_col(df_m, ["departement", "dpt"])] if c]
        if c_f_mandat == c_m_id:
            df_merged = df_merged.merge(df_m[cols_m], on=c_f_mandat, how="left")
        else:
            df_merged = df_merged.merge(df_m[cols_m], left_on=c_f_mandat, right_on=c_m_id, how="left")

    if c_f_date and c_t_id:
        cols_t = [c for c in [c_t_id, get_col(df_t, ["annee", "année"]), get_col(df_t, ["date_seance", "date"])] if c]
        if c_f_date == c_t_id:
            df_merged = df_merged.merge(df_t[cols_t], on=c_f_date, how="left")
        else:
            df_merged = df_merged.merge(df_t[cols_t], left_on=c_f_date, right_on=c_t_id, how="left")

    if c_f_theme and c_th_id:
        cols_th = [c for c in [c_th_id, get_col(df_th, ["libelle_theme", "theme"])] if c]
        if c_f_theme == c_th_id:
            df_merged = df_merged.merge(df_th[cols_th], on=c_f_theme, how="left")
        else:
            df_merged = df_merged.merge(df_th[cols_th], left_on=c_f_theme, right_on=c_th_id, how="left")

    # --- CONSTITUTION DU DF FINAL ---
    df_final = pd.DataFrame()

    c_occ = get_col(df_merged, ["id_occurrence", "id_occurence"])
    c_lem = get_col(df_merged, ["lemme_detecte", "lemme", "mot_cle"])
    c_ctx = get_col(df_merged, ["contexte", "context"])
    c_sco = get_col(df_merged, ["score_ia", "score_pertinence"])
    c_clu = get_col(df_merged, ["cluster_id", "ia_cluster_id"])
    c_nom = get_col(df_merged, ["nom_orateur", "nom"])
    c_nai = get_col(df_merged, ["date_naissance"])
    c_dec = get_col(df_merged, ["date_deces"])
    c_grp = get_col(df_merged, ["grp_politique", "groupe_politique"])
    c_fam = get_col(df_merged, ["famille_politique"])
    c_dep = get_col(df_merged, ["departement", "dpt"])
    c_ann = get_col(df_merged, ["annee", "année"])
    c_dat = get_col(df_merged, ["date_seance", "date"])
    c_lib = get_col(df_merged, ["libelle_theme", "theme"])

    df_final["id_occurrence"] = df_merged[c_occ] if c_occ else df_merged.index
    df_final["lemme_detecte"] = df_merged[c_lem] if c_lem else "Inconnu"
    df_final["contexte"] = df_merged[c_ctx] if c_ctx else ""
    df_final["score_ia"] = pd.to_numeric(df_merged[c_sco] if c_sco else 0, errors="coerce").fillna(0)
    df_final["cluster_id"] = df_merged[c_clu] if c_clu else 0
    df_final["id_orateur"] = df_merged[c_f_orateur] if c_f_orateur else "Inconnu"
    df_final["nom_orateur"] = df_merged[c_nom] if c_nom else "Inconnu"
    df_final["date_naissance"] = df_merged[c_nai] if c_nai else np.nan
    df_final["date_deces"] = df_merged[c_dec] if c_dec else np.nan
    df_final["grp_politique"] = df_merged[c_grp] if c_grp else "Non renseigné"
    df_final["famille_politique"] = df_merged[c_fam] if c_fam else "Non renseignée / Autres"
    df_final["departement"] = df_merged[c_dep] if c_dep else "Inconnu"

    if c_ann:
        df_final["annee"] = pd.to_numeric(df_merged[c_ann], errors="coerce")
    elif c_dat:
        df_final["annee"] = pd.to_datetime(df_merged[c_dat], errors="coerce").dt.year
    else:
        df_final["annee"] = 2000
    df_final["date_seance"] = df_merged[c_dat] if c_dat else np.nan

    df_final["libelle_theme"] = df_merged[c_lib] if c_lib else "Non renseigné"
    df_final["theme"] = df_final["libelle_theme"]

    df_final["grp_politique"] = df_final["grp_politique"].fillna("Non renseigné")
    df_final["famille_politique"] = df_final["famille_politique"].replace(["Non renseignée / Autres", "Non renseigné", "NULL", "", None], np.nan)
    df_final["famille_politique"] = df_final["famille_politique"].fillna("Non renseignée / Autres")
    df_final["nom_orateur"] = df_final["nom_orateur"].fillna("Inconnu")
    df_final["departement"] = df_final["departement"].fillna("Inconnu")
    df_final["libelle_theme"] = df_final["libelle_theme"].fillna("Non renseigné")

    df_mandats_out = df_m.copy()
    c_m_orateur = get_col(df_mandats_out, ["id_orateur", "id_acteur"])
    if c_m_orateur and c_m_orateur != "id_orateur":
        df_mandats_out = df_mandats_out.rename(columns={c_m_orateur: "id_orateur"})
    c_m_dep = get_col(df_mandats_out, ["departement", "dpt"])
    if c_m_dep and c_m_dep != "departement":
        df_mandats_out = df_mandats_out.rename(columns={c_m_dep: "departement"})

    return df_final, df_mandats_out

# ---------------------------------------------------------
# CHARGEMENT ET CORRECTION DES FAMILLES POLITIQUES
# ---------------------------------------------------------
df_faits, df_mandats_complet = load_all_data()

df_faits["famille_politique"] = df_faits["famille_politique"].replace({
    "Centre Gauche": "Centre gauche",
    "Centre Droite": "Centre droit",
    "Extrême Gauche": "Extrême gauche",
    "Extrême Droite": "Extrême droite",
    "Non Inscrits": "Non inscrits"
})


# ---------------------------------------------------------
# 5. NAVIGATION PAR ONGLETS EN HAUT
# ---------------------------------------------------------
tab_dashboard, tab_deputes = st.tabs([
    "📊 Dashboard Global",
    "👤 Annuaire des Députés"
])

# =========================================================================================
# PAGE 1 : DASHBOARD GLOBAL
# =========================================================================================
with tab_dashboard:
    afficher_header(
        "Analyse Sémantique des Discours Parlementaires",
        "Archives parlementaires françaises — occurrences thématiques validées par l’IA"
    )

    if "date_seance" in df_faits.columns and not df_faits["date_seance"].isna().all():
        df_faits["annee"] = pd.to_datetime(df_faits["date_seance"], errors="coerce").dt.year
        df_faits = df_faits.dropna(subset=["annee"])
        df_faits["annee"] = df_faits["annee"].astype(int)

    # On filtre la Ve République
    df_valide = df_faits[(df_faits["annee"] >= 1958) & (df_faits["annee"] <= 2026)].copy()

    if not df_valide.empty:
        min_year = int(df_valide["annee"].min())
        max_year = int(df_valide["annee"].max())
    else:
        min_year, max_year = 1958, 2026

    col_time, _ = st.columns([1, 2])
    with col_time:
        annee_slider = st.slider("📅 Période historique", min_year, max_year, (min_year, max_year))

    df_page1 = df_valide[(df_valide["annee"] >= annee_slider[0]) & (df_valide["annee"] <= annee_slider[1])].copy()

    st.markdown("---")

    def nettoyer_et_classer_famille(groupe):
        if pd.isna(groupe): return "Autres / Non-inscrits"
        g = str(groupe).lower().strip()
        if g == "" or g == "none" or g == "null" or g == "inconnu": return "Autres / Non-inscrits"
        
        if any(mot in g for mot in ['soc', 'com', 'gauch', 'lfi', 'insoumis', 'écolo', 'ecolo', 'nupes', 'radic', 'pcf', 'ps']): return "Gauche"
        elif any(mot in g for mot in ['rpr', 'ump', 'lr', 'droit', 'répub', 'repub', 'udf', 'indépen', 'libéral', 'unr', 'udr']): return "Droite"
        elif any(mot in g for mot in ['centr', 'modem', 'udi', 'renaissance', 'marche', 'lrem', 'horizons', 'ensemble']): return "Centre"
        elif any(mot in g for mot in ['front nat', 'rassemblement nat', 'rn', 'fn', 'national', 'recouv']): return "Extrême Droite"
        else: return "Autres / Non-inscrits"

    col_groupe_source = None
    for col in ["famille_politique", "groupe_politique", "grp_politique"]:
        if col in df_page1.columns:
            col_groupe_source = col
            break

    if col_groupe_source:
        df_page1["famille_politique_calculee"] = df_page1[col_groupe_source].apply(nettoyer_et_classer_famille)
    else:
        df_page1["famille_politique_calculee"] = "Autres / Non-inscrits"

    g1, g2 = st.columns(2)

    with g1:
        st.subheader("📈 Évolution chronologique")
        col_theme_faits = "theme" if "theme" in df_page1.columns else "libelle_theme"

        if col_theme_faits in df_page1.columns:
            df_trend = df_page1.groupby(["annee", col_theme_faits]).size().reset_index(name="Nombre")
            df_trend[col_theme_faits] = df_trend[col_theme_faits].replace({"migration": "Migration", "etranger": "Étranger", "invasion": "Invasion"})

            if not df_trend.empty:
                fig_line = px.line(df_trend, x="annee", y="Nombre", color=col_theme_faits, markers=True, color_discrete_map=COULEURS_THEMES)
                fig_line = appliquer_theme_plotly(fig_line, "Évolution chronologique des occurrences")
                fig_line.update_xaxes(title="Année")
                fig_line.update_yaxes(title="Nombre d’occurrences")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.warning("Aucune donnée disponible pour cette période.")
        else:
            st.error("Colonne thématique introuvable dans les données.")

    with g2:
        st.subheader("📊 Volume total par grande famille")
        couleurs_completes = {
            "Extrême gauche": "#780000", "Gauche": "#c1121f", "Centre gauche": "#f4a261", "Centre": "#ffb703",
            "Centre droit": "#fb8500", "Droite": "#00509d", "Extrême droite": "#001a2c", "Non inscrits": "#6c757d", "Non renseignée / Autres": "#adb5bd"
        }

        df_bar = df_page1.groupby("famille_politique").size().reset_index(name="Volume total").sort_values(by="Volume total", ascending=False) 

        fig_bar = px.bar(
            df_bar, x="Volume total", y="famille_politique", color="famille_politique", color_discrete_map=couleurs_completes,
            orientation="h", template="plotly_white", text="Volume total", labels={"famille_politique": "Courant Politique", "Volume total": "Phrases extraites"}
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

# =========================================================================================
# PAGE 2 : ANNUAIRE DES DÉPUTÉS
# =========================================================================================
with tab_deputes:
    afficher_header("🏛️ Fiche Parlementaire", "Profil biographique et mandats parlementaires")

    df_annuaire = df_faits[df_faits["famille_politique"] != "Non renseignée / Autres"]

    col_search1, col_search2 = st.columns(2)

    with col_search1:
        familles_dispo_p2 = ["Toutes"] + sorted(df_annuaire["famille_politique"].dropna().unique().tolist())
        choix_famille = st.selectbox("1. Sélectionner la famille politique", options=familles_dispo_p2)

    if choix_famille != "Toutes":
        df_deputes_dispo = df_annuaire[df_annuaire["famille_politique"] == choix_famille]
    else:
        df_deputes_dispo = df_annuaire

    list_deputes = sorted(df_deputes_dispo["nom_orateur"].dropna().unique().tolist())

    if not list_deputes:
        st.warning("Aucun orateur disponible avec ce filtre.")
        st.stop()

    with col_search2:
        choix_depute = st.selectbox("2. Sélectionner l’orateur", options=list_deputes)

    df_depute_profile = df_annuaire[df_annuaire["nom_orateur"] == choix_depute]

    if not df_depute_profile.empty:
        info = df_depute_profile.iloc[0]

        id_sycomore = info["id_orateur"] if "id_orateur" in info and pd.notnull(info["id_orateur"]) else "Inconnu"
        date_n = info["date_naissance"] if "date_naissance" in info and pd.notnull(info["date_naissance"]) else "Inconnue"
        date_d = info["date_deces"] if "date_deces" in info and pd.notnull(info["date_deces"]) else "Vivante / Non renseignée"

        st.markdown(f"## 🏛️ {choix_depute}")
        st.markdown("### 📋 Données personnelles")

        col_bio1, col_meta_an = st.columns([2, 1])
        with col_bio1:
            st.markdown(f"""
            - **Identifiant Sycomore :** `{id_sycomore}`
            - **Date de naissance :** `{date_n}`
            - **Date de décès :** `{date_d}`
            """)

        with col_meta_an:
            if str(id_sycomore) != "Inconnu":
                id_propre = str(id_sycomore).replace("PA", "")
                st.link_button("🌐 Ouvrir la fiche Sycomore", f"https://www2.assemblee-nationale.fr/sycomore/fiche?num_dept={id_propre}", use_container_width=True)

        st.markdown("#### 📂 Historique des mandats scrapés")

        df_ses_mandats = df_mandats_complet[df_mandats_complet["id_orateur"] == id_sycomore].drop_duplicates()
        st.dataframe(df_ses_mandats, use_container_width=True, hide_index=True)

        st.markdown("---")

        col_map, col_radar = st.columns(2)

        with col_map:
            st.markdown("### 🗺️ Implantation parlementaire")
            map_rows, depts_non_localises = [], []

            if not df_ses_mandats.empty:
                for dept_raw, sous_df in df_ses_mandats.groupby("departement", dropna=True):
                    found = trouver_coord_departement(dept_raw)
                    if found:
                        nom_canonique, lat, lon = found
                        map_rows.append({"Département": nom_canonique, "lat": lat, "lon": lon, "Nombre de mandats": len(sous_df)})
                    else:
                        d_clean = str(dept_raw).strip()
                        if d_clean and d_clean.lower() != "inconnu": depts_non_localises.append(d_clean)

            if map_rows:
                df_map = pd.DataFrame(map_rows)
                fig_map = px.scatter_mapbox(
                    df_map, lat="lat", lon="lon", hover_name="Département", hover_data={"Nombre de mandats": True, "lat": False, "lon": False},
                    size="Nombre de mandats", size_max=22, zoom=4.2, center={"lat": 46.6, "lon": 2.2}, height=450,
                    mapbox_style="open-street-map", color_discrete_sequence=[BLEU_FR]
                )
                fig_map.update_traces(hovertemplate="<b>%{hovertext}</b><br>Nombre de mandats : %{customdata[0]}<extra></extra>", marker=dict(opacity=0.88))
                fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, paper_bgcolor="white")
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.info("Aucun département localisable pour cet orateur.")
            
            if depts_non_localises: st.warning("Départements non localisés : " + ", ".join(sorted(set(depts_non_localises))))

        with col_radar:
            st.markdown("### 🎯 Empreinte Thématique")
            col_theme = "theme" if "theme" in df_depute_profile.columns else ("libelle_theme" if "libelle_theme" in df_depute_profile.columns else None)

            if col_theme and not df_depute_profile[col_theme].dropna().empty:
                df_radar = df_depute_profile[col_theme].value_counts(normalize=True).reset_index()
                df_radar.columns = ["Thème", "Proportion"]
                df_radar["Proportion"] = df_radar["Proportion"] * 100 

                df_radar["Thème"] = df_radar["Thème"].astype(str).str.lower().str.strip()
                themes_ref = pd.DataFrame({"Thème": ["migration", "etranger", "invasion"]})
                df_radar = pd.merge(themes_ref, df_radar, on="Thème", how="left").fillna(0)

                df_radar["Thème"] = df_radar["Thème"].replace({"migration": "Migration", "etranger": "Étranger", "invasion": "Invasion"})

                fig_radar = px.line_polar(df_radar, r="Proportion", theta="Thème", line_close=True, color_discrete_sequence=[BLEU_FR], height=420)
                fig_radar.update_traces(fill='toself', opacity=0.7)
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%")),
                    margin=dict(l=40, r=40, t=30, b=20), showlegend=False
                )
                st.plotly_chart(fig_radar, use_container_width=True)
                
                if df_radar['Proportion'].max() > 0:
                    theme_dominant = df_radar.loc[df_radar['Proportion'].idxmax()]
                    st.info(f"💡 Thème majoritaire : **{theme_dominant['Thème']}** ({theme_dominant['Proportion']:.1f}% des mentions).")
            else:
                st.warning("Données thématiques indisponibles pour cet orateur.")
    else:
        st.warning("Aucune donnée disponible pour cet orateur.")
