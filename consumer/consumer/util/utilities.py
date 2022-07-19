#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2016, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2016. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

"""
This file is a suite of utility functions.

"""
import os
import logging
from configobj import ConfigObj
import pytz
import datetime


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['get_config',
           'get_logger']



def get_config(config):
    """
    This function returns configuration dictionary. It checks the conf_path parameter wheter it is directory
    or a file. If a directory, it appends 'dqconfig_test.ini' as a file name. If the directory or file does not
    exist, a message is printed on a console and None is returned. Otherwise, the file is processed into
    dictionary, that is returned.

    Parameters
    ----------
    config : str
        name of the configuration file including path, or path

    Returns
    -------
    conf : config Object
        a configuration object
    """
    if os.path.isdir(config):
        config = os.path.join(config, 'dqconfig.ini')
    if not os.path.isfile(config):
        return None

    return ConfigObj(config)


def get_logger(name, conf):
    """
    This function initializes logger. If logger is not configured or the logging directory does not exist,
    the logging messages will be added into default.log file.

    Parameters
    ----------
    name : str
        name of the logger, typically name of file that uses the logger

    conf : config Object
        a configuration object

    timezone : str
        a standard string defining local timezone, for convenience initialized to known location

    Returns
    -------
    logger : logger
    """

    try:
        # try absolute path
        lfile = conf['log_file']
    except KeyError:
        print('config warning: log file is not configured, logging to default.log')
        lfile = 'default.log'
    except:
        print('config error: log file directory does not exist')
        lfile = 'default.log'

    try:
        timezone = conf['time_zone']
    except KeyError:
        timezone = 'America/Chicago'

    tz = pytz.timezone(timezone)

    class Formatter(logging.Formatter):
        def converter(self, timestamp):
            return datetime.datetime.fromtimestamp(timestamp, tz)

        def formatTime(self, record, datefmt=None):
            dt = self.converter(record.created)
            if datefmt:
                s = dt.strftime(datefmt)
            else:
                t = dt.strftime(self.default_time_format)
                s = self.default_msec_format % (t, record.msecs)
            return s

    logger = logging.getLogger(name)
    handler = logging.FileHandler(lfile)
    handler.setFormatter(Formatter("%(asctime)s:  %(levelname)s:  %(name)s:  %(message)s", "%Y-%m-%dT%H:%M:%S%z"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


