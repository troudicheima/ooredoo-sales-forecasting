# -*- coding: utf-8 -*-
"""
utils/theme.py

Module central de design pour l'application "Ooredoo Sales Intelligence".
Fournit :
- le CSS global (couleurs, typographie, cartes, sidebar, animations)
- des fonctions Python pour générer les composants visuels réutilisables
  (cartes KPI, header de page, bloc de marque dans la sidebar, bulles de chat)
- une palette de couleurs cohérente pour les graphiques Plotly

À importer et appeler en tout début de chaque page :
    from utils.theme import apply_theme
    apply_theme(page_title="Dashboard", page_icon="📊")
"""

import os
import base64
import streamlit as st

# ---------------------------------------------------------------------------
# PALETTE DE COULEURS OOREDOO
# ---------------------------------------------------------------------------
COLOR_PRIMARY = "#E4032E"       # rouge Ooredoo
COLOR_PRIMARY_DARK = "#A8001F"  # rouge foncé (dégradés)
COLOR_PRIMARY_LIGHT = "#FDEBEE" # rouge très clair (fonds d'accent)
COLOR_BG = "#FAFAFA"            # fond général
COLOR_SURFACE = "#FFFFFF"       # cartes / surfaces
COLOR_SURFACE_ALT = "#F3F4F6"   # surfaces secondaires (gris très clair)
COLOR_TEXT = "#1A1A1A"          # texte principal (gris foncé / noir)
COLOR_TEXT_SECONDARY = "#6B7280"  # texte secondaire (gris moyen)
COLOR_BORDER = "#E5E7EB"        # bordures discrètes

# Palette pour les graphiques Plotly : rouge Ooredoo en tête, puis neutres
PLOTLY_COLORWAY = [
    COLOR_PRIMARY, "#2D2D2D", "#9CA3AF", "#F59E0B", "#4B5563", "#D1D5DB",
]

PLOTLY_LAYOUT = dict(
    colorway=PLOTLY_COLORWAY,
    plot_bgcolor=COLOR_SURFACE,
    paper_bgcolor=COLOR_SURFACE,
    font=dict(family="Inter, sans-serif", color=COLOR_TEXT, size=13),
    title_font=dict(family="Inter, sans-serif", size=16, color=COLOR_TEXT),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    margin=dict(t=50, l=10, r=10, b=10),
)


def style_fig(fig):
    """Applique le thème Ooredoo à une figure Plotly existante."""
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(gridcolor=COLOR_BORDER, zerolinecolor=COLOR_BORDER)
    fig.update_yaxes(gridcolor=COLOR_BORDER, zerolinecolor=COLOR_BORDER)
    return fig


# ---------------------------------------------------------------------------
# CSS GLOBAL
# ---------------------------------------------------------------------------
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

/* Fond général de l'application */
.stApp {{
    background-color: {COLOR_BG};
}}

/* Masquer les éléments par défaut de Streamlit pour un rendu plus premium */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
.stAppDeployButton {{display: none;}}
header[data-testid="stHeader"] {{background: transparent;}}

/* ============================= SIDEBAR ============================= */
section[data-testid="stSidebar"] {{
    background-color: {COLOR_SURFACE};
    border-right: 1px solid {COLOR_BORDER};
}}

section[data-testid="stSidebar"] .block-container {{
    padding-top: 1.2rem;
}}

/* Bloc de marque (logo + nom de l'app) dans la sidebar */
.sidebar-brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 4px 4px 18px 4px;
    margin-bottom: 12px;
    border-bottom: 1px solid {COLOR_BORDER};
}}
.sidebar-brand-logo-img {{
    width: 40px;
    height: 40px;
    min-width: 40px;
    object-fit: contain;
}}
.sidebar-brand-text {{
    display: flex;
    flex-direction: column;
    line-height: 1.15;
}}
.sidebar-brand-title {{
    font-weight: 700;
    font-size: 15px;
    color: {COLOR_TEXT};
}}
.sidebar-brand-subtitle {{
    font-size: 11px;
    color: {COLOR_TEXT_SECONDARY};
    font-weight: 500;
}}

.sidebar-footer {{
    position: fixed;
    bottom: 18px;
    padding: 0 4px;
    font-size: 11px;
    color: {COLOR_TEXT_SECONDARY};
    line-height: 1.6;
}}

/* Liens de navigation générés automatiquement par Streamlit (pages/) */
section[data-testid="stSidebarNav"] {{
    padding-top: 0;
}}
section[data-testid="stSidebarNav"] ul {{
    padding: 0 8px;
}}
section[data-testid="stSidebarNav"] a {{
    border-radius: 10px !important;
    padding: 10px 14px !important;
    margin-bottom: 4px !important;
    font-weight: 500 !important;
    color: {COLOR_TEXT} !important;
    transition: all 0.15s ease-in-out;
}}
section[data-testid="stSidebarNav"] a:hover {{
    background-color: {COLOR_PRIMARY_LIGHT} !important;
    color: {COLOR_PRIMARY_DARK} !important;
}}
section[data-testid="stSidebarNav"] a[aria-current="page"] {{
    background: linear-gradient(135deg, {COLOR_PRIMARY}, {COLOR_PRIMARY_DARK}) !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 10px rgba(228, 3, 46, 0.25);
}}
section[data-testid="stSidebarNav"] a[aria-current="page"] span {{
    color: white !important;
}}

/* ============================= HEADER DE PAGE ============================= */
.page-header {{
    padding: 4px 0 18px 0;
    margin-bottom: 22px;
    border-bottom: 1px solid {COLOR_BORDER};
    animation: fadeInDown 0.4s ease-out;
}}
.page-header-title {{
    font-size: 30px;
    font-weight: 800;
    color: {COLOR_TEXT};
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0;
}}
.page-header-badge {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: linear-gradient(135deg, {COLOR_PRIMARY}, {COLOR_PRIMARY_DARK});
    font-size: 22px;
}}
.page-header-subtitle {{
    font-size: 14.5px;
    color: {COLOR_TEXT_SECONDARY};
    margin: 6px 0 0 58px;
    font-weight: 500;
}}

/* ============================= CARTES KPI ============================= */
.kpi-card {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    animation: fadeInUp 0.4s ease-out;
    height: 100%;
}}
.kpi-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
}}
.kpi-icon {{
    font-size: 20px;
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background-color: {COLOR_PRIMARY_LIGHT};
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 10px;
}}
.kpi-value {{
    font-size: 26px;
    font-weight: 800;
    color: {COLOR_TEXT};
    line-height: 1.1;
}}
.kpi-label {{
    font-size: 12.5px;
    color: {COLOR_TEXT_SECONDARY};
    font-weight: 600;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}}
.kpi-accent {{
    height: 3px;
    width: 32px;
    background: linear-gradient(90deg, {COLOR_PRIMARY}, {COLOR_PRIMARY_DARK});
    border-radius: 4px;
    margin-top: 10px;
}}

/* ============================= CARTE DE PREDICTION ============================= */
.prediction-card {{
    background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_PRIMARY_DARK} 100%);
    border-radius: 20px;
    padding: 32px 34px;
    color: white;
    box-shadow: 0 10px 30px rgba(228, 3, 46, 0.28);
    animation: fadeInUp 0.4s ease-out;
}}
.prediction-label {{
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    opacity: 0.85;
}}
.prediction-value {{
    font-size: 46px;
    font-weight: 800;
    margin: 6px 0 2px 0;
    line-height: 1.1;
}}
.prediction-sub {{
    font-size: 13px;
    opacity: 0.85;
    font-weight: 500;
}}

/* ============================= SECTIONS / CONTENEURS ============================= */
.section-card {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 16px;
    padding: 20px 22px;
    margin-bottom: 18px;
    animation: fadeInUp 0.4s ease-out;
}}
.section-title {{
    font-size: 16px;
    font-weight: 700;
    color: {COLOR_TEXT};
    margin-bottom: 4px;
}}

/* ============================= CHAT ASSISTANT IA ============================= */
.chat-bubble-user {{
    background-color: {COLOR_SURFACE_ALT};
    color: {COLOR_TEXT};
    border-radius: 16px 16px 4px 16px;
    padding: 12px 16px;
    margin: 6px 0;
    max-width: 80%;
    margin-left: auto;
    font-size: 14.5px;
}}
.chat-bubble-assistant {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-left: 3px solid {COLOR_PRIMARY};
    border-radius: 16px 16px 16px 4px;
    padding: 12px 16px;
    margin: 6px 0;
    max-width: 85%;
    font-size: 14.5px;
}}

.example-chip {{
    display: inline-block;
    background-color: {COLOR_SURFACE_ALT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 20px;
    padding: 7px 14px;
    margin: 4px 6px 4px 0;
    font-size: 13px;
    color: {COLOR_TEXT};
    font-weight: 500;
}}

.badge-info {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background-color: {COLOR_PRIMARY_LIGHT};
    color: {COLOR_PRIMARY_DARK};
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 12.5px;
    font-weight: 600;
    margin-bottom: 4px;
}}

/* ============================= BOUTONS STREAMLIT ============================= */
.stButton > button {{
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.15s ease-in-out;
}}
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {COLOR_PRIMARY}, {COLOR_PRIMARY_DARK});
    border: none;
    box-shadow: 0 4px 10px rgba(228, 3, 46, 0.25);
}}
.stButton > button[kind="primary"]:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 14px rgba(228, 3, 46, 0.35);
}}

/* ============================= ANIMATIONS ============================= */
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeInDown {{
    from {{ opacity: 0; transform: translateY(-10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
</style>
"""


def apply_theme(page_title: str = "Ooredoo Sales Intelligence", page_icon: str = "📡", layout: str = "wide"):
    """À appeler en tout premier dans chaque page : configure la page,
    injecte le CSS global et affiche le logo + le bloc de marque dans la sidebar."""
    st.set_page_config(page_title=f"{page_title} — Ooredoo", page_icon=page_icon, layout=layout)
    st.markdown(CSS, unsafe_allow_html=True)
    render_sidebar_brand()


@st.cache_data
def _get_logo_base64() -> str | None:
    """Charge le logo depuis assets/ooredoo_logo.png et le convertit en base64,
    pour pouvoir l'intégrer directement dans le bloc HTML de la sidebar
    (nécessaire pour l'afficher à côté du texte, ce que st.logo() seul ne permet pas)."""
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "ooredoo_logo.png")
    if not os.path.exists(logo_path):
        return None
    with open(logo_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def render_sidebar_brand():
    """Bloc logo + nom de l'application, côte à côte, en haut de la sidebar."""
    logo_b64 = _get_logo_base64()
    logo_html = (
        f'<img class="sidebar-brand-logo-img" src="data:image/png;base64,{logo_b64}">'
        if logo_b64 else ""
    )
    st.sidebar.markdown(
        f"""
        <div class="sidebar-brand">
            {logo_html}
            <div class="sidebar-brand-text">
                <div class="sidebar-brand-title">Ooredoo Sales Intelligence</div>
                <div class="sidebar-brand-subtitle">AI-Powered Sales Forecasting</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_footer():
    st.sidebar.markdown(
        """
        <div class="sidebar-footer">
            Sales Analytics Platform<br>v1.0 — 2026
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str, subtitle: str, icon: str = "📊"):
    """Header de page moderne : icône badge + titre + sous-titre."""
    st.markdown(
        f"""
        <div class="page-header">
            <p class="page-header-title"><span class="page-header-badge">{icon}</span>{title}</p>
            <p class="page-header-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(icon: str, value: str, label: str):
    """Retourne le HTML d'une carte KPI (à utiliser dans une colonne st.columns)."""
    return f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-accent"></div>
        </div>
        """


def render_prediction_card(label: str, value: str, sub: str):
    return f"""
        <div class="prediction-card">
            <div class="prediction-label">{label}</div>
            <div class="prediction-value">{value}</div>
            <div class="prediction-sub">{sub}</div>
        </div>
        """


def render_badge(text: str, icon: str = "ℹ️"):
    return f'<div class="badge-info">{icon} {text}</div>'