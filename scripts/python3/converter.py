#!/usr/bin/env python3
"""@author TELEMAC-MASCARET Consortium

   @brief Run a converions of mesh files using stbtel
"""
# _____          ___________________________________________________
# ____/ Imports /__________________________________________________/
#
# ~~> dependencies towards standard python
import sys
from argparse import ArgumentParser
from data_manip.conversion.convert_ecmwf import ecmwf2srf, ecmwf2srf_parser
from data_manip.conversion.convert_gebco import gebco2srf, gebco2srf_parser
from data_manip.conversion.convert_hycom import hycom2srf, hycom2srf_parser
from data_manip.conversion.convert_kenue import kenue2shp, kenue2shp_parser
from data_manip.conversion.dat2vtu import convert_drogues_file_to_vtu, \
                                          dat2vtu_parser
from data_manip.conversion.stbtel_converter import run_converter, \
                                                   stbtel_converter_parser
from data_manip.conversion.sis2gaia import sis2gaia_parser, sis2gaia
from data_manip.extraction.extract_ptravers_res_to_geoc import \
        extract_ptravers_res_to_geoc, extrac_ptraver_parser
from pretel.convert_listing_courlis import\
        convert_listing_courlis, convert_courlis_parser
from pretel.generate_atm import generate_atm, generate_atm_parser
from pretel.convert_to_bnd import generate_bnd, generate_bnd_parser
from pretel.stbtel_refine import run_refine, stbtel_refine_parser
from vvytel.xml2py import xml2py, xml2py_parser

# _____             ________________________________________________
# ____/ MAIN CALL  /_______________________________________________/
#

__author__ = "Yoann Audouin"
__date__ = "$21-Sep-2012 16:51:09$"

def print_actions_help():
    """ Print help for the list of actions """
    print(\
'''\n
Tools for handling SELAFIN files and TELEMAC binary related in python\n
Possible actions:\n
    refine     Refinement of the mesh using stbtel
    ''')

def main():
    """
    Main function of the converter
    """

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# ~~~~ Reads config file ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    parser = ArgumentParser()
    subparser = parser.add_subparsers(\
            help='converter command to do', dest='command')

    subparser = ecmwf2srf_parser(subparser)
    subparser = gebco2srf_parser(subparser)
    subparser = hycom2srf_parser(subparser)
    subparser = kenue2shp_parser(subparser)
    subparser = dat2vtu_parser(subparser)
    subparser = generate_atm_parser(subparser)
    subparser = generate_bnd_parser(subparser)
    subparser = stbtel_converter_parser(subparser, 'srf2med',\
            'Conversion from serafin (single or double precision) to MED')
    subparser = stbtel_converter_parser(subparser, 'srf2vtk',\
            'Conversion from serafin (single or double precision) to ascii VTK')
    subparser = stbtel_converter_parser(subparser, 'med2srf',\
            'Conversion from MED to serafin single precision')
    subparser = stbtel_converter_parser(subparser, 'med2srfd',\
            'Conversion from MED to serafin double precision')
    subparser = stbtel_refine_parser(subparser)
    subparser = sis2gaia_parser(subparser)
    subparser = xml2py_parser(subparser)
    subparser = extrac_ptraver_parser(subparser)
    subparser = convert_courlis_parser(subparser)

    options = parser.parse_args()

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# ~~~~ Reads code name ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    if options.command == 'ecmwf2srf':
        ecmwf2srf(options.tfrom, options.tstop, options.blcorner,
                  options.trcorner, options.dataset, options.stream,
                  options.root_name)
    elif options.command == 'gebco2srf':
        gebco2srf(options.gebco_file, options.abval, options.beval,
                  options.axp, options.sph2ll, options.ll2sph,
                  options.ll2utm, options.utm2ll)
    elif options.command == 'hycom2srf':
        hycom2srf(options.tfrom, options.tstop, options.blcorner,
                  options.trcorner, options.root_name, options.t2d)
    elif options.command == 'kenue2shp':
        kenue2shp(options.args)
    elif options.command == 'dat2vtu':
        convert_drogues_file_to_vtu(options.drogues_file, options.vtu_file)
    elif options.command == 'generate_atm':
        generate_atm(options.geo_file, options.slf_file, options.atm_file,
                     options.ll2utm)
    elif options.command == 'generate_bnd':
        varnames = []
        for var in options.varnames.split(";"):
            if len(var) < 16:
                name = var + ' '*(16-len(var))
            else:
                name = var[:16]
            varnames.append(name)

        varunits = []
        for var in options.varunits.split(";"):
            if len(var) < 16:
                name = var + ' '*(16-len(var))
            else:
                name = var[:16]
            varunits.append(name)

        generate_bnd(options.cli_file, options.geo_file, options.slf_file,
                     options.bnd_file,
                     varnames,
                     varunits)
    elif options.command in ['srf2med', 'srf2vtk', 'med2srf', 'med2srfd']:
        run_converter(options.command, options.input_file, options.output_file,
                      options.root_dir, options.bnd_file, options.log_file,
                      options.ndomains, options.srf_bnd, options.debug)
    elif options.command == "refine":
        run_refine(options.input_file, options.output_file, options.root_dir,
                   options.bnd_file)
    elif options.command == "sis2gaia":
        sis2gaia(options.sis_cas, options.gaia_cas)
    elif options.command == "xml2py":
        xml2py(options.input_file, options.out_file, options.skip)
    elif options.command == "extract_ptravers_res_to_geoc":
        extract_ptravers_res_to_geoc(options.args, options.outputFileName,
                                     options.record)
    elif options.command == "convert_listing_courlis":
        convert_listing_courlis(options.args, options.outputFileName,
                                options.write_opt, options.budget,
                                options.txt_format, options.csv_format,
                                options.xlsx_format, options.time_check)
    else:
        parser.print_help()

    sys.exit(0)

if __name__ == "__main__":
    main()
