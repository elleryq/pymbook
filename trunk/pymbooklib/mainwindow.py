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
"""MainWindow"""
import sys
import os

import pygtk
pygtk.require('2.0')
import gtk
import gobject

import pdb
import version
from version import APP_NAME, APP_VERSION, APP_COMMENT, APP_AUTHORS
from pdbwidget import PDBWidget
from pdbcontents import PDBContents
from pdbcanvas import PDBCanvas
from bookshelf import BookshelfWidget, find_pdbs
from translation import _

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

    def __repr__(self):
        return "State"

class ShelfState( State ):
    def __init__(self, window):
        super(ShelfState, self).__init__(window)

    def enter(self):
        self.window.btn_shelf.set_sensitive( True )
        self.window.btn_content.set_sensitive( False )
        self.window.btn_return.set_sensitive( False )
        self.window.notebook.set_current_page(SHELF_TAB)
        return super(ShelfState, self).enter()

    def __repr__(self):
        return "ShelfState"

class ShelfCanBackState( ShelfState ):
    def __init__(self, window):
        super(ShelfCanBackState, self).__init__(window)

    def enter(self):
        self.window.btn_return.set_sensitive( True )
        return super(ShelfCanBackState, self).enter()

    def __repr__(self):
        return "ShelfCanBackState"

class ContentState( State ):
    def __init__(self, window):
        super(ContentState, self).__init__(window)

    def enter(self):
        self.window.btn_shelf.set_sensitive( True )
        self.window.btn_content.set_sensitive( False )
        self.window.btn_return.set_sensitive( False )
        self.window.notebook.set_current_page(CONTENT_TAB)
        return super(ContentState, self).enter()

    def __repr__(self):
        return "ContentState"

class ContentCanBackState( ContentState ):
    def __init__(self, window):
        super(ContentCanBackState, self).__init__(window)

    def enter(self):
        self.window.btn_return.set_sensitive( True )
        return super(ContentCanBackState, self).enter()

    def __repr__(self):
        return "ContentCanBackState"

class ReadingState( State ):
    def __init__(self, window):
        super(ReadingState, self).__init__(window)

    def enter(self):
        self.window.btn_shelf.set_sensitive( True )
        self.window.btn_content.set_sensitive( True )
        self.window.btn_return.set_sensitive( False )
        self.window.notebook.set_current_page(CONTEXT_TAB)
        return super(ReadingState, self).enter()

    def __repr__(self):
        return "ReadingState"

class MainWindow:
    ENTRY_SHELF_PATH = "bookshelf_path"
    ENTRY_WIDTH = "width"
    ENTRY_HEIGHT = "height"
    ENTRY_FONT_NAME = "font_name"
    ENTRY_FONT_SIZE = "font_size"
    ENTRY_CURRENT_PDB = "current_pdb"
    ENTRY_CURRENT_CHAPTER = "current_chapter"
    ENTRY_CURRENT_PAGE = "current_page"
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

    def __init__(self, filename=None):
        self.pdb_filename = None
        self.pdb = None
        self.pref_dlg = None
        self.load_config()
    	self.initialize_component()
        if filename and self.open_pdb( filename ):
            self.pdb_filename = filename

    def initialize_component(self):
    	try:
            self.builder = gtk.Builder()
            self.builder.set_translation_domain(APP_NAME)
            glade_file = os.path.join( os.path.dirname( version.__file__ ), 'main_window.glade' )
            self.builder.add_from_file( glade_file )
    	except BaseException, e:
            print e
            err_dialog = gtk.MessageDialog(
                    None, 
                    gtk.DIALOG_MODAL, 
                    gtk.MESSAGE_ERROR, 
                    gtk.BUTTONS_CLOSE, 
                    repr(e))
            result = err_dialog.run()
            err_dialog.destroy()
            self.leave()
            return
    	self.window = self.builder.get_object("window1")
        self.window.set_title( APP_NAME )
        self.window.set_position( gtk.WIN_POS_CENTER )
        # set minimal size
        self.window.set_size_request( 
                self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT )
        # resize to saved size
        self.window.resize(
                self.config.getint( self.SECTION, self.ENTRY_WIDTH ), 
                self.config.getint( self.SECTION, self.ENTRY_HEIGHT ) )

        self.btn_shelf = self.builder.get_object("btn_shelf")
        self.btn_content = self.builder.get_object("btn_content")
        self.btn_return = self.builder.get_object("btn_return")
        
        self.act_quit = self.builder.get_object("act_quit")
        self.notebook=self.builder.get_object("notebook1")

        # Recent files
        self.recent = gtk.RecentManager()
        menu_recent = gtk.RecentChooserMenu(self.recent)
        menu_recent.set_limit(10)
        self.file_filter = gtk.RecentFilter()
        self.file_filter.add_pattern("*.pdb")
        self.file_filter.add_pattern("*.updb")
        menu_recent.set_filter(self.file_filter)
        menu_recent.connect("item-activated", self.select_recent_cb)
        menuitem_recent = self.builder.get_object("mi_recent_files")
        menuitem_recent.set_submenu(menu_recent)

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
        frame.add(self.pdb_canvas)
        label = gtk.Label(_("Text"))
        self.notebook.append_page(frame, label)

        enter_reading_state = False
        if self.config.has_option(self.SECTION, self.ENTRY_CURRENT_CHAPTER):
            self.pdb_canvas.set_chapter(
                self.config.getint( self.SECTION, self.ENTRY_CURRENT_CHAPTER) )
            enter_reading_state = True
        if self.config.has_option(self.SECTION, self.ENTRY_CURRENT_PAGE ):
            self.pdb_canvas.set_page(
                self.config.getint( self.SECTION, self.ENTRY_CURRENT_PAGE) )
            enter_reading_state = True

        frame.show()
        self.pdb_canvas.show()

        filename = None
        if self.config.has_option( self.SECTION, self.ENTRY_CURRENT_PDB ):
            filename = self.config.get( self.SECTION, self.ENTRY_CURRENT_PDB )
        if filename and len(filename) and self.open_pdb( filename ):
            self.pdb_filename = filename
            if enter_reading_state:
                self.state = ReadingState(self).enter()
            else:
                self.state = ContentState(self).enter()
        else:
            self.state = ShelfState(self).enter()

        # connect signals
        self.bookshelf.connect("book_selected", self.bookshelf_book_selected_cb )
        self.pdb_contents.connect("chapter_selected", self.pdb_contents_chapter_selected_cb)
        self.pdb_canvas.connect("tell_callback", self.pdb_canvas_tell_callback )

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
        import urlparse
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
        uri = urlparse.urljoin( "file://", pdb_filename.encode('utf-8') )
        self.recent.add_full(uri, {'mime_type':'application/octet-stream',
                'app_name': APP_NAME, 'app_exec': 'pymbook', 'group':'pymbook',
                'display_name': self.pdb.book_name.encode('utf-8') } )
        return True

    def leave(self):
        rect = self.window.get_allocation()
        self.config.set( self.SECTION, self.ENTRY_WIDTH, rect.width )
        self.config.set( self.SECTION, self.ENTRY_HEIGHT, rect.height )
        self.config.set( self.SECTION, self.ENTRY_CURRENT_PDB,
                    self.pdb_filename )
        self.save_config()
    	gtk.main_quit()

    def window1_delete_event_cb(self, widget, event, data=None):
        self.act_quit.activate()

    def select_recent_cb(self, menu):
        filename = menu.get_current_item().get_uri_display()
        if self.open_pdb( filename ):
            self.pdb_filename = filename
            self.state = ContentState( self ).enter()

    def act_quit_activate_cb(self, b):
        self.leave()
    
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
            builder.set_translation_domain(APP_NAME)
            glade_file = os.path.join( os.path.dirname( version.__file__ ), 'preference_dialog.glade' )
            pref_dlg = builder.add_from_file( glade_file )
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
        if isinstance(self.state, ReadingState):
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

    def pdb_canvas_tell_callback(self, widget, chapter, page):
        self.config.set( self.SECTION, self.ENTRY_CURRENT_CHAPTER, chapter )
        self.config.set( self.SECTION, self.ENTRY_CURRENT_PAGE, page )
        self.save_config()
