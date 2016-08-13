# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from datetime import datetime
import os

# Create your models here.

from gentities.models import Gentity, Guser


# Function to save files with a name that keeps consistency
def update_file(instance, filename):
    instance.file_name = filename
    ext = filename.partition('.')[2]
    now = datetime.now()
    new_filename = 'budget_file_%s.%s' % (now.strftime('%Y%m%d%H%M%f'), ext)
    return os.path.join("budgets/", new_filename)


class Budget_file(models.Model):
    file = models.FileField("File related to the budget", upload_to=update_file, blank=True)
    file_name = models.CharField('File name', max_length=200, blank=True, null=True)
    content_type = models.CharField("Type of file", max_length=200, blank=True, null=True)
    description = models.CharField("Small description", max_length=300, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % (self.file)


class Gbudget(models.Model):
    gentity = models.ForeignKey(Gentity, blank=True, null=True)
    title = models.CharField('Title for the budget', blank=True, null=True, max_length=150)
    removed = models.BooleanField('The budget is removed?', default=False)
    administrator = models.ForeignKey(Guser, blank=True, null=True)
    gusers_edit = models.ManyToManyField(Guser, blank=True, related_name='can_edit_gbudget')
    initial_bc3 = models.ForeignKey(Budget_file, blank=True, null=True, related_name='initial')
    final_bc3 = models.ForeignKey(Budget_file, blank=True, null=True, related_name='final')
    created = models.DateTimeField('Created', auto_now_add=True)
    modified = models.DateTimeField('Last modification', auto_now=True)

    def __unicode__(self):
        return u'%s - %s (%s)' % (self.gentity, self.title, self.created)


class Vrecord(models.Model):
    """
    ~V | [ PROPIEDAD_ARCHIVO ] | VERSION_FORMATO [ \ DDMMAAAA ] | [ PROGRAMA_EMISION ] |
    [ CABECERA ] \ { ROTULO_IDENTIFICACION \ } | [ JUEGO_CARACTERES ] | [ COMENTARIO ] | [ TIPO INFORMACION ] |
    [ NUMERO CERTIFICACION  ] | [  FECHA CERTIFICACION ] | [ URL_BASE ] |
    """
    CHARSET = (('cp1252', 'ANSI'), ('850', '850'), ('cp437', '437'))
    TYPES = (
        (1, 'Base de datos'), (2, 'Presupuesto'), (3, 'Certificación (a origen)'),
        (4, u'Actualización de base de datos'))
    gbudget = models.ForeignKey(Gbudget)
    owner = models.CharField('Data base editor', blank=True, null=True, max_length=150)
    version = models.CharField('Format file version', default='FIEBDC-3/2016', max_length=100)
    date = models.DateField('Date', blank=True, null=True)
    emisor = models.CharField('Computer program or company that created the BC3 file', blank=True, null=True,
                              max_length=150)
    header = models.CharField('General title of ROTULOS_IDENTIFICACION', blank=True, null=True, max_length=200)
    char_set = models.CharField('Char set', choices=CHARSET, max_length=10, default='850')
    comment = models.CharField('Small description about this BC3', blank=True, null=True, max_length=300)
    type = models.IntegerField('Type of information', choices=TYPES, blank=True, null=True)
    # NÚMERO CERTIFICACIÓN: Valor numérico indicando el orden de la certificación (1, 2, 3,…)
    # Solo tiene sentido cuando el tipo de información es Certificación.
    certification_number = models.IntegerField('Order of the certification', blank=True, null=True)
    certification_date = models.DateField('Date of the certification', blank=True, null=True)
    url = models.URLField('Url where documents and images can be found', blank=True, null=True)

    class Meta:
        ordering = ['gbudget']

    def __unicode__(self):
        return u'%s (%s)' % (self.gbudget, self.date)


class Vrecord_label(models.Model):
    """
    ROTULO_IDENTIFICACION: Asigna secuencialmente títulos a los valores definidos en el campo PRECIO del registro ~C, y
    los conjuntos de campos de números de decimales del registro ~K, que tal como se indica en su ESPECIFICACION, puede
    representar distintas épocas, ámbitos geográficos, etc., estableciéndose una relación biunívoca entre ambos. Véanse
    los anexos 5 (Ámbitos territoriales) y 6 (Divisas).

    En el caso de que en el registro ~V existan más campos ROTULO_IDENTIFICACION que campos PRECIO en el registro ~C o
    que conjuntos de campos de decimales en el registro ~K, se entenderá que el PRECIO y los conjuntos de campos de
    decimales de dicho resto serán iguales al último definido.
    """
    vrecord = models.ForeignKey(Vrecord)
    title = models.CharField('Sequential title', max_length=200)

    class Meta:
        ordering = ['vrecord', 'id']

    def __unicode__(self):
        return u'%s (%s)' % (self.vrecord, self.title)


#############################################################

class Krecord(models.Model):
    """
    ~K | { DN \ DD \ DS \ DR \ DI \ DP \ DC \ DM \ DIVISA \ } | CI \ GG \ BI \ BAJA \ IVA |
    { DRC \ DC \ \ DFS \ DRS \ \ DUO \ DI \ DES \ DN \ DD \ DS \ DSP \ DEC \ DIVISA \ } | [ n ] |
    The first field only is there because compatibility. We will not read it.
    """
    gbudget = models.ForeignKey(Gbudget)
    ci = models.FloatField('Percentage CI', default=0)
    gg = models.FloatField('Percentage GG', default=13)
    bi = models.FloatField('Percentage BI', default=6)
    baja = models.FloatField('Percentage BAJA', default=1)
    iva = models.FloatField('Percentage IVA', default=21)

    class Meta:
        ordering = ['gbudget']

    def __unicode__(self):
        return u'%s (CI %s, GG %s, BI %s, BAJA %s, IVA %s)' % (
            self.gbudget, self.ci, self.gg, self.bi, self.baja, self.iva)


class Krecord_scope(models.Model):
    krecord = models.ForeignKey(Krecord, related_name='additional')
    vrecord_label = models.ForeignKey(Vrecord_label, related_name='krecord_scope')
    # Number of decimal places of the ...
    drc = models.IntegerField('... efficiency (or measure) in a chapter or subchapter break down.', default=3)
    dc = models.IntegerField('... price of a chapter or subchapter.', default=2)
    dfs = models.IntegerField('... factores de rendimiento de unidades de obra y de elementos compuestos.', default=3)
    drs = models.IntegerField('... rendimientos de las unidades de obra y de los elementos compuestos.', default=3)
    duo = models.IntegerField('... price of a unit of work.', default=2)
    di = models.IntegerField('... importes resultantes de multiplicar los rendimientos totales de los ...', default=2)
    des = models.IntegerField('... price of the simple elements.', default=2)
    dn = models.IntegerField('... field "equal-size parts" in the measure lines.', default=2)
    dd = models.IntegerField('... three dimensions in the measure lines.', default=2)
    ds = models.IntegerField('... total sum of a measure.', default=2)
    dsp = models.IntegerField('... línea de subtotal de mediciones.', default=2)
    dec = models.IntegerField('... importe de los elementos compuestos.', default=2)
    divisa = models.CharField('... monetary unit.', default='Euro', max_length=10)

    class Meta:
        ordering = ['krecord__gbudget']

    def __unicode__(self):
        return u'%s (DRC %s, DC %s, DFS %s, DRS %s, DUO %s, DI %s, DES %s, DN %s, ...)' % (
            self.krecord, self.drc, self.dc, self.dfs, self.drs, self.duo, self.di, self.des, self.dn)


#############################################################

class Crecord(models.Model):
    """
    ~C | CODIGO { \ CODIGO } | [ UNIDAD ] | [ RESUMEN ] | { PRECIO \ } | { FECHA \ } | [ TIPO ] |
    """
    TYPES = ((0, 'Sin clasificar'), (1, 'Mano de obra'), (2, 'Maquinaria y medios auxiliares'), (3, 'Materiales'),
             (4, 'Componentes adicionales de residuo'), (5, 'Clasificación de residuo'))
    HIERARCHY = ((0, 'Root'), (1, 'Chapter'), (2, 'Normal concept'))
    gbudget = models.ForeignKey(Gbudget)
    code = models.CharField('Code of the described concept', max_length=22)
    hierarchy = models.IntegerField('Hierarchy: root, chapter or concept', choices=HIERARCHY, default=2)
    unit = models.CharField('Unit of measurement', blank=True, null=True, max_length=7)
    summary = models.CharField('Summary of the concept', blank=True, null=True, max_length=300)
    type = models.CharField('Type of concept', blank=True, null=True, max_length=10)
    # ~T | CODIGO_CONCEPTO |  TEXTO_DESCRIPTIVO  |
    text = models.TextField('Concept description', blank=True, null=True)

    def __unicode__(self):
        if self.summary:
            if len(self.summary) > 50:
                s = '%s...' % self.summary[:50]
            else:
                s = '%s' % self.summary
        else:
            s = 'No summary'
        return u'Budget: %s, %s - (%s) %s' % (self.gbudget.id, self.code, self.get_hierarchy_display(), s)
        #
        # return '%s %s %s' % (self.gbudget.id, self.code, s)


class Crecord_alias(models.Model):
    crecord = models.ForeignKey(Crecord)
    code = models.CharField('Alias code for crecord.code', max_length=22)

    def __unicode__(self):
        return u'Budget: %s, Alias: %s -> Real code: %s' % (self.crecord.gbudget.id, self.code, self.crecord.code)


class Crecord_price(models.Model):
    crecord = models.ForeignKey(Crecord)
    vrecord_label = models.ForeignKey(Vrecord_label, related_name='crecord_price')
    price = models.FloatField('Price of the concept', blank=True, null=True)
    date = models.DateField('Date when the price was defined', blank=True, null=True)

    def __unicode__(self):
        return u'Budget: %s, %s -> %s (%s)' % (self.crecord.gbudget.id, self.crecord.code, self.price, self.date)


#############################################################

class Drecord(models.Model):
    """
    ~D | CODIGO_PADRE | < CODIGO_HIJO \ [ FACTOR ] \ [ RENDIMIENTO ] \ > |
    < CODIGO_HIJO \ [ FACTOR ] \ [ RENDIMIENTO ] \ {CODIGO_PORCENTAJE ; } \ > |
    """
    gbudget = models.ForeignKey(Gbudget)
    parent = models.ForeignKey(Crecord, related_name='parent_drecord')
    child = models.ForeignKey(Crecord, related_name='child_drecord')
    factor = models.FloatField('Eficiency factor', default=1.0)
    efficency = models.FloatField('Número de unidades, rendimiento o medición', default=1.0)

    def __unicode__(self):
        return u'Budget: %s, Parent: %s -> Child: %s (factor: %s, efficiency: %s)' % (
            self.gbudget.id, self.parent.code, self.child.code, self.factor, self.efficency)


class Drecord_percentage_code(models.Model):
    drecord = models.ForeignKey(Drecord)
    percentage_code = models.CharField('Percentage code', blank=True, null=True, max_length=15)

    # ~D|PP009|UOT002\1.000\0.180\UOP009\1.000\0.052\UOT004\1.000\0.120\UOL003\1.000\2.000\||
    # ~D|AUX001|MQ001\1\0.0800\|MQ001\1\0.0800\\|
    # ~D|UOB001|MTB001\1\1.0000\AUX008\1\0.1000\MO011\1\0.5000\%MA\1\0.0200\%CI\1\0.0600\|MTB001\1\1.0000\%MA;%CI;\AUX008\1\0.1000\%MA;%CI;\MO011\1\0.5000\%MA;%CI;\%MA\1\0.0200\%CI;\%CI\1\0.0600\\|
    def __unicode__(self):
        return u'Budget: %s, Parent: %s -> Child: %s (percentage: %s)' % (
            self.drecord.gbudget.id, self.drecord.parent.code, self.drecord.child.code, self.percentage_code)


#############################################################

class Rrecord(models.Model):
    """
    ~ R | CODIGO_PADRE | { TIPO_DESCOMPOSICION \ CODIGO_HIJO \ { PROPIEDAD \ VALOR \ [UM] \ } | } |
    """
    TYPES = ((0, 'Residuo de componente de colocación'), (1, 'Residuo de componente de demolición'),
             (2, 'Residuo de componente de excavación'), (3, 'Residuo de componente de embalaje'))
    gbudget = models.ForeignKey(Gbudget)
    parent = models.ForeignKey(Crecord, related_name='parent_rrecord')
    child = models.ForeignKey(Crecord, related_name='child_rrecord', blank=True, null=True)
    type = models.IntegerField('Tipo de residuo', blank=True, null=True)

    def __unicode__(self):
        c = self.child.code if self.child else 'No defined'
        t = self.type if self.type else 'No defined'
        return u'Budget: %s, Parent: %s -> Child: %s (type: %s)' % (self.gbudget.id, self.parent.code, c, t)


class Rrecord_property(models.Model):
    PROPERTIES = (('r', 'Rendimiento'), ('rp', 'Porcentaje total de residuo de colocación'))
    rrecord = models.ForeignKey(Rrecord)
    property = models.CharField('Característica del residuo', choices=PROPERTIES, max_length=4, default='r')
    value = models.CharField('Valor de la propiedad', blank=True, null=True, max_length=20)
    unit = models.CharField('Measurement unit', blank=True, null=True, max_length=20)

    def __unicode__(self):
        return u'Budget: %s, Parent: %s -> Child: %s (type: %s) / Property: %s, Value: %s, Units: %s' % (
            self.rrecord.gbudget.id, self.rrecord.parent.code, self.rrecord.child.code, self.rrecord.type,
            self.property, self.value, self.unit)


#############################################################

class Wrecord(models.Model):
    """
    ~W | < ABREV_AMBITO \ [ AMBITO ] \ > |
    """
    gbudget = models.ForeignKey(Gbudget)
    abbrev = models.CharField('Abbreviation of the geographical scope', blank=True, null=True, max_length=10)
    scope = models.CharField('Complete name of the geographical scope', blank=True, null=True, max_length=100)

    def __unicode__(self):
        return u'Budget: %s, Abbrev: %s -> Scope: %s' % (self.gbudget.id, self.abbrev, self.scope)


#############################################################

class Lrecord(models.Model):
    """
    ~L | | < CODIGO_SECCION_PLIEGO \ [ ROTULO_SECCION_PLIEGO ] \ > |
    ~L | CODIGO_CONCEPTO | { CODIGO_SECCION_PLIEGO \ TEXTO_SECCION_PLIEGO \ } |
       { CODIGO_SECCION_PLIEGO \ ARCHIVO_TEXTO_RTF \ } | { CODIGO_SECCION_PLIEGO \ ARCHIVO_TEXTO_HTM \ } |
    """
    gbudget = models.ForeignKey(Gbudget)
    section_code = models.CharField('Scope statement section code', blank=True, null=True, max_length=20)
    section_title = models.CharField('Scope statement section title', blank=True, null=True, max_length=100)

    def __unicode__(self):
        return u'Budget: %s, Code: %s -> Title: %s' % (self.gbudget.id, self.section_code, self.section_title)


class Lrecord_section(models.Model):
    lrecord = models.ForeignKey(Lrecord, related_name='lrecord')
    crecord = models.ForeignKey(Crecord, related_name='crecord')
    text = models.TextField('Text asigned to the Scope stament section by de concept', blank=True, null=True)
    rtf_file = models.ForeignKey(Budget_file, related_name="lrecord_rtf_file", blank=True)
    htm_file = models.ForeignKey(Budget_file, related_name="lrecord_htm_file", blank=True)

    def __unicode__(self):
        return u'%s, Concept: %s (%s ...)' % (self.lrecord, self.crecord.code, self.text[:30])


#############################################################
class Qrecord(models.Model):
    """
    ~Q | < CODIGO_CONCEPTO \ > | { CODIGO_SECCION_PLIEGO \ CODIGO_PARRAFO \ { ABREV_AMBITO ; } \ } |
    """
    crecord = models.ForeignKey(Crecord, related_name='qcrecord')
    lrecord = models.ForeignKey(Lrecord, related_name='lqrecord', blank=True, null=True)
    paragraph_code = models.CharField('Scope statement paragraph code', blank=True, null=True, max_length=20)
    abbrev = models.ManyToManyField(Wrecord, blank=True)


#############################################################

class Jrecord(models.Model):
    """
    ~J | CODIGO_PARRAFO | [ TEXTO_PARRAFO ] | | [ ARCHIVO_PARRAFO_RTF ] | [ ARCHIVO_PARRAFO_HTM ] |
    """
    qrecord = models.ForeignKey(Qrecord)
    paragraph_text = models.TextField('Text of the paragraph', blank=True, null=True)
    rtf_file = models.ForeignKey(Budget_file, related_name="jrecord_rtf_file", blank=True)
    htm_file = models.ForeignKey(Budget_file, related_name="jrecord_htm_file", blank=True)


#############################################################
class Grecord(models.Model):
    """
    ~G | CODIGO_CONCEPTO | < ARCHIVO_GRAFICO.EXT \ > | [URL_EXT] |
    """
    crecord = models.ForeignKey(Crecord)
    file = models.ForeignKey(Budget_file, related_name="grecord_file", blank=True)
    url = models.CharField("Relative url to file", blank=True, null=True, max_length=60)


#############################################################
class Erecord(models.Model):
    """
    ~E | CODIGO_ENTIDAD | [ RESUMEN ] | [ NOMBRE ] | { [ TIPO ] \ [ SUBNOMBRE ] \ [ DIRECCIÓN ] \ [ CP ] \
        [ LOCALIDAD ] \ [ PROVINCIA ] \ [ PAIS ] \ { TELEFONO ; } \ { FAX ; } \ { PERSONA_CONTACTO ; } \ } |
        [ CIF ] \ [ WEB ] \ [ EMAIL ] \ |
    """
    TYPES = (('C', 'Central'), ('D', 'Delegación'), ('R', 'Representante'))
    gbudget = models.ForeignKey(Gbudget)
    # CODIGO del SCc que define a la entidad (empresa, organismo, etc.):
    code = models.CharField('Company code', blank=True, null=True, max_length=50)
    summary = models.CharField('Nombre abreviado de la entidad', blank=True, null=True, max_length=20)
    name = models.CharField('Nombre completo de la entidad', blank=True, null=True, max_length=100)
    type = models.CharField('Tipo de entidad', choices=TYPES, max_length=4, default='C')
    subname = models.CharField('Nombre de la delegación o representante', blank=True, null=True, max_length=100)
    address = models.CharField('Dirección de la entidad', blank=True, null=True, max_length=100)
    cp = models.IntegerField('Postal code', blank=True, null=True)
    location = models.CharField('Localidad', blank=True, null=True, max_length=100)
    province = models.CharField('Provincia', blank=True, null=True, max_length=100)
    country = models.CharField('País', blank=True, null=True, max_length=100)
    tel = models.CharField('Tel', blank=True, null=True, max_length=15)
    fax = models.CharField('Fax', blank=True, null=True, max_length=15)
    contact = models.CharField('Contact', blank=True, null=True, max_length=50)
    cif = models.CharField('CIF', blank=True, null=True, max_length=15)
    web = models.CharField('Web', blank=True, null=True, max_length=50)
    email = models.CharField('E-mail', blank=True, null=True, max_length=50)


#############################################################
# class Orecord(models.Model):
#     """
#     ~O | CODIGO_RAIZ_BD # CODIGO_CONCEPTO | | < CODIGO_ARCHIVO \ CODIGO_ENTIDAD # CODIGO_CONCEPTO \ > |
#     """
#     root_code = models.CharField('Código raíz de la base de datos', max_length=50)
#     crecord = models.ForeignKey(Crecord)
#         models.CharField('Código del concepto en la anterior base de datos', max_length=50)


#############################################################
class Xrecord_ti(models.Model):
    """
    X record Technical Information
    ~X | | < CODIGO_IT \ DESCRIPCION_IT \ UM \ > |
    ~X | CODIGO_CONCEPTO | < CODIGO_IT \ VALOR_IT \ > |
    """
    # TYPES = (('ce', 'Coste energético (MJ)'), ('eCO2', 'Emisión de CO2 (kg)'), ('m', 'Masa del elemento (kg)'),
    #          ('ler', 'Código ler de la lista europea de residuos'), ('v', 'Volumen (m3)'))
    gbudget = models.ForeignKey(Gbudget)
    ti_code = models.CharField('Code of the technical information', max_length=36)
    description = models.TextField('Code of the technical information', blank=True, null=True)
    unit = models.CharField('Unit of measure', blank=True, null=True, max_length=20)

    def __unicode__(self):
        return u'Budget: %s, TI code: %s (%s)' % (self.gbudget.id, self.ti_code, self.unit)


class Xrecord(models.Model):
    """
    ~X | | < CODIGO_IT \ DESCRIPCION_IT \ UM \ > |
    ~X | CODIGO_CONCEPTO | < CODIGO_IT \ VALOR_IT \ > |
    """
    crecord = models.ForeignKey(Crecord, related_name='xcrecord')
    xrecord_ti = models.ForeignKey(Xrecord_ti)
    value = models.CharField('Value for the technical information given', max_length=26, blank=True, null=True)

    def __unicode__(self):
        return u'Budget: %s, %s -> %s -- Value: %s' % (
            self.crecord.gbudget.id, self.crecord.code, self.xrecord_ti.ti_code, self.value)


#############################################################

class Id_bim(models.Model):
    id_bim = models.CharField('BIM identifier', max_length=200)

    def __unicode__(self):
        return u'ID_BIM: %s' % (self.id_bim)


class Mrecord(models.Model):
    """
    ~M | [ CODIGO_PADRE \ ] CODIGO_HIJO | { POSICION \ } | MEDICION_TOTAL |
        { TIPO \ COMENTARIO { # ID_BIM } \ UNIDADES \ LONGITUD \ LATITUD \ ALTURA \ } | [ ETIQUETA ] |
    """
    parent = models.ForeignKey(Crecord, related_name='parent_mrecord', blank=True, null=True)
    child = models.ForeignKey(Crecord, related_name='child_mrecord')
    cpos = models.CharField('Chapter position', blank=True, null=True, max_length=30)
    spos = models.CharField('SubChapter position', blank=True, null=True, max_length=30)
    ipos = models.CharField('Budget item (partida) position', blank=True, null=True, max_length=30)
    # pos = models.CharField('Position', max_length=30, blank=True, null=True)
    m_total = models.FloatField('Total measurement. Equals efficiency of Drecord')
    label = models.CharField('Etiqueta', blank=True, null=True, max_length=30)

    def __unicode__(self):
        p = '%s -> ' % self.parent if self.parent else ''
        return u'Budget: %s, %s%s %s\%s\%s (%s)' % (self.child.gbudget.id, p, self.child.code, self.cpos, self.spos,
                                                    self.ipos, self.m_total)


class Mrecord_type(models.Model):
    """
    { TIPO \ COMENTARIO { # ID_BIM } \ UNIDADES \ LONGITUD \ LATITUD \ ALTURA \ }
    """
    TYPES = ((0, 'Empty'), (1, 'Subtotal parcial'), (2, 'Subtotal acumulado'), (3, 'Expresión'))
    mrecord = models.ForeignKey(Mrecord)
    type = models.IntegerField('Type', choices=TYPES, blank=True, null=True)
    comment = models.TextField('Comment or expression. Depending on TYPES', blank=True, null=True)
    id_bims = models.ManyToManyField(Id_bim, blank=True)
    units = models.FloatField('Number of units', blank=True, null=True)
    longitude = models.FloatField('Longitude', blank=True, null=True)
    latitude = models.FloatField('Latitude', blank=True, null=True)
    height = models.FloatField('Height', blank=True, null=True)

    def __unicode__(self):
        return u'%s, units: %s, lon: %s, lat: %s, height: %s, ' % (self.mrecord, self.units, self.longitude,
                                                                   self.latitude, self.height)


#############################################################
class Arecord(models.Model):
    """
    ~A | CODIGO_CONCEPTO | < CLAVE_TESAURO \ > |
    """
    crecord = models.ForeignKey(Crecord)
    key = models.CharField('Thesaurus key', max_length=50)

    def __unicode__(self):
        return u'Budget: %s, %s -> key: %s' % (self.crecord.gbudget.id, self.crecord, self.key)


#############################################################
# class Brecord(models.Model):
#     """
#     ~B | CODIGO_CONCEPTO | CODIGO_NUEVO |
#     """
#     crecord = models.ForeignKey(Crecord, related_name='bcrecord')
#     new_code = models.CharField('New code for concept', max_length=22)



#############################################################
class Frecord(models.Model):
    """
    ~F | CODIGO_CONCEPTO | { TIPO \  { ARCHIVO.EXT ; } \ [ DESCRIPCION_ARCHIVO ] \ } | [URL_EXT] |
    """
    crecord = models.ForeignKey(Crecord)
    url = models.URLField('Relative url', blank=True, null=True)

    def __unicode__(self):
        return u'Budget: %s, %s -> url: %s' % (self.crecord.gbudget.id, self.crecord, self.url)

class Frecord_files(models.Model):
    TYPES = ((0, 'Otros'), (1, 'Características técnicas y de fabricación'),
             (2, 'Manual de colocación, uso y mantenimiento'), (3, 'Certificado/s de elementos y sistemas'),
             (4, 'Normativa y bibliografía'), (5, 'Tarifa de precios'), (6, 'Condiciones de venta'),
             (7, 'Carta de colores'), (8, 'Ámbito de aplicación y criterios selección'),
             (9, 'Cálculo de elementos y sistemas'), (10, 'Presentación, datos generales, objetivos, etc. de empresa'),
             (11, 'Certificado/s de empresa'), (12, 'Obras realizadas'), (13, 'Imagen'))
    frecord = models.ForeignKey(Frecord)
    type = models.IntegerField('Type of file', choices=TYPES)
    files = models.ManyToManyField(Budget_file, related_name="frecord_file", blank=True)
    description = models.CharField('File description', blank=True, null=True, max_length=200)

    def __unicode__(self):
        return u'%s, %s -> %s' % (self.frecord, self.type, self.description)