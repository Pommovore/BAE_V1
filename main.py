# Fichier : 3_create_vector_store.py

# Installation des bibliothèques requises :
# pip install langchain sentence-transformers faiss-cpu
# faiss-cpu est la version de FAISS qui fonctionne sur le processeur (CPU).

import os
import pickle
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import FAISS

# --- CONFIGURATION ---
# --- CONFIGURATION ---
data_dir = 'data'
input_txt_path = os.path.join(data_dir, "rules_text.txt")  # Le fichier texte généré à l'étape 1
# Le fichier contenant nos morceaux de texte préparés
input_pickle_path = os.path.join(data_dir, "docs_chunks.pkl")  # Le nom du fichier de sauvegarde
# Le dossier où sera sauvegardée notre base de données vectorielle
vector_store_path =  os.path.join(data_dir, "faiss_index")

# --- SCRIPT DE VECTORISATION ET DE STOCKAGE ---

# 1. Charger les morceaux de texte (docs)
if not os.path.exists(input_pickle_path):
    print(f"Erreur : Le fichier '{input_pickle_path}' n'a pas été trouvé.")
    print("Veuillez d'abord exécuter le script de l'étape 2 pour créer et sauvegarder les documents.")
else:
    try:
        print(f"Chargement des documents depuis '{input_pickle_path}'...")
        with open(input_pickle_path, "rb") as f:
            docs = pickle.load(f)
        print(f"✅ {len(docs)} documents chargés avec succès.")

        # 2. Créer le modèle d'embedding
        # Nous utilisons un modèle open-source et performant de Sentence-Transformers.
        # LangChain le téléchargera automatiquement la première fois que vous l'utiliserez.
        print("\nInitialisation du modèle d'embedding (cela peut prendre un moment au premier lancement)...")
        embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        print("✅ Modèle d'embedding chargé.")

        # 3. Créer la base de données vectorielle (Vector Store)
        # Cette étape prend chaque document, calcule son embedding et le stocke dans FAISS.
        # C'est l'étape la plus longue du processus de préparation.
        print("\nCréation de la base de données vectorielle FAISS. Veuillez patienter...")
        db = FAISS.from_documents(docs, embeddings)
        print("✅ Base de données vectorielle créée en mémoire.")

        # 4. Sauvegarder la base de données sur le disque
        # Cela nous permettra de la recharger directement dans notre application finale
        # sans avoir à tout recalculer.
        db.save_local(vector_store_path)
        print(f"\n✅ La base de données a été sauvegardée dans le dossier : '{vector_store_path}'")
        print("\nVotre système est maintenant prêt pour l'étape finale : l'interrogation !")

    except Exception as e:
        print(f"\n❌ Une erreur est survenue : {e}")
