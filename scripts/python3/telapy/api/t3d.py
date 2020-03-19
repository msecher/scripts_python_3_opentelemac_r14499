# -*- coding: utf-8 -*-
"""
    Python wrapper to the Fortran APIs of Telemac 3D

    Author(s): Fabrice Zaoui, Yoann Audouin, Cedric Goeury, Renaud Barate

    Copyright EDF 2016
"""

from __future__ import print_function
import os
from telapy.api.api_module import ApiModule
from utils.exceptions import TelemacException


class Telemac3d(ApiModule):
    """The Telemac3dPython class for APIs"""
    _instanciated = False

    def __new__(cls, *args, **kwargs):
        if cls._instanciated:
            raise TelemacException("a Telemac3d instance already exists")
        instance = ApiModule.__new__(cls)
        cls._instanciated = True
        return instance

    def __init__(self, casfile,
                 user_fortran=None,
                 dicofile=None,
                 lang=2, stdout=6,
                 comm=None,
                 log_lvl='INFO',
                 recompile=True):
        """
        Constructor for Telemac3d

        @param casFile Name of the steering file
        @param user_fortran Name of the user Fortran (default=None)
        @param dicofile Path to the dictionary (default=None)
        @param lang Language for ouput (1: French, 2:English) (default=2)
        @param stdout Where to put the listing (default on terminal)
        @param comm MPI communicator (default=None)
        @param recompile If true recompiling the API (default=True)
        """
        if dicofile is None:
            hometel = os.getenv("HOMETEL")
            if hometel is not None:
                default_dicofile = os.path.join(os.getenv("HOMETEL"),
                                                "sources",
                                                "telemac3d",
                                                "telemac3d.dico")
            else:
                default_dicofile = 'telemac3d.dico'
            dicofile = default_dicofile

        super(Telemac3d, self).__init__("t3d", casfile, user_fortran,
                                        dicofile, lang, stdout, comm,
                                        recompile, log_lvl=log_lvl)

    def __del__(self):
        """
        Destructor
        """
        Telemac3d._instanciated = False
