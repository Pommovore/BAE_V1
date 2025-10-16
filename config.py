#!/usr/bin/env python
# coding: utf-8
"""
Created on 25 / 01 / 2022

@author: AJCO7475
"""
import os
import sys
import yaml
import logging
import platform

logger = logging.getLogger("BAX")
logging.basicConfig()


# --------------------------------- CLASSE bcolors ---------------------------
# bcolors : "embeliissements" des logs
class bcolors:
    HEADER = '\033[95m'
    RED = '\033[31m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    YELLOW = '\033[33m'
    PURPLE = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BLACK = '\033[30m'
    LIGHT_RED = '\033[91m'
    LIGHT_GREEN = '\033[92m'
    LIGHT_YELLOW = '\033[93m'
    LIGHT_BLUE = '\033[94m'
    LIGHT_MAGENTA = '\033[95m'
    LIGHT_CYAN = '\033[96m'
    LIGHT_GRAY = '\033[37m'
    DARK_GRAY = '\033[90m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    INPUT = OKCYAN
    OUTPUT = BG_CYAN


# =============================================================================
# load_config
#
# - charger les fichiers de configuration et le returner dans une variable
# - initialiser le logger
# =============================================================================
def load_config(cfg_filename=None, cfg_dir_filename=None, log_level=None, log_file=None):
    global logger
    #
    # chargement du fichier avec les configurations des repertoires, dépendant de la machine
    #
    if cfg_dir_filename is None:
        cfg_dir_filename = os.path.join("config", platform.uname()[1] + "_cfg.yaml")
    try:
        yaml_file = open(cfg_dir_filename, 'r')
    except IOError:
        print(f"config file '{cfg_dir_filename}' not found on this ({platform.uname()[1]}) machine, "
              f"please check the file exists and is placed in 'config' directory")
        sys.exit(1)
    app_dir_config = yaml.load(yaml_file, Loader=yaml.Loader)
    if app_dir_config is None:
        print(f"Impossible to load parameters from config file '{cfg_dir_filename}'")
        sys.exit(1)
    #
    # chargement du fichier avec les autres paramètres de configuration
    #
    if cfg_filename is None:
        cfg_filename = os.path.join('config', 'cfg.yaml')
    try:
        yaml_file = open(cfg_filename, 'r')
    except IOError:
        print(f"config file '{cfg_filename}' not found on this ({platform.uname()[1]}) machine, "
              f"please check the file exists and is placed in 'config' directory")
        sys.exit(1)
    app_config = yaml.load(yaml_file, Loader=yaml.Loader)
    app_config.update(app_dir_config)
    if app_config is None:
        print(f"Impossible to load parameters from config file '{cfg_filename}'")
        sys.exit(1)
    # fixer le niveau de verbosité depuis le fichier de configuration s'il n'a pas été précisé sur la ligne de commande
    if log_level is not None:
        print(f"INFO: log level is set to '{log_level}' by user")
    else:
        if app_config["log_level"] is not None:
            print(f"INFO: log level is set to '{app_config["log_level"]}' in '{cfg_filename}' file")
            log_level = app_config["log_level"]
        else:
            log_level = os.environ.get("LOGLEVEL", None)
            if log_level is not None:
                print(f"INFO: log level is set to '{log_level}' in LOGLEVEL environment variable")
    # à moins que ce soit spécifié autrement le niveau de log est DEBUG
    if log_level == "CRITICAL":
        logger.setLevel(logging.CRITICAL)
    elif log_level == "ERROR":
        logger.setLevel(logging.ERROR)
    elif log_level == "WARNING":
        logger.setLevel(logging.WARNING)
    elif log_level == "INFO":
        logger.setLevel(logging.INFO)
    else:
        if log_level is None:
            print("INFO: log level is set to 'DEBUG' by default")
        elif log_level != "DEBUG":
            print(
                "INFO: specified log_level value ({}) is incorrect, use CRITICAL, ERROR, WARNING, INFO or DEBUG. log "
                "level is set to 'DEBUG' by default".format(log_level))
        logger.setLevel(logging.DEBUG)
    if log_file is not None:
        logs_filename = os.path.join(app_config["output_dir"], log_file)
        print(f"INFO: logs go to file '{logs_filename}' ...")
        logging.basicConfig(filename=logs_filename, level=log_level)
    else:
        print("INFO: logs go screen")
        logging.basicConfig(level=log_level)
    return app_config


# =============================================================================
# open_outstream
# =============================================================================
def open_outstream(output_file=None, res_dir=None, encoding='utf-8'):
    outstream = sys.stdout
    if output_file is not None and res_dir is not None:
        filename = os.path.join(res_dir, output_file)
        outstream = open(filename, 'w', encoding=encoding)
        logger.debug(f"writing results to '{filename}' ...")
    return outstream


# =============================================================================
# close_outstream
# =============================================================================
def close_outstream(outstream, output_file=None):
    if output_file is not None:
        outstream.close()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    load_config()
