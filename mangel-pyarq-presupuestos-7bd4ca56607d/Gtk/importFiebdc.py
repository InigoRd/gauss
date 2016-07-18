#!/usr/bin/python
# -*- coding: utf-8 -*-
## File importFiebdc.py
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

# Modules
import sys
import time
import os.path
import pygtk
pygtk.require('2.0')
import gtk
import gobject
import threading
gobject.threads_init()

# pyArq-Presupuestos Modules
from Generic import utils
from Generic import globalVars
#from Generic import durusdatabase
import gui

class FileSelectionWindow(object):
    """importFiebdc.FileSelectionWindow:
    
    Description:
        Class to show the selection file window
    Constructor:
        importFiebdc.FileSelectionWindow(mainWindow, readFileMethod, budget,
            filename, cancelMethod, filetype)
    Ancestry:
    +-- object
      +-- FileSelectionWindow
    Atributes:
        "__mainWindow": gui.MainWindow object
        "__readFileMethod": Method to read the selected file
        "__budget": Budget object
        "__filename": "file"
        "__filetype": "budget" ,"database" or "durus"
        "__cancelMethod": Method to cancel the read method
        "__file": The selected file
        "__window": The selection file window
    Methods:
        __init__(self, mainWindow, readFileMethod, budget
                 arg_List, cancelMethod)
        _launchProgressWindow(self, _file)
        _openFile(self, filename)
    """

    def __init__(self, mainWindow, readFileMethod, budget, filename,
                 cancelMethod, filetype):
        """def __init__(self, mainWindow, readFileMethod, budget,
                        filename, cancelMethod, filetype)
        
        mainWindow: gui.MainWindow object
        readFileMethod: Method to read the selected file
        budget: base.Budget object
        filename: "file"
        cancelMethod: Method to cancel the read method
        fileytpe: "budget", "database" or "durus".
        Sets the init atributes, creates the file selection window
        Connects the events:
            * clicked ok button: _openFile
            * clicked cancel button: destroy window
            * destroy event: _destroy
        """
        # TODO: Add file filter
        self.__mainWindow = mainWindow
        self.__readFileMethod = readFileMethod
        self.__budget = budget
        self.__filename = filename
        self.__filetype = filetype
        self.__cancelMethod = cancelMethod
        self.__file = None
        self.__window = gtk.FileChooserDialog(title=_("Open File"),
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                     gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        self.__window.set_default_response(gtk.RESPONSE_OK)
        #if self.__filetype == "budget" or self.__filetype == "database":
        self.__window.set_current_folder(globalVars.getHomePath("BUDGET"))
        #else: # "durus"
        #    self.__window.set_current_folder(
        #        globalVars.getHomePath("DURUS-DATABASE"))
        if self.__window.run() == gtk.RESPONSE_OK:
            self._openFile(self.__window.get_filename())
        self.__window.destroy()

    def _launchProgressWindow(self, file):
        """def _launchProgressWindow(self, file)
        
        Launch the progress window
        """
        self.__filename = file
        _emptyPage = gui.EmptyPage(self.__mainWindow, self.__readFileMethod,
                                   self.__budget, self.__filename,
                                   self.__cancelMethod, self.__filetype)
        self.__mainWindow.appendEmptyPage(_emptyPage)
        _emptyPage.run()

    def _openFile(self, filename):
        """def _openFile(self, filename)
        
        filename: the filename to open
        If the selected file has a bc3 extension 
        _launchProgressWindow is called
        """
        _file = filename
        if sys.getfilesystemencoding():
            _file = _file.decode(sys.getfilesystemencoding())
            #-#
            _file = _file.encode("utf-8")
            #-#
        self.__file = _file
        _filename = os.path.basename(self.__file)
        _filename_ext = _filename.split(".")[-1]
        if (self.__filetype == "budget" or self.__filetype == "database") and \
            _filename_ext != "bc3" and _filename_ext != "BC3":
            print _("The file must have 'bc3' extension")
        #elif self.__filetype == "durus" and _filename_ext != "durus":
        #    print _("The file must have 'durus' extension")
        else:
            self.__window.destroy()
            # TODO: the file exits? is it not binary?, can it be readed?
            self._launchProgressWindow(self.__file)


class ProgressWindow(object):
    """importFiebdc.ProgressWindow:
    
    Description:
        Class to show the progress window and launch a thread  to read
        the database file
    Constructor:
        importFiebdc.ProgressWindow(mainWindow, readFileMethod, budget,
                 filename, cancelMethod)
    Ancestry:
    +-- object
      +-- ProgressWindow
    Atributes:
        "__mainWindow":
        "__readFileMethod":
        "__budget":
        "__filename":
        "__cancelMethod":
        "__children": Thread instance
        "__cancel": list with boolean values
        "__window": progress window widget
        "__progress_bar": probres bar widget
        "__label": label widget
    Methods:
        closeWindow(self)
        __init__(self, mainWindow, readFileMethod, budget
                 filename, cancelMethod)
        closeWindow(self)
        main(self)
        _autoClose(self)
        _updateLabel(self, _time)
        _updateProgressBar(self)
        _launchTimeout(self)
        _launchChildren(self, mainWindow, readFileMethod, budget
                    filename, cancelMethod)
        _cancelChildren(self,widget=None)
        _destroy(self, widget)
        _delete_event(self, widget, event)

    """
    def __init__(self, mainWindow, readFileMethod, budget,
                 filename, cancelMethod):
        """def __init__(self, mainWindow, readFileMethod, budget
                        filename, cancelMethod)
        
        mainWindow: gui.MainWindow object
        readFileMethod: Method to read the selected file
        budget: base.Budget object
        filenamer: "file"
        cancelMethod: Method to cancel the read method
        Sets the init atributes, creates the progress window
        Connects the events:
            * destroy signal: self._destroy
            * delete_event signal: self._delete_event
            * clicked cancel button: self._cancelChildren
        """
        self.__mainWindow = mainWindow
        self.__readFileMethod = readFileMethod
        self.__filename = filename
        self.__budget = budget
        self.__cancelMethod = cancelMethod
        self.__children = None
        self.__cancel = [False, False]
        self.__window = gtk.Window()
        self.__window.set_title(_("Loading file ..."))
        self.__window.connect("destroy", self._destroy)
        self.__window.connect("delete_event", self._delete_event)
        _Vbox1 = gtk.VBox(False, 0)
        self.__window.add(_Vbox1)
        _align = gtk.Alignment(0.5, 0.5, 0, 0)
        _align.show()
        _Vbox1.pack_start(_align, False, False, 5)
        self.__progress_bar = gtk.ProgressBar()
        self.__progress_bar.show()
        _align.add(self.__progress_bar)
        self.__label = gtk.Label()
        self.__label.set_text(_("Time: 0s"))
        self.__label.show()
        _Vbox1.add(self.__label)
        self.__throbber = gtk.Image()
        self.__throbber.set_from_file(globalVars.getAppPath("THROBBER-ICON"))
        _Vbox1.add(self.__throbber)
        self.__throbber.show()
        self.__animation = gtk.gdk.PixbufAnimation(globalVars.getAppPath("THROBBER-GIF"))
        _pixbuf = self.__throbber.get_pixbuf()
        self.__throbber.set_from_animation(self.__animation)
        _Hbox1 = gtk.HBox(False, 0)
        _Vbox1.add(_Hbox1)
        _button1 = gtk.Button(_("Cancel"))
        _button1.connect("clicked", self._cancelChildren)
        _button1.show()
        _Hbox1.pack_start(_button1, True, True, 0)
        _Hbox1.show()
        _Vbox1.show()
        
    def main(self):
        """def main(self)
        
        Launch the thread
        Launch the timeouts
        Shows window and starts the GTK+ event processing loop.
        """

        self._launchChildren()
        self._launchTimeout()
        self.__window.show()
        gtk.main()

    def closeWindow(self):
        """def closeWindow(self)
        
        Sets the __children atribute to None
        This causes that the timiouts is ended and then the window is
        closed.
        This method is called from thread when it is finished
        """
        self.__children = None

    def _launchTimeout(self):
        """def _launchTimeout(self)
        
        Launch the timeouts: 
            1- update progress bar
            2- update time labal
            3- If the other timetouts are stoped the window is closed
        """
        gobject.timeout_add(100, self._updateProgressBar)
        gobject.timeout_add(1000, self._updateLabel, time.time())
        self.__cancel = [False, False]
        gobject.timeout_add(1000, self._autoClose)

    def _updateProgressBar(self):
        """def _updateProgressBar(self)
        
        update progress bar in a timeout
        If the thread end or is canceled the timeout is stoped
        """
        if  self.__children is None or self.__children.isCanceled() == True:
            self.__cancel[0] = True
            return False
        else:
            self.__progress_bar.pulse()
            return True

    def _updateLabel(self, _time):
        """def _updateProgressBar(self)
        
        update time label in a timeout
        If the thread end or is canceled the timeout is stoped
        """
        if  self.__children is None or self.__children.isCanceled() == True:
            self.__cancel[1] = True
            return False
        else:
            _time = time.time() - _time
            self.__label.set_text(utils.mapping(_("Time: $1"),
                ("%.0f" %_time,)))
            return True

    def _autoClose(self):
        """def _updateProgressBar(self)
        
        If the time label and progress bar timeouts are stoped the window is 
        closed and ist tiemeout is stoped
        """
        if self.__cancel == [ True, True ]:
            self.__window.destroy()
            return False
        else:
            return True

    def _launchChildren(self):
        """_launchChildren(self)
        
        Launch the thread to read the file
        """
        if self.__children is None:
            self.__children =  Thread(self, self.__mainWindow,
                self.__readFileMethod, self.__budget, self.__filename,
                self.__cancelMethod)
            self.__children.start()

    def _cancelChildren(self,widget=None):
        """_cancelChildren(self,widget=None)
        
        Method connected to "clicked" singal of cancel button
        Stops the thread and close the window
        """
        if self.__children:
            self.__children.cancel()
        self.__window.destroy()

    def _delete_event(self, widget, event):
        """_delete_event(self, widget, event)
        
        widget: the widget where the event is emitted from
        event: the "gtk.gdk.Event"
        Method connected to "delete_event" signal of window widget
        This signal is emitted when a user press the close titlebar button.
        Stops the thread if exits.
        Returns True so the signal "destroy" is emitted.
        """
        if self.__children:
            self._cancelChildren()
        return True

    def _destroy(self, widget):
        """_destroy(self, widget)
        
        widget: the widget where the event is emitted from
        Method connected to "destroy" signal of window widget
        This signal is emited when the method connected to "delete_event"
        signal returns True or when the program call the destroy() method of
        the gtk.Window widget.
        The window is closed and the GTK+ event processing loop is ended.
        """
        gtk.main_quit()

class Thread(threading.Thread):
    """importFiebdc.Thread:
    
    Description:
        Thread class to read a file without freeze the gui
    Constructor:
        importFiebdc.Thread(page, mainWindow,
                     readFileMethod, budget, filename, cancelMethod, filetype)
    Ancestry:
    +--threading.Thread
      +-- importFiebdc.Thread
    Atributes:
        "__page": The page instance that launch the thread
        "__mainWindow": gui.MainWindow instance
        "__readFileMethod": Method to read the selected file
        "__budget
        "__filename": "file"
        "__cancelMethod": Method to cancel the read method
        "__filetype": "budget", "database" or "durus"
        "__cancel": Boolean value, True: the thread is stoped
    Methods:
        __init__(self, page, mainWindow,
                 readFileMethod, arg_tuple, cancelMethod)
        run(self)
        cancel(self)
        isCanceled(self)
    """

    def __init__(self, page, mainWindow, readFileMethod, budget,
                 filename, cancelMethod, filetype):
        """def __init__(page, mainWindow, readFileMethod, budget,
                 filename, cancelMethod, filetype)
        
        page: The page instance that launch the thread
        mainWindow: gui.Mainwindow object
        readFileMethod: Method to read the selected file
        budget: base.Budget object
        filename: "file"
        cancelMethod: Method to cancel the read method
        filetype: "budget", "database" or "durus"
        Sets the instance atributes.
        """
        super(Thread, self).__init__()
        self.__page = page
        self.__mainWindow = mainWindow
        self.__readFileMethod = readFileMethod
        self.__budget = budget
        self.__filename = filename
        self.__cancelMethod = cancelMethod
        self.__filetype = filetype
        self.__cancel = False

    def run(self):
        """run(self)
        
        
        """
        _budget = self.__readFileMethod(self.__budget, self.__filename,
                                        self.__page)
        if _budget is None:
            self.__page.threadCanceled()
        else:
            _mainWindow = self.__mainWindow
            self.__page.threadFinishedSignal(_budget)
            #if self.__filetype == "database":
            #    self.saveDurusDatabase()
        self.clear()
        
    #def saveDurusDatabase(self):
    #    _path = globalVars.getHomePath("DURUS-DATABASE")
    #    _file_whit_path_bc3 = self.__budget.filename
    #    _filename_bc3 = _file_whit_path_bc3.split("/")[-1]
    #    _filename = _filename_bc3.split(".")[-2]
    #    _file = _path + _filename + ".durus"
    #    print utils.mapping(_("Saving file: $1"), (_file,))
    #    _time = time.time()
    #    _durus_file = durusdatabase.DurusFile(_file,True)
    #    _durus_file.setBudget(self.__budget)
    #    _durus_file.close()
    #    print utils.mapping(_("Saving time: $1 seconds"),
    #          (("%.2f" %(time.time()-_time) ),))

    def cancel(self):
        """cancel(self)
        
        Sets the "__cancel" atribute to True and call "__cancelMethod" to stop
        read the file
        """
        self.__cancel = True
        self.__cancelMethod()

    def isCanceled(self):
        """isCanceled(self)
        
        Return True if the thread has been canceled
        """
        return self.__cancel
    
    def clear(self):
        del self.__page
        del self.__mainWindow
        del self.__readFileMethod
        del self.__budget
        del self.__filename
        del self.__cancelMethod
        del self.__cancel
