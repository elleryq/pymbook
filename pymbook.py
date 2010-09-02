#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import locale, gettext

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

DIR="/usr/share/locale"

SHELF_TAB = 0
INDEX_TAB = 1
CONTENT_TAB = 2

def tr( s ):
    return s

locale.setlocale( locale.LC_ALL, '' )
locale.bindtextdomain( APP_NAME, DIR )
gettext.bindtextdomain( APP_NAME, DIR )
locale.textdomain( APP_NAME )
try:
    lang=gettext.translation( APP_NAME, DIR )
    lang.install( APP_NAME, DIR )
    _=lang.gettext
except:
    # fallback
    _=tr

class MainWindow:
    ENTRY_SHELF_PATH = "bookshelf_path"
    ENTRY_WIDTH = "width"
    ENTRY_HEIGHT = "height"
    ENTRY_FONT_NAME = "font_name"
    ENTRY_FONT_SIZE = "font_size"
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
    	except Exception, e:
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

        self.act_quit = self.builder.get_object("act_quit")
        self.notebook=self.builder.get_object("notebook1")

        font = "%s %d" % ( 
                self.config.get( self.SECTION, self.ENTRY_FONT_NAME ),
                self.config.getint( self.SECTION, self.ENTRY_FONT_SIZE ) )

        # Add bookshelf tab
        self.bookshelf = BookshelfWidget( self.config.get( self.SECTION, self.ENTRY_SHELF_PATH ) )
        self.bookshelf.set_size_request(
                self.config.getint( self.SECTION, self.ENTRY_WIDTH ), 
                self.config.getint( self.SECTION, self.ENTRY_HEIGHT ) )
        self.bookshelf.set_font( font )
        frame=gtk.Frame()
        frame.show()
        frame.add( self.bookshelf )
        label = gtk.Label( _("Bookshelf") )
        self.notebook.append_page( frame, label )
        self.bookshelf.show()

        # Add contents tab
        self.pdb_index=PDBContents()
        self.pdb_index.set_size_request( 
                self.config.getint( self.SECTION, self.ENTRY_WIDTH ), 
                self.config.getint( self.SECTION, self.ENTRY_HEIGHT ) )
        self.pdb_index.set_font( font )
        frame=gtk.Frame()
        frame.show()
        frame.add( self.pdb_index )
        label = gtk.Label( _("Contents") )
        self.notebook.append_page( frame, label )
        self.pdb_index.show()

        # Add text tab
        self.pdb_canvas=PDBCanvas()
        frame=gtk.Frame()
        frame.set_size_request(
                self.config.getint( self.SECTION, self.ENTRY_WIDTH ), 
                self.config.getint( self.SECTION, self.ENTRY_HEIGHT ) )
        self.pdb_canvas.set_font( font )
        frame.show()
        frame.add(self.pdb_canvas)
        label = gtk.Label(_("Text"))
        self.notebook.append_page(frame, label)
        self.pdb_canvas.show()

        # connect signals
        self.pdb_index.connect("chapter_selected", self.pdbindex_chapter_selected_cb)
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

    def window1_delete_event_cb(self, widget, event, data=None):
        self.act_quit.activate()

    def act_quit_activate_cb(self, b):
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

        filter=gtk.FileFilter()
        filter.set_name(_("PDB/uPDB files"))
        filter.add_pattern("*.pdb")
        filter.add_pattern("*.updb")
        dialog.add_filter(filter)
    
        response=dialog.run()
        if response==gtk.RESPONSE_OK:
            self.pdb_filename=dialog.get_filename()
            self.pdb=pdb.PDBFile(self.pdb_filename).parse()
            self.pdb_index.set_pdb( self.pdb )
            self.pdb_index.redraw_canvas()
            self.pdb_canvas.set_pdb( self.pdb )
            self.pdb_canvas.redraw_canvas()
            self.notebook.set_current_page(INDEX_TAB)
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
            self.pdb_index.set_font( font_name )
            self.pdb_canvas.set_font( font_name )
            font = font_name.split()
            self.config.set( self.SECTION, self.ENTRY_FONT_NAME, font[0] )
            self.config.set( self.SECTION, self.ENTRY_FONT_SIZE, font[-1] )
            self.save_config()
        dialog.destroy()
        self.pdb_index.redraw_canvas()
        self.pdb_canvas.redraw_canvas()

    def act_index_activate_cb(self, b):
        self.notebook.set_current_page(INDEX_TAB)

    def act_preference_activate_cb(self, b):
        try:
            builder = gtk.Builder()
            pref_dlg = builder.add_from_file( "preference_dialog.glade" )
        except Exception, e:
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

    def pdbindex_chapter_selected_cb(self, widget, chapter):
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
        self.notebook.set_current_page(CONTENT_TAB)
        self.pdb_canvas.set_chapter(chapter)
        self.pdb_canvas.redraw_canvas()

def main():
    window=MainWindow()
    gtk.main()

if __name__ == "__main__":
    main()

# TODO: Shelf function.
