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
import pango

import pdb
import version
from version import APP_NAME, APP_VERSION, APP_COMMENT, APP_AUTHORS
from pdbwidget import PDBWidget
from pdbcontents import PDBContents
from pdbcanvas import PDBCanvas
from bookshelf import BookshelfWidget, find_pdbs
import config
from state import ShelfState, ShelfCanBackState 
from state import ContentState, ContentCanBackState 
from state import ReadingState
from translation import _
from utils import get_font_tuple

class MainWindow:
    """MainWindow"""
    def __init__(self, filename=None):
        self.pdb_filename = None
        self.pdb = None
        self.pref_dlg = None
        self.config = config.Config()
        self.config.load()
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
            print( e )
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
                config.DEFAULT_WIDTH, config.DEFAULT_HEIGHT )
        # resize to saved size
        self.window.resize(
                self.config[config.ENTRY_WIDTH], 
                self.config[config.ENTRY_HEIGHT] )

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
                self.config[config.ENTRY_FONT_NAME],
                self.config[config.ENTRY_FONT_SIZE] )

        # Add bookshelf tab
        self.bookshelf = BookshelfWidget( self.config[config.ENTRY_SHELF_PATH] )
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
        if self.config[config.ENTRY_CURRENT_CHAPTER]:
            self.pdb_canvas.set_chapter(
                self.config[config.ENTRY_CURRENT_CHAPTER] )
            enter_reading_state = True
        if self.config[config.ENTRY_CURRENT_PAGE]:
            self.pdb_canvas.set_page(
                self.config[config.ENTRY_CURRENT_PAGE] )
            enter_reading_state = True

        frame.show()
        self.pdb_canvas.show()

        filename = None
        if self.config[config.ENTRY_CURRENT_PDB]:
            filename = self.config[config.ENTRY_CURRENT_PDB]
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
        self.config[config.ENTRY_WIDTH] = rect.width
        self.config[config.ENTRY_HEIGHT] = rect.height
        self.config[config.ENTRY_CURRENT_PDB] = self.pdb_filename
        self.config.save()
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
                self.config[config.ENTRY_FONT_NAME],
                self.config[config.ENTRY_FONT_SIZE] ) )
        response=dialog.run()
        if response==gtk.RESPONSE_OK:
            font_name=dialog.get_font_name()
            self.bookshelf.set_font( font_name )
            self.pdb_contents.set_font( font_name )
            self.pdb_canvas.set_font( font_name )
            font, font_size = get_font_tuple( font_name )
            self.config[config.ENTRY_FONT_NAME] = font
            self.config[config.ENTRY_FONT_SIZE] = font_size
            self.config.save()
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
        shelf_path=os.path.expanduser( self.config[config.ENTRY_SHELF_PATH] ).encode( sys.getfilesystemencoding() )
        chooser_btn.set_current_folder( shelf_path )

        result=pref_dlg.run()
        # OK
        if result==gtk.RESPONSE_OK:
            selected_path = chooser_btn.get_filename()
            if selected_path:
                self.config[config.ENTRY_SHELF_PATH] = selected_path
                self.config.save()
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
        self.config[config.ENTRY_CURRENT_CHAPTER] = chapter
        self.config[config.ENTRY_CURRENT_PAGE] = page
        self.config.save()
