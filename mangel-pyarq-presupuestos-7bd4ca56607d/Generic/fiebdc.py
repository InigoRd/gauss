#!/usr/bin/python
# -*- coding: utf-8 -*-
## File fiebdc.py
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

# specifications in http://www.fiebdc.org

# Modules
import time
import re
import calendar
import os.path
import unicodedata
import hashlib
# pyArq-Presupuestos modules
import base
from Generic import utils
from Generic import globalVars

class Read(object):
    """fiebdc.Read:
    
    Description:
        Reads and parses a fiebdc file
    Constructor:
        fiebdc.Read(filename=None, budget=None)
    Ancestry:
    +-- object
      +-- Read
    Atributes:
        "__budget": budget ("base.Budget" object)
        "__file_format": File format of the fiebdc file
        "__format_list": List of file format that can be readed
        "__character_sets_dict": Dictionary with the character sets supported
        "__character_set": character_set of the file
        "__generator": program which the file is created
        "__cancel": Boolean value, True mean that the read process must stop
        "__filename": The filename of the fiebdc file that is readed
        "__pattern": re compiled pattern dict
        "__statistics": Statistics object, records number
    Methods:
        __init__(self, filename=None, budget=None)
        cancel(self)
        eraseControlCharacters(self, string)
        validateCode(self, code)
        parseDate(self, date)
        parseRecord(self,record)
        _parseV(self, field_list)
        _parseC(self, field_list)
        _parseDY(self, field_list)
        _parseMN(self, field_list)
        _parseT(self, field_list)
        _parseK(self, field_list)
        _parseW(self, field_list)
        _parseL(self, field_list)
        _parseQ(self, field_list)
        _parseJ(self, field_list)
        _parseG(self, field_list)
        _parseE(self, field_list)
        _parseX(self, field_list)
        _parseF(self, field_list)
        readFile(self, budget=None, filename=None)
    """
    def __init__(self, filename=None, budget=None):
        """def __init__(self, filename=None, budget=None)
        
        Sets the instance attributes
        """
        self.__budget = budget
        self.__filename = filename
        if not self.__budget is None:
            self.__budget.filename = self.__filename
        self.__cancel = False
        self.__format_list = ["FIEBDC-3/95", "FIEBDC-3/98", "FIEBDC-3/2002",
                              "FIEBDC-3/2004", "FIEBDC-3/2007"]
        # ANSI->¿"ISO-8859-15" or "latin1 ISO-8859-1" or "cp1252 windows-1252"?
        # 850 -> IBM850 -> cp850
        # 437 -> IBM437 -> cp437
        self.__character_sets_dict = {"ANSI" : "cp1252",
                                      "850" : "850",
                                      "437" : "cp437"}
        self.__file_format = "FIEBDC-3/2007"
        self.__generator = globalVars.version
        self.__character_set = "850"
        self.__pattern = {
            "control_tilde" : re.compile(u"((\r\n)| |\t)+~"),
            "control_vbar" : re.compile(u"((\r\n)| |\t)+\|"),
            "control_backslash" : re.compile(ur"((\r\n)| |\t)+\\"),
            "valid_code" : re.compile(u"[^A-Za-z0-9ñÑ.$#%&_]"),
            "special_char": re.compile(u"[#%&]"),
            "no_float": re.compile(u"[^\-0-9.]"),
            "formula" : re.compile(u".*[^0123456789\.()\+\-\*/\^abcdp ].*"),
            "comment": re.compile(u"#.*\r\n"),
            "empty_line": re.compile(ur"(\r\n) *\r\n"),
            "space_before_backslash" : re.compile(ur"( )+\\"),
            "space_after_backslash" : re.compile(ur"\\( )+"),
            "start_noend_backslash" : re.compile(u"(\r\n\\\.*[^\\\])\r\n"),
            "end_oper": re.compile(u"(\+|-|\*|/|/^|@|&|<|>|<=|>=|=|!) *\r\n"),
            "matricial_var" : re.compile(u"(\r\n *[%|\$][A-ZÑ].*=.*,) *\r\n"),
            "descomposition" : re.compile(u"^([^:]+):(.*)$"),
            "var" : re.compile(u"^([$%][A-ZÑ][()0-9, ]*)=(.*)$"),
            "after_first_tilde" : re.compile(u"^[^~]*~"),
            "end_control" : re.compile(u"((\r\n)| |\t)+$"),
            }
        self.__statistics = Statistics()

    def cancel(self):
        """def cancel(self)
        
        Sets the "__cancel" attribute to True, It stops the read process.
        """
        self.__cancel = True

    def eraseControlCharacters(self, string):
        """eraseControlCharacters(self,string)
        
        Return a copy of the string with the blank characters (32),
        tabs (9) and end of line (13 and 10) before of the separators
        '~', '|' erased.
        Before separator \ not deleted because it affects the reading of the
        record ~P
        """
        # "control_tilde" : "((\r\n)| |\t)+~"
        string = self.__pattern["control_tilde"].sub(u"~",string)
        # "control_vbar" : "((\r\n)| |\t)+\|"
        string = self.__pattern["control_vbar"].sub(u"|",string)
        # "control_backslash" : r"((\r\n)| |\t)+\\"
        #string = self.__pattern["control_backslash"].sub(r"\\",string)
        return string

    def validateCode(self, code):
        """validateCode(self, code)
        
        Test if the code have invalid characters and try to erase it,
        if it is posible return a valid code else return a empty string.
        """
        if not isinstance(code, unicode):
            print _("Invalid code, it must be a unicode string")
            return u""
        # Valid chararcter: A-Z a-z 0-9 ñ Ñ . $ # % & _ 
        # "valid_code" : "[^A-Za-z0-9ñÑ.$#%&_]"
        _ucode = self.__pattern["valid_code"].sub(u"", code)
        if _ucode != code:
            try:
                print utils.mapping(_("The code '$1' have invalid characters."),
                               (code.encode("utf8"),))
            except:
                print utils.mapping(_("The code '$1' have invalid characters and can not be encoded in utf8."), (code,))
            
            if len(_ucode) == 0:
                _normalize_code = ''.join((c for c in unicodedata.normalize('NFD', _ucode) if unicodedata.category(c) != 'Mn'))
                # from http://www.leccionespracticas.com/uncategorized/eliminar-tildes-con-python-solucionado/
                _ucode = self.__pattern["valid_code"].sub(u"", _normalize_code)
                if len(_ucode) == 0:
                    _hash_code = hashlib.sha256()
                    _hash_code.update(code.encode('utf-8'))
                    _hexdigest_code = _hash_code.hexdigest()
                    _ucode = self.__pattern["valid_code"].sub(u"", _hexdigest_code)
            code = _ucode
        # the lasts characters can not be <#> or <##>
        # <##> -> root record in FIEFDC-3
        # <#> -> chapter record in FIEFDC-3
        if len(code) > 0:
            while code[-1] == u"#":
                code = code[:-1]
            if len(code) > 20:
                code = code[:20]
            # only one charecter # % or &
            if sum([code.count(c) for c in u'#%&']) > 1:
                print utils.mapping(_("The code '$1' contains special "\
                                      "characters repeated."),(code.encode("utf8"),))
                _i = min([code.find(c) for c in u'#%&'])
                code = code[:_i+1] + \
                        self.__pattern["special_char"].sub(u"", code[_i+1:])
        return code

    def parseDate(self, date):
        """parseDate(self, date)
        
        date: in the format:
            uneven len: add a Leading 0
            len = 8  DDMMYYYY
            len <= 6 DDMMYY “80/20”. >80 -> >1980 <80 -> <2080
            len < 5  MMYY
            len < 3  YY
        Test date string and return a tuple (YYYY, MM, DD)
        or None if the date format is invalid
        """
        # All characters must be numbers, len <= 8 and not empty string
        if not date.isdigit() or len(date) > 8 or date == u"":
            return None
        else:
            if len(date)%2 == 1: # uneven len: add a leading 0
                date = u"0" + date
            if len(date) == 8:
                _d = int(date[:2])
                _m = int(date[2:4])
                _y = int(date[4:8])
            elif len(date) <= 6:
                _y = int(date[-2:])
                if _y < 80: _y = 2000 + _y
                else: _y = 1900 + _y
                if len(date) == 6:
                    _d = int(date[:2])
                    _m = int(date[2:4])
                elif len(date) == 4:
                    _d = 0
                    _m = int(date[:2])
                elif len(date) == 2:
                    _d = 0
                    _m = 0
        if not _d in range(1,31): _d = 0
        if not _m in range(1,12): _m = 0
        if _m == 0: _d = 0
        if _m != 0 and _d != 0:
            if calendar.monthrange(_y, _m)[1] < _d:
                _d = 0
        return (_y, _m, _d)

    def parseRecord(self,record):
        """parseRecord(self,record)
        
        record: the record line readed from the file whith the format:
            type|field|field|subfield\subfield|...
        [a] nothing or "a"
        {a} zero or more #-#twice#-# "a"
        <a> one or more #-#twice#-# "a"
        Types: V C D Y M N T K L Q J G E X B F A
            V: Property and Version
                1- [File_Owner]
                2- Format_Version[\DDMMYYYY]
                3- [Program_Generator]
                4- [Header]\{Title\}
                5- [Chaters_set]
                6- [Comment]
            C: Record:
                1- Code{\Code}
                2- [Unit]
                3- [Summary]
                4- {Price\}
                5- {Date\}
                6- [Type]
            D or Y: DECOMPOSITION or ADD DECOMPOSITION
                1- Parent Code
                2- <Child Code\ [Factor]\ [Yield]>
            M or N: MEASURE or ADD MEASURE
                1- [Parent Code\]Child Code
                2- {Path\}
                3- TOTAL MEASURE
                4- {Type\Comment\Unit\Length\Width\Height\}
                5- [Label]
            T: Text
                1- Code
                2- Description text
            K: Coefficients
                1- { DN \ DD \ DS \ DR \ DI \ DP \ DC \ DM \ DIVISA \ }
                2-  CI \ GG \ BI \ BAJA \ IVA
                3- { DRC \ DC \ DRO \ DFS \ DRS \ DFO \ DUO \ DI \ DES \ DN \
                  DD \ DS \ DIVISA \ }
                4- [ n ]
            L: Sheet of Conditions 1
                A) 
                    1- Empty
                    2- {Section Code\Section Title}
                B)
                    1- Record Code
                    2- {Section Code\Section Text}
                    3- {Section Code\RTF file}
                    4- {Section Code\HTM file}
            Q: Sheet of Conditions 2
                1- Record Code
                2- {Section Code\Paragraph key\{Field key;}\}|
            J: Sheet of Conditions 3
                1- Paragraph code
                2- [Paragraph text]
                3- [RTF file]
                4- [HTML file]
            G: Grafic info
                1- <grafic_file.ext\>
            E: Company
                1- company Code
                2 [ summary ]
                3- [ name ]
                4- { [ type ] \ [ subname ] \ [ address ] \ [ postal_code ]
                  \ [ town ] \ [ province ] \ [ country ] \ { phone; } 
                  \ { fax; }  \ {contact_person; } \ }
                5- [ cif ] \ [ web ] \ [ email ] \
            X: Tecnical information
                A)
                    1- Empty
                    2- < TI_Code \ TI_Descitption \ TI_Unit >
                B)
                    1- Record_code
                    2- < TI_Code \ TI_value >
            F: #-#Adjunto#-# File
                1- Record code
                2- { Type \ { Filenames; } \ [Description] }
            B: Change code
                1- Record Code
                2- New code
            A: Labels
                1- Record Code
                2- <Label\>
        """
        # TODO:  ~L ~J RTF and HTML files
        # TODO:  test ~Q ~J ~G
        # TODO:  ~P. Registro tipo Descripción Paramétrica.
        # TODO:  ~O. Registro tipo Relación Comercial.
        # TODO: test records
        _field_list = record.split(u"|")
        self.__statistics.records = self.__statistics.records +1
        _budget = self.__budget
        if _field_list[0] == u"V":
            self.__statistics.V += 1
            self._parseV(_field_list)
        elif _field_list[0] == u"C":
            self.__statistics.C += 1
            self._parseC(_field_list)
        elif _field_list[0] == u"D":
            self.__statistics.D += 1
            self._parseDY(_field_list)
        elif _field_list[0] == u"Y":
            self.__statistics.Y += 1
            self._parseDY(_field_list)
        elif _field_list[0] == u"M":
            self.__statistics.M += 1
            self._parseMN(_field_list)
        elif _field_list[0] == u"N":
            self.__statistics.N += 1
            self._parseMN(_field_list)
        elif _field_list[0] == u"T":
            self.__statistics.T += 1
            self._parseT(_field_list)
        elif _field_list[0] == u"K":
            self.__statistics.K += 1
            self._parseK(_field_list)
        elif _field_list[0] == u"W":
            self.__statistics.W += 1
            self._parseW(_field_list)
        elif _field_list[0] == u"L":
            self.__statistics.L += 1
            self._parseL(_field_list)
        elif _field_list[0] == u"Q":
            self.__statistics.Q += 1
            self._parseQ(_field_list)
        elif _field_list[0] == u"J":
            self.__statistics.J += 1
            self._parseJ(_field_list)
        elif _field_list[0] == u"G":
            self.__statistics.G += 1
            self._parseG(_field_list)
        elif _field_list[0] == u"E":
            self.__statistics.E += 1
            self._parseE(_field_list)
        elif _field_list[0] == "O":
            self.__statistics.O += 1
        elif _field_list[0] == u"P":
            self.__statistics.P += 1
            self._parseP(_field_list)
        elif _field_list[0] == u"X":
            self.__statistics.X += 1
            self._parseX(_field_list)
        elif _field_list[0] == u"B":
            self.__statistics.B += 1
            self._parseB(_field_list)
        elif _field_list[0] == u"F":
            self.__statistics.F += 1
            self._parseF(_field_list)
        elif _field_list[0] == u"A":
            self.__statistics.A += 1
            self._parseA(_field_list)
        else:
            self.__statistics.unknow += 1

    def _parseV(self, field_list):
        """_parseV(self, field_list)
        
        field_list: field list of the record
            0- V :Property and Version
            1- [File_Owner]
            2- Format_Version[\DDMMYYYY]
            3- [Program_Generator]
            4- [Header]\{Title\}
            5- [Chaters_set]
            6- [Comment]
            7- [Data type]
            8- [Number budget certificate]
            9- [Date budget certificate]
        """
        if self.__statistics.records != 1:
            print utils.mapping(_("The 'V' record (Property and Version) "\
                    "must be the first record in the file but it is the "\
                    "number: $1"), (self.__statistics.records,))
            print _("The default values were taken and this V record is "\
                  "ignored")
            return
        # _____number of fields_____
        # Any INFORMATION after last field separator is ignored
        if len(field_list) > 10:
            field_list = field_list[:10]
        # If there are no sufficient fields, the fields are added
        # with empty value:""
        else:
            field_list = field_list + [u""]*(10-len(field_list))
        # control character are erased: end of line, tab, space
        # only leading and trailing whitespace in owner, generator, comment
        # _____Fields_____
        _record_type = self.delete_control_space(field_list[0])
        _owner = field_list[1].strip()
        _owner = self.delete_control(_owner)
        _version_date = self.delete_control_space(field_list[2])
        _generator = field_list[3].strip()
        _generator = self.delete_control(_generator)
        _header_title = field_list[4].strip()
        _header_title = self.delete_control(_header_title)
        _character_set = self.delete_control_space(field_list[5])
        _comment = field_list[6].strip(u"\t \n\r")
        _data_type = self.delete_control_space(field_list[7])
        _number_certificate = self.delete_control_space(field_list[8])
        __date_certificate = self.delete_control_space(field_list[9])
        # _____Owner_____
        self.__budget.setOwner(_owner)
        # _____Version-Date_____
        _version_date = _version_date.split(u"\\")
        _file_format = _version_date[0]
        if _file_format in self.__format_list:
            self.__file_format = _file_format
            print utils.mapping(_("FIEBDC format: $1"),(_file_format,))

        if len(_version_date) > 1:
            _date = _version_date[1]
            if _date != u"":
                _parsed_date = self.parseDate(_date)
                if _parsed_date is not  None:
                    self.__budget.setDate(_parsed_date)
        # _____Generator_____
        # ignored field
        print utils.mapping(_("FIEBDC file generated by $1"),(_generator,))
        # _____Header_Title_____
        _header_title = _header_title.split(u"\\")
        _header_title = [_title.strip() for _title in _header_title]
        _header = _header_title.pop(0)
        _header = [_item.encode("utf8") for _item in _header]
        _title = [ ]
        for _title_index in _header_title:
            if _title_index != u"":
                _title.append(_title_index)
        _title = [_item.encode("utf8") for _item in _title]
        if _header != u"":
            self.__budget.setTitleList([ _header, _title])
        # _____Characters_set_____
        # field parsed in readFile method
        # _____Comment_____
        if _comment != u"":
            self.__budget.setComment(_comment.encode("utf8"))
        # _____Data type_____
        # 1 -> Base data.
        # 2 -> Budget.
        # 3 -> Budget certificate.
        # 4 -> Base date update.
        try:
            _data_type = int(_data_type)
        except ValueError:
            _data_type = ""
        if _data_type == 3:
            # _____Number budget certificate_____
            try:
                _number_certificate = int(_number_certificate)
            except ValueError:
                _number_certificate = ""
            # _____Date budget certificate_____
            if _date_certificate != "":
                _parsed_date_certificate = self.parseDate(_date_certificate)
                if _parsed_date_certificate is None:
                    _date_certificate = ""
                else:
                    _date_certificate = _parsed_date_certificate
            self.__budget.setBudgetype(_data_type)
            self.__budget.setCertificateOrder(_number_certificate)
            self.__budget.setCertificateDate(_parsed_date_cerfificate)
        elif _data_type != "":
            self.__budget.setBudgeType(_data_type)
        self.__statistics.valid = self.__statistics.valid + 1

    def _parseK(self, field_list):
        """_parseK(self, field_list)
        
        field_list: field list of the record
            0- K: Coefficients
            1- { DN \ DD \ DS \ DR \ DI \ DP \ DC \ DM \ DIVISA \ }
            2- CI \ GG \ BI \ BAJA \ IVA
            3-
              A){ DRC \ DC \ DRO \ DFS \ DRS \ DFO \ DUO \ DI \ DES \ DN \
                 DD \ DS \ DIVISA \ }
              B){ DRC \ DC \ \ DFS \ DRS \ \ DUO \ DI \ DES \ DN \
                 DD \ DS \ DSP\ DEC\ DIVISA \ }
            4- [ n ]
        """
        # _____Number of fields_____
        # Any INFORMATION after last field separator is ignored
        # The record must have 3 fields
        # The last field is ignored, pyArq hate dll's
        if len(field_list) > 4:
             field_list = field_list[1:4]
        # The record must have 3 fields
        else:
             field_list = field_list[1:] + [""]*(4-len(field_list))
        # control character are erased: end of line, tab, space
        # _____Fields_____
        _field0 = self.delete_control_space(field_list[0])
        _field1 = self.delete_control_space(field_list[1])
        _field2 = self.delete_control_space(field_list[2])
        # _____Field 1_____
        if len(_field1) > 0 and _field1[-1] == u"\\":
            _field1 = _field1[:-1]
            # if there are a \ character at the end it must be erased
        _percentages = _field1.split(u"\\")
        if len(_percentages) > 5:
            _percentages = _percentages[:5]
        # If there are no sufficient subfields, the subfields are added
        # with empty value:""
        else:
            _percentages = _percentages + [u""]*(5-len(_percentages))
        _percentage_titles = [ "CI", "GG", "BI", "BAJA", "IVA" ]
        _percentage_dict = {}
        for _percentage_index in range(len(_percentages)):
            try:
                _percentage = int(_percentages[_percentage_index])
            except ValueError:
                _percentage = ""
            _percentage_dict[_percentage_titles[_percentage_index]] = \
                _percentage
        self.__budget.setPercentages(_percentage_dict)
        # _____Field 0 and 1_____
        # Default number of decimal places
        # Number of titles in ~V record
        _title_num = len(self.__budget.getTitleList()[1])
        if _title_num == 0: _title_num = 1
        # If the field 2 is empty, the field 0 is readed
        if _field2 == u"":
            # _____Field 0_____
            if _field0[-1] == u"\\":
                _field0 = _field0[:-1]
                # if there are a \ character at the end it must be erased
            _decimal_list = _field0.split(u"\\")
            _decimal_index = 0
            if len(_decimal_list)%9 != 0:
                # if it is not multiple of 9, empty subfield are added
                _decimal_list = _decimal_list + [""]*(9 - \
                                len(_decimal_list)%9)
            # The number of decimal values is the same as the numbers of 
            # titles in the V record
            if len(_decimal_list)//9 > _title_num:
                _decimal_list = _decimal_list[:_title_num*9]
            elif len(_decimal_list)//9 < _title_num:
                _decimal_list = _decimal_list + _decimal_list[-9:] * \
                                (_title_num-(len(_decimal_list)//9))
            while _decimal_index <= len(_decimal_list)-9:
                _decimals = _decimal_list[_decimal_index:(_decimal_index + 9)]
                _forlist = range(len(_decimals)-1)
                for _index in range(len(_decimals)):
                    try:
                        #TODO: test this
                        _decimals[_index] = int(_decimals[_index])
                    except ValueError:
                        _decimals[_index] = ""
                _DN = _decimals[0]
                _DD = _decimals[1]
                _DS = _decimals[2]
                _DR = _decimals[3]
                _DI = _decimals[4]
                _DP = _decimals[5]
                _DC = _decimals[6]
                _DM = _decimals[7]
                _DIVISA = _decimals[8]
                _percentage_dict = {"DN" : _DN,
                                    "DD" : _DD,
                                    "DSP" : _DS,
                                    "DS" : _DS,
                                    "DFC" : _DR,
                                    "DFPU" : _DR,
                                    "DFUO" : _DR,
                                    "DFA" : _DR,
                                    "DRC" : _DR,
                                    "DRPU" : _DR,
                                    "DRUO" : _DR,
                                    "DRA" : _DR,
                                    "DP" : _DC,
                                    "DC" : _DC,
                                    "DPU" : _DC,
                                    "DUO" : _DC,
                                    "DEA" : _DC,
                                    "DES" : _DC,
                                    "DIR" : _DI,
                                    "DIRC" : _DI,
                                    "DCD" : _DP,
                                    "DIVISA": _DIVISA }
                _decimal_index = _decimal_index + 9
                self.__budget.setDecimals(_percentage_dict,
                                          (_decimal_index//9))
        else:
            # _____Field 3_____
            if _field2[-1] == "\\":
                _field2 = _field2[:-1]
                # if there are a \ character at the end it must be erased
            _decimal_list = _field2.split("\\")
            # test if the Divisa subfield is 12 or 14 position
            # Divisa is the only Alphanumeric subfield
            # "no_float": "[^0-9.]"
            if len(_decimal_list) >= 13 and \
               self.__pattern["no_float"].search(_decimal_list[12]):
                _multiple = 13
            elif len(_decimal_list) >= 15 and \
               self.__pattern["no_float"].search(_decimal_list[14]):
                _multiple = 15
            else:
                if self.__file_format == "FIEBDC-3/2002":
                    _multiple = 13
                elif self.__file_format == "FIEBDC-3/2004":
                    _multiple = 13
                elif self.__file_format == "FIEBDC-3/2007":
                    _multiple = 15
                else:
                    _multiple = 15
            _decimal_index = 0
            if len(_decimal_list)%_multiple != 0 :
                # if it is not multiple of _multiple, empty subfield are added
                _decimal_list = _decimal_list + \
                                [""]*(_multiple-len(_decimal_list)%_multiple)
            # The number of decimal values is the same as the numbers of 
            # titles in the V record
            if len(_decimal_list)//_multiple > _title_num:
                _decimal_list = _decimal_list[:_title_num*_multiple]
            elif len(_decimal_list)//_multiple < _title_num:
                _decimal_list = _decimal_list + [_decimal_list[-_multiple:]]*\
                             (_title_num-(len(_decimal_list)//_multiple))
            while _decimal_index <= len(_decimal_list)-_multiple:
                _decimals = _decimal_list[_decimal_index:(_decimal_index +\
                            _multiple)]
                for _index in range(len(_decimals)-1):
                    try:
                        _decimals[_index] = int(_decimals[_index])
                    except:
                        _decimals[_index] = ""
                if _multiple == 13:
                    _DRC = _decimals[0]
                    _DC = _decimals[1]
                    _DRO = _decimals[2]
                    _DFS = _decimals[3]
                    _DRS = _decimals[4]
                    _DFO = _decimals[5]
                    _DUO = _decimals[6]
                    _DI = _decimals[7]
                    _DES = _decimals[8]
                    _DN = _decimals[9]
                    _DD = _decimals[10]
                    _DS = _decimals[11]
                    _DIVISA = _decimals[12]
                    _percentage_dict = {
                                  "DN" : _DN,
                                  "DD" : _DD,
                                  "DSP" : _DS,
                                  "DS" : _DS,
                                  "DFC" : _DFS,
                                  "DFPU" : _DRC,
                                  "DFUO" : _DFS,
                                  "DFA" : _DFS,
                                  "DRC" : _DRS,
                                  "DRPU" : _DRC,
                                  "DRUO" : _DRS,
                                  "DRA" : _DRS,
                                  "DP" : _DC,
                                  "DC" : _DC,
                                  "DPU" : _DC,
                                  "DUO" : _DUO,
                                  "DEA" : _DES,
                                  "DES" : _DES,
                                  "DIR" : _DI,
                                  "DIRC" : _DC,
                                  "DCD" : _DI,
                                  "DIVISA": _DIVISA,
                                }
                else: # _multiple == 15:
                    _DRC = _decimals[0]
                    _DC = _decimals[1]
                    _DRO = _decimals[2]
                    _DFS = _decimals[3]
                    _DRS = _decimals[4]
                    _DFO = _decimals[5]
                    _DUO = _decimals[6]
                    _DI = _decimals[7]
                    _DES = _decimals[8]
                    _DN = _decimals[9]
                    _DD = _decimals[10]
                    _DS = _decimals[11]
                    _DSP = _decimals[12]
                    _DEC = _decimals[13]
                    _DIVISA = _decimals[14]
                    _percentage_dict = {
                                  "DN" : _DN,
                                  "DD" : _DD,
                                  "DSP" : _DSP,
                                  "DS" : _DS,
                                  "DFC" : _DFS,
                                  "DFPU" : _DRC,
                                  "DFUO" : _DFS,
                                  "DFA" : _DFS,
                                  "DRC" : _DRS,
                                  "DRPU" : _DRC,
                                  "DRUO" : _DRS,
                                  "DRA" : _DRS,
                                  "DP" : _DC,
                                  "DC" : _DC,
                                  "DPU" : _DC,
                                  "DUO" : _DUO,
                                  "DEA" : _DEC,
                                  "DES" : _DES,
                                  "DIR" : _DI,
                                  "DIRC" : _DC,
                                  "DCD" : _DI,
                                  "DIVISA": _DIVISA}
                _decimal_index = _decimal_index + 13
                self.__budget.setDecimals(_percentage_dict,
                                           (_decimal_index//13))
        self.__statistics.valid = self.__statistics.valid +1

    def _parseC(self, field_list):
        """_parseC(self, field_list)
        
        field_list: field list of the record
            0- C: Record
            1- Code{\Code}
            2- [Unit]
            3- [Summary]
            4- {Price\}
            5- {Date\}
            6- [Type]
        """
        # _____number of fields_____
        # Any INFORMATION after last field separator is ignored
        if len(field_list) > 7:
            field_list = field_list[:7]
        # If there are no sufficient fields, the fields are added
        # with empty value:""
        else:
            field_list = field_list + [u""]*(7-len(field_list))
        # control character are erased: en of line, tab, space 
        # _____Fields_____
        _record_type = field_list[0]
        _codes = self.delete_control_space(field_list[1])
        _unit = self.delete_control_space(field_list[2])
        _summary = self.delete_control(field_list[3])
        _prices = self.delete_control_space(field_list[4])
        _dates = self.delete_control_space(field_list[5])
        _type = self.delete_control_space(field_list[6])
        # _____Code_____
        _codes = _codes.split(u"\\")
        if len(_codes) > 0:
            # parse the hierarchy of the first code
            # hierarchy: 0->root, 1->Chapter/subchapter, 2->other
            if len(_codes[0]) > 2 and _codes[0][-2:] == u"##":
                _hierarchy = 0
            elif len(_codes[0]) > 1 and _codes[0][-1:] == u"#":
                _hierarchy = 1
            else:
                _hierarchy = 2
            # "#" and "##" characters at the end of the code are erased
            # invalid characters are also erased
            # maximun len 20 characters
            _codes = [self.validateCode(_code) for _code in _codes]
        # empty codes are ignored
        while u"" in _codes:
            _codes.remove(u"")
        if len(_codes) > 0:
            #TODO: test this
            _code = _codes[0]
            _synonyms = [synonym.encode("utf8") for synonym in _codes]
        else:
            print _("Record C without a valid code")
            return
        # _____Unit_____
        # nothing to do
        # _____Summary_____
        # nothing to do
        # _____Price_____ and _____Dates_____
        # last \ is erased
        if len(_dates) > 0 and _dates[-1] == u"\\":
            _dates = _dates[:-1]
        if len(_prices) > 0 and _prices[-1] == u"\\":
            _prices = _prices[:-1]
        _dates = _dates.split(u"\\")
        _prices = _prices.split(u"\\")
        # number of prices = number of titles in "V" line
        # if there are no sufficient prices it takes the last price defined
        _title_num = len(self.__budget.getTitleList()[1])
        if _title_num == 0: _title_num = 1
        if len(_prices) > _title_num: _prices = _prices[:_title_num]
        elif len(_prices) < _title_num:
            _prices = _prices + [_prices[-1]]*(_title_num-len(_prices))
        # number of dates = number of prices
        # if there are no sufficient dates it takes the last date defined
        if len(_dates) > len(_prices): _dates = _dates[:len(_prices)]
        elif len(_dates) < len(_prices):
            _dates = _dates + [_dates[-1]]*(len(_prices)-len(_dates))
        for _index in range(len(_prices)):
            # TODO: lack to specify the number of decimals of the price
            try:
                _prices[_index] = float(_prices[_index])
            except:
                _prices[_index] = 0.0
            _parsed_date = self.parseDate(_dates[_index])
            if _parsed_date is None:
                _dates[_index] = ""
            else:
                _dates[_index] = _parsed_date
        # _____Type_____
        # 0 Without classifying
        #       EA  Auxiliary element
        #       EU  Unitary element
        #       EC  Complex element
        #       EF  Functional element
        #       OB  Construction site
        #       PA  Cost overrun
        #       PU  Unitary budget
        # 1 Labourforce 
        #       H   Labourforce
        # 2 Machinery and auxiliary equipment
        #       Q   Machinery
        #       %   Auxiliary equipment
        # 3 Building materials
        #       MC  Cement
        #       MCr Ceramic
        #       MM  Wood
        #       MS  Iron and steel
        #       ME  Energy
        #       MCu Copper
        #       MAl Aluminium
        #       ML  Bonding agents
        #       M   Others materials
        #  Hierarchy        type  subtype
        # 0->root         -> 0 -> None,OB
        # 1->[sub]chapter -> 0 -> None,PU
        # 2->Other        -> 0 -> None,EA,EU,EC,EF,PA
        #                    1 -> None,H
        #                    2 -> None,Q,%
        #                    3 -> None,MC,MCr,MM,MS,ME,MCu,Mal,ML,M
        if _hierarchy == 0:
            if _type == u"OB":
                _subtype = _type
                _type = 0
            elif _type == u"0" or _type == u"":
                _subtype = u""
                _type = 0
            else:
                print utils.mapping(_("Incorrect type ($1) in the code $2"),
                      (_type.encode("utf8"), _code.encode("utf8")))
                _type = 0
                _subtype = u""
        elif _hierarchy == 1:
            if _type == u"PU":
                _subtype = _type
                _type = 0
            elif _type == u"0" or _type == u"":
                _subtype = u""
                _type = 0
            else:
                print utils.mapping(_("Incorrect type ($1) in the code $2"),
                      (_type.encode("utf8"), _code.encode("utf8")))
                _type = 0
                _subtype = u""
        else:
            if _type == u"EA" or _type == u"EU" or _type == u"EC" or \
               _type == u"EF" or _type == u"PA":
                _subtype = _type
                _type = 0
            elif _type == u"H":
                _subtype = _type
                _type = 1
            elif _type == u"Q" or _type == u"%":
                _subtype = _type
                _type = 2
            elif _type == u"MC" or _type == u"MCr" or _type == u"MM" or \
                 _type == u"MS" or _type == u"ME" or _type == u"MCu" or \
                 _type == u"Mal" or _type == u"ML" or _type == u"M":
                _subtype = _type
                _type = 3
            elif _type == u"0" or _type == u"1" or _type == u"2" or \
                 _type == u"3":
                _subtype = u""
                _type = int(_type)
            elif _type == u"":
                _subtype = u""
                _type = 0
            else:
                print utils.mapping(_("Incorrect type ($1) in the code $2"),
                      (_type.encode("utf8"), _code.encode("utf8")))
                _type = 0
                _subtype = u""
        self.__budget.setRecord(_code.encode("utf8"), _synonyms, _hierarchy,
            _unit.encode("utf8"), _summary.encode("utf8"),
            _prices, _dates, _type, _subtype.encode("utf8"))
        self.__statistics.valid = self.__statistics.valid + 1
    
    def _parseDY(self, field_list):
        """_parseDY(self, field_list)
        
        field_list: field list of the record
            0- D or Y: DECOMPOSITION or ADD DECOMPOSITION
            1- Parent Code
            2- <Child Code\ [Factor]\ [Yield]>
        """
        # _____number of fields_____
        # Any INFORMATION after last field separator is ignored
        # The record must have 3 fields
        if len(field_list) > 3:
            field_list = field_list[:3]
        # If there are no sufficient fields, the fields are added
        # with empty value:""
        else:
            field_list = field_list + [u""]*(3-len(field_list))
        # control character are erased: end of line, tab, space 
        # _____Fields_____
        _record_type = field_list[0]
        _code = self.delete_control_space(field_list[1])
        _children = self.delete_control_space(field_list[2])
        # _____Code_____
        # "#" and "##" characters at the end of the code are erased
        # invalid characters are also erased
        _code = self.validateCode(_code)
        # _____children_____
        # TODO: test the number of decimals in factor an yield values
        _children = _children.split(u"\\")
        _children_list = [ ]
        _child_index = 0
        while _child_index < len(_children)-3:
            # _____subfields_____
            _child_code = _children[_child_index]
            _factor = _children[_child_index+1]
            _yield = _children[_child_index+2]
            # _____child_code_____
            _child_code = self.validateCode(_child_code)
            # _____factor_____
            if _factor != u"":
                try:
                    _factor = float(_factor)
                except ValueError:
                    print utils.mapping(_("ValueError loadig the "\
                          "descomposition of the record $1, the factor "\
                          "of the child $2 must be a float number and "\
                          "can not be $3, seted default value 1.0"),
                          (_code.encode("utf8"), _child_code.encode("utf8"), _factor.encode("utf8")))
                    _factor = 1.0
            #____yield___
            if _yield != u"":
                try:
                    _yield = float(_yield)
                except ValueError:
                    print utils.mapping(_("ValueError loading the "\
                          "descomposition of the record $1, the yield of "\
                          "the child $2, must be a float number and can"\
                          "not be $3,  seted default value 1.0"),
                           (_code.encode("utf8"), _child_code.encode("utf8"), _factor.encode("utf8")))
                    _yield = 1.0
            if _child_code != u"" and _code != u"":
                _children_list.append([_child_code, _factor, _yield ])
            if _record_type == u"D":
                _position = _child_index / 3
            else: #_record_type == "Y"
                _position = -1
            self.__budget.setTree(_code.encode("utf8"), _child_code.encode("utf8"), _position, _factor, 
                _yield, "", "", "", "")
            _child_index = _child_index + 3
        self.__statistics.valid = self.__statistics.valid +1

    def _parseT(self, field_list):
        """_parseT(self, field_list)
        
        field_list: field list of the record
            0- T: Text
            1- Record code
            2- Description text
        """
        # _____Number of fields_____
        # Any INFORMATION after last field separator is ignored
        # The record must have 3 fields
        if len(field_list) > 3:
            field_list = field_list[0:3]
        field_list = field_list[1:]
        if len(field_list) != 2:
            return
        # control character are erased: end of line, tab, space
        # _____Fields_____
        _code = self.delete_control_space(field_list[0])
        _text = field_list[1]
        # _____Code_____
        # "#" and "##" characters at the end of the code are erased
        # invalid characters are also erased
        _code = self.validateCode(_code) 
        # _____Text_____
        self.__budget.setText(_code.encode("utf8"), _text.encode("utf8"))
        self.__statistics.valid = self.__statistics.valid + 1

    def _parseMN(self, field_list):
        """_parseMN(self, field_list)
        
        field_list: field list of the record
            0- M or N: MEASURE or ADD MEASURE
            1- [Parent Code\]Child Code
            2- {Path\}
            3- TOTAL MEASURE
            4- {Type\Comment\Unit\Length\Width\Height\}
            5- [Label]
        """
        # _____Number of fields_____
        # Any INFORMATION after last field separator is ignored
        # The record must have 6 fields
        if len(field_list) > 6:
            field_list = field_list[:6]
        # If there are no sufficient fields, the fields are added
        # with empty value:""
        else:
            field_list = field_list + [u""]*(6-len(field_list))
        # control character are erased: end of line, tab, space
        # _____Fields_____
        _record_type = field_list[0]
        _codes = self.delete_control_space(field_list[1])
        _path = self.delete_control_space(field_list[2])
        _total = self.delete_control_space(field_list[3])
        _lines = self.delete_control(field_list[4])
        _label = self.delete_control_space(field_list[5])
        # _____Codes_____
        _code_list = _codes.split(u"\\")
        # "#" and "##" characters at the end of the code are erased
        # invalid characters are also erased
        if len(_code_list) == 2:
            _parent_code = self.validateCode(_code_list[0]) 
            if _parent_code == u"":
                _parent_code = None
            else:
                _parent_code = _parent_code.encode("utf8")
            _child_code =  self.validateCode(_code_list[1])
        elif len(_code_list) == 1:
            _child_code =  self.validateCode(_code_list[0])
            _parent_code = None
        else:
            print utils.mapping(_("Invalid codes in $1 record, codes $2"),
                  (_record_type.encode("utf8"), _codes.encode("utf8")))
            return
        if _child_code == u"":
            print utils.mapping(_("Empty child code in $1 record, codes: "\
                  "$2"), (_record_type.encode("utf8"), _codes.encode("utf8")))
            return
        if _parent_code == None:
            # Empty parent code. No-estructured measures.
            pass

        # _____Path_____
        _path_list = _path.split( u"\\" )
        if len(_path_list) > 0:
            while len(_path_list) > 0 and _path_list[-1] == u"":
                _path_list = _path_list[:-1]
            if len(_path_list) == 0:
                # Empty path. No-estructured measures. Path fixed to -2
                _path = -2
            else:
                _path = _path_list[-1]
            try:
                _path = int(_path)
            except ValueError:
                print utils.mapping(_("Invalid path in $1 record, "\
                      "codes $2"), (_record_type.encode("utf8"), _codes.encode("utf8")))
                return
            if _path > 0:
                _path -= 1
        else:
            _path = -2
        # _____Total_____
        try:
            _total = float(_total)
        except ValueError:
            print utils.mapping(_("Invalid Total Measure value in $1 "\
                  "record, codes $2. Total fixed to 0."),
                  (_record_type.encode("utf8"), _codes.encode("utf8")))
            _total = 0
        # _____Measure lines_____
        _lines = _lines.split(u"\\")
        _line_index = 0
        _line_list = [ ]
        while _line_index < len(_lines)-6:
            _linetype = _lines[_line_index]
            if _linetype == u"":
                _linetype = 0
            elif _linetype == u"1" or _linetype == u"2" or \
                   _linetype == u"3":
                    _linetype = int(_linetype)
            else:
                _linetype = 0
            _comment= _lines[_line_index + 1]
            if _linetype == 3:
                # "formula": ".*[^0123456789\.()\+\-\*/\^abcdp ].*"
                if self.__pattern["formula"].match(_comment):
                    print utils.mapping(_("The comment is not a formula or "\
                          "its have invalid characters, in the $1 record, "\
                          "codes $2"), (_record_type.encode("utf8"), _codes.encode("utf8")))
                    return
                else:
                    _formula = _comment.encode("utf8")
                    _comment = ""
            else:
                _formula = ""
                _comment = _comment.encode("utf8")
            _units = _lines[_line_index + 2]
            _units = self.__pattern["no_float"].sub(u"", _units)
            _length = _lines[_line_index + 3]
            _length = self.__pattern["no_float"].sub(u"", _length)
            _width = _lines[_line_index + 4]
            _width  = self.__pattern["no_float"].sub(u"", _width)
            _height = _lines[_line_index + 5]
            _height  = self.__pattern["no_float"].sub(u"", _height)

            try:
                if _units != u"":
                    _units = float(_units)
                if _length != u"": _length = float(_length)
                if _width != u"": _width = float(_width)
                if _height != u"": _height = float(_height)
            except ValueError:
                print utils.mapping(_("The measure values are not float "\
                      "numbers, code $1"), (_codes.encode("utf8"),))
                return
            # Prevent subfield units remains empty.
            if (_units == u"" and (_length != u"" or _width != u""
                                   or _height != u"")):
                _units = 1.0
            _line_list.append([_linetype, _comment, _units,
                               _length, _width, _height, _formula])
            _line_index = _line_index + 6
        self.__budget.setTree(_parent_code, _child_code.encode("utf8"), _path, "", "",
                           _total, _line_list, _label.encode("utf8"), _record_type.encode("utf8"))
        self.__statistics.valid = self.__statistics.valid + 1

    def _parseW(self, field_list):
        """_parseW(self, field_list)
        
        field_list: field list of the record
            0- W: Geografical field
            1- Field Code
            2- Field
        """
        # _____Number of fields_____
        # Any INFORMATION after last field separator is ignored
        # The record must have 2 fields
        if len(field_list) >= 2:
            field_list = field_list[1:2]
        else:
            return
        # control character are erased: end of line, tab, space
        # _____Fields_____
        _code_fields = field_list[0]
        # last \ is erased
        if len(_code_fields) and _code_fields[-1] == u"\\":
            _code_fields = _code_fields[:-1]
        _code_fields = _code_fields.split(u"\\")
        _field_dict = {}
        _field_index = 0
        while _field_index < len(_code_fields)-1:
            # _____subfields_____
            _field_code = _code_fields[_field_index]
            _field_title = _code_fields[_field_index+1]
            # control character are erased: end of line, tab, space
            # _____section_code_____
            #"control": "[\t \n\r]"
            _field_code = self.delete_control_space(_field_code)
            # _____section_title_____
            if _field_code != u"":
                _field_dict[_field_code.encode("utf8")] = _field_title.encode("utf8")
            _field_index = _field_index + 2
        self.__budget.setSheetFields(_field_dict)
        self.__statistics.valid = self.__statistics.valid +1
    
    def _parseL(self, field_list):
        """_parseL(self, field_list)
        
        field_list: field list of the record
            0- L: Sheet of Conditions 1
            A:
                1- Empty
                2- {Section Code\Section Title}
            B:
                1- Record Code
                2- {Section Code\Section Text}
                3- {Section Code\RTF file}
                4- {Section Code\HTM file}
        """
        # _____Number of fields_____
        # The record must have at least 3 fields
        if len(field_list) < 3:
            return
        _code = field_list[1]
        if _code == u"":
            # A: Section Titles
            # Any INFORMATION after last field separator is ignored
            # The record must have 3 fields
            if len(field_list) > 3:
                field_list = field_list[0:3]
            field_list = field_list[1:3]
            # _____Fields_____
            _section_codes = field_list[1]
            # last \ is erased
            if len(_section_codes) and _section_codes[-1] == u"\\":
                _section_codes = _section_codes[:-1]
            _section_codes = _section_codes.split(u"\\")
            _section_dict = {}
            _section_index = 0
            while _section_index < len(_section_codes)-1:
                # _____subfields_____
                _section_code = _section_codes[_section_index]
                
                _section_title = _section_codes[_section_index+1]
                # control character are erased: end of line, tab, space
                # _____section_code_____
                _section_code = self.delete_control_space(_section_code)
                # _____section_title_____
                _section_title = self.delete_control_space(_section_title)
                if _section_code != u"":
                    _section_dict[_section_code.encode("utf8")] = _section_title.encode("utf8")
                _section_index = _section_index + 2
            self.__budget.setSheetSections(_section_dict)
            self.__statistics.valid = self.__statistics.valid +1
            
        else:
            # Any INFORMATION after last field separator is ignored
            # The record must have 5 fields
            if len(field_list) > 5:
                field_list = field_list[0:5]
            field_list = field_list[1:]
            # _____Fields_____
            # _____Record Code_____
            _record_code = self.delete_control_space(field_list[0])
            # "#" and "##" characters at the end of the code are erased
            # invalid characters are also erased
            _record_code = self.validateCode(_record_code)
            _scodes_text = field_list[1]
            if _scodes_text == u"":
                # TODO: rtf and html files
                print "Html and rtf files not yet implemented in ~L record"
            else:
                # _____Section-code_Section-text_____
                # last \ is erased
                if len(_scodes_text) and _scodes_text[-1] == u"\\":
                    _scodes_text = _scodes_text[:-1]
                _scodes_text = _scodes_text.split(u"\\")
                _paragraph_dict = {}
                _section_dict = {}
                _section_index = 0
                while _section_index < len(_scodes_text)-1:
                    # _____subfields_____
                    _section_code = _scodes_text[_section_index]
                    _section_text = _scodes_text[_section_index+1]
                    # control character are erased: end of line, tab, space
                    # _____section_code_____
                    _section_code = self.delete_control_space(_section_code)
                    # _____section_text_____
                    if _section_code != u"" and _section_text != u"":
                        #-# paragraph #-#
                        _paragraph_code = _record_code + _section_code + u"*"
                        _paragraph_dict[ _paragraph_code.encode("utf8") ] = _section_text.encode("utf8")
                        _section_dict[_section_code.encode("utf8")] = _paragraph_code.encode("utf8")
                    _section_index = _section_index + 2
                self.__budget.setSheetParagraphs(_paragraph_dict)
                self.__budget.setSheetRecord(_record_code.encode("utf8"), "*", _section_dict)
                self.__statistics.valid = self.__statistics.valid +1
    
    def _parseQ(self, field_list):
        """_parseQ(self, field_list)
        
        field_list: field list of the record
            0- Q: Sheet of Conditions 2
            1- Record Code
            2- {Section Code\Paragraph key\{Field key;}\}|
        """
        # _____Number of fields_____
        # The record must have at least 3 fields
        if len(field_list) < 3:
            return
        _code = field_list[1]
        # Any INFORMATION after last field separator is ignored
        # The record must have 3 fields
        if len(field_list) > 3:
            field_list = field_list[0:3]
        field_list = field_list[1:]
        # _____Fields_____
        # _____Record Code_____
        _record_code = self.delete_control_space(field_list[0])
        # "#" and "##" characters at the end of the code are erased
        # invalid characters are also erased
        _record_code = self.validateCode(_record_code)
        _scodes_pkey = field_list[1]
        # last \ is erased
        if len(_scodes_pkey) and _scodes_pkey[-1] == u"\\":
            _scodes_pkey = _scodes_pkey[:-1]
        _scodes_pkey = _scodes_pkey.split(u"\\")
        _field_dict = {}
        _section_index = 0
        while _section_index < len(_scodes_pkey) -1:
            # _____subfields_____
            _section_code = _scodes_pkey[_section_index]
            _paragraph_key = _scodes_text[_section_index+1]
            _field_keys = _scodes_text[_section_index+2]
            # control character are erased: end of line, tab, space
            # _____section_code_____
            _section_code = self.delete_control_space(_section_code)
            # _____section_text_____
            _paragraph_key = self.delete_control_space(_paragraph_key)
            # _____Fields keys_____
            _field_keys = self.delete_control_space(_field_keys)
            # last ; is erased
            if len(_field_keys) and _field_keys[-1] == u";":
                _field_keys = _field_keys[:-1]
            _field_keys_list = _scodes_pkey.split(u";")
            for _field_key in _field_keys_list:
                if _field_key != u"" and _section_code != u"" and \
                   _paragraph_key != u"":
                    if _field_key in _field_dict:
                        _section_dict = _field_dict[_field_key]
                    else:
                        _section_dict = {}
                        _field_dict[_field_key] = _section_dict
                    _section_dict[_section_code.encode("utf8")] = _paragraph_code.encode("utf8")
            _section_index = _section_index + 3
        for _field, _section_dict in _field_dict.iteritems():
            self.__budget.setSheetRecord(_record_code.encode("utf8"), _field.encode("utf8"), _section_dict)
        self.__statistics.valid = self.__statistics.valid +1
    
    def _parseJ(self, field_list):
        """_parseJ(self, field_list)
        
        field_list: field list of the record
            0- J: Sheet of Conditions 3
            1- Paragraph code
            2- [Paragraph text]
            3- [RTF file]
            4- [HTML file]
        """
        # _____Number of fields_____
        # The record must have at least 3 fields
        if len(field_list) < 3:
            return
        # Any INFORMATION after last field separator is ignored
        # The record must have 5 fields
        if len(field_list) > 5:
            field_list = field_list[0:5]
        field_list = field_list[1:]
        # _____Fields_____
        # _____Paragraph code_____
        _paragraph_code = self.delete_control_space(field_list[0])
        # _____Paragraph text_____
        _paragraph_text = field_list[1]
        if _paragraph_text == u"":
            # TODO: rtf and html files
            print "Html and rtf files not yet implemented in ~J record"
        else:
            self.__budget.setSheetParagraph(paragraph_code.encode("utf8"), paragraph_text.encode("utf8"))
            self.__statistics.valid = self.__statistics.valid +1
    
    def _parseG(self, field_list):
        """_parseG(self, field_list)
        
        field_list: field list of the record
            0- G: Grafic info
            1- record code
            2- <grafic_file.ext\>
        """
        # _____Number of fields_____
        # The record must have at least 3 fields
        if len(field_list) < 3:
            return
        # Any INFORMATION after last field separator is ignored
        # The record must have 3 fields
        if len(field_list) > 3:
            field_list = field_list[0:3]
        field_list = field_list[1:]
        # _____Fields_____
        # _____Record Code_____
        _record_code = self.delete_control_space(field_list[0])
        # "#" and "##" characters at the end of the code are erased
        # invalid characters are also erased
        _record_code = self.validateCode(_record_code)
        # _____Grafic files_____
        _grafic_files = self.delete_control(field_list[1])
        # _____subfields_____
        # last \ is erased
        if len(_grafic_files) and _grafic_files[-1] == u"\\":
            _grafic_files = _grafic_files[:-1]
        _grafic_file_list = _grafic_files.split(u"\\")
        _tested_grafic_file_list = []
        for _grafic_file in _grafic_file_list:
            _str_grafic_file = _grafic_file.encode("utf8")
            _path = os.path.dirname(self.__filename)
            _grafic_file_path = os.path.join(_path, _str_grafic_file)
            if os.path.exists(_grafic_file_path):
                _tested_grafic_file_list.append(_grafic_file_path)
            else:
                _name_ext = os.path.splitext(_str_grafic_file)
                _grafic_file_name = _name_ext[0]
                _grafic_file_ext = _name_ext[1]
                _grafic_file_name_u = _grafic_file_name.upper()
                _grafic_file_name_l = _grafic_file_name.lower()
                _grafic_file_ext_u = _grafic_file_ext.upper()
                _grafic_file_ext_l = _grafic_file_ext.lower()
                _uu = _grafic_file_name_u + _grafic_file_ext_u
                _ul = _grafic_file_name_u + _grafic_file_ext_l
                _lu = _grafic_file_name_l + _grafic_file_ext_u
                _ll = _grafic_file_name_l + _grafic_file_ext_l
                _grafic_file_path_uu = os.path.join(_path, _uu)
                _grafic_file_path_ul = os.path.join(_path, _ul)
                _grafic_file_path_lu = os.path.join(_path, _lu)
                _grafic_file_path_ll = os.path.join(_path, _ll)
                if os.path.exists(_grafic_file_path_uu):
                    _tested_grafic_file_list.append(_grafic_file_path_uu)
                elif os.path.exists(_grafic_file_path_ul):
                    _tested_grafic_file_list.append(_grafic_file_path_ul)
                elif os.path.exists(_grafic_file_path_lu):
                    _tested_grafic_file_list.append(_grafic_file_path_lu)
                elif os.path.exists(_grafic_file_path_ll):
                    _tested_grafic_file_list.append(_grafic_file_path_ll)
                else:
                    print utils.mapping(_("The file $1 do not exist"),
                        (_grafic_file_path,))
        if len(_grafic_file_list) > 0:
            for _grafic_file in _tested_grafic_file_list:
                self.__budget.addFile(_record_code.encode("utf8"), _grafic_file, "img", "")
            self.__statistics.valid = self.__statistics.valid +1
    
    def _parseE(self, field_list):
        """_parseE(self, field_list)
        
        field_list: field list of the record
            0- E: Company
            1- company Code
            2 [ summary ]
            3- [ name ]
            4- { [ type ] \ [ subname ] \ [ address ] \ [ postal_code ]
              \ [ town ] \ [ province ] \ [ country ] \ { phone; } 
              \ { fax; }  \ {contact_person; } \ }
            5- [ cif ] \ [ web ] \ [ email ] \
        """
        
        # _____Number of fields_____
        # Any INFORMATION after last field separator is ignored
        # The record must have 6 fields
        if len(field_list) > 6:
            field_list = field_list[1:6]
        # If there are no sufficient fields, the fields are added
        # with empty value:""
        else:
            field_list = field_list[1:] + [u""]*(6-len(field_list))
        # _____Fields_____
        # _____company Code_____
        _company_code = self.delete_control_space(field_list[0])
        if _company_code == u"":
            return
        # _____Summary_____

        _sumamary = self.delete_control(field_list[1])
        # _____Name_____
        _name = self.delete_control(field_list[2])
        # _____local_offices_____
        _local_offices = self.delete_control(field_list[3])
        # _____subfields of local_offices_____
        # last \ is erased
        if len(_local_offices) and _local_offices[-1] == u"\\":
            _local_offices = _local_offices[:-1]
        _local_offices_list = _local_offices.split(u"\\")
        # If there are no sufficent subfields, the subfields are added 
        # whith empty value
        _nsub = len(_local_offices_list) % 10
        if _nsub != 0:
            _local_offices_list = _local_offices_list + \
                                   [u""]*(10-len(field_list))
        _local_offices = []
        _local_offices_index = 0
        while _local_offices_index < len(_local_offices_list)-9:
            # _____subfields_____
            _type = _local_offices_list[_local_offices_index]
            _subname = _local_offices_list[_local_offices_index+1]
            _address = _local_offices_list[_local_offices_index+2]
            _postal_code = _local_offices_list[_local_offices_index+3]
            _town = _local_offices_list[_local_offices_index+4]
            _province = _local_offices_list[_local_offices_index+5]
            _country = _local_offices_list[_local_offices_index+6]
            _phone = _local_offices_list[_local_offices_index+7]
            # last ; is erased
            if len(_phone) and _phone[-1] == u";":
                _phone = _phone[:-1]
            _phone_list = _phone.split(u";")
            _phone_list = [_phone.encode("utf8") for _phone in _phone_list]
            _fax = _local_offices_list[_local_offices_index+8]
            # last ; is erased
            if len(_fax) and _fax[-1] == u";":
                _fax = _fax[:-1]
            _fax_list = _fax.split(u";")
            _fax_list = [_fax.encode("utf8") for _fax in _fax_list]
            _contact_person = _local_offices_list[_local_offices_index+9]
            if _type != u"" or _subname != u"" or _address != u"" or \
               _postal_code != u"" or _town != u"" or _province != u"" or \
               _country != u"" or _phone != u"" or _fax != u"" or \
               _contact_person != u"":
                _local_offices.append([_type.encode("utf8"), _subname.encode("utf8"),
                                       _address.encode("utf8"), _postal_code.encode("utf8"),
                                       _town.encode("utf8"), _province.encode("utf8"),
                                       _country.encode("utf8"), _phone_list,
                                       _fax_list, _contact_person.encode("utf8")])
            _local_offices_index = _local_offices_index + 10
        # _____cif web email_____
        _c_w_e = self.delete_control_space(field_list[4])
        # last \ is erased
        if len(_c_w_e) and _c_w_e[-1] == u"\\":
            _c_w_e = _c_w_e[:-1]
        _c_w_e_list = _c_w_e.split(u"\\")
        # _____subfields_____
        # If there are no sufficient fields, the fields are added
        # with empty value:""
        _c_w_e_list = _c_w_e_list + [u""]*(3-len(_c_w_e_list))
        _cif = _c_w_e_list[0]
        _web = _c_w_e_list[1]
        _email = _c_w_e_list[2]
        self.__budget.setCompany(_company_code.encode("utf8"),
                    _sumamary.encode("utf8"), _name.encode("utf8"), 
                    _local_offices, _cif.encode("utf8"),
                    _web.encode("utf8"), _email.encode("utf8"))
        self.__statistics.valid = self.__statistics.valid +1
    
    def _parseX(self, field_list):
        """_parseX(self, field_list)
        
        field_list: field list of the record
            A)
                0- X: Tecnical information
                1- Empty
                2- < TI_Code \ TI_Descitption \ TI_Unit >
            B)
                0- X: Tecnical information
                1- Record_code
                2- < TI_Code \ TI_value >
        """
        # Tecnical information
        # The record must have at least 3 fields
        if len(field_list) < 3:
            return
        # Any INFORMATION after last field separator is ignored
        # The record must have 3 fields
        if len(field_list) > 3:
            field_list = field_list[0:3]
        field_list = field_list[1:]
        # _____Fields_____
        # "control": "[\t \n\r]"
        _field_1 = self.delete_control_space(field_list[0])
        _field_2 = self.delete_control_space(field_list[1])
        if _field_1 == u"":
            # A)
            _field_2_list = _field_2.split(u"\\")
            _ti_index = 0
            while _ti_index < len(_field_2_list)-3:
                _ti_code = _field_2_list[_ti_index]
                _ti_description = _field_2_list[_ti_index+1]
                _ti_unit = _field_2_list[_ti_index+2]
                if _ti_code != "":
                    self.__budget.addTecInfo(_ti_code.encode("utf8"), _ti_description.encode("utf8"),
                                             _ti_unit.encode("utf8"))
                _ti_index = _ti_index + 3
        else:
            # B)
            # "#" and "##" characters at the end of the code are erased
            # invalid characters are also erased
            _record_code = self.validateCode(_field_1)
            _field_2_list = _field_2.split(u"\\")
            _ti_index = 0
            _ti_dict = {}
            while _ti_index < len(_field_2_list)-2:
                _ti_code = _field_2_list[_ti_index]
                _ti_value = _field_2_list[_ti_index+1]
                if _ti_code != u"" and _ti_value != u"":
                    _ti_dict[_ti_code.encode("utf8")] = _ti_value.encode("utf8")
                _ti_index = _ti_index + 2
            self.__budget.setTecnicalInformation(_record_code.encode("utf8"), _ti_dict)
        self.__statistics.valid = self.__statistics.valid +1

    def _parseF(self, field_list):
        """_parseF(self, field_list)
        
        field_list: field list of the record
            0- F: Files
            1- Record code
            2- { Type \ { Filenames; } \ [Description] }
        """

        # _____Number of fields_____
        # The record must have at least 3 fields
        if len(field_list) < 3:
            return
        # Any INFORMATION after last field separator is ignored
        # The record must have 3 fields
        if len(field_list) > 3:
            field_list = field_list[0:3]
        field_list = field_list[1:]
        # _____Fields_____
        # _____Record Code_____
        _record_code = self.delete_control_space(field_list[0])
        # "#" and "##" characters at the end of the code are erased
        # invalid characters are also erased
        _record_code = self.validateCode(_record_code)
        # _____Grafic files_____
        _files = self.delete_control(field_list[1])
        # _____subfields_____
        # last \ is erased
        if len(_files) and _files[-1] == u"\\":
            _files = _files[:-1]
        _files_list = _files.split(u"\\")
        # adding empty subfiels if necesary
        if len(_files_list)%3 > 0:
            _files_list.extend[u""]*(3 - len(_files_list)%3)
        _file_index = 0
        _tested_files_list = []
        while _file_index < len(_files_list)-3:
            _type = _files_list[_file_index].replace(u" ",u"")
##            _types = {
##                "0": _("others"),
##                "1": _("características técnicas y de fabricación"),
##                "2": _("manual de colocación, uso y mantenimiento"),
##                "3": _("certificado/s de elementos y sistemas"),
##                "4": _("normativa y bibliografía"),
##                "5": _("tarifa de precios"),
##                "6": _("condiciones de venta"),
##                "7": _("carta de colores"),
##                "8": _("ámbito de aplicación y criterios selección"),
##                "9": _("cálculo de elementos y sistemas"),
##                "10": _("presentación, datos generales, objetivos, etc. de "\
##                        "empresa"),
##                "11": _("certificado/s de empresa"),
##                "12": _("obras realizadas")}
            _types = [u"0", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"10",
                      u"11", u"12"]
            if not _type in _types:
                _type = u"0"
            _filenames = _files_list[_file_index + 1]
            _description = _files_list[_file_index + 2]
            _file_index += 3
            if len(_filenames) and _filenames[-1] == u";":
                _files = _files[:-1]
            _filenames_list = _files.split(u";")
            _path = os.path.dirname(self.__filename)
            for _filename in filenames_list:
                _file_path = os.path.join(_path, _filename.encode("utf8"))
                if os.path.exists(_file_path):
                    _tested_files_list.append([_file_path, _type.encode("utf8"),
                                               _description.encode("utf8")])
                else:
                    _name_ext = os.path.splitext(_filename)
                    _file_name = _name_ext[0]
                    _file_ext = _name_ext[1]
                    _file_name_u = _file_name.upper()
                    _file_name_l = _file_name.lower()
                    _file_ext_u = _file_ext.upper()
                    _file_ext_l = _file_ext.lower()
                    _uu = _file_name_u + _file_ext_u
                    _ul = _file_name_u + _file_ext_l
                    _lu = _file_name_l + _file_ext_u
                    _ll = _file_name_l + _file_ext_l
                    _file_path_uu = os.path.join(_path, _uu)
                    _file_path_ul = os.path.join(_path, _ul)
                    _file_path_lu = os.path.join(_path, _lu)
                    _file_path_ll = os.path.join(_path, _ll)
                    if os.path.exists(_file_path_uu):
                        _tested_files_list.append([_file_path_uu, _type.encode("utf8"),
                                                   _description.encode("utf8")])
                    elif os.path.exists(_grafic_file_path_ul):
                        _tested_files_list.append([_file_path_ul, _type.encode("utf8"),
                                                   _description.encode("utf8")])
                    elif os.path.exists(_grafic_file_path_lu):
                        _tested_files_list.append([_file_path_lu, _type.encode("utf8"),
                                                   _description.encode("utf8")])
                    elif os.path.exists(_grafic_file_path_ll):
                        _tested_files_list.append([_file_path_ll, _type.encode("utf8"),
                                                   _description.encode("utf8")])
                    else:
                        print utils.mapping(_("The file $1 do not exist"),
                            (_file_path,))
        if len(_tested_files_list) > 0:
            for _file in _tested_file_list:
                self.__budget.addFile(_record_code.encode("utf8"), _file[0], file[1], file[2])
        self.__statistics.valid = self.__statistics.valid +1

    def _parseB(self, field_list):
        """_parseB(self, field_list)
        
        field_list: field list of the record
            0- B: Change code
            1- Record Code
            2- New code
        """
        # _____Number of fields_____
        # Any INFORMATION after last field separator is ignored
        # The record must have 3 fields
        if len(field_list) > 3:
            field_list = field_list[0:3]
        field_list = field_list[1:]
        if len(field_list) != 2:
            return
        # control character are erased: end of line, tab, space
        # _____Fields_____
        _code = self.delete_control_space(field_list[0])
        _new_code = self.delete_control_space(field_list[1])
        # _____Codes_____
        # "#" and "##" characters at the end of the code are erased
        # invalid characters are also erased
        _code = self.validateCode(_code)
        _new_code = self.validateCode(_new_code)
        # change code
        self.__budget.changeCode(_code, _new_code)
        self.__statistics.valid = self.__statistics.valid + 1

    def _parseA(self, field_list):
        """_parseA(self, field_list)
        
        field_list: field list of the record
            0- A: Labels
            1- Record Code
            2- <Label\>
        """
        # _____Number of fields_____
        # Any INFORMATION after last field separator is ignored
        # The record must have 3 fields
        if len(field_list) > 3:
            field_list = field_list[0:3]
        field_list = field_list[1:]
        if len(field_list) != 2:
            return
        # control character are erased: end of line, tab, space
        # _____Fields_____
        # "control": "[\t \n\r]"
        _code = self.delete_control_space(field_list[0])
        _labels = self.delete_control_space(field_list[1])
        # _____Codes_____
        # "#" and "##" characters at the end of the code are erased
        # invalid characters are also erased
        _code = self.validateCode(_code)
        # _____Labels_____
        # last \ is erased
        # TODO: change the others parsers to this:
        while len(_labels) > 0 and _labels[-1] == u"\\":
            _labels = _labels[:-1]
        # replace "_" to " "
        _labels = _labels.replace(u"_",u" ")
        _label_list = _labels.split(u"\\")
        for _label in _label_list:
            self.__budget.addLabel(_code.encode("utf8"), _label.encode("utf8"))
        self.__statistics.valid = self.__statistics.valid + 1

    def _parseP(self, field_list):
        """_parseP(self, field_list)
        
        field_list: Parametric record
            A) Global paremetric record
                0- P: Parametric
                1- Empty
                2- [Parametric description]
                3- [library.DLL]
            B) Family Parametric record
                0- P: Parametric
                1- Family Code
                2- [Parametric description]
        """
        # TODO: Use global parametric record
        if len(field_list) > 2:
            # delete control caracters and spaces
            _family_code = self.delete_control_space(field_list[1])
            if _family_code == u"": # A)Global paremetric record
                # The record must have 3 or 4 fields
                if len(field_list) > 4:
                    field_list = field_list[0:4]
                field_list = field_list[1:]
                if len(field_list) == 2:
                    field_list.append(u"")
                if len(field_list) != 3:
                    return
            else: # B)Family Parametric record
                # The record must have 3 fields
                if len(field_list) > 3:
                    field_list = field_list[0:3]
                field_list = field_list[1:]
                if len(field_list) != 2:
                    print _("PyArq hates parametric DLLs")
                    return
        else:
            return
        # _____Description_____
        _description = field_list[1]
        if _description == u"":
            print _("PyArq hates parametric DLLs")
            return
        # Adding last end of line
        _description = _description + u"\r\n"
        # Delete comments
        # "comment" : "#.*\r\n"
        _description = self.__pattern["comment"].sub(u"\r\n",_description)
        # Tabs to spaces
        _description = _description.replace(u"\t",u" ")
        # Delete empty lines
        # "empty_line": r"(\r\n) *\r\n"
        while self.__pattern["empty_line"].search(_description):
            _description = self.__pattern["empty_line"].sub(
                            lambda x: x.groups()[0], _description)
        # Delete spaces before and after /
        # "space_before_backslash" : r"( )+\\"
        _description = self.__pattern["space_before_backslash"].sub(
                        ur"\\",_description)
        # "space_after_backslash" : r"\\( )+"
        _description = self.__pattern["space_after_backslash"].sub(
                        ur"\\",_description)
        # Join lines that start but not end with /
        _description = u"\r\n" + _description # add leading end of line
        # "start_noend_backslash": "(\r\n\\\.*[^\\\])\r\n"
        while self.__pattern["start_noend_backslash"].search(_description):
            _description = self.__pattern["start_noend_backslash"].sub(
                            lambda x: x.groups()[0], _description)
        # Join lines that end with a + - * / ^ and @ & < > <= >= = <> !
        # "end_oper" : "(\+|-|\*|/|/^|@|&|<|>|<=|>=|=|!) *\r\n"
        _description = self.__pattern["end_oper"].sub(
                        lambda x: x.groups()[0], _description)
        # Join lines for matricial vars
        # matricial_var : "(\r\n *[%|\$][A-ZÑ].*=.*,) *\r\n"
        while self.__pattern["matricial_var"].search(_description):
            _description = self.__pattern["matricial_var"].sub(
                            lambda x: x.groups()[0], _description)
        _description = _description[2:]  # remove leading end of line
        #_description = re.sub(r"\\( )+",r"\\",_description)
        _lines = _description.split(u"\r\n")
        _final_description = u""
        _pass_line = 0
        for index in range(len(_lines)):
            _line = _lines[index]
            # Parse lines
            if len(_line) != 0: # Delete empty lines
                if _pass_line > 0:
                    _pass_line = _pass_line -1
                    _line = u""
                elif _line.isspace():
                    _line = u""
                elif  _line[0] != u"\\":
                    # Delete spaces out "" delimiter
                    _list = _line.split(u'"')
                    _final_line = u""
                    for index1 in range(len(_list)):
                        if index1 % 2 != 0:
                            _parcial_line = u'"' + _list[index1]
                        else:
                            _parcial_line =  u'"' + _list[index1].replace(u" ",u"")
                        _final_line = _final_line + _parcial_line
                    _line = _final_line[1:]
                    _lines[index] = _line
                    # parse data
                    if len(_line) > 2 and _line[:2] == u"::":
                        # Delete spaces out " delimiter
                        #print "__PRECIO__" + _line[2:]
                        pass
                    elif len(_line) > 2 and _line[:2] == u"%:":
                        # Delete spaces out " delimiter
                        #print "__%AUX__" + _line[2:]
                        pass
                    elif len(_line) > 3 and _line[:2] == u"%%:":
                        # Delete spaces out " delimiter
                        #print "__%%AUX__" + _line[2:]
                        pass
                    elif self.__pattern["var"].search(_line):
                        # Delete spaces out " delimiter
                        #print "line =", _line
                        while _line.count(u'"') % 2 == 1 and \
                              index + _pass_line + 1 < len(_lines) -1:
                            _line = _line + _lines[index + _pass_line + 1]
                            _pass_line = _pass_line + 1
                        _search = self.__pattern["var"].search(_line)
                        if _search is not None:
                            _var = _search.groups()[0] + u" = " + _search.groups()[1]
                            #print "__VAR__" + str(_var)
                            pass
                        else:
                            #print "no __VAR__", _line
                            pass
                    elif self.__pattern["descomposition"].search(_line):
                        # Delete spaces out " delimiter
                        #_patern = "(^[^:]*):(.*)$"
                        _search = self.__pattern["descomposition"].search(_line)
                        if _search is not None:
                            _var = _search.groups()[0] + u":" + _search.groups()[1]
                            #print "__Descomposición__" + str(_var)
                            pass
                        else:
                            #print "no __Descomposición__", _line
                            pass
                    else:
                        print "Parametric: code: " + _family_code.encode("utf8")
                        print "******* Desconocido *** : " + _line
                        if index-10 > 0: print "-11 :", _lines[index-11].encode("utf8")
                        if index-10 > 0: print "-10 :", _lines[index-10].encode("utf8")
                        if index-9 > 0: print "-9 :", _lines[index-9].encode("utf8")
                        if index-8 > 0: print "-8 :", _lines[index-8].encode("utf8")
                        if index-7 > 0: print "-7 :", _lines[index-7].encode("utf8")
                        if index-6 > 0: print "-6 :", _lines[index-6].encode("utf8")
                        if index-5 > 0: print "-5 :", _lines[index-5].encode("utf8")
                        if index-4 > 0: print "-4 :", _lines[index-4].encode("utf8")
                        if index-3 > 0: print "-3 :", _lines[index-3].encode("utf8")
                        if index-2 > 0: print "-2 :", _lines[index-2].encode("utf8")
                        if index-1 > 0: print "-1 :", _lines[index-1].encode("utf8")
                        print "-0 :", _lines[index-0]
                        pass
                else:
                    _parameter_list = _line.split(u"\\")[1:-1]
                    if len(_parameter_list) >= 2:
                        if _parameter_list[0] == u"C" or \
                           _parameter_list[0] == u"COMENTARIO":
                            #print "__COMENTARIO__" + _parameter_list[1]
                            self.__budget.setParametricSelectComment(
                                _family_code.encode("utf8"), _parameter_list[1].encode("utf8"))
                        elif _parameter_list[0] == u"R" or \
                           _parameter_list[0] == u"RESUMEN":
                            #print "__RESUMEN__" + _parameter_list[1]
                            self.__budget.setParametricSummary(_family_code.encode("utf8"),
                                _parameter_list[1].encode("utf8"))
                        elif _parameter_list[0] == u"T" or \
                           _parameter_list[0] == u"TEXTO":
                            #print "__TEXTO__" + _parameter_list[1]
                            self.__budget.setParametricText(_family_code.encode("utf8"),
                                _parameter_list[1].encode("utf8"))
                        elif _parameter_list[0] == u"P" or \
                           _parameter_list[0] == u"PLIEGO":
                            #print "__PLIEGO__" + str(_parameter_list[1:])
                            pass
                        elif _parameter_list[0] == u"K" or \
                           _parameter_list[0] == u"CLAVES":
                            #print "__CLAVES__" + str(_parameter_list[1:])
                            pass
                        elif _parameter_list[0] == u"F" or \
                           _parameter_list[0] == u"COMERCIAL":
                            #print "__COMERCIAL__" + str(_parameter_list[1:])
                            pass
                        else:
                            #print "==PARAMETRO==" + str(_parameter_list[:])
                            pass
                _final_description = _final_description + _line + u"\r\n"
                
                #print _line
        # Delete last empty line
        _description = _final_description[:-2]
        _lines = _description.split(u"\r\n")
        for _line in _lines:
            pass
            #print _line
        self.__statistics.valid = self.__statistics.valid + 1

    def readFile(self, budget=None, filename=None, interface=None):
        """readFile(self, budget=None, filename=None)
        
        filename: the filename of the fiebdc file
        budget: base.obra object
        interface: a object to send messages
            must have readFile_send_message(message)
                      readFile_set_statistics(statistics)
                      readFile_progress(percent)
                      readFile_end()
                      readFile_cancel()
        Return the budget objetc or None if the file can be readed
        """
        if not filename is None and not budget is None:
            self.__filename = filename
            self.__budget = budget
            self.__budget.filename = self.__filename
        if self.__filename is None or self.__budget is None or self.__cancel:
            return None
        if not os.path.exists(self.__filename):
            return None
        if interface is None:
            interface = Interface()
        interface.readFile_set_statistics(self.__statistics)
        _time = time.time()
        try:
            _file =  open(self.__filename, 'r')
        except IOError:
            print utils.mapping("IOError: $1", (self.__filename,))
            return None
        self.__budget.filename = self.__filename
        interface.readFile_send_message(utils.mapping(_("Loading file $1"),
                         (self.__filename,)))
        _filesize = float(os.path.getsize(self.__filename))
        interface.readFile_progress(_file.tell() / _filesize)
        _buffer = _file.read(1000)
        # set codepage from V record
        _record_list = _buffer.split("~")
        registro_V = _record_list[1]
        # ~V|[PROPIEDAD_ARCHIVO]|VERSION_FORMATO[\DDMMAAAA]|[PROGRAMA_EMISION]|
        # [CABECERA]\{ ROTULO_IDENTIFICACION \}|[JUEGO_CARACTERES]|
        # [COMENTARIO]|[TIPO INFORMACIÓN]|[NÚMERO CERTIFICACIÓN]|
        # [FECHA CERTIFICACIÓN ] |
        registro_V = registro_V.split("|")
        if registro_V[0] == "V":
            #_codepage = registro_V[5]
            if len(registro_V) > 5:
                _version = registro_V[5].strip()
                # remove leading spaces
                if _version in self.__character_sets_dict:
                    self.__character_set = self.__character_sets_dict[_version]
                    interface.readFile_send_message(utils.mapping(
                        _("FIEBDC character encoding: $1"),
                          (self.__character_set,)))
                else:
                    interface.readFile_send_message(utils.mapping(
                        _("This Character encoding do not exist in "\
                          "FIEBDC3! Default Character encoding: $1"),
                          (self.__character_set,)))
            else:
                interface.readFile_send_message(utils.mapping(_(
                         "This V record dot have a character encoding! "\
                         "Default character encoding: $1"),
                         (self.__character_set,)))
        else:
            interface.readFile_send_message(utils.mapping(_(
                  "Not 'V' record in File! Default character encoding: "\
                  "$1"), (self.__character_set,)))
        _buffer = unicode(_buffer, self.__character_set)
        # Any INFORMATION between the beginning of the file and the
        # beginning of the first registry “~” is ignored
        #"after_first_tilde" : "^[^~]*~"
        _buffer = self.__pattern["after_first_tilde"].sub("",_buffer)
        while _buffer != u"" and not self.__cancel:
            #-# the blank characters (32), tabs (9) and end of line (13 and 10)
            # before the separators '~', '|' are erased.
            # Before separator \ not deleted because it affects the reading of
            # the record ~P
            _buffer = self.eraseControlCharacters(_buffer)
            _record_list = _buffer.split(u"~")
            # The last record can be incomplete unless it is the last one of
            # the file
            if len(_record_list) > 1:
                # not the end
                _last_record = _record_list.pop()
            else:
                # the end record
                # The blank characters (32), tabs (9) and end of line
                # (13 and 10) at the end of the file are ignored.
                #"end_control" : "((\r\n)| |\t)+$"
                _record_list[-1] = self.__pattern["end_control"].sub(u"",
                                           _record_list[-1])
                _last_record = u""
            for record in _record_list:
                if self.__cancel:
                    break
                self.parseRecord(record)
            interface.readFile_progress(_file.tell() / _filesize)
            _buffer2 = _file.read(100000)
            _buffer2 = unicode(_buffer2, self.__character_set)
            _buffer = _last_record + _buffer2
        _file.close()
        if self.__cancel:
            interface.readFile_cancel()
            return None
        else:
            self.__statistics.time = time.time()-_time
            if self.__statistics.O > 0:
                interface.readFile_send_message(
                    utils.mapping(_("$1 unsuported record type O: "\
                    "Comercial Relationship"), (self.__statistics.O,)))
            if self.__statistics.valid == 0:
                interface.readFile_send_message(_("This file is not a valid FIBDC3 file"))
                return None
            interface.readFile_end()
            self._testBudget(self.__budget)
            return self.__budget

    def _testBudget(self, budget):
        """testBudget(self,budget)
        
        budget: base.obra object
        Test and repair budget object after read it from bc3 file
        """
        # TODO: more to do here
        print _("Testing budget ...")
        # Add price to records without price
        _iter = budget.iter()
        _titlelist = budget.getTitleList()[1]
        if len(_titlelist) == 0:
            _titlenum = 1
        else:
            _titlenum = len(_titlelist)
        for _code in _iter:
            _record = budget.getRecord(_code)
            _prices = _record.getPrices()
            _len_prices = len(_prices)
            if _titlenum > _len_prices:
                _leftprices = _titlenum - _len_prices
                for _index in range(0,_leftprices):
                    _root = budget.getRecord(budget.getRoot())
                    _price = [0.0, _root.getDate(_len_prices + _index)]
                    budget.addPriceToRecord(_price,_record)
        print _("End Test")

    def delete_control_space(self, text):
        text = self.delete_control(text)
        text = text.replace(u" ", u"")
        return text

    def delete_control(self, text):
        text = text.replace(u"\t", u"")
        text = text.replace(u"\r", u"")
        text = text.replace(u"\n", u"")
        return text
    
class Interface(object):
    """fiebdc.Interface
    
    Description:
        An example interface
    Constructor:
        fiebdc.Interface()
    Ancestry:
    +-- object
      +-- Interface
    Atributes:
        "__progress": The progress percentage
        "__statistics": The record statistics 
    Methods:
        __init__(self)
        readFile_send_message(message)
        readFile_progress(percent)
        readFile_set_statistics(statistics)
        readFile_end()
        readFile_cancel()
        
    """
    def __init__(self):
        self.__progress = 0.0
        self.__statistics = Statistics()

    def readFile_set_statistics(self, statistics):
        """readFile_set_statistics(statistics)
        
        statistics: record statistics from readFile method
        
        sets record statistics
        """
        self.__statistics = statistics

    def readFile_send_message(self, message):
        """readFile_send_message(message)
        
        message: mesage from readFile method
        
        print message
        """
        print message

    def readFile_progress(self, percent):
        """progress(percent)
        
        percent: Percentage executed.
        
        Sets progress
        """
        self.__progress = percent

    def readFile_end(self):
        """readFile_end()
        
        The readFile method end successfully
        """
        print self.__statistics

    def readFile_cancel(self):
        """readFile_cancel()
        
        The readFile method is canceled
        """
        print _("Process terminated")

class Statistics(object):
    """fiebdc.Statistics
    
    Description:
        BC3 Statistics. Records types.
    Constructor:
        fiebdc.Statistics()
    Ancestry:
    +-- object
      +-- Statistics
    Atributes:
        "records": number of records
        "valid": number of valid records
        "V": number of  V records
        "C": number of C records
        "D":number of D records
        "Y":number of Y records
        "M":number of M records
        "N":number of N records
        "T":number of T records
        "K":number of K records
        "W":number of W records
        "L":number of L records
        "Q":number of Q records
        "J": number of J records
        "G":number of G records
        "E":number of E records
        "O":number of O records
        "P":number of P records
        "X":number of X records
        "B":number of B records
        "F":number of F records
        "A":number of A records
        "unknow": number of Unknow records
        "time": Time to load

    Methods:
        __init__(self)

    """
    def __init__(self):
            self.records = 0
            self.valid = 0
            self.V = 0
            self.C = 0
            self.D = 0
            self.Y = 0
            self.M = 0
            self.N = 0
            self.T = 0
            self.K = 0
            self.W = 0
            self.L = 0
            self.Q = 0
            self.J = 0
            self.G = 0
            self.E = 0
            self.O = 0
            self.P = 0
            self.X = 0
            self.B = 0
            self.F = 0
            self.A = 0
            self.unknow = 0
            self.time = 0.0

    def __str__(self):
        return utils.mapping(_("Time to load: $1 seconds"),
                (("%.2f" %(self.time)),)) + "\n" + \
               utils.mapping(_("Records/Valid Records: $1/$2"), 
               (self.records, self.valid)) + "\n" +\
               "V: %s\n" %(self.V,) + \
               "C: %s\n" %(self.C,) + \
               "D: %s\n" %(self.D,) + \
               "Y: %s\n" %(self.Y,) + \
               "M: %s\n" %(self.M,) + \
               "N: %s\n" %(self.N,) + \
               "T: %s\n" %(self.T,) + \
               "K: %s\n" %(self.K,) + \
               "W: %s\n" %(self.W,) + \
               "L: %s\n" %(self.L,) + \
               "Q: %s\n" %(self.Q,) + \
               "J: %s\n" %(self.J,) + \
               "G: %s\n" %(self.G,) + \
               "E: %s\n" %(self.E,) + \
               "O: %s\n" %(self.O,) + \
               "P: %s\n" %(self.P,) + \
               "X: %s\n" %(self.X,) + \
               "B: %s\n" %(self.B,) + \
               "F: %s\n" %(self.F,) + \
               "A: %s\n" %(self.A,) + \
               "?: %s\n" %(self.unknow,)

