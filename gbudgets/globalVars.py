#!/usr/bin/python
# -*- coding: utf-8 -*-
## File globalVars.py
## This file is part of pyArq-Presupuestos.
##
## Copyright (C) 2010-2014 Miguel Ángel Bárcena Rodríguez
##                         <miguelangel@obraencurso.es>
##
## pyArq-Presupuestos is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## pyArq-Presupuestos is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.

# module for global variables
import os
import sys

version = "pyArq Presupuestos v0.0.0"
changeset = 22
baseversion = 0

# path: Paths where find the program files needed
path = {
    "HOME" : "",
    "APPDATA" : "",
    #"DURUS-DATABASE": "/pyArq-Presupuestos/durus/",
    "BUDGET": "/pyArq-Presupuestos/budget/",
    "ICON" : "/images/pyArq-Presupuestos.png",
    "CHAPTER-ICON" : "/images/chapter.png",
    "UNIT-ICON" : "/images/unit.png",
    "MATERIAL-ICON" : "/images/material.png",
    "MACHINERY-ICON" : "/images/machinery.png",
    "LABOURFORCE-ICON": "/images/labourforce.png",
    "MENU-ICON": "/images/menu.png",
    "CONNECTED-ICON": "/images/connected.png",
    "DISCONNECTED-ICON": "/images/disconnected.png",
    "CLOSE-ICON": "/images/close.png",
    "DESCRIPTION-ICON": "/images/description.png",
    "SHEET-ICON": "/images/sheet.png",
    "DECOMPOSITION-ICON" : "/images/decomposition.png",
    "MEASURE-ICON" : "/images/measure.png",
    "ACUMULATEDLINE-ICON" : "/images/acumulatedline.png",
    "PARCIALLINE-ICON" : "/images/parcialline.png",
    "NORMALLINE-ICON" : "/images/normalline.png",
    "CALCULATEDLINE-ICON" : "/images/calculatedline.png",
    "ARROW-ICON": "/images/arrow.png",
    "IMAGE-ICON": "/images/image.png",
    "DXF-ICON": "/images/dxf.png",
    "THROBBER-ICON": "/images/throbber.png",
    "THROBBER-GIF": "/images/throbber.gif",
    "BUDGET-ICON": "/images/budget.png",
    "PYARQ-ICON": "/images/pyArq.png",
    }

color = {
    "ACTIVE" : "#CDD7FF",           # blue
    "INDEX-EVEN" : "#C4C4C4",       # dark grey
    "INDEX-UNEVEN" : "#DDDDDD",     # grey
    "EVEN" : "#E6E6E6",             # dark white
    "UNEVEN": "#FFFFFF",            # white
    "CHAPTER-EVEN": "#D8E6E6",      # dark cian
    "CHAPTER-UNEVEN": "#F0FFFF",    # cian
    "TEXT": "#000000",              # black
    "CALCULATED-TEXT": "#FF00FF",   # 
    "SUBTOTAL": "#FAC8C8",
    "SUBTOTAL-PARCIAL": "#ADD8E6",
    }

desktop = {
    "autodetect" : True,
    "desktop" : "",
    "browser" : "firefox",
    "mailapp" : "evolution",
    "imageapp" : "gthumb",
    "cadapp" : "qcad",
    }

def getAppPath(key):
    return path["APPDATA"] + path[key]

def getHomePath(key):
    return path["HOME"] + path[key]

if os.name == 'posix':
    path["HOME"] = os.environ.get('HOME')
elif sys.platform == 'win32':
    path["HOME"] = os.environ.get('HOMEPATH')
    # TODO: Mac Os, 
    # TODO: Test in diferents os

#-#
path["BUDGET"] = "/pyArq-Presupuestos/"
#-#
