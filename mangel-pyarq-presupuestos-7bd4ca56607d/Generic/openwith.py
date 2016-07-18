#!/usr/bin/python
# -*- coding: utf-8 -*-
## File openwith.py
## This file is part of pyArq-Presupuestos.
##
## Copyright (C) 2010-2013 Miguel Ángel Bárcena Rodríguez
##                    <miguelangel@obraencurso.es>
##
## This file is based in gtkgui_helpers.py and common/helpers.py from gajim
##
## Copyright (C) 2003-2008 Yann Leboulanger <asterix AT lagaule.org>
## Copyright (C) 2005-2006 Dimitur Kirov <dkirov AT gmail.com>
##                         Nikos Kouremenos <kourem AT gmail.com>
## Copyright (C) 2006 Alex Mauer <hawke AT hawkesnest.net>
## Copyright (C) 2006-2007 Travis Shirk <travis AT pobox.com>
## Copyright (C) 2006-2008 Jean-Marie Traissard <jim AT lapin.org>
## Copyright (C) 2007 Lukas Petrovicky <lukas AT petrovicky.net>
##                    James Newton <redshodan AT gmail.com>
##                    Julien Pivotto <roidelapluie AT gmail.com>
## Copyright (C) 2007-2008 Stephan Erb <steve-e AT h3c.de>
## Copyright (C) 2008 Brendan Taylor <whateley AT gmail.com>
##                    Jonathan Schleifer <js-gajim AT webkeks.org>
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 3 only.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Gajim. If not, see <http://www.gnu.org/licenses/>.
##
# Modules
import subprocess
import os

# pyArq-Presupuestos modules
import globalVars

# from gtkgui_helpers.py 
def autodetect_desktop():
    # recognize the environment and sets it in globalVars
    if os.name == 'nt':
        globalVars.desktop["desktop"] = "windows"
    else:
        _processes = get_running_processes()
        if 'gnome-session' in _processes:
            globalVars.desktop["desktop"] = "gnome"
        elif 'startkde' in _processes:
            globalVars.desktop["desktop"] = "kde"
        elif 'startxfce4' in _processes or 'xfce4-session' in _processes:
            globalVars.desktop["desktop"] = "xfce"
        elif 'startlxde' in _processes or 'lxsession' in _processes:
            globalVars.desktop["desktop"] = "lxde"
        elif 'awesome' in _processes:
            globalVars.desktop["desktop"] = "awesome"
        elif 'dwm' in _processes:
            globalVars.desktop["desktop"] = "dwm"
        elif 'startfluxbox' in _processes:
            globalVars.desktop["desktop"] = "fluxbox"
        elif 'fvwm2' in _processes:
            globalVars.desktop["desktop"] = "fvwm"
        else:
            globalVars.desktop["desktop"] = ""

def get_running_processes():
    '''returns running processes or None (if not /proc exists)'''
    if os.path.isdir('/proc'):
        # under Linux: checking if 'gnome-session' or
        # 'startkde' programs were run before gajim, by
        # checking /proc (if it exists)
        #
        # if something is unclear, read `man proc`;
        # if /proc exists, directories that have only numbers
        # in their names contain data about processes.
        # /proc/[xxx]/exe is a symlink to executable started
        # as process number [xxx].
        # filter out everything that we are not interested in:
        files = os.listdir('/proc')

        # files that doesn't have only digits in names...
        files = filter(str.isdigit, files)

        # files that aren't directories...
        files = [f for f in files if os.path.isdir('/proc/' + f)]

        # processes owned by somebody not running gajim...
        # (we check if we have access to that file)
        files = [f for f in files if os.access('/proc/' + f +'/exe', os.F_OK)]

        # be sure that /proc/[number]/exe is really a symlink
        # to avoid TBs in incorrectly configured systems
        files = [f for f in files if os.path.islink('/proc/' + f + '/exe')]

        # list of processes
        processes = [os.path.basename(os.readlink('/proc/' + f +'/exe')) for f in files]

        return processes
    return []

# from common/helpers.py

def exec_command(command):
    subprocess.Popen('%s &' % command, shell=True).wait()

def build_command(executable, parameter):
    # we add to the parameter (can hold path with spaces)
    # "" so we have good parsing from shell
    parameter = parameter.replace('"', '\\"') # but first escape "
    command = '%s "%s"' % (executable, parameter)
    return command

def launch_file(kind, uri):
    # kind = "url" ,"mail", "image", "dxf"
    _desktop = globalVars.desktop["desktop"]
    if _desktop == "windows":
        try:
            os.startfile(uri) # if pywin32 is installed we open
        except Exception:
            pass
    else:
        if kind == 'mail' and not uri.startswith('mailto:'):
            uri = 'mailto:' + uri
        if _desktop == "gnome":
            command = 'gnome-open'
        elif _desktop == "kde":
            command = 'kfmclient exec'
        elif _desktop == "xfce":
            command = 'exo-open'
        else:
            if kind == 'url':
                command = globalVars.desktop["browser"]
            elif kind == 'mail':
                command = globalVars.desktop["mailapp"]
            elif kind == 'image':
                command = globalVars.desktop["imageapp"]
            elif kind == 'dxf':
                command = globalVars.desktop["cadapp"]
            else:  # if no app is configured
                return
        command = build_command(command, uri)
        try:
            exec_command(command)
        except Exception:
            pass
