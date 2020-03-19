r"""@author TELEMAC-MASCARET Consortium

    @note ... this work is based on a collaborative effort between
                 TELEMAC-MASCARET consortium members
    @brief Report class for validation
"""
from __future__ import print_function
# _____          ___________________________________________________
# ____/ Imports /__________________________________________________/
#
# ~~> dependencies towards standard python
import time as ttime
from os import path, sep
from utils.exceptions import TelemacException
from config import CFGS
from collections import OrderedDict

def plot_bar_report_time(data, title, fig_name=''):
    """
    Plot of stat from report

    @param data (dict) Dictionary from compute stat
    @param title (str) Title of the figure
    @param fig_name (str) If given save figure instead of displaying it
    """
    import matplotlib.pyplot as plt
    import numpy as np

    pre_times = [item['pre'] for item in data.values()]
    run_times = [item['run'] for item in data.values()]
    vnv_times = [item['vnv'] for item in data.values()]
    post_times = [item['post'] for item in data.values()]

    ind = np.arange(len(data))
    width = 0.35

    p_pre = plt.bar(ind, pre_times, width)
    p_run = plt.bar(ind, run_times, width, bottom=pre_times)
    p_vnv = plt.bar(ind, vnv_times, width, bottom=np.add(pre_times, run_times))
    bottom = np.add(np.add(pre_times, run_times), vnv_times)
    p_post = plt.bar(ind, post_times, width, bottom=bottom)

    plt.ylabel('times (s)')
    plt.title(title)
    plt.xticks(ind, data.keys(), rotation=90, ha="center")
    plt.legend((p_pre[0], p_run[0], p_vnv[0], p_post[0]),
               ('pre', 'run', 'vnv', 'post'))

    if fig_name != '':
        plt.savefig(fig_name)
    else:
        plt.show()
    plt.clf()

def get_report_path(report_name, type_valid):
    """
    Build report full path
    $HOMETEL/[report_name]_[config]_[version]_[type_valid]_[date].csv
    where:
    - report_name is the one given as argument
    - config is the name of the configuration for which the validation is run
    - version is the version of the code
    - type_valid is the one given as argument
    - date is the data at which the report is written

    @param report_name (str) Name given to the report
    @param type_valid (str) Type of validation (notebook, examples...)


    @returns (str) The path
    """

    full_report_name = "{}_{}_{}_{}_{}.csv".format(\
                            report_name,
                            CFGS.cfgname,
                            CFGS.configs[CFGS.cfgname].get('version', 'trunk'),
                            type_valid,
                            ttime.strftime("%Y-%m-%d-%Hh%Mmin%Ss",
                                           ttime.localtime(ttime.time())))

    report_path = path.join(CFGS.get_root(), full_report_name)

    return report_path

class Report(object):
    """
    Reader/writer for validation report
    """

    def __init__(self, name, type_valid):
        """

        @param name (str) Name of the report (full_path will be build from
        there)
        @param type_valid (str) Type of validation (examples, notebooks..)
        name
        @param file_name (str)
        """

        if type_valid not in ['examples', 'notebooks']:
            raise TelemacException(\
                    "Unknown validation type: {}".format(type_valid))

        self.type_valid = type_valid
        self.values = OrderedDict()
        if name != '':
            self.file_name = get_report_path(name, type_valid)
        else:
            self.file_name = ''

    def add_notebook(self, nb_file, time, passed):
        """
        Adding a notebook to the report

        @param nb_file (str) Name of the notebook
        @param time (float) execution time
        @param passed (bool) If the notebook worked
        """
        if self.type_valid != 'notebooks':
            raise TelemacException(\
                    'add_action is only possible for a notebooks report')

        self.values[nb_file] = {\
                'time':time,
                'passed':passed}

    def add_action(self, file_name, rank, action, time, passed):
        """
        Add a new action to the report

        @param file_name (str) Name of the file for which the action
        @param action (str) Name of the action
        @param time (float) Time to run the action
        @param passed (bool) If the action worked
        """
        if self.type_valid != 'examples':
            raise TelemacException(\
                    'add_action is only possible for an example report')

        if file_name not in self.values:
            self.values[file_name] = OrderedDict()

        self.values[file_name][action] = {\
                'rank':rank,
                'time':time,
                'passed':passed}

    def read(self, file_name=None):
        """
        Read data from existing file

        @param file_name (str) Name of the file to read from (by default will
        use the name from class)
        """
        if file_name is None:
            file_name = self.file_name

        with open(file_name, 'r') as f:
            header = f.readline().split(';')
            if header[0] == 'Notebook file':
                self.type_valid = 'notebooks'
                for line in f:
                    nb_file, time, passed = line.split(';')
                    self.add_notebook(nb_file, float(time), passed == 'True')
            else:
                self.type_valid = 'examples'
                for line in f:
                    py_file, rank, action, time, passed = line.split(';')
                    self.add_action(py_file, int(rank), action, float(time),
                                    passed == 'True')


    def write(self, file_name=None):
        """
        Write content of class into a file

        @param file_name (str) Name of the output file (by default will take
        name used with Report was initialised)
        """

        if file_name is None:
            file_name = self.file_name

        if self.type_valid == 'examples':
            header = "Python file;rank;action_name;duration;passed\n"
            with open(file_name, 'w') as f:
                f.write(header)
                for file_name, actions in self.values.items():
                    for action_name, action_info in actions.items():
                        llist = [file_name,
                                 str(action_info['rank']),
                                 action_name,
                                 str(action_info['time']),
                                 str(action_info['passed'])]
                        f.write(';'.join(llist)+'\n')
        elif self.type_valid == 'notebooks':
            header = "Notebook file;duration;passed\n"
            with open(file_name, 'w') as f:
                f.write(header)
                for file_name, actions in self.values.items():
                    llist = [file_name,
                             str(actions['time']),
                             str(actions['passed'])]
                    f.write(';'.join(llist)+'\n')

    def compute_stats(self):
        """
        Will compute stats from the report info
        """

        module_time = {}
        rank_time = {}
        per_module_time = {}

        for py_file, actions in self.values.items():
            module = get_module_from_path(py_file)
            if module not in module_time:
                module_time[module] = \
                        {'pre':0.0, 'run':0.0, 'vnv':0.0, 'post':0.0}
                per_module_time[module] = {}
            short_name = path.basename(py_file)
            per_module_time[module][short_name] = \
                        {'pre':0.0, 'run':0.0, 'vnv':0.0, 'post':0.0}
            for action, data in actions.items():
                rank = data['rank']
                time = data['time']
                if rank not in rank_time:
                    rank_time[rank] = \
                            {'pre':0.0, 'run':0.0, 'vnv':0.0, 'post':0.0}
                if action not in ['pre', 'vnv', 'post']:
                    per_module_time[module][short_name]['run'] += time
                    module_time[module]['run'] += time
                    rank_time[rank]['run'] += time
                else:
                    per_module_time[module][short_name][action] += time
                    module_time[module][action] += time
                    rank_time[rank][action] += time

        return per_module_time, module_time, rank_time

    def plot_stats(self):
        """
        Plot stat from
        """
        per_module_time, module_time, rank_time = self.compute_stats()

        plot_bar_report_time(\
                 module_time,
                 'Execution time per module',
                 fig_name='module_time.png')
        plot_bar_report_time(\
                rank_time,
                'Execution time per rank',
                fig_name='rank_time.png')

        for module, time in per_module_time.items():
            plot_bar_report_time(\
                    time,
                    'Exuction time per vnv_*.py for '+module,
                    fig_name=module+'_time.png')


def get_module_from_path(file_name):
    """
    extract module from path
    """
    names = file_name.split(sep)
    i = names.index('examples')
    return names[i+1]
