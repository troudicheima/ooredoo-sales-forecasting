# -*- coding: utf-8 -*-
import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.theme import render_header, render_badge
from utils.rag_utils import ask_llm, generate_monthly_report
from utils.report_export import generate_docx_report, generate_pdf_report

render_header(
    title="Assistant IA",
    subtitle="Interrogez vos données de ventes en langage naturel.",
    icon="🤖",
)

st.markdown(
    render_badge(
        "Le modèle LightGBM produit les prévisions chiffrées (page Prévisions) — "
        "l'Assistant IA, lui, explique les données et les résultats en langage naturel, "
        "à partir d'informations réelles récupérées via un pipeline RAG.",
        icon="🧠",
    ),
    unsafe_allow_html=True,
)
st.write("")

tab_chat, tab_report = st.tabs(["💬 Poser une question", "📄 Générer un rapport"])

# ---------------------------------------------------------------------
# Onglet 1 — Chat
# ---------------------------------------------------------------------
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    EXAMPLE_QUESTIONS = [
        "Quelles sont les ventes du mois de mars 2025 ?",
        "Quelles sont les régions qui vendent le plus ?",
        "Quelle est la précision du modèle ?",
        "Comment évoluent les ventes 5G ?",
        "Quels produits ont la meilleure performance ?",
    ]

    if not st.session_state.messages:
        st.markdown("**💡 Exemples de questions :**")
        chip_cols = st.columns(len(EXAMPLE_QUESTIONS))
        clicked_question = None
        for i, q in enumerate(EXAMPLE_QUESTIONS):
            with chip_cols[i]:
                if st.button(q, key=f"chip_{i}", use_container_width=True):
                    clicked_question = q
        st.write("")
    else:
        clicked_question = None

    for msg in st.session_state.messages:
        bubble_class = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-assistant"
        avatar = "🧑‍💼" if msg["role"] == "user" else "🤖"
        align = "flex-end" if msg["role"] == "user" else "flex-start"
        st.markdown(
            f"""
            <div style="display:flex; flex-direction:column; align-items:{align};">
                <div class="{bubble_class}">{avatar} {msg['content']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("📚 Sources utilisées pour cette réponse"):
                for s in msg["sources"]:
                    st.markdown(f"- {s}")

    question = st.chat_input("Posez votre question sur les ventes, les tendances, le modèle...")
    question = question or clicked_question

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
        with st.spinner("Recherche dans les données et rédaction de la réponse..."):
            answer, sources = ask_llm(question, chat_history=history)
        st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
        st.rerun()

    if st.session_state.messages:
        if st.button("🗑️ Effacer la conversation"):
            st.session_state.messages = []
            st.rerun()

# ---------------------------------------------------------------------
# Onglet 2 — Génération de rapport
# ---------------------------------------------------------------------
with tab_report:
    st.markdown('<div class="section-title">📄 Génération automatique d\'un rapport mensuel</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1.4])
    with col1:
        year = st.selectbox("Année", [2022, 2023, 2024, 2025], index=3)
    with col2:
        month = st.selectbox("Mois", list(range(1, 13)), index=0)
    with col3:
        st.write("")
        st.write("")
        generate_report = st.button("📄 Générer le rapport", type="primary", use_container_width=True)

    if generate_report:
        with st.spinner("Génération du rapport en cours..."):
            report_text = generate_monthly_report(year, month)
        st.session_state["last_report"] = report_text
        st.session_state["last_report_period"] = (year, month)

    if st.session_state.get("last_report"):
        report_text = st.session_state["last_report"]
        year, month = st.session_state["last_report_period"]
        report_title = f"Rapport de ventes — {month:02d}/{year}"

        st.markdown('<div class="section-card">' + report_text.replace("\n", "<br>") + '</div>', unsafe_allow_html=True)

        dl_col1, dl_col2, dl_col3 = st.columns(3)
        with dl_col1:
            st.download_button(
                "⬇️ Télécharger (.txt)",
                data=report_text,
                file_name=f"rapport_ventes_{year}_{month:02d}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with dl_col2:
            docx_bytes = generate_docx_report(report_text, report_title)
            st.download_button(
                "⬇️ Télécharger (.docx)",
                data=docx_bytes,
                file_name=f"rapport_ventes_{year}_{month:02d}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        with dl_col3:
            pdf_bytes = generate_pdf_report(report_text, report_title)
            st.download_button(
                "⬇️ Télécharger (.pdf)",
                data=pdf_bytes,
                file_name=f"rapport_ventes_{year}_{month:02d}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )