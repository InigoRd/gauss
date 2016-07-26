#!/usr/bin/python
# -*- coding: utf-8 -*-
## File base.py
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

"""base module

In this module are defined the data structures in the
classes:
 * Record: data of each record
 * ParamentricRecord: data of each parametric record
 * Decomposition: data of the decomposition of each record
 * Measure: data of the measure of each record
 * MeasureLine: each measure line data
 * Decimals: data of the decimal places of all the numbers in a budget
 * Sheet: data of the sheet of conditions of a budget
 * Budget: all data of a budget
 * Company: company data
 * Office: company office data
 * File: file data
 * RecordType: Record type data

schema:
 * Budget:
   +-- __records: dictionary records { code : Record }
      * Record:
        +-- code: record code
        +-- synonyms: list of synonym codes 
        +-- hierarchy: A integer number:
            0 -> root
            1 -> Chapter/Subchapter
            2 -> Other
        +-- unit:  unit of measure of the record
        +-- summary: Short description of the record
        +-- prices: List of Prices/Dates
        +-- type
        +-- subtype
            "type" and "subtype":
                0 Without classifying
                   EA  Auxiliary element
                   EU  Unitary element
                   EC  Complex element
                   EF  Functional element
                   OB  Construction site
                   PA  Cost overrun
                   PU  Unitary budget
                1 Labourforce 
                   H   Labourforce
                2 Machinery and auxiliary equipment
                   Q   Machinery
                   %   Auxiliary equipment
                3 Building materials
                   MC  Cement
                   MCr Ceramic
                   MM  Wood
                   MS  Iron and steel
                   ME  Energy
                   MCu Copper
                   MAl Aluminium
                   ML  Bonding agents
                   M   Others materials
                Hierarchy         type  subtype
                0->root         -> 0 -> None,OB
                1->[sub]chapter -> 0 -> None,PU
                2->Other        -> 0 -> None,EA,EU,EC,EF,PA
                                   1 -> None,H
                                   2 -> None,Q,%
                                   3 -> None,MC,MCr,MM,MS,ME,MCu,Mal,ML,M
        +-- parents: List of parent codes
        +-- children: list of Decomposition
           * Decomposition:
             +-- position: Position of the child in the parent descomposition
                 TODO: change this: the position of the record in the budget
             +-- code: child record code
             +-- budget: list of budget and amended budget measures
                * Measure:
                  +-- measure: Total result of measure
                  +-- lines: List of measure lines
                     * MeasureLine:
                       +-- type: Line type:
                            empty string -> Normal
                            1 -> Parcial Subtotal
                            2 -> Accumulated Subtotal
                            3 -> Formula, the comment is a formula.
                       +-- comment: Can be a descriptive text or a formula
                            Valid Operator: '(', ')', '+', '-', '*', '/' and 
                                            '^'
                            Valid variable: 'a', 'b', 'c','d' y 'p'
                                            (Pi=3.1415926)
                       +-- units: Number of Units (a)
                       +-- length: length (b)
                       +-- width: width (c)
                       +-- height: height (d)
                  +-- label: Record Identifiers that are used by some measure
                      programs
                  +-- factor: Factor
                  +-- yield_: Yield
             +-- certification: list of certifications for months measures
                * Measure
             +-- real_cost: list of real cost of construction for months
                 measures
                * Measure
             +-- cost_goals: list of cost goals of construction for months
                 measures
                * Measure
             +-- cost_planned: list of costs planned and amended cost planned
                 measures
                * Measure
        +-- text: Long Description of the record
        +-- sheet: Sheet of conditions object
           * Sheet:
             +-- sheet_dict:
                 { <Field key> : { <Section key> : <Paragraph key>}}
        +-- files:  List of file object
             +-- file
                * Name
                * Type
                * Description
   +-- __synonyms: synonyms dictionary. TODO
   +-- __root: root record code
   +-- __decimals: decimals dictionay = { int : Decimals }
      * Decimals:
        +-- DN: Number of decimal places of the field "equal-size parts" in the
            measure lines.
            Default: 2 decimal places.
        +-- DD: Number of decimal places of the three dimensions in the 
            measure lines.
            Default: 2 decimal places.
        +-- DS: Number of decimal places of the total sum of a measure.
            Default: 2 decimal places.
        +-- DFP: Number of decimal places of the yield factor in a 
            decomposition of a budget record.
            Default: 3 decimal places.
        +-- DFC: Number of decimal places of the yield factor in a 
            decomposition of a chapter or subchapter, and in its measure lines.
            Dafault: 3 decimal places.
        +-- DFUO: Number of decimal places of the yield factor in a 
            decomposition of a unit of work.
            Default: 3 decimal places.
        +-- DFA: Number of decimal places of the yield factor in a 
            decomposition of a Auxiliary element.
            Default: 3 decimal places.
        +-- DRP: Number of decimal places of the yield in a decomposition
            of a budget record.
            Number of decumal places of the result of the multiplication of 
            the factor and the yield in a decompositon of a budget.
            Default: 3 decimal places.
        +-- DRC: Number of decimal places of the yield (or measure) in a 
            decomposition of a chapter or subchapter.
            Number of decimal places of the result of the multiplictaion of
            the yield (or measure) and the factor in a decomposition of a 
            chapter or subcharter.
            Default: 3 decimal places.
        +-- DRUO: Number of decimal places of the yield in a decomposition of a
            unit of work.
            Decimal places of the result of the multiplication of the yield
            and the factor in a descomposition of a unit of work.
            Default: 3 decimal places.
        +-- DRA: Number of decimal places of the yield in a decompositon of a
            auxiliar element.
            Number of decimal places of the result of the multiplication of 
            the yield and the factor in a descomposition of a auxilar element.
            Default: 3 decimal places.
        +-- DP: Number of decimal places of the price of a budget.
            Default: 2 decimal places.
        +-- DC: Number of decimal places of the price of a chapter or 
            subchapter.
            Default: 2 decimal places.
        +-- DUO: Number of decimal places of the price of a unit of work.
            Default: 2 decimal places.
        +-- DEA: Number of decimal places of the price of a auxiliar element.
            Default: 2 decimal places.
        +-- DES: Number of decimal places of the price of the simple elements.
            Default: 2 decimal places.
        +-- DIR: Number of decimal places of the resulting amount to multiply 
            the total yield and the price of the elements of a unit of work.
            (When there are not measures)
        +-- DIM: Number of decimal places of the resulting amount to multiply 
            the total yield and the price of the elements of a unit of work.
            (When there are measures)
        +-- DIRC: Number of decimal places of the resulting amount to multiply 
            the total yield and the price of the elements of a budget, chapter
            or a subchapter.(When there are not measures)
        +-- DIMC: Number of decimal places of the resulting amount to multiply 
            the total yield and the price of the elements of a budget, chapter
            or a subchapter. (When there are measures)
        +-- DCD: Number of decimal places ot the resulting amount to sum the
            direct costs of a unit of work (and auxiliar element).
            Number of decimal places of the indirect costs.
            Default: 2 decimal places.
        +-- DIVISA: monetary unit.
   +-- __percentages: percentages dictionary:
                      { "CI"  : "",
                        "GG"  : "",
                        "BI"  : "",
                        "BAJA": "",
                        "IVA" : ""}
   +-- __file_owner
   +-- __title_list: titles list: [ "Header", ["Title1", "Title2", ... ] ]
   +-- __title_index: A integer. The active group of Prices and Decimals.
   +-- __sheet_sections: sheet sections dictionary { sheet_code : sheet_title }
   +-- __sheet_fields: sheet fields dictionary { field_code : field_title }
   +-- __sheet_paragraphs: sheet paragraphs dictionary 
                           { paragraph_code : paragraph_text}
   +-- __companys: Dictionary whith companys object
                   { company_code: company_object }
      * Comapany:
        +-- code: company code
        +-- summary: short name
        +-- name: long name
        +-- offices: List of offices:
           * Office:
             +-- type: office type
                    "C"  Central office.
                    "D"  Local Office.
                    "R"  Performer.
             +-- subname: Office name
             +-- address: Ofiice address
             +-- postal_code: postal code
             +-- town: town
             +-- province: province/state
             +-- country: country
             +-- phone: list of phone numbers
             +-- fax: list of fax numbers
             +-- contact_person: Contact person in the office
        +-- cif: CIF
        +-- web: web page
        +-- email: email
"""

# Modules
import re
import datetime
import os

# pyArq-Presupuestos modules
from Generic import fiebdc
from Generic import utils

class Record(object):
    """base.Record:
    
    Description:
        Record object
    Constructor:
        base.Record(decimals, code, synonyms, hierarchy, unit, summary,
                 prices, type_, subtype, parents=None, text=None)
    Ancestry:
    +-- object
      +-- Record
    Atributes:
        "code": Code string
        "recordType": RecordType object
        "synonyms": List of synonym codes.
        "parents":List of parent codes
        "children": Decomposition list,
                  list of "Decomposition" instances
        "unit": measure unit of the record
        "summary": Short description of the record
        "prices": List of prices/dates
        "text": Long Description of the record
        "sheet": Sheet of conditions object
        "files": List of file object
        "labels": List of record labels
    Methods:
        __getstate__(self)
        __setstate__(self, tuple)
        __init__(self, filename=None, budget=None)
        {get/set}Code
        {get/set}Synonyms
        {get/set}RecordType
        {get/set}Unit
        {get/set}Summary
        {get/set}Prices
        addPrice
        _validate_price_date
        getPrice
        getAmount
        getDate
        {get/set}Parents
        appendParent
        {get/set}children
        appendChild
        {get/set}Text
        {get/set}Sheet
        {get/set}Files
        addFile
        {get/set}Labels
        addLabel
        getChildPositions:
    """
    __slots__ = ["_Record__code", "_Record__synonyms",
                 "_Record__recordType", "_Record__unit",
                 "_Record__summary", "_Record__prices",
                 "_Record__parents", "_Record__children",
                 "_Record__text", "_Record__sheet",
                 "_Record__files", "_Record__labels"]

    def __getstate__(self):
        return (self.__code, self.__synonyms, self.__recordType,
                self.__unit, self.__summary, self.__prices,
                self.__parents, self.__children, self.__text,
                self.__sheet, self.__files, self.__labels)

    def __setstate__(self, tuple):
        self.__code = tuple[0]
        self.__synonyms = tuple[1]
        self.__recordType = tuple[2]
        self.__unit = tuple[3]
        self.__summary = tuple[4]
        self.__prices = tuple[5]
        self.__parents = tuple[6]
        self.__children = tuple[7]
        self.__text = tuple[8]
        self.__sheet = tuple[9]
        self.__files = tuple[10]
        self.__labels = tuple[11]

    def __init__(self, decimals, code, synonyms, hierarchy, unit, summary,
                 prices, type_, subtype, parents=None, text=None):
        self.code = code
        self.synonyms = synonyms
        self.recordType = (hierarchy, type_, subtype)
        self.unit = unit
        self.summary = summary
        self.setPrices(prices, decimals)
        if parents is None:
            parents = []
        self.parents = parents
        self.children = []
        if text is None:
            text = ""
        self.text = text
        self.sheet = Sheet()
        self.files = []
        self.labels = []

    def getCode(self):
        return self.__code

    def setCode(self, code):
        """setCode(self,code)
        
        Sets the code, must be a valid code
        """
        if not utils.is_valid_code(code)[0]:
            raise ValueError, utils.mapping(_("Invalid code: $1"),(str(code),))
        self.__code = code

    def getSynonyms(self):
        return self.__synonyms

    def setSynonyms(self,synonyms):
        """setSynonyms(self,synonyms)
        
        Sets the synonyms codes of the record.
        synonyms must fulfill:
            - must be a list
            - the items must be valid codes
        """
        if not isinstance(synonyms, list):
            raise TypeError, utils.mapping(_("Synonyms ($1) must be a list, " \
                  "code: $2"), (str(synonyms), self.__code))
        for code in synonyms:
            if not utils.is_valid_code(code)[0]:
                raise ValueError, utils.mapping(_("Invalid Code in synomyms "\
                      "list ($1) code: $2"), (str(code), self.__code))
        self.__synonyms = synonyms

    def getRecordType(self):
        return self.__recordType

    def setRecordType(self, recordType):
        """setRecordType(self, recordType)
        
        Set the record type.
        recordType (hierarchy, type,subtype)
        
        hierarchy must be -1, 0, 1 or 2
        type must be 0, 1, 2, 3 or a empty string
        subtype must be EA, EU, EC, EF, OB, PA, PU, H, Q, %, MC, MCr, 
                MM, MS, ME, MCu, MAl, ML, M, or a empty string
        """
        _recordType = RecordType(recordType[0],recordType[1],recordType[2])
        self.__recordType = _recordType

    def getUnit(self):
        return self.__unit

    def setUnit(self,unit):
        """setUnit(self,unit)
        
        Set the unit of measure
        The unit must be a string.
        """
        if not isinstance(unit, str):
            raise TypeError, utils.mapping(_("Unit ($1) must be a string: $2"),
                  (str(unit), self.__code))
        self.__unit = unit

    def getSummary(self):
        return self.__summary

    def setSummary(self,summary):
        """setSummary(self,summary)
        
        Set the summary of a record
        The summary must be a string.
        """
        if not isinstance(summary, str):
            raise TypeError, utils.mapping(_("Summary ($1) must be a string: "\
                  "$1"), (str(summary), self.__code))
        self.__summary = summary

    def getPrices(self):
        return self.__prices

    def setPrices(self, prices, decimals):
        """setPrice(self, prices, decimals)
        
        Set the price list of the record.
        prices must fulfill:
            - it must be a list
            - the items must be a list with two items
            - the first item: price must be a float
        """
        if not isinstance(prices, list):
            raise TypeError, utils.mapping(_("Prices ($1) must be a list: $2"),
                  (str(prices), self.__code))
        for index in range(len(prices)):
            _price_date = prices[index]
            _price_date = self._validate_price_date(_price_date, decimals)
            prices[index] = _price_date
        self.__prices = prices

    def addPrice(self, price_date, decimals):
        """addPrice(self, price_date, decimals)
        
        Add a price to the price list of the record.
        price must fulfill:
            - must be a list with two items
            - the first item: price must be a float
        """
        price_date = self._validate_price_date(price_date, decimals)
        self.__prices.append(price_date)

    def _validate_price_date(self, price_date, decimals):
        if not isinstance(price_date, list) and len(price_date) == 2:
            raise ValueError, utils.mapping(_("Price ($1) must be a list"\
                  " with two items: $2"), (str(price_date), self.__code))
        _price = price_date[0]
        _date = price_date[1]
        if not isinstance(_price, float):
            raise TypeError, utils.mapping(_("Price must be a float "\
                      "number: $1"), (str(_price),))
        _D = decimals.getD(self.recordType)
        _price = round(_price, _D)
        price_date[0] = _price
        # TODO: validate date
        return price_date

    def getPrice(self, index_price):
        if len(self.__prices) <= index_price:
            raise IndexError, _("The record do not have this Price. Code: %s"
                                % self.__code)
        return self.__prices[index_price][0]

    def getDate(self, index_price):
        if len(self.__prices) <= index_price:
            raise IndexError, _("The record do not have this Price")
        return self.__prices[index_price][1]

    def getParents(self):
        return self.__parents

    def setParents(self,parents):
        """setParents(self,parents)
        
        Sets the list of parents codes of the record.
        parents must fulfill
            - it must be a list
            - the items must be valid codes
        """
        if not isinstance(parents, list):
            raise TypeError, utils.mapping(_("Parents ($1) must be a list: $2"),
                  (str(parents), self.__code))
        for parent in parents:
            if not utils.is_valid_code(parent)[0]:
                raise ValueError, utils.mapping(_("Invalid parent code ($1) " \
                      "in the record: $2"), (str(padre), self.__code))
        self.__parents = parents

    def appendParent(self, parent):
        """appendParent(self, parent)
        
        parent must be a valid code
        Append a parent to the list of parents codes of the record.

        """
        if not utils.is_valid_code(parent)[0]:
            raise ValueError, utils.mapping(_("Invalid parent code ($1) " \
                  "in the record: $2"), (str(parent), self.__code))
        self.__parents.append(parent)

    def getchildren(self):
        return self.__children

    def setchildren(self,children):
        """setchildren(self,children)
        
        Sets the list of children of a record
        children must fulfill
            - it must be a list
            - the items must be instances of Decomposition class
        """
        if not isinstance(children, list):
            raise TypeError, utils.mapping(_("children ($1) must be a list, "\
                  "record: $2"), (str(children), self.__code))
        for _child in children:
            if not isinstance(_child, Decomposition):
                raise ValueError, utils.mapping(_("child ($1) must be a "\
                      "Decomposition object, record: $2"),
                      (str(_child), self.__code))
            _record_code = self.code
            for _measure_list in [_child.budgetMeasures, _child.certification,
                                  _child.real_cost, _child.cost_goals,
                                  _child.cost_planned]:
                if isinstance(_measure_list, list):
                    for _measure in _measure_list:
                        _measurerecordCode = _record_code
        self.__children = children

    def appendChild(self, child_code, decimals, factor=0.0, yield_=0.0,
                    measure=0.0, measure_list=None, type_=None, label=None):
        """appendChildren(self, child_code, factor=0.0, yield_=0.0,
                    measure=0.0, measure_list=None, type_=None, label=None))
        
        position:
        child_code:
        factor:
        yield_:
        measure:
        measure_list:
        type_:
        label:
        
        Append a child to the list of children
        """
        if measure_list is None:
            measure_list = []
        if type_ is None:
            type_ = ""
        if label is None:
            label = ""
        _measure = Measure(decimals, self.recordType,
                           measure, [], label, factor, yield_)
        if len(measure_list) > 0:
            _measure.buildMeasure( measure_list, type_, decimals,
                                 self.recordType)
        _position = len(self.__children)
        _child = Decomposition(_position, child_code, [_measure])
        self.__children.append(_child)
        return _child

    def getText(self):
        return self.__text

    def setText(self,text):
        """setText(self,text)
        
        Sets the text of the record
        It must be a string
        """
        if not isinstance(text, str):
            raise TypeError, utils.mapping(_("Text ($1) must be a string, "\
                  "record: $2"), (str(text), self.__code))
        self.__text = text

    def getSheet(self):
        return self.__sheet

    def setSheet(self, sheet):
        """setSheet(self, sheet)
        
        Sets the sheet of condition object
        """
        if not isinstance(sheet, Sheet):
            raise ValueError, _("sheet must be a Sheet instance")
        self.__sheet = sheet

    def getFiles(self):
        return self.__files

    def setFiles(self, files):
        """setFiles(self, files)
        
        Sets the files list
        """
        # TODO: only sets files and File object format (durusdatabase)
        if not isinstance(files, list):
            raise ValueError, utils.mapping(_("files must be a list: $1"),
                                              str(files))
        _files = []
        for file in files:
            if isinstance(file, File):
                _files.append(file)
            elif isinstance(file, list):
                _file_path = file[0]
                _type = file[1]
                _description = file[2]
                if not os.path.exists(file[0]):
                    raise ValueError, _("Incorrect path")
                _file = File(file_path, type_, description)
                _files.append(_file)
            else:
                raise ValueError, utils.mapping(_(
                      "file must be a list or a File object: $1"),str(file))
        self.__files = _files
        

    def addFile(self, file_path, type_, description):
        """addFile(self, file_path, type_, description)
        
        Add a file to a record instance
        """
        if not os.path.exists(file_path):
            raise ValueError, _("Incorrect path")
        _name = os.path.basename(file_path)
        _isin = False
        for _ofile in self.__files:
            if _ofile.name == _name:
                _isin = True
        if not _isin:
            _file = File(_name, type_, description)
            self.__files.append(_file)

    def getLabels(self):
        return self.__labels

    def setLabels(self, labels):
        """setLabels(self, labels)
        
        Sets the labels list of a record
        """
        if not isinstance(labels, list):
            raise ValueError, _("labels must be a list")
        _labels = []
        for _label in labels:
            if isinstance(_label, str):
                _labels.append(_label)
            else:
                raise ValueError, _("label must be a string")
        self.__labels = _labels

    def addLabel(self, label):
        """addLabel(self, label)
        
        Add a label to a record instance
        """
        if not isinstance(label, str):
            raise ValueError, _("Label must be a string")
        if not label in self.__labels:
            self.__labels.append(label)

    def getChildPositions(self, child_code):
        """getChildPath(self, child_code):
        
        Try to return positions of a childcode
        """
        children = self.children
        positions = []
        for child in children:
            if child.code == child_code:
                positions.append(child.position)
        return positions

    recordType = property(getRecordType, setRecordType, None,
        """Record Type object
        """)
    code = property(getCode, setCode, None,
        """Record code
        """)
    synonyms = property(getSynonyms, setSynonyms, None,
        """List of codes synonyms of the code
        """)
    unit = property(getUnit,setUnit, None,
        """Measure Unit of the record
        """)
    summary = property(getSummary, setSummary, None, 
        """Short description of the record
        """)
    prices = property(getPrices, None, None, 
        """List of Price/Date
        """)
    parents = property(getParents, setParents, None,
        """List of codes of the records which the record is in 
        its decomposition
        """)
    children = property(getchildren, setchildren, None,
        """List of Decompositon intances""")
    text = property(getText, setText, None,
        """Long description of the record""")
    sheet = property(getSheet, setSheet, None,
        """Sheet of conditions object""")
    files = property(getFiles, setFiles, None,
        """File list""")
    labels = property(getLabels, setLabels, None,
        """Label list""")

class ParametricRecord(Record):
    """base.ParametricRecord:
    
    Description:
        Parametric Record object
    Constructor:
        base.ParametricRecord(budget, code, synonyms, hierarchy, unit, summary,
                 prices, type_, subtype, parents=None, text=None)
    Ancestry:
    +-- object
      +-- Record
        +-- ParametricRecord
    Atributes:

    Methods:

    """

    __slots__ = ["_ParametricRecord__budget",
                 "_ParametricRecord__code", "_ParametricRecord__synonyms",
                 "_ParametricRecord__hierarchy", "_ParametricRecord__unit",
                 "_ParametricRecord__summary", "_ParametricRecord__prices",
                 "_ParametricRecord__type", "_ParametricRecord__subtype",
                 "_ParametricRecord__parents", "_ParametricRecord__children",
                 "_ParametricRecord__text", "_ParametricRecord__sheet",
                 "_ParametricRecord__files", "_ParametricRecord__labels",
                 "_ParametricRecord__parameters",
                 "_ParametricRecord__select_comment", 
                 "_ParametricRecord__vars",
                 "_ParametricRecord__parametric_summary",
                 "_ParametricRecord__parametric_text",]

    def __getstate__(self):
        return (self.__budget, self.__code, self.__synonyms, self.__hierarchy,
                self.__unit, self.__summary, self.__prices, self.__type,
                self.__subtype, self.__parents, self.__children, self.__text,
                self.__sheet, self.__files, self.__labels, self.__parameters,
                self.__select_comment, self.__vars,
                self.__parametric_summary, self.__parametric_text)

    def __setstate__(self, tuple):
        self.__budget = tuple[0]
        self.__code = tuple[1]
        self.__synonyms = tuple[2]
        self.__hierarchy = tuple[3]
        self.__unit = tuple[4]
        self.__summary = tuple[5]
        self.__prices = tuple[6]
        self.__type = tuple[7]
        self.__subtype = tuple[8]
        self.__parents = tuple[9]
        self.__children = tuple[10]
        self.__text = tuple[11]
        self.__sheet = tuple[12]
        self.__files = tuple[13]
        self.__labels = tuple[14]
        self.__parameters = tuple[15]
        self.__select_comment = tuple[16]
        self.__vars = tuple[17]
        self.__parametric_summary = tuple[18]
        self.__parametric_text = tuple[19]
    
    def __init__(self, budget, code, synonyms, hierarchy, unit, summary,
                 prices, type_, subtype, parents=None, text=None):
        if parents is None:
            parents = []
        if text is None:
            text = ""
        Record.__init__(self, budget, code, synonyms, hierarchy, unit, summary,
                 prices, type_, subtype, parents, text)
        self.__parameters = {}
        self.__select_comment = ""
        self.__vars = {}
        self.parametric_summary = ""
        self.parametric_text = ""

    def getParameter(self, parameter):
        if parameter in self.__parameters:
            return self.__parameters[parameter]
        else:
            return None

    def setParameter(self, parameter, parameter_list):
        self.__parameters[parameter] = parameter_list

    def getSelectComment(self):
        return self.__select_comment

    def setSelectComment(self, select_comment):
        self.__select_comment = select_comment
    def getVar(self, var):
        if var in self.__vars:
            return self.__vars[var]
        else:
            return None

    def setVar(self, var, var_list):
        self.__vars[var] = var_list

    def getParametricSummary(self):
        return self.__parametric_summary

    def setParametricSummary(self, parametric_summary):
        self.__parametric_summary = parametric_summary

    def getParametricText(self):
        return self.__parametric_text

    def setParametricText(self, parametric_text):
        self.__parametric_text = parametric_text

    parameter = property(getParameter, setParameter, None,
        """Record parameter
        """)
    select_comment = property(getSelectComment, setSelectComment, None,
        """Seclect comment
        """)
    var = property(getVar, setVar, None,
        """Record var
        """)
    parametric_summary = property(getParametricSummary, setParametricSummary,
        None,
        """Parametric summary
        """)
    parametric_text = property(getParametricText, setParametricText, None,
        """Seclect comment
        """)

class Decomposition(object):
    """base.Decomposition:
    
    Description:
        Decomposition object
    Constructor:
        base.Decomposition(position, code, budgetMeasures, certification=None,
                 real_cost=None, cost_goals=None, cost_planned=None)
    Ancestry:
    +-- object
      +-- Decomposition
    Atributes:
        "position": the position of the child record in the parent record
        "code": Record code.
        Measures:
        "budgetMeasures": list of budget and Amended budget measures
        "certification": list of certifications for months measures
        "real_cost": list of real cost of construction for months measures
        "cost_goals": list of cost goals of construction for months measures
        "cost_planned": list of costs planned and amended cost planned measures
    Methods:
        __getstate__(self)
        __setstate__(self, tuple)
        __init__( position, code, budgetMeasures, certification=None,
                 real_cost=None, cost_goals=None, cost_planned=None)
        {get/set}position
        {get/set}Code
        {get/set}BudgetMeasures
        {get/set}Certification
        {get/set}RealCost
        {get/set}CostGoals
        {get/set}CostPlanned
    """
    __slots__ = ["_Decomposition__position",
                 "_Decomposition__code",
                 "_Decomposition__budgetMeasures",
                 "_Decomposition__certification",
                 "_Decomposition__real_cost",
                 "_Decomposition__cost_goals",
                 "_Decomposition__cost_planned",
                ]
    def __getstate__ (self):
        return (self.__position, self.__code, self.__budgetMeasures,
                self.__certification, self.__real_cost, self.__cost_goals,
                self.__cost_planned)
    def __setstate__(self,tuple):
        self.__position = tuple[0]
        self.__code = tuple[1]
        self.__budgetMeasures = tuple[2]
        self.__certification = tuple[3]
        self.__real_cost = tuple[4]
        self.__cost_goals = tuple[5]
        self.__cost_planned = tuple[6]

    def __init__(self, position, code, budgetMeasures, certification=None,
                 real_cost=None, cost_goals=None, cost_planned=None):
        self.position = position
        self.code = code
        self.budgetMeasures = budgetMeasures
        self.certification = certification
        self.real_cost = real_cost
        self.cost_goals = cost_goals
        self.cost_planned = cost_planned
    def getPosition(self):
        return self.__position
    def setPosition(self, position):
        if not isinstance(position, int):
            raise ValueError, _("Position must be a integer")
        self.__position = position
    def getCode(self):
        return self.__code
    def setCode(self, code):
        self.__code = code
    def getBudgetMeasures(self):
        return self.__budgetMeasures
    def setBudgetMeasures(self, budgetMeasures):
        if not isinstance(budgetMeasures, list):
            raise ValueError, _("BudgetMeasures atribute must be a list")
        for _measure in budgetMeasures:
            if not isinstance(_measure, Measure):
                raise ValueError, _("BudgetMeasures item must be a Measure "/
                                    "object")
        self.__budgetMeasures = budgetMeasures
    def getCertification(self):
        return self.__certification
    def setCertification(self, certification):
        if not (certification is None or isinstance(certification, list)):
            raise ValueError, _("Certification atribute must be a list or None")
        self.__certification = certification
    def getRealCost(self):
        return self.__real_cost
    def setRealCost(self, real_cost):
        if not (real_cost is None or  isinstance(real_cost, list)):
            raise ValueError, _("Real cost atribute must be a list or None")
        self.__real_cost = real_cost
    def getCostGoals(self):
        return self.__cost_goals
    def setCostGoals(self, cost_goals):
        if not (cost_goals is None or  isinstance(cost_goals, list)):
            raise ValueError, _("Cost goals atribute must be a list or None")
        self.__cost_goals = cost_goals
    def getCostPlanned(self):
        return self.__cost_planned
    def setCostPlanned(self, cost_planned):
        if not (cost_planned is None or  isinstance(cost_planned, list)):
            raise ValueError, _("Cost Planned atribute must be a list or None")
        self.__cost_planned = cost_planned
    position = property(getPosition, setPosition, None,
        """Postion of the record in the budget
        """)
    code = property(getCode, setCode, None,
        """Record code
        """)
    budgetMeasures = property(getBudgetMeasures, setBudgetMeasures, None, 
        """list of budget and Amended budget measures
        """)
    certification = property(getCertification, setCertification,None, 
        """ list of certifications by months measures
        """)
    real_cost = property(getRealCost, setRealCost, None,
        """ list of real cost of construction for months measures
        """)
    cost_goals = property(getCostGoals, setCostGoals, None,
        """ list of cost goals of construction for months measures
        """)
    cost_planned = property(getCostPlanned, setCostPlanned, None,
        """ list of costs planned and amended cost planned measures
        """)


class Measure(object):
    """base.Measure:
    
    Description:
        Measure object
    Constructor:
        base.Measure(decimals, recordType, measure, lines,
                     label, factor, yield_)
    Ancestry:
    +-- object
      +-- Measure
    Atributes:
        "measure": Total result of measure.
        "lines": List of measure lines, List of LineM instances.
        "label": Record Identifiers that are used by some measure programs.
        "factor":
        "yield":
        "fixed": If fixed is True the yield is not calculated from measure
    Methods:
        __getstate__()
        __setstate__(tuple)
        __init__(decimals, recordType, measure, lines,
                 label, factor, yield_)
        getMeasure()
        setMeasure(measure, decimals)
        {get/set}Lines
        {get/set}Label
        getFactor()
        setFactor(factor, decimals, recordType)
        getYield()
        setYield(yield_, decimals, recordType)
        getFixed()
        setFixed(decimals)
        buildMeasure(list_lines, type, decimals)
        calculateMeasure(decimals)
        updateYield(decimals)
    """
    __slots__ = ["_Measure__measure",
                 "_Measure__lines",
                 "_Measure__label",
                 "_Measure__factor",
                 "_Measure__yield_",
                 "_Measure__fixed"]
    def __getstate__ (self):
        return (self.__measure, self.__lines, self.__label,
                self.__factor, self.__yield_, self.__fixed)
    def __setstate__(self,tuple):
        self.__measure = tuple[0]
        self.__lines = tuple[1]
        self.__label = tuple[2]
        self.__factor = tuple[3]
        self.__yield_ = tuple[4]
        self.__fixed = tuple[5]
    def __init__(self, decimals, recordType, measure, lines,
                 label, factor, yield_):
        self.setMeasure(measure, decimals)
        self.lines = lines
        self.label = label
        self.setFactor(factor, decimals, recordType)
        self.setYield(yield_, decimals, recordType)
        self.__fixed = False

    def getMeasure(self):
        return self.__measure
    def setMeasure(self, measure, decimals):
        if not isinstance(measure, float):
            raise ValueError, utils.mapping(_("Measure must be a float "\
                  "number. Type: $1"), (type(measure),))
        # TODO: test after
        _DS = decimals.DS
        measure = round(measure, _DS)
        self.__measure = measure

    def getLines(self):
        return self.__lines
    def setLines(self, lines):
        if not isinstance(lines, list):
            raise ValueError, _("Lines must be a list")
        for _line in lines:
            if not isinstance(_line, MeasureLine):
                raise ValueError, _("Line must be a MeasureLine objetc")
        self.__lines = lines
    def getLabel(self):
        return self.__label
    def setLabel(self, label):
        self.__label = label
    def setFactor(self, factor, decimals, recordType):
        if not isinstance(factor, float):
            raise ValueError, utils.mapping(_("Factor must be a float number "\
                  "|$1|"), (factor,))
        # TODO: test after
        _DF = decimals.getDF(recordType)
        factor = round(factor, _DF)
        self.__factor = factor

    def getFactor(self):
        return self.__factor
    
    def setYield(self, yield_, decimals, recordType):
        if not isinstance(yield_, float):
            raise ValueError, _("Yield must be a float number")
        # TODO: test after
        _DR = decimals.getDR(recordType)
        yield_ = round(yield_, _DR)
        self.__yield_ = yield_

    def getYield(self):
        return self.__yield_

    def setFixed(self, fixed, decimals):
        if not isinstance(fixed, bool):
            raise ValueError, _("Fixed must be boolean object")
        self.__fixed = fixed
        self.updateYield(decimals)

    def getFixed(self):
        return self.__fixed

    measure = property(getMeasure, None, None,
    """Total result of the measure
    """)
    lines = property(getLines, setLines, None,
    """List of measure lines, List of "MeasureLine" instances
    """)
    label = property(getLabel, setLabel, None,
    """Record identifiers that are used in some measure programs
    """)
    factor = property(getFactor, None, None, 
        """Factor
        """)
    yield_ = property(getYield, None, None, 
        """Yield of a record
        """)
    fixed = property(getFixed, setFixed,None, 
        """If fixed is True the yield is not calculated from measure
        """)

    def buildMeasure(self, list_lines, type_, decimals, recordType):
        """setMeasure(list_lines, type_, decimals, recordType)
        
        list_lines: list of measure lines
            [ [linetype, comment, units, length, width, height, formula], ... ]
            linetype:
                #-#empty string -> Normal
                0 -> Normal
                1 -> Parcial Subtotal
                2 -> Accumulated Subtotal
                3 -> Formula
            comment: comment string
            units: Number of Units (a)
            length: Length (b)
            width: Width (c)
            height: Height (d)
            formula: Can be a formula or a empty string
                Valid Operator: '(', ')', '+', '-', '*', '/' and '^'
                Valid variable: 'a', 'b', 'c','d' and 'p' (Pi=3.1415926)
        type: type of action
            M: Set measure
            A: Add measure
        decimal: budget decimals object
        
        Sets the measurelines for a record
        """
        # TODO: calcutate measure from lines
        _parcial = 0
        _total = 0
        _lines = []
        for _line in list_lines:
            _type, _comment = _line[0], _line[1]
            _units, _length = _line[2], _line[3]
            _width, _height = _line[4], _line[5]
            _formula = _line[6]
            _measure_line = MeasureLine(decimals, _type, _comment, _units,
                                        _length, _width, _height, _formula)
            _lines.append(_measure_line)

        if type_ == "M":
            self.lines = _lines
        elif type_ == "A":
            self.lines.extend(_lines)
        else:
            raise ValueError, utils.mapping(_("Type must be M or A. Type: $1"),
                                            (type_,))
        self.calculateMeasure(decimals, recordType)

    def calculateMeasure(self, decimals, recordType):
        #TODO: round acumulated_subtotal and parcial_subtotal
        if len(self.lines) > 0:
            _acumulated_total = 0.0
            _parcial_total = 0.0
            for line in self.lines:
                _parcial = line.parcial
                _acumulated_total += _parcial
                if line.lineType == 2:
                    line.setAcumulatedSubtotal(_acumulated_total, decimals)
                elif line.lineType == 1:
                    _parcialSubtotal = _acumulated_total - _parcial_total
                    line.setParcialSubtotal(_parcialSubtotal, decimals)
                    _parcial_total = _acumulated_total
            self.setMeasure(_acumulated_total, decimals)
            _DR = decimals.getDR(recordType)
            self.updateYield(decimals, recordType)
    def updateYield(self, decimals, recordType):
        if not self.fixed:
            self.setYield(self.measure, decimals, recordType)

class MeasureLine(object):
    """base.MeasureLine:
    
    Description:
        MeasureLine object
    Constructor:
        base.MeasureLine(budget, type_, comment, units, length, width, height,
                         formula)
    Ancestry:
    +-- object
      +-- MeasureLine
    Atributes:
        "lineType": Line type:
            #-#empty string -> Normal
            0 -> Normal
            1 -> Parcial Subtotal
            2 -> Accumulated Subtotal
            3 -> Formula, the comment is a formula.
        "comment": Descriptive text string
        "units": Number of Units (a)
        "length": length (b)
        "width": Width (c)
        "height": Height (d)
        "formula": can be a valid formula or a empty string
            Valid Operator: '(', ')', '+', '-', '*', '/' and '^'
            Valid variable: 'a', 'b', 'c','d'y 'p' (Pi=3.1415926)
        "partial" : result of measure line
        "parcial_subtotal"
        "acumulated_subtotal"
    Methods:
        __getstate__(self)
        __setstate__(self, tuple)
        __init__(self, decimals, type_, comment, units, length, width, height,
                 formula)
        {get/set}LineType
        {get/set}Comment
        {get/set}Units
        {get/set}Length
        {get/set}Width
        {get/set}Height
        {get/set}Formula
        getParcial
        {get/set}ParcialSubtotal
        {get/set}AcumulatedSubtotal
        calculateParcial
        eval_formula
    """
    __slots__ = ["_MeasureLine__lineType",
                 "_MeasureLine__comment",
                 "_MeasureLine__units",
                 "_MeasureLine__length",
                 "_MeasureLine__width",
                 "_MeasureLine__height",
                 "_MeasureLine__formula",
                 "_MeasureLine__parcial",
                 "_MeasureLine__parcial_subtotal",
                 "_MeasureLine__acumulated_subtotal",
                ]
    def __getstate__ (self):
        return (self.__lineType, self.__comment, self.__units,
                self.__length, self.__width, self.__height, self.__formula,
                self.__parcial)
    def __setstate__(self,tuple):
        self.__lineType = tuple[0]
        self.__comment = tuple[1]
        self.__units = tuple[2]
        self.__length = tuple[3]
        self.__width = tuple[4]
        self.__height = tuple[5]
        self.__formula = tuple[6]
        self.__parcial = tuple[7]
        #self.calculateParcial()
    def __init__(self, decimals, type_, comment, units, length, width, height,
                 formula):
        self.__parcial = 0.0
        self.__parcial_subtotal = 0.0
        self.__acumulated_subtotal = 0.0
        self.lineType = type_
        self.comment = comment
        self.setUnits(units, decimals)
        self.setLength(length, decimals)
        self.setWidth(width, decimals)
        self.setHeight(height, decimals)
        self.setFormula(formula, decimals)
        #self.calculateParcial()
    def getLineType(self):
        return self.__lineType
    def getComment(self):
        return self.__comment
    def getUnits(self):
        return self.__units
    def getLength(self):
        return self.__length
    def getWidth(self):
        return self.__width
    def getHeight(self):
        return self.__height
    def getFormula(self):
        return self.__formula
    def getParcial(self):
        return self.__parcial
    def getParcialSubtotal(self):
        return self.__parcial_subtotal
    def getAcumulatedSubtotal(self):
        return self.__acumulated_subtotal
    def setParcialSubtotal(self, parcial_subtotal, decimals):
        if not isinstance(parcial_subtotal, float):
            raise ValueError, utils.mapping(_(" Parcial Subtotal must be a "\
                      "float number. Parcial: $1"), (str(parcial_subtotal),))
        _DS = decimals.DS
        parcial_subtotal = round(parcial_subtotal, _DS)
        self.__parcial_subtotal = parcial_subtotal
    def setAcumulatedSubtotal(self, acumulated_subtotal, decimals):
        if not isinstance(acumulated_subtotal, float):
            raise ValueError, utils.mapping(_(" Acumulated Subtotal must be "\
                      "a float number. Parcial: $1"),
                     (str(acumulated_subtotal),))
        _DS = decimals.DS
        acumulated_subtotal = round(acumulated_subtotal, _DS)
        self.__acumulated_subtotal = acumulated_subtotal
    def calculateParcial(self, decimals):
        _DS = decimals.DS
        if self.lineType == 1 or self.lineType == 2:
            _parcial = 0.0
        elif self.lineType == 0: # self.formula == "":
            if isinstance(self.units, float):
                _a = self.units
            else:
                _a = 0.0
            if isinstance(self.length, float):
                _b = self.length
            else:
                _b = 1.0
            if isinstance(self.width, float):
                _c = self.width
            else:
                _c = 1.0
            if isinstance(self.height, float):
                _d = self.height
            else:
                _d = 1.0
            _parcial =  _a * _b  * _c * _d
        else:
            _parcial = self.eval_formula()
        _parcial = round(_parcial, _DS)
        self.__parcial = _parcial

    def setLineType(self, type_):
        if not type_ in [0, 1, 2, 3]:
            raise ValueError, utils.mapping(_("Invalid measure line type ($1)"),
                  (str(type_),))
        self.__lineType = type_
    def setComment(self, comment):
        if not isinstance(comment, str):
            raise ValueError, utils.mapping(_("Measure Comment must be a "\
                  "string ($1)"), (str(comment),))
        self.__comment = comment
    def setUnits(self, units, decimals):
        if units != "":
            if not isinstance(units, float):
                raise ValueError, utils.mapping(_("Invalid Measure Units ($1)"),
                      (str(units),))
            _DN = decimals.DN
            units = round(units, _DN)
        self.__units = units
        try:
            self.calculateParcial(decimals)
        except AttributeError:
            pass
    def setLength(self, length, decimals):
        if length != "":
            if not isinstance(length, float):
                raise ValueError, utils.mapping(_("Invalid Measure length ($1)"),
                      (str(units),))
            _DD = decimals.DD
            length = round(length, _DD)
        self.__length = length
        try:
            self.calculateParcial(decimals)
        except AttributeError:
            pass
    def setWidth(self, width, decimals):
        if width != "":
            if not isinstance(width, float):
                raise ValueError, utils.mapping(_("Invalid Measure Width ($1)"),
                      (str(units),))
            _DD = decimals.DD
            width = round(width, _DD)
        self.__width = width
        try:
            self.calculateParcial(decimals)
        except AttributeError:
            pass
    def setHeight(self, height, decimals):
        if height != "":
            if not isinstance(height, float):
                raise ValueError, utils.mapping(_("Invalid Measure Height ($1)"),
                      (str(height),))
            _DD = decimals.DD
            height = round(height, _DD)
        self.__height = height
        try:
            self.calculateParcial(decimals)
        except AttributeError:
            pass
    def setFormula(self, formula, decimals):
        if not isinstance(formula, str):
            raise ValueError, utils.mapping(_("Formula must be a "\
                  "string ($1)"), (str(formula),))
        if re.match(".*[^0123456789\.()\+\-\*/\^abcdp ].*", formula):
            raise ValueError, utils.mapping(_("There is invalid characters"\
                  "in formula ($1)"), (str(formula),))
        self.__formula = formula
        try:
            self.calculateParcial(decimals)
        except AttributeError:
            pass

    lineType = property(getLineType, setLineType, None,
    """Type of measure line
    """)
    comment = property(getComment, setComment, None,
    """Text
    """)
    units = property(getUnits, None, None,
    """Number of units
    """)
    length = property(getLength, None, None,
    """Length measure
    """)
    width = property(getWidth, None, None,
    """Width measure
    """)
    height = property(getHeight, None, None,
    """Height measure
    """)
    formula = property(getFormula, None, None,
    """Formula
    """)
    parcial = property(getParcial, None, None,
    """result of measure line
    """)
    acumulated_subtotal = property(getAcumulatedSubtotal,
                                   None, None,
    """Acumulated subtotal
    """)
    parcial_subtotal = property(getParcialSubtotal,
                                None, None,
    """Parcial subtotal
    """)
    def eval_formula(self):
        """eval_formula()
        
        formula:
            Valid Operator: '(', ')', '+', '-', '*', '/' and '^'
            Valid variable: 'a', 'b', 'c','d'y 'p' (Pi=3.1415926)
        units: Number of Units (a)
        length: Length (b)
        width: Width (c)
        height: Height (d)

        Evals the formula and return the result
        """
        formula = self.formula
        a = self.units
        b = self.length
        c = self.width
        d = self.height
        if a == "": a = 0.0
        if b == "": b = 0.0
        if c == "": c = 0.0
        if d == "": d = 0.0
        try:
            a = float(a)
        except:
            raise ValueError, _("'a' value must be a float number")
        try:
            b = float(b)
        except:
            raise ValueError, _("'b' value must be a float number")
        try:
            c = float(c)
        except:
            raise ValueError, _("'c' value must be a float number")
        try:
            d = float(d)
        except:
            raise ValueError, _("'d' value must be a float number")
        # spaces are erased
        formula.replace(" ","")
        # operators and varibles are replaced
        formula = formula.replace("+", " + ")
        formula = formula.replace("-", " - ")
        formula = formula.replace("*", " * ")
        formula = formula.replace("/", " / ")
        formula = formula.replace("^", " ** ")
        formula = formula.replace("(", " ( ")
        formula = formula.replace(")", " ) ")
        formula = formula.replace("a", str(a))
        formula = formula.replace("b", str(b))
        formula = formula.replace("c", str(c))
        formula = formula.replace("d", str(d))
        formula = formula.replace("p", "3.1415926")
        _list_formula = formula.split(" ")
        _formula2 = ""
        for oper in _list_formula:
            try:
                _float_oper= str(float(oper))
                _formula2 = _formula2 + _float_oper
            except ValueError:
                _formula2 = _formula2 + oper
        _g ={"__builtins__":{}}
        try:
            return eval(_formula2, _g)
        except:
            raise ValueError, _("Invalid formula")

class Decimals(object):
    """base.Decimals:
    
    Description:
        Decimals object
    Constructor:
        base.Decimals(DN=2, DD=2, DSP=2, DS=2,
                      DFC=3, DFPU=3, DFUO=3, DFA=3,
                      DRP=3, DRC=3, DRUO=3, DRA=3,
                      DP=2, DC=2, DPU=2, DUO=2, DEA=2, DES=2,
                      DIR=2, DIM=2, DIRC=2, DIMC=2, DCD=2,
                      DIVISA="EUR")
    Ancestry:
    +-- object
      +-- Decimals
    Atributes:
        "DN": Number of decimal places of the field "equal-size parts" in the
            measure lines.
            Default: 2 decimal places.
        "DD": Number of decimal places of the three dimensions in the 
            measure lines.
            Default: 2 decimal places.
        "DSP": Number of decimal places of the subtotal of a measure.
            Default: 2 decimal places.
        "DS": Number of decimal places of the total sum of a measure.
            Default: 2 decimal places.
        "DFC": Number of decimal places of the yield factor in a decomposition
            of a chapter or subchapter.
            Dafault: 3 decimal places.
        "DFPU": Number of decimal places of the yield factor in a decomposition
            of a unitary budget.
            Default: 3 decimal places.
        "DFUO": Number of decimal places of the yield factor in a decomposition
            of a unit of work.
            Default: 3 decimal places.
        "DFA": Number of decimal places of the yield factor in a decomposition
            of a Auxiliary element.
            Default: 3 decimal places.
        "DRC": Number of decimal places of the yield in a 
            decomposition of a chapter or subchapter.
            Number of decimal places of the result of the multiplictaion of
            the yield (or measure) and the factor in a decomposition of a 
            chapter or subcharter.
            Default: 3 decimal places.
        "DRPU": Number of decimal places of the yield in a decomposition
            of a unitary budget record.
            Number of decumal places of the result of the multiplication of 
            the factor and the yield in a decompositon of a untitary budget.
            Default: 3 decimal places.
        "DRUO": Number of decimal places of the yield in a decomposition of a
            unit of work.
            Decimal places of the result of the multiplication of the yield
            and the factor in a descomposition of a unit of work.
            Default: 3 decimal places.
        "DRA": Number of decimal places of the yield in a decompositon of a
            auxiliar element.
            Number of decimal places of the result of the multiplication of 
            the yield and the factor in a descomposition of a auxilar element.Decimales
            Default: 3 decimal places.
        "DP": Number of decimal places of the price of a budget.
            Default: 2 decimal places.
        "DC": Number of decimal places of the price of a chapter or subchapter.
            Default: 2 decimal places.
        "DPU": Number of decimal places of the price of a unitary budget.
            Default: 2 decimal places.
        "DUO": Number of decimal places of the price of a unit of work.
            Default: 2 decimal places.
        "DEA": Number of decimal places of the price of a auxiliar element.
            Default: 2 decimal places.
        "DES": Number of decimal places of the price of the simple elements.
            Default: 2 decimal places.
        "DIR": Number of decimal places of the resulting amount to multiply 
            the total yield and the price of the elements of a unit of work or
            a auxiliar element.
        "DIRC": Number of decimal places of the resulting amount to multiply 
            the total yield and the price of the elements of a budget, chapter
            or a subchapter.
        "DCD": Number of decimal places ot the resulting amount to sum the
            direct costs of a unit of work (and auxiliar element).
            Number of decimal places of the indirect costs.
            Default: 2 decimal places.
        "DIVISA": monetary unit.
    Methods:
        __init__(DN=2, DD=2, DSP=2, DS=2,
                 DFC=3, DFPU=3, DFUO=3, DFA=3,
                 DRC=3, DRPU=3, DRUO=3, DRA=3,
                 DP=2, DC=2, DPU=2, DUO=2, DEA=2, DES=2,
                 DIR=2, DIRC=2, DCD=2,
                 DIVISA="EUR")
        __getitem__(key)
        haskey(key)
        getD(recordtype)
        getDF(recordType)
        getDR(recordType)
        getDI(recordType)
    """
    # TODO: get/set methods
    def __init__(self,
                 DN=2, DD=2, DSP=2, DS=2,
                 DFC=3, DFPU=3, DFUO=3, DFA=3, 
                 DRC=3, DRPU=3, DRUO=3, DRA=3, 
                 DP=2, DC=2, DPU=2, DUO=2, DEA=2, DES=2, 
                 DIR=2, DIRC=2, DCD=2, 
                 DIVISA="EUR" ):
        self.DN = DN
        self.DD = DD
        self.DSP = DSP
        self.DS = DS
        self.DFP = 3
        self.DFC = DFC
        self.DFPU = DFPU
        self.DFUO = DFUO
        self.DFA = DFA
        self.DRP = 3
        self.DRC = DRC
        self.DRPU = DRPU
        self.DRUO = DRUO
        self.DRA = DRA
        self.DP = DP
        self.DC = DC
        self.DPU = DPU
        self.DUO = DUO
        self.DEA = DEA
        self.DES = DES
        self.DIR = DIR
        self.DIRC = DIRC
        self.DCD = DCD
        self.DIVISA = DIVISA
    def __getitem__(self, key):
        return self.__dict__[key]
    def haskey(self, key):
        return key in self.__dict__
    def getD(self, recordType):
        # DP: budget.
        # DC: chapter and subcharter. 
        # DUO: unit.
        # DEA: auxiliar element.
        # DES: simple element.
        _hierarchy = recordType.hierarchy
        if _hierarchy == 0: #budget, type 0, subtipe "OB"
            _decimal = self.DP
        elif _hierarchy == 1: #chapter/subcharter, type 0, subtipe ""
            _decimal = self.DC
        else: # other
            _type = recordType.type
            _subtype = recordType.subtype
            if _subtype == "EA": # auxiliar element type 0 subitype "EA"
                _decimal = self.DEA
            if _subtype == "PU": # unitary budget type 0 subitype "PU"
                _decimal = self.DPU
            elif (_type in [1, 2, 3] or
                  _subtype in ["H", "Q", "%", "MC", "MCr", "MM", "MS", "ME",
                                "MCu", "Mal","ML", "M"]
                 ): # simple element
                _decimal = self.DES
            else: # unit  type 0, subtipe ["EU", "EC", "EF", "PA"]
                _decimal = self.DUO
        return _decimal
    def getDF(self, recordType):
        # Factor: DF
        #   ->DFP: Budget
        #   ->DFC: Chapter/Subchapter
        #   ->DFUO: Unit
        #   ->DFA: Auxiliar
        #   ->DFPU: Unitary budget
        if recordType.hierarchy == 0: #budget
            _decimal = self.DFP
        elif recordType.hierarchy == 1: #chapter/subcharter
            _decimal = self.DFC
        else: # other
            if recordType.subtype == "EA": # auxiliar element
                _decimal = self.DFA
            if recordType.subtype == "PU": # unitary budget element
                _decimal = self.DFPU
            else: # unit  EU EC EF PA
                _decimal = self.DFUO
        return _decimal
    def getDR(self, recordType):
        # Yield: DR
        #   ->DRP: Budget
        #   ->DRC: Chapter/Subchapter
        #   ->DRUO: Unit
        #   ->DRA: Auxiliar
        #   ->DRPU: Unitary budget
        if recordType.hierarchy == 0: #budget
            _decimal = self.DRP
        elif recordType.hierarchy == 1: #chapter/subcharter
            _decimal = self.DRC
        else: # other
            if recordType.subtype == "EA": # auxiliar element
                _decimal = self.DRA
            if recordType.subtype == "PU": # unitary budget element
                _decimal = self.DRPU
            else: # unit
                _decimal = self.DRUO
        return _decimal
    def getDI(self, recordType):
        # DIRC: budget, chapter and subcharter. 
        # DIR: unit, auxiliar element.
        _hierarchy = recordType.hierarchy
        _subtype = recordType.subtype
        if _hierarchy == 0 or _hierarchy == 1 or _subtype == "PU":
            #budget, type 0, subtipe "OB"
            #chapter/subcharter, type 0, subtipe ""
            #unitary budget, type 2, subtype "PU"
            _decimal = self.DIRC
        else: # other
            # auxiliar element type 0 subitype "EA"
            # unit  type 0, subtipe ["EU", "EC", "EF", "PA", "PU"]
            _decimal = self.DIR
        return _decimal

class Sheet(object):
    """base.Sheet:
    Description:
        Sheet of conditions object
    Constructor:
        base.Sheet(sheet_dict)
    Ancestry:
    +-- object
      +-- Sheet
    Atributes:
        "sheet_dict": { <Field key> : { <Section key> : <Paragraph key>}
            <Field key>: must be in Budget.SheetFields
            <Section key>: must be in Budget.SheetSections
            <Paragraph key>: must be in Budget.SheetParagraph
    Methods:
        __getstate__(self)
        __setstate__(self, tuple)
        __init__(self, sheet_dict={})
        {get/set}Sheet_dict
        getFields
        getSections
        getParagraph
        addField
        addSection
    """
    __slots__ = ["_Sheet__sheet_dict"]
    def __getstate__ (self):
        return (self.__sheet_dict,)
    def __setstate__(self,tuple):
        self.__sheet_dict = tuple[0]
    def __init__(self):
        self.__sheet_dict = {}
    def getSheet_dict(self):
        return self.__sheet_dict
    def setSheet_dict(self, sheet_dict):
        if not isinstance(sheet_dict, dict):
            raise ValueError, _("sheet_dict must be a dictionay")
        self.__sheet_dict = sheet_dict
    def getFields(self):
        return self.sheet_dict.keys()
    def getSections(self, field):
        if field in self.__sheet_dict:
            return self.__sheet_dict[field].keys()
        else:
            return None
    def getParagraph(self, field, section):
        if (field in self.__sheet_dict and
            section in self.__sheet_dict[field]):
            return self.__sheet_dict[field][section]
        else:
            return None
    def addField(self, field, section_dict):
        if not isinstance(field, str):
            raise ValueError, _("sheet field must be a string")
        if not isinstance(section_dict, dict):
            raise ValueError, _("section_dict must be a dictionary")
        self.__sheet_dict[field] = section_dict
    def addSection(self, field, section, paragraph):
        if not isinstance(field, str):
            raise ValueError, _("sheet field must be a string")
        if not isinstance(section, str):
            raise ValueError, _("sheet section must be a string")
        if not isinstance(paragraph, str):
            raise ValueError, _("sheet paragraph must be a string")
        if not field in self.__sheet_dict:
            self.addField(field, { })
        _field = self.__sheet_dict[field]
        _field[section] = paragraph
    sheet_dict = property(getSheet_dict, setSheet_dict, None,
    """Sheet dictionary { <Field key> : { <Section key> : <Paragraph key>}""")

class Budget(object):
    """base.Budget:
    
    Description:
        Budget objetc
    Constructor:
        base.Budget()
    Ancestry:
    +-- object
      +-- Budget
    Atributes:
        "filename": file name of the budget file (FIEBDC)
        "__records": Dictionary with the budget records.
            { "code" : Record object, }
        "__synonyms": Dictionary with the records synonums.
            { "code" : ["synonym",],}
            Each record code can have synonym codes.
        "__root": The root record code.
        "__title_list": List with the Headers and list of Titles for prices and
            decimal places.
            [ "Header", ["Title1", "Title2", ... ] ]
            The records can have diferent prices for diferent ages, geografical
            places, ...
            The Headers is the type of hierarchy of the prices
            Each Title have a group of Prices and a Decimals definition
        "__decimals": List with the decimal places used to round the 
            result of the calculations with prices and measures
            The values are Decimals objects 
            The <0> objets is the default Decimals (seted in FIEBDC-3),
            The others keys are for the diferent groups of Prices
        "__percentages": Dictionary with the percentages
            keys:
                "CI"    Indirect Cost
                "GG"    General expenses
                "BI"    Industrial benefit
                "BAJA"  Low (what this do here?)
                "IVA"   Tax
        "__file_owner"
        "__comment"
        "__date"
        "__budgetType" A integer. Type of data in budget
                0 -> Undefined
                1 -> Base data.
                2 -> Budget.
                3 -> Certificate.
                4 -> Base date update.
        "__budgetCerficateOrder" Only valid if budgetType is 3.
        "__budgetCerficateDate" Only valid if budgetType is 3
        "__title_index": A integer. The active group of Prices and Decimals.
        "__sheet_sections": Dictionary whith de sheet sections
        "__sheet_fields": Dictionary whith sheet fields
        "__sheet_paragraphs": Dictionary whith sheet paragraphs
        "__companys": Dictionary whith companys object
                         { company_code: company_object }
        "__tec_info": Dictionary whith tecnical information
                        {ti_code : ["desciption text", "unit"]}
        "__labels": Label dictionary { "label": [ "code", ], }
    Methods:
        iter
        iterPreOrder
        iterPostOrder
        getRoot(self)
        hasPath(self, path)
        getchildren(self, code)
        setOwner(self, owner)
        setDate(self, date)
        setComment(self, comment)
        setBudgetType(self, type)
        setCertificateOrder(self, order)
        setCertificateDate(self, date)
        setTitleList(self, title)
        getTitleList(self)
        getActiveTitle(self)
        setDecimals(self, dictionary)
        getDecimals(self, decimal="All", N=None)
        setPercentages(self, dictionary)
        getPercentages(self, percentage="All")
        getAllParents(self, code)
        getAllchildren(self, code)
        getNDecomposition(self, code, N)
        getDecomposition(self,code)
        getMeasure(self, path)
        getStrYield
        getStrFactor
        setTree(sef, code, child_code, position, factor, yield_, total,
                list_lines, label, type)
        eval_formula(self, formula, a, b, c, d)
        getText(self, code)
        setText(self, code, text)
        setRecord(self, code, synonyms, hierarchy, unit, sumary, ...
        hasRecord(self, code)
        getRecord
        addPriceToRecord
        getStrPriceFromRecord
        getCode(self, path)
        getAmount
        getStrAmount
        setSheetSection(self, sheet_code, sheet_title)
        hasSheetSection(self, section)
        setSheetSections(self,dictionary)
        setSheetField(self, field_code, field_title)
        hasSheetField(self, field)
        getSheetField(self, field)
        setSheetFields(self, field_dict)
        setSheetParagraph(self, paragraph_code, paragraph_text)
        hasSheetParagraph(self, paragraph)
        getSheetParagraph(self, paragraph)
        setSheetParagraphs(self, paragraph_dict)
        setSheetRecord(self, record_code,field, section_dict)
        addFile(self, record_code, filename)
        setCompany(self, code, summary, name, offices, cif, web, email )
        getCompany
        getCompanyKeys
        addTecInfo(self, ti_code, text, unit)
        hasTecInfo(self, ti_code)
        getTecInfo(self, ti_code)
        setTecnicalInformation(self, _record_code, _ti_dict)
        changeCode(self, record_code, new_rocord_code)
        addLabel
        setParametricSelectComment
        setParametricSummary
        setParametricText
    """


    def __init__(self):
        """__init__(self)
        
        Initialize the budget atributes
        """
        self.__title_index = 0
        self.__decimals = [Decimals(), Decimals()]
        self.__percentages = { "CI" : "" ,"GG": "", "BI": "",
                               "BAJA": "", "IVA" : ""}
        self.__title_list = [ "", [ ] ]
        self.__root = None
        self.__file_owner = ""
        self.__comment = ""
        self.__budgetCerficateOrder = None
        self.__budgetCerficateDate = None
        self.__date = (0,0,0)
        self.__budgetType = 0
        self.__records = { }
        self.__synonyms = { }
        self.__sheet_sections = { }
        self.__sheet_fields = { }
        self.__sheet_paragraphs = { }
        self.__companys = { }
        self.__tec_info = { }
        self.__labels = { }

    def __getstate__(self):
        return (self.__title_index, self.__decimals, self.__percentages,
                self.__title_list, self.__root, self.__file_owner,
                self.__records, self.__synonyms, self.__sheet_sections,
                self.__sheet_fields, self.__sheet_paragraphs,self.__companys,
                self.__tec_info, self.__labels)

    def __setstate__(self, tuple):
        self.__title_index = tuple[0]
        self.__decimals = tuple[1]
        self.__percentages = tuple[3]
        self.__title_list = tuple[4]
        self.__root = tuple[4]
        self.__file_owner = tuple[5]
        self.__records = tuple[6]
        self.__synonyms = tuple[7]
        self.__sheet_sections = tuple[8]
        self.__sheet_fields = tuple[9]
        self.__sheet_paragraphs = tuple[10]
        self.__companys = tuple[11]
        self.__tec_info = tuple[12]
        self.__labels = tuple[13]

    def iter(self):
        for record in self.__records:
            yield record
    def iterPreOrder(self, recordCode, codes=None):
        if codes is None:
            codes = []
        _children = self.getchildren(recordCode)
        for _child in _children:
            if not _child in codes:
                codes.append(_child)
                self.iterPreOrder(_child, codes)
        return codes
    def iterPostOrder(self, recordCode, codes=None):
        if codes is None:
            codes = []
        _children = self.getchildren(recordCode)
        for _child in _children:
            if not _child in codes:
                self.iterPreOrder(_child, codes)
                codes.append(_child)
        return codes

    def getRoot(self):
        """getRoot(self)
        
        Returns the root record code
        """
        return self.__root

    def hasPath(self, path):
        """hasPath(self, path)
        
        path: The path of the record in the budget, It is a tuple.
        Tests if the path is valid in the budget
        """
        try:
            self.getCode(path)
            return True
        except ValueError:
            return False

    def getchildren(self, code):
        """getchildren(self, code)
        
        code: a record code.
        Return a list whith the child codes of a record
        """
        _record = self.__records[code]
        _children = _record.children
        _child_code = [ _child.code for _child in _children ]
        return _child_code
    def setOwner(self, owner):
        """setOwner(self, owner)
        
        owner: data owner 
        Set the data owner.
        """
        if isinstance(owner, basestring):
            self.__file_owner = owner
        else:
            raise  TypeError, _("Owner must be a string")

    def setDate(self, date):
        """setOwner(self, date)
        
        date (_y, _m, _d)
        Set the date when de file was generated
        """
        if isinstance(date, tuple) and len(date) == 3 and \
           isinstance(date[0], int) and isinstance(date[1], int) and \
           isinstance(date[2], int) and date[1] in range(13) and \
           date[2] in range(32):
            if date[1] != 0 and date[2] != 0:
                datetime.date(*date)
            self.__date = date
        else:
            raise  TypeError, utils.mapping(_("Invalid Date: $1"),(str(date),))    

    def setComment(self, comment):
        """setOwner(self, comment)
        
        comment: text to comment the budged
        Set the comment.
        """
        if isinstance(comment, basestring):
            self.__comment = comment
        else:
            raise  TypeError, _("Comment must be a string")

    def setBudgeType(self, budget_type):
        """setOwner(self, budget_type)
        
        budget_type: type of data in budget
            0 -> Undefined
            1 -> Base data.
            2 -> Budget.
            3 -> Budget certificate.
            4 -> Base date update.
        Set the budget type.
        """
        if budget_type in [1, 2, 3, 4]:
            self.__budgetType = budget_type
        else:
            raise  ValueError, _("Budget type must be 1, 2, 3 or 4.")
                                            
    def setCertificateOrder(self, certificate_order, certificate_date):
        """setOwner(self, budget_type)
        
        certificate_order: certificate number
        certificate_date: certificate date
        Set the certificate order and date.
        """
        if isinstance(certificate_order, int):
            self.__budgetCerficateOrder = certificate_order
        else:
            raise  ValueError, _("Certificate order must be a integer.")

    def setCertificateDater(self, certificate_date):
        """setCertidicateDate(self, certificate_date)
        
        Set the certificate date.
        """
        if isinstance(certificate_date, tuple) and \
           len(certificate_date) == 3 and \
           isinstance(certificate_date[0], int) and \
           isinstance(certificate_date[1], int) and \
           isinstance(certificate_date[2], int):
            datetime.date(*certificate_date)
            self.__budgetCerficateDate = certificate_date
        else:
            raise  ValueError, _("Budget certificate Date must be a valid Date.")

    def setTitleList(self, title_list):
        """setTitleList(self, title_list)
        
        title_list: [ "Header", ["Title1", "Title2", ... ] ]
        Set the header and titles for the price groups and decimals.
        """
        title_list[0] = str(title_list[0])
        if isinstance(title_list, list) and isinstance(title_list[1], list):
            for i in range(len(title_list[1])):
                title_list[1][i] = str(title_list[1][i])
            self.__title_list = title_list
        else:
            raise TypeError, _("Invalid title list format")

    def getTitleList(self):
        """ getTitleList(self)
        
        Returns the header and titles for the price groups and decimals.
        """
        return self.__title_list

    def getActiveTitle(self):
        """getActiveTitle(self)
        
        Returns the active Title of price group
        """
        return self.__title_index

    def setDecimals(self, dictionary, N):
        """setDecimals(self, dictionary, N)
        
        dictionay: the decimal dictionary
        N: the price group
        Sets the Decimals for a price group.
        """
        if N == -1 or N == len(self.__decimals):
            _default_decimals = self.__decimals[0]
            self.__decimals.append(_default_decimals)
        elif N < len(self.__decimals):
            _default_decimals = self.__decimals[N]
        else:
            raise IndexError, _("Invalid Index Title")
        for _decimal in dictionary:
            if dictionary[_decimal] == "":
                dictionary[_decimal] = eval("_default_decimals." + _decimal)
        decimals = Decimals(dictionary["DN"], dictionary["DD"],
                            dictionary["DSP"], dictionary["DS"],
                            dictionary["DFC"],
                            dictionary["DFPU"], dictionary["DFUO"],
                            dictionary["DFA"], dictionary["DRC"],
                            dictionary["DRPU"], dictionary["DRUO"],
                            dictionary["DRA"], dictionary["DP"],
                            dictionary["DC"], dictionary["DPU"],
                            dictionary["DUO"], dictionary["DEA"],
                            dictionary["DES"], dictionary["DIR"],
                            dictionary["DIRC"], dictionary["DCD"],
                            dictionary["DIVISA"])
        self.__decimals[N] = decimals
    def getDecimals(self, decimal=None, N=None):
        """getDecimals(self,decimal="All",N=None)
        
        decimal:
            "All": Return a Decimals objet for a price group
            "keys": Return the keys of a Decimal object
            key: Return a Decimal value for a price group
        N: the price group None,1,2,..
            None: Return the active price group
        """
        if decimal is None: decimal = "All"
        if N is None: N = self.getActiveTitle()
        if decimal == "All":
            return self.__decimals[N+1]
        elif decimal == "keys":
            return self.__decimals[N+1].keys
        elif self.__decimals[N+1].haskey(decimal):
            return self.__decimals[N+1][decimal]
        else:
            raise KeyError, _("Decimal Key error")

    def setPercentages(self, dictionary):
        """setPercentages(self, dictionary):
        
        dictionary: the percentage dictionary
        Sets the percentage dictionary.
        """
        _default_percentages = self.__percentages
        for percentage in dictionary:
            if dictionary[percentage] == 0: 
                dictionary[percentage] = ""
            elif dictionary[percentage] == "":
                dictionary[percentage] = _default_percentages[percentage]
        _percentages = { "CI": dictionary["CI"],
                         "GG": dictionary["GG"],
                         "BI": dictionary["BI"],
                         "BAJA": dictionary["BAJA"],
                         "IVA" : dictionary["IVA"]}
        self.__percentages = _percentages

    def getPercentages(self, key=None):
        """getPercentages(self, key=None)
        
        key:
            "All": Return the Percentages dictionary
            "keys": Return the keys of a Percentages object
            key: Return a Percentages value for the key
        """
        if Key is None:
            key = "All"
        if key == "All":
            return self.__percentages
        elif key == "keys":
            return self.__percentages.keys
        elif key in self.__percentages:
            return self.__percentages[key]
        else:
            raise KeyError, _("Invalid Percentage key")

    def getAllParents(self,code):
        """getAllParents(self,code)
        
        code: a record code.
        Returns a list with all the parents of a record
        All record which the record is in its descomposition list, 
        including the parents of the parents
        """
        if code in self.__records:
            _parents = self.__records[code].parents
            if len(_parents) == 0: return [ ]
            for _antecesor in _parents[:]:
                _parents = _parents + self.getAllParents(_antecesor)
            return _parents
        else:
            return [ ]

    def getAllchildren(self,code):
        """getAllchildren(self,code
        
        code: a record code.
        Returns a list with all the children of a record, including
        the children of the children
        """
        if code in self.__records:
            _children = self.__records[code].children
            _children = [ _child.code for _child in _children ]
            for _child in _children[:]:
                _children = _children + self.getAllchildren(_child)
            return _children
        else:
            return [ ]

    def getNDecomposition(self, code, N):
        """getDecomposition(self,path)
        
        path: the path for a record
        Returns the Decomposition object of a record
        """
        _record = self.getRecord(code)
        _decomposition_list = _record.children
        _decomposition = _decomposition_list[N]
        return _decomposition
    
    def getDecomposition(self, path):
        """getDecomposition(self,path)
        
        path: the path for a record
        Returns the Decomposition object of a record
        """
        if path == (0,):
            _type = self.getRecord(self.__root).recordType
            return Decomposition( 0, self.__root,
                   [Measure(self.getDecimals(), _type,
                            0.0, [], "", 1.0, 1.0)])
        else:
            return self.getNDecomposition(self.getCode(path[:-1]), path[-1])

    def getMeasure(self, path):
        """getMeasure(self, path)
        
        path: the path for a record
        Return the measute object of a record
        """
        _decomposition = self.getDecomposition(path)
        _measure = _decomposition.budgetMeasures[0]
        return _measure

    def getStrYield(self, measure, recordType):
        #_DR = measure.getDR(self.getDecimals())
        _DR = self.getDecimals().getDR(recordType)
        _yield = ("%." + str(_DR) + "f" ) % measure.yield_
        return _yield

    def getStrFactor(self, measure, recorType):
        _DF = self.getDecimals().getDF(recordType)
        #_DF = measure.getDF(self.getDecimals())
        _factor = ("%." + str(_DF) + "f" ) % measure.factor
        return _factor

    def setTree(self, code, child_code, position, factor, yield_, total,
                list_lines, label, type_):
        """setTree(self, code, child_code, position, factor,yield_, total,
        list_lines, label, type_)
        
        code: the parent record code
        child_code: child record code
        position: position of child record in record parent record
            decomposition. Position == -1 -> new child
        factor:
        yield_:
        total: total measure (float)
        list_lines: list of measure lines
            [ [linetype, comment, units, length, width, height], ... ]
            linetype:
                empty string -> Normal
                1 -> Parcial Subtotal
                2 -> Accumulated Subtotal
                3 -> Formula, the comment is a formula.
            comment: Can be a descriptive text or a formula
                Valid Operator: '(', ')', '+', '-', '*', '/' and '^'
                Valid variable: 'a', 'b', 'c','d'y 'p' (Pi=3.1415926)
            units: Number of Units (a)
            length: Length (b)
            width: Width (c)
            height: Height (d)
        label: Record Identifiers that are used by some measure programs.
        type_: type of action
            M: Set measure
            A: Add measure
        Sets the decomposition of a record in a child record
        """
        if code is None: # No-estructured measures
            code = self.getRoot()
            if code == None: # No root
                print "No-estructured measures. Adding root record", 
                self.setRecord("root", [], 0, "", "", [0.0,], [(1,1,1970)],
                                     0, "")       
                code = self.getRoot()

        if not utils.is_valid_code(code)[0]:
            raise ValueError, utils.mapping(_("Invalid parent code: $1"),
                                            (code,))
        if not utils.is_valid_code(child_code)[0]:
            raise ValueError, utils.mapping(_("Invalid child code: $1 $2"),
                                           (code,child_code))
        if not isinstance(position, int):
            raise ValueError, utils.mapping(_("Invalid position in measure "\
                  "$1, in code $2"), (parent_code, position))
        # Test circular references
        _all_parent_list = self.getAllParents(code) + [ code ]
        _all_child_list = self.getAllchildren(child_code) + [ child_code ]
        for _parent_code in _all_parent_list:
            if _parent_code in _all_child_list:
                # TODO: change return to except
                print utils.mapping(_("Circular Decomposition, parent code: "\
                      "$1, child code: $2, repeated code: $3"),
                      (code, child_code, _parent_code))
                return

        # Creating reference to parent code in child record
        if child_code in self.__records:
            _child_record = self.__records[child_code]
        else:
            _child_record = self.setRecord(child_code, [], -1, "", "", [], [],
                                     "", "")
        if code in self.__records:
            code = self.__records[code].code
        _child_record.appendParent(code)
        child_code = self.__records[child_code].code
        if code in self.__records:
            # if the code exits retake previous values.
            _record = self.__records[code]
            _child_number = len(_record.children)
            if position == -1: # New child
                position = _child_number
            if position == -2: # No-estructured measures or empty position (error in FIEBDC file)
                positions = _record.getChildPositions(child_code)
                if len(positions) == 1:
                    position = positions[0]
                    print utils.mapping(_("No-estructured measure or empty position. Parent Code: "\
                          "$1, Child code: $2, Position: $3"),(code, child_code, position))
                else:
                    position = _child_number
                    print utils.mapping(_("No-estructured measure or empty position. "\
                          "Repeated child in unspecified position. "\
                          "It is impossible to determine the position. "\
                          "New child is added in the decomposition. "\
                          "Parent code: $1, Child code: $2, Position: $3"),(code, child_code, position))
            if position == _child_number:
                # The record do not have the child
                if not isinstance(factor, float): factor = 1.0
                if not isinstance(yield_, float): yield_ = 1.0
                if not isinstance(total, float): total = 0.0
                if not isinstance(list_lines, list): list_lines = []
                _child = _record.appendChild(child_code, self.getDecimals(),
                         factor, yield_, total, list_lines, type_, label)
            elif position < _child_number:
                # The record have the child
                _child = _record.children[position]
                if child_code != "" and child_code != _child.code:
                    _child.code = child_code
                if factor != "" :
                    if not isinstance(factor, float):
                        factor == 1.0
                    _child.budgetMeasures[0].setFactor(factor,
                        self.getDecimals(), _record.recordType)
                if yield_ != "":
                    if not isinstance(yield_, float):
                        yield_ = 1.0
                    _child.budgetMeasures[0].setYield(yield_, 
                        self.getDecimals(), _record.recordType)
                _measure = _child.budgetMeasures[0]
                if total != "":
                    if not isinstance(total, float):
                        yield_ = 0.0
                    _measure.setMeasure(total, self.getDecimals())
                if isinstance(list_lines, list) and len(list_lines) > 0:
                    _measure.buildMeasure(list_lines, type_, self.getDecimals(),
                                          _record.recordType)
                if isinstance(label, str) and label != "" :
                    _measure.label = label
            else:
                # TODO: change return for except
                print utils.mapping(_("Error: Invalid child position in "
                      "decomposition. Parent code: $1 Child code: $2 "\
                      "Position: $3"), (code, child_code, position))
                return
        else:
            if child_code == "" : 
                print utils.mapping(_("Error: Empty child code. Parent code: "\
                      "$1 Position: $2"), (code, position))
                return
            if position == -1:
                position = 0
            elif position != 0:
                print utils.mapping(_("Error: Invalid child position in "\
                      "decomposition. Parent code: $1 Child code: $2 "\
                      "Position: $3"), (code, child_code, position))
                return
            if not isinstance(factor, float):
                factor = 1.0
            if not isinstance(yield_, float):
                yield_ = 1.0
            if not isinstance(total, float):
                total = 1.0
            _record = self.setRecord(code, [], "", "", "", [], [],
                                     "", "")
            _child = _record.appendChild(child_code, self.getDecimals(),
                         factor, yield_, total, list_lines, type_, label)

    def eval_formula(self, formula, a, b, c, d):
        """eval_formula(self, formula, a, b, c, d)
        
        formula:
            Valid Operator: '(', ')', '+', '-', '*', '/' and '^'
            Valid variable: 'a', 'b', 'c','d'y 'p' (Pi=3.1415926)
        units: Number of Units (a)
        length: Length (b)
        width: Width (c)
        height: Height (d)

        Evals the formula and return the result
        """
        if a == "": a = 0.0
        if b == "": b = 0.0
        if c == "": c = 0.0
        if d == "": d = 0.0
        try:
            a = float(a)
        except:
            raise ValueError, _("'a' value must be a float number")
        try:
            b = float(b)
        except:
            raise ValueError, _("'b' value must be a float number")
        try:
            c = float(c)
        except:
            raise ValueError, _("'c' value must be a float number")
        try:
            d = float(d)
        except:
            raise ValueError, _("'d' value must be a float number")
        # spaces are erased
        sre.sub("[ ]","",formula)
        # operators and varibles are replaced
        formula = formula.replace("+", " + ")
        formula = formula.replace("-", " - ")
        formula = formula.replace("*", " * ")
        formula = formula.replace("/", " / ")
        formula = formula.replace("^", " ** ")
        formula = formula.replace("(", " ( ")
        formula = formula.replace(")", " ) ")
        formula = formula.replace("a", str(a))
        formula = formula.replace("b", str(b))
        formula = formula.replace("c", str(c))
        formula = formula.replace("d", str(d))
        formula = formula.replace("p", "3.1415926")
        _list_formula = formula.split(" ")
        _formula2 = ""
        for oper in _list_formula:
            try:
                _float_oper= str(float(oper))
                _formula2 = _formula2 + _float_oper
            except ValueError:
                _formula2 = _formula2 + oper
        _g = {"__builtins__":{}}
        try:
            return eval(_formula2, _g)
        except:
            raise ValueError, _("Invalid formula")

    def getText(self,code):
        """getText(self,code)
        
        code: the record code
        Returns the description text of a record
        """
        if code in self.__records:
            return self.__records[code].text
        else:
            raise IndexError, _("Invalid code")

    def setText(self,code,text):
        """setText(self,code,text)
        
        code: the parent record code
        text: the descripion text
        Sests the description text of a record
        """
        if not utils.is_valid_code(code)[0]:
            raise ValueError, utils.mapping(_("Invalid record: $1"), (code,))
        if not code in self.__records:
            _record = self.setRecord(code, [], "", "", "", [], [],
                                     "", "")
            _record.text = text
        else:
            _record = self.__records[code]
            _record.text = text

    def setRecord(self, code, synonyms, hierarchy, unit, summary, price, date,
                  type_, subtype):
        """setRecord(self, code, synonyms, hierarchy, unit, summary, price,
                     date, type_, subtype)
        
        code: Code string
        synonyms: List of synonym codes of the record
        hierarchy:
            0 -> root
            1 -> Chapter/Subchapter
            2 -> Other
        unit: unit of measure record
        summary: Short description of a record
        price: List of prices
        date: List of dates
        "type_" and "subtype":
            0 Without classifying
               EA  Auxiliary element
               EU  Unitary element
               EC  Complex element
               EF  Functional element
               OB  Construction site
               PA  Cost overrun
               PU  Unitary budget
            1 Labourforce 
               H   Labourforce
            2 Machinery and auxiliary equipment
               Q   Machinery
               %   Auxiliary equipment
            3 Building materials
               MC  Cement
               MCr Ceramic
               MM  Wood
               MS  Iron and steel
               ME  Energy
               MCu Copper
               MAl Aluminium
               ML  Bonding agents
               M   Others materials
          Hierarchy            type subtype
            0->root         -> 0 -> None,OB
            1->[sub]chapter -> 0 -> None,PU
            2->Other        -> 0 -> None,EA,EU,EC,EF,PA
                               1 -> None,H
                               2 -> None,Q,%
                               3 -> None,MC,MCr,MM,MS,ME,MCu,Mal,ML,M
        Adds a record in the budget
        """
        # hierarchy
        if hierarchy == 0 :
            # is the root record
            if self.__root is None:
                self.__root = code
            else:
                print _("Only can be one root record")
                return
                # TODO: If the root is created in settree. No-estructured measures
                # TODO  Rewrite root values
        # retake previous values.
        # TODO: test synonyms
        _budget = self
        if not code in self.__records:
            if code[-1] == "$":
                _record = ParametricRecord(_budget.getDecimals(), code,
                                           synonyms, hierarchy,
                                           unit, summary, [], type_, subtype,
                                           [], "")
            else:
                _record = Record(_budget.getDecimals(), code, synonyms,
                                 hierarchy, unit,
                                 summary, [], type_, subtype,[], "")
            self.__records[code] = _record
            _prices = [[price[i], date[i]] for i in range(len(price))]
            _record.setPrices(_prices, self.getDecimals())
        else:
            _record = self.__records[code]
            code = _record.code
            if len(synonyms) != 0 and synonyms[0] == "":
                synonyms = _record.synonyms
            if unit == "":
                unit = _record.unit
            if summary == "":
                summary = _record.summary
            #TODO: test empty price list
            if len(price) == 0 or price[0] == "": 
                _prices = _record.prices
            else:
                _prices = [ [price[i], date[i]] for i in range(len(price))]
            if type_ == "":
                type_ = _record.recordType.type
            _record.synonyms = synonyms
            _record.unit = unit
            _record.summary = summary
            _record.setPrices(_prices, self.getDecimals())
            _record.recordType.hierarchy = hierarchy
            _record.recordType.type = type_
            _record.recordType.subtype = subtype
        return _record

    def hasRecord(self,code):
        """hasRecord(self,code)
        
        code: Code record
        Return True if the budget have this record code.
        """
        if code in self.__records:
            return True
        else:
            return False

    def getRecord(self, code):
        """getRecord(self, code)
        
        code: Code record
        Return the Record object
        """
        return self.__records[code]

    def addPriceToRecord(self, price_date, record):
        """addPriceToRecord(self, price, record)
        
        Add a price to the price list of the record.
        price must fulfill:
            - must be a list with two items
            - the first item: price must be a float
        """
        record.addPrice(price_date, self.getDecimals())

    def getStrPriceFromRecord(self, index_price, record):
        _price = record.getPrice(index_price)
        _D = self.getDecimals().getD(record.recordType)
        _price = ("%." + str(_D) + "f" ) % _price
        return _price

    def getCode(self, path):
        """getCode(self, path)
        
        path: path record in the budget.
        Return the code record
        """
        if isinstance(path, tuple) and len(path)>= 1:
            if path[0] == 0:
                _code = self.__root
                for i in path[1:]:
                    if isinstance(i, int):
                        _record = self.__records[_code]
                        _children_list = _record.children
                        try:
                            _child = _children_list[i]
                        except:
                            raise ValueError, _("This record does not exits")
                        _code = _child.code
                    else:
                        raise ValueError, _("Path item must be a integer")
                return _code
            else:
                raise ValueError, _("This record does not exits")
        else:
            raise ValueError, utils.mapping(_("Path must be a not empty "\
                  "tuple: $1"), (str(path),))

    def getAmount(self, path):
        """def getAmount(self,path)
        
        path: record path
        Calculate the record amount
        """
        if len(path) == 1:
            # root: amount is the root price
            _root = self.getRecord(self.getRoot())
            _amount = _root.getPrice(self.__title_index)
            return _amount
        else:
            _parent_code = self.getCode(path[:-1])
            _parent_record = self.getRecord(_parent_code)
            _child_number = path[-1]
            
            _decomposition = _parent_record.children[_child_number]
            _factor = _decomposition.budgetMeasures[0].factor
            _yield = _decomposition.budgetMeasures[0].yield_
            _child_code = _decomposition.code
            _child_record = self.getRecord(_child_code)
            _price = _child_record.getPrice(self.getActiveTitle())
            _DR = self.getDecimals().getDR(_parent_record.recordType)
            _total_yield = round(_factor * _yield, _DR)
            _DI = self.getDecimals().getDI(_parent_record.recordType)
            _amount = round(_total_yield * _price, _DI)
            return _amount

    def getStrAmount(self, path):
        """def getStrAmount(self, path)
        
        path: record path
        Calculate the string record amount
        """
        if len(path) == 1: #root
            _root = self.getRecord(self.getRoot())
            _amount = self.getStrPriceFromRecord(self.__title_index, _root)
            return _amount
        else:
            _parent_code = self.getCode(path[:-1])
            _parent_record = self.getRecord(_parent_code)
            _amount = self.getAmount(path)
            _DI = self.getDecimals().getDI(_parent_record.recordType)
            _amount = ("%." + str(_DI) + "f") % _amount
            return _amount

    def setSheetSection(self,sheet_code,sheet_title):
        if not isinstance(sheet_code, str):
            raise ValueError, _("The sheet code must be a string")
        if not isinstance(sheet_title, str):
            raise ValueError, _("The sheet title must be a string")
        self.__sheet_sections[sheet_code] = sheet_title
    def hasSheetSection(self, section):
        return section in self.__sheet_sections
    def getSheetSection(self, section):
        return self.__sheet_sections[section]
    def setSheetSections(self,dictionary): 
        if not isinstance(dictionary, dict):
            raise ValueError, _("The sheet sections must be a dictionary")
        for sheet_code in dictionary.keys():
            self.setSheetSection(sheet_code, dictionary[sheet_code])
    def setSheetField(self, field_code, field_title):
        if not isinstance(field_code, str):
            raise ValueError, _("The field code must be a string")
        if not isinstance(field_title, str):
            raise ValueError, _("The field title must be a string")
        self.__sheet_fields[field_code] = field_title
    def hasSheetField(self, field):
        return field in self.__sheet_fields
    def getSheetField(self, field):
        return self.__sheet_fields[field]
    def setSheetFields(self, field_dict):
        if not isinstance(field_dict, dict):
            raise ValueError, _("The sheet field must be a dictionary")
        for field_code in field_dict.keys():
            self.setSheetField( field_code, field_dict[field_code])
    def setSheetParagraph(self, paragraph_code, paragraph_text):
        if not isinstance(paragraph_code, str):
            raise ValueError, _("The paragraph code must be a string")
        if not isinstance(paragraph_text, str):
            raise ValueError, _("The paragraph text must be a string")
        self.__sheet_paragraphs[paragraph_code] = paragraph_text
    def hasSheetParagraph(self, paragraph):
        return paragraph in self.__sheet_paragraphs
    def getSheetParagraph(self, paragraph):
        return self.__sheet_paragraphs[paragraph]
    def setSheetParagraphs(self, paragraph_dict):
        if not isinstance(paragraph_dict, dict):
            raise ValueError, _("The paragraph dict must be a dictionary")
        for paragraph_code in paragraph_dict.keys():
            self.setSheetParagraph( paragraph_code, paragraph_dict[paragraph_code])
    def setSheetRecord(self, record_code, field, section_dict):
        if not isinstance(record_code, str):
            raise ValueError, _("The record_code code must be a string")
        if not isinstance(field, str):
            raise ValueError, _("The field must be a string")
        if not isinstance(section_dict, dict):
            raise ValueError, _("The section dict must be a dictionary")
        #-#
        # TODO: Add a empty record?
        if not self.hasRecord(record_code):
            print utils.mapping(_("Error: The budget do not have this record "\
                "code and can not be added the sheet text in the field $1. "\
                "Record Code: $2"), ( field, record_code))
            return
        #-#
        if not self.hasSheetField(field):
            self.setSheetField(field, "")
        for section, paragraph in section_dict.iteritems():
            if not self.hasSheetParagraph(paragraph):
                self.setSheetParagraph(paragraph,"")
            if not self.hasSheetSection(section):
                self.setSheetSection(section, "")
            _sheet = self.getRecord(record_code).getSheet()
            _sheet.addSection(field, section, paragraph)
    def addFile(self, record_code, filepath, type_, description):
        if not isinstance(record_code, str):
            raise ValueError, _("The record_code code must be a string")
        if not isinstance(filepath, str):
            raise ValueError, _("The filename must be a string")
        #-#
        # TODO: Add a empty record?
        if not self.hasRecord(record_code):
            print utils.mapping(_("Error: The budget do not have the record "\
                "code $1 and can not be added the file: $2"),
                (record_code, filepath))
            return
        #-#
        _record = self.getRecord(record_code)
        _record.addFile(filepath, type_, description)
    def setCompany(self, company_code, sumamary, name, offices,
                   cif, web, email):
        if not isinstance(company_code, str):
            raise ValueError, _("The company code must be a string")
        if not isinstance(sumamary, str):
            raise ValueError, _("The summary must be a string")
        if not isinstance(name, str):
            raise ValueError, _("The name must be a string")
        if not isinstance(offices, list):
            raise ValueError, _("The name must be a list")
        _offices = []
        for _office in offices:
            if not isinstance(_office, list):
                raise ValueError, _("The office must be a list")
            if not len(_office) == 10:
                raise ValueError, _("The office must be a 10 items list")
            for _item in _office[:7] + _office[9:10]:
                if not isinstance(_item, str):
                    raise ValueError, _("This office item must be a "\
                                        "string")
            for _item in _office[7:8]:
                if not isinstance(_item, list):
                    raise ValueError, _("This office item must be a "\
                                        "list")
            _offices.append(Office(_office[0],
                                  _office[1],
                                  _office[2],
                                  _office[3],
                                  _office[4],
                                  _office[5],
                                  _office[6],
                                  _office[7],
                                  _office[8],
                                  _office[9]))
        if not isinstance(cif, str):
            raise ValueError, _("The name must be a string")
        if not isinstance(web, str):
            raise ValueError, _("The web must be a string")
        if not isinstance(email, str):
            raise ValueError, _("The email must be a string")
        
        self.__companys[company_code] = Company(company_code, sumamary, name,
                                                _offices, cif, web, email)
    def getCompany(self, company_code):
        return self.__companys[company_code]
    def getCompanyKeys(self):
        return self.__companys.keys()
    def addTecInfo(self, ti_code, text, unit):
        if not isinstance(ti_code, str):
            raise ValueError, _("The tecnical info code must be a string")
        if not isinstance(text, str):
            raise ValueError, _("The tecnical info description must be a "\
                                "string")
        if not isinstance(unit, str):
            raise ValueError, _("The tecnical info unit must be a string")
        self.__tec_info[ti_code] = [text, unit]
    def hasTecInfo(self, ti_code):
        return ti_code in self.__tec_info
    def getTecInfo(self, ti_code):
        return self.__tec_info[ti_code]
    def setTecnicalInformation(self, record_code, ti_dict):
        """setTecnicalInformation(record_code, ti_dict)
        
        Sets the tecnical information to a record
        record_code: the record code
        ti_dict: {ti_code : ti_value}
        """
        # TODO: setTecnicalInformation
        pass
    def changeCode(self, record_code, new_record_code):
        """changeCode(self, record_code, new_record_code):
        
        Change the record code for a new recor code.
        """
        if self.hasRecord(record_code) and not self.hasRecord(new_record_code):
            _record = self.__records[code]
            _record.code = new_record_code
            _parents = _record.parents
            for _parent in _parents:
                _decomposition_list = self.__records[_parent].children
                for _decomposition in _decomposition_list:
                    if _decomposition.code == record_code:
                        _decomposition.code = new_record_code
                        break
            _children = self.getchildren(record_code)
            for _child in _children:
                _parents_list = self.__records[_child].parents
                for index in range(len(_parents_list)):
                    if _parents_list[index] == record_code:
                        _parents_list[index] = new_record_code
                        break
            self.__records[new_record_code] = _record
            del self.__records[record_code]
            # TODO: attachment files

    def addLabel(self, record_code, label):
        """addLabel(self, record_code, label)
        
        Add a label to a record
        """
        if not isinstance(label,str):
            raise ValueError, _("The label must be a string")
        if self.hasRecord(record_code):
            _record = self.__records[record_code]
            _record.addLabel(label)
            if not label in self.__labels:
                self.__labels[label] = [record_code]
            else:
                _codes = self.__labels[label]
                if not record_code in _codes:
                    _codes.append(record_code)
    def setParametricSelectComment(self, record_code, comment):
        """setParametricSelectComment(self, record_code, comment)
        
        Sets Paramtric Record Select Comment
        """
        if not isinstance(record_code, str):
            raise ValueError, _("The record_code code must be a string")
        if not isinstance(comment, str):
            raise ValueError, _("The parametric select comment must be a "\
                                "string")
        if not self.hasRecord(record_code):
            print utils.mapping(_("Error: The budget do not have the record "\
                "code $1 and can not be added the Parametric select comment: "\
                "$2"),
                (record_code, comment))
            return
        _record = self.getRecord(record_code)
        if not isinstance(_record, ParametricRecord):
            print utils.mapping(_("Error: The Record $1 is not a "\
                "Parametric Record and can not have Parametric comment"),
                (record_code,))
        else:
            _record.select_comment = comment

    def setParametricSummary(self, record_code, summary):
        """setParametricSummary(self, record_code, summary)
        
        Sets parametric record summary
        """
        if not isinstance(record_code, str):
            raise ValueError, _("The record_code code must be a string")
        if not isinstance(summary, str):
            raise ValueError, _("The summary record must be a string")
        if not self.hasRecord(record_code):
            print utils.mapping(_("Error: The budget do not have the record "\
                "code $1 and can not be seted the summary: $2"),
                (record_code, summary))
            return
        _record = self.getRecord(record_code)
        if not isinstance(_record, ParametricRecord):
            print utils.mapping(_("Error: The Record $1 is not a "\
                "Parametric Record and can not have Parametric summary"),
                (record_code,))
        else:
            self.getRecord(record_code).parametric_summary = summary

    def setParametricText(self, record_code, text):
        """setParametricText(self, record_code, text)
        
        Sets parametric record text
        """
        if not isinstance(record_code, str):
            raise ValueError, _("The record_code code must be a string")
        if not isinstance(text, str):
            raise ValueError, _("The text record must be a string")
        if not self.hasRecord(record_code):
            print utils.mapping(_("Error: The budget do not have the record "\
                "code $1 and can not be seted the text: $2"),
                (record_code, text))
            return
        _record = self.getRecord(record_code)
        if not isinstance(_record, ParametricRecord):
            print utils.mapping(_("Error: The Record $1 is not a "\
                "Parametric Record and can not have Parametric text"),
                (record_code,))
        else:
            self.getRecord(record_code).parametric_text = text

class Office(object):
    """base.Office:
    
    Description:
        Office of a company
    Constructor:
        base.Office(type, subname, address, postal_code, town, province,
                         country, phone, fax, contact_person)
    Ancestry:
    +-- object
      +-- Office
    Atributes:
        "officeType" : type of Office
                       are defined:
                        "C"  Central.
                        "D"  Local Office.
                        "R"  performer.
        "subname" : name of Office or Performer
        "address" :
        "postal_code" :
        "town" :
        "province" :
        "country" :
        "phone" : list of phone numbers
        "fax" : list of fax numbers
        "contact_person" : name of contact person
        "values":
    Methods:
        __getstate__(self)
        __setstate__(self, tuple)
        __init__(self, measure, lines, label)
        {get/set}OfficeType
        {get/set}Subname
        {get/set}Address
        {get/set}PostalCode
        {get/set}Town
        {get/set}Province
        {get/set}Country
        {get/set}Phone
        {get/set}Fax
        {get/set}ContactPerson
        getValues
    """
    __slots__ = ["_Office__officeType",
                 "_Office__subname",
                 "_Office__address",
                 "_Office__postal_code",
                 "_Office__town",
                 "_Office__province",
                 "_Office__country",
                 "_Office__phone",
                 "_Office__fax",
                 "_Office__contact_person",
                 ]
    def __getstate__ (self):
        return ( self.__officeType,
                 self.__subname,
                 self.__address,
                 self.__postal_code,
                 self.__town,
                 self.__province,
                 self.__country,
                 self.__phone,
                 self.__fax,
                 self.__contact_person)
    def __setstate__(self,tuple):
        self.__officeType = tuple[0]
        self.__subname = tuple[1]
        self.__address = tuple[2]
        self.__postal_code = tuple[3]
        self.__town = tuple[4]
        self.__province = tuple[5]
        self.__country = tuple[6]
        self.__phone = tuple[7]
        self.__fax = tuple[8]
        self.__contact_person = tuple[9]

    def __init__(self, type_, subname, address, postal_code, town, province,
                 country, phone, fax, contact_person):
        self.officeType = type_
        self.subname = subname
        self.address = address
        self.postal_code = postal_code
        self.town = town
        self.province = province
        self.country = country
        self.phone = phone
        self.fax = fax
        self.contact_person = contact_person
    def getOfficeType(self):
        return self.__officeType
    def setOfficeType(self, type_):
        self.__officeType = type_
    def getSubname(self):
        return self.__subname
    def setSubname(self, subname):
        self.__subname = subname
    def getAddress(self):
        return self.__address
    def setAddress(self, address):
        self.__address = address
    def getPostalCode(self):
        return self.__postal_code
    def setPostalCode(self, postal_code):
        self.__postal_code = postal_code
    def getTown(self):
        return self.__town
    def setTown(self, town):
        self.__town = town
    def getProvince(self):
        return self.__province
    def setProvince(self, province):
        self.__province = province
    def getCountry(self):
        return self.__country
    def setCountry(self, country):
        self.__country = country
    def getPhone(self):
        return self.__phone
    def setPhone(self, phone):
        self.__phone = phone
    def getFax(self):
        return self.__fax
    def setFax(self, fax):
        self.__fax = fax
    def getContactPerson(self):
        return self.__contact_person
    def setContactPerson(self, contact_person):
        self.__contact_person = contact_person
    def getValues(self):
        return {"officeType": self.officeType,
                "subname": self.subname,
                "address": self.address,
                "postal code": self.postal_code,
                "town": self.town,
                "province": self.province,
                "country": self.country,
                "phone": self.phone,
                "fax": self.fax,
                "contact person": self.contact_person,
               }
    officeType = property(getOfficeType, setOfficeType, None,
    """Type of office
    """)
    subname = property(getSubname, setSubname, None,
    """Name of office
    """)
    address = property(getAddress, setAddress, None,
    """Adress
    """)
    postal_code = property(getPostalCode, setPostalCode, None,
    """Postal code
    """)
    town = property(getTown, setTown, None,
    """Town
    """)
    province = property(getProvince, setProvince, None,
    """Province
    """)
    country = property(getCountry, setCountry, None,
    """Country
    """)
    phone = property(getPhone, setPhone, None,
    """Phone numbers
    """)
    fax = property(getFax, setFax, None,
    """Fax numbers
    """)
    contact_person = property(getContactPerson, setContactPerson, None,
    """Contact Person
    """)
    values = property(getValues, None, None,
    """Dictionary with comapany values
    """)

class Company(object):
    """base.Company:
    
    Description:
        Company object
        __slots__ attribute, __getstate__ and __setstate__ method are defined
        to use less ram memory.
    Constructor:
        base.Company(code, summary, name, offices, cif, web, email)
    Ancestry:
    +-- object
      +-- Company
    Atributes:
        "code": code to indentifie the company in the buget
        "summary": short name
        "name": long name
        "offices": List of Offices
        "cif": CIF
        "web": web page
        "email": email
        "values": 
    Methods:
        __getstate__(self)
        __setstate__(self, tuple)
        __init__(self, measure, lines, label)
        {get/set}Code
        {get/set}Summary
        {get/set}Name
        {get/set}Offices
        {get/set}Cif
        {get/set}Web
        {get/set}Email
        getValues
    """
    __slots__ = ["_Company__code",
                 "_Company__summary",
                 "_Company__name",
                 "_Company__offices",
                 "_Company__cif",
                 "_Company__web",
                 "_Company__email",
                 ]
    def __getstate__ (self):
        return ( self.__code,
                 self.__summary,
                 self.__name,
                 self.__offices,
                 self.__cif,
                 self.__web,
                 self.__email)
    def __setstate__(self,tuple):
        self.__code = tuple[0]
        self.__summary = tuple[1]
        self.__name = tuple[2]
        self.__offices = tuple[3]
        self.__cif = tuple[4]
        self.__web = tuple[5]
        self.__email = tuple[6]

    def __init__(self, code, summary, name, offices, cif, web, email):
        self.code = code
        self.summary = summary
        self.name = name
        self.offices = offices
        self.cif = cif
        self.web = web
        self.email = email
    def getCode(self):
        return self.__code
    def setCode(self, code):
        self.__code = code
    def getSummary(self):
        return self.__summary
    def setSummary(self, summary):
        self.__summary = summary
    def getName(self):
        return self.__name
    def setName(self, name):
        self.__name = name
    def getOffices(self):
        return self.__offices
    def setOffices(self, offices):
        self.__offices = offices
    def getCif(self):
        return self.__cif
    def setCif(self, cif):
        self.__cif = cif
    def getWeb(self):
        return self.__web
    def setWeb(self, web):
        self.__web = web
    def getEmail(self):
        return self.__email
    def setEmail(self, email):
        self.__email = email
    def getValues(self):
        return {"code": self.code,
                "summary": self.summary,
                "name": self.name,
                "cif": self.cif,
                "web": self.web,
                "email": self.email}
    code = property(getCode, setCode, None,
    """Company code 
    """)
    summary = property(getSummary, setSummary, None,
    """Company summary
    """)
    name = property(getName, setName, None,
    """Company name
    """)
    offices = property(getOffices, setOffices, None,
    """List of Offices
    """)
    cif = property(getCif, setCif, None,
    """CIF
    """)
    web = property(getWeb, setWeb, None,
    """Web page
    """)
    email = property(getEmail, setEmail, None,
    """Email
    """)
    values = property(getValues, None, None,
    """Dictionary with comapany values
    """)

class File(object):
    """base.Company:
    
    Description:
        File object
    Constructor:
        base.File(name, type_, description)
    Ancestry:
    +-- object
      +-- File
    Atributes:
        "name": name
        "fileType": type of file
        "description": description file
    Methods:
        __getstate__(self)
        __setstate__(self, tuple)
        __init__(self, path,type_, description)
        {get/set}Name
        {get/set}FileType
        {get/set}Description
        getValues
    """
    __slots__ = ["_File__name",
                 "_File__fileType",
                 "_File__description",

                 ]
    def __getstate__ (self):
        return (self.__name,
                self.__description,
                self.__fileType,
               )
    def __setstate__(self,tuple):
        self.__name = tuple[0]
        self.__fileType = tuple[1]
        self.__description = tuple[2]
    def __init__(self, name, type_, description):
        self.name = name
        self.fileType = type_
        self.description = description
    def getName(self):
        return self.__name
    def setName(self, name):
        self.__name = name
    def getFileType(self):
        return self.__fileType
    def setFileType(self, type_):
        self.__fileType = type_
    def getDescription(self):
        return self.__description
    def setDescription(self, description):
        self.__description = description
    def getValues(self):
        return {"name": self.name,
                "fileType": self.fileType,
                "description": self.description,
               }
    name = property(getName, setName, None,
    """File name
    """)
    fileType = property(getFileType, setFileType, None,
    """FileType
    """)
    description = property(getDescription, setDescription, None,
    """File description
    """)
    values = property(getValues, None, None,
    """Dictionary with file values
    """)

class RecordType(object):
    """base.RecordType:
    
    Description:
        Record Type object
        "hierarchy":
           -1 -> temporarily unfixed
            0 -> root
            1 -> Chapter/Subchapter
            2 -> Other
        "type" and "subtype":
            0 Without classifying
               EA  Auxiliary element
               EU  Unitary element
               EC  Complex element
               EF  Functional element
               OB  Construction site
               PA  Cost overrun
               PU  Unitary budget
            1 Labourforce 
               H   Labourforce
            2 Machinery and auxiliary equipment
               Q   Machinery
               %   Auxiliary equipment
            3 Building materials
               MC  Cement
               MCr Ceramic
               MM  Wood
               MS  Iron and steel
               ME  Energy
               MCu Copper
               MAl Aluminium
               ML  Bonding agents
               M   Others materials
          Hierarchy           type  subtype
            0->root         -> 0 -> None,OB
            1->[sub]chapter -> 0 -> None,PU
            2->Other        -> 0 -> None,EA,EU,EC,EF,PA
                               1 -> None,H
                               2 -> None,Q,%
                               3 -> None,MC,MCr,MM,MS,ME,MCu,Mal,ML,M
    Constructor:
        base.File(hierarchy,type_,subtype)
    Ancestry:
    +-- object
      +-- RecordType
    Atributes:
        "hierarchy": hierarchy
        "type": type
        "subtype": subtype
    Methods:
        __getstate__(self)
        __setstate__(self, tuple)
        __init__(self, hierarchy, type, subtype)
        {get/set}Hierarchy
        {get/set}Type
        {get/set}Subtype
    """
    __slots__ = ["_RecordType__hierarchy",
                 "_RecordType__type",
                 "_RecordType__subtype",
                 ]
    def __getstate__ (self):
        return (self.__hierarchy,
                self.__type,
                self.__subtype,
               )
    def __setstate__(self,tuple):
        self.__hierarchy = tuple[0]
        self.__type = tuple[1]
        self.__subtype = tuple[2]
    def __init__(self, hierarchy, type_, subtype):
        self.hierarchy = hierarchy
        self.type = type_
        self.subtype = subtype
    def getHierarchy(self):
        return self.__hierarchy
    def setHierarchy(self, hierarchy):
        if not hierarchy in [-1, 0 , 1 ,2, ""]:
            raise ValueError, utils.mapping(_("Invalid Hierarchy ($1) "\
                  "The hierarchy must be -1, 0, 1, 2"), (str(hierarchy),))
        elif hierarchy == "":
            print "Hierarchy temporarily set to an empty string"
        #TODO Check empty Hierarchy in Generic.fiebdc.Read._testBudget
        self.__hierarchy = hierarchy
    def getType(self):
        return self.__type
    def setType(self, type_):
        if not type_ in  ["", 0, 1, 2, 3] :
            raise ValueError, utils.mapping(_("Invalid type ($1),"\
                  "the type must be (empty string,0,1,2,3)"),(str(type_)),)
        self.__type = type_
    def getSubtype(self):
        return self.__subtype
    def setSubtype(self, subtype):
        if not subtype in ["", "OB", "PU", "EA", "EU", "EC", "EF", "PA", "H",
                           "Q", "%", "MC", "MCr", "MM", "MS", "ME", "MCu",
                           "Mal","ML","M"]:
            raise ValueError, utils.mapping(_("Invalid subtype ($1), The "\
                  "subtype must one in (empty string, EA, "\
                  "EU, EC, EF, OB, PA, PU, H, Q, %, MC, MCr, "\
                  "MM, MS, ME, MCu, MAl, ML, M)"), (str(subtype),))
        self.__subtype = subtype
    hierarchy = property(getHierarchy, setHierarchy, None,
    """Record Hierarchy
           -1 -> temporarily unfixed
            0 -> root
            1 -> Chapter/Subchapter
            2 -> Other
    """)
    type = property(getType, setType, None,
    """Record Type
            0 Without classifying
            1 Labourforce 
            2 Machinery and auxiliary equipment
            3 Building materials
    """)
    subtype = property(getSubtype, setSubtype, None,
    """Record Subtype
            None
            EA  Auxiliary element
            EU  Unitary element
            EC  Complex element
            EF  Functional element
            OB  Construction site
            PA  Cost overrun
            PU  Unitary budget
            H   Labourforce
            Q   Machinery
            %   Auxiliary equipment
            MC  Cement
            MCr Ceramic
            MM  Wood
            MS  Iron and steel
            ME  Energy
            MCu Copper
            MAl Aluminium
            ML  Bonding agents
            M   Others materials
    """)
