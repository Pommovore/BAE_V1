# Fichier : 4_query_system_OLLAMA.py

# Installation des bibliothèques requises :
# pip install langchain langchain-community faiss-cpu sentence-transformers

import os
import sys
import getopt
from config import load_config, bcolors, logger

# La bibliothèque python-dotenv n'est plus nécessaire !
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
# old : from langchain_community.chat_models import ChatOllama
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA

import pickle
# old : from langchain.embeddings import SentenceTransformerEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from deep_translator import GoogleTranslator

import subprocess

# =============================================================================
# lancer_LLM
# =============================================================================
def lancer_LLM(llm_name):

    # La commande et ses arguments doivent être passés sous forme de liste
    commande = ["ollama", "pull", llm_name]

    try:
        # Exécute la commande et capture la sortie
        resultat = subprocess.run(
            commande,
            capture_output=True,  # Capture stdout et stderr
            text=True,  # Décode la sortie en texte (str) au lieu de bytes
            check=True  # Lève une exception si le code de retour n'est pas 0 (erreur)
        )

        # Affiche le résultat
        print("--- Sortie Standard (stdout) ---")
        print(resultat.stdout)

        print("--- Code de retour ---")
        print(resultat.returncode)

    except subprocess.CalledProcessError as e:
        # Gère le cas où la commande échoue (code de retour non nul)
        print(f"La commande a échoué avec le code de retour {e.returncode}")
        print(f"Erreur (stderr) :\n{e.stderr}")

    except FileNotFoundError:
        # Gère le cas où l'exécutable (ici 'ls') n'est pas trouvé
        print(f"L'exécutable '{commande[0]}' n'a pas été trouvé.")

# =============================================================================
# usage
# =============================================================================
def usage():
    """
    afficher le message d'aide

    :return:
    """
    script_name = os.path.basename(__file__)
    print(f"{script_name}  : () facultative item, <> : mandatory item\n"
          "    (--cfg=<filename>)\n"
          "    (--lf=<log file>)\n"
          "    (--ll=<log level:CRITICAL|ERROR|WARNING|INFO|DEBUG>)\n"
          "    (-h : this help)\n")


# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    language = None
    cfg_filename = None
    # --- CONFIGURATION ---
    app_config = load_config()
    data_dir = app_config['data_dir']
    language = app_config['language']
    rules_file = app_config['rules_' + language + '_file']
    embeddings_model_name = app_config['embeddings_' + language + '_model_name']
    llm_model_name = app_config['llm_' + language + '_model_name']
    llm_temperature = float(app_config['llm_temperature'])

    # Le dossier où sera sauvegardée la base de données vectorielle
    vector_store_path = os.path.join(data_dir, "faiss_index_" + language)
    # --- check visuel
    logger.info(f"data_dir={bcolors.INPUT}{data_dir}{bcolors.ENDC}")
    logger.info(f"language={bcolors.INPUT}{language}{bcolors.ENDC}")
    logger.info(f"embeddings_model_name={bcolors.INPUT}{embeddings_model_name}{bcolors.ENDC}")
    logger.info(f"llm_model_name={bcolors.INPUT}{llm_model_name}{bcolors.ENDC}")
    logger.info(f"vector_store_path={bcolors.INPUT}{vector_store_path}{bcolors.ENDC}")

    logger.info("--- Initialisation du système expert Bolt Action avec OLLAMA...")
    logger.info(f"-> Chargement du modèle '{llm_model_name}'...")
    lancer_LLM(llm_model_name)

    logger.info(f"-> Chargement du modèle d'embedding depuis '{embeddings_model_name}'...")
    # old : embeddings = SentenceTransformerEmbeddings(model_name=embeddings_model_name)
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

    logger.info(f"-> Chargement de la base de données depuis '{vector_store_path}'...")
    db = FAISS.load_local(vector_store_path, embeddings, allow_dangerous_deserialization=True)

    # On initialise le LLM local avec Ollama
    logger.info("-> Initialisation du LLM local (via Ollama)...")
    # Assurez-vous d'avoir fait "wh" dans votre terminal avant.
    # Vous pouvez remplacer "llama3" par "mistral" si vous préférez.
    llm = ChatOllama(model=llm_model_name, temperature=llm_temperature)

    # --- CRÉATION DE LA CHAÎNE RAG ---

    retriever = db.as_retriever(search_kwargs={'k': 4})

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )

    logger.info("\n✅ Système prêt ! Posez vos questions sur les règles de Bolt Action.")
    logger.info("   (Tapez 'quitter' ou 'exit' pour arrêter)\n")

    # --- BOUCLE INTERACTIVE (inchangée) ---

    while True:
        user_question_fr = input("Votre question (en français) : ")
        if user_question_fr.lower() in ["quitter", "exit"]:
            print("Fin du programme.")
            break
        if not user_question_fr.strip():
            continue

        print("\n-> Traduction de la question en anglais...")
        try:
            user_question_en = GoogleTranslator(source='auto', target='en').translate(user_question_fr)
            print(f"   Question traduite : \"{user_question_en}\"")
        except Exception as e:
            print(f"Erreur de traduction de la question : {e}")
            continue

        logger.info(f"\n--- lancemenent de la requete : {user_question_en.upper()} ---")
        result = qa_chain.invoke({"query": user_question_en})
        answer_en = result['result']

        print("-> Traduction de la réponse en français...")
        try:
            answer_fr = GoogleTranslator(source='auto', target='fr').translate(answer_en)
        except Exception as e:
            print(f"Erreur de traduction de la réponse : {e}")
            answer_fr = "Traduction impossible."

        print("\n--- Réponse en Anglais / English Answer ---")
        print(answer_en)
        print("------------------------------------------\n")

        print("--- Réponse en Français / French Answer ---")
        print(answer_fr)
        print("-----------------------------------------\n")

        print("--- Sources utilisées (en anglais) ---")
        for i, source in enumerate(result['source_documents']):
            print(f"Source {i + 1}:\n\"{source.page_content[:300]}...\"\n")
        print("------------------------------------\n")
