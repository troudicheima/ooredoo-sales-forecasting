# -*- coding: utf-8 -*-
"""
main.py — Point d'entrée de l'application.

Utilise st.navigation() (API moderne de Streamlit) plutôt que le simple
dossier pages/, afin de garder le contrôle total sur l'ordre des éléments
de la sidebar : le logo + le nom de l'application doivent apparaître
AVANT le menu de navigation, ce que le dossier pages/ classique ne
permet pas (Streamlit y place toujours le menu tout en haut, de force).
"""

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(__file__))

from utils.theme import apply_theme, render_sidebar_header, render_sidebar_footer

# 1) Configuration de la page + injection du CSS global (une seule fois, ici)
apply_theme(page_title="Ooredoo Sales Intelligence", page_icon="📡")

# 2) Logo + nom de l'application, tout en haut de la sidebar
render_sidebar_header()

# 3) Déclaration des pages de l'application
home_page = st.Page("views/home.py", title="Accueil", icon="🏠", default=True)
dashboard_page = st.Page("pages/Dashboard.py", title="Dashboard", icon="📊")
previsions_page = st.Page("pages/Previsions.py", title="Prévisions", icon="🔮")
assistant_page = st.Page("pages/Assistant_IA.py", title="Assistant IA", icon="🤖")

# 4) Menu de navigation, affiché juste APRÈS le logo/texte
pg = st.navigation([home_page, dashboard_page, previsions_page, assistant_page])

# 5) Footer de la sidebar (position fixe en bas, peu importe l'ordre d'appel)
render_sidebar_footer()

# 6) Exécution de la page actuellement sélectionnée
pg.run()