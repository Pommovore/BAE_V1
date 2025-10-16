# Installation de la bibliothèque requise :
# Dans votre terminal, exécutez la commande suivante :
# pip install langchain

import os  # Utilisé pour vérifier si le fichier existe
import sys
import getopt

from config import load_config, bcolors, logger

import pickle  # On importe le module pickle

# Importation du "Text Splitter" de LangChain
from langchain.text_splitter import RecursiveCharacterTextSplitter


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
                                   ["cfg=", "ll=", "lf=", "l="])
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
    # Le nom du fichier texte à morceler
    input_txt_path = os.path.join(data_dir, rules_file.replace('.pdf', '.txt'))
    # Le fichier contenant nos morceaux de texte préparés
    output_pickle_path = os.path.join(data_dir, rules_file.replace('.pdf', '_chunks.pkl'))
    # --- check visuel
    logger.info(f"data_dir={bcolors.INPUT}{data_dir}{bcolors.ENDC}")
    logger.info(f"language={bcolors.INPUT}{language}{bcolors.ENDC}")
    logger.info(f"input_txt_path={bcolors.INPUT}{input_txt_path}{bcolors.ENDC}")
    logger.info(f"output_pickle_path={bcolors.OUTPUT}{output_pickle_path}{bcolors.ENDC}")

    # --- SCRIPT DE DÉCOUPAGE ---

    # 1. Vérifier si le fichier texte existe
    if not os.path.exists(input_txt_path):
        logger.error(f"Erreur : Le fichier '{input_txt_path}' n'a pas été trouvé.")
        logger.error("Veuillez d'abord exécuter le script de l'étape 1 pour extraire le texte du PDF.")
    else:
        try:
            logger.info(f"Lecture du fichier '{input_txt_path}'...")
            with open(input_txt_path, 'r', encoding='utf-8') as f:
                full_text = f.read()

            logger.info("Le fichier a été lu avec succès. Début du découpage en morceaux...")

            # 2. Création de l'instance du Text Splitter
            # C'est ici que la magie opère.
            text_splitter = RecursiveCharacterTextSplitter(
                # La taille de chaque morceau (chunk). 1000 est une bonne valeur de départ.
                chunk_size=1000,

                # Un chevauchement entre les morceaux pour ne pas perdre de contexte.
                # Si un morceau se termine au milieu d'une phrase importante,
                # le début de cette phrase sera dans le morceau précédent.
                chunk_overlap=150,

                # On conserve la notion de paragraphes, très utile pour le contexte.
                separators=["\n\n", "\n", " ", ""]
            )

            # 3. Découpage du document
            # La méthode create_documents prend une liste de textes.
            # Comme nous n'avons qu'un seul gros texte, nous le mettons dans une liste.
            # LangChain va automatiquement stocker le contenu et des métadonnées.
            docs = text_splitter.create_documents([full_text])

            # 4. Affichage des résultats pour vérification
            logger.info("\n✅ Découpage terminé !")
            logger.info(f"Le document a été divisé en {len(docs)} morceaux (chunks).")

            # Affichons un aperçu pour voir à quoi ça ressemble
            logger.info("\n--- Aperçu du premier morceau (Chunk 1) ---")
            logger.info(docs[0].page_content)
            logger.info("\n-------------------------------------------")

            logger.info(f"\nTaille du premier morceau : {len(docs[0].page_content)} caractères.")

            # Affichage du deuxième morceau pour voir le chevauchement
            if len(docs) > 1:
                logger.info("\n--- Aperçu du début du deuxième morceau (Chunk 2) ---")
                logger.info(docs[1].page_content[:200] + "...")  # Affiche les 200 premiers caractères
                logger.info("\n-------------------------------------------------")

            # --- PARTIE 2 : SAUVEGARDE AVEC PICKLE ---
            logger.info(f"\nSauvegarde des morceaux dans le fichier '{output_pickle_path}'...")

            # On ouvre le fichier en mode "write binary" (wb)
            with open(output_pickle_path, "wb") as f:
                pickle.dump(docs, f)  # On "dumpe" (verse) notre variable docs dans le fichier

            logger.info("✅ Sauvegarde terminée avec succès !")

        except Exception as e:
            logger.error(f"\n❌ Une erreur est survenue : {e}")
