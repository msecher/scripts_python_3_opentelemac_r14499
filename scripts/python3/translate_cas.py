#!/usr/bin/env python3
"""@author TELEMAC-MASCARET Consortium

@brief Run the partiotionning step
"""
# _____          ___________________________________________________
# ____/ Imports /__________________________________________________/
#
import sys
from os import path
import argparse
# ~~> dependencies towards other pytel/modules
from config import add_config_argument, update_config, CFGS
from execution.telemac_cas import TelemacCas
from utils.exceptions import TelemacException


def main():
    """ Main function of partel.py """
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# ~~ Reads config file ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    print('\n\nLoading Options and Configurations\n'+72*'~'+'\n')
    parser = argparse.ArgumentParser(
        description='Translate a keyword')
    parser = add_config_argument(parser)
    parser.add_argument(
        "module",
        choices=['postel3d', 'telemac2d', 'telemac3d', 'tomawac', 'artemis',
                 'sisyphe', 'waqtel', 'khione', 'stbtel'],
        help="Name of the module for which to translate")
    parser.add_argument(
        "cas_file",
        help="Name of the steering file to translatefile to be partitionned")
    args = parser.parse_args()

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# ~~~~ Environment ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    update_config(args)
    cfg = CFGS.configs[CFGS.cfgname]
    CFGS.compute_execution_info()

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # Searching for the dictionary associated with the steering case
    dico_file = path.join(cfg['MODULES'][args.module]['path'],
                          args.module+'.dico')
    if not path.exists(dico_file):
        raise TelemacException(\
            'Could not find the dictionary file: {}'.format(dico_file))
    cas = TelemacCas(args.cas_file, dico_file, check_files=False)

    cas.write_fr_gb()

    print('\n\nMy work is done\n\n')
    sys.exit(0)


if __name__ == "__main__":
    main()
