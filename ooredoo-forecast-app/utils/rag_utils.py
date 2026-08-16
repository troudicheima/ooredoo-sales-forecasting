# -*- coding: utf-8 -*-
"""
utils/rag_utils.py

Pipeline RAG (Retrieval-Augmented Generation) :
1. retrieve_context()  -> recherche les documents les plus pertinents dans ChromaDB
2. retrieve_context_for_month() -> récupération EXACTE par métadonnées (rapports)
3. ask_llm()            -> envoie la question + le contexte récupéré au LLM,
                           avec des règles strictes pour éviter les hallucinations
                           et interdire au LLM de prédire des ventes lui-même.
"""

import os
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

VECTOR_STORE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vector_store")
COLLECTION_NAME = "ooredoo_knowledge"

# NOTE : "llama-3.3-70b-versatile" a été décommissionné par Groq le 16/08/2026.
# Modèle de remplacement recommandé par Groq (email officiel) : openai/gpt-oss-120b
LLM_MODEL = "openai/gpt-oss-120b"

MOIS_FR = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
    7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre",
}

SYSTEM_PROMPT = """Tu es l'assistant IA de l'application de prévision des ventes d'Ooredoo.

RÈGLES STRICTES À RESPECTER ABSOLUMENT :
1. Tu réponds UNIQUEMENT à partir du contexte fourni ci-dessous (extrait de la base de
   données réelle de l'entreprise). N'utilise pas de connaissances générales sur Ooredoo
   ou le marché télécom tunisien qui ne figureraient pas dans ce contexte.
2. Tu ne calcules et n'inventes JAMAIS de chiffres de prévision de ventes toi-même.
   Les prévisions sont produites exclusivement par un modèle de machine learning séparé
   (LightGBM). Si on te demande une prévision chiffrée que tu ne trouves pas dans le
   contexte, dis à l'utilisateur d'aller sur la page "Prévisions" de l'application.
3. Si l'information demandée n'est pas dans le contexte fourni, dis clairement que tu
   ne disposes pas de cette donnée — n'invente jamais une réponse plausible.
4. Réponds toujours en français, de façon claire, concise et compréhensible par un
   public non technique (managers, équipes commerciales).
5. Quand c'est pertinent, appuie tes réponses sur des chiffres précis tirés du contexte.
6. N'AVANCE JAMAIS de cause ou d'explication (Ramadan, Aïd, promotion, saisonnalité,
   effet concurrentiel, migration technologique, etc.) pour justifier une variation de
   ventes, SAUF si cette cause est EXPLICITEMENT mentionnée dans le contexte fourni pour
   le mois concerné. Par exemple, ne mentionne un "effet Ramadan" sur un mois que si le
   document de contexte de CE mois précis indique explicitement qu'il inclut le Ramadan.
   Si tu ignores la cause réelle d'une variation, dis simplement "la cause de cette
   variation n'est pas précisée dans les données disponibles" plutôt que de spéculer.
7. Quand tu produis un tableau Markdown : chaque ligne de données DOIT contenir exactement
   le même nombre de cellules que la ligne d'en-tête, et AUCUNE cellule ne doit être laissée
   vide (si tu n'as pas d'information pour une cellule, écris "-"). N'ajoute JAMAIS de ligne
   de commentaire, de note, ou de référence à une autre ligne à l'intérieur d'un tableau
   (par exemple, n'écris jamais une ligne du type "déjà listé ci-dessus" ou "voir plus haut")
   — chaque entité (région, produit, catégorie) n'apparaît qu'UNE SEULE FOIS dans un tableau,
   avec toutes ses colonnes remplies normalement.
"""


@st.cache_resource
def get_collection():
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)
    return client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_fn)


def retrieve_context(question: str, n_results: int = 6) -> list[str]:
    collection = get_collection()
    results = collection.query(query_texts=[question], n_results=n_results)
    return results["documents"][0]


def retrieve_context_for_month(year: int, month: int) -> list[str]:
    """
    Récupère le contexte pour un rapport mensuel par FILTRE EXACT sur les
    métadonnées (année/mois), plutôt que par recherche sémantique floue.
    Inclut aussi les données du mois précédent, pour permettre au LLM de
    faire une comparaison d'un mois sur l'autre dans le rapport.
    """
    collection = get_collection()
    docs = []

    def fetch_month(y: int, m: int) -> list[str]:
        month_docs = []
        for doc_type in ["national_monthly", "category_monthly", "region_monthly"]:
            result = collection.get(
                where={
                    "$and": [
                        {"type": {"$eq": doc_type}},
                        {"year": {"$eq": y}},
                        {"month": {"$eq": m}},
                    ]
                }
            )
            month_docs.extend(result["documents"])
        return month_docs

    docs.extend(fetch_month(year, month))

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    prev_docs = fetch_month(prev_year, prev_month)
    if prev_docs:
        docs.append(
            f"--- Données du mois précédent ({MOIS_FR[prev_month]} {prev_year}), "
            f"pour comparaison ---"
        )
        docs.extend(prev_docs)

    for doc_type in ["technology_yearly", "top_regions", "top_products",
                      "model_metrics", "business_assumptions"]:
        result = collection.get(where={"type": {"$eq": doc_type}})
        docs.extend(result["documents"])

    return docs


def ask_llm(
    question: str,
    chat_history: list[dict] | None = None,
    context_docs: list[str] | None = None,
    max_tokens: int = 800,
) -> tuple[str, list[str]]:
    """
    Retourne (réponse_du_llm, documents_utilisés_comme_contexte).
    context_docs : si fourni, on saute la recherche sémantique et on utilise
                   directement ces documents comme contexte (utilisé par les
                   rapports mensuels, où l'on connaît exactement le mois voulu).
    max_tokens : budget de génération. Les rapports (tableaux, plusieurs
                 sections) ont besoin de bien plus de place qu'une réponse
                 de chat classique -> generate_monthly_report() utilise une
                 valeur plus élevée que la valeur par défaut du chat.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return (
            "⚠️ Aucune clé API trouvée. Ajoutez `GROQ_API_KEY=...` dans votre "
            "fichier `.env` à la racine du projet, puis relancez l'application.",
            [],
        )

    if context_docs is None:
        context_docs = retrieve_context(question)
    context_text = "\n".join(f"- {d}" for d in context_docs)

    user_message = (
        f"Contexte extrait de la base de données Ooredoo :\n{context_text}\n\n"
        f"Question de l'utilisateur : {question}"
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(chat_history if chat_history else [])
    messages.append({"role": "user", "content": user_message})

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=LLM_MODEL,
        max_tokens=max_tokens,
        temperature=0.3,
        reasoning_effort="low",  # modèle de raisonnement : on limite l'effort de
                                  # "réflexion" interne pour laisser un maximum
                                  # de budget de tokens à la réponse elle-même
        messages=messages,
    )
    answer = response.choices[0].message.content
    return answer, context_docs


def generate_monthly_report(year: int, month: int) -> str:
    """Génère un rapport en langage naturel pour un mois donné, à partir du RAG."""
    context_docs = retrieve_context_for_month(year, month)

    mois_txt = MOIS_FR.get(month, str(month))
    question = (
        f"Génère un rapport de synthèse clair et structuré des ventes du mois de "
        f"{mois_txt} {year}, avec les chiffres clés, les tendances principales, "
        f"et une comparaison chiffrée avec le mois précédent (variation en unités "
        f"vendues et en chiffre d'affaires, en pourcentage). Structure le rapport "
        f"avec des sections courtes. Si aucune donnée n'est disponible pour ce mois "
        f"précis ou pour le mois précédent dans le contexte fourni, dis-le "
        f"clairement au lieu d'improviser.\n\n"
        f"Consignes de formatage des tableaux (à respecter strictement) : "
        f"chaque région, catégorie ou produit doit apparaître UNE SEULE FOIS par "
        f"tableau, avec toutes les colonnes remplies (jamais de cellule vide, "
        f"écris '-' si une valeur manque) ; n'ajoute aucune ligne de commentaire "
        f"ou de renvoi vers une autre ligne dans un tableau."
    )
    answer, _ = ask_llm(question, context_docs=context_docs, max_tokens=3000)
    return answer