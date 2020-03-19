""" @author TELEMAC-MASCARET Consortium

    @brief Collection of run methods for runcode.py
"""
from __future__ import print_function
import threading
import shutil
from os import path
from subprocess import Popen, PIPE
from utils.files import get_file_content, put_file_content, \
                        symlink_file
from utils.messages import Messages
from utils.exceptions import TelemacException
from execution.process import print_twice
from execution.get import get_file_format

def run_partition(partel, cas, geom, fmtgeom, conlim, ncsize,
                  section_name, zone_name, weir_name, use_link, i_part, concat):

    """
    @brief copies the partitions

    @param partel (string): the path of PARTEL
    @param cas (string): name of the *.cas file
    @param geom (string): name of the geometry file
    @param fmtgeom (string): format of the geometry file
    @param conlim (string): the name of the *.cli file
    @param i_files (list): list of input files for the CAS
    @param ncsize (int): number of processors
    @param bypass (boolean): continue execution after exception was
      raised if True, kill the execution otherwise
    @param section_name (string): path to the section ascii input file. This
        file has to be split by partel at the same time as the geometry file.
        To do so, partel needs to know its name, which is why it is returned
        by process_lit.
    @param zone_name (string): path to the zone ascii input file. This file
        has the same treatment as the one above.
    @param weir_name (string): path to the weir ascii input file. This file
        has the same treatment as the one above.
    @param use_link (boolean): if True, do not copy the input files but create
        links to them in the temporary directory
    @param i_part (int): type of partitionner, 1:metis; 2: scotch
    @param concat (boolean): If output is concatenate

    @return True (earlier if there is only one processor)
    """

    if ncsize < 2:
        return True
    # ~~ split GEO, g_conlim, SECTIONS, ZONES and WEIR file ~~~~~~~~~~~~~~~~~
    print('\n... partitioning base files '\
            '(geo, conlim, sections, zones and weirs)')
    run_partel(partel, geom, fmtgeom, conlim, ncsize, False,
               section_name, zone_name, weir_name, geom, fmtgeom, i_part,
               concat)

    # ~~ split input files ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    print('\n... splitting / copying other input files')
    for k in cas.in_files:
        submit = cas.in_files[k].split(';')
        file_name = submit[1]
        if submit[5][-4:] == 'GEOM':
            continue
        elif submit[5][0:7] == 'SELAFIN':
            print('  partitioning: '+ path.basename(file_name))
            file_format = get_file_format(cas, k)
            run_partel(partel, file_name, file_format, conlim, ncsize,
                       False, section_name, zone_name, weir_name, geom,
                       fmtgeom, i_part, concat)
        elif submit[5][0:5] == 'PARAL' or \
             (submit[5][0:5] == 'WEIRS' and weir_name == ''):
            if use_link:
                print('  duplilinking: '+ path.basename(file_name))
                for n in range(ncsize):
                    symlink_file(file_name,
                                 file_name+('00000'+str(ncsize-1))[-5:]+\
                                 '-'+('00000'+str(n))[-5:])
            else:
                print('    duplicating: '+ path.basename(file_name))
                for n in range(ncsize):
                    shutil.copy2(file_name,
                                 file_name+('00000'+str(ncsize-1))[-5:]+\
                                 '-'+('00000'+str(n))[-5:])


def run_partel(partel, par_file, file_format, conlim, ncsize, bypass,
               section_name, zone_name, weir_name, geom, fmtgeom, i_part,
               concat):

    """
    @brief Runs PARTEL

    @param partel (string): the path of partel
    @param par_file (string): the name of the PARTEL file
    @param file_format (string): the format of the filee to partition
    @param conlim (string): the name of the *.cli file
    @param ncsize (int): the number of processors
    @param bypass (boolean): continue execution after exception was
        raised if True, kill the execution otherwise
    @param section_name (string): path to the section ascii input file. This
        file has to be split by partel at the same time as the geometry file.
        To do so, partel needs to know its name, which is why it is returned
        by process_lit.
    @param zone_name (string): path to the zone ascii input file. This file
        has the same treatment as the one above.
    @param weir_name (string): path to the weir ascii input file. This file
        has the same treatment as the one above.
    @param fmtgeom (string): format of the geometry file (serafin, serafind,
        med)
    @param i_part (int): type of partitionner, 1:metis; 2: scotch
    @param concat (boolean): If output is concatenate

    @return void
    """
    partel_input = 'partel_'+par_file+'.par'
    partel_log = 'partel_'+par_file+'.log'
    put_file_content(partel_input,
                     [par_file, file_format, conlim, str(ncsize), str(i_part),
                      section_name, zone_name, weir_name, geom, fmtgeom, concat,
                      ''])
    par_cmd = partel.replace('<partel.log>', partel_log)\
                    .replace('<partel.par>', partel_input).split(';')

    mes = Messages(size=10)
    for par in par_cmd:
        print('     +> '+par)
        tail, code = mes.run_cmd(par, bypass)
        if code != 0:
            if path.exists(partel_log):
                log = "Here is the log:\n"+ \
                      '\n'.join(get_file_content(partel_log))
            else:
                log = "No log available check command:\n"+par_cmd
            raise TelemacException(\
                     'Could not split your file '+par_file\
                     +' with the error as follows:'\
                     +'\n        '+tail\
                     +'\n\n'+log)

def run_code(exe, sortiefile):

    """
    @brief runs the exe file

    @param exe (string): name of the exe file
    @param sortiefile (string): name of the *.sortie listing file

    @return True if no exception was raised or bypass is True
    """

    ofile = None
    lasterr = []
    lastout = []
    # If sortiefile is required, open it
    if sortiefile != None:
        ofile = open(sortiefile, "w")
    # Start process with command 'exe', and direct standard output and
    # standard error into PIPE (part of the Popen object called proc)
    proc = Popen(exe, bufsize=1024, stdout=PIPE, stderr=PIPE, shell=True)
    # Define a thread, thread1, thread2 that will execute the subroutine
    # 'print_twice', with the args given.
    thread1 = threading.Thread(target=print_twice,
                               args=(proc.stdout, ofile, lastout))
    thread2 = threading.Thread(target=print_twice,
                               args=(proc.stderr, ofile, lasterr))
    # Start the print_twice thread. This continues until
    # the stdout buffer is empty
    # (usually when the Telemac code has terminated)
    thread1.start()
    thread2.start()
    # Wait for thread1, thread2 to terminate before continuing
    thread1.join()
    thread2.join()
    # Close the sortiefile, if used
    if ofile:
        ofile.close()
    # Wait to make sure that the Telemac code really has terminated
    # Note: this is probably unnecessary, but done to make sure that
    #         a zero return code is returned, indicating successful completion.
    proc.wait()
    if proc.returncode != 0:
        raise TelemacException('Fail to run\n'+exe)

def run_recollection(gretel, cas, glogeo, fmtgeo, globnd,
                     ncsize):

    """
    @brief Recollects the results

    @param gretel (string): the path of gredel
    @param cas (string): the name of the *.cas file
    @param glogeo (string): global geometry file (.geo)
    @param fmtgeo (string): format of the global geometry file
        (serafin, serafind, med)
    @param globnd (string): global boundary file (.cli)
    @param o_files (list): list of the output files
    @param ncsize (int): the number of processors
    @param bypass (boolean): continue execution after exception was
        raised if True, kill the execution otherwise

    @return True if there is only one processor or no exception was
        raised or bypass is True
    """

    if ncsize < 2:
        return
    # ~~ aggregate output files ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    for k in cas.out_files:
        submit = cas.out_files[k].split(';')
        file_name = submit[1]
        tpe = submit[5]
        if tpe[0:7] == 'SELAFIN':
            print('     collecting: '+ path.basename(file_name))
            file_format = get_file_format(cas, k)
            # We need nplan for gretel in med format
            try:
                nplan = cas.get("NUMBER OF HORIZONTAL LEVELS")
            except TelemacException:
                nplan = 0
            run_gretel(gretel, file_name, file_format, glogeo, fmtgeo,
                       globnd, ncsize, nplan, False)
        if tpe[0:6] == 'DELWAQ':
            print('     collecting: '+ path.basename(file_name))
            run_gredel(gretel, file_name, glogeo, tpe[6:], ncsize, False)

def run_gretel(gretel, gre_file, file_format, geom, geo_format, bnd,
               ncsize, nplan, bypass):

    """
    @brief Runs GRETEL, the functions that merges results

    @param gretel (string): the path of gredel
    @param gre_file (string): the name of the GRETEL file
    @param file_format (string): format of the GRETEL file
    @param geom (string): name of the geometry file
    @param geo_format (string): format of the geometry file
    @param bnd (string): name of the boundary file
    @param ncsize (int): number of processors
    @param nplan (int): number of vertical layers
    @param bypass (boolean): continue execution after exception was
        raised if True, kill the execution otherwise

    @return None
    """

    # ~~ Run GRETEL ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    gretel_par = 'gretel_'+gre_file+'.par'
    gretel_log = 'gretel_'+gre_file+'.log'
    put_file_content(gretel_par,
                     [geom, geo_format, bnd, gre_file,
                      file_format, str(ncsize), str(nplan)])
    mes = Messages(size=10)
    cmd = '{} < {} >> {}'.format(gretel, gretel_par, gretel_log)
    tail, code = mes.run_cmd(cmd, bypass)
    if code != 0:
        if path.exists(gretel_log):
            log = "Here is the log:\n"+ \
                  '\n'.join(get_file_content(gretel_log))
        else:
            log = "No log available check command:\n"+cmd
        raise TelemacException(\
                 'Could not split your file '+gre_file\
                 +' (runcode='+str(code)+') with the error as follows:'\
                 +'\n        '+tail+'\n\n'+log)
    return

def run_gredel(gredel, gredel_file, geom, gredel_type, ncsize, bypass):

    """
    @brief Runs GREDEL, the functions that merge Delwaq results

    @param gredel (string): the path of gredel
    @param gredel_file (string): the name of the GREDEL file
    @param geom (string): the name of the geometry file
    @param gredel_type (string): XXX
    @param ncsize (int): the number of processors
    @param bypass (boolean): continue execution after exception was
        raised if True, kill the execution otherwise

    @return None
    """

    # ~~ Change GRETEL into GREDEL ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    path_gredel = path.dirname(gredel)
    _, ext_gredel = path.splitext(path.basename(gredel))
    gredel = path.join(path_gredel,
                       'gredel' + gredel_type.lower() + '_autop' + ext_gredel)
    # ~~ Run GREDEL ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    gredel_par = 'gretel_'+gredel_file+'.par'
    gredel_log = 'gretel_'+gredel_file+'.log'
    put_file_content(gredel_par,
                     [geom, gredel_file, str(ncsize)])
    mes = Messages(size=10)
    cmd = '{} < {} >> {}'.format(gredel, gredel_par, gredel_log)

    tail, code = mes.run_cmd(cmd, bypass)
    if code != 0:
        raise TelemacException(\
           'Could not split your file (runcode='+str(code)+\
           ').\n      '+gredel_file+'\n        '+tail)
    return
