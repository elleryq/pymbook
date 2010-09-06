#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2010 elleryq@gmail.com
#
#  This file is part of pymbook
#  pymbook is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  pymbook is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with pymbook.  If not, see <http://www.gnu.org/licenses/>.
"""pymbook"""
import sys
import os

import pygtk
pygtk.require('2.0')
import gtk
import gobject

from pymbooklib import pdb
from pymbooklib.version import APP_NAME, APP_VERSION, APP_COMMENT, APP_AUTHORS
from pymbooklib.pdbwidget import PDBWidget
from pymbooklib.pdbcontents import PDBContents
from pymbooklib.pdbcanvas import PDBCanvas
from pymbooklib.bookshelf import BookshelfWidget, find_pdbs
from pymbooklib.translation import _

SHELF_TAB = 0
CONTENT_TAB = 1
CONTEXT_TAB = 2

class State( object ):
    def __init__(self, window):
        self.window = window

    def enter(self):
        return self

    def leave(self):
        return self

class ShelfState( State ):
    def __init__(self, window):
        super(ShelfState, self).__init__(window)

    def enter(self):
        super(ShelfState, self).enter()
        self.window.btn_shelf.set_sensitive( True )
        self.window.btn_content.set_sensitive( False )
        self.window.btn_return.set_sensitive( False )
        self.window.notebook.set_current_page(SHELF_TAB)

class ShelfCanBackState( ShelfState ):
    def __init__(self, window):
        super(ShelfCanBackState, self).__init__(window)

    def enter(self):
        super(ShelfCanBackState, self).enter()
        self.window.btn_return.set_sensitive( True )

class ContentState( State ):
    def __init__(self, window):
        super(ContentState, self).__init__(window)

    def enter(self):
        super(ContentState, self).enter()
        self.window.btn_shelf.set_sensitive( True )
        self.window.btn_content.set_sensitive( False )
        self.window.btn_return.set_sensitive( False )
        self.window.notebook.set_current_page(CONTENT_TAB)

class ContentCanBackState( ContentState ):
    def __init__(self, window):
        super(ContentCanBackState, self).__init__(window)

    def enter(self):
        super(ContentCanBackState, self).enter()
        self.window.btn_return.set_sensitive( True )

class ReadingState( State ):
    def __init__(self, window):
        super(ReadingState, self).__init__(window)

    def enter(self):
        super(ReadingState, self).enter()
        self.window.btn_shelf.set_sensitive( True )
        self.window.btn_content.set_sensitive( True )
        self.window.btn_return.set_sensitive( False )
        self.window.notebook.set_current_page(CONTEXT_TAB)

class MainWindow:
    ENTRY_SHELF_PATH = "bookshelf_path"
    ENTRY_WIDTH = "width"
    ENTRY_HEIGHT = "height"
    ENTRY_FONT_NAME = "font_name"
    ENTRY_FONT_SIZE = "font_size"
    ENTRY_CURRENT_PDB = "current_pdb"
    DEFAULT_FONT_NAME = "文泉驛微米黑"
    DEFAULT_FONT_SIZE = 16
    DEFAULT_WIDTH = 640
    DEFAULT_HEIGHT = 480
    DEFAULT_SHELF_PATH = "~/download/"
    DEFAULT_CONFIG_CONTENT = """
[mbook]
%s = %s
%s = %d
%s = %d
%s = %s
%s = %d
""" % ( ENTRY_SHELF_PATH, DEFAULT_SHELF_PATH, 
        ENTRY_WIDTH, DEFAULT_WIDTH, 
        ENTRY_HEIGHT, DEFAULT_HEIGHT,
        ENTRY_FONT_NAME, DEFAULT_FONT_NAME,
        ENTRY_FONT_SIZE, DEFAULT_FONT_SIZE )
    CONFIG_FILENAME = "~/.config/pymbook.conf"
    SECTION = 'mbook'

    def __init__(self):
        self.pdb = None
        self.pdb_filename = None
        self.pref_dlg = None
        self.load_config()
    	self.initialize_component()

    def initialize_component(self):
    	try:
    		self.builder = gtk.Builder()
    		self.builder.add_from_file( "main_window.glade" )
    	except BaseException, e:
            err_dialog = gtk.MessageDialog(
                    self.window, 
                    gtk.DIALOG_MODAL, 
                    gtk.MESSAGE_ERROR, 
                    gtk.BUTTONS_CLOSE, 
                    repr(e))
            result = err_dialog.run()
            err_dialog.destroy()
            return
    	self.window = self.builder.get_object("window1")
        self.window.set_title( APP_NAME )
        self.window.set_position( gtk.WIN_POS_CENTER )
        self.window.set_size_request(
                self.config.getint( self.SECTION, self.ENTRY_WIDTH ), 
                self.config.getint( self.SECTION, self.ENTRY_HEIGHT ) )

        self.btn_shelf = self.builder.get_object("btn_shelf")
        self.btn_content = self.builder.get_object("btn_content")
        self.btn_return = self.builder.get_object("btn_return")
        
        self.act_quit = self.builder.get_object("act_quit")
        self.notebook=self.builder.get_object("notebook1")

        font = "%s %d" % ( 
                self.config.get( self.SECTION, self.ENTRY_FONT_NAME ),
                self.config.getint( self.SECTION, self.ENTRY_FONT_SIZE ) )

        # Add bookshelf tab
        self.bookshelf = BookshelfWidget( self.config.get( self.SECTION, self.ENTRY_SHELF_PATH ) )
        self.bookshelf.set_font( font )
        frame=gtk.Frame()
        frame.show()
        frame.add( self.bookshelf )
        label = gtk.Label( _("Bookshelf") )
        self.notebook.append_page( frame, label )
        self.bookshelf.show()

        # Add contents tab
        self.pdb_contents=PDBContents()
        self.pdb_contents.set_font( font )
        frame=gtk.Frame()
        frame.show()
        frame.add( self.pdb_contents )
        label = gtk.Label( _("Contents") )
        self.notebook.append_page( frame, label )
        self.pdb_contents.show()

        # Add text tab
        self.pdb_canvas=PDBCanvas()
        frame=gtk.Frame()
        self.pdb_canvas.set_font( font )
        frame.show()
        frame.add(self.pdb_canvas)
        label = gtk.Label(_("Text"))
        self.notebook.append_page(frame, label)
        self.pdb_canvas.show()

        filename = None
        if self.config.has_option( self.SECTION, self.ENTRY_CURRENT_PDB ):
            filename = self.config.get( self.SECTION, self.ENTRY_CURRENT_PDB )
        if filename and len(filename) and self.open_pdb( filename ):
            self.pdb_filename = filename
            self.state = ContentState(self).enter()
        else:
            self.state = ShelfState(self).enter()

        # connect signals
        self.bookshelf.connect("book_selected", self.bookshelf_book_selected_cb )
        self.pdb_contents.connect("chapter_selected", self.pdb_contents_chapter_selected_cb)

    	self.builder.connect_signals(self)
    	self.window.show()

    def load_config(self):
        import ConfigParser
        import io
        self.config = ConfigParser.RawConfigParser()
        if os.path.exists( os.path.expanduser( self.CONFIG_FILENAME ) ):
            self.config.readfp( open( os.path.expanduser( self.CONFIG_FILENAME ) ) )
        else:
            self.config.readfp( io.BytesIO(self.DEFAULT_CONFIG_CONTENT) )

    def save_config(self):
        import ConfigParser
        self.config.write( open(os.path.expanduser( self.CONFIG_FILENAME ), "wt" ) )

    def open_pdb( self, pdb_filename ):
        try:
            self.pdb=pdb.PDBFile(pdb_filename).parse()
            self.pdb_contents.set_pdb( self.pdb )
            self.pdb_contents.redraw_canvas()
            self.pdb_canvas.set_pdb( self.pdb )
            self.pdb_canvas.redraw_canvas()
        except BaseException, ex:
            dialog=gtk.MessageDialog(
                    self.window, 
                    gtk.DIALOG_MODAL, 
                    gtk.MESSAGE_ERROR, 
                    gtk.BUTTONS_CLOSE, 
                    _("Cannot open specified pdb."))
            result = dialog.run()
            dialog.destroy()
            return False
        self.window.set_title( "%s - %s" % ( APP_NAME, self.pdb.book_name ) )
        return True

    def window1_delete_event_cb(self, widget, event, data=None):
        self.act_quit.activate()

    def act_quit_activate_cb(self, b):
        rect = self.window.get_allocation()
        self.config.set( self.SECTION, self.ENTRY_WIDTH, rect.width )
        self.config.set( self.SECTION, self.ENTRY_HEIGHT, rect.height )
        self.config.set( self.SECTION, self.ENTRY_CURRENT_PDB,
                    self.pdb_filename )
        self.save_config()
    	gtk.main_quit()
    
    def act_about_activate_cb(self, b):
        dialog=gtk.AboutDialog()
        dialog.set_name( APP_NAME )
        dialog.set_version( APP_VERSION )
        dialog.set_authors( APP_AUTHORS )
        dialog.set_comments( APP_COMMENT )
        dialog.set_license( _("Distributed under the GPL3.") )
        dialog.run()
        dialog.destroy()

    def act_open_activate_cb(self, b):
        dialog=gtk.FileChooserDialog( _("Open..."),
                None,
                gtk.FILE_CHOOSER_ACTION_OPEN,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                 gtk.STOCK_OPEN, gtk.RESPONSE_OK) )
        dialog.set_default_response(gtk.RESPONSE_OK)

        _filter=gtk.FileFilter()
        _filter.set_name(_("PDB/uPDB files"))
        _filter.add_pattern("*.pdb")
        _filter.add_pattern("*.updb")
        dialog.add_filter(_filter)
    
        response=dialog.run()
        if response==gtk.RESPONSE_OK:
            self.pdb_filename=dialog.get_filename()
            if self.open_pdb( self.pdb_filename ):
                self.state = ContentState( self ).enter()
        elif response==gtk.RESPONSE_CANCEL:
            pass
        dialog.destroy()

    def act_font_activate_cb(self, b):
        dialog=gtk.FontSelectionDialog(_("Choose font"))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_font_name( "%s %d" % (
                self.config.get( self.SECTION, self.ENTRY_FONT_NAME ),
                self.config.getint( self.SECTION, self.ENTRY_FONT_SIZE ) ) )
        response=dialog.run()
        if response==gtk.RESPONSE_OK:
            font_name=dialog.get_font_name()
            self.pdb_contents.set_font( font_name )
            self.pdb_canvas.set_font( font_name )
            font = font_name.split()
            self.config.set( self.SECTION, self.ENTRY_FONT_NAME, font[0] )
            self.config.set( self.SECTION, self.ENTRY_FONT_SIZE, font[-1] )
            self.save_config()
        dialog.destroy()
        self.pdb_contents.redraw_canvas()
        self.pdb_canvas.redraw_canvas()

    def act_index_activate_cb(self, b):
        self.state = ContentCanBackState(self).enter()

    def act_preference_activate_cb(self, b):
        try:
            builder = gtk.Builder()
            pref_dlg = builder.add_from_file( "preference_dialog.glade" )
        except BaseException, e:
            print( e )
            return
        pref_dlg = builder.get_object("dialog1")
        chooser_btn = builder.get_object("filechooserbutton1")
        shelf_path=os.path.expanduser( self.config.get( self.SECTION, self.ENTRY_SHELF_PATH) ).encode( sys.getfilesystemencoding() )
        chooser_btn.set_current_folder( shelf_path )

        result=pref_dlg.run()
        # OK
        if result==gtk.RESPONSE_OK:
            selected_path = chooser_btn.get_filename()
            if selected_path:
                self.config.set( self.SECTION, self.ENTRY_SHELF_PATH, selected_path )
                self.save_config()
        pref_dlg.destroy()

    def act_shelf_activate_cb( self, b ):
        if isinstance(self.state, type(self.state)):
            self.state = ShelfCanBackState(self).enter()
        else:
            self.state = ShelfState(self).enter()

    def act_return_activate_cb( self, b ):
        self.state = ReadingState(self).enter()

    def pdb_contents_chapter_selected_cb(self, widget, chapter):
        if chapter==-1:
            dialog=gtk.MessageDialog(
                    self.window, 
                    gtk.DIALOG_MODAL, 
                    gtk.MESSAGE_ERROR, 
                    gtk.BUTTONS_CLOSE, 
                    _("No such chapter."))
            result = dialog.run()
            dialog.destroy()
            return
        self.notebook.set_current_page(CONTEXT_TAB)
        self.pdb_canvas.set_chapter(chapter)
        self.pdb_canvas.redraw_canvas()
        self.state = ReadingState(self).enter()

    def bookshelf_book_selected_cb(self, widget, book):
        if book==-1:
            dialog=gtk.MessageDialog(
                    self.window, 
                    gtk.DIALOG_MODAL, 
                    gtk.MESSAGE_ERROR, 
                    gtk.BUTTONS_CLOSE, 
                    _("No such book."))
            result = dialog.run()
            dialog.destroy()
            return

        book_name, pdb_filename = self.bookshelf.get_book(book) 
        if self.open_pdb( pdb_filename ):
            self.pdb_filename = pdb_filename
            self.state = ContentState(self).enter()

def main():
    window=MainWindow()
    gtk.main()

if __name__ == "__main__":
    main()

