# -*- coding: utf-8 -*-
"""
build_knowledge_base.py

Transforme les données chiffrées (ventes, métriques du modèle) en documents
texte, puis les indexe dans une base vectorielle ChromaDB pour que
l'Assistant IA (RAG) puisse les retrouver et y répondre.

À exécuter :
  - une première fois avant d'utiliser l'Assistant IA
  - puis à chaque fois que les données ou le modèle sont mis à jour

    python build_knowledge_base.py

Note : la toute première exécution télécharge automatiquement un petit
modèle d'embedding (~80 Mo, gratuit, local, pas de clé API nécessaire),
ça peut prendre 1-2 minutes selon votre connexion.
"""

import json
import shutil
import os
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions

DATA_PATH = "data/ooredoo_sales_synthetic_2022_2025.csv"
MODEL_METADATA_PATH = "models/model_metadata.json"
VECTOR_STORE_PATH = "vector_store"
COLLECTION_NAME = "ooredoo_knowledge"

MOIS_FR = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
    7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre",
}


def build_documents(df: pd.DataFrame, metadata: dict) -> tuple[list[str], list[dict]]:
    documents = []
    metadatas = []

    # -------------------------------------------------------------
    # 1) Résumé mensuel national (toutes régions, tous produits)
    # -------------------------------------------------------------
    monthly = df.groupby(["year", "month"]).agg(
        quantity_sold=("quantity_sold", "sum"),
        revenue=("revenue", "sum"),
        ramadan=("ramadan", "max"),
        eid=("eid", "max"),
    ).reset_index()

    for _, r in monthly.iterrows():
        mois_txt = f"{MOIS_FR[int(r['month'])]} {int(r['year'])}"
        contexte_evt = []
        if r["ramadan"] == 1:
            contexte_evt.append("ce mois inclut une partie du Ramadan")
        if r["eid"] == 1:
            contexte_evt.append("ce mois inclut une fête de l'Aïd")
        contexte_txt = f" ({', '.join(contexte_evt)})" if contexte_evt else ""
        documents.append(
            f"Ventes nationales en {mois_txt}{contexte_txt} : "
            f"{r['quantity_sold']:.0f} unités vendues pour un chiffre d'affaires "
            f"total de {r['revenue']:.0f} DT (toutes régions et tous produits confondus)."
        )
        metadatas.append({"type": "national_monthly", "year": int(r["year"]), "month": int(r["month"])})

    # -------------------------------------------------------------
    # 2) Résumé mensuel par catégorie de produit
    # -------------------------------------------------------------
    monthly_cat = df.groupby(["year", "month", "product_category"]).agg(
        quantity_sold=("quantity_sold", "sum"), revenue=("revenue", "sum")
    ).reset_index()

    for _, r in monthly_cat.iterrows():
        mois_txt = f"{MOIS_FR[int(r['month'])]} {int(r['year'])}"
        documents.append(
            f"En {mois_txt}, la catégorie {r['product_category']} a représenté "
            f"{r['quantity_sold']:.0f} unités vendues pour {r['revenue']:.0f} DT de revenu."
        )
        metadatas.append({"type": "category_monthly", "year": int(r["year"]), "month": int(r["month"])})

    # -------------------------------------------------------------
    # 3) Résumé mensuel par région
    # -------------------------------------------------------------
    monthly_region = df.groupby(["year", "month", "region"]).agg(
        quantity_sold=("quantity_sold", "sum"), revenue=("revenue", "sum")
    ).reset_index()

    for _, r in monthly_region.iterrows():
        mois_txt = f"{MOIS_FR[int(r['month'])]} {int(r['year'])}"
        documents.append(
            f"En {mois_txt}, la région {r['region']} a vendu {r['quantity_sold']:.0f} "
            f"unités pour un chiffre d'affaires de {r['revenue']:.0f} DT."
        )
        metadatas.append({"type": "region_monthly", "year": int(r["year"]), "month": int(r["month"])})

    # -------------------------------------------------------------
    # 4) Résumé annuel par technologie (migration 4G/5G/xDSL/Fibre)
    # -------------------------------------------------------------
    yearly_tech = df.groupby(["year", "technology"])["quantity_sold"].sum().reset_index()
    for year in yearly_tech["year"].unique():
        sub = yearly_tech[yearly_tech["year"] == year]
        total = sub["quantity_sold"].sum()
        parts = [f"{row['technology']} : {row['quantity_sold']/total*100:.1f}%"
                 for _, row in sub.iterrows()]
        documents.append(
            f"En {int(year)}, la répartition des ventes par technologie était : "
            + ", ".join(parts) + "."
        )
        metadatas.append({"type": "technology_yearly", "year": int(year), "month": 0})

    # -------------------------------------------------------------
    # 5) Top régions et top produits (vue globale)
    # -------------------------------------------------------------
    top_regions = df.groupby("region")["revenue"].sum().sort_values(ascending=False).head(5)
    documents.append(
        "Les 5 régions générant le plus de chiffre d'affaires sur toute la période "
        "2022-2025 sont, dans l'ordre : "
        + ", ".join(f"{region} ({rev:.0f} DT)" for region, rev in top_regions.items()) + "."
    )
    metadatas.append({"type": "top_regions", "year": 0, "month": 0})

    top_products = df.groupby("product_name")["quantity_sold"].sum().sort_values(ascending=False).head(5)
    documents.append(
        "Les 5 produits les plus vendus en volume sur toute la période 2022-2025 sont : "
        + ", ".join(f"{p} ({q:.0f} unités)" for p, q in top_products.items()) + "."
    )
    metadatas.append({"type": "top_products", "year": 0, "month": 0})

    # -------------------------------------------------------------
    # 6) Métriques du modèle de prévision
    # -------------------------------------------------------------
    documents.append(
        f"Le modèle de prévision utilisé en production est un modèle LightGBM. "
        f"Il a été validé sur les 20% de données les plus récentes (période de test à "
        f"partir du {metadata['split_date']}), avec les métriques suivantes : "
        f"MAE (erreur absolue moyenne) = {metadata['MAE']} unités, "
        f"RMSE (racine de l'erreur quadratique moyenne) = {metadata['RMSE']} unités, "
        f"MAPE (erreur en pourcentage) = {metadata['MAPE_%']}%. "
        f"Le modèle a été entraîné sur {metadata['n_train']} lignes et testé sur "
        f"{metadata['n_test']} lignes."
    )
    metadatas.append({"type": "model_metrics", "year": 0, "month": 0})

    # -------------------------------------------------------------
    # 7) Hypothèses métier du dataset (contexte pour interpréter les résultats)
    # -------------------------------------------------------------
    documents.append(
        "Hypothèses métier prises en compte dans les données et le modèle : "
        "le Ramadan augmente généralement les ventes Mobile et Data ; "
        "les vacances d'été augmentent les ventes Internet Fixe ; "
        "les promotions augmentent en moyenne les ventes de 15 à 50% selon la remise ; "
        "la technologie 5G devient progressivement plus populaire entre 2022 et 2025 ; "
        "la technologie xDSL diminue progressivement au profit de la Fibre ; "
        "Mobile reste la catégorie de produit la plus vendue en volume ; "
        "certaines régions (Tunis, Sfax, Sousse) vendent structurellement plus que "
        "les régions moins peuplées ; les campagnes de la concurrence font généralement "
        "baisser les ventes d'environ 20%."
    )
    metadatas.append({"type": "business_assumptions", "year": 0, "month": 0})

    return documents, metadatas


def main():
    print("Chargement des données...")
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])

    with open(MODEL_METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print("Construction des documents texte...")
    documents, metadatas = build_documents(df, metadata)
    print(f"  -> {len(documents)} documents générés")

    # -------------------------------------------------------------
    # Réinitialiser le vector store (pour éviter les doublons si on
    # relance le script plusieurs fois)
    # -------------------------------------------------------------
    if os.path.exists(VECTOR_STORE_PATH):
        shutil.rmtree(VECTOR_STORE_PATH)

    print("Indexation dans ChromaDB (téléchargement du modèle d'embedding "
          "si première utilisation)...")
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)
    collection = client.create_collection(name=COLLECTION_NAME, embedding_function=embedding_fn)

    ids = [f"doc_{i}" for i in range(len(documents))]
    # ChromaDB limite la taille des lots -> on indexe par paquets de 100
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
            ids=ids[i:i + batch_size],
        )
        print(f"  -> {min(i + batch_size, len(documents))}/{len(documents)} documents indexés")

    print(f"\nTerminé ! Base de connaissances créée dans '{VECTOR_STORE_PATH}/' "
          f"avec {len(documents)} documents.")


if __name__ == "__main__":
    main()