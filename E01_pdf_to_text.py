# Installation de la bibliothèque requise :
# Dans votre terminal, exécutez la commande suivante :
# pip install pypdf

import os  # Utilisé pour vérifier si le fichier existe
import sys
import time  # Juste pour l'exemple, pour voir la mise à jour
import getopt
import re
# PDF loaders
import pypdf
from langchain_community.document_loaders import UnstructuredPDFLoader

from config import load_config, bcolors, logger

# =============================================================================
# format_text_to_markdown
# =============================================================================
def format_text_to_markdown(raw_text: str) -> str:
    """
    Nettoie le texte PDF, supprime le bruit et applique un formatage Markdown
    pour améliorer la structure pour les applications RAG.
    """

    # 1. NETTOYAGE PRÉLIMINAIRE ET SUPPRESSION DU BRUIT CONNU

    # Suppression des identifiants de source (spécifiques à votre input)
    text = re.sub(r'\+\]', '', raw_text)

    bruit_patterns = [
        # Motifs de pied/en-tête de page liés à la mise en page
        r'BOLT 3rd Edition Layouts Correx\.indd \d+\s*BOLT 3rd Edition Layouts Correx\.indd \d+',
        r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}( \d{2}/\d{2}/\d{4} \d{2}:\d{2})?',
        r'\n\s*Bolt Action V3\s*\n',
        r'\n\s*\d{1,3}\s*Bolt Action V3\s*\n',
        r'\n\s*44mm if 2 lines\s*\n',

        # Numéros de page isolés ou en marge
        r'^\s*\d{1,3}\s*$',
        r'\n\s*\d{1,3}\s*$',  # Numéro de page en fin de ligne après le nettoyage initial
    ]

    for pattern in bruit_patterns:
        text = re.sub(pattern, '\n', text, flags=re.MULTILINE | re.IGNORECASE)

    # 2. RECONSTRUCTION DE LA STRUCTURE EN MARKDOWN (Titres)

    lines = text.split('\n')
    markdown_lines = []

    # Titres majeurs (Chapitres, Sections principales)
    major_titles = [
        "INTRODUCTION", "CONTENTS", "WARGAMES AND HISTORY", "BASIC SUPPLIES",
        "CONVENTIONS OF WAR", "UNITS", "THE TURN", "ORDERS", "MOVEMENT",
        "SHOOTING", "WEAPONS", "CLOSE QUARTERS", "HEADQUARTERS", "ARTILLERY",
        "VEHICLES", "BUILDINGS", "ARRANGING A GAME OF BOLT ACTION", "FORCE SELECTION",
        "ARMY LISTS", "OPTIONAL RULES", "COMMON TRANSPORT VEHICLES", "RULES SUMMARY",
        "CREDITS", "INDEX",
    ]

    # Titres des Listes d'Armées
    army_list_titles = [
        "GERMANY", "UNITED STATES", "GREAT BRITAIN", "SOVIET UNION",
        "IMPERIAL JAPAN",
    ]

    # Détection et conversion des lignes en titres Markdown
    for line in lines:
        stripped_line = line.strip()

        if not stripped_line:
            markdown_lines.append(line)
            continue

        # Titres de Niveau 1 ou 2 (Gros blocs)
        if stripped_line in major_titles:
            markdown_lines.append(f'\n## {stripped_line}\n')
        elif stripped_line in army_list_titles:
            markdown_lines.append(f'\n## ARMIES OF {stripped_line}\n')

        # Titres de Niveau 3 (Sous-sections, souvent Capitales au début de l'extrait)
        # Ex: FALL WEISS – THE INVASION OF POLAND, SEPTEMBER 1939
        elif stripped_line.isupper() and len(stripped_line) < 70 and not stripped_line.isdigit():
            # Vérifie si la ligne contient plus de 3 mots, sinon c'est potentiellement un bruit ou un titre très court
            if len(stripped_line.split()) > 3:
                markdown_lines.append(f'\n### {stripped_line}\n')
            else:
                # Si le titre est court et n'est pas un titre principal, le laisser en texte normal pour l'instant
                markdown_lines.append(line)

        # Lignes normales
        else:
            markdown_lines.append(line)

    text = '\n'.join(markdown_lines)

    # 3. NETTOYAGE FINAL (Espacement et cohérence)

    # Remplacement des sauts de ligne multiples (après application des titres)
    text = re.sub(r'\n{2,}', '\n\n', text).strip()

    # Remplacement des espaces multiples par un seul
    text = re.sub(r'[ \t]+', ' ', text)

    # Remplacement des espaces multiples autour des titres (s'assure qu'ils sont bien centrés/isolés)
    text = re.sub(r'\n\s*## ', '\n## ', text)
    text = re.sub(r' ##\s*\n', ' ##\n', text)
    text = re.sub(r'\n\s*### ', '\n### ', text)
    text = re.sub(r' ###\s*\n', ' ###\n', text)

    # Nettoyage des lignes vides inutiles
    text = re.sub(r'\n\n\n+', '\n\n', text)

    return text


# =============================================================================
# nettoyage_raw_text
# =============================================================================
def nettoyage_raw_text(input_raw_txt_file, output_clean_txt_file=None):
    try:
        # Lecture du fichier texte brut
        with open(input_raw_txt_file, 'r', encoding='utf-8') as f:
            texte = f.read()

        # --- ÉTAPE 1 : Nettoyages globaux avec Regex (sur tout le texte) ---

        # Règle 1 : Supprime les lignes de métadonnées d'exportation (InDesign)
        texte = re.sub(r'^BOLT 3rd Edition Layouts Correx\.indd.*$', '', texte, flags=re.MULTILINE)

        # Règle 2 : Supprime les césures avec tiret pour recoller les mots
        texte = re.sub(r'-\n', '', texte)

        # --- ÉTAPE 2 : Traitement ligne par ligne pour la logique fine ---

        lines = texte.split('\n')
        repaired_lines = []

        # Liste des ponctuations qui marquent une fin de phrase ou d'idée
        end_of_line_punctuation = ('.', '!', '?', ':', ')', ']', '"')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Règle 3 : Supprime les bruits spécifiques restants sur chaque ligne
            # Supprime les pieds de page simples comme "Bolt Action V3"
            line = re.sub(r'^Bolt Action V3$', '', line)
            # Supprime les en-têtes complexes comme "RULES SUMMARY 311" ou "312 RULES SUMMARY"
            line = re.sub(r'^(RULES SUMMARY|BOLT ACTION)\s+\d+.*$', '', line)
            line = re.sub(r'^\d+\s+(RULES SUMMARY|BOLT ACTION).*$', '', line)
            # Supprime les légendes d'images (marquées par , , etc.)
            line = re.sub(r'^[].*$', '', line)

            # S'assure que la ligne n'est pas vide après nettoyage
            line = line.strip()
            if not line:
                continue

            # Règle 4 : Formate les titres en majuscules
            # Si une ligne est en majuscules et courte, on la traite comme un titre
            if line.isupper() and len(line.split()) < 7 and not any(char.isdigit() for char in line):
                # Formatage en titre Markdown pour donner du sens à la structure
                formatted_title = f"\n## {line.title()}\n"
                repaired_lines.append(formatted_title)
                continue  # On passe à la ligne suivante

            # Règle 5 : Fusionne les lignes de paragraphes coupées (césures implicites)
            # C'est la règle la plus importante pour la lisibilité
            if (repaired_lines and
                    not repaired_lines[-1].strip().endswith(end_of_line_punctuation) and
                    not repaired_lines[-1].strip().endswith('##') and
                    line and line[0].islower()):
                # La ligne précédente ne se termine pas -> on fusionne
                repaired_lines[-1] += ' ' + line
            else:
                # Sinon, c'est une nouvelle ligne
                repaired_lines.append(line)

        # Reconstitue le texte à partir des lignes réparées
        final_texte = "\n".join(repaired_lines)

        # Règle 6 : Normalise les sauts de ligne pour une meilleure lisibilité
        final_texte = re.sub(r'\n\s*\n+', '\n\n', final_texte)

        # --- SAUVEGARDE DU FICHIER PROPRE ---
        with open(output_clean_txt_file, 'w', encoding='utf-8') as f:
            f.write(final_texte)

        print(
            f"✅ Nettoyage final terminé. Le fichier propre '{bcolors.OUTPUT}{output_clean_txt_file}{bcolors.ENDC}' a été créé.")

    except FileNotFoundError:
        print(f"Erreur : Le fichier d'entrée '{input_raw_txt_file}' n'a pas été trouvé.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")


# =============================================================================
# extraction_pypdf
# =============================================================================
def extraction_pypdf(pdf_file_path, output_raw_txt_file, output_clean_txt_file):
    try:
        logger.info(f"Ouverture du fichier PDF '{pdf_file_path}'...")
        #
        # Ouvre le fichier PDF en mode lecture binaire ('rb')
        with open(pdf_file_path, 'rb') as input_pdf_file:
            # Crée un objet lecteur pour le PDF
            reader = pypdf.PdfReader(input_pdf_file)
            #
            # Initialise une chaîne de caractères vide pour stocker tout le texte
            full_text = ""
            num_pages = len(reader.pages)
            logger.info(f"Le document contient {num_pages} pages. Extraction en cours...")
            #
            # Boucle sur chaque page du document
            for page_num, page in enumerate(reader.pages):
                # Extrait le texte de la page actuelle
                texte = page.extract_text()
                if texte:
                    # Ajoute le texte de la page au texte complet
                    full_text += texte + "\n"  # Ajoute un saut de ligne entre les pages

                # Affiche la progression
                print(f"\r  - Extraction en cours... Page {page_num + 1}/{num_pages}", end="")
        #
        # Sauvegarde du texte extrait dans un fichier .txt
        logger.info(f"\nSauvegarde du texte extrait dans '{output_raw_txt_file}'...")
        with open(output_raw_txt_file, 'w', encoding='utf-8') as output_file:
            output_file.write(full_text)

        logger.info("\n✅ Succès ! Le texte des règles a été extrait et sauvegardé.")
        logger.info(f"Le fichier '{output_raw_txt_file}' est prêt pour le nettoyage.")
    except Exception as e:
        logger.error(f"\n❌ Une erreur est survenue : {e}")
    logger.info("\n" + "-" * 80)
    #
    # nettoyage du texte brut
    nettoyage_raw_text(output_raw_txt_file, output_clean_txt_file)


# =============================================================================
# extraction_unstructured
# =============================================================================
def extraction_unstructured(pdf_file_path, output_raw_txt_file, output_clean_txt_file):

        # --- 1. Initialiser le Loader ---
    # Nous utilisons le mode par défaut (partitioning) pour une extraction de texte structurée.
    # 'strategy="auto"' permet à Unstructured de choisir la meilleure méthode (rapide ou plus détaillée)
    loader = UnstructuredPDFLoader(
        file_path=pdf_file_path,
        mode="paged"  # Optionnel : traite le document page par page
    )

    # --- 2. Charger et Extraire les Documents ---
    # La méthode .load() exécute l'extraction et retourne une liste d'objets 'Document'.
    # Chaque objet Document contient le texte extrait (page_content) et des metadata.
    try:
        print(f"Chargement du fichier '{bcolors.INPUT}{pdf_file_path}{bcolors.ENDC}' ...")
        documents = loader.load()
    except FileNotFoundError:
        print(f"Erreur : Le fichier {pdf_file_path} n'a pas été trouvé.")
        documents = []

    # --- 3. Combiner le Texte Brut ---
    # Pour obtenir le texte brut complet du PDF, nous concaténons le contenu de toutes les pages/documents.
    full_text = ""
    if documents:
        nr_doc = 0
        for doc in documents:
            # Ajoute le contenu de la page/chunk, suivi d'une double ligne pour la séparation
            full_text += doc.page_content + "\n\n"
            # Affiche la progression
            nr_doc = nr_doc + 1
            print(f"\r  - Extraction en cours... Doc {nr_doc}/{len(documents)}", end="")
        print("✅ Texte extrait avec succès (aperçu) :")
        print("-" * 30)
        print(full_text[:100] + "...")  # Affiche les 1500 premiers caractères
        print("-" * 30)
        print(f"Nombre total de caractères extraits : {len(full_text)}")

    else:
        print("❌ Aucun contenu n'a pu être chargé.")
    #
    # sauvegarde du texte brut
    with open(output_raw_txt_file, 'w', encoding='utf-8') as output_file:
        output_file.write(full_text)
    #
    # nettoyage du texte brut
    # nettoyage_raw_text(output_raw_txt_file, output_clean_txt_file)
    with open(output_raw_txt_file, 'r', encoding='utf-8') as f:
        raw_texte = f.read()
    clean_texte = format_text_to_markdown(raw_texte)
    with open(output_clean_txt_file, 'w', encoding='utf-8') as output_file:
        output_file.write(clean_texte)

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
    # Localisation du fichier PDF de règles
    i_pdf_file = os.path.join(data_dir, rules_file)
    # Le nom du fichier texte extrait du PDF (brut et final)
    o_raw_txt_file = os.path.join(data_dir, rules_file.replace('.pdf', '_raw.txt'))
    o_clean_txt_file = os.path.join(data_dir, rules_file.replace('.pdf', '.txt'))
    # --- check visuel
    logger.info(f"data_dir={bcolors.INPUT}{data_dir}{bcolors.ENDC}")
    logger.info(f"language={bcolors.INPUT}{language}{bcolors.ENDC}")
    logger.info(f"rules_file={bcolors.INPUT}{rules_file}{bcolors.ENDC}")
    logger.info(f"pdf_file_path={bcolors.INPUT}{i_pdf_file}{bcolors.ENDC}")
    logger.info(f"output_raw_txt_path={bcolors.OUTPUT}{o_raw_txt_file}{bcolors.ENDC}")
    logger.info(f"output_txt_path={bcolors.OUTPUT}{o_clean_txt_file}{bcolors.ENDC}")

    # --- SCRIPT D'EXTRACTION ---

    # 1. Vérifier si le fichier PDF existe avant de continuer
    if not os.path.exists(i_pdf_file):
        logger.info(f"Erreur : Le fichier '{i_pdf_file}' n'a pas été trouvé.")
        logger.info("Veuillez vous assurer que le fichier PDF des règles se trouve dans le même dossier que ce script.")
    else:
        print(f"Lancement du nettoyage final du fichier {bcolors.INPUT}'{i_pdf_file}'{bcolors.ENDC}...")
        if app_config['pdf_reader'] == 'pypdf':
            extraction_pypdf(i_pdf_file, o_raw_txt_file, o_clean_txt_file)
        elif app_config['pdf_reader'] == 'unstructured':
            extraction_unstructured(i_pdf_file, o_raw_txt_file, o_clean_txt_file)