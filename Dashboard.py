import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import unicodedata
import numpy as np

duckdb.sql("PRAGMA threads=2;")
duckdb.sql("PRAGMA memory_limit='500MB';")
duckdb.sql("PRAGMA temp_directory='duckdb_swap_space';")
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

couleurs_politiques = {
    "Extrême gauche": "#780000",   # Rouge très foncé
    "Gauche": "#c1121f",           # Rouge classique
    "Centre gauche": "#f4a261",    # Orange clair
    "Centre": "#ffb703",           # Jaune/Orange
    "Centre droit": "#fb8500",     # Orange foncé
    "Droite": "#00509d",           # Bleu classique
    "Extrême droite": "#001a2c",   # Bleu très sombre / Noir
    "Non renseignée / Autres": "#8d99ae" # Gris neutre
}
st.markdown("""
<style>

/* Cache la barre native Streamlit en haut : Deploy + menu */
header[data-testid="stHeader"] {
    display: none !important;
}

[data-testid="stToolbar"] {
    display: none !important;
}

.stDeployButton {
    display: none !important;
}

#MainMenu {
    visibility: hidden !important;
}

footer {
    visibility: hidden !important;
}

/* Fond général */
.stApp {
    background: linear-gradient(180deg, #F8F9FA 0%, #EEF1F5 100%);
    color: #2B2B2B;
}

/* Cache totalement la sidebar */
section[data-testid="stSidebar"] {
    display: none;
}

/* Conteneur principal */
.block-container {
    padding-top: 1rem !important;
    padding-left: 3rem;
    padding-right: 3rem;
}

/* Bandeau drapeau */
.republic-header {
    background: linear-gradient(
        90deg,
        #001F5B 0%, #001F5B 33%,
        #FFFFFF 33%, #FFFFFF 66%,
        #E63946 66%, #E63946 100%
    );
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

.hero-subtitle {
    color: #555555;
    font-size: 16px;
}

/* Titres */
h1, h2, h3 {
    color: #001F5B;
    font-family: Georgia, serif;
}

/* Zone des onglets */
div[data-baseweb="tab-list"] {
    background: transparent !important;
    gap: 10px;
    border-bottom: 2px solid #001F5B;
    margin-bottom: 24px;
}

/* Onglets non actifs */
button[data-baseweb="tab"] {
    background-color: #EEF1F5 !important;
    color: #001F5B !important;
    border: 1px solid #BFC7D5 !important;
    border-radius: 10px 10px 0 0 !important;
    padding: 12px 22px !important;
    font-weight: 700 !important;
    box-shadow: none !important;
}

/* Texte des onglets */
button[data-baseweb="tab"] p {
    color: #001F5B !important;
    font-weight: 700 !important;
}

/* Onglet actif */
button[data-baseweb="tab"][aria-selected="true"] {
    background-color: #001F5B !important;
    color: white !important;
    border: 1px solid #001F5B !important;
    border-bottom: 4px solid #E63946 !important;
}

/* Texte onglet actif */
button[data-baseweb="tab"][aria-selected="true"] p {
    color: white !important;
}

/* Supprime le cadre/halo blanc bizarre */
button[data-baseweb="tab"]:focus,
button[data-baseweb="tab"]:active {
    outline: none !important;
    box-shadow: none !important;
}

/* Cartes KPI */
div[data-testid="metric-container"] {
    background-color: white;
    border-left: 6px solid #001F5B;
    padding: 18px;
    border-radius: 13px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}

/* Séparateurs */
hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, #001F5B, #FFFFFF, #E63946);
    margin: 25px 0;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    border: 1px solid #D0D0D0;
}

/* Selectbox / slider */
.stSelectbox, .stSlider {
    background-color: white;
    border-radius: 10px;
    padding: 8px;
}

/* Texte */
p, li, div {
    font-family: Arial, sans-serif;
}

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
        """,
        unsafe_allow_html=True
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
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=40, r=30, t=70, b=40),
        legend=dict(
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#DDDDDD",
            borderwidth=1
        )
    )
    return fig


# ---------------------------------------------------------
# 3. CARTE : COORDONNÉES + NORMALISATION DES DÉPARTEMENTS
# ---------------------------------------------------------
# Centre approximatif des départements. Suffisant pour afficher l'implantation.
COORD_DEPARTEMENTS = {
    "Ain": {"lat": 46.2052, "lon": 5.2255},
    "Aisne": {"lat": 49.5597, "lon": 3.6244},
    "Allier": {"lat": 46.3400, "lon": 3.1600},
    "Alpes-de-Haute-Provence": {"lat": 44.0920, "lon": 6.2350},
    "Hautes-Alpes": {"lat": 44.5586, "lon": 6.0778},
    "Alpes-Maritimes": {"lat": 43.7031, "lon": 7.2661},
    "Ardèche": {"lat": 44.7353, "lon": 4.5999},
    "Ardennes": {"lat": 49.7621, "lon": 4.6285},
    "Ariège": {"lat": 42.9639, "lon": 1.6052},
    "Aube": {"lat": 48.2973, "lon": 4.0744},
    "Aude": {"lat": 43.0541, "lon": 2.3491},
    "Aveyron": {"lat": 44.3500, "lon": 2.5750},
    "Bouches-du-Rhône": {"lat": 43.5333, "lon": 5.4333},
    "Calvados": {"lat": 49.1210, "lon": -0.3650},
    "Cantal": {"lat": 45.0492, "lon": 2.1567},
    "Charente": {"lat": 45.6484, "lon": 0.1567},
    "Charente-Maritime": {"lat": 45.7463, "lon": -0.6337},
    "Cher": {"lat": 47.0833, "lon": 2.4000},
    "Corrèze": {"lat": 45.3720, "lon": 1.8730},
    "Corse": {"lat": 42.0396, "lon": 9.0129},
    "Côte-d'Or": {"lat": 47.3167, "lon": 5.0167},
    "Côtes-d'Armor": {"lat": 48.5142, "lon": -2.7658},
    "Creuse": {"lat": 46.1700, "lon": 2.0200},
    "Dordogne": {"lat": 45.1840, "lon": 0.7210},
    "Doubs": {"lat": 47.0667, "lon": 6.2333},
    "Drôme": {"lat": 44.7500, "lon": 5.1167},
    "Eure": {"lat": 49.0920, "lon": 1.1520},
    "Eure-et-Loir": {"lat": 48.4469, "lon": 1.4890},
    "Finistère": {"lat": 48.3000, "lon": -4.0000},
    "Gard": {"lat": 43.9595, "lon": 4.2976},
    "Haute-Garonne": {"lat": 43.6047, "lon": 1.4442},
    "Gers": {"lat": 43.6460, "lon": 0.5867},
    "Gironde": {"lat": 44.8378, "lon": -0.5792},
    "Hérault": {"lat": 43.6119, "lon": 3.8772},
    "Ille-et-Vilaine": {"lat": 48.1147, "lon": -1.6794},
    "Indre": {"lat": 46.8114, "lon": 1.6868},
    "Indre-et-Loire": {"lat": 47.3941, "lon": 0.6848},
    "Isère": {"lat": 45.1667, "lon": 5.4167},
    "Jura": {"lat": 46.6750, "lon": 5.5500},
    "Landes": {"lat": 43.8900, "lon": -0.5000},
    "Loir-et-Cher": {"lat": 47.5861, "lon": 1.3359},
    "Loire": {"lat": 45.4397, "lon": 4.3872},
    "Haute-Loire": {"lat": 45.0437, "lon": 3.8852},
    "Loire-Atlantique": {"lat": 47.2184, "lon": -1.5536},
    "Loiret": {"lat": 47.9029, "lon": 1.9093},
    "Lot": {"lat": 44.4475, "lon": 1.4419},
    "Lot-et-Garonne": {"lat": 44.2031, "lon": 0.6164},
    "Lozère": {"lat": 44.5170, "lon": 3.5000},
    "Maine-et-Loire": {"lat": 47.4784, "lon": -0.5632},
    "Manche": {"lat": 49.1150, "lon": -1.0900},
    "Marne": {"lat": 48.9567, "lon": 4.3630},
    "Haute-Marne": {"lat": 48.1110, "lon": 5.1390},
    "Mayenne": {"lat": 48.3067, "lon": -0.6133},
    "Meurthe-et-Moselle": {"lat": 48.6921, "lon": 6.1844},
    "Meuse": {"lat": 48.7720, "lon": 5.1610},
    "Morbihan": {"lat": 47.6582, "lon": -2.7608},
    "Moselle": {"lat": 49.1191, "lon": 6.1727},
    "Nièvre": {"lat": 46.9909, "lon": 3.1628},
    "Nord": {"lat": 50.6292, "lon": 3.0573},
    "Oise": {"lat": 49.4300, "lon": 2.0800},
    "Orne": {"lat": 48.4300, "lon": 0.0800},
    "Paris": {"lat": 48.8566, "lon": 2.3522},
    "Pas-de-Calais": {"lat": 50.4801, "lon": 2.4412},
    "Puy-de-Dôme": {"lat": 45.7719, "lon": 3.0870},
    "Pyrénées-Atlantiques": {"lat": 43.2951, "lon": -0.3708},
    "Hautes-Pyrénées": {"lat": 43.2329, "lon": 0.0781},
    "Pyrénées-Orientales": {"lat": 42.6886, "lon": 2.8948},
    "Bas-Rhin": {"lat": 48.5734, "lon": 7.7521},
    "Haut-Rhin": {"lat": 47.7508, "lon": 7.3359},
    "Rhône": {"lat": 45.7500, "lon": 4.8500},
    "Haute-Saône": {"lat": 47.6220, "lon": 6.1550},
    "Saône-et-Loire": {"lat": 46.6550, "lon": 4.5580},
    "Sarthe": {"lat": 48.0061, "lon": 0.1996},
    "Savoie": {"lat": 45.5646, "lon": 5.9178},
    "Haute-Savoie": {"lat": 45.8992, "lon": 6.1294},
    "Seine-Maritime": {"lat": 49.4431, "lon": 1.0993},
    "Seine-et-Marne": {"lat": 48.5400, "lon": 2.6600},
    "Deux-Sèvres": {"lat": 46.3237, "lon": -0.4648},
    "Somme": {"lat": 49.8941, "lon": 2.2958},
    "Tarn": {"lat": 43.9264, "lon": 2.1480},
    "Tarn-et-Garonne": {"lat": 44.0176, "lon": 1.3550},
    "Var": {"lat": 43.5000, "lon": 6.2000},
    "Vaucluse": {"lat": 43.9493, "lon": 4.8055},
    "Vendée": {"lat": 46.6700, "lon": -1.4300},
    "Vienne": {"lat": 46.5802, "lon": 0.3404},
    "Haute-Vienne": {"lat": 45.8354, "lon": 1.2620},
    "Vosges": {"lat": 48.1734, "lon": 6.4500},
    "Yonne": {"lat": 47.7982, "lon": 3.5738},

    # Départements historiques / anciens noms
    "Seine": {"lat": 48.8566, "lon": 2.3522},
    "Seine-et-Oise": {"lat": 48.8014, "lon": 2.1301},
    "Seine-Inférieure": {"lat": 49.4431, "lon": 1.0993},
    "Loire-Inférieure": {"lat": 47.2184, "lon": -1.5536},
    "Basses-Pyrénées": {"lat": 43.2951, "lon": -0.3708},
    "Basses-Alpes": {"lat": 44.0920, "lon": 6.2350},
    "Côtes-du-Nord": {"lat": 48.5142, "lon": -2.7658},
    "Charente-Inférieure": {"lat": 45.7463, "lon": -0.6337},
}


def normaliser_texte(s: str) -> str:
    """Normalise un nom pour mieux matcher les départements."""
    if pd.isna(s):
        return ""
    s = str(s).strip()
    s = s.replace("’", "'").replace("`", "'")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = s.replace("œ", "oe")
    s = s.replace(" ", "-").replace("_", "-")
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


# Alias : clé normalisée → nom canonique présent dans COORD_DEPARTEMENTS
ALIAS_DEPARTEMENTS = {normaliser_texte(k): k for k in COORD_DEPARTEMENTS.keys()}
ALIAS_DEPARTEMENTS.update({
    "seine-inferieure": "Seine-Inférieure",
    "seine-maritime": "Seine-Maritime",
    "loire-inferieure": "Loire-Inférieure",
    "loire-atlantique": "Loire-Atlantique",
    "basses-pyrenees": "Basses-Pyrénées",
    "pyrenees-atlantiques": "Pyrénées-Atlantiques",
    "basses-alpes": "Basses-Alpes",
    "alpes-basses": "Basses-Alpes",
    "alpes-de-haute-provence": "Alpes-de-Haute-Provence",
    "cotes-du-nord": "Côtes-du-Nord",
    "cotes-d-armor": "Côtes-d'Armor",
    "charente-inferieure": "Charente-Inférieure",
    "charente-maritime": "Charente-Maritime",
    "cote-d-or": "Côte-d'Or",
    "deux-sevres": "Deux-Sèvres",
    "puy-de-dome": "Puy-de-Dôme",
    "bouches-du-rhone": "Bouches-du-Rhône",
    "rhone": "Rhône",
    "herault": "Hérault",
    "ardeche": "Ardèche",
    "correze": "Corrèze",
    "drome": "Drôme",
    "nievre": "Nièvre",
    "vendee": "Vendée",
    "finistere": "Finistère",
    "isere": "Isère",
    "ariege": "Ariège",
})


def trouver_coord_departement(dept_raw: str):
    """Retourne (nom_canonique, lat, lon) ou None si non trouvé."""
    key = normaliser_texte(dept_raw)
    nom_canonique = ALIAS_DEPARTEMENTS.get(key)

    if not nom_canonique:
        return None

    coord = COORD_DEPARTEMENTS[nom_canonique]
    return nom_canonique, coord["lat"], coord["lon"]


# ---------------------------------------------------------
# 4. CHARGEMENT ET NETTOYAGE DES DONNÉES
# ---------------------------------------------------------
# Dossier contenant les 6 fichiers .parquet du modèle en étoile.
# À modifier seulement si tes fichiers ne sont pas dans ce dossier.
PARQUET_DIR = "data"


# Nom exact des fichiers Parquet attendus.
PARQUET_FILES = {
    "faits": "Faits_Occurrences.parquet",
    "orateurs": "Dim_Orateurs.parquet",
    "mandats": "Dim_Mandats.parquet",
    "temps": "Dim_Temps.parquet",
    "theme": "Dim_Theme.parquet",
    "seance": "Dim_Seance.parquet",
}


def parquet_path(nom_fichier: str) -> str:
    """Construit un chemin compatible Windows / DuckDB."""
    return f"{PARQUET_DIR.rstrip('/')}/{nom_fichier}"


def sql_string(value: str) -> str:
    """Protège les apostrophes dans les chemins SQL."""
    return value.replace("'", "''")


def quote_ident(col: str) -> str:
    """Protège les noms de colonnes, même avec accents."""
    return '"' + col.replace('"', '""') + '"'


def get_parquet_columns(conn, path: str) -> set[str]:
    """Lit uniquement le schéma d'un fichier Parquet, sans charger toutes les données."""
    desc = conn.execute(
        f"DESCRIBE SELECT * FROM read_parquet('{sql_string(path)}')"
    ).df()
    return set(desc["column_name"].tolist())


def first_existing_expr(alias: str, available_cols: set[str], candidates: list[str], default_sql: str = "NULL") -> str:
    """
    Retourne alias.colonne si elle existe, sinon une valeur par défaut.
    Pratique si tes noms de colonnes changent un peu entre JSONL / Parquet.
    """
    for col in candidates:
        if col in available_cols:
            return f"{alias}.{quote_ident(col)}"
    return default_sql


@st.cache_data()
def load_all_data():
    conn = duckdb.connect()

    conn.execute("PRAGMA threads=2;")
    conn.execute("PRAGMA memory_limit='400MB';")
    # On force DuckDB à utiliser le disque dur si la RAM est pleine
    conn.execute("PRAGMA temp_directory='duckdb_swap';")

    chemins = {key: parquet_path(filename) for key, filename in PARQUET_FILES.items()}

    try:
        cols_f = get_parquet_columns(conn, chemins["faits"])
        cols_o = get_parquet_columns(conn, chemins["orateurs"])
        cols_m = get_parquet_columns(conn, chemins["mandats"])
        cols_t = get_parquet_columns(conn, chemins["temps"])
        cols_th = get_parquet_columns(conn, chemins["theme"])
        cols_s = get_parquet_columns(conn, chemins["seance"])
    except Exception as e:
        conn.close()
        st.error(
            "Impossible de lire les fichiers Parquet. Vérifie le chemin PARQUET_DIR "
            "et le nom exact des 6 fichiers .parquet."
        )
        st.exception(e)
        st.stop()

    # Colonnes de faits
    fait_id_occurrence = first_existing_expr("f", cols_f, ["id_occurrence", "Id_occurence", "Id_occurrence"], "NULL")
    fait_lemme = first_existing_expr("f", cols_f, ["lemme_detecte", "lemme", "mot_cle"], "NULL")
    fait_contexte = first_existing_expr("f", cols_f, ["contexte", "context"], "NULL")
    fait_score = first_existing_expr("f", cols_f, ["score_ia", "ia_score_pertinence", "score_pertinence"], "0.0")
    fait_label = first_existing_expr("f", cols_f, ["label_ia", "ia_cluster_nom", "cluster_nom"], "NULL")
    fait_cluster_id = first_existing_expr("f", cols_f, ["ia_cluster_id", "cluster_id"], "NULL")
    fait_coord_x = first_existing_expr("f", cols_f, ["ia_coord_x", "coord_x"], "NULL")
    fait_coord_y = first_existing_expr("f", cols_f, ["ia_coord_y", "coord_y"], "NULL")
    fait_statut = first_existing_expr("f", cols_f, ["ia_filtre_statut", "filtre_statut"], "NULL")
    fait_rhetorique = first_existing_expr("f", cols_f, ["est_rhetorique_migratoire", "est_rhétorique_migratoire"], "NULL")

    # Dimensions
    orateur_nom = first_existing_expr("o", cols_o, ["nom", "nom_orateur", "nom_canonical_orateur"], "NULL")
    orateur_naissance = first_existing_expr("o", cols_o, ["date_naissance"], "NULL")
    orateur_deces = first_existing_expr("o", cols_o, ["date_deces"], "NULL")

    mandat_leg = first_existing_expr("m", cols_m, ["num_legislature", "legislature"], "NULL")
    
    # CORRECTION BUG 1 : On sépare bien le groupe politique de la famille politique !
    mandat_groupe = first_existing_expr("m", cols_m, ["grp_politique", "groupe_politique"], "NULL")
    mandat_famille = first_existing_expr("m", cols_m, ["famille_politique"], "NULL")
    
    mandat_dept = first_existing_expr("m", cols_m, ["dpt", "departement", "département"], "NULL")

    temps_date = first_existing_expr("t", cols_t, ["date_seance", "date"], "NULL")
    temps_annee = first_existing_expr("t", cols_t, ["annee", "année"], "NULL")
    temps_mois = first_existing_expr("t", cols_t, ["mois"], "NULL")

    theme_libelle = first_existing_expr("th", cols_th, ["libelle_theme", "theme", "libellé_theme"], "NULL")

    seance_source = first_existing_expr("s", cols_s, ["nom_fichier_source", "source_fichier", "fichier_source"], "NULL")
    seance_type = first_existing_expr("s", cols_s, ["type_seance", "type_séance"], "NULL")

    # Filtre
    where_clauses = []
    if "est_rhetorique_migratoire" in cols_f:
        where_clauses.append("LOWER(CAST(f.est_rhetorique_migratoire AS VARCHAR)) IN ('true', '1', 'oui')")
    elif "est_rhétorique_migratoire" in cols_f:
        where_clauses.append("LOWER(CAST(f.\"est_rhétorique_migratoire\" AS VARCHAR)) IN ('true', '1', 'oui')")

    if "ia_filtre_statut" in cols_f:
        where_clauses.append("COALESCE(f.ia_filtre_statut, 'retenu') = 'retenu'")

    if "ia_cluster_id" in cols_f:
        where_clauses.append("COALESCE(f.ia_cluster_id, 0) <> -1")

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    query_faits = f"""
    SELECT 
        -- Table de faits
        {fait_id_occurrence} AS id_occurrence,
        {fait_lemme} AS lemme_detecte,
        {fait_contexte} AS contexte,
        {fait_label} AS label_ia,
        {fait_score} AS score_ia,
        {fait_cluster_id} AS ia_cluster_id,
        {fait_coord_x} AS ia_coord_x,
        {fait_coord_y} AS ia_coord_y,
        {fait_statut} AS ia_filtre_statut,
        {fait_rhetorique} AS est_rhetorique_migratoire,

        -- Orateur
        f.id_orateur,
        {orateur_nom} AS nom_orateur,
        {orateur_naissance} AS date_naissance,
        {orateur_deces} AS date_deces,

        -- Mandat
        f.id_mandat,
        {mandat_leg} AS num_legislature,
        {mandat_groupe} AS grp_politique,
        {mandat_famille} AS famille_politique, -- CORRECTION BUG 1 APPLIQUÉE ICI
        {mandat_dept} AS departement,

        -- Temps
        f.id_date,
        {temps_date} AS date_seance,
        {temps_annee} AS annee,
        {temps_mois} AS mois,

        -- Thème
        f.id_theme,
        {theme_libelle} AS libelle_theme,
        {theme_libelle} AS theme,

        -- Séance
        f.id_seance,
        {seance_source} AS nom_fichier_source,
        {seance_type} AS type_seance

    FROM read_parquet('{sql_string(chemins["faits"])}') f
    
    -- CORRECTION BUG 3 : La jointure sécurisée par REGEX pour l'orateur !
    LEFT JOIN read_parquet('{sql_string(chemins["orateurs"])}') o 
        ON regexp_extract(CAST(f.id_orateur AS VARCHAR), '\\d+') = regexp_extract(CAST(o.id_orateur AS VARCHAR), '\\d+')
        
    LEFT JOIN read_parquet('{sql_string(chemins["mandats"])}') m 
        ON f.id_mandat = m.id_mandat
    LEFT JOIN read_parquet('{sql_string(chemins["temps"])}') t 
        ON f.id_date = t.id_date
    LEFT JOIN read_parquet('{sql_string(chemins["theme"])}') th 
        ON f.id_theme = th.id_theme
    LEFT JOIN read_parquet('{sql_string(chemins["seance"])}') s 
        ON f.id_seance = s.id_seance
    {where_sql}
    LIMIT 100000
    """

    try:
        df_faits = conn.execute(query_faits).df()
    except Exception as e:
        conn.close()
        st.error("Erreur pendant la jointure des tables Parquet avec DuckDB.")
        st.stop()

    # 1. On transforme les "faux vides" en vrais NaN pour Pandas
    df_faits["famille_politique"] = df_faits["famille_politique"].replace(
        ["Non renseignée / Autres", "Non renseigné", "NULL", "", None], np.nan
    )

    # 2. CRUCIAL : On trie par Orateur ET par Année pour respecter l'histoire !
    # On s'assure d'abord que l'année est bien un nombre
    df_faits["annee"] = pd.to_numeric(df_faits["annee"], errors="coerce")
    df_faits = df_faits.sort_values(by=["id_orateur", "annee"])

    # 3. LA MAGIE TEMPORELLE : ffill (vers le futur) puis bfill (vers le passé)
    df_faits["famille_politique"] = (
        df_faits.groupby("id_orateur")["famille_politique"]
        .ffill()  # Si vide, prend le parti du mandat précédent
        .bfill()  # Si toujours vide, prend le parti du mandat suivant
    )

    # 4. S'il reste des orateurs 100% inconnus sur toute leur vie, on les met dans Autres
    df_faits["famille_politique"] = df_faits["famille_politique"].fillna("Non renseignée / Autres")

    # Nettoyage minimal pour éviter les erreurs dans les filtres et graphiques.
    df_faits["famille_politique"] = df_faits["famille_politique"].fillna("Non renseignée / Autres")
    df_faits["grp_politique"] = df_faits["grp_politique"].fillna("Non renseigné")
    df_faits["nom_orateur"] = df_faits["nom_orateur"].fillna("Inconnu")
    df_faits["departement"] = df_faits["departement"].fillna("Inconnu")
    df_faits["libelle_theme"] = df_faits["libelle_theme"].fillna("Non renseigné")
    df_faits["theme"] = df_faits["theme"].fillna(df_faits["libelle_theme"])
    df_faits["score_ia"] = pd.to_numeric(df_faits["score_ia"], errors="coerce").fillna(0)
    df_faits["annee"] = pd.to_numeric(df_faits["annee"], errors="coerce")

    # Table complète des mandats pour la fiche député.
    mandat_date_debut = first_existing_expr("m", cols_m, ["debut_mandat", "date_debut_mandat", "date_debut"], "NULL")
    mandat_date_fin = first_existing_expr("m", cols_m, ["fin_mandat", "date_fin_mandat", "date_fin"], "NULL")

    query_mandats = f"""
    SELECT 
        m.id_orateur,
        {mandat_leg} AS num_legislature,
        {mandat_groupe} AS grp_politique,
        {mandat_dept} AS departement,
        {mandat_date_debut} AS date_debut_mandat,
        {mandat_date_fin} AS date_fin_mandat
    FROM read_parquet('{sql_string(chemins["mandats"])}') m
    """

    df_mandats = conn.execute(query_mandats).df()
    df_mandats["grp_politique"] = df_mandats["grp_politique"].fillna("Non renseigné")
    df_mandats["departement"] = df_mandats["departement"].fillna("Inconnu")

    # CORRECTION BUG 2 : SUPPRESSION DES `pd.to_datetime` QUI CASSAIENT LE FORMAT "DD - MM - YYYY" !
    # On laisse les dates exactement comme le SQL les a préparées.

    conn.close()

    return df_faits, df_mandats


# Chargement global — exécuté une seule fois grâce au cache Streamlit
df_faits, df_mandats_complet = load_all_data()

# On écrase TOUTES les variations de majuscules directement dans la mémoire de l'application !
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

        # =========================================================
        # 📅 CORRECTION SECURITE : Extraction propre des années
        # =========================================================
        if "date_seance" in df_faits.columns:
            df_faits["annee"] = pd.to_datetime(df_faits["date_seance"], errors="coerce").dt.year
            df_faits = df_faits.dropna(subset=["annee"])
            df_faits["annee"] = df_faits["annee"].astype(int)

        # On filtre la Ve République pour ton volume de données dispo
        df_valide = df_faits[(df_faits["annee"] >= 1958) & (df_faits["annee"] <= 2026)].copy()

        # Config du Slider Temporel
        if not df_valide.empty:
            min_year = int(df_valide["annee"].min())
            max_year = int(df_valide["annee"].max())
        else:
            min_year, max_year = 1958, 2026

        col_time, _ = st.columns([1, 2])

        with col_time:
            annee_slider = st.slider(
                "📅 Période historique",
                min_year,
                max_year,
                (min_year, max_year)
            )

        # Filtrage du dataset selon la période choisie
        df_page1 = df_valide[
            (df_valide["annee"] >= annee_slider[0]) &
            (df_valide["annee"] <= annee_slider[1])
        ].copy()

        st.markdown("---")

        # =========================================================
        # 🏛️ CORRECTION RADICALE : Cartographie des Familles Politiques
        # =========================================================
        def nettoyer_et_classer_famille(groupe):
            if pd.isna(groupe): 
                return "Autres / Non-inscrits"
            g = str(groupe).lower().strip()
            if g == "" or g == "none" or g == "null" or g == "inconnu":
                return "Autres / Non-inscrits"
            
            # 🔴 Détection Famille de Gauche & Extrême Gauche
            if any(mot in g for mot in ['soc', 'com', 'gauch', 'lfi', 'insoumis', 'écolo', 'ecolo', 'nupes', 'radic', 'pcf', 'ps']):
                return "Gauche"
            # 🔵 Détection Famille de Droite
            elif any(mot in g for mot in ['rpr', 'ump', 'lr', 'droit', 'répub', 'repub', 'udf', 'indépen', 'libéral', 'unr', 'udr']):
                return "Droite"
            # 🟡 Détection Famille du Centre
            elif any(mot in g for mot in ['centr', 'modem', 'udi', 'renaissance', 'marche', 'lrem', 'horizons', 'ensemble']):
                return "Centre"
            # ⚫ Détection Famille d'Extrême Droite
            elif any(mot in g for mot in ['front nat', 'rassemblement nat', 'rn', 'fn', 'national', 'recouv']):
                return "Extrême Droite"
            else:
                return "Autres / Non-inscrits"

        # On cherche d'abord dans 'famille_politique', sinon dans 'groupe_politique', sinon dans 'grp_politique'
        col_groupe_source = None
        for col in ["famille_politique", "groupe_politique", "grp_politique"]:
            if col in df_page1.columns:
                col_groupe_source = col
                break

        if col_groupe_source:
            df_page1["famille_politique_calculee"] = df_page1[col_groupe_source].apply(nettoyer_et_classer_famille)
        else:
            # Sécurité ultime : si aucune colonne de parti n'est présente dans la table de faits
            df_page1["famille_politique_calculee"] = "Autres / Non-inscrits"

        # =========================================================
        # 📊 CONSTRUCTION DES DEUX GRAPHIQUES CÔTE À CÔTE
        # =========================================================
        g1, g2 = st.columns(2)

        with g1:
            st.subheader("📈 Évolution chronologique")

            # Tolérance sur le nom de la colonne de thèmes
            col_theme_faits = "theme" if "theme" in df_page1.columns else "libelle_theme"

            if col_theme_faits in df_page1.columns:
                df_trend = (
                    df_page1
                    .groupby(["annee", col_theme_faits])
                    .size()
                    .reset_index(name="Nombre")
                )
                
                # Correction cosmétique pour la légende Plotly (met une majuscule)
                df_trend[col_theme_faits] = df_trend[col_theme_faits].replace({
                    "migration": "Migration", "etranger": "Étranger", "invasion": "Invasion"
                })

                if not df_trend.empty:
                    fig_line = px.line(
                        df_trend,
                        x="annee",
                        y="Nombre",
                        color=col_theme_faits,
                        markers=True,
                        color_discrete_map=COULEURS_THEMES
                    )

                    fig_line = appliquer_theme_plotly(fig_line, "Évolution chronologique des occurrences")
                    fig_line.update_xaxes(title="Année")
                    fig_line.update_yaxes(title="Nombre d’occurrences")
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.warning("Aucune donnée disponible pour cette période.")
            else:
                st.error("Colonne thématique introuvable dans les données.")

        with g2:
            # ---------------------------------------------------------
            # 📊 GRAPHIQUE 2 : LA RÉPARTITION GLOBALE (TOP)
            # ---------------------------------------------------------
            st.subheader("📊 Volume total par grande famille")
            
            # 🎨 LE VRAI DICTIONNAIRE DE COULEURS (Avec toutes tes nuances !)
            couleurs_completes = {
                "Extrême gauche": "#780000",   # Rouge très foncé
                "Gauche": "#c1121f",           # Rouge classique
                "Centre gauche": "#f4a261",    # Orange clair
                "Centre": "#ffb703",           # Jaune
                "Centre droit": "#fb8500",     # Orange foncé
                "Droite": "#00509d",           # Bleu
                "Extrême droite": "#001a2c",   # Bleu très sombre
                "Non inscrits": "#6c757d",     # Gris foncé
                "Non renseignée / Autres": "#adb5bd" # Gris clair
            }

            # 🚨 ON REPREND TA VRAIE COLONNE : "famille_politique"
            df_bar = df_page1.groupby("famille_politique").size().reset_index(name="Volume total")
            
            # On trie du plus grand au plus petit
            df_bar = df_bar.sort_values(by="Volume total", ascending=False) 

            fig_bar = px.bar(
                df_bar,
                x="Volume total",
                y="famille_politique",
                color="famille_politique",
                color_discrete_map=couleurs_completes, # On applique le dico complet
                orientation="h",
                template="plotly_white",
                text="Volume total", 
                labels={"famille_politique": "Courant Politique", "Volume total": "Phrases extraites"}
            )
            
            # On supprime la légende qui fait doublon avec l'axe Y
            fig_bar.update_layout(showlegend=False)
            
            st.plotly_chart(fig_bar, use_container_width=True)
# =========================================================================================
# PAGE 2 : ANNUAIRE DES DÉPUTÉS
# =========================================================================================
with tab_deputes:
        
        # ==============================================================================
        # 👤 SECTION : ANNUAIRE DES DÉPUTÉS
        # ==============================================================================

        afficher_header(
            "🏛️ Fiche Parlementaire",
            "Profil biographique et mandats parlementaires"
        )

        # 1. 🧹 ON PURGE : On crée un tableau dédié à l'annuaire sans l'orateur "Inconnu"
        df_annuaire = df_faits[df_faits["famille_politique"] != "Non renseignée / Autres"]

        # 2. 🎯 Disposition en 2 colonnes pour les menus
        col_search1, col_search2 = st.columns(2)

        with col_search1:
            # On cherche les familles dans notre NOUVEAU tableau purgé !
            familles_dispo_p2 = ["Toutes"] + sorted(
                df_annuaire["famille_politique"].dropna().unique().tolist()
            )

            choix_famille = st.selectbox(
                "1. Sélectionner la famille politique",
                options=familles_dispo_p2
            )

        # 3. 🎯 Filtrage en cascade de la liste des députés
        if choix_famille != "Toutes":
            df_deputes_dispo = df_annuaire[df_annuaire["famille_politique"] == choix_famille]
        else:
            df_deputes_dispo = df_annuaire

        list_deputes = sorted(
            df_deputes_dispo["nom_orateur"].dropna().unique().tolist()
        )

        if not list_deputes:
            st.warning("Aucun orateur disponible avec ce filtre.")
            st.stop()

        with col_search2:
            choix_depute = st.selectbox(
                "2. Sélectionner l’orateur",
                options=list_deputes
            )

        # 4. 🎯 On isole les données de ce député (Toujours à partir du tableau purgé)
        df_depute_profile = df_annuaire[df_annuaire["nom_orateur"] == choix_depute]

        # ==============================================================================
        # AFFICHAGE DE LA BIO ET DES MANDATS
        # ==============================================================================
        if not df_depute_profile.empty:
            info = df_depute_profile.iloc[0]

            # Vérification sécurisée des colonnes d'identification
            if "id_orateur" in info and pd.notnull(info["id_orateur"]):
                id_sycomore = info["id_orateur"]
            elif "id_acteur" in info and pd.notnull(info["id_acteur"]):
                id_sycomore = info["id_acteur"]
            else:
                id_sycomore = "Inconnu"

            date_n = info["date_naissance"] if pd.notnull(info["date_naissance"]) else "Inconnue"
            date_d = info["date_deces"] if pd.notnull(info["date_deces"]) else "Vivante / Non renseignée"

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
                    # L'URL a besoin qu'on enlève le "PA" de l'identifiant s'il est présent
                    id_propre = str(id_sycomore).replace("PA", "")
                    url_an = f"https://www2.assemblee-nationale.fr/sycomore/fiche?num_dept={id_propre}"
                    st.link_button(
                        "🌐 Ouvrir la fiche Sycomore",
                        url_an,
                        use_container_width=True
                    )

            st.markdown("#### 📂 Historique des mandats scrapés")

            df_ses_mandats = (
                df_mandats_complet[df_mandats_complet["id_orateur"] == id_sycomore]
                .drop_duplicates()
            )

            st.dataframe(
                df_ses_mandats,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")

            # =========================================================
            # 🛠️ DISPOSITION CÔTE À CÔTE : CARTE ET RADAR
            # =========================================================
            col_map, col_radar = st.columns(2)

            with col_map:
                st.markdown("### 🗺️ Implantation parlementaire")

                map_rows = []
                depts_non_localises = []

                if not df_ses_mandats.empty:
                    for dept_raw, sous_df in df_ses_mandats.groupby("departement", dropna=True):
                        found = trouver_coord_departement(dept_raw)

                        if found:
                            nom_canonique, lat, lon = found
                            map_rows.append({
                                "Département": nom_canonique,
                                "lat": lat,
                                "lon": lon,
                                "Nombre de mandats": len(sous_df)
                            })
                        else:
                            d_clean = str(dept_raw).strip()
                            if d_clean and d_clean.lower() != "inconnu":
                                depts_non_localises.append(d_clean)

                if map_rows:
                    df_map = pd.DataFrame(map_rows)

                    fig_map = px.scatter_mapbox(
                        df_map,
                        lat="lat",
                        lon="lon",
                        hover_name="Département",
                        hover_data={"Nombre de mandats": True, "lat": False, "lon": False},
                        size="Nombre de mandats",
                        size_max=22,
                        zoom=4.2,  # Légèrement réduit pour s'adapter à la colonne
                        center={"lat": 46.6, "lon": 2.2},
                        height=450, # Aligné avec la hauteur du radar
                        mapbox_style="open-street-map",
                        color_discrete_sequence=[BLEU_FR]
                    )

                    fig_map.update_traces(
                        hovertemplate=(
                            "<b>%{hovertext}</b><br>"
                            "Nombre de mandats : %{customdata[0]}"
                            "<extra></extra>"
                        ),
                        marker=dict(opacity=0.88)
                    )

                    fig_map.update_layout(
                        margin={"r": 0, "t": 0, "l": 0, "b": 0},
                        paper_bgcolor="white"
                    )

                    st.plotly_chart(fig_map, use_container_width=True)
                else:
                    st.info("Aucun département localisable pour cet orateur.")

                if depts_non_localises:
                    st.warning(
                        "Départements non localisés automatiquement : "
                        + ", ".join(sorted(set(depts_non_localises)))
                    )

            with col_radar:
                st.markdown("### 🎯 Empreinte Thématique")

                # Détection automatique : gère à la fois 'theme' et 'libelle_theme'
                col_theme = "theme" if "theme" in df_depute_profile.columns else ("libelle_theme" if "libelle_theme" in df_depute_profile.columns else None)

                if col_theme and not df_depute_profile[col_theme].dropna().empty:
                    
                    # 1. Calcul des proportions 
                    df_radar = df_depute_profile[col_theme].value_counts(normalize=True).reset_index()
                    df_radar.columns = ["Thème", "Proportion"]
                    df_radar["Proportion"] = df_radar["Proportion"] * 100  # Conversion en %

                    # 2. Harmonisation en minuscules et suppression des espaces invisibles
                    df_radar["Thème"] = df_radar["Thème"].astype(str).str.lower().str.strip()
                    
                    # 🚨 LA CORRECTION EST ICI : On utilise "etranger" SANS accent pour coller à ton JSONL
                    themes_ref = pd.DataFrame({"Thème": ["migration", "etranger", "invasion"]})
                    df_radar = pd.merge(themes_ref, df_radar, on="Thème", how="left").fillna(0)

                    # 3. On renomme proprement pour faire un bel affichage sur le graphique
                    df_radar["Thème"] = df_radar["Thème"].replace({
                        "migration": "Migration",
                        "etranger": "Étranger",
                        "invasion": "Invasion"
                    })

                    # 4. Construction du graphique Radar
                    fig_radar = px.line_polar(
                        df_radar,
                        r="Proportion",
                        theta="Thème",
                        line_close=True,
                        color_discrete_sequence=[BLEU_FR],
                        height=420
                    )
                    
                    fig_radar.update_traces(fill='toself', opacity=0.7)
                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100], # Bloqué à 100% fixes
                                ticksuffix="%"
                            )
                        ),
                        margin=dict(l=40, r=40, t=30, b=20),
                        showlegend=False
                    )

                    st.plotly_chart(fig_radar, use_container_width=True)
                    
                    # Petit texte explicatif d'analyse
                    if df_radar['Proportion'].max() > 0:
                        theme_dominant = df_radar.loc[df_radar['Proportion'].idxmax()]
                        st.info(f"💡 Thème majoritaire : **{theme_dominant['Thème']}** ({theme_dominant['Proportion']:.1f}% des mentions).")
                else:
                    st.warning("Données thématiques indisponibles pour cet orateur.")
        else:
            st.warning("Aucune donnée disponible pour cet orateur.")
