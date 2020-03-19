#!/usr/bin/env python3
"""@author TELEMAC-MASCARET Consortium
   @brief
"""
# _____          ___________________________________________________
# ____/ Imports /__________________________________________________/
#
# ~~> dependencies towards standard python
import sys
import time
from os import path, walk, chdir, remove
from argparse import ArgumentParser
from shutil import rmtree
# ~~> dependencies towards other pytel/modules
from utils.messages import Messages, svn_banner
from utils.files import check_sym_link
from utils.exceptions import TelemacException
from vvytel.run_notebook import run_notebook
from vvytel.vnv_api import check_api, pre_api
from vvytel.report_class import Report
from config import update_config, CFGS
from runcode import add_runcode_argument

# _____             ________________________________________________
# ____/ MAIN CALL  /_______________________________________________/
#

TAGS = ["telemac2d",
        "telemac3d",
        "mascaret",
        "courlis",
        "sisyphe",
        "nestor",
        "tomawac",
        "aed",
        "waqtel",
        "python2",
        "python3",
        "postel3d",
        "stbtel",
        "khione",
        "artemis",
        "gaia",
        "gotm",
        "full_valid",
        "med"]


def check_python_rank_tags(py_file, options):
    """
    Checks if a Python vnv script match the rank and tags options
    """
    val_dir = path.dirname(py_file)

    chdir(val_dir)

    # Importing vnv_class from py_file
    try:
        # Code foor Python 3.5+
        import importlib.util
        # This allow Python script decalared in the example folder to be loaded
        sys.path.append(val_dir)
        spec = importlib.util.spec_from_file_location("vnv_module", py_file)
        vnv_stuff = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vnv_stuff)
    except:
        from importlib.machinery import SourceFileLoader

        vnv_stuff = SourceFileLoader("vnv_module", py_file).load_module()


    name = path.splitext(py_file)[0]
    my_vnv_study = vnv_stuff.VnvStudy(name, val_dir, options)

    # Checkcing ranks if will run all ranks <= options.rank
    rank = my_vnv_study.rank
    rank_ok = rank <= options.rank

    if not rank_ok and options.verbose:
        print('\n ~> '+py_file)
        print('     > nothing to do here (rank):')
        print('       {} > {}: '.format(rank, options.rank))

    # Checking tags will run all the test contains one of the tags in
    # options.tags And skip the ones with a - before them (-mascaret will
    # skip file with mascaret tag)
    tags = my_vnv_study.tags
    if tags != []:
        tags_ok = False
        opt_tags = options.tags.split(';')

        if '+' in options.tags:
            for opt_tag in opt_tags:
                if '+' in opt_tag:
                    # All the tag in opt_tag must be in tag
                    tag_ok = True
                    for tag2 in opt_tag.split('+'):
                        tag_ok = tag_ok and (tag2 in tags)
                elif '-' in opt_tag:
                    # - means reverse tag must no be in
                    tag_ok = opt_tag[1:] not in tags
                else:
                    tag_ok = opt_tag in tags
                tags_ok = tags_ok or tag_ok
        else:
            for tag in tags:
                # If -tag that means that the Python should not be run
                if '-'+tag in opt_tags:
                    tags_ok = False
                    break
                tag_ok = tag in opt_tags
                # Checking that at least one of the tags is in opt_tags
                tags_ok = tags_ok or tag_ok
    else:
        raise TelemacException("Missing tag in Python file:\n"+py_file)

    if not tags_ok and options.verbose:
        print('\n ~> '+py_file)
        print('     > nothing to do here (tag):')
        print('       File tags: {}'.format(';'.join(tags)))
        print('       Options tags: {}'.format(options.tags))

    # Cleaning up sys.path
    sys.path.remove(val_dir)

    return tags_ok and rank_ok


def run_validation_python(cfg, options, report, xcpts):
    """
    Run validation for vnv Python scripts

    @param cfg (Dict) Configuration information
    @parma options (ArgumentParser) List of arguments
    @param report (Report) Time of actions
    @param xcpts () Error handler
    """
    # Building list of files to run

    if options.args != []:
        list_files = []
        for ffile in options.args:
            list_files.append(path.abspath(ffile))
    else:
        # Looping on all folders to find the scripts to execute
        list_files = []
        # Loop on modules
        for code_name in cfg['VALIDATION']:
            val_root = cfg['val_root']
            dirpath, dirnames, _ = next(walk(path.join(val_root, code_name)))
            for ddir in dirnames:
                _, _, filenames = next(walk(path.join(dirpath, ddir)))
                for fle in filenames:
                    root, ext = path.splitext(path.basename(fle))
                    if ext == '.py' and root[0:4] == 'vnv_':
                        # check rank and tag
                        file_name = path.join(dirpath, ddir, fle)
                        if check_python_rank_tags(file_name, options):
                            list_files.append(file_name)

    n_files = len(list_files)
    root = CFGS.get_root()
    for ifile, py_file in enumerate(sorted(list_files)):
        if options.cleanup or options.full_cleanup:
            clean_vnv_working_dir(py_file, full=options.full_cleanup)
        else:
            print('\n\nValidation < {}/{} > of {}'\
                  .format(ifile+1, n_files, py_file.replace(root, '<root>')))
            run_python(py_file, options, report, xcpts)

def clean_vnv_working_dir(py_file, full=False):
    """
    Clean the working directory

    @param py_file (str) Path of the vnv_study file
    @param full(boolean) If True just delete the entire folder
    """

    vnv_study_dir, _ = path.splitext(py_file)
    if full:
        rmtree(vnv_study_dir)
    else:
        for dirpath, dirnames, _ in walk(vnv_study_dir):
            for dirname in dirnames:
                if dirname == CFGS.cfgname:
                    rmtree(path.join(dirpath, dirname))


def run_python(py_file, options, report, xcpts):
    """
    Run a vnv Python script

    @param py_file (str) Name of the Python file to run
    @param options (ArgumentParser) Options of the script
    @param report (Report) Contains execution time
    @param xcpts () Error Handler
    """
    try:
        abs_py_file = path.abspath(py_file)

        if not path.isfile(abs_py_file):
            raise TelemacException(\
               '\nNot able to find your Python file:\n{}'\
               .format(abs_py_file))

        val_dir = path.dirname(abs_py_file)

        chdir(val_dir)
        # Importing vnv_class from py_file
        try:
            # Code foor Python 3.5+
            import importlib.util
            # This allow Python script decalared in the example folder to be loaded
            sys.path.append(val_dir)
            spec = importlib.util.spec_from_file_location("vnv_module", py_file)
            vnv_stuff = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(vnv_stuff)
        except:
            from importlib.machinery import SourceFileLoader

            vnv_stuff = SourceFileLoader("vnv_module", py_file).load_module()

        name = path.splitext(py_file)[0]
        my_vnv_study = vnv_stuff.VnvStudy(name, val_dir, options)

        # Pre-treatment part
        # It is always done
        my_vnv_study.pre()

        if options.api:
            pre_api(my_vnv_study)

        # Cleaning ?
        if options.cleanup or options.full_cleanup:
            my_vnv_study.clean_vnv_working_dir(full=options.full_cleanup)
            return

        # Execution part
        if options.vnv_run:
            chdir(val_dir)
            my_vnv_study.run()

            # cleaning temporary files (if no post):
            if not options.vnv_post:
                for ffile in my_vnv_study.temporary_files:
                    remove(path.join(val_dir, ffile))

        # Check part
        if options.vnv_check:
            chdir(val_dir)
            my_vnv_study.check_results()
            if options.api:
                check_api(my_vnv_study)

        # Post_treatment part
        if options.vnv_post:
            chdir(val_dir)
            my_vnv_study.post()

            # cleaning temporary files:
            for ffile in my_vnv_study.temporary_files:
                remove(path.join(val_dir, ffile))

    except Exception as exc:
        if options.bypass:
            xcpts.add_messages([{'name':py_file,
                                 'msg':str(exc)}])
        else:
            raise exc
    finally:
        #Updating report information
        if my_vnv_study is not None:
            for action, actions in my_vnv_study.action_time.items():
                report.add_action(abs_py_file, my_vnv_study.rank,
                                  action, actions[1], actions[0])
    # Cleaning up sys.path
    if val_dir in sys.path:
        sys.path.remove(val_dir)


def run_validation_notebooks(options, report, xcpts):
    """
    Run validation of the notebooks

    @param options (ArgumentParser) Options of the script
    @param report (Report) Contains execution time
    @param xcpts (Message) Error handler
    """
    root = CFGS.get_root()

    if options.args != []:
        # Files to run given in arguments
        nb_files = options.args
    else:
        # Looking through notebook folder for notebook to run
        nb_files = []

        for dirpath, _, ffiles in walk(path.join(root, 'notebooks')):
            for ffile in ffiles:
                # Skipping jupyter temporary folders
                if '.ipynb' in dirpath:
                    continue
                # If we have a notebook
                if '.ipynb' in ffile:
                    nb_files.append(path.join(dirpath, ffile))

    # Run notebook validation
    n_nb = len(nb_files)
    for i, nb_file in enumerate(sorted(nb_files)):
        print('Validation <{}/{}> ~> Running notebook {} in {}'\
              .format(i+1, n_nb, path.basename(nb_file), path.dirname(nb_file)))
        try:
            start = time.time()
            run_notebook(nb_file, options.nb_timeout,
                         update_nb=options.nb_update)
            end = time.time()
            report.add_notebook(nb_file, end-start, True)
        except Exception as exc:
            if options.bypass:
                report.add_notebook(nb_file, 0.0, False)
                xcpts.add_messages([{'name':nb_file,
                                     'msg':str(exc)}])
            else:
                raise exc

def set_parser():
    """
    Defining parser for validateTELEMAC.py

    @return (Namespace) Arguments values
    """

    print('\n\nLoading Options and Configurations\n' + 72 * '~' + '\n')
    parser = ArgumentParser( \
        description=('''\n
Used to validate the TELEMAC system against a benchmark of test cases for
a certain rank, and a certain tag'''))

    parser = add_runcode_argument(parser)
    parser.add_argument( \
        "-b", "--bypass", action="store_true", dest="bypass", default=False,
        help="will bypass execution failures and try to carry on "\
              "(final report at the end)")
    # Combine with all filters above, "rank" now controls everything
    # and Jenkins can control "rank"
    parser.add_argument( \
        "-k", "--rank", dest="rank", type=int, default=4,
        help="specify the ranks to be validated all rank lower or equal to "
             "the value will be run")
    parser.add_argument( \
        "--tags", dest="tags", default='all',
        help=\
         "specify tags (; separated) to run "\
         "  '-tag' will do the opposite and "\
         "tag1+tag2 will run cases that has both tag1 and tag2), "\
         "default is all of them")
    parser.add_argument( \
        "--valrootdir", dest="val_root", default='',
        help="specify the directory in which to search the validation cases, "\
              "default is taken from config file")
    parser.add_argument( \
        "--vnv-pre", action="store_true", dest="vnv_pre", default=False,
        help="Only do pre-treatment")
    parser.add_argument( \
        "--vnv-run", action="store_true", dest="vnv_run", default=False,
        help="Only do execution for each study")
    parser.add_argument( \
        "--vnv-check", action="store_true", dest="vnv_check", default=False,
        help="Only do check of results (epsilons)")
    parser.add_argument( \
        "--vnv-post", action="store_true", dest="vnv_post", default=False,
        help="Only do post-treatment")
    parser.add_argument( \
        "--report-name", dest="report_name", default='',
        help="will create a csv containing information on the validation "\
             "such as execution time, rank, if it passed...")
    parser.add_argument( \
        "--clean", action="store_true", dest="cleanup", default=False,
        help="will erase all object, executable, result files "\
              "from subfolders for the actual configuration")
    parser.add_argument( \
        "--full-clean", action="store_true", dest="full_cleanup", default=False,
        help="will erase all vnv study folders regarding of configurations")

    # Options for notebook
    parser.add_argument(
        "--notebook",
        dest="notebook",
        action="store_true", default=False,
        help="Run validation of notebook")
    parser.add_argument(
        "--notebook-timeout",
        dest="nb_timeout", type=int, default=60000,
        help="Time after whihc the notebook will be killed if still running")
    parser.add_argument(
        "--notebook-update",
        dest="nb_update",
        action="store_true", default=False,
        help="Update notebook file with the runned one")
    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true", default=False,
        help="More verbose validation")

    # Options for api
    parser.add_argument(
        "--api",
        dest="api",
        action="store_true", default=False,
        help="Run validation of api")

    parser.add_argument("args", metavar='Python file(s)', nargs='*')
    options = parser.parse_args()

    # Conversion of options.tags (replacing all by list) and checking that the
    # value is valid
    # Removing quotes
    tmp_tag = options.tags.strip("'\"")
    options.tags = tmp_tag
    # Checking that tags are valid
    for tag in options.tags.split(';'):
        if '+' in tag:
            for and_tag in tag.split('+'):
                # Removing - if in tag
                ttag = and_tag[1:] if and_tag[0] == '-' else and_tag
                if ttag not in TAGS:
                    raise TelemacException(\
                       "Unknow tag: {tag}\nTags available: {tags}"\
                       .format(tag=ttag, tags=';'.join(TAGS)))
        else:
            if tag == 'all':
                continue
            # Removing - if in tag
            ttag = tag[1:] if tag[0] == '-' else tag
            if ttag not in TAGS:
                raise TelemacException(\
                   "Unknow tag: {tag}\nTags available: {tags}"\
                   .format(tag=ttag, tags=';'.join(TAGS)))

    # Replacing all by list of tags
    if 'all' in options.tags.split(';'):
        options.tags = options.tags.replace('all', ';'.join(TAGS))

    # If pre, run, post are all false switching them to true
    if not(options.vnv_pre or options.vnv_run or
           options.vnv_check or options.vnv_post):
        options.vnv_pre = True
        options.vnv_run = True
        options.vnv_check = True
        options.vnv_post = True

    return options

def config_corrections(options, cfgname):
    """
    overwrite configuration wiht options arguments

    @param options (Value) List of argparse options
    @param cfgname (string) Name of the configuration

    @return (dict) The configuration info
    """
    CFGS.cfgname = cfgname
    cfg = CFGS.configs[cfgname]
    # still in lower case
    if options.val_root != '':
        cfg['val_root'] = options.val_root
    # parsing for proper naming
    CFGS.compute_vnv_info()
    print('    +> ' + cfgname + ': ' + ', '.join(cfg['VALIDATION'].keys()))
    if options.cleanup:
        cfg['REBUILD'] = 2

    return cfg

def main():
    """
     @brief Main function of validateTELEMAC.
    """
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # ~~ Handles input arguments
    options = set_parser()

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # ~~~~ Environment ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    update_config(options)
    version = CFGS.configs[CFGS.cfgname].get('version', 'trunk')

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # ~~~~ banners ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    svn_banner(CFGS.get_root(), version)

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # ~~~~ Works for all configurations unless specified ~~~~~~~~~~~~~~~
    # Checking if symlink is available
    if options.use_link and not check_sym_link(options.use_link):
        raise TelemacException(\
                '\nThe symlink option is only available on Linux systems. '
                'Remove the option and try again')

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # ~~~~ Forces not to use any Xwindows backend for Jenkins ~~~~~~~~~~
    if options.vnv_post:
        import matplotlib.pyplot as plt

        plt.switch_backend('agg')

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # ~~~~ Reporting errors ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    xcpts = Messages()

    # ~~~~ Reporting summary ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    if options.notebook:
        type_valid = 'notebooks'
    else:
        type_valid = 'examples'

    report = Report(options.report_name, type_valid)

    # ~~~ Running validation
    cfg = config_corrections(options, CFGS.cfgname)

    if options.notebook:
        run_validation_notebooks(options, report, xcpts)
    else:
        run_validation_python(cfg, options, report, xcpts)

    # Writting report
    if options.report_name != '':
        report.write()

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # ~~~~ Reporting errors ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    if xcpts.not_empty():
        print('\n\nHummm ... I could not complete my work.\n'
              '{}\n{}'.format('~' * 72, xcpts.except_messages()))
        sys.exit(1)

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # ~~~~ Jenkins' success message ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    else:
        print('\n\nMy work is done\n\n')
        sys.exit(0)

if __name__ == "__main__":
    main()
