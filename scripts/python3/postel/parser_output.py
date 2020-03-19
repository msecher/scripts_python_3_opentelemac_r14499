r"""@author TELEMAC-MASCARET Consortium

    @brief
            Functions to read Telemac result file
"""
import re
from os import path, walk
from fnmatch import fnmatch
from utils.files import get_file_content
from utils.exceptions import TelemacException

def get_latest_output_files(input_file):
    """
    Inspired from matchSafe in utils.py
    Follows first the simple template casFile+'_*??h??min??s.sortie'
    and then look for the parallel equivalent
    """
    # ~~> list all entries
    dir_path, _, filenames = next(walk(path.dirname(input_file)))
    # ~~> match expression
    exnames = [] # [ path.basename(input_file) ]
    for fout in filenames:
        if fnmatch(fout, path.basename(input_file)+'_*??h??min??s.sortie'):
            exnames.append(fout)
    if exnames == []:
        return []
    casbase = sorted(exnames).pop()
    exnames = [path.join(dir_path, casbase)]
    casbase = path.splitext(casbase)[0]
    for fout in filenames:
        if fnmatch(fout, casbase+'_*.sortie'):
            exnames.append(path.join(dir_path, fout))
    return exnames


class OutputFileData(object):
    """
    @brief : Read and store data result file
    :return:
    """
    def __init__(self, file_name=''):
        self.output = []
        if file_name != '':
            self.output = self._get_file_content(file_name)

    def _get_file_content(self, file_name):
        """
        @brief : Get the content of the file
                 if file does not exist then system exit
        :return:
        """
        if not path.exists(file_name):
            raise TelemacException(\
                    '... could not find your .sortie file: '
                    '{}'.format(file_name))
        return get_file_content(file_name)

    def get_time_profile(self):
        """
        @brief : Returns the time profile in iteration and in seconds,
                         read from the TELEMAC-* output file
                         Also sets the xLabel to either 'Time (s)'
                         or 'Iteration #'
        :return: Iteration and Time
        """
        form = re.compile(r'\s*ITERATION\s+(?P<iteration>\d+)'\
                + r'\s+(TIME)[\s:]*(?P<others>.*?)'\
                + r'(?P<number>\b((?:(\d+)\b)|(?:(\d+(|\.)'\
                + r'\d*[dDeE](\+|\-)?\d+'\
                + r'|\d+\.\d+))))\s+S\s*(|\))\s*\Z', re.I)
        itr = []
        time = []
        for line in self.output:
            proc = re.match(form, line)
            if proc:
                itr.append(int(proc.group('iteration')))
                time.append(float(proc.group('number')))
        return ('Iteration #', itr), ('Time (s)', time)

    # ~~ Name of the study ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Returns the name of the study, read from the TELEMAC output file
    #   +> If no name, returns NO NAME
    #   +> If not found, returns NAME NO FOUND
    def get_name_of_study(self):
        """
        @brief : the name of the study, read from the TELEMAC output file
        :return: returns NO NAME if no name and NAME NO FOUND if not found
        """
        form = re.compile(r'\s*(?P<before>.*?)(NAME OF THE STUDY'\
                          +r')[\s:]*(?P<after>.'\
                          +r'*?)\s*\Z', re.I)
        for line in range(len(self.output)):
            proc = re.match(form, self.output[line])
            if proc:
                if self.output[line+1].strip() == '':
                    return 'NO NAME OF STUDY'
                return self.output[line+1].strip()
        return 'NAME OF STUDY NOT FOUND'

    def get_volume_profile(self):
        """
        @brief : Returns the time series of Values, read from
                 the TELEMAC-2D output file
                 volumes, fluxes, errors, etc.
                 Assumptions:
                 - if VOLUME ... is not found, will not try
                 to read FLUX and ERROR
                 - for every VOLUME instance, it will advance
                  to find FLUX and ERROR
                 Also sets the yLabel to either 'Volume (m3/s)'
                 or 'Fluxes (-)' or 'Error(-)'
        :return:
        """
        form_liqnumbers = re.compile(r'\s*(THERE IS)\s+(?P<number>\d+)'\
                             + r'\s+(LIQUID BOUNDARIES:)\s*\Z', re.I)
        form_liqnumberp = re.compile(r'\s*(NUMBER OF LIQUID BOUNDARIES)'\
                             + r'\s+(?P<number>\d+)\s*\Z', re.I)
        form_volinitial = re.compile(r'\s*(INITIAL VOLUME )'\
                             + r'[\s:]*\s+(?P<value>\b([-+]|)((?:(\d+)\b)|'\
                             + r'(?:(\d+(|\.)'\
                             + r'\d*[dDeE](\+|\-)?\d+|\d+\.\d+))))\s+'\
                             + r'(?P<after>.*?)\s*\Z', re.I)
        form_voltotal = re.compile(r'\s*(VOLUME IN THE DOMAIN)[\s:]*'\
                             + r'\s+(?P<value>\b([-+]|)((?:(\d+)\b)|'\
                             + r'(?:(\d+(|\.)'\
                             + r'\d*[dDeE](\+|\-)?\d+|\d+\.\d+))))\s+'\
                             + r'(?P<after>.*?)\s*\Z', re.I)
        form_volfluxes = re.compile(r'\s*(FLUX BOUNDARY)\s+'\
                             + r'(?P<number>\d+)\s*:\s*'\
                             + r'(?P<value>[+-]*\b((?:(\d+)\b)|(?:(\d+(|\.)'\
                             + r'\d*[dDeE](\+|\-)?\d+|\d+\.\d+))))(.\s|\s)+'\
                             + r'(?P<after>.*?)\s*\Z', re.I)
        form_volerror = re.compile(r'\s*(RELATIVE ERROR IN VOLUME AT T '\
                             + r'=)\s+'\
                             + r'(?P<at>[+-]*\b((?:(\d+)\b)|(?:(\d+(|\.)'\
                             + r'\d*[dDeE](\+|\-)?\d+|\d+\.\d+))))\s+S :\s+'\
                             + r'(?P<value>[+-]*\b((?:(\d+)\b)|(?:(\d+(|\.)'\
                             + r'\d*[dDeE](\+|\-)?\d+|\d+\.\d+))))'\
                             + r'\s*\Z', re.I)
        iline = 0
        # ~~ Searches for number of liquid boundaries ~~~~~~~~~~~~~~~~~~~
        fluxes_prof = []
        bound_names = []
        liqnumber = 0
        while iline < len(self.output):
            proc = re.match(form_liqnumbers, self.output[iline])
            if not proc:
                proc = re.match(form_liqnumberp, self.output[iline])
            if proc:
                liqnumber = int(proc.group('number'))
                for i in range(liqnumber):
                    fluxes_prof.append([])
                    bound_names.append('Boundary ' + str(i+1))
                break
            iline = iline + 1
        # ~~ Initiates profiles ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        volumes_prof = []
        volumes_name = 'Volumes (m3/s)'
        errors_prof = []
        errors_name = 'Error (-)'
        fluxes_name = 'Fluxes (-)'
        # ~~ Reads the rest of time profiles ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        while iline < len(self.output):
            if re.match(form_volinitial, self.output[iline]):
                break
            proc = re.match(form_voltotal, self.output[iline])
            if proc:
                volumes_prof.append(float(proc.group('value')))
                for i in range(liqnumber):
                    iline = iline + 1
                    proc = re.match(form_volfluxes, self.output[iline])
                    while not proc:
                        iline = iline + 1
                        if iline >= len(self.output):
                            raise TelemacException(\
                                    '... Could not parse FLUXES'
                                    'FOR BOUNDARY {}'.format(str(i+1)))
                        proc = re.match(form_volfluxes, self.output[iline])
                    fluxes_prof[i].append(float(proc.group('value')))
                iline = iline + 1
                proc = re.match(form_volerror, self.output[iline])
                while not proc:
                    iline = iline + 1
                    if iline >= len(self.output):
                        raise TelemacException(\
                                '... Could not parse RELATIVE ERROR IN VOLUME ')
                errors_prof.append(float(proc.group('value')))

            iline = iline + 1

        # ~~ Adds initial volume ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        while iline < len(self.output):
            proc = re.match(form_volinitial, self.output[iline])
            if proc:
                volumes_prof.insert(0, float(proc.group('value')))
                break
            iline = iline + 1
        # ~~ Adds initial error ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        errors_prof.insert(0, 0.0) # assumed
        # ~~ Adds initial fluxes ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        for i in range(liqnumber):      # 0.0 may not be the correct value
            fluxes_prof[i].insert(0, 0.0)

        return (volumes_name, volumes_prof), \
               (fluxes_name, bound_names, fluxes_prof),\
               (errors_name, errors_prof)

    def get_value_history_output(self, vrs):
        """
        @brief : Read values from the TELEMAC-2D output file
        @param vrs (string) voltotal: extract total volume
                            volfluxes: extract boundary fluxes
                            volerror: extract error in volume
        :return: x,y arrays for plotting
        """
        # ~~ Extract data
        _, time = self.get_time_profile()
        voltot, volflu, volerr = self.get_volume_profile()
        volinfo = []
        for varname in vrs.split(';'):
            # ~~ y-axis ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            if varname == "voltotal":
                volinfo.append(voltot)
            elif varname == "volfluxes":
                volinfo.append(volflu)
            elif varname == "volerror":
                volinfo.append(volerr)
            else:
                raise TelemacException(\
                       '... do not know how to extract: '
                       '{} '.format(varname))
        return time, volinfo

    def get_user_defined_output(self, user_form, line_num=False):
        """
        @brief : Read user defined values from the TELEMAC-* output file
        @param user_form (string) user gives a regular expression
                                  to find in the file.
        @param line_num(boolean) return or not the line number
        :return: file line and line number
        """
        iline = 0
        user_value = []
        num_line = []
        while iline < len(self.output):
            proc = re.match(user_form, self.output[iline])
            if proc:
                user_value.append(self.output[iline].strip())
                num_line.append(iline)
            iline += 1
        if line_num:
            return user_value, num_line
        else:
            return user_value
