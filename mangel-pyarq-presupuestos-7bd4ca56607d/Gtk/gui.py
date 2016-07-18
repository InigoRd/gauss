# -*- coding: utf-8 -*-
## File gui.py
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
##

"""Gui module

The MainWindow class contain the toplevel WINDOW,
this window have a notebook with a page for each budget.
Each budget or notebook page is showed by the Page class, this class contain
the main widget showed in a page notebook.
The main widget can show the budget information in several panes.
This panes are ordened in gtk.Paned represented for the class Paned which can
have 2 viewes represented for the View class or other gtk.Paned that have other
viewes or more gtk.Paned.
The view can have diferente type of widgets to show the budget information.
The DecompositionList class show the decompositon list information of a record
The Measure class show the measure information of a record
The Sheet class class show the sheet of condition information of a record

The views can send signal to the others.
All the viewes ordered in panes can be or not be connected to the others,
if there are connecteded to the others when the user change the active code in
one of the panes the active code change in the others.

"""
# TODO: Config file

# Standar Modules
import os
import time
import pygtk
pygtk.require('2.0')
import gtk
import gobject
import weakref

# pyArq-Presupuestos Modules
from Gtk import importFiebdc
from Generic import base
from Generic import fiebdc
#from Generic import durusdatabase
from Generic import utils
from Generic import globalVars
from Generic import openwith

# Load default icon
if os.path.exists(globalVars.getAppPath("ICON")):
    icon = gtk.gdk.pixbuf_new_from_file(globalVars.getAppPath("ICON"))
    gtk.window_set_default_icon_list(icon)
else:
    print utils.mapping(_("The icon file does not exist. '$1'"),
          (globalVars.getAppPath("ICON"),))

# Autodetect desktop
if globalVars.desktop["autodetect"]:
    openwith.autodetect_desktop()
    print utils.mapping(_("pyArq-Presupuestos running on $1"),
                        (globalVars.desktop["desktop"],))

# Add MenutoolButton to Uimanager
class MenuToolAction(gtk.Action):
       __gtype_name__ = "MenuToolAction"

gobject.type_register(MenuToolAction)
MenuToolAction.set_tool_item_type(gtk.MenuToolButton)


class MainWindow(object):
    """gui.MainWindow:
    
    Description:
        Creates and shows the main window.
        This is the interface base class.
    Constructor:
        gui.MainWindow()
    Ancestry:
    +-- object
      +-- MainWindow
    Atributes:
    Methods:
        changeHistorySignal
        changeActiveSignal
        appendEmptyPage
        updatePage
        closePage
    """
    # TODO:* Can choose open budget in new window
    # TODO:* Can choose show more than one notebook in the same window or
    # TODO:  can show basedata notebook in a side pane
    __ui = '''<ui>
    <menubar name="MenuBar">
      <menu action="File">
        <menuitem action="ImportFiebdc"/>
        <menuitem action="Close"/>
      </menu>
      <menu action="View">
      </menu>
      <menu action="Go">
        <menuitem action="GoPrevious"/>
        <menuitem action="GoPosterior"/>
        <menuitem action="GoUp"/>
        <menuitem action="GoToRoot"/>
      </menu>
    </menubar>
    <toolbar name="ToolBar">
      <toolitem action="ImportFiebdc"/>
      <toolitem action="Close"/>
      <separator name="sep1"/>
      <toolitem action="GoPrevMenu"/>
      <toolitem action="GoPostMenu"/>
      <toolitem action="GoUp"/>
      <toolitem action="GoToRoot"/>
    </toolbar>
    </ui>'''

    #<menu action="Test">
    #  <menuitem action="ImportFiebdcPriceDatabase"/>
    #  <menuitem action="OpenPriceDatabase"/>
    #</menu>

    def __init__(self):
        """__init__()
        
        Initialize the atributes self.__page_list without data.
        Creates the widgets "window" and "__notebook".
        
        self.__window: gtk.Window object
        self.__uimanager: gtk.UIManager object
        self.__page_list: List of pages ("Page" object)
        self.__notebook: Notebook widget ("gtk.Notebook" object)
        self.__general_action_group: "General" action group
        self.__navigation_action_group: "Navigation" action group
        """
        self.__page_list = []
        # Main window
        self.__window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.__window.set_default_size(771, 570)
        self.__window.set_title("Presupuestos")
        self.__window.set_border_width(0)
        self.__window.connect("destroy", self._destroy)
        self.__window.connect("delete_event", self._delete_event)
        # Vertical box
        _vbox1 = gtk.VBox(False, 0)
        self.__window.add(_vbox1)
        _vbox1.show()
        #Uimanager
        self.__uimanager = gtk.UIManager()
        _accelgroup = self.__uimanager.get_accel_group()
        self.__window.add_accel_group(_accelgroup)
        self.__general_action_group = gtk.ActionGroup("General")
        self.__general_action_group.add_actions(
            [("File", None, _("_File"), None),
             ("ImportFiebdc", gtk.STOCK_OPEN, _('_Import Fiebdc'), "",
                _('Import FIEBDC'), self._menuitemImportFiebdc),
             ("Close", gtk.STOCK_CLOSE, _("_Close"), None, _('Close'),
                self._menuitemClose),
             ("View", None, _("_View")),
             ("Go", None, _("_Go")),
             ("Test", None, _("_Test")),
             #('ImportFiebdcPriceDatabase', gtk.STOCK_OPEN,
             #   _("Import Fiebdc _price database"), "", _("Import database"),
             #   self._menuitemImportPriceDatabase ),
             #("OpenPriceDatabase", gtk.STOCK_OPEN, _('_Open price database'),
             #   "", _('Open Database'), self._menuitemOpenPriceDatabase),
            ])
        self.__navigation_action_group = gtk.ActionGroup("Navigation")
        self.__navigation_action_group.add_actions(
            [("Go", None, _("_Go")),
             ("GoPrevious", gtk.STOCK_GO_BACK, _("_Back"),"",
                _("Go to the previous visited item"),
                  self._menuitemGoPrevious),
             ("GoPosterior", gtk.STOCK_GO_FORWARD, _("_Forward"),"",
                _("Go to the next visited item"), self._menuitemGoPosterior),
             ("GoUp", gtk.STOCK_GO_UP, _("_Up Item"),"",
                _("Go up item"), self._menuitemGoUp),
             ("GoToRoot", gtk.STOCK_GOTO_TOP, _("_Root"),"",
                _("Go to root"), self._menuitemGoToRoot),
            ])
        self.__navigation_action_group.add_action(
            MenuToolAction("GoPrevMenu", None ,
                           _("Go to the previous visited item"),
                           gtk.STOCK_GO_BACK))
        self.__navigation_action_group.add_action(
             MenuToolAction("GoPostMenu", None ,
                           _("Go to the next visited item"),
                           gtk.STOCK_GO_FORWARD))
        self.__navigation_action_group.set_sensitive(False)
        self.__navigation_action_group.get_action("GoPostMenu").set_sensitive(
            False)
        self.__navigation_action_group.get_action("GoPrevMenu").set_sensitive(
            False)
        self.__uimanager.insert_action_group(self.__general_action_group, 0)
        self.__uimanager.insert_action_group(self.__navigation_action_group, 1)
        self.__uimanager.add_ui_from_string(self.__ui)
        _menu_bar = self.__uimanager.get_widget("/MenuBar")
        _vbox1.pack_start(_menu_bar, False, False, 0)
        _toolbar = self.__uimanager.get_widget("/ToolBar")
        _toolbar.get_settings().set_long_property("gtk-toolbar-icon-size",
            gtk.ICON_SIZE_SMALL_TOOLBAR, "pyArq-Presupuestos:toolbar")
        _vbox1.pack_start(_toolbar, False, False, 0)
        # menuToolButton go prev
        _go_prev_button = self.__uimanager.get_widget(
            "/ToolBar/GoPrevMenu")
        _go_prev_button.set_arrow_tooltip_text(_("Back history"))
        _go_prev_button.connect('clicked', self._menuitemGoPrevious)
        # menuToolButton go pos
        _go_post_button = self.__uimanager.get_widget(
            "/ToolBar/GoPostMenu")
        _go_post_button.set_arrow_tooltip_text(_("Forward history"))
        _go_post_button.connect('clicked', self._menuitemGoPosterior)
        # Notebook
        self.__notebook = gtk.Notebook()
        _vbox1.pack_start(self.__notebook, True, True, 0)
        self.__notebook.set_tab_pos(gtk.POS_TOP)
        self.__notebook.set_show_tabs(True)
        self.__notebook.set_show_border(True)
        self.__notebook.set_scrollable(True)
        self.__notebook.connect("switch-page", self._switch_page)
        self.__notebook.show()
        self._main()
        #TODO: create budget object in mainwindow?

    def changeHistorySignal(self):
        """changeHistorySignal()
        
        A pane emit the updateHistory signal.
        
        Nothing to do now
        """
        pass

    def changeActiveSignal(self):
        """changeActiveSignal()
        
        A pane emit the change-active signal.
        
        Chech buttons sensitive
        """
        self._checkButtonsSensitive(self.__notebook.get_current_page())

    def _checkButtonsSensitive(self, page_num):
        """_checkButtonsSensitive(page_num)
        
        page_num: page number in notebook
        
        Check and if necessary update the sensitive state of the navigation
        buttons.
        """
        _page = self.__page_list[page_num]
        if isinstance(_page, Page) and \
           self.__navigation_action_group.get_sensitive():
            # GoToRoot and GoUp actions
            _goto_root = self.__navigation_action_group.get_action("GoToRoot")
            _go_up = self.__navigation_action_group.get_action("GoUp")
            if len(_page.activePathRecord) == 1 and \
               _goto_root.get_sensitive():
                _goto_root.set_sensitive(False)
                _go_up.set_sensitive(False)
            elif len(_page.activePathRecord) != 1 and \
               not _goto_root.get_sensitive():
                _goto_root.set_sensitive(True)
                _go_up.set_sensitive(True)
            # GoPrevMenu action
            _go_Previous = self.__navigation_action_group.get_action(
                "GoPrevious")
            _go_prev = self.__navigation_action_group.get_action("GoPrevMenu")
            if _page.previousPathRecord is None:
                if _go_prev.get_sensitive():
                    _go_prev.set_sensitive(False)
                    _go_Previous .set_sensitive(False)
            else:
                if not _go_prev.get_sensitive():
                    _go_prev.set_sensitive(True)
                    _go_Previous.set_sensitive(True)
            # GoPostMenu action
            _go_Posterior = self.__navigation_action_group.get_action(
                "GoPosterior")
            _go_post = self.__navigation_action_group.get_action("GoPostMenu")
            if _page.posteriorPathRecord is None:
                if _go_post.get_sensitive():
                    _go_post.set_sensitive(False)
                    _go_Posterior.set_sensitive(False)
            else:
                if not _go_post.get_sensitive():
                    _go_post.set_sensitive(True)
                    _go_Posterior.set_sensitive(True)

    def _switch_page(self, notebook, page, page_num,):
        """_switch_page(notebook, page, page_num)
         
        Method connected to the "switch-page" signal of the notebook widget
        
        It changes the sensitive state of the navigation action group
        """
        _page = self.__page_list[page_num]
        if isinstance(_page, EmptyPage) and \
           self.__navigation_action_group.get_sensitive():
            self.__navigation_action_group.set_sensitive(False)
        elif isinstance(_page, Page):
            if not self.__navigation_action_group.get_sensitive():
                self.__navigation_action_group.set_sensitive(True)
            self._checkButtonsSensitive(page_num)
            _go_prev = self.__uimanager.get_widget("/ToolBar/GoPrevMenu")
            _go_prev.set_menu(_page.back_menu)
            _go_post = self.__uimanager.get_widget("/ToolBar/GoPostMenu")
            _go_post.set_menu(_page.forward_menu)

    def _main(self):
        """main()
        
        Shows window and starts the GTK+ event processing loop.
        """
        self.__window.show()
        gtk.main()

    def appendEmptyPage(self, emptyPage):
        """appendEmptyPage(widget, label)
        
        Append a empty page to the notebook.
        """
        self.__page_list.append(emptyPage)
        self.__notebook.append_page(emptyPage.widget, emptyPage.title)
        # TODO: reordenable and detachable Pages
        #self.__notebook.set_tab_reorderable(emptyPage.widget, True)
        #self.__notebook.set_tab_detachable(emptyPage.widget, True)

    def updatePage(self, empty_page, page):
        """updatePage(page)
        
        Update emptyPage to Page.
        """
        _page_num = self.__notebook.page_num(empty_page.widget)
        self.__page_list[_page_num] = page
        if self.__notebook.get_current_page() == _page_num:
            _go_prev = self.__uimanager.get_widget("/ToolBar/GoPrevMenu")
            _go_prev.set_menu(page.back_menu)
            _go_post = self.__uimanager.get_widget("/ToolBar/GoPostMenu")
            _go_post.set_menu(page.forward_menu)
            if not self.__navigation_action_group.get_sensitive():
                self.__navigation_action_group.set_sensitive(True)
                self._checkButtonsSensitive(_page_num)

    def _menuitemImportFiebdc(self, widget):
        """_menuitemImportFiebdc(widget)
        
        widget: the widget where the event is emitted from
        Callback to open a budget file.
        
        Creates and shows a file selection window to open a budget file.
        """
        _budget = base.Budget()
        _budget_file = fiebdc.Read()
        _read_method = _budget_file.readFile
        _filename = "file"
        _filetype = "budget"
        _exit_method = _budget_file.cancel
        _file_window = importFiebdc.FileSelectionWindow(self,
            _read_method, _budget, _filename, _exit_method, _filetype)

    #def _menuitemImportPriceDatabase(self, widget):
    #    """_menuitemImportPriceDatabase(widget)
    #    
    #    widget: the widget where the event is emitted from
    #    Callback to open a price database file.
    #    
    #    Creates and shows a file selection window to open a price database
    #    file.
    #    """
    #    _budget = base.Budget()
    #    _budget_file = fiebdc.Read()
    #    _read_method = _budget_file.readFile
    #    _filename = "file"
    #    _filetype = "database"
    #    _exit_method = _budget_file.cancel
    #    _file_window = importFiebdc.FileSelectionWindow(self,
    #        _read_method, _budget, _filename, _exit_method, _filetype)

    #def _menuitemOpenPriceDatabase(self, widget):
    #    """_menuitemOpenPriceDatabase(widget)
    #    
    #    widget: the widget where the event is emitted from
    #    Callback to open a price database from a durus file.
    #    
    #    Creates and shows a file selection window to open a durus database
    #    """
    #    _budget = None
    #    _budget_file = durusdatabase.Read()
    #    _read_method = _budget_file.readFile
    #    _filename = "file"
    #    _filetype = "durus"
    #    _exit_method = _budget_file.cancel
    #    _file_window = importFiebdc.FileSelectionWindow(self,
    #        _read_method, _budget, _filename, _exit_method, _filetype)

    def _menuitemClose(self, widget):
        """_menuitemClose(widget)
        
        widget: the widget where the event is emitted from
        
        Callback to close a budget file.
        """
        _page_num = self.__notebook.get_current_page()
        if _page_num != -1:
            _page = self.__page_list[_page_num]
            #if isinstance(_page, EmptyPage) and _page.filetype == "durus":
            #    print _("Cancel reading Durus database has not been "
            #            "implemented.")
            #else:
            _page.close()

    def closePage(self, page):
        """closePage(page)
        
        page: EmptyPage or Page object
        
        Removes a page from notebook and page_list.
        Hide navigation action group if necessary
        """
        if page in self.__page_list:
            _page_num = self.__page_list.index(page)
            self.__page_list.pop(_page_num)
            page.clear()
            self.__notebook.remove_page(_page_num)
            if len(self.__page_list) == 0:
                self.__navigation_action_group.set_sensitive(False)
        else:
            raise IndexError, _("The page is not in the page list")


    def _menuitemGoToRoot(self, widget):
        """_menuitemGoToRoot(widget)
        
        widget: the widget where the event is emitted from
        
        Callback to go to root record.
        """
        _page_num = self.__notebook.get_current_page()
        if _page_num == -1:
            return
        _page = self.__page_list[_page_num]
        if isinstance(_page, Page):
            #not loading budget
            _page.propagateMessageFrom("change_active", (-1,), (0,))

    def _menuitemGoUp(self, widget):
        """_menuitemGoUp(widget)
        
        widget: the widget where the event is emitted from
        
        Callback to go to up record.
        """
        _page_num = self.__notebook.get_current_page()
        if _page_num != -1:
            _page = self.__page_list[_page_num]
            if isinstance(_page, Page):
                #not loading budget
                _active_path = _page.activePathRecord
                if len(_active_path) > 1:
                    _budget = _page.budget
                    _up_path = _active_path[:-1]
                    if _budget.hasPath(_up_path):
                        _page.propagateMessageFrom("change_active", (-1,),
                                                   _up_path)

    def _menuitemGoPrevious(self, widget):
        """_menuitemGoPrevious(widget)
        
        widget: the widget where the event is emitted from
        
        Callback to go to previous record.
        """
        _page_num = self.__notebook.get_current_page()
        if _page_num != -1:
            _page = self.__page_list[_page_num]
            if isinstance(_page, Page):
                #not loading budget
                _previous_path = _page.previousPathRecord
                if _previous_path is not None:
                    _budget = _page.budget
                    if _budget.hasPath(_previous_path):
                        _page.propagateMessageFrom("change_active", (-1,),
                                                   _previous_path)

    def _menuitemGoPosterior(self, widget):
        """_menuitemPosterior(widget)
        
        widget: the widget where the event is emitted from
        
        Callback to go to posterior record.
        """
        _page_num = self.__notebook.get_current_page()
        if _page_num != -1:
            _page = self.__page_list[_page_num]
            if isinstance(_page, Page):
                #not loading budget
                _posterior_path = _page.posteriorPathRecord
                if _posterior_path is not None:
                    _budget = _page.budget
                    if _budget.hasPath(_posterior_path):
                        _page.propagateMessageFrom("change_active", (-1,),
                                                   _posterior_path)

    def _delete_event(self, widget, event):
        """_delete_event(widget, event)
        
        widget: the widget where the event is emitted from
        event: the "gtk.gdk.Event"
        
        Method connected to "delete_event" signal of main window widget
        This signal is emitted when a user press the close titlebar button.
        It Returns True so the signal "destroy" is emitted.
        """
        for _page in self.__page_list:
            _page.clear()
        return False # -> destroy

    def _destroy(self, widget):
        """_destroy(widget)
        
        widget: the widget where the event is emitted from
        Method connected to "destroy" signal of main window widget
        
        This signal is emited when the method connected to "delete_event"
        signal returns True or when the program call the destroy() method of
        the gtk.Window widget.
        The window is closed and the GTK+ event processing loop is ended.
        """
        gtk.main_quit()


class EmptyPage(object):
    """gui.EmptyPage:
    
    Description:
    It creates and shows a page in the notebook while a budget is loaded.
    The page show the pyarq logo, loading time and a progress bar.
    Constructor:
        gui.EmptyPage(mainWindow, readFileMethod, budget, filename,
                 cancelMethod, filetype):
            mainWindow: gui.Mainwindow object
            readFileMethod: Method to read the selected file
            budget: base.Budget object
            filename: "file"
            cancelMethod: Method to cancel the read method
            filetype: "budget", "database" or "durus"
    Ancestry:
    +-- object
      +-- EmptyPage
    Atributes:
        widget: Read. Main widget showed in the pane
        title: Read. Page Title
        filetype: Read. budget, basedata or durus
    Methods:
        run
        readFile_progress
        readFile_send_message
        readFile_set_statistics
        readFile_end
        readFile_cancel
        stopLoading
        threadFinishedSignal
        threadCanceled
        close
        clear
    """

    def __init__(self, mainWindow, readFileMethod, budget, filename,
                 cancelMethod, filetype):
        """__init__(mainWindow, readFileMethod, budget, filename,
                        cancelMethod, filetype)
        
        mainWindow: gui.Mainwindow object
        readFileMethod: Method to read the selected file
        budget: base.Budget object
        filename: "file"
        cancelMethod: Method to cancel the read method
        filetype: "budget", "database" or "durus"
        
        self.__mainWindow: gui.Mainwindow object
        self.__readFileMethod: Method to read the selected file
        self.__budget: base.Budget object
        self.__filename: "file"
        self.__cancelMethod: Method to cancel the read method
        self.__filetype: "budget", "database" or "durus"
        self.__children: the read thread
        self.__progress: 0 to 1 progress
        self.__statistics: record statistics
        self.__widget: main widget, a gtk.VBox object
        self.__main_item: None
        self.__throbber: a gtk.Image
        self.__animationThobber: a gtk.gdk.PixbufAnimation
        self.__quietThobber: a pixbuf
        self.__budget_icon: a gtk.gdk.pixbuf
        self.__title: a gtk.HBox
        self.__statusbar: a gtk.Statusbar
        self.__statuscontext: the statusbar context
        self.__progress_bar: a gtk.ProgressBar
        """
        self.__mainWindow = mainWindow
        self.__readFileMethod = readFileMethod
        self.__budget = budget
        self.__filename = filename
        self.__filetype = filetype
        self.__cancelMethod = cancelMethod
        self.__children = None
        self.__cancel = [False, False]
        self.__progress = 0.0
        self.__statistics = None
        self.__widget = gtk.VBox()
        self.__main_item = None
        self.__widget.show()
        self.__throbber = gtk.Image()
        self.__throbber.set_from_file(globalVars.getAppPath("THROBBER-ICON"))
        self.__throbber.show()
        self.__animationThobber = gtk.gdk.PixbufAnimation(
                                  globalVars.getAppPath("THROBBER-GIF"))
        self.__quietThobber = self.__throbber.get_pixbuf()
        self.__budget_icon = gtk.gdk.pixbuf_new_from_file(
                             globalVars.getAppPath("BUDGET-ICON"))
        _filename = os.path.basename(filename)
        _rootfilename = os.path.splitext(_filename)[0]
        if not _rootfilename == "":
            _filename = _rootfilename
        _titleLabel = gtk.Label(_filename)
        _titleLabel.show()
        self.__title = gtk.HBox()
        self.__title.add(self.__throbber)
        self.__title.add(_titleLabel)
        self.__statusbar = gtk.Statusbar()
        self.__statuscontext = self.__statusbar.get_context_id("Statusbar")
        self.__statusbar.show()
        _align = gtk.Alignment(0.5, 0.5, 0, 0)
        _iconVbox = gtk.VBox()
        _pyArqIcon = gtk.Image()
        _pyArqIcon.set_from_file(globalVars.getAppPath("PYARQ-ICON"))
        _pyArqIcon.show()
        _iconVbox.pack_start(_pyArqIcon, True, True, 0)
        _link = gtk.LinkButton("http://pyarq.obraencurso.es",
                               "http://pyarq.obraencurso.es")
        _iconVbox.pack_start(_link, True, True, 0)
        _link.show()
        _iconVbox.show()
        _align.add(_iconVbox)
        _align.show()
        self.__widget.pack_start(_align, True, True, 0)
        _progressframe = gtk.Frame()
        _progressframe.set_shadow_type(gtk.SHADOW_IN)
        _progressframe.show()
        self.__progress_bar = gtk.ProgressBar()
        self.__progress_bar.show()
        _progressframe.add(self.__progress_bar)
        self.__statusbar.pack_start(_progressframe, False, False, 0)
        self.__widget.pack_end(self.__statusbar, False, True, 0)
        self.__main_item = None

    def run(self):
        """run()
        
        Launch clildren and timeouts
        """
        self.__statusbar.push(self.__statuscontext, _("Time: 0s"))
        self.__throbber.set_from_animation(self.__animationThobber)
        self._launchChildren()
        self._launchTimeout()

    def readFile_progress(self, percent):
        """readFile_progress(percent)
        
        percent: Percentage executed.
        
        Sets progress
        """
        _progress = str(int(round(100 * percent,0)))
        self.__progress = percent

    def readFile_send_message(self, message):
        """readFile_send_message(message)
        
        message: mesage from readFile method
        
        print message
        """
        print message

    def readFile_set_statistics(self, statistics):
        """readFile_set_statistics(statistics)
        
        statistics: record statistics from readFile method
        
        sets record statistics
        """
        self.__statistics = statistics

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

    def stopLoading(self):
        """stopLoading()
        
        Stop progressbar
        """
        self.__throbber.set_from_pixbuf(self.__budget_icon)
        self.__progress_bar.hide()
        self.__statusbar.pop(self.__statuscontext)

    def _launchChildren(self):
        """_launchChildren()
        
        Launch the thread to read the file
        """
        if self.__children is None:
            self.__children = importFiebdc.Thread(self, self.__mainWindow,
                self.__readFileMethod, self.__budget, self.__filename,
                self.__cancelMethod, self.__filetype)
            self.__children.start()

    def _launchTimeout(self):
        """_launchTimeout()
        
        Launch the timeouts: 
            1- update progress bar
            2- update time label
            3- If the other timetouts are stoped the window is closed
        """
        gobject.timeout_add(1000, self._updateLabel, time.time())
        gobject.timeout_add(500, self._updateProgressBar)
        self.__cancel = [False, False]
        #self.__cancel = [True, False]
        gobject.timeout_add(1000, self._autoClose)

    def _updateProgressBar(self):
        """_updateProgressBar()
        
        update progress bar in a timeout
        If the thread end or is canceled the timeout is stoped
        """
        if  self.__children is None or self.__children.isCanceled() == True:
            self.__cancel[0] = True
            return False
        else:
            self.__progress_bar.set_fraction(self.__progress)
            _text = "%s%%" %str(int(round(100 * self.__progress,0)))
            self.__progress_bar.set_text(_text)
            return True

    def _updateLabel(self, _time):
        """_updateProgressBar(_time)
        
        update time label in a timeout
        If the thread end or is canceled the timeout is stoped
        """
        if  self.__children is None or self.__children.isCanceled() == True:
            self.__cancel[1] = True
            return False
        else:
            _time = time.time() - _time
            _text = utils.mapping(_("Time: $1"), ("%.0f" %_time,))
            self.__statusbar.pop(self.__statuscontext)
            self.__statusbar.push(self.__statuscontext, _text)
            return True

    def _autoClose(self):
        """_updateProgressBar()
        
        If the time label and progress bar timeouts are stoped the window is 
        closed and ist tiemeout is stoped
        """
        if self.__cancel == [ True, True ]:
            return False
        else:
            return True

    def threadFinishedSignal(self, budget):
        """threadFinishedSignal(budget)
        
        Sets the self.__children to None
        This causes that the timeouts is ended.
        This method is called from thread when it finish
        """
        self.__budget = budget
        self.__children = None
        self.stopLoading()
        _page = Page(self.__mainWindow, self.__budget)
        _children = self.__widget.get_children()
        for _child in _children:
            self.__widget.remove(_child)
        self.__widget.pack_start(_page.widget, True, True, 0)
        self.__mainWindow.updatePage(self, _page)

    def threadCanceled(self):
        """threadCanceled()
        
        Sets the __children atribute to None
        This causes that the timeouts is ended.
        This method is called from thread when is canceled
        """
        self.__children = None
        self.stopLoading()
        self.__mainWindow.closePage(self)

    def close(self):
        """close()
        
        Close page canceling children
        """
        self.__children.cancel()

    def clear(self):
        """clear()
        
        clear vars
        """
        pass

    def _getWidget(self):
        """_getWidget()
        
        Return de main widget to show in the page
        """
        return self.__widget

    def _getTitle(self):
        """_getTitle()
        
        Return the title of the page, a gtk.Label objetc
        """
        return self.__title

    def _getFiletype(self):
        """_getFiletipe()
        
        Return the title of the page, a gtk.Label objetc
        """
        return self.__filetype

    widget = property(_getWidget, None, None,
                      "Main widget showed in the pane")
    title = property(_getTitle, None, None,
                      "Page Title")
    filetype = property(_getFiletype, None, None,
                      "Filetype: budget, basedata or durus")


class Page(object):
    """gui.Page:
    
    Description:
    It creates and shows a page in the notebook from a budget object.
    The page can show the budget information in several panes ordered
    according to "panes_list" information.
    Constructor:
        gui.Page(mainWindow, budget, active_code=None)
            mainwindow: MainWindow object
            budget: base.Budget object
            active_code: Active record code
    Ancestry:
    +-- object
      +-- Page
    Atributes:
        widget: Read. Notebook page Widget. (a gtk.VBox instance)
        budget: Read-Write. Budget to show in the page. (base.obra object)
        panes_list: Read. info list for create the panes
            ej: [ "v", pane1, pane2 ] , [ "h", pane1, pane2 ]
                [ "v", [ "h", pane1, pane2 ], [ "h", pane1, pane2 ] ]
            pane types:
                * "DecompositionList": its creates a "DecompositionList" object 
                * "RecordDescription" : its creates a "Description" objetc
                * "Measure": its creates a "Measure" objetc
                * "FileView": its creates a "FileView" objet
                * "CompanyView": its creates a "CompanyView" object
        title: Read. Notebook page title (gtk.Label object)
        activePathRecord: Read. The active path record
        previousPathRecord: Read. The previous path record
        posteriorPathRecord Read. The posterior path record
        back_menu: back menu to show in menutoolbutton
        forward_menu: forward menu to show in menutoolbutton
    Methods:
        propagateMessageFrom
        sendMessageTo
        close
        clear
        getItem
    """
    # TODO:  * The panes can be ordered as the user wishes 
    # TODO:  * Panes in windows
    # TODO:  * pane types
    # TODO:      * General budget properties (is better a dialog?)

    def __init__(self, mainWindow, budget, path_record=None):
        """__init__(mainWindow, budget, path_record=None)
        
        mainWindow: MainWindow object
        budget: "base.Budget" object
        path_record: the active path record
        
        self.__mainWindow: MainWindow object
        self.__widget: a gtk.VBox
        self.__panes_list: 
        self.__main_item: 
        self.__active_path_record:
        self.__history_back:
        self.__history_forward:
        self.__back_menu: a gtk.Menu
        self.__forward_menu: a gtk.Menu
        """
        if path_record is None:
            path_record = (0,)
        #TODO: __panes_list should come from config file...
        self.__mainWindow = mainWindow
        self.__widget = gtk.VBox()
        self.__panes_list = [ "v", "DecompositionList", [ "v", "Measure",
            "RecordDescription" ]]
        self.__main_item = None
        self.__active_path_record = ()
        self.__history_back = []
        self.__history_forward = []
        self.__back_menu = gtk.Menu()
        self.__back_menu.show()
        self.__forward_menu = gtk.Menu()
        self.__forward_menu.show()
        self.budget = budget
        self._setActivePathRecord(path_record)
        self.__widget.show()
        self.__budget_icon = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("BUDGET-ICON"))
        self.__chapter_icon = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("CHAPTER-ICON"))
        self.__unit_icon  = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("UNIT-ICON") )
        self.__material_icon  = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("MATERIAL-ICON") )
        self.__machinery_icon = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("MACHINERY-ICON"))
        self.__labourforce_icon = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("LABOURFORCE-ICON"))

    def propagateMessageFrom(self, message, pane_path, arg=None):
        """propagateMessageFrom(message, pane_path, arg=None)
        
        message: string message
                * "change_active": change active code
                * "autoclose"
                * "split h"
                * "split v"
        pane_path: tuple that represents the pane path which emits the message
        arg: arguments for the message
             if message is "change_active" arg is the path record
        
        The panes are connectted to this method to send messages to other panes
        """
        _budget = self.__budget
        if message == "change_active" and _budget.hasPath(arg):
            self.sendMessageTo(self.__main_item, message, pane_path, arg)
            self._setActivePathRecord(arg)
            self.__mainWindow.changeActiveSignal()
        elif message == "autoclose":
            self._closeItem(pane_path)
        elif message == "split h":
            self._splitItem(pane_path, "h")
        elif message == "split v":
            self._splitItem(pane_path, "v")

    def sendMessageTo(self, pane, message, pane_path, arg=None):
        """sendMessageTo(pane, message, pane_path, arg=None)
        pane: the receiver pane
        message: string message
        pane_path: tuple that represents the pane pane_path which emits the message
        arg: arguments for the message
        
        Sends a message to a pane
        """
        if not pane.pane_path == pane_path:
            pane.runMessage(message, pane_path, arg)

    def close(self):
        """close()
        
        Close Page
        """
        self.__mainWindow.closePage(self)

    def clear(self):
        """clear()
        
        Clear atributes
        """
        self.propagateMessageFrom("clear", (0,))
        del self.__budget
        del self.__panes_list
        del self.__widget
        del self.__title
        del self.__active_path_record
        del self.__main_item

    def getItem(self, pane_path):
        """getItem(pane_path)
        
        Return the item whith the path "pane_path", it can return a Paned
        instance or a View instance
        """
        _item = self.__main_item
        if len(pane_path) == 1:
            return _item
        else:
            return _item.getItem(pane_path[1:])

    def _setMainItem(self, item):
        """_setMainItem(item)
        
        Sets a new main item in the page
        """
        if not self.__main_item is None:
            _old_main_widget = self.__main_item.widget
            self.__widget.remove(_old_main_widget)
        self.__main_item = item
        _main_widget = self.__main_item.widget
        _main_widget.show()
        self.__widget.pack_start(_main_widget, True, True, 0)

    def _splitItem(self, pane_path, orientation):
        """_splitItem(pane_path, orientation)
        
        Splits the item that is identifies by the pane_path and the orientation
        """
        _item = self.getItem(pane_path)
        _parent = self.getItem(pane_path[:-1])
        _item.pane_path =  pane_path + (0,)
        _item_clone0 = _item.getClone(pane_path + (0,))
        _item_clone1 = _item.getClone(pane_path + (1,))
        _paned = Paned(orientation, pane_path, _item_clone0, _item_clone1)
        if len(pane_path) > 1:
            _parent.setItem(pane_path[-1], [_paned])
        else:
            self._setMainItem(_paned)

    def _closeItem(self, pane_path):
        """_closeItem(pane_path)
        
        Closes the item that is identifies by the pane_path
        """
        _item = self.getItem(pane_path)
        if len(pane_path) > 1:
            # There are more than one item
            _parent = self.getItem(pane_path[:-1])
            _brothers = [ _brother for _brother in _parent]
            _brothers.remove(_item)
            _brother = _brothers[0]
            
            _parent.widget.remove(_brother.widget)
            _brother.pane_path = pane_path[:-1]
            if len(pane_path) > 2:
                _grandparent = self.getItem(pane_path[:-2])
                _grandparent.setItem(pane_path[-2], [_brother])
                _parent.widget.destroy()
                _parent.clear()
                _item.clear()
            else:
                _grandparent = self
                _grandparent._setMainItem(_brother)
                _parent.widget.destroy()
                _parent.clear()
                _item.clear()
        else:
            # Thre is only one item in the page, it can not be closed
            pass

    def _itemsFactory(self, list_paned, pane_path=None):
        """_itemsFactory(list_paned, pane_path=None)
        
        list_paned: list in "__panes_list" format
            [ "v" or "h", panel1_type, panel2_type]
            which contains the info for create the widgets. 
            panel types:
                * "DecompositionList"
                * "RecordDescription"
                * "Measure"
                * "Sheet of Conditions"
                * "FileView"
                * "CompanyView"
        pane_path: tuple that represents the item path in the page
        
        Creates the items and widgets and returns the main item
        """
        if pane_path is None:
            pane_path = (0,)
        if not isinstance(list_paned , list):
            raise ValueError, _("The value must be a list")
        if list_paned[0] == "v" or  list_paned[0] == "h":
            if len(list_paned) != 3:
                raise ValueError, _("Incorrect len")
            if not isinstance(list_paned[1],list):
                list_paned[1] = [list_paned[1]]
            if not isinstance(list_paned[2],list):
                list_paned[2] = [list_paned[2]]
            _item1 = self._itemsFactory(list_paned[1],pane_path + (0,))
            _item2 = self._itemsFactory(list_paned[2],pane_path + (1,)) 
            _item = Paned(list_paned[0], pane_path, _item1, _item2)
        elif list_paned[0] == "DecompositionList":
            _item = View( "DecompositionList", self.__budget,
                weakref.ref(self), pane_path, self.__active_path_record)
        elif list_paned[0] == "RecordDescription":
            _item = View( "RecordDescription", self.__budget,weakref.ref(self),
                pane_path, self.__active_path_record)
        elif list_paned[0] == "Measure":
            _item = View( "Measure", self.__budget, weakref.ref(self), pane_path,
                self.__active_path_record)
        elif list_paned[0] == "Sheet of Conditions":
            _item  = Sheet(sef.__budget, weakref.ref(self), pane_path,
                self.__active_path_record)
        elif list_paned[0] == "FileView":
            _item  = FileView(sef.__budget, weakref.ref(self), pane_path,
                self.__active_path_record)
        elif list_paned[0] == "CompanyView":
            _item  = CompanyView(sef.__budget, weakref.ref(self), pane_path,
                self.__active_path_record)
        else:
            _item = None
            raise ValueError, utils.mapping(_("Incorrect item $1"),
                  (str(list_paned[0]),))
        return _item

    def _setActivePathRecord(self, path_record):
        """_setActivePathRecord(path_record)
        
        path_record: the active record path
        
        Sets the active record path
        """
        if path_record != self.__active_path_record:
            if self.__budget.hasPath(path_record):
                self.__active_path_record = path_record
                self._appendHistory(path_record)
            else:
                raise ValueError, utils.mapping(_("The budget does not have "\
                    "the path record: $1"), (str(path_record),))

    def _appendHistory(self, path):
        """_appendHistory(path))
        
        path: the new active path record
        
        Append the new active path record to history lists and update menus
        """
        if len(self.__history_back) > 1 and path in self.__history_back[:-1]:
            # the new active record is in back history list
            # then append forward history and pop back history
            _items_num = len(self.__history_back) - \
                         self.__history_back.index(path) -1 
            for _item in range(_items_num):
                _record_path = self.__history_back.pop()
                _first_menuitem = self.__back_menu.get_children()[0]
                self.__back_menu.remove(_first_menuitem)
                self.__history_forward.append(_record_path)
                _menuitem = self._menuItemFactory(_record_path)
                _menuitem.connect_object("activate", self._menuHistoryForward,
                    _record_path, _menuitem)
                self.__forward_menu.prepend(_menuitem)
            while len(self.__history_forward) > 100:
                    # list too long
                    self.__history_forward.pop(0)
                    _last_menuitem = self.__forward_menu.get_children()[-1]
                    self.__forward_menu.remove(_last_menuitem)
        else:
            # the new active record not is in back history list
            if len(self.__history_forward) > 1 and \
               path in self.__history_forward:
                # the new active record is in history forward list
                # then append back history and pop forward history
                _items_num = len(self.__history_forward) - \
                             self.__history_forward.index(path)
                for _item in range(_items_num):
                    _record_path = self.__history_forward.pop()
                    _first_menuitem = self.__forward_menu.get_children()[0]
                    self.__forward_menu.remove(_first_menuitem)
                    self.__history_back.append(_record_path)
                    if len(self.__history_back) > 1:
                        _menuitem = self._menuItemFactory(
                            self.__history_back[-2])
                        _menuitem.connect_object("activate",
                            self._menuHistoryBack, self.__history_back[-2],
                            _menuitem)
                        self.__back_menu.prepend(_menuitem)
            else:
                # the new active record not is in history forward list
                # then append back history and clear forward history
                self.__history_forward[:] = []
                for _child in self.__forward_menu.get_children():
                    self.__forward_menu.remove(_child)
                self.__history_back.append(path)
                if len(self.__history_back) > 1:
                    _menuitem = self._menuItemFactory(self.__history_back[-2])
                    _menuitem.connect_object("activate", self._menuHistoryBack,
                        self.__history_back[-2], _menuitem)
                    self.__back_menu.prepend(_menuitem)
            while len(self.__history_back) > 100:
                # list too long
                self.__history_back.pop(0)
                _last_menuitem = self.__back_menu.get_children()[-1]
                self.__back_menu.remove(_last_menuitem)
        self.__mainWindow.changeHistorySignal()

    def _getImage(self, record):
        """_getImage(record)
        
        record: record object
        
        Returns an image depending on the type of record
        """
        _hierarchy = record.recordType.hierarchy
        _type = record.recordType.type
        _subtype = record.recordType.subtype
        if _hierarchy == 0:
            _icon = self.__budget_icon
        elif _hierarchy == 1:
            _icon = self.__chapter_icon
        else:
            if _type == 0:
                _icon = self.__unit_icon
            elif _type == 1:
                _icon = self.__labourforce_icon
            elif _type == 2:
                _icon = self.__machinery_icon
            else:
                _icon = self.__material_icon
        _image = gtk.Image()
        _image.set_from_pixbuf(_icon)
        return _image

    def _menuFactory(self):
        """_menuFactory()
        
        record: record object
        
        Creates menus for history back an history forward tool buttons
        """

        # Back Menu
        # clear menu
        for _child in self.__back_menu.get_children():
            self.__back_menu.remove(_child)
        # pupulate menu
        if len(self.__history_back) > 1:
            for _record_path in self.__history_back[:-1]:
                _menuitem = self._menuItemFactory(_record_path)
                _menuitem.connect_object("activate", self._menuHistoryBack,
                    _record_path, _menuitem)
                self.__back_menu.prepend(_menuitem)
        # Forward Menu
        # clear menu
        for _child in self.__forward_menu.get_children():
            self.__forward_menu.remove(_child)
        # pupulate menu
        if len(self.__history_forward) > 0:
            for _record_path in self.__history_forward[:]:
                _menuitem = self._menuItemFactory(_record_path)
                _menuitem.connect_object("activate", self._menuHistoryForward,
                    _record_path, _menuitem)
                self.__forward_menu.prepend(_menuitem)

    def _menuItemFactory(self, record_path):
        """_menuItemFactory(record_path):
        
        record_path: record path
        
        Creates and return a menuItem to go to the record
        """
        _code = self.budget.getCode(record_path)
        _record = self.budget.getRecord(_code)
        _summary = _record.summary
        _text = _code + " " + _summary
        if len(_text) > 30:
            _text = _text[:27] + "..."
        _image = self._getImage(_record)
        _menuitem = gtk.ImageMenuItem(_text)
        _menuitem.set_image(_image)
        _menuitem.show()
        return _menuitem

    def _menuHistoryBack(self, record_path, menu_item):
        """_menuHistoryBack(record_path, menu_item)
        
        Go to the record selected in History Back menu
        """
        if self.budget.hasPath(record_path):
            self.propagateMessageFrom("change_active", (-1,), record_path)

    def _menuHistoryForward(self, record_path, menu_item):
        """_menuHistoryForward(record_path, menu_item)
        
        Go to the record selected in History Forward menu
        """
        if self.budget.hasPath(record_path):
            self.propagateMessageFrom("change_active", (-1,), record_path)

    def _getActivePathRecord(self):
        """_getActivePathRecord()
        
        Return the Active Path Record
        """
        return self.__active_path_record
    
    def _getPreviousPathRecord(self):
        """_getPreviousPathRecord()
        
        Return the Previous Path Record
        """
        if len(self.__history_back) > 1: 
            return self.__history_back[-2]
        else:
            return None

    def _getPosteriorPathRecord(self):
        """_getPosteriorPathRecord()
        
        Return the Posterior Path Record
        """
        if len(self.__history_forward) > 0: 
            return self.__history_forward[-1]
        else:
            return None

    def _getBackMenu(self):
        """_getBackMenu()
        
        Return the Back Menu
        """
        return self.__back_menu

    def _getForwardMenu(self):
        """_getForwardMenu()
        
        Return the Forward Menu
        """
        return self.__forward_menu

    def _getTitle(self):
        """_getTitle()
        
        Return the page title, a gtk.Label objetc
        """
        return self.__title
    
    def _getWidget(self):
        """_getWidget()
        
        Return de main widget to show in the pane
        """
        return self.__widget
    
    def _setBudget(self, budget):
        """_setBudget(budget)
        
        budget: a base.Budget object
        
        Sets the budget and the active code atributes,
        creates the page title and the widgets in the pane and
        shows the main widget.
        """
        if budget is None:
            self.clear()
            return
        self.__budget = budget
        self._setActivePathRecord((0,))
        # Todo: change page title
        self.__title = gtk.Label(self.__budget.getCode(
                       self.__active_path_record))
        _panes_list = self.__panes_list
        self.__main_item = self._itemsFactory(_panes_list)
        _main_widget = self.__main_item.widget
        _main_widget.show()
        self.__widget.pack_start(_main_widget, True, True, 0)

    def _getBudget(self):
        """_getBudget()
        
        Return de budget, a "base.Budget" object.
        """
        return self.__budget
    
    def _getPanesList(self):
        """_getPanesList()
        
        Return the panes list, info list for create the panes.
        """
        return self.__panes_list

    budget = property(_getBudget, _setBudget, None,
                      "Budget to show, base.Budget object")
    widget = property(_getWidget, None, None,
                      "Main widget showed in the pane")
    title = property(_getTitle, None, None,
                      "Page Title")
    panes_list = property(_getPanesList, None, None,
                      "Info list for create the panes")
    activePathRecord = property(_getActivePathRecord, None, None,
                      "Active Path Record")
    previousPathRecord = property(_getPreviousPathRecord, None, None,
                      "Previous Active Path Record")
    posteriorPathRecord = property(_getPosteriorPathRecord, None, None,
                      "Posterior Active Path Record")
    back_menu = property(_getBackMenu, None, None,
                      "Back Menu")
    forward_menu = property(_getForwardMenu, None, None,
                      "Forward Menu")

class View(object):
    """gui.View:
    
    Description:
        It creates a view to show the budget info
    Constructor:
        View(view_type, budget, wr_page, pane_path, active_path_record)
            view_type: the object type to show
                * DecompositionList
                * Description
                * Measure
                * Sheet
                * FileView
                * CompanyView
            budget: the budget to show
            wr_page: weak reference to the page where the view must be showed
            pane_path: the position or path of the view in the page notebook
            active_path_record: the record path that must be showed
    Ancestry:
    +-- object
      +-- View
    Atributes:
        pane_path: Read-Write. The tuple that identifies the view in the main 
            notebook page
        widget: Read. the main gtk widget to show in a view object,
            a gtk.VBox object
    Methods:
        getItem
        propagateMessgeFrom
        runMessage
        getClone
        clear
    """

    def __init__(self, view_type, budget, wr_page, pane_path,
                 active_path_record):
        """__init__(view_type, budget, wr_page, pane_path, active_path_record)
        view_type: the object type to show
            * DecompositionList
            * Description
            * Measure
            * Sheet
            * FileView
            * CompanyView
        budget: the budget to show
        wr_page: weak reference to the page where the view must be showed
        pane_path: the position or path of the view in the page notebook
        active_path_record: the record path that must be showed
        
        self.__active_path_record: the record path that must be showed
        self.__view_type: the object type to show
            * DecompositionList
            * Description
            * Measure
            * Sheet of conditions
            * FileView
            * CompanyView
        self.__wr_page: weak reference to the page where the view must be
            showed
        self.__budget: the budget to show
        self.__pane_path: the position or path of the view in the page notebook
        self.__connected: boolean value, True means that the View object sends
            and receives signals from/to others views
        self.__widget: main widget. a gtk.VBox
        self.__view: the object to show:
            * DecompositionList object
            * Description object
            * Measure object
            * Sheet object
            * FileView object
            * Comapany View
        self.__connected_button: a button to switch self.__connected True or
            False
        
        Creates and shows a new view
        """
        self.__active_path_record = active_path_record
        self.__view_type = view_type
        self.__wr_page = wr_page
        self.__budget = budget
        self.__pane_path = pane_path
        self.__connected = True
        # view_type liststore
        _liststore = gtk.ListStore(str)
        _liststore.append([_("Decomposition")]) #0
        _liststore.append([_("Description")]) #1
        _liststore.append([_("Measure")]) #2
        _liststore.append([_("Sheet of Conditions")]) #3
        _liststore.append([_("Files")]) #4
        _liststore.append([_("Companies")]) #5
        _combobox = gtk.ComboBox(_liststore)
        _cell = gtk.CellRendererText()
        _combobox.pack_start(_cell, True)
        _combobox.add_attribute(_cell, 'text', 0)
        self.__widget = gtk.VBox()
        _hbox = gtk.HBox()
        if view_type == "DecompositionList":
            self.__view = DecompositionList(budget, weakref.ref(self),
                          pane_path, active_path_record)
            _combobox.set_active(0)
            _view_icon = gtk.Image()
            _view_icon.set_from_file(globalVars.getAppPath(
                "DECOMPOSITION-ICON"))
        elif view_type == "RecordDescription":
            self.__view = Description(budget, weakref.ref(self),
                          pane_path, active_path_record)
            _combobox.set_active(1)
            _view_icon = gtk.Image()
            _view_icon.set_from_file(globalVars.getAppPath(
                "DESCRIPTION-ICON"))
        elif view_type == "Measure":
            self.__view = Measure(budget, weakref.ref(self),
                          pane_path, active_path_record)
            _combobox.set_active(2)
            _view_icon = gtk.Image()
            _view_icon.set_from_file(globalVars.getAppPath("MEASURE-ICON"))
        elif view_type == "Sheet of Conditions":
            self.__view = Sheet(budget, weakref.ref(self),
                          pane_path, active_path_record)
            _combobox.set_active(3)
            _view_icon = gtk.Image()
            _view_icon.set_from_file(globalVars.getAppPath("SHEET-ICON"))
        elif view_type == "FileView":
            self.__view = FileView(budget, weakref.ref(self),
                          pane_path, active_path_record)
            _combobox.set_active(4)
            _view_icon = gtk.Image()
            _view_icon.set_from_file(globalVars.getAppPath("SHEET-ICON"))
        elif view_type == "CompanyView":
            self.__view = CompanyView(budget, weakref.ref(self), pane_path,
                          active_path_record)
            _combobox.set_active(5)
            _view_icon = gtk.Image()
            _view_icon.set_from_file(globalVars.getAppPath("SHEET-ICON"))
        else:
            raise ValueError, _(utils.mapping("Invalid type of View: $1",
                  view_type))
        _view_icon.show()
        _combobox.connect("changed", self._change_combo)
        _combobox.show()
        self.__widget.pack_start(_hbox,False)
        self.__widget.pack_start(self.__view.widget, True, True)
        _hbox.pack_start(_view_icon, False, False,0)
        _hbox.pack_start(_combobox, False, False,0)
        _invisible = gtk.HBox()
        _invisible.show()
        _hbox.pack_start(_invisible, True, False,0)
        _icon_menu = gtk.Image()
        _icon_menu.set_from_file(globalVars.getAppPath("MENU-ICON"))
        _icon_menu.show()
        _menu_button = gtk.ToolButton()
        _menu_button.set_icon_widget(_icon_menu)
        _menu_button.connect("clicked", self._menu_view)
        _menu_button.show()
        _icon_connected = gtk.Image()
        _icon_connected.set_from_file(globalVars.getAppPath("CONNECTED-ICON"))
        _icon_connected.show()
        _hbox.pack_start(_menu_button, False, False, 0)
        self.__connected_button = gtk.ToolButton()
        self.__connected_button.set_icon_widget(_icon_connected)
        self.__connected_button.connect("clicked", self._connected)
        self.__connected_button.show()
        _hbox.pack_start(self.__connected_button, False, False, 0)
        _icon_close = gtk.Image()
        _icon_close.set_from_file(globalVars.getAppPath("CLOSE-ICON"))
        _icon_close.show()
        _close_button = gtk.ToolButton()
        _close_button.set_icon_widget(_icon_close)
        _close_button.connect("clicked", self._closeItem)
        _close_button.show()
        _hbox.pack_start(_close_button, False, False, 0)
        _hbox.show()
        self.__widget.show()

    def getItem(self, pane_path):
        """getItem(pane_path)
        
        Return itself.
        """
        return self

    def _closeItem(self, close_button):
        """_closeItem(close_button)
        
        Method connected to the "clicked" signal of the _close_button widget
        Send the "autoclose" message to the page to close this view
        """
        self.propagateMessageFrom("autoclose", self.__pane_path)

    def _change_combo(self, combobox):
        """_change_combo(combobox)
        
        Method connected to the "changed" signal of the _combobox widget
        It changes the view type to the type selected in the combobox
        """
        _index = combobox.get_active()
        _budget = self.__view.budget
        _wr_page = self.__view.page
        _pane_path = self.__view.pane_path
        _path_record = self.__view.active_path_record
        _hbox = self.__widget.get_children()[0]
        _combobox = _hbox.get_children()[1]
        _hbox.remove(_combobox)
        _invisible = _hbox.get_children()[1]
        _hbox.remove(_invisible)
        _menu_button = _hbox.get_children()[1]
        _hbox.remove(_menu_button)
        _connected_button = _hbox.get_children()[1]
        _hbox.remove(_connected_button)
        _close_button = _hbox.get_children()[1]
        _hbox.remove(_close_button)
        self.__widget.remove(self.__view.widget)
        self.__widget.remove(_hbox)
        _hbox.destroy()
        _view_icon = gtk.Image()
        if _index == 0:
            self.__view = DecompositionList(_budget, _wr_page, _pane_path,
                          _path_record)
                        
            _view_icon.set_from_file(globalVars.getAppPath(
                "DECOMPOSITION-ICON"))
            self.__view_type = "DecompositionList"
        elif _index == 1:
            self.__view = Description(_budget, _wr_page, _pane_path,
                         _path_record)
            _view_icon.set_from_file(globalVars.getAppPath("DESCRIPTION-ICON"))
            self.__view_type = "RecordDescription"
        elif _index == 2:
            self.__view = Measure(_budget, _wr_page, _pane_path,
                         _path_record)
            _view_icon.set_from_file(globalVars.getAppPath("MEASURE-ICON"))
            self.__view_type = "Measure"
        elif _index == 3:
            self.__view = Sheet(_budget, _wr_page, _pane_path,
                         _path_record)
            _view_icon.set_from_file(globalVars.getAppPath("SHEET-ICON"))
            self.__view_type = "Sheet of Conditions"
        elif _index == 4:
            self.__view = FileView(_budget, _wr_page, _pane_path,
                         _path_record)
            _view_icon.set_from_file(globalVars.getAppPath("SHEET-ICON"))
            self.__view_type = "FileView"
        elif _index == 5:
            self.__view = CompanyView(_budget, _wr_page, _pane_path,
                          _path_record)
            _view_icon.set_from_file(globalVars.getAppPath("SHEET-ICON"))
            self.__view_type = "CompanyView"
        _view_icon.show()
        _hbox = gtk.HBox()
        _hbox.pack_start(_view_icon, False, False,0)
        _hbox.pack_start(_combobox, False, False,0)
        _hbox.pack_start(_invisible, True, False,0)
        _hbox.pack_start(_menu_button, False, False, 0)
        _hbox.pack_start(_connected_button, False, False, 0)
        _hbox.pack_start(_close_button, False, False, 0)
        _hbox.show()
        self.__widget.pack_start(_hbox, False, False, 0)
        self.__widget.pack_start(self.__view.widget, True, True, 0)

    def _menu_view(self, widget):
        """_menu_view(widget)
        
        Method connected to the "clicked" signal of the __connected_button
        It shows a popup menu with some options
        """
        _menu_view = gtk.Menu()
        _item_leftright = gtk.MenuItem(_("Split View Left/Right"))
        _menu_view.append(_item_leftright)
        _item_leftright.connect_object("activate", self._split_view, "h")
        _item_leftright.show()
        _item_topbottom = gtk.MenuItem(_("Split View Top/Bottom"))
        _menu_view.append(_item_topbottom)
        _item_topbottom.connect_object("activate", self._split_view, "v")
        _item_topbottom.show()
        _item_close = gtk.MenuItem(_("Close view"))
        _menu_view.append(_item_close)
        _item_close.connect_object("activate", self._closeItem, None)
        _item_close.show()
        _menu_view.popup(None, None, None, 0, 0)

    def _split_view(self, orientation):
        """_menu_view(orientation)
        
        orientation: orientation split, "h" or "v"
        
        Method connected to the "activate" signal of the _item_leftright and
        _item_topbottom menu items.
        It sends the "split" message to the page to splits the view in the
        specified orientation
        """
        self.propagateMessageFrom( "split " + orientation, self.__pane_path)

    def _connected(self, widget):
        """_connected(widget)
        
        Method connected to the "clicked" signal of the _menu_button
        It changes the __connected atribute to True or False, if the 
        _connected atribute is False the view do not send and receive messages
        to/from others views
        """
        if self.__connected:
            _icon = gtk.Image()
            _icon.set_from_file(globalVars.getAppPath("DISCONNECTED-ICON"))
            _icon.show()
            self.__connected_button.set_icon_widget(_icon)
            self.__connected = False
        else:
            _icon = gtk.Image()
            _icon.set_from_file(globalVars.getAppPath("CONNECTED-ICON"))
            _icon.show()
            self.__connected_button.set_icon_widget(_icon)
            self.__connected = True

    def propagateMessageFrom(self, message, pane_path, arg=None):
        """propagateMessageFrom(message, pane_path, arg=None)
        
        message: string message
        pane_path: tuple that represents the pane path which emits the message
        arg: arguments for the message
        The panes are connectted to this method to send messages to other panes
        """
        if self.__connected or message == "autoclose" or \
           message == "split h" or message == "split v":
            self.__wr_page().propagateMessageFrom(message, pane_path, arg)

    def runMessage(self, message, pane_path, arg=None):
        """runMessage(message, pane_path, arg=None)
        
        message: the message type
            "change_active": change the active record
            "clear": clear instance
        pane_path: tuple that identifies the pane in the notebook page
        arg: tuple whit two items:
            0: record path in the budget
            1: record code
        This method receives a message and executes its corresponding action
        """
        if self.__connected:
            self.__view.runMessage(message, pane_path, arg)
            if message == "change_active":
                if self.__budget.hasPath(arg):
                    _path_record = arg
                    self.__active_path_record = _path_record

    def _getWidget(self):
        """_getWidget()
        
        Return de pane widget
        """
        return self.__widget

    def _getPanePath(self):
        """_getPanePath()
        
        return the tuple that identifies the pane in the notebook page
        """
        return self.__view.pane_path

    def _setPanePath(self, pane_path):
        """_setPanePath()
        
        set the tuple that identifies the pane in the notebook page
        """
        self.__pane_path = pane_path
        self.__view.pane_path = pane_path

    def getClone(self, new_pane_path):
        """getClone(new_pane_path)
        
        new_pane_path: the path that identifies the clone view in the page
        
        return a clone of itself
        """
        return View(self.__view_type, self.__budget, self.__wr_page,
                       new_pane_path, self.__active_path_record)

    def clear(self):
        """clear()
        
        Clear the intance atributes
        """
        del self.__wr_page
        del self.__budget
        del self.__pane_path
        del self.__widget
        del self.__view
        del self.__connected
        del self.__connected_button

    pane_path = property(_getPanePath, _setPanePath, None,
        "path that identifies the item in the notebook page")
    widget = property(_getWidget, None, None, "View widget")


class Paned(object):
    """gui.Paned:
    
    Description:
        It creates and shows gtk.Hpaned or gtk.Vpaned to show in page budget
    Constructor:
        Paned(orientation, widget1, widget2)
            orientation: The orientation of the pane separator, can be "v" or
                "h"
            widget1: the top or left pane widget
            widget2: the botton or right pane widget
    Ancestry:
    +-- object
      +-- Paned
    Atributes:
        widget: Read. Pane widget("gtk.VPaned" or "gtk.HPaned" object)
        pane_path: Read-Write. The paned path in the page
    Methods:
        getClone
        getItem
        setItem
        runMessage
        clear(self)
    """
    # TODO:  *control the position paned separator. Now is always in the middle
    # TODO:     can be with a float(0.0-1.0) aspect ratio
    # TODO:          0.0 no space for widget1
    # TODO:          1.0 all the space for widget1

    def __init__(self, orientation, pane_path, item1, item2):
        """__init__(oritentation, pane_path, item1, item2)
        
        orientation: The orientation of de gtk.Paned, can be "v" or "h"
        pane_path: the paned path in the page
        item1: the top or left pane object
        item2: the bottom or right pane object
        
        self.__orientation: The orientation of de gtk.Paned, can be "v" or "h"
        self.__widget: Main widget, a gtk.VPaned o gtk.HPaned
        self.__items: list of items showed in the paned, its can be View or
            Paned instances
        self.__pane_path: the paned path in the page
        
        Creates and shows a new gtk.Paned
        """
        self.__orientation = orientation
        if not isinstance(item1.widget, gtk.Widget) or \
           not isinstance(item2.widget, gtk.Widget):
            raise ValueError, _("The item must be a widget object.")
        if orientation == "v":
            self.__widget = gtk.VPaned()
        elif orientation == "h":
            self.__widget = gtk.HPaned()
        else:
            raise ValueError, _("Invalid orientation.")
        self.__widget.pack1(item1.widget,True,False)
        self.__widget.pack2(item2.widget,True,False)
        self.__widget.show()
        self.__items = [item1, item2]
        self.__pane_path = pane_path

    def __getitem__(self, item):
        """__getitem__(item)
        
        Called to implement evaluation of self[key].
        The accepted keys should be integers 0 or 1.
        """
        return self.__items[item]

    def getClone(self, new_pane_path):
        """getClone(new_pane_path)
        
        Return a clone Paned instance with the path new_path
        """
        return Paned(self.__orientation, new_pane_path,
                     self.__items[0].getClone(new_pane_path + (0,)),
                     self.__items[1].getClone(new_pane_path + (1,)))

    def getItem(self,pane_path):
        """getItem(pane_path)
        
        Return the item whith the specified path.
        """
        _item = self.__items[pane_path[0]]
        if len(pane_path) == 1:
            return _item
        else:
            return _item.getItem(pane_path[1:])
        
    def setItem(self, pane_path, item_list):
        """setItem(pane_path, item_list)
        
        Sets the first item in the item_list whith the especified path and
        remove the old item in this position.
        """
        item = item_list[0]
        if pane_path == 0 or pane_path == 1:
            _old_item = self.__items[pane_path]
            self.__widget.remove(_old_item.widget)
            self.__items[pane_path] = item
            if pane_path == 0:
                self.__widget.pack1(item.widget,True,False)
            else:
                self.__widget.pack2(item.widget,True,False)
            return True
        return False

    def runMessage(self, message, pane_path, arg=None):
        """runMessage(message, pane_path, arg=None)
        
        message: the message type
            "change_active": change the active record
            "clear": clear instance
        pane_path: tuple that identifies the pane in the notebook page
        arg: arguments
        
        This method receives a message and send this to the items of the paned
        """
        for _item in self.__items:
            if not _item.pane_path == pane_path:
                _item.runMessage(message, pane_path, arg)

    def _getWidget(self):
        """_getWidget()
        
        Return de gtk.Paned widget
        """
        return self.__widget

    def _getPanePath(self):
        """_getPanePath()
        
        Return de Paned path in the notebook page
        """
        return self.__pane_path

    def _setPanePath(self, pane_path):
        """_setPanePath()
        
        sets the tuple that identifies the pane in the notebook page
        """
        self.__pane_path = pane_path
        self.__items[0].pane_path = pane_path + (0,)
        self.__items[1].pane_path = pane_path + (1,)

    def clear(self):
        """clear()
        
        Delete atributes
        """
        del self.__widget
        del self.__orientation
        del self.__items
        del self.__pane_path

    widget = property(_getWidget, None, None, "gtk.Paned widget")
    pane_path = property(_getPanePath, _setPanePath, None,
        "Pane path in the notebook page")


class TreeView(object):
    """gui.Treeviev:
    
    Description:
        It creates the columns in a treeview, is the base class for 
        DescompositionList and Measure classes 
    Constructor:
        TreView(args)
        args: list of tuples, the tuple items are:
            0.type:
                * index column
                * float column
                * text column
                * calculated column
                * calculated text
                * type column
            1. clicked method
            2. width
            3. text color
            4. backgruound colors
            5. model column index
    Ancestry:
    +-- object
      +-- TreeView
    Atributes:
        columns: list of columns (gtk.TreeViewColumn objects)
    Methods:
        createColumn
        createTextBaseColumn
        createBaseColumn
    """

    def __init__(self, args):
        """__init__(args)
        
        args: list of tuples, the tuple items are:
            0.type:
                * index column
                * float column
                * text column
                * calculated column
                * Calculated text
                * type column
            1. clicked method
            2. width
            3. text color
            4. backgruound colors
            5. model column index
        
        Create the columns form the args info calling creatheColumn to create
        each column
        """
        self.columns = [ self.createColumn(arg) for arg in args ]
        self.columns.append(self.createColumn(("END",)))
    
    def createColumn(self, args):
        """createColumn(args)
        
        args: tuple with the args
            0.type:
                * index column
                * float column
                * text column
                * calculated column
                * calculated text
                * type column
            1. clicked method
            2. width
            3. text color
            4. backgruound colors
            5. model column index
        
        Return a column created whith the arg info
        """
        if args[0] == "INDEX":
            _index_column = self.createBaseColumn(args)
            _text_index_cell = gtk.CellRendererText()
            _text_index_cell.set_property('foreground-gdk',
                gtk.gdk.color_parse(globalVars.color["TEXT"]))
            _pixbuf_index_cell = gtk.CellRendererPixbuf()
            _arrow_icon = gtk.gdk.pixbuf_new_from_file(
                globalVars.getAppPath("ARROW-ICON"))
            _pixbuf_index_cell.set_property("pixbuf", _arrow_icon)
            _index_column.pack_start(_text_index_cell, True)
            _index_column.pack_start(_pixbuf_index_cell, True)
            _index_column.set_cell_data_func(_text_index_cell,
                self._colorCell,
                [gtk.gdk.color_parse(globalVars.color["INDEX-UNEVEN"]),
                gtk.gdk.color_parse(globalVars.color["INDEX-EVEN"])])
            return _index_column
        elif args[0] == "TEXT":
            _column, _cell = self.createTextBaseColumn(args)
            _column.add_attribute(_cell, 'text', args[5])
            return _column
        elif args[0] == "FLOAT":
            _column, _cell = self.createTextBaseColumn(args)
            _column.add_attribute(_cell, 'text', args[5])
            _column.get_cell_renderers()[0].set_property('xalign', 1.0)
            return _column
        elif args[0] == "CALCULATED":
            _column, cell = self.createTextBaseColumn(args)
            _column.get_cell_renderers()[0].set_property('xalign', 1.0)
            return _column
        elif args[0] == "CALCULATEDTEXT":
            _column, cell = self.createTextBaseColumn(args)
            return _column
        elif args[0] == "TYPE":
            _column = self.createBaseColumn(args)
            _type_cell1 = gtk.CellRendererPixbuf()
            _type_cell2 = gtk.CellRendererText()
            _type_cell2.set_property('foreground-gdk', args[3])
            _column.pack_start(_type_cell1, True)
            _column.pack_start(_type_cell2, True)
            _column.add_attribute(_type_cell2, 'text', args[5])
            _column.set_cell_data_func(_type_cell1,
                self._colorCell, args[4])
            _column.set_cell_data_func(_type_cell2,
                self._colorCell, args[4])
            return _column
        elif args[0] == "PIXBUF":
            _column = self.createBaseColumn(args)
            _type_cell1 = gtk.CellRendererPixbuf()
            _column.pack_start(_type_cell1, True)
            _column.set_cell_data_func(_type_cell1,
                self._colorCell, args[4])
            return _column
        elif args[0] == "END":
            _end_column = gtk.TreeViewColumn()
            _end_column.set_clickable(False)
            _end_cell = gtk.CellRendererText()
            _end_cell.set_property('cell-background-gdk',
                gtk.gdk.color_parse(globalVars.color["UNEVEN"]))
            _end_column.pack_start(_end_cell, True)
            return _end_column
        return None

    def createTextBaseColumn(self, args):
        """createTextBaseColumn(args)
        
        args: tuple with the args
            0.type:
                * float column
                * text column
                * calculated column
                * calculated text
            1. clicked method
            2. width
            3. text color
            4. backgruound colors
            5. model column index
        
        Return a column and its CellREndererText
        """
        _column = self.createBaseColumn(args)
        _cell = gtk.CellRendererText()
        _cell.set_property('foreground-gdk', args[3])
        _column.pack_start(_cell, True)
        _column.set_cell_data_func(_cell, self._colorCell, args[4])
        return _column, _cell

    def createBaseColumn(self, args):
        """createBaseColumn(args)
        
        args: tuple with the args
            0.type:
                * index column
                * float column
                * text column
                * calculated column
                * calculated text column
                * type column
            1. clicked method
            2. width
            3. text color
            4. backgruound colors
            5. model column index
        
        Return a column
        """
        _column = gtk.TreeViewColumn()
        _column.set_clickable(True)
        _column.connect("clicked", args[1])
        _column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        _column.set_fixed_width(args[2])
        _column.set_resizable(True)
        return _column


class DecompositionList(TreeView):
    """gui.DecompositionList:
    
    Description:
        Class to show a budget Decomposition List
    Constructor:
        DecompositionList(budget, page, pane_path, path_record=(0,))
        budget: budget showed ("base.Budget" object)
        page: weak reference from Page instance which creates this class
        pane_path: tuple that represents the view path in the Page
        path_record: the record path that must be showed
        Returns the newly created DecompositionList instance
    Ancestry:
    +-- object
      +-- TreeView
        +-- DecompositionList
    Atributes:
        budget: Read. Budget to show, base.obra object.
        widget: Read. Window that contains the table, gtk.ScrolledWindow
        pane_path: Read-Write. Pane page identifier
        page: Read-Write. weak ref from Page object which creates this class
        active_path_record: Read. Active path record
    Methods:
        runMessage
    """

    def __init__(self, budget, page, pane_path, path_record=None):
        """__init__(budget, page, pane_path, path_record=None)
        
        budget: budget showed ("base.Budget" object)
        page: weak reference from Page instance which creates this class
        pane_path: tuple that represents the path of the List in the Page
        path_record: the record path that must be showed
        
        self.__budget: budget showed ("base.Budget" object)
        self.__page: weak reference from Page instance which creates this class
        self.__pane_path: tuple that represents the path of the List in the Page
        self.__liststore: list model which store the list data
            (gtk.ListStore object)
        self.__active_path_record: the record path that must be showed
        self.__treeview: widget for displaying decomposition lists
            (gtk.TreeView)
        self.__scrolled_window: widget to contain the treeview object
        self.__chapter_background_colors: background colors of the Code
            column cells when there is a chapter record,
            list of gtk.gdk.Color objects [even cell, uneven cell]
        self.__chapter_background_colors
        self.__index_column: Index column (gtk.TreeViewColumn object)
        self.__code_column: Record code column (gtk.TreeViewColumn)
        self.__type_column: Record Type column (gtk.TreeViewColumn)
        self.__unit_column: Unit of measure column (gtk.TreeViewColumn)
        self.__description_column: record's short description column 
            (gtk.TreeViewColumn)
        self.__measure_column: Measure column (gtk.TreeViewColumn)
        self.__price_column: Price column (gtk.TreeViewColumn)
        self.__amount_column: Amount column(gtk.TreeViewColumn)
        self.__end_column: End empty column (gtk.TreeViewColumn)
        self.__chapter_icon: a gtk.gdk.pixbuf
        self.__unit_icon: a gtk.gdk.pixbuf
        self.__material_icon: a gtk.gdk.pixbuf
        self.__machinery_icon: a gtk.gdk.pixbuf
        self.__labourforce_icon: a gtk.gdk.pixbuf
        self.__treeselection: active selection
        self.__selection_control: state of the selection control (True/False)
        self.__cursor: cursor position in the table
        
        Sets the init atributes
        Creates the init list values in self.__liststore from the budget 
            showing the top record descomposition
        Creates the list in self.__treeview
            * Creates the columns and cell
            * Sets te the column headers values
            * Sets the selection properties
            * Connects the events
        """
        # TODO: to group all columns in a dicctionary
        # Budget
        if path_record is None:
            parh_record = (0,)
        if not isinstance(budget, base.Budget):
            raise ValueError, _("Argument must be a Budget object")
        self.__budget = budget
        self.__page = page
        self.__pane_path = pane_path
        # ListStore
        self.__liststore = gtk.ListStore(object
            #, int, int, str, str, str, str, str,str
            )
        if path_record is None:
            print _("Record path can not be None")
            path_record = (0,)
        self.__active_path_record = path_record
        self._setListstoreValues(self.__active_path_record)
        # Treeview
        self.__treeview = gtk.TreeView(self.__liststore)
        self.__treeview.set_enable_search(False)
        self.__treeview.set_reorderable(False)
        self.__treeview.set_headers_clickable(True)
        self.__treeview.show()
        # Scrolled_window
        self.__scrolled_window = gtk.ScrolledWindow()
        self.__scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                        gtk.POLICY_AUTOMATIC)
        self.__scrolled_window.add(self.__treeview)
        # colors
        _text_color = gtk.gdk.color_parse(globalVars.color["TEXT"])
        _background_color = [
            gtk.gdk.color_parse(globalVars.color["UNEVEN"]),
            gtk.gdk.color_parse(globalVars.color["EVEN"])]
        self.__chapter_background_colors = [
            gtk.gdk.color_parse(globalVars.color["CHAPTER-UNEVEN"]),
            gtk.gdk.color_parse(globalVars.color["CHAPTER-EVEN"])]
        super(DecompositionList,self).__init__(
            [("INDEX",self._selectAll,42),
            ("CALCULATEDTEXT", self._showParentRecord, 
             gtk.Label("A"*10).size_request()[0] +10,
             _text_color, _background_color),
            ("PIXBUF", self._showParentRecord, 26, _text_color,
             _background_color),
            ("CALCULATEDTEXT", self._showParentRecord,
            gtk.Label(_("a"*4)).size_request()[0] +10,
            _text_color, _background_color),
            ("CALCULATEDTEXT", self._showParentRecord,
            gtk.Label("a"*30).size_request()[0] +10,
            _text_color, _background_color),
            ("CALCULATED", self._showParentRecord,
            gtk.Label("a"*10).size_request()[0] +10,
            _text_color, _background_color),
            ("CALCULATED", self._showParentRecord,
            gtk.Label("a"*10).size_request()[0] +10,
            _text_color, _background_color),
            ("CALCULATED", self._showParentRecord,
            gtk.Label("a"*10).size_request()[0] +10,
            gtk.gdk.color_parse(globalVars.color["CALCULATED-TEXT"]),
            _background_color),
            ])
        self.__index_column = self.columns[0]
        self.__code_column = self.columns[1]
        self.__type_column = self.columns[2]
        self.__unit_column = self.columns[3]
        self.__description_column = self.columns[4]
        self.__measure_column = self.columns[5]
        self.__price_column = self.columns[6]
        self.__amount_column = self.columns[7]
        self.__end_column = self.columns[8]
        # Index column
        self.__treeview.append_column(self.__index_column)
        # Code column
        self.__treeview.append_column(self.__code_column)
        # Type column
        self.__treeview.append_column(self.__type_column)
        self.__chapter_icon = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("CHAPTER-ICON"))
        self.__unit_icon  = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("UNIT-ICON") )
        self.__material_icon  = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("MATERIAL-ICON") )
        self.__machinery_icon = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("MACHINERY-ICON"))
        self.__labourforce_icon = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("LABOURFORCE-ICON"))
        self.__type_column.get_cell_renderers()[0].set_property("pixbuf",
            self.__labourforce_icon)
        
        # Unit column
        self.__treeview.append_column(self.__unit_column)
        # Description column
        self.__treeview.append_column(self.__description_column)
        # Measure Column
        self.__treeview.append_column(self.__measure_column)
        # Price column
        self.__treeview.append_column(self.__price_column)
        # Amount column
        self.__treeview.append_column(self.__amount_column)
        # End Column
        self.__treeview.append_column(self.__end_column)
        # Connect
        self.__treeview.connect("row-activated", self._showRowRecord)
        self.__treeview.connect("move-cursor", self._moveCursor)
        self.__treeview.connect("key-press-event", self._treeviewKeyPressEvent)
        self.__treeview.connect("button-press-event",
            self._treeviewClickedEvent)
        self.__treeview.connect("cursor-changed", self._treeviewCursorChanged)
        # control selection
        self.__treeselection = self.__treeview.get_selection()
        self.__treeselection.set_mode(gtk.SELECTION_MULTIPLE)
        self.__treeselection.set_select_function(self._controlSelection)
        self.__selection_control = True
        if len(self.__liststore) > 0:
            self.__treeview.set_cursor_on_cell((0,),self.__unit_column,
                self.__unit_column.get_cell_renderers()[0],True)
        self.__treeview.grab_focus()
        self.__cursor = self.__treeview.get_cursor()
        # Show
        self._setColumnsHeaders()
        self.__scrolled_window.show()

    def _treeviewCursorChanged(self, treeview):
        """_treeviewCursorChanged(treeview)
        
        treeview: treewiew widget
        Method connected to "cursor-changed" signal
        The "cursor-changed" signal is emitted when the cursor moves or is set
        Sets the new cursor position in self.__cursor, it is used to avoid 
        unnecessary changes in cursor position.
        """
        event = gtk.get_current_event()
        (_cursor_path, _column) = treeview.get_cursor()
        if event is None or event.type !=  gtk.gdk.BUTTON_RELEASE:
            if not _column is self.__index_column:
                self.__cursor = treeview.get_cursor()

    def _treeviewClickedEvent(self, widget, event):
        """_treeviewClickedEvent(widget, event)
        
        widget: treewiew widget
        event: clicked event
        Method connected to "button-press-event" signal
        The "button-press-event" signal is emitted when a mouse button is
        pressed.
        Returns TRUE to stop other handlers from being invoked for the event.
        Returns FALSE to propagate the event further.
        
        The events in end column are ignored.
        If the user click in a row of the index column the cursor is moved to
        this row but not to the index column
        """
        if event.button == 1:
            path_at_pos = self.__treeview.get_path_at_pos(int(event.x),
                                                        int(event.y))
            if not path_at_pos is None: 
                _path_cursor, _column, _x, _y = path_at_pos
                if _column == self.columns[-1]:
                    return True
                if _column is self.columns[0]:
                    self.__cursor[0] == _path_cursor
        return False

    def _treeviewKeyPressEvent(self, widget, event):
        """_treeviewKeyPressEvent(widget, event)
        
        widget: treewiew widget
        event: Key Press event
        Method connected to "key-press-event" signal
        The "key-press-event" signal is emitted when the user presses a key
        on the keyboard.
        Returns :TRUE to stop other handlers from being invoked for the event.
        Returns :FALSE to propagate the event further.
        
        If the user press the right cursor button and the cursor is in the
        amount column or pres the left cursor button and the cursor is
        in the code column the event is estoped, else the event is propagated. 
        """
        (_cursor_path, _column) = self.__treeview.get_cursor()
        if (event.keyval == gtk.keysyms.Right \
            and _column == self.columns[-2]) \
            or (event.keyval == gtk.keysyms.Left \
            and _column == self.columns[1]):
            return True
        return False

    def _moveCursor(self, treeview, step, count):
        """_moveCursor(treeview, step, count)
        
        treeview: the treeview that received the signal
        step: the movement step size
        count: the number of steps to take
        
        Method connected to "move-cursor" signal
        The "move-cursor" signal is emitted when the user moves the cursor
        using the Right, Left, Up or Down arrow keys or the Page Up,
        Page Down, Home and End keys.
        
        Returns :TRUE if the signal was handled.
        """
        return False

    def _controlSelection(self, selection):
        """_controlSelection(selection)
        
        selection: treeselection
        
        Method connected to set_selection_function() 
        This method is called before any node is selected or unselected,
        giving some control over which nodes are selected.
        The selection function should return TRUE if the state
        of the node may be toggled, and FALSE if the state of the node should
        be left unchanged.
        
        The selection only run if the user click in the index column, else
        the previous selection is erased.
        """
        _column = self.__treeview.get_cursor()[1]
        if _column is self.columns[0] \
            or self.__selection_control == False:
            return True
        else:
            self.__selection_control = False
            self.__treeselection.unselect_all()
            self.__selection_control = True
            return False

    def _selectAll(self, column):
        """_selectAll(column)
        
        column: index column
        Method connected to "clicked" event in the index column
        If the user clickes in the index column header selecs or deselects 
        all rows
        """
        (_model, _pathlist) = self.__treeselection.get_selected_rows()
        # it avoid to set cursor in the index column
        self.__treeview.set_cursor(self.__cursor[0], self.__cursor[1])
        self.__selection_control = False
        if len(_pathlist) == 0:
            # select all
            self.__treeselection.select_all()
        else:
            # unselect all
            self.__treeselection.unselect_all()
        self.__selection_control = True

    def _setColumnsHeaders(self):
        """_setColumnsHeaders()
        
        Sets the headers column values
        """
        _path_record = self.__active_path_record
        _number = _path_record[-1]
        _budget = self.__budget
        _code = _budget.getCode(_path_record)
        _decomposition = _budget.getDecomposition(_path_record)
        _stryield = _budget.getStrYield(_decomposition.budgetMeasures[0],
                                        _budget.getRecord(_code).recordType)
        _record = _budget.getRecord(_code)
        _unit = _record.unit
        _description = _record.summary
        _price = _budget.getStrPriceFromRecord(self.budget.getActiveTitle(),
                                               _record)
        # TODO: round to decimal places in amount
        _amount = float(_stryield) * float(_price)
        if len(_path_record) == 1: # root record
            _amount = _price
        else:
            _parent_code = self.budget.getCode(self.__active_path_record[:-1])
            _parent_record = self.__budget.getRecord(_parent_code)
            _amount = _budget.getStrAmount(self.__active_path_record)
        
        self.__code_column.set_title(_("Code") + chr(10) + "[" + _code + "]")
        self.__unit_column.set_title(_("Unit") + chr(10) + "[" + _unit + "]")
        self.__description_column.set_title(
           _("Description") + chr(10) + "[" + _description + "]")
        self.__measure_column.set_title(
            _("Measure") + chr(10) + "[" + _stryield + "]")
        self.__price_column.set_title(
            _("Price") + chr(10) + "[" + _price + "]")
        self.__amount_column.set_title(
            _("Amount") + chr(10) + "[" + str(_amount) + "]")

    def _setListstoreValues(self, path_record):
        """_setListstoreValues(path_record)
        
        path_record: Record path in the budget
        Sets the liststore record values from a path record
        """
        self.__liststore.clear()
        _budget = self.__budget
        if not _budget.hasPath(path_record):
            raise ValueError, _("Invalid path")
        else:
            _parent_code = _budget.getCode(path_record)
            for N,_code in enumerate(_budget.getchildren(_parent_code)):
                _decomposition = _budget.getNDecomposition(_parent_code, N)
                _record = _budget.getRecord(_code)
                _values = [_record,
                           #_record.hierarchy,
                           #_record.type,
                           #_record.subtype,
                           #_code,
                           #_record.unit,
                           #_record.summary,
                           #_decomposition.yield_,
                           #_decomposition.budget[0].yield_,
                           #_record.prices[_budget.getActiveTitle()].prices]
                           #_record.getPrice(_budget.getActiveTitle())
                           ]
                _treeiter = self.__liststore.append(_values)

    def _colorCell(self, column, cell_renderer, tree_model, iter, lcolor):
        """_colorCell(column, cell_renderer, tree_model, iter, lcolor)
        
        column: the gtk.TreeViewColumn in the treeview
        cell_renderer: a gtk.CellRenderer
        tree_model: the gtk.TreeModel
        iter: gtk.TreeIter pointing at the row
        lcolor: list with 2 gtk colors for even and uneven record
        
        Method connected to "set_cell_data_func" of many column
        The set_cell_data_func() method sets the data function (or method) 
        to use for the column gtk.CellRenderer specified by cell_renderer.
        This function (or method) is used instead of the standard attribute
        mappings for setting the column values, and should set the attributes
        of the cell renderer as appropriate. func may be None to remove the
        current data function. The signature of func is:
        -def celldatafunction(column, cell, model, iter, user_data)
        -def celldatamethod(self, column, cell, model, iter, user_data)
        where column is the gtk.TreeViewColumn in the treeview, cell is the
        gtk.CellRenderer for column, model is the gtk.TreeModel for the
        treeview and iter is the gtk.TreeIter pointing at the row.
        
        The method sets cell background color and text for all columns.
        """
        _row_path = tree_model.get_path(iter)
        _number = _row_path[-1]
        _record = tree_model[_row_path][0]
        if column is self.__index_column:
            cell_renderer.set_property('text', str(_number + 1))
            self.__index_column.get_cell_renderers()[1].set_property(
                'cell-background-gdk', lcolor[_number % 2])
        elif column is self.__code_column:
            # if the record is a chapter
            if tree_model.get_value(iter, 0).recordType.hierarchy == 1: 
                lcolor = self.__chapter_background_colors
            _code = _record.code
            cell_renderer.set_property('text', _code)
        elif column is self.__unit_column:
            _unit = _record.unit
            cell_renderer.set_property('text', _unit)
        elif column is self.__description_column:
            _summary = _record.summary
            cell_renderer.set_property('text', _summary)
        elif column is self.__measure_column:
            _parent_code = self.budget.getCode(self.__active_path_record)
            _parent_record = self.__budget.getRecord(_parent_code)
            _decomposition = _parent_record.children[_number]
            _stryield = self.__budget.getStrYield(
                _decomposition.budgetMeasures[0], _parent_record.recordType)
            cell_renderer.set_property('text', _stryield)
        elif column is self.__price_column:
            _price = self.budget.getStrPriceFromRecord(
                       self.budget.getActiveTitle(), _record)
            cell_renderer.set_property('text', _price)
        elif column is self.__amount_column:
            _parent_code = self.budget.getCode(self.__active_path_record)
            _parent_record = self.__budget.getRecord(_parent_code)
            _amount = self.budget.getStrAmount(
                        self.__active_path_record + (_number,))
            cell_renderer.set_property('text', str(_amount))
        elif column is self.__type_column:
            _hierarchy = tree_model[_row_path][0].recordType.hierarchy
            _type = tree_model[_row_path][0].recordType.type
            _subtype = tree_model[_row_path][0].recordType.subtype
            if _hierarchy == 1:
                cell_renderer.set_property("pixbuf",self.__chapter_icon)
            else:
                if _type == 0:
                    cell_renderer.set_property("pixbuf",self.__unit_icon)
                elif _type == 1:
                    cell_renderer.set_property("pixbuf",
                        self.__labourforce_icon)
                elif _type == 2:
                    cell_renderer.set_property("pixbuf",
                        self.__machinery_icon)
                else:
                    cell_renderer.set_property("pixbuf",self.__material_icon)
        if self.__treeview.get_cursor() == (_row_path,column):
            cell_renderer.set_property('cell-background-gdk',
                gtk.gdk.color_parse(globalVars.color["ACTIVE"]))
        else:
            cell_renderer.set_property('cell-background-gdk',
                lcolor[_number % 2])

    def _showParentRecord(self, column):
        """_showParentRecord(column)
        
        column: the column that is clicked
        Method connected to "clicked" event of many columns
        Show the parent record
        """
        _budget = self.__budget
        if len(self.__active_path_record) == 1:
            # The active record is the root record
            # This avoid to move the cursor to the clicked column
            self.__treeview.set_cursor(self.__cursor[0], self.__cursor[1])
        else:
            _path_record = self.__active_path_record[:-1]
            _parent = self.__active_path_record[-1]
            self.__active_path_record = _path_record
            self._setColumnsHeaders()
            self._setListstoreValues(self.__active_path_record)
            arg = ( _path_record )
            _page = self.__page()
            _page.propagateMessageFrom("change_active", self.__pane_path, arg)
            self.__treeview.set_cursor(_parent, self.__cursor[1])
            self.__cursor = self.__treeview.get_cursor()

    def _showMessageRecord(self, record_path):
        """_showMessageRecord(record_path)
        
        record_path: the path of  the record to show
        Method connected to "change_active" message
        Show the record especified in the "change_active" message
        """
        _budget = self.__budget
        self.__active_path_record = record_path
        self._setColumnsHeaders()
        self._setListstoreValues(self.__active_path_record)
        self.__treeview.set_cursor((0,))

    def _showRowRecord(self, treeview, treeview_path, column):
        """_showRowRecord(treeview, treeview_path, column)
        
        treeview: treview to show
        treeview_path: the path of the record to show
        code: the code of the record to show
        
        Method connected to "row-activated" event
        The "row-activated" signal is emitted when the row_activated() method
        is called or the user double clicks a treeview row.
        "row-activated" is also emitted when a non-editable row is selected
        and one of the keys: Space, Shift+Space, Return or Enter is pressed.
        Show the especified record
        """
        if not (column is self.__end_column) and \
           not (column is self.__index_column):
            _budget = self.__budget
            _model = treeview.get_model()
            _iter = _model.get_iter(treeview_path)
            _code = _model.get_value(_iter, 0).code
            #_code = _model.get_value(_iter, 4)
            _path_record = self.__active_path_record + treeview_path
            if self.__budget.hasPath(_path_record):
                # if this record path is valid
                self.__active_path_record = _path_record
                self._setColumnsHeaders()
                self._setListstoreValues(self.__active_path_record)
                self.__treeview.set_cursor((0,))
                _arg = ( _path_record )
                _page = self.__page()
                _page.propagateMessageFrom("change_active", self.__pane_path,
                                       _arg )

    def runMessage(self, message, pane_path, arg=None):
        """runMessage(message, pane_path, arg=None)
        
        message: the message type
            "change_active": change the active record
            "clear": clear instance
        pane_path: tuple that identifies the pane in the notebook page
        arg: tuple whit two items:
            0: record path in the budget
            1: record code
        This method receives a message and executes its corresponding action
        """
        _budget = self.__budget
        if message == "change_active":
            if _budget.hasPath(arg):
                _path_record = arg
                self._showMessageRecord( _path_record)
        elif message == "clear":
            self._clear()

    def _clear(self):
        """_clear()
        
        it deletes the __budget reference
        """
        del self.__budget 

    def _getWidget(self):
        """_getWidget()
        
        return the main widget (gtk.ScrolledWindow)
        """
        return self.__scrolled_window

    def _getPanePath(self):
        """_getPanePath()
        
        return the tuple that identifies the pane in the notebook page
        """
        return self.__pane_path

    def _setPanePath(self, pane_path):
        """_setPanePath()
        
        sets the tuple that identifies the pane in the notebook page
        """
        self.__pane_path = pane_path

    def _getPage(self):
        """_getPage()
        
        return the Page
        """
        return self.__page

    def _setPage(self,page):
        """_setPage()
        
        set the Page
        """
        self.__page = page

    def _getBudget(self):
        """_getBudget()
        
        return the Budget objet
        """
        return self.__budget

    def _getActivePathRecord(self):
        """_getActivePathRecord()
        
        return the Active Path Record
        """
        return self.__active_path_record

    widget = property(_getWidget, None, None,
        "Pane configuration list")
    pane_path = property(_getPanePath, _setPanePath, None,
        "path that identifie the item in the page notebook")
    page = property(_getPage, _setPage, None,
        "weak reference from Page instance which creates this class")
    budget =  property(_getBudget, None, None,
        "Budget object")
    active_path_record =  property(_getActivePathRecord, None, None,
        "Active path record")


class Measure(TreeView):
    """gui.Measure:
    
    Description:
        Class to show a Measure List
    Constructor:
        Measure(budget, page, pane_path, path_record=(0,)
        budget: budget showed ("base.Budget" object)
        page: weak reference from Page instance which creates this class
        pane_path: tuple that represents the path of the List in the Page
        path_record: path of the active record in the budget
    Ancestry:
    +-- object
      +-- TreeView
        +-- DecompositionList
    Atributes:
        budget: Read. Budget to show, base.obra instance.
        widget: Read. Window that contains the table, gtk.ScrolledWindow
        pane_path: Read-Write. Pane page identifier
        page: Read-Write. weak reference from Page instance which creates
              this class
        active_path_record: Read. Path of the active record in the budget
    Methods:
        runMessage
    """

    def __init__(self, budget, page, pane_path, path_record=None):
        """__init__(budget, page, pane_path, path_record=None)
        
        budget: budget: budget showed ("base.Budget" object)
        page: weak reference from Page instance which creates this class
        pane_path: tuple that represents the path of the List in the Page
        path_record: path of the active record in the budget
        
        self.__budget: budget showed ("base.Budget" object)
        self.__page: weak reference from Page instance which creates this class
        self.__pane_path: tuple that represents the path of the List in the Page
        self.__active_path_record: path of the active record in the budget
        self.__liststore: list model which store the list data
            (gtk.ListStore object)
        self.__treeview:  widget to display decomposition lists
            (gtk.TreeView)
        self.__scrolled_window: widget to scroll the treeview
            gtk.ScrolledWindow()
        self.__chapter_background_colors: The background colors of the Code
            column cells when there is a chapter record
            as a list of gtk.gdk.Color objects [even cell, uneven cell]
        self.__index_column: Index column (gtk.TreeViewColumn object)
        self.__linetype_column: Linetype column (gtk.TreeViewColumn object)
        self.__comment_column: Comment column (gtk.TreeViewColumn)
        self.__unit_column: Unit column (gtk.TreeViewColumn)
        self.__length_column: Legth column (gtk.TreeViewColumn)
        self.__width_column: With column (gtk.TreeViewColumn)
        self.__height_column: Height column (gtk.TreeViewColumn)
        self.__formula_column: Formula column (gtk.TreeViewColumn)
        self.__parcial_column: Parcial column (gtk.TreeViewColumn)
        self.__subtotal_column: Subtotal column (gtk.TreeViewColumn)
        self.__end_column: End empty column (gtk.TreeViewColumn
        self.__calculatedline_icon: gtk.gdk.pixbuf
        self.__normalline_icon: gtk.gdk.pixbuf
        self.__parcialline_icon: gtk.gdk.pixbuf
        self.__acumulatedline_icon: gtk.gdk.pixbuf
        self.__treeselection: active selection
        self.__selection_control: state of the selection control (True/False)
        self.__cursor: Situation of the cursor in the table
        
        Sets the init atributes
        Creates the init list values in self.__liststore from the budget 
            showing the top record from the record with path path_record
        Creates the list in self.__treeview
            * Creates the columns and cell
            * Sets te the column headers values
            * Sets the selection properties
            * Connects the events
        """
        # Seting init args
        if path_record is None:
            path_record = (0,)
        if not isinstance(budget, base.Budget):
            raise ValueError, _("Argument must be a Budget object")
        self.__budget = budget
        self.__page = page
        self.__pane_path = pane_path
        if not isinstance(path_record, tuple):
            print _("Record path must be a tuple")
            path_record = (0,)
        self.__active_path_record = path_record
        # ListStore
        self.__liststore = gtk.ListStore(object)
        self._setListstoreValues(self.__active_path_record)
        # Treeview
        self.__treeview = gtk.TreeView(self.__liststore)
        self.__treeview.set_enable_search(False)
        self.__treeview.set_reorderable(False)
        self.__treeview.set_headers_clickable(True)
        self.__treeview.show()
        # Scrolled_window
        self.__scrolled_window = gtk.ScrolledWindow()
        self.__scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
            gtk.POLICY_AUTOMATIC)
        self.__scrolled_window.add(self.__treeview)
        # colors
        _text_color = gtk.gdk.color_parse(globalVars.color["TEXT"])
        _calculated_text =gtk.gdk.color_parse(globalVars.color["CALCULATED-TEXT"])
        _background_color = [
            gtk.gdk.color_parse(globalVars.color["UNEVEN"]),
            gtk.gdk.color_parse(globalVars.color["EVEN"])]
        self.__chapter_background_colors = [
            gtk.gdk.color_parse(globalVars.color["CHAPTER-UNEVEN"]),
            gtk.gdk.color_parse(globalVars.color["CHAPTER-EVEN"])]
        super(Measure,self).__init__(
            [("INDEX",self._selectAll,42),
            ("PIXBUF", self._passMethod,
             gtk.Label("A"*4).size_request()[0] +10,
             _text_color, _background_color),
            ("CALCULATEDTEXT", self._passMethod, 
             gtk.Label("A"*12).size_request()[0] +10,
             _text_color, _background_color),
            ("CALCULATED", self._passMethod, 
             gtk.Label("A"*5).size_request()[0] +10,
             _text_color, _background_color),
            ("CALCULATED", self._passMethod, 
             gtk.Label("A"*7).size_request()[0] +10,
             _text_color, _background_color),
            ("CALCULATED", self._passMethod, 
             gtk.Label("A"*7).size_request()[0] +10,
             _text_color, _background_color),
            ("CALCULATED", self._passMethod, 
             gtk.Label("A"*7).size_request()[0] +10,
             _text_color, _background_color),
            ("CALCULATEDTEXT", self._passMethod, 
             gtk.Label("A"*12).size_request()[0] +10,
             _text_color, _background_color),
            ("CALCULATED", self._passMethod, 
             gtk.Label("A"*7).size_request()[0] +10,
             _calculated_text, _background_color),
            ("CALCULATED", self._passMethod, 
             gtk.Label("A"*7).size_request()[0] +10,
             _calculated_text, _background_color),
            ])
        # Colums
        self.__index_column = self.columns[0]
        self.__linetype_column = self.columns[1]
        self.__comment_column = self.columns[2]
        self.__units_column = self.columns[3]
        self.__length_column = self.columns[4]
        self.__width_column = self.columns[5]
        self.__height_column = self.columns[6]
        self.__formula_column = self.columns[7]
        self.__parcial_column = self.columns[8]
        self.__subtotal_column = self.columns[9]
        self.__end_column = self.columns[10]
        # Index column
        self.__treeview.append_column(self.__index_column)
        # Linetype column
        self.__treeview.append_column(self.__linetype_column)
        self.__calculatedline_icon = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("CALCULATEDLINE-ICON"))
        self.__normalline_icon = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("NORMALLINE-ICON") )
        self.__parcialline_icon  = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("PARCIALLINE-ICON") )
        self.__acumulatedline_icon = gtk.gdk.pixbuf_new_from_file(
            globalVars.getAppPath("ACUMULATEDLINE-ICON"))
        # Comment column
        self.__treeview.append_column(self.__comment_column)
        # Units column
        self.__treeview.append_column(self.__units_column)
        # Length column
        self.__treeview.append_column(self.__length_column)
        # Width_column
        self.__treeview.append_column(self.__width_column)
        # Height column
        self.__treeview.append_column(self.__height_column)
        # Formula column
        self.__treeview.append_column(self.__formula_column)
        # Parcial column
        self.__treeview.append_column(self.__parcial_column)
        # Subtotal column
        self.__treeview.append_column(self.__subtotal_column)
        # End Column
        self.__treeview.append_column(self.__end_column)
        # Connect
        self.__treeview.connect("move-cursor", self._moveCursor)
        self.__treeview.connect("key-press-event", self._treeviewKeyPressEvent)
        self.__treeview.connect("button-press-event",
            self._treeviewClickedEvent)
        self.__treeview.connect("cursor-changed", self._treeviewCursorChanged)
        # control selection
        self.__treeselection = self.__treeview.get_selection()
        self.__treeselection.set_mode(gtk.SELECTION_MULTIPLE)
        self.__treeselection.set_select_function(self._controlSelection)
        self.__selection_control = True
        self.__treeview.set_cursor_on_cell((1,), self.columns[1],
            self.columns[1].get_cell_renderers()[0],True)
        self.__treeview.grab_focus()
        self.__cursor = self.__treeview.get_cursor()
        # Show
        self._setColumnsHeaders()
        self.__scrolled_window.show()

    def _passMethod(self, column):
        """_passMethod(column)
        
        column: the column that is clicked
        Method connected to "clicked" event of many columns
        Do nothing
        """
        pass

    def _setListstoreValues(self, path_record):
        """_setListstoreValues(path_record)
        
        path_record: Record path in the budget
        Sets the liststore record values from a path record
        """
        self.__liststore.clear()
        _budget = self.__budget
        if not _budget.hasPath(path_record):
            raise ValueError, _("Invalid path")
        else:
            _measure = _budget.getMeasure(path_record)
            if isinstance(_measure, base.Measure):
                _lines = _measure.lines
                for _line in _lines:
                    _values = [ _line ]
                    _treeiter = self.__liststore.append(_values)
            else:
                raise ValueError, utils.mapping(_("measure must be a Measure "\
                      "object. Type: $1"), (type(_measure),))

    def _setColumnsHeaders(self):
        """_setColumnsHeaders()
        
        Sets the headers column values
        """
        _measure = self.__budget.getMeasure(self.__active_path_record)
        _DS = self.__budget.getDecimals("DS")
        _total = _measure.measure
        _total_str = ("%." + str(_DS) + "f" ) % _total
        self.columns[1].set_title(_("Type"))  # Σ parcial Σ total
        self.columns[2].set_title(_("Comment"))
        self.columns[3].set_title(_("N\n(a)"))
        self.columns[4].set_title(_("Length\n(b)"))
        self.columns[5].set_title(_("Width\n(c)"))
        self.columns[6].set_title(_("Height\n(d)"))
        self.columns[7].set_title(_("Formula"))
        self.columns[8].set_title(_("Parcial\n[%s]" % _total_str))
        self.columns[9].set_title(_("Subtotal"))

    def _controlSelection(self, selection):
        """_controlSelection(selection)
        
        selection: treeselection
        
        Method connected to set_selection_function() 
        This method is called before any node is selected or unselected,
        giving some control over which nodes are selected.
        The selection function should return TRUE if the state
        of the node may be toggled, and FALSE if the state of the node should
        be left unchanged.
        
        The selection only run if the user click in the index column, else
        the previous selection is erased.
        """
        _column = self.__treeview.get_cursor()[1]
        if _column is self.columns[0] \
            or self.__selection_control == False:
            return True
        else:
            self.__selection_control = False
            self.__treeselection.unselect_all()
            self.__selection_control = True
            return False 

    def _showMessageRecord(self, record_path):
        """_showMessageRecord(record_path)
        
        record_path: the path of the record to show
        Method connected to "change_active" message
        Show the record especified in the "change_active" message
        """
        _budget = self.__budget
        self.__active_path_record = record_path
        self._setColumnsHeaders()
        self._setListstoreValues(self.__active_path_record)
        self.__treeview.set_cursor((0,))

    def _treeviewCursorChanged(self, treeview):
        """_treeviewCursorChanged(treeview)
        
        treeview: treewiew widget
        Method connected to "cursor-changed" signal
        The "cursor-changed" signal is emitted when the cursor moves or is set
        Sets the new cursor position in self.__cursor, it is used to avoid 
        unnecessary changes in cursor position.
        """
        event = gtk.get_current_event()
        (_cursor_path, _column) = treeview.get_cursor()
        if event is None or event.type !=  gtk.gdk.BUTTON_RELEASE:
            if not _column is self.__index_column:
                self.__cursor = treeview.get_cursor()

    def _moveCursor(self, treeview, step, count):
        """moveCursor(treeview, step, count)
        
        treeview: the treeview that received the signal
        step: the movement step size
        count: the number of steps to take
        
        Method connected to "move-cursor" signal
        The "move-cursor" signal is emitted when the user moves the cursor
        using the Right, Left, Up or Down arrow keys or the Page Up,
        Page Down, Home and End keys.
        
        Returns :TRUE if the signal was handled.
        """
        return False

    def _treeviewClickedEvent(self, widget, event):
        """_treeviewClickedEvent(widget, event)
        
        widget: treewiew widget
        event: clicked event
        Method connected to "button-press-event" signal
        The "button-press-event" signal is emitted when a mouse button is
        pressed.
        Returns TRUE to stop other handlers from being invoked for the event.
        Returns FALSE to propagate the event further.
        
        The events in end column are ignored.
        If the user click in a row of the index column the cursor is moved to
        this row but not to the index column
        """
        if event.button == 1:
            path_at_pos = self.__treeview.get_path_at_pos(int(event.x),
                                                        int(event.y))
            if not path_at_pos is None: 
                _path_cursor, _column, _x, _y = path_at_pos
                if _column == self.columns[-1]:
                    return True
                if _column is self.columns[0]:
                    self.__cursor[0] == _path_cursor
        return False

    def _treeviewKeyPressEvent(self, widget, event):
        """_treeviewKeyPressEvent(widget, event)
        
        widget: treewiew widget
        event: Key Press event
        Method connected to "key-press-event" signal
        The "key-press-event" signal is emitted when the user presses a key
        on the keyboard.
        Returns :TRUE to stop other handlers from being invoked for the event.
        Returns :FALSE to propagate the event further.
        
        If the user press the right cursor button and the cursor is in the
        amount column or pres the left cursor button and the cursor is
        in the code column the event is estoped, else the event is propagated. 
        """
        (_cursor_path, _column) = self.__treeview.get_cursor()
        if (event.keyval == gtk.keysyms.Right \
            and _column == self.columns[-2]) \
            or (event.keyval == gtk.keysyms.Left \
            and _column == self.columns[1]):
            return True
        return False

    def runMessage(self, message, pane_path, arg=None):
        """runMessage(message, pane_path, arg=None)
        
        message: the message type
            "change_active": change the active record
            "clear": clear instance
        pane_path: tuple that identifies the pane in the notebook page
        arg: tuple whit two items:
            0: record path in the budget
            1: record code
        This method receives a message and executes its corresponding action
        """
        _budget = self.__budget
        if message == "change_active":
            if _budget.hasPath(arg):
                _path_record = arg
                self._showMessageRecord( _path_record)
        elif message == "clear":
            self._clear()

    def _selectAll(self, column):
        """_selectAll(column)
        
        column: index column
        Method connected to "clicked" event in the index column
        If the user clickes in the index column header selecs or deselects 
        all rows
        """
        (_model, _pathlist) = self.__treeselection.get_selected_rows()
        # it avoid to set cursor in the index column
        self.__treeview.set_cursor(self.__cursor[0], self.__cursor[1])
        self.__selection_control = False
        if len(_pathlist) == 0:
            # select all
            self.__treeselection.select_all()
        else:
            # unselect all
            self.__treeselection.unselect_all()
        self.__selection_control = True

    def _colorCell(self, column, cell_renderer, tree_model, iter, lcolor):
        """_colorCell(column, cell_renderer, tree_model, iter, lcolor)
        
        column: the gtk.TreeViewColumn in the treeview
        cell_renderer: a gtk.CellRenderer
        tree_model: the gtk.TreeModel
        iter: gtk.TreeIter pointing at the row
        lcolor: list with 2 gtk colors for even and uneven record
        
        Method connected to "set_cell_data_func" of many column
        The set_cell_data_func() method sets the data function (or method) 
        to use for the column gtk.CellRenderer specified by cell_renderer.
        This function (or method) is used instead of the standard attribute
        mappings for setting the column values, and should set the attributes
        of the cell renderer as appropriate. func may be None to remove the
        current data function. The signature of func is:
        -def celldatafunction(column, cell, model, iter, user_data)
        -def celldatamethod(self, column, cell, model, iter, user_data)
        where column is the gtk.TreeViewColumn in the treeview, cell is the
        gtk.CellRenderer for column, model is the gtk.TreeModel for the
        treeview and iter is the gtk.TreeIter pointing at the row.
        
        The method sets cell background color for all columns
        and text for index and amount columns.
        """
        _row_path = tree_model.get_path(iter)
        _number = _row_path[-1]
        if column is self.__index_column:
            cell_renderer.set_property('text', str(_number + 1))
            self.__index_column.get_cell_renderers()[1].set_property(
                'cell-background-gdk', lcolor[_number % 2])
        elif column is self.__linetype_column:
            _measure = tree_model[_row_path][0]
            _type = _measure.lineType
            if _type == 0:
                cell_renderer.set_property("pixbuf",self.__normalline_icon)
            elif _type == 1:
                cell_renderer.set_property("pixbuf",self.__parcialline_icon)
            elif _type == 2:
                cell_renderer.set_property("pixbuf",
                        self.__acumulatedline_icon)
            else: #elif _type == 3:
                cell_renderer.set_property("pixbuf",
                        self.__calculatedline_icon)
                
        elif column is self.__comment_column:
            _measure = tree_model[_row_path][0]
            _comment = str(_measure.comment)
            cell_renderer.set_property('text', _comment)
        elif column is self.__units_column:
            _measure = tree_model[_row_path][0]
            _units = _measure.units
            if isinstance(_units, float):
                _DN = self.__budget.getDecimals("DN")
                _units = ("%." + str(_DN) + "f" ) % _units
            cell_renderer.set_property('text', _units)
        elif column is self.__length_column:
            _measure = tree_model[_row_path][0]
            _length = _measure.length
            if isinstance(_length, float):
                _DD = self.__budget.getDecimals("DD")
                _length = ("%." + str(_DD) + "f" ) % _length
            cell_renderer.set_property('text', _length)
        elif column is self.__width_column:
            _measure = tree_model[_row_path][0]
            _width = _measure.width
            if isinstance(_width, float):
                _DD = self.__budget.getDecimals("DD")
                _width = ("%." + str(_DD) + "f" ) % _width
            cell_renderer.set_property('text', _width)
        elif column is self.__height_column:
            _measure = tree_model[_row_path][0]
            _height = _measure.height
            if isinstance(_height, float):
                _DD = self.__budget.getDecimals("DD")
                _height = ("%." + str(_DD) + "f" ) % _height
            cell_renderer.set_property('text', _height)
        elif column is self.__formula_column:
            _measure = tree_model[_row_path][0]
            _formula = _measure.formula
            cell_renderer.set_property('text', _formula)
        elif column is self.__parcial_column:
            _measure_line = tree_model[_row_path][0]
            _parcial = _measure_line.parcial
            _type = _measure_line.lineType
            if _type == 1 or _type == 2:
                _parcial = ""
            else:
                if isinstance(_parcial, float):
                    _DS = self.__budget.getDecimals("DS")
                    _parcial = ("%." + str(_DS) + "f" ) % _parcial
            cell_renderer.set_property('text', _parcial)
        elif column is self.__subtotal_column:
            _measure_line = tree_model[_row_path][0]
            _type = _measure_line.lineType
            if _type == 1 or _type == 2:
                if _type == 1:
                    _color = gtk.gdk.color_parse(
                               globalVars.color["SUBTOTAL-PARCIAL"])
                    _subtotal = _measure_line.parcial_subtotal
                else: #elif _type == 2:
                    _color = gtk.gdk.color_parse(globalVars.color["SUBTOTAL"])
                    _subtotal = _measure_line.acumulated_subtotal
                lcolor = [_color, _color]
                if isinstance(_subtotal, float):
                    _DS = self.__budget.getDecimals("DS")
                    _subtotal= ("%." + str(_DS) + "f" ) % _subtotal
                cell_renderer.set_property('text', _subtotal)
            else:
                cell_renderer.set_property('text', "")

        if self.__treeview.get_cursor() == (_row_path,column):
            cell_renderer.set_property('cell-background-gdk',
                gtk.gdk.color_parse(globalVars.color["ACTIVE"]))
        else:
            cell_renderer.set_property('cell-background-gdk',
                lcolor[_number % 2])

    def _clear(self):
        """_clear()
        
        it deletes the __budget value
        """
        del self.__budget

    def _getWidget(self):
        """_getWidget()
        
        return the main widget (gtk.ScrolledWindow)
        """
        return self.__scrolled_window

    def _getPanePath(self):
        """_getPanePath()
        
        return the tuple that identifies the pane in the notebook page
        """
        return self.__pane_path

    def _setPanePath(self, pane_path):
        """_setPanePath()
        
        sets the tuple that identifies the pane in the notebook page
        """
        self.__pane_path = pane_path

    def _getPage(self):
        """_getPage()
        
        return the Page
        """
        return self.__page

    def _setPage(self,page):
        """_setPage()
        
        set the Page
        """
        self.__page = page

    def _getBudget(self):
        """_getBudget()
        
        return the Budget objet
        """
        return self.__budget

    def _getActivePathRecord(self):
        """getActivePathRecord()
        
        return the Active Path Record
        """
        return self.__active_path_record

    widget = property(_getWidget, None, None,
        "Pane configuration list")
    pane_path = property(_getPanePath, _setPanePath, None,
        "Path that identifies the item in the page notebook")
    page = property(_getPage, _setPage, None,
        "Weak reference from Page instance which creates this class")
    budget =  property(_getBudget, None, None,
        "Budget object")
    active_path_record =  property(_getActivePathRecord, None, None,
        "Active Code")


class Description(object):
    """gui.Description
    
    Description:
        Class to show a description text of a record in a pane
    Constructor:
        Description(budget, code)
        budget: base.Budget object
        code: record code
    Ancestry:
    +-- object
      +-- Description
    Atributes:
        widget: the main widget (gtk.ScrolledWindow object)
        pane_path: the tuple that identifies the pane in the notebook page
        budget: The budget (base.obra objetc)
        active_path_record: The active path record
    Methods:
        runMessage
    """
    # TODO: make standar: "DecompositonList and Description"

    def __init__(self, budget, page, pane_path, path_record=None):
        """__init__(budget, page, pane_path, path_record=None)
        
        budget: the budget (base.obra object)
        page: weak reference from Page instance which creates this class
        pane_path: the path position of the description in the page
        path_record: the path of the active record
        
        self.__budget: the budget (base.obra object)
        self.__page: weak reference from Page instance which creates this class
        self.__pane_path: the path position of the description in the page
        self.__active_path_recordthe path of the active record

        self.__textbuffer: The textbuffer of the textview that contain
            the record text.
        self.__label: The gtk.label with the title of the pane
        self.__widget: the main pane widget, a gtk.ScrolledWindow()
        
        Creates an shows the scroledwindow that contain the description text
        of the record to be showed in a pane.
        """
        if path_record is None:
            path_record = (0,)
        self.__budget = budget
        self.__page = page
        self.__pane_path = pane_path
        self.__active_path_record = path_record
        _budget = budget
        _text = _budget.getRecord(self.__budget.getCode(
                self.__active_path_record)).text
        _scrollwindow = gtk.ScrolledWindow()
        _scrollwindow.set_policy(gtk.POLICY_AUTOMATIC,
                                 gtk.POLICY_AUTOMATIC)
        _textview = gtk.TextView()
        _textview.set_wrap_mode(gtk.WRAP_WORD)
        self.__textbuffer = _textview.get_buffer()
        self.__textbuffer.set_text(_text)
        _textview.show()
        _hbox = gtk.HBox()
        _hbox.pack_start(_textview, True, True, 5)
        _hbox.show()
        _vbox = gtk.VBox()
        self.__label = gtk.Label(utils.mapping(_("Description text of the "\
                     "record $1"), (self.__budget.getCode(
                    self.__active_path_record),)))
        self.__label.set_alignment(0, 0)
        self.__label.show()
        _vbox.pack_start(self.__label, False, False, 5)
        _vbox.pack_start(_hbox, True, True, 5)
        _vbox.show()
        _scrollwindow.add_with_viewport(_vbox)
        _scrollwindow.show()
        self.__widget = _scrollwindow


    def _setActivePathRecord(self, path_record):
        """_setActivePathRecord(path_record))
        
        path_record: active path record
        Set the new path code to show its description text.
        """
        _budget = self.__budget
        self.__active_path_record = path_record
        _code = _budget.getCode(self.__active_path_record)
        self.__label.set_text(utils.mapping(_("Description text of the record "\
            "$1"), (_code,)))
        _text = _budget.getRecord(_code).text
        self.__textbuffer.set_text(_text)

    def runMessage(self, message, pane_path, arg=None):
        """runMessage(message, pane_path, arg=None)
        
        message: the message type
            "change_active": change the active record
            "clear": clear instance
        pane_path: tuple that identifies the pane in the notebook page
        arg: tuple whit two items:
            0: record path in the budget
            1: record code
        This method receives a message and executes its corresponding action
        """
        _budget = self.__budget
        if message == "change_active":
            if _budget.hasPath(arg):
                self._setActivePathRecord(arg)
        elif message == "clear":
            self._clear()

    def _clear(self):
        """_clear()
        
        Delete all instance atributes
        """
        del self.__widget
        del self.__pane_path
        del self.__budget
        del self.__active_code
        del self.__textbuffer
        del self.__label

    def _getWidget(self):
        """_getWidget()
        
        return the main widget (gtk.ScrolledWindow)
        """
        return self.__widget

    def _getPanePath(self):
        """_getPanePath()
        
        return the tuple that identifies the pane in the notebook page
        """
        return self.__pane_path

    def _setPanePath(self, pane_path):
        """_setPanePath()
        
        sets the tuple that identifies the pane in the notebook page
        """
        self.__pane_path = pane_path

    def _getPage(self):
        """_getPage()
        
        return the weak reference from Page instance
        """
        return self.__page

    def _setPage(self, page):
        """_setPage()
        
        set the weak reference from Page instance
        """
        self.__page = page

    def _getBudget(self):
        """_getBudget()
        
        return the budget object
        """
        return self.__budget

    def _getActivePathRecord(self):
        """_getActivePathRecord()
        
        return the Active Path Record
        """
        return self.__active_path_record

    pane_path = property(_getPanePath, _setPanePath, None,
        "Path that identifie the item in the page notebook")
    widget = property(_getWidget, None, None,
        "The main widget (gtk.ScrolledWindow)")
    page = property(_getPage, _setPage, None,
        "Weak reference from Page instance which creates this class")
    budget = property(_getBudget, None, None,
        "Budget object")
    active_path_record = property(_getActivePathRecord, None, None,
        "Active Path Record")


class Sheet(object):
    """gui.Sheet
    
    Description:
        Class to show a sheeet of conditions text of a record in a pane
    Constructor:
        Sheet(budget, code)
        budget: budget object
        code: code record
    Ancestry:
    +-- object
      +-- Sheet
    Atributes:
        widget: the main widget (gtk.VBox() object)
        pane_path: the tuple that identifies the pane in the notebook page
        page: weak reference from Page instance which creates this class
        budget: The budget (base.obra objetc)
        active_path_record: The active path record
    Methods:
        runMessage
    """

    def __init__(self, budget, page, pane_path, path_record=None):
        """__init__(budget, page, pane_path, path_record=None)
        
        budget: the budget (base.obra object)
        page: weak reference from Page instance which creates this class
        pane_path: the path position of the description in the page
        path_record: the path of the active record
        
        self.__budget: the budget (base.obra object)
        self.__page: weak reference from Page instance which creates this class
        self.__pane_path: the path position of the description in the page
        self.__active_path_record: the path of the active record
        self.__label: The gtk.label with the title of the pane
        self.__field_liststore: the field liststore
        self.__field_treeview: the field treeview
        self.__field_selection: the field selected in field treview
        self.__section_liststore: the section liststore
        self.__section_treeview: the section treeview
        self.__section_selection: the section selected in the section treeview
        self.__textbuffer: The textbuffer of the textview that contain
            the record text.
        self.__widget: main widget, a gtk.VBox()
        
        Creates an shows the scroledwindow that contain the description text
        of the record to be showed in a pane.
        """
        if path_record is None:
            path_record = (0,)
        self.__budget = budget
        self.__page = page
        self.__pane_path = pane_path
        self.__active_path_record = path_record
        _budget = budget
        _main_box = gtk.VBox()
        self.__label = gtk.Label(utils.mapping(_("Sheet of Conditions of the "\
                       "record $1"), (self.__budget.getCode(
                       self.__active_path_record),)))
        self.__label.set_alignment(0, 0)
        self.__label.show()
        _frame = gtk.Frame()
        _frame.set_shadow_type(gtk.SHADOW_IN)
        _frame_box = gtk.VBox()
        _list_box = gtk.HBox()
        self.__field_liststore = gtk.ListStore(str, str)
        self.__field_treeview = gtk.TreeView(self.__field_liststore)
        _field_treeselection = self.__field_treeview.get_selection()
        _field_treeselection.set_mode(gtk.SELECTION_SINGLE)
        self.__field_selection = None
        _field_treeselection.set_select_function(
            self._field_controlSelection)
        self.__field_treeview.show()
        _fieldcode_cell = gtk.CellRendererText()
        _field_column = gtk.TreeViewColumn(_("Field"))
        _field_column.pack_start(_fieldcode_cell, False)
        _field_cell = gtk.CellRendererText()
        _field_column.pack_end(_field_cell, True)
        _field_column.add_attribute(_fieldcode_cell, "text", 0)
        _field_column.add_attribute(_field_cell, "text", 1)
        self.__field_treeview.append_column(_field_column)
        _field_scrollwindow = gtk.ScrolledWindow()
        _field_scrollwindow.set_policy(gtk.POLICY_AUTOMATIC,
                                 gtk.POLICY_AUTOMATIC)
        _field_scrollwindow.add(self.__field_treeview)
        _field_scrollwindow.show()
        self.__section_liststore = gtk.ListStore(str, str)
        self.__section_treeview = gtk.TreeView(self.__section_liststore)
        _section_treeselection = self.__section_treeview.get_selection()
        _section_treeselection.set_mode(gtk.SELECTION_SINGLE)
        self.__section_selection = None
        _section_treeselection.set_select_function(
            self._section_controlSelection)
        self.__section_treeview.show()
        _sectioncode_cell = gtk.CellRendererText()
        _section_column = gtk.TreeViewColumn(_("Section"))
        _section_column.pack_start(_sectioncode_cell, False)
        _section_column.add_attribute(_sectioncode_cell, "text", 0)
        _section_cell = gtk.CellRendererText()
        _section_column.pack_end(_section_cell, True)
        _section_column.add_attribute(_section_cell, "text", 1)
        self.__section_treeview.append_column(_section_column)
        _section_scrollwindow = gtk.ScrolledWindow()
        _section_scrollwindow.set_policy(gtk.POLICY_AUTOMATIC,
                                 gtk.POLICY_AUTOMATIC)
        _section_scrollwindow.add(self.__section_treeview)
        _section_scrollwindow.show()
        
        _list_box.pack_start(_field_scrollwindow, True, True, 5)
        _list_box.pack_start(_section_scrollwindow, True, True, 5)
        _list_box.show()
        
        _scrollwindow = gtk.ScrolledWindow()
        _scrollwindow.set_policy(gtk.POLICY_AUTOMATIC,
                                 gtk.POLICY_AUTOMATIC)
        _textview = gtk.TextView()
        _textview.set_wrap_mode(gtk.WRAP_WORD)
        self.__textbuffer = _textview.get_buffer()
        _textview.show()
        _hbox = gtk.HBox()
        _hbox.pack_start(_textview, True, True, 5)
        _hbox.show()
        _frame_box.pack_start(self.__label, False, False, 5)
        _frame_box.pack_start(_list_box, False, False, 5)
        _frame_box.show()
        _frame.add(_frame_box)
        _frame.show()
        _main_box.pack_start(_frame, False)
        _vbox = gtk.VBox()
        _vbox.pack_start(_hbox, True, True, 5)
        _vbox.show()
        _main_box.pack_start(_scrollwindow, True, True, 5)
        _main_box.show()
        _scrollwindow.add_with_viewport(_vbox)
        _scrollwindow.show()
        self.__widget = _main_box
        self._setFields()

    def _setFields(self):
        """_setFields()
        
        Set the fields items in the field treeview
        """
        _record = self.__budget.getRecord(self.__budget.getCode(
                  self.__active_path_record))
        _sheet = _record.getSheet()
        _field_list = _sheet.getFields()
        self.__field_liststore.clear()
        for _field in _field_list:
            _field_text = self.__budget.getSheetField(_field)
            _iter = self.__field_liststore.append([_field, _field_text])
        _treeselection = self.__field_treeview.get_selection()
        _treeselection.select_path(0)

    def _setSection(self):
        """_setSection()
        
        Set the section items in the section treeview
        """
        self.__section_liststore.clear()
        if not self.__field_selection is None:
            _record = self.__budget.getRecord(self.__budget.getCode(
                  self.__active_path_record))
            _sheet = _record.getSheet()
            _section_list = _sheet.getSections(self.__field_selection)
            for _section in _section_list:
                _section_text = self.__budget.getSheetSection(_section)
                _iter = self.__section_liststore.append([_section, _section_text])
            _treeselection = self.__section_treeview.get_selection()
            _treeselection.select_path(0)

    def _setText(self):
        """_setText()
        
        Set the text in the textview
        """
        if not self.__section_selection is None and\
           not self.__field_selection is None:
            _record = self.__budget.getRecord(self.__budget.getCode(
                  self.__active_path_record))
            _sheet = _record.getSheet()
            _paragraph_code = _sheet.getParagraph(self.__field_selection,
                                                  self.__section_selection)
            _paragraph = self.__budget.getSheetParagraph(_paragraph_code)
            self.__textbuffer.set_text(_paragraph)
        else:
            self.__textbuffer.set_text("")

    def _field_controlSelection(self, selection):
        """_controlSelection(selection)
        
        selection: treeselection
        
        Method connected to set_selection_function() in field treeview
        This method is called before any node is selected or unselected,
        giving some control over which nodes are selected.
        The selection function should return TRUE if the state
        of the node may be toggled, and FALSE if the state of the node should
        be left unchanged.
        
        When a user select a row in the field treeview the section treeview is
        reloaded to show the sections of this field and already the text sheet.
        """
        _treeiter = self.__field_liststore.get_iter(selection)
        self.__field_selection = self.__field_liststore.get_value(_treeiter, 0)
        self._setSection()
        return True

    def _section_controlSelection(self, selection):
        """_section_controlSelection(selection)
        
        selection: treeselection
        
        Method connected to set_selection_function() in sector treeview
        This method is called before any node is selected or unselected,
        giving some control over which nodes are selected.
        The selection function should return TRUE if the state
        of the node may be toggled, and FALSE if the state of the node should
        be left unchanged.
        
        When a user select a row in the field treeview the text sheet for this
        section in showed
        """
        _treeiter = self.__section_liststore.get_iter(selection)
        self.__section_selection = self.__section_liststore.get_value(_treeiter, 0)
        self._setText()
        return True

    def _setActivePathRecord(self, path_record):
        """_setActivePathRecord(path_record))
        
        path_record: active path record
        
        Set the new path code to show its sheet of condition text.
        """
        self.__field_selection = None
        self.__field_liststore.clear()
        self.__section_selection = None
        self.__section_liststore.clear()
        self.__textbuffer.set_text("")
        _budget = self.__budget
        self.__active_path_record = path_record
        _code = _budget.getCode(self.__active_path_record)
        self.__label.set_text(utils.mapping(_("Sheet2 of Conditions of the "\
                     "record $1"), (_code,)))
        self._setFields()

    def runMessage(self, message, pane_path, arg=None):
        """runMessage(message, pane_path, arg=None)
        
        message: the message type
            "change_active": change the active record
            "clear": clear instance
        pane_path: tuple that identifies the pane in the notebook page
        arg: tuple whit two items:
            0: record path in the budget
            1: record code
        This method receives a message and executes its corresponding action
        """
        _budget = self.__budget
        if message == "change_active":
            if _budget.hasPath(arg):
                self._setActivePathRecord(arg)
        elif message == "clear":
            self._clear()

    def _clear(self):
        """_clear()
        
        Deletes all the instance atributes
        """
        del self.__page
        del self.__widget
        del self.__pane_path
        del self.__budget
        del self.__active_code
        del self.__textbuffer
        del self.__label
        del self.__textbuffer
        del self.__label
        del self.__field_liststore
        del self.__field_treeview
        del self.__field_selection
        del self.__section_liststore
        del self.__section_treeview
        del self.__section_selection

    def _getWidget(self):
        """_getWidget()
        
        return the main widget (gtk.ScrolledWindow)
        """
        return self.__widget

    def _getPanePath(self):
        """_getPanePath()
        
        return the tuple that identifies the pane in the notebook page
        """
        return self.__pane_path

    def _setPanePath(self, pane_path):
        """_setPanePath()
        
        sets the tuple that identifies the pane in the notebook page
        """
        self.__pane_path = pane_path

    def _getPage(self):
        """_getPage()
        
        return the weak reference from Page instance
        """
        return self.__page

    def _setPage(self, page):
        """_setPage()
        
        set the weak reference from Page instance
        """
        self.__page = page

    def _getBudget(self):
        """_getBudget()
        
        return the budget object
        """
        return self.__budget

    def _getActivePathRecord(self):
        """_getActivePathRecord()
        
        return the Active Path Record
        """
        return self.__active_path_record

    pane_path = property(_getPanePath, _setPanePath, None,
        "Path that identifie the item in the page notebook")
    widget = property(_getWidget, None, None,
                      "Lista de configuracion de vistas")
    page = property(_getPage, _setPage, None,
        "Weak reference from Page instance which creates this class")
    budget = property(_getBudget, None, None,
        "Budget object")
    active_path_record = property(_getActivePathRecord, None, None,
        "Active Path Record")


class FileView(object):
    """gui.FileView
    
    Description:
        Class to show the file icons of a record in a pane
    Constructor:
        Description(budget, page, pane_path, path_record=(0,))
        budget: the budget (base.obra object)
        page: weak reference from Page instance which creates this class
        pane_path: the path position of the description in the page
        path_record: the path of the active record
    Ancestry:
    +-- object
      +-- FileView
    Atributes:
        widget: the main widget (gtk.ScrolledWindow object)
        pane_path: the tuple that identifies the pane in the notebook page
        budget: The budget (base.obra objetc)
        active_code: The active code of the record
    Methods:
        runMessage
    """

    def __init__(self, budget, page, pane_path, path_record=None):
        """__init__(budget, page, pane_path, path_record=None)
        
        budget: the budget (base.obra object)
        page: weak reference from Page instance which creates this class
        pane_path: the path position of the description in the page
        path_record: the path of the active record
        
        self.__budget: the budget (base.obra object)
        self.__page: weak reference from Page instance which creates this class
        self.__pane_path: the path position of the description in the page
        self.__active_path_record: the path of the active record
        self.__active_code: the code of the active record
        self.__icon_box: the box that contains the icon
        self.__widget: main widget, a gtk.ScrolledWindow
        
        Creates an shows the scroledwindow that contain icon files
        of the record to be showed in a pane.
        """
        if path_record is None:
            path_record = (0,)
        self.__budget = budget
        self.__page = page
        self.__pane_path = pane_path
        self.__active_path_record = path_record
        self.__active_code = budget.getCode(self.__active_path_record)
        _budget = budget
        _record = self.__budget.getRecord(self.__budget.getCode(
                    self.__active_path_record))
                    
        self.__icon_box = self._getIconBox(_record)
        _scrollwindow = gtk.ScrolledWindow()
        _scrollwindow.set_policy(gtk.POLICY_ALWAYS,
                                 gtk.POLICY_NEVER)
        self.__icon_box.show()
        _scrollwindow.add_with_viewport(self.__icon_box)
        _scrollwindow.show()
        self.__widget = _scrollwindow

    def _getIconBox(self, record):
        """_getIconBox(record)
        
        record: the active record object
        
        Creates and returns the box whith te icon files of the active record.
        """
        ## TODO: add others filetypes: avi, pdf, ppt...
        _files = record.getFiles()
        _hbox = gtk.HBox()
        _frame = gtk.Frame()
        _frame.set_shadow_type(gtk.SHADOW_IN)
        for _file in _files:
            _path = os.path.dirname(self.__budget.filename)
            _file_path = os.path.join(_path, _file.name)
            _filetype = utils.getFiletype(_file_path)
            _box = gtk.VBox()
            if _filetype == "image":
                _event_box = gtk.EventBox()
                try:
                    _image_pixbuf = gtk.gdk.pixbuf_new_from_file(_file_path)
                    _image_pixbuf = _image_pixbuf.scale_simple(64, 64,
                                    gtk.gdk.INTERP_BILINEAR)
                except:
                    _image_pixbuf = gtk.gdk.pixbuf_new_from_file(
                                    globalVars.getAppPath("IMAGE-ICON"))
                    _image_pixbuf = _image_pixbuf.scale_simple(64, 64,
                                    gtk.gdk.INTERP_BILINEAR)
                _image_icon = gtk.Image()
                _image_icon.set_from_pixbuf(_image_pixbuf)
                _image_icon.show()
                _event_box.add(_image_icon) 
                _box.pack_start(_event_box, False, False, 5)
                _event_box.connect("button-press-event", self._launchFile,
                                   "image", _file_path)
                _event_box.show()
                
            elif _filetype == "dxf":
                _event_box = gtk.EventBox()
                _dxf_icon = gtk.Image()
                _dxf_pixbuf = gtk.gdk.pixbuf_new_from_file(
                                    globalVars.getAppPath("DXF-ICON"))
                _dxf_pixbuf = _dxf_pixbuf.scale_simple(64, 64,
                              gtk.gdk.INTERP_BILINEAR)
                _dxf_icon.set_from_pixbuf(_dxf_pixbuf)
                _dxf_icon.show()
                _event_box.add(_dxf_icon)
                _box.pack_start(_event_box, False, False, 5)
                _event_box.connect("button-press-event", self._launchFile, 
                                   "dxf", _file_path)
                _event_box.show()
            _label_event_box = gtk.EventBox()
            _label = gtk.Label(_file.name)
            _label_event_box.add(_label)
            _label_event_box.show()
            _label.show()
            _box.pack_start(_label_event_box, False, False, 5)
            _box.show()
            _hbox.pack_start(_box, False, False, 5)
        _hbox.show()
        _frame.add(_hbox)
        return _frame

    def _launchFile(self, widget, event, kind, file_path):
        """_launchFile(widget, event, kind, file_path)
        
        widget: the widget that emit the signal
        event: the event that emit the signal
        king: kind of file
        file_path: the path file to be launch
        
        Launch the file if a double click emit the signal.
        Method connected to "button-press-event" signal in images event box
        """
        if event.type is gtk.gdk._2BUTTON_PRESS:
            openwith.launch_file(kind, file_path)

    def _setActivePathRecord(self, path_record):
        """_setActivePathRecord(path_record))
        
        path_record: active path record
        Set the new path code to show its description text.
        """
        _budget = self.__budget
        self.__active_path_record = path_record
        _code = _budget.getCode(self.__active_path_record)
        _record = self.__budget.getRecord(_code)
        self.__icon_box.destroy()
        self.__icon_box =  self._getIconBox(_record)
        self.__icon_box.show()
        self.__widget.add_with_viewport(self.__icon_box)

    def runMessage(self, message, pane_path, arg=None):
        """runMessage(message, pane_path, arg=None)
        
        message: the message type
            "change_active": change the active record
            "clear": clear instance
        pane_path: tuple that identifies the pane in the notebook page
        arg: tuple whit two items:
            0: record path in the budget
            1: record code
        This method receives a message and executes its corresponding action
        """
        _budget = self.__budget
        if message == "change_active":
            if _budget.hasPath(arg):
                self._setActivePathRecord(arg)
        elif message == "clear":
            self._clear()

    def _clear(self):
        """_clear()
        
        Delete all instance atributes
        """
        del self.__widget
        del self.__pane_path
        del self.__budget
        del self.__active_code

    def _getWidget(self):
        """_getWidget()
        
        return the main widget (gtk.ScrolledWindow)
        """
        return self.__widget

    def _getPanePath(self):
        """_getPanePath()
        
        return the tuple that identifies the pane in the notebook page
        """
        return self.__pane_path

    def _setPanePath(self, pane_path):
        """_setPanePath()
        
        sets the tuple that identifies the pane in the notebook page
        """
        self.__pane_path = pane_path

    def _getPage(self):
        """_getPage()
        
        return the weak reference from Page instance
        """
        return self.__page

    def _setPage(self, page):
        """setPage()
        
        set the weak reference from Page instance
        """
        self.__page = page

    def _getBudget(self):
        """getBudget()
        
        return the budget object
        """
        return self.__budget

    def _getActivePathRecord(self):
        """_getActivePathRecord()
        
        return the Active Path Record
        """
        return self.__active_path_record

    pane_path = property(_getPanePath, _setPanePath, None,
        "Path that identifie the item in the page notebook")
    widget = property(_getWidget, None, None,
        "The main widget (gtk.ScrolledWindow)")
    page = property(_getPage, _setPage, None,
        "Weak reference from Page instance which creates this class")
    budget = property(_getBudget, None, None,
        "Budget object")
    active_path_record = property(_getActivePathRecord, None, None,
        "Active Path Record")


class CompanyView(object):
    """gui.CompanyView:
    
    Description:
        Class to show the company records of a budget
    Constructor:
        CompanyView(budget, page, pane_path, path_record=(0,))
        budget: budget showed ("base.Budget" object)
        page: weak reference from Page instance which creates this class
        pane_path: tuple that represents the path of the List in the Page
        path_record: path of the active record in the budget
    Ancestry:
    +-- object
      +-- CompanyView
    Atributes:
        active_path_record: Read. Path of the active record in the budget
        widget: Read. Window that contains the main widget, a gtk.HPaned
        pane_path: Read-Write. Pane page identifier
        page: Read-Write. weak reference from Page instance which creates this class
        budget: Read. Budget to show, base.budget instance.
    Methods:
        runMessage
    """

    def __init__(self, budget, page, pane_path, path_record=None):
        """__init__(budget, page, pane_path, path_record=None)
        
        budget: budget: budget showed ("base.Budget" object)
        page: weak reference from Page instance which creates this class
        pane_path: tuple that represents the path of the List in the Page
        path_record: path of the active record in the budget
        
        self.__selection:
        self.__budget: budget: budget showed ("base.Budget" object)
        self.__page: weak reference from Page instance which creates this class
        self.__pane_path: tuple that represents the path of the List in the Page
        self.__active_path_record: path of the active record in the budget
        self.__widget: main widget, a gtk.HPaned
        self.__treestore: to store companys data
        self.__option_View: OptionView object
        
        Creates an shows the scroledwindow that contain the company data.
        """
        if path_record is None:
            path_record = (0,)
        self.__selection = None
        # Seting init args
        if not isinstance(budget, base.Budget):
            raise ValueError, _("Argument must be a Budget object")
        self.__budget = budget
        self.__page = page
        self.__pane_path = pane_path
        self.__active_path_record = path_record
        # main widget
        self.__widget = gtk.HPaned()
        self.__widget.set_position(230)
        # TreeStore
        self.__treestore = gtk.TreeStore(str, str)
        self._setTreeStoreValues()
        # Select Treeview
        _select_treeview = gtk.TreeView(self.__treestore)
        _select_treeview.set_enable_search(False)
        _select_treeview.set_reorderable(False)
        _select_treeview.set_headers_visible(False)
        _select_treeview.show()
        # Scrolled_window
        _scrolled_window = gtk.ScrolledWindow()
        _scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
            gtk.POLICY_AUTOMATIC)
        _scrolled_window.add(_select_treeview)
        # colors
        _text_color = gtk.gdk.color_parse(globalVars.color["TEXT"])
        _background_color = [
            gtk.gdk.color_parse(globalVars.color["UNEVEN"]),
            gtk.gdk.color_parse(globalVars.color["EVEN"])]
        _code_column = gtk.TreeViewColumn()
        _code_column.set_clickable(True)
        _code_column.set_fixed_width(200)
        _code_cell = gtk.CellRendererText()
        _code_cell.set_property('foreground-gdk', _text_color)
        _code_column.pack_start(_code_cell, True)
        _code_column.add_attribute(_code_cell, 'text', 0)
        _summary_cell = gtk.CellRendererText()
        _summary_cell.set_property('foreground-gdk', _text_color)
        _code_column.pack_start(_summary_cell, True)
        _code_column.add_attribute(_summary_cell, 'text', 1)
        # Index column
        _select_treeview.append_column(_code_column)
        # control selection
        _treeselection = _select_treeview.get_selection()
        _treeselection.set_mode(gtk.SELECTION_SINGLE)
        _treeselection.set_select_function(self._controlSelection)
        # Show
        _scrolled_window.show()
        # Option View
        self.__option_View = OptionView("")
        # Selection
        _select_treeview.set_cursor((0,), None, False)
        _select_treeview.grab_focus()
        #
        self.__widget.add1(_scrolled_window)
        self.__widget.add2(self.__option_View.widget)
        self.__widget.show()

    def _setOptions(self, type):
        """_setOptions(type)
        
        type: "company" or "office"
        Sets the Options in the OptionView
        """
        if type == "company":
            _options = [("code", _("Code"), "string",
                         _("""Code that define the company""")),
                        ("summary", _("Summary"), "string",
                         _("""Summary of the company name""")),
                        ("name", _("Name"), "string",
                         _("""Complete name""")),
                        ("cif", _("CIF"), "string",
                         _("""Fiscal identifier number""")),
                        ("web", _("Web"), "string",
                         _("""Company web page""")),
                        ("email", _("Email"), "string",
                         _("""Company email""")),
                        ]
            self.__option_View.options = _options
        elif type == "office":
            _options = [("type", _("Type"), "string",
                         _("""Type of Office:
                           C: Central office
                           D: Local office
                           R: Performer""")),
                        ("subname", _("Name"), "string",
                         _("Office name")),
                        ("address", _("Address"), "string",""),
                        ("postal code", _("Postal code"), "string",""),
                        ("town", _("Town"), "string",""),
                        ("province", _("Province"), "string",""),
                        ("country", _("Country"), "string",""),
                        ("phone", _("Phone"), "list",
                         _("Phone numbers of the office")),
                        ("fax", _("Fax"), "list",
                         _("Fax numbers of the office")),
                        ("contact person", _("Contact person"), "string",
                         _("Contact persons in the office")),
                       ]
            self.__option_View.options = _options
        else:
            print _("Unknow Option Type")

    def _setTreeStoreValues(self):
        """_setTreeStoreValues()
        
        Sets the treestore values from the budget
        """
        _budget = self.__budget
        _company_keys = _budget.getCompanyKeys()
        for _company_key in _company_keys:
            _company = _budget.getCompany(_company_key)
            _values = [_company_key, _company.summary]
            _treeiter = self.__treestore.append(None, _values)
            _offices = _company.offices
            for _office in _offices:
                # TODO: Test offices
                _values = [_office.officeType, _office.subname]
                self.__treestore.append(_treeiter, _values)


    def _controlSelection(self, selection):
        """_controlSelection(selection)
        
        selection: selection
        
        Method connected to set_selection_function() 
        This method is called before any node is selected or unselected,
        giving some control over which nodes are selected.
        The selection function should return TRUE if the state
        of the node may be toggled, and FALSE if the state of the node should
        be left unchanged.
        
        The selection changes the company/office in the option treeview
        """
        if len(selection) == 1:
            # The selection is a company
            _company_key = self.__treestore[selection][0]
            _company = self.__budget.getCompany(_company_key)
            _selection = "company"
            _values = _company.values
        else:
            # The selection is a office
            _company_key = self.__treestore[selection[:1]][0]
            _company = self.__budget.getCompany(_company_key)
            _selection = "office"
            _office = _company.offices[selection[1]]
            _values = _office.values
        if not self.__selection == _selection:
            self.__selection = _selection
            self.options = _selection
        self.__option_View.values = _values

        return True

    def _showMessageRecord(self, record_path):
        """_showMessageRecord(record_path)
        
        record_path: the path of the record to show
        Method connected to "change_active" message
        Show the record especified in the "change_active" message
        """
        self.__active_path_record = record_path

    def runMessage(self, message, pane_path, arg=None):
        """runMessage(message, pane_path, arg=None)
        
        message: the message type
            "change_active": change the active record
            "clear": clear instance
        pane_path: tuple that identifies the pane in the notebook page
        arg: tuple whit two items:
            0: record path in the budget
            1: record code
        This method receives a message and executes its corresponding action
        """
        _budget = self.__budget
        if message == "change_active":
            if _budget.hasPath(arg):
                _path_record = arg
                self._showMessageRecord( _path_record)
            pass
        elif message == "clear":
            self._clear()

    def _colorCell(self, column, cell_renderer, tree_model, iter, lcolor):
        """_colorCell(column, cell_renderer, tree_model, iter, lcolor)
        
        column: the gtk.TreeViewColumn in the treeview
        cell_renderer: a gtk.CellRenderer
        tree_model: the gtk.TreeModel
        iter: gtk.TreeIter pointing at the row
        lcolor: list with 2 gtk colors for even and uneven record
        
        Method connected to "set_cell_data_func" of many column
        The set_cell_data_func() method sets the data function (or method) 
        to use for the column gtk.CellRenderer specified by cell_renderer.
        This function (or method) is used instead of the standard attribute
        mappings for setting the column values, and should set the attributes
        of the cell renderer as appropriate. func may be None to remove the
        current data function. The signature of func is:
        -def celldatafunction(column, cell, model, iter, user_data)
        -def celldatamethod(self, column, cell, model, iter, user_data)
        where column is the gtk.TreeViewColumn in the treeview, cell is the
        gtk.CellRenderer for column, model is the gtk.TreeModel for the
        treeview and iter is the gtk.TreeIter pointing at the row.
        
        The method sets cell background color for all columns
        and text for index and amount columns.
        """
        _row_path = tree_model.get_path(iter)
        _number = _row_path[-1]
        if column is self.__index_column:
            cell_renderer.set_property('text', str(_number + 1))
            self.__index_column.get_cell_renderers()[1].set_property(
                'cell-background-gdk', lcolor[_number % 2])
        if self.__treeview.get_cursor() == (_row_path,column):
            cell_renderer.set_property('cell-background-gdk',
                gtk.gdk.color_parse(globalVars.color["ACTIVE"]))
        else:
            cell_renderer.set_property('cell-background-gdk',
                lcolor[_number % 2])

    def _clear(self):
        """_clear()
        
        it deletes the self.__budget value
        """
        del self.__budget

    def _getWidget(self):
        """_getWidget()
        
        return the main widget (gtk.ScrolledWindow)
        """
        return self.__widget

    def _getPanePath(self):
        """_getPanePath()
        
        return the tuple that identifies the pane in the notebook page
        """
        return self.__pane_path

    def _setPanePath(self, pane_path):
        """_setPanePath()
        
        sets the tuple that identifies the pane in the notebook page
        """
        self.__pane_path = pane_path

    def _getPage(self):
        """_getPage()
        
        return the Page
        """
        return self.__page

    def _setPage(self,page):
        """_setPage()
        
        set the Page
        """
        self.__page = page

    def _getBudget(self):
        """_getBudget()
        
        return the Budget objet
        """
        return self.__budget
    
    def _getActivePathRecord(self):
        """_getActivePathRecord()
        
        return the Active Path Record
        """
        return self.__active_path_record
    
    active_path_record = property(_getActivePathRecord, None, None,
        "Active path record")
    widget = property(_getWidget, None, None,
        "main widget")
    pane_path = property(_getPanePath, _setPanePath, None,
        "Path that identifies the item in the page notebook")
    page = property(_getPage, _setPage, None,
        "Weak reference from Page instance which creates this class")
    budget =  property(_getBudget, None, None,
        "Budget object")


class OptionView(object):
    """gui.OptionView:
    
    Description:
        It creates a treeview whith the column "Option Name" "Value"
        and "Type" to show and edit Options
    Constructor:
        OptionView(option_list)
        option_list: list of options
            (option_name, type)
    Ancestry:
    +-- object
      +-- OptionView
    Atributes:
        widget: Read. Main widget
        options: Write
        values: Write
    Methods:
    """

    def __init__(self, option_list):
        """__init__(option_list)
        
        self.__option_dict:
            {"option key" : ["option name", "value", "option type",
                              "option_description"]}
        self.__option_list: option keys list
        self.__option_types: valid option types list
        self.__liststore: gtk.ListStore
        self.__treeview: gtk.TreeView
        self.__option_column: option column
        self.__value_column: value column
        self.__type_column: type column
        self.__description_label: gtk.Label
        self.__widget: Main widget
        
        Creates an shows the widget that contain the option data.
        """
        self.__option_dict = {}
        self.__option_list = []
        self.__option_types = {"boolean" : _("Boolean"),
                             "integer": _("Integer"),
                             "string":  _("Text"),
                             "color" : _("Color"),
                             "list" : _("List")}
        # ListStore
        self.__liststore = gtk.ListStore(str, str, str, str, str)
        # Treeview
        self.__treeview = gtk.TreeView(self.__liststore)
        self.__treeview.set_enable_search(False)
        self.__treeview.set_reorderable(False)
        self.__treeview.set_headers_clickable(False)
        # vbox
        _vbox = gtk.VBox()
        # Scrolled_window
        _scrolled_window = gtk.ScrolledWindow()
        _scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                        gtk.POLICY_AUTOMATIC)
        _scrolled_window.add(self.__treeview)
        _scrolled_window.show()
        _vbox.pack_start(_scrolled_window)
        # colors
        _text_color = gtk.gdk.color_parse(globalVars.color["TEXT"])
        _background_color = [
            gtk.gdk.color_parse(globalVars.color["UNEVEN"]),
            gtk.gdk.color_parse(globalVars.color["EVEN"])]
        # Option Column
        self.__option_column = gtk.TreeViewColumn()
        self.__option_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.__option_column.set_fixed_width(150)
        self.__option_column.set_resizable(True)
        _option_cell = gtk.CellRendererText()
        _option_cell.set_property('foreground-gdk', _text_color)
        self.__option_column.pack_start(_option_cell, True)
        self.__option_column.set_cell_data_func(_option_cell, self._colorCell,
                                                _background_color)
        self.__option_column.set_title(_("Option name"))
        self.__option_column.add_attribute(_option_cell, 'text', 1)
        self.__treeview.append_column(self.__option_column)
        # Value Column
        self.__value_column = gtk.TreeViewColumn()
        self.__value_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.__value_column.set_fixed_width(275)
        self.__value_column.set_resizable(True)
        _value_cell = gtk.CellRendererText()
        _value_cell.set_property('foreground-gdk', _text_color)
        self.__value_column.pack_start(_value_cell, True)
        self.__value_column.set_cell_data_func(_value_cell, self._colorCell,
                                               _background_color)
        self.__value_column.set_title(_("Value"))
        self.__value_column.add_attribute(_value_cell, 'text', 2)
        self.__treeview.append_column(self.__value_column)
        # Type Column
        self.__type_column = gtk.TreeViewColumn()
        self.__type_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.__type_column.set_fixed_width(70)
        self.__type_column.set_resizable(True)
        _type_cell = gtk.CellRendererText()
        _type_cell.set_property('foreground-gdk', _text_color)
        self.__type_column.pack_start(_type_cell, True)
        self.__type_column.set_cell_data_func(_type_cell, self._colorCell,
                                               _background_color)
        self.__type_column.set_title(_("Type"))
        self.__treeview.append_column(self.__type_column)
        # End Column
        _end_column = gtk.TreeViewColumn()
        _end_column.set_clickable(False)
        _end_cell = gtk.CellRendererText()
        _end_cell.set_property('cell-background-gdk',
            gtk.gdk.color_parse(globalVars.color["UNEVEN"]))
        _end_column.pack_start(_end_cell, True)
        self.__treeview.append_column(_end_column)
        # Connect
        self.__treeview.connect("key-press-event", self._treeviewKeyPressEvent)
        self.__treeview.connect("button-press-event", 
            self._treeviewClickedEvent)
        # control selection
        _treeselection = self.__treeview.get_selection()
        _treeselection.set_mode(gtk.SELECTION_MULTIPLE)
        _treeselection.set_select_function(self._controlSelection)
        # labels
        _frame = gtk.Frame()
        _frame.set_shadow_type(gtk.SHADOW_OUT)
        _vbox2 = gtk.VBox()
        _frame.add(_vbox2)
        _alignement = gtk.Alignment(xalign=0, yalign=0, xscale=0, yscale=0)
        _alignement.set_padding(0, 0, 12, 0)
        _label = gtk.Label()
        _label.set_markup("<b>" + _("Description:") + "</b>")
        _label.show()
        _alignement.add(_label)
        _alignement.show()
        _alignement2 = gtk.Alignment(xalign=0, yalign=0, xscale=0, yscale=0)
        _alignement2.set_padding(0, 0, 24, 0)
        self.__description_label  = gtk.Label()
        self.__description_label.show()
        _alignement2.add(self.__description_label)
        _alignement2.show()
        _vbox2.pack_start(_alignement, False)
        _vbox2.pack_start(_alignement2, False)
        _vbox2.show()
        _frame.show()
        _vbox.pack_start(_frame, False)
        # Show
        self.__treeview.show()
        _vbox.show()
        self.__widget = _vbox

    def _treeviewKeyPressEvent(self, widget, event):
        """_treeviewKeyPressEvent(widget, event)
        
        widget: treewiew widget
        event: Key Press event
        Method connected to "key-press-event" signal
        The "key-press-event" signal is emitted when the user presses a key
        on the keyboard.
        Returns :TRUE to stop other handlers from being invoked for the event.
        Returns :FALSE to propagate the event further.
        
        If the user press the right cursor button and the cursor is in the
        value column or pres the left cursor button and the cursor is
        in the value column the event is estoped, else the event is propagated. 
        """
        (_cursor_path, _column) = self.__treeview.get_cursor()
        if (event.keyval == gtk.keysyms.Right \
           and _column == self.__value_column) \
           or (event.keyval == gtk.keysyms.Left \
           and _column == self.__value_column):
            return True
        else:
            _description = self.__liststore[_cursor_path][4]
            self.__description_label.set_text(_description)
            return False

    def _treeviewClickedEvent(self, widget, event):
        """_treeviewClickedEvent(widget, event)
        
        widget: treewiew widget
        event: clicked event
        Method connected to "button-press-event" signal
        The "button-press-event" signal is emitted when a mouse button is
        pressed.
        Returns TRUE to stop other handlers from being invoked for the event.
        Returns FALSE to propagate the event further.
        
        The cursos is moved to value column.
        """
        path_at_pos = self.__treeview.get_path_at_pos(int(event.x),
                                                      int(event.y))
        if not path_at_pos is None:
            _path_cursor, _column, _x, _y = path_at_pos
            _description = self.__liststore[_path_cursor][4]
            self.__description_label.set_text(_description)
            if _column == self.__value_column:
                return False
            else:
                self.__treeview.set_cursor(_path_cursor,self.__value_column,
                                           True)
                self.__treeview.grab_focus()
                return True
        return True

    def _controlSelection(self, selection):
        """_controlSelection(selection)
        
        selection: treeselection
        
        Method connected to set_selection_function() 
        This method is called before any node is selected or unselected,
        giving some control over which nodes are selected.
        The selection function should return TRUE if the state
        of the node may be toggled, and FALSE if the state of the node should
        be left unchanged.
        
        Return False so none row is selected
        """
        return False

    def _colorCell(self, column, cell_renderer, tree_model, iter, lcolor):
        """_colorCell(column, cell_renderer, tree_model, iter, lcolor)
        
        column: the gtk.TreeViewColumn in the treeview
        cell_renderer: a gtk.CellRenderer
        tree_model: the gtk.TreeModel
        iter: gtk.TreeIter pointing at the row
        lcolor: list with 2 gtk colors for even and uneven record
        
        Method connected to "set_cell_data_func" of the column
        The set_cell_data_func() method sets the data function (or method) 
        to use for the column gtk.CellRenderer specified by cell_renderer.
        This function (or method) is used instead of the standard attribute
        mappings for setting the column values, and should set the attributes
        of the cell renderer as appropriate. func may be None to remove the
        current data function. The signature of func is:
        -def celldatafunction(column, cell, model, iter, user_data)
        -def celldatamethod(self, column, cell, model, iter, user_data)
        where column is the gtk.TreeViewColumn in the treeview, cell is the
        gtk.CellRenderer for column, model is the gtk.TreeModel for the
        treeview and iter is the gtk.TreeIter pointing at the row.
        
        The method sets cell background color for all columns
        and text for type column.
        """
        _row_path = tree_model.get_path(iter)
        _number = _row_path[-1]
        if self.__treeview.get_cursor() == (_row_path,column):
            cell_renderer.set_property('cell-background-gdk',
                gtk.gdk.color_parse(globalVars.color["ACTIVE"]))
        else:
            cell_renderer.set_property('cell-background-gdk',
                lcolor[_number % 2])
        if column is self.__type_column:
            _type = self.__option_types[tree_model[_row_path][3]]
            cell_renderer.set_property('text', _type)

    def _setOptions(self, option_list):
        """_setOptions(option_list)
        
        option_list: list of tuples
            (option, option name, type)
            option: option identifier
            option name: a string with the option name
            Description: a string with the option description
            type: can be "boolean"
                         "integer"
                         "string"
                         "color"
        Sets the Options in the treeview rows
        """
        self.__option_dict = {}
        self.__option_list = []
        self.__liststore.clear()
        if isinstance(option_list, list):
            for _option in option_list:
                if isinstance(_option, tuple) and len(_option) == 4:
                    _option_key = _option[0]
                    _option_name = _option[1]
                    _option_type = _option[2]
                    _option_description = _option[3]
                    if isinstance(_option_key, str) and \
                       (isinstance(_option_name, str) or\
                       isinstance(_option_name, unicode))and \
                       _option_type in self.__option_types.keys():
                        self.__liststore.append([_option_key, _option_name, "",
                            _option_type, _option_description])
                        self.__option_dict[_option_key] = [_option_name, "",
                            _option_type, _option_description]
                        self.__option_list.append(_option_key)
                    else:
                        print _("Option values must be strings")
                else:
                    print _("Option must be a tuple with 4 items")
        else:
            print _("Option list must be a list")

    def _setValues(self, values):
        """_setValues(values)
        
        values: dictionary {option : value}

        Sets the Options values
        """
        if isinstance(values, dict):
            for _option, _value in values.iteritems():
                if _option in self.__option_dict:
                    _type = self.__option_dict[_option][2]
                    if _type == "boolean":
                        if isinstance(_value, bool):
                            _num = self.__option_list.index(_option)
                            _iter = self.__liststore.get_iter((_num,))
                            self.__liststore.set_value(_iter, 2, _value)
                            self.__option_dict[_option][1] = _value
                        else:
                            print _("Icorrect type, must be boolean")
                    elif _type == "integer":
                        try:
                            _value = int(_value)
                        except ValueError:
                            print _("Icorrect type, must be integer")
                        else:
                            _num = self.__option_list.index(_option)
                            _iter = self.__liststore.get_iter((_num,))
                            self.__liststore.set_value(_iter, 2, _value)
                            self.__option_dict[_option][1] = _value
                    elif _type == "string":
                        if isinstance(_value, str):
                            _num = self.__option_list.index(_option)
                            _iter = self.__liststore.get_iter((_num,))
                            self.__liststore.set_value(_iter, 2, _value)
                            self.__option_dict[_option][1] = _value
                        else:
                            print _("Icorrect type, must be string")
                    elif _type == "list":
                        if isinstance(_value, list):
                            _num = self.__option_list.index(_option)
                            _iter = self.__liststore.get_iter((_num,))
                            _str_value = ""
                            for _item_value in _value:
                                _str_value = _str_value + _item_value + ","
                            if _str_value[-1] == ",":
                                _str_value = _str_value[:-1]
                            self.__liststore.set_value(_iter, 2, _str_value)
                            self.__option_dict[_option][1] = _value
                        else:
                            print _("Icorrect type, must be list")
                    elif _type == "color":
                        if isinstance(_value, str):
                            try:
                                _color = gtk.gdk.color_parse(_value)
                            except ValueError:
                                print _("Icorrect type, must be a parseable " \
                                        "color")
                            else:
                                _num = self.__option_list.index(_option)
                                _iter = self.__liststore.get_iter((_num,))
                                self.__liststore.set_value(_iter, 2, _value)
                                self.__option_dict[_option][1] = _value
                    else:
                        print _("Type must be boolean, integer, string or "\
                                "color")
                else:
                    print _("Value must be in the option dict")
        else:
            print _("Values must be a dict")
        self.__treeview.set_cursor((0),self.__value_column, False)
        self.__treeview.grab_focus()
        (_cursor_path, _column) = self.__treeview.get_cursor()
        _description = self.__liststore[_cursor_path][4]
        self.__description_label.set_text(_description)

    def _getWidget(self):
        """_getWidget()
        
        return the main widget (gtk.ScrolledWindow)
        """
        return self.__widget

    widget = property(_getWidget, None, None,
        "main widget")
    values = property(None, _setValues, None,
        "values")
    options = property(None, _setOptions, None,
        "options")
