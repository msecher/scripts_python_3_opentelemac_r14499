r"""@author TELEMAC-MASCARET Consortium

    @note ... this work is based on a collaborative effort between
                 TELEMAC-MASCARET consortium members
    @brief
"""

from __future__ import print_function
from os import system
###############################################################################
def run_telemac_api(module, cas, ncsize, user_fortran):
    """
    Run Telemac using the api
	@param module		Name of the module
    @param cas			The name of the steering file
    @param ncsize		Number of parallel processors
    @param user_frotran	Name of the user fortran None if none
    """
    cmd = "mpiexec -n {ncsize} template.py {module} {cas} {fortran} > run.log"
    if user_fortran is not None:
        fortran = " -f "+user_fortran
    else:
        fortran = ''
    print(cmd.format(module=module, cas=cas, ncsize=ncsize, fortran=fortran))
    system(cmd.format(module=module, cas=cas, ncsize=ncsize, fortran=fortran))
    passed = False
    with open('run.log', 'r') as fobj:
        for line in fobj.readlines():
            if "My work is done" in line:
                passed = True
    return passed

