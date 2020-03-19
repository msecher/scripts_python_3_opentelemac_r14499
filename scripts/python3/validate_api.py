#!/usr/bin/env python3
"""
   @author TELEMAC-MASCARET Consortium
   @brief Function for validation of the Python API
"""
from os import path, chdir, remove, listdir, sep
from filecmp import cmp
import shutil
from argparse import ArgumentParser
from vvytel import copy_file_to_tmp
from vvytel import get_result_file_name
from vvytel import run_telemac_api
from vvytel import run_telemac_normal
from config import add_config_argument, update_config, CFGS

MODULE_HANDLED = ['telemac2d', 'telemac3d', 'artemis', 'tomawac']

def main(modules, example, nncsize, clean):
    """
    Main function
    """
    # Running main function
    root_dir = CFGS.get_root()

    if path.exists('ValidationTelApy.log'):
        remove('ValidationTelApy.log')
    fichier = open('ValidationTelApy.log', 'a')
    fichier.write("-----Listing Validation telapy-------\n")

    seq_only = {}
    skip_test = {}
    # Specifcation for each module
    for module in MODULE_HANDLED:
        seq_only[module] = []
        skip_test[module] = []

    # Sequential only test cases
    seq_only['telemac2d'].append('t2d_hydraulic_jump_v1p0.cas')
    seq_only['telemac2d'].append('t2d_hydraulic_jump_v2p0.cas')
    seq_only['telemac2d'].append('t2d_wesel.cas')
    seq_only['telemac2d'].append('t2d_wesel_pos.cas')
    seq_only['telemac2d'].append('t2d_delwaq.cas')
    seq_only['telemac2d'].append('t2d_ruptmoui.cas')
    seq_only['telemac2d'].append('t2d_triangular_shelf.cas')
    seq_only['telemac2d'].append('t2d_island.cas')
    seq_only['telemac2d'].append('t2d_tide-jmj_real_gen.cas')
    seq_only['telemac2d'].append('t2d_tide-jmj_type_gen.cas')
    seq_only['telemac2d'].append('t2d_dambreak_v1p0.cas')

    seq_only['telemac3d'].append('t3d_delwaq.cas')
    seq_only['telemac3d'].append('t3d_pluie.cas')
    seq_only['telemac3d'].append('t3d_tide-jmj_real_gen.cas')

    seq_only['artemis'].append('none')

    seq_only['tomawac'].append('tom_turning_wind.cas')
    seq_only['tomawac'].append('tom_manche.cas')
    seq_only['tomawac'].append('tom_manchelim.cas')
    # Test case that can not work with api

    # Using homere_adj not handle by api
    skip_test['telemac2d'].append('estimation')
    # Reruning telemac from homere not handled by api
    skip_test['telemac2d'].append('convergence')
    # Case that are not run by validation
    skip_test['telemac2d'].append('t2d_tide-jmj_type_med.cas')
    skip_test['telemac2d'].append('t2d_tide-ES_real.cas')

    # Non telemac3d case in folder
    skip_test['telemac3d'].append('t2d_canal.cas')
    skip_test['telemac3d'].append('p3d_amr.cas')
    skip_test['telemac3d'].append('p3d_bump.cas')
    skip_test['telemac3d'].append('p3d_canal.cas')
    skip_test['telemac3d'].append('p3d_cooper.cas')
    skip_test['telemac3d'].append('p3d_depot.cas')
    skip_test['telemac3d'].append('p3d_flume_slope.cas')
    skip_test['telemac3d'].append('p3d_gouttedo.cas')
    skip_test['telemac3d'].append('p3d_lock-hydro.cas')
    skip_test['telemac3d'].append('p3d_lock-nonhydro.cas')
    skip_test['telemac3d'].append('p3d_nonlinearwave.cas')
    skip_test['telemac3d'].append('p3d_piledepon.cas')
    skip_test['telemac3d'].append('p3d_piledepon-nonhydro.cas')
    skip_test['telemac3d'].append('p3d_pluie.cas')
    skip_test['telemac3d'].append('p3d_rouse.cas')
    skip_test['telemac3d'].append('p3d_stratification.cas')
    skip_test['telemac3d'].append('p3d_tetra.cas')
    skip_test['telemac3d'].append('p3d_vent.cas')
    skip_test['telemac3d'].append('p3d_V.cas')
    # Coupling test case
    skip_test['telemac3d'].append('depot')
    skip_test['telemac3d'].append('heat_exchange')

    # Artemis animated test case
    skip_test['artemis'].append('art_bj78_animated.cas')
    skip_test['artemis'].append('art_creocean_animated.cas')
    skip_test['artemis'].append('art_creocean_2.cas')
    skip_test['artemis'].append('art_creocean.cas')

    # Tomawac coupled test cases
    skip_test['tomawac'].append('3Dcoupling')

    for module in modules:
        fichier.write("-- For module " + module + "\n")
        module_dir = path.join(root_dir, 'examples', module)
        list_test_case = []
        if example != '':
            list_test_case.append(example)
        else:
            list_test_case = sorted(listdir(module_dir))

        # Sequential only test_case
        for i, test_case in enumerate(list_test_case):
            if test_case in skip_test[module]:
                continue
            case_dir = path.join(module_dir, test_case)
            tmp_dir = path.join(case_dir, 'tmp')
            print("<"+str(i+1)+"/"+str(len(list_test_case))+'> '+str(test_case))
            fichier.write('Running test case '+test_case+'\n')
            list_file = copy_file_to_tmp.copy_file_to_tmp(\
                    case_dir, tmp_dir, \
                    module, root_dir, skip_test[module])

            chdir(tmp_dir)

            for cas, fortran in list_file:
                #
                # Running Telemac based on telapy
                #
                if cas in skip_test[module]:
                    continue
                # Get results names
                res_file = get_result_file_name.get_result_file_name(module,
                                                                     cas)
                api_res_file = res_file+'_api'

                # Running in sequential mode
                # if the case does not run in parallel
                if cas in seq_only[module]:
                    ncsize = 1
                else:
                    ncsize = nncsize
                passed_api = run_telemac_api.run_telemac_api(module, cas,
                                                             ncsize, fortran)

                if passed_api:
                    shutil.move(res_file, api_res_file)
                # Running Telemac classical way
                #
                passed_normal = run_telemac_normal.run_telemac_normal(module,
                                                                      cas,
                                                                      ncsize)

                #
                # Result comparison between api and
                #  classical Telemac computation
                #
                if not passed_normal:
                    fichier.write('   Normal run crashed\n')
                if not passed_api:
                    fichier.write('   Api run crashed\n')
                if not passed_api or not passed_normal:
                    fichier.write(str(cas)+'                       FAILED'+'\n')
                    continue
                if not path.exists(res_file):
                    fichier.write('   Missing '+res_file+"\n")
                    fichier.write(str(cas)+'                       FAILED'+'\n')
                    continue
                if not path.exists(api_res_file):
                    fichier.write('   Missing '+api_res_file+"\n")
                    fichier.write(str(cas)+'                       FAILED'+'\n')
                    continue
                compare = cmp(res_file, api_res_file)

                if compare:
                    fichier.write(str(cas)+'                       PASSED'+'\n')
                else:
                    fichier.write(str(cas)+'                       FAILED'+'\n')

            if clean:
                chdir(module_dir+sep+test_case)
                shutil.rmtree(module_dir+sep+test_case+sep+'tmp')

        fichier.write('my work is done '+'\n')

if __name__ == "__main__":
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# ~~ Reads config file ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    print('\n\nLoading Options and Configurations\n'+72*'~'+'\n')
    PARSER = ArgumentParser(\
        description='Make the validation of Telemac-Mascaret API '\
            'and/or executable using the API')
    PARSER = add_config_argument(PARSER)
    PARSER.add_argument(\
        "-m", "--module",
        dest='modules',
        default="telemac2d",
        help="specify the list of folder to validate seprated by ,")
    PARSER.add_argument(\
        "--clean",
        action="store_true",
        dest="clean",
        default=False,
        help="Remove tmp folders")
    PARSER.add_argument(\
        "-n", "--cnsize",
        dest='ncsize',
        default=4,
        help="specify the number of processor the test case will be run with")
    PARSER.add_argument(\
        "-e", "--example",
        dest='example',
        default="",
        help="specify the name of the test case to compute")
    ARGS = PARSER.parse_args()
    update_config(ARGS)
    main(ARGS.modules.split(','), \
         ARGS.example, ARGS.ncsize, ARGS.clean)
