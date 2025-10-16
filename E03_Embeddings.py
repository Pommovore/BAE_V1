# Fichier : 3_create_vector_store.py

# Installation des bibliothèques requises :
# pip install langchain sentence-transformers faiss-cpu
# faiss-cpu est la version de FAISS qui fonctionne sur le processeur (CPU).

import os
import sys
import getopt

import pickle
# old : from langchain.embeddings import SentenceTransformerEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
# old : from langchain.vectorstores import FAISS
from langchain_community.vectorstores import FAISS
from config import load_config, bcolors, logger


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
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h",
                                   ["cfg=", "ll=", "lf=", "lc=", "in=",
                                    "id=", "if=", "od=", "of=", "rf=", "out=", "sep="])
    except getopt.GetoptError as err:
        logger.error(err)
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt in "--cfg":
            cfg_filename = arg
        elif opt in "--ll":
            if arg in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]:
                log_level = arg
        elif opt in "--lf":
            log_file = arg

    # --- CONFIGURATION ---
    app_config = load_config(cfg_filename=cfg_filename)
    data_dir = app_config['data_dir']
    language = app_config['language']
    rules_file = app_config['rules_' + language + '_file']
    embeddings_model_name = app_config['embeddings_' + language + '_model_name']
    # Le fichier contenant nos morceaux de texte préparés
    input_pickle_path = os.path.join(data_dir, rules_file.replace('.pdf', '_chunks.pkl'))
    # Le dossier où sera sauvegardée notre base de données vectorielle
    vector_store_path = os.path.join(data_dir, "faiss_index_" + language)
    # --- check visuel
    logger.info(f"data_dir={bcolors.INPUT}{data_dir}{bcolors.ENDC}")
    logger.info(f"language={bcolors.INPUT}{language}{bcolors.ENDC}")
    logger.info(f"input_pickle_path={bcolors.INPUT}{input_pickle_path}{bcolors.ENDC}")
    logger.info(f"embeddings_model_name={bcolors.INPUT}{embeddings_model_name}{bcolors.ENDC}")
    logger.info(f"vector_store_path={bcolors.OUTPUT}{vector_store_path}{bcolors.ENDC}")

    # --- SCRIPT DE VECTORISATION ET DE STOCKAGE ---

    # 1. Charger les morceaux de texte (docs)
    if not os.path.exists(input_pickle_path):
        logger.info(f"Erreur : Le fichier '{input_pickle_path}' n'a pas été trouvé.")
        logger.info("Veuillez d'abord exécuter le script de l'étape 2 pour créer et sauvegarder les documents.")
    else:
        try:
            logger.info(f"Chargement des documents depuis '{input_pickle_path}'...")
            with open(input_pickle_path, "rb") as f:
                docs = pickle.load(f)
            logger.info(f"✅ {len(docs)} documents chargés avec succès.")

            # 2. Créer le modèle d'embedding
            # Nous utilisons un modèle open-source et performant de Sentence-Transformers.
            # LangChain le téléchargera automatiquement la première fois que vous l'utiliserez.
            logger.info(f"\nInitialisation du modèle d'embedding : {bcolors.INPUT}{embeddings_model_name}{bcolors.ENDC} "
                        f"(cela peut prendre un moment au premier lancement)...")
            # old : embeddings = SentenceTransformerEmbeddings(model_name=embeddings_model_name)
            embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
            logger.info("✅ Modèle d'embedding chargé.")

            # 3. Créer la base de données vectorielle (Vector Store)
            # Cette étape prend chaque document, calcule son embedding et le stocke dans FAISS.
            # C'est l'étape la plus longue du processus de préparation.
            logger.info("\nCréation de la base de données vectorielle FAISS. Veuillez patienter...")
            db = FAISS.from_documents(docs, embeddings)
            logger.info("✅ Base de données vectorielle créée en mémoire.")

            # 4. Sauvegarder la base de données sur le disque
            # Cela nous permettra de la recharger directement dans notre application finale
            # sans avoir à tout recalculer.
            db.save_local(vector_store_path)
            logger.info(f"\n✅ La base de données a été sauvegardée dans le dossier : '{vector_store_path}'")
            logger.info("\nVotre système est maintenant prêt pour l'étape finale : l'interrogation !")

        except Exception as e:
            logger.error(f"\n❌ Une erreur est survenue : {e}")
