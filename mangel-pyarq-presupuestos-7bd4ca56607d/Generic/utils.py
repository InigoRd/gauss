#!/usr/bin/python
# -*- coding: utf-8 -*-
## File utils.py
## This file is part of pyArq-Presupuestos.
##
## Copyright (C) 2010-2013 Miguel Ángel Bárcena Rodríguez
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

# Modules
import re 
import imghdr

# add wmf to imghdr
def test_wmf(h, f):
    """wmf image library"""
    if h[:6] == "\xd7\xcd\xc6\x9a\x00\x00":
        return 'wmf'
imghdr.tests.append(test_wmf)

# add dxf to imghdr
def test_dxf(h, f):
    """AutoCAD DXF: Drawing Interchange Format"""
    if  isinstance(f,file):
        _pos = f.tell()
        f.seek(0)
        _h = f.read(128)
        f.seek(-32, 2)
        _l = f.read(32)
        f.seek(_pos)
    else:
        _h = h
        _l = h[-32:]
    _h = _h.replace("\r","")
    _l = _l.replace("\r","")
    if ("  0\nSECTION\n  2\nHEADER\n" in _h or\
       "  0\nSECTION\n  2\nCLASSES\n" in _h or\
       "  0\nSECTION\n  2\nTABLES\n" in _h or\
       "  0\nSECTION\n  2\nBLOCKS\n" in _h or\
       "  0\nSECTION\n  2\nENTITIES\n" in _h or\
       "  0\nSECTION\n  2\nOBJECTS\n" in _h or\
       "  0\nSECTION\n  2\nTHUMBNAILIMAGE\n" in _h) and \
       _l[-19:] == "  0\nENDSEC\n  0\nEOF\n":
        return 'dxf'
imghdr.tests.append(test_dxf)


def mapping(string, tuple):
    """mapping(string, tuple)
    
    string: a message string
    tuple: a truple with string items
    Return the string replacing the $[n] words whith its corresponding value
    from the tuple.
    It is used because the gettext module can not #-#supotr#-# strings as:
        "Invalid type (%s) in record: %s" %(type, record)
    """
    for _index in range(len(tuple)):
        string = string.replace("$" + str(_index+1), str(tuple[_index]))
    return string

def eliminate_duplicates(list):
    """eliminate_duplicates(list)
    
    Return a copy of the list without duplicate values
    """
    _result = [ ]
    for item in list:
        if item not in _result:
            _result.append(item)
    return _result

def is_valid_code(code):
    """is_valid_code(code)
    
    code: a string code
    Funtion to test if a record code is valid
    A valid code must fulfill:
        - Be a not empty string
        - The valid characters are the defined in MSdos 6.0 including .$#%&_
            What it means? I am not sure, so I test if all the character 
            are in cp850
        - Cannot contain the following characters
            <~>   separator of records if FIEBDC-3
            <|>   separator of fields if FIEBDC-3
            <\>   separator of subfield in FIEBDC-3
            <\t>  tab -> control character
            < >   space -> control character
            <\n>  end of line -> control character
            <\r>  end of line -> control character
        - Cannot end with <#> or <##>, root and chapter code record
    It return a tuple (is_valid, code)
        is_valid (True/False)
            True: the code is valid
            False: the code is not valid
        code(False/code)
            False: the code is not valid and can not be corrected
            code: the code or the corrected code
    """
    _is_valid = True
    if not isinstance(code, str):
        print "Not a string, code:", code, type(code)
        return False, False
    if code == "":

        return False, False
    try:
        _unicode_code = unicode(code, "utf8",'replace')
        _code_utf8 = _unicode_code.encode("utf8",'replace')
        _code_cp850 = _unicode_code.encode("cp850",'replace')
        _unicode_code = unicode(_code_cp850, "cp850",'replace')

    except UnicodeError:
        print "Unicode Error, code:", code
        return False, False
    if _code_utf8 != code:
        print "Not in cp950, code:", code
        _is_valid = False
        if _code_utf8 == "":
            return False, False
        code = _code_utf8
    _code2 = re.sub("[\t \n\r~|\\\]","",code)
    if _code2 != code:
        print "Control characters in code:", code
        if _code2 == "":
            return False, False
        _is_valid = False
        code = _code2
    if code[-1] == "#":
        print "# in code:", code
        _is_valid =  False
        while code[-1] == "#":
            code = code[:-1]
    if code == "":
        print "Empty code"
        return False, False
    return _is_valid, code

def getFiletype(filename, h=None):
    """getFiletype(filename, h=None):
    
    filename: the filename to test
    h: raw string, if h is not None the filename is ignored and h is assumed
    to contain the byte stream to test
    """
    _type = imghdr.what(filename, h)
    _image_types = ["rgb", "gif", "pbm", "pgm", "ppm", "tiff", "rast", "xbm",
                    "jpeg", "bmp", "png", "wmf"]
    if _type in _image_types:
        return "image"
    elif _type == "dxf":
        return "dxf"
##    _video_types = ["avi", "mpg", "mkv", "ogm"]
##    elif _type in _video_types:
##        return "video"
##    elif _type == "pdf":
##        return "pdf"
##    elif _type == "ppt" or _type == "odp":
##        return "presentation"
    else:
        return None
