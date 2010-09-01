#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import locale, gettext

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import math
import cairo

import pdb

APP="pymbook"
DIR="/usr/share/locale"
VERSION="0.1"
COMMENT=""

INDEX_TAB=0
CONTENT_TAB=1

def tr( s ):
    return s

locale.setlocale( locale.LC_ALL, '' )
locale.bindtextdomain( APP, DIR )
gettext.bindtextdomain( APP, DIR )
locale.textdomain( APP )
try:
    lang=gettext.translation( APP, DIR )
    lang.install( APP, DIR )
    _=lang.gettext
except:
    # fallback
    _=tr

class ContentPager:
    def __init__(self, pdb, width, height):
        self.current=0
        self.pages=[]
        for num in range(pdb.chapters):
            content = pdb.chapter(num)
            columns=0
            words=0
            page=[]
            num_in_chapter=0
            for c in content:
                if c==u'\u000a' or words>=height:
                    columns=columns+1
                    words=0
                if c!='\u000d' and c!='\u000a':
                    words=words+1
                page.append( c )
                if columns>=width:
                    self.pages.append( (num, num_in_chapter, page) )
                    num_in_chapter=num_in_chapter+1
                    page=[]
                    columns=0
                    words=0
            self.pages.append( (num, num_in_chapter, page) )

    def get_current_page(self):
        return self.pages[self.current][2]

    def get_current_page_in_chapter(self):
        return self.pages[self.current][1]

    def get_current_chapter(self):
        return self.pages[self.current][0]

    def count_pages(self):
        return len(self.pages)

    def count_chapter_pages(self,chapter):
        pages=[ ch for ch, n_in_p, p in self.pages if ch==chapter ]
        return len(pages)

    def go_chapter(self,chapter):
        self.current=0
        for chap, n_in_page, page in self.pages:
            if chap==chapter:
                break
            self.current=self.current+1

    def go_previous(self):
        self.current=self.current-1
        if self.current<0:
            self.current=0

    def go_next(self):
        self.current=self.current+1
        if self.current>=len(self.pages):
            self.current=len(self.pages)-1

class PDBWidget(gtk.DrawingArea):
    font_name = '文泉驛微米黑'
    font_size = 16
    pdb = None

    def __init__(self):
        super(PDBWidget, self).__init__()

    def set_font(self, font):
        t=font.split(' ')
        self.font_name = t[0]
        self.font_size = int(t[-1])

    def redraw_canvas(self):
        if self.window:
            alloc=self.get_allocation()
            rect=gtk.gdk.Rectangle(0, 0, alloc.width, alloc.height)
            self.window.invalidate_rect(rect, True)
            self.window.process_updates(True)

class PDBIndex(PDBWidget):
    __gsignals__ = dict(chapter_selected=(gobject.SIGNAL_RUN_FIRST,
                                      gobject.TYPE_NONE,
                                      (gobject.TYPE_INT,)))

    def __init__(self):
        super(PDBIndex, self).__init__()
        self.old_rect=None
        self.recalc=True
        self.pdb=None

        self.connect("expose_event", self.expose)
        self.connect("scroll-event", self.scroll_event )
        self.connect("button_release_event", self.button_release)
        self.connect("motion-notify-event", self.motion_notify)
        self.add_events( gtk.gdk.BUTTON_PRESS_MASK | 
                        gtk.gdk.BUTTON_RELEASE_MASK | 
                        gtk.gdk.POINTER_MOTION_MASK )

    def set_pdb(self, pdb):
        self.pdb=pdb

    def expose(self, widget, event):
        if not self.pdb:
            return False

        cx=widget.window.cairo_create()

        # get canvas size
        rect=self.get_allocation()

        cell_width=self.font_size*2
        cell_height=self.font_size+self.font_size/3

        # The first time.
        if not self.old_rect:
            self.recalc=True
        # If windows size is changed.
        elif self.old_rect and self.old_rect!=rect:
            self.recalc=True

        if self.recalc:
            self.x_pos_list=range(rect.width-cell_width*2, rect.x+cell_width, -cell_width)
            self.y_pos_list=range(0, rect.height, (rect.height-1) )
            self.regions=[ gtk.gdk.region_rectangle( (x, self.y_pos_list[0], cell_width, self.y_pos_list[-1]-self.y_pos_list[0]) ) for x in self.x_pos_list[1:]]
            columns_in_page=len( self.x_pos_list )
            self.old_rect=rect
            self.recalc=False

        # draw grid
        cx.set_source_rgb( 0, 0, 0 )
        for x in self.x_pos_list:
            cx.save()
            cx.move_to( x, self.y_pos_list[0] )
            cx.line_to( x, self.y_pos_list[-1] )
            cx.stroke()
            cx.restore()
        for y in self.y_pos_list:
            cx.save()
            cx.move_to( self.x_pos_list[0], y )
            cx.line_to( self.x_pos_list[-1], y )
            cx.stroke()
            cx.restore()

        cx.save()
        cx.select_font_face( self.font_name )
        cx.set_font_size( self.font_size)
        start_x = 1
        start_y = 0
        columns_in_page=len( self.x_pos_list )
        for chapter_title in self.pdb.contents:
            x = self.x_pos_list[ start_x ] + cell_width/4
            y = self.y_pos_list[ start_y ] + cell_height
            for c in chapter_title:
                cx.move_to( x, y )
                cx.show_text( c )
                y=y+cell_height
            start_x=start_x+1
            if start_x>columns_in_page:
                start_x=1
                start_y=start_y+1
        cx.restore()

        return False

    def scroll_event(self, widget, event):
        return True

    def button_release(self, widget, event):
        if not self.pdb:
            return False
        self.emit("chapter_selected", self.which_chapter(event.x, event.y ))
        return False
    
    def motion_notify(self, widget, event):
        if not self.pdb:
            return False
        # TODO:
        #print("which chapter? %d" % self.which_chapter(event.x, event.y) )
        return False

    def which_chapter(self, x, y):
        chapter=0
        for r in self.regions:
            if r.point_in( int(x), int(y) ):
                break
            chapter=chapter+1
        if chapter>=self.pdb.chapters:
            chapter=-1
        return chapter

class PDBCanvas(PDBWidget):
    def __init__(self):
        super(PDBCanvas, self).__init__()
        self.old_rect=None
        self.pager=None
        self.recalc=True
        self.pdb=None
        self.chapter=0

        self.set_events(gtk.gdk.SCROLL_MASK)

        self.connect("expose_event", self.expose)
        self.connect("scroll-event", self.scroll_event )

    def set_pdb(self, pdb):
        self.pdb=pdb
        self.page=0
        self.chapter=0

    def set_chapter(self, chapter):
        self.chapter=chapter
        self.recalc=True

    def expose(self, widget, event):
        if not self.pdb:
            return False

        cx=widget.window.cairo_create()

        # get canvas size
        rect=self.get_allocation()

        cell_width=self.font_size+self.font_size/4
        cell_height=self.font_size+self.font_size/3

        # The first time.
        if not self.old_rect:
            self.recalc=True
        # If windows size is changed.
        elif self.old_rect and self.old_rect!=rect:
            self.recalc=True

        if self.recalc:
            self.x_pos_list=range(rect.width-cell_width*2, rect.x+cell_width, -cell_width)
            self.y_pos_list=range(cell_height, rect.height, cell_height)
            columns_in_page=len( self.x_pos_list )
            words_in_line=len(self.y_pos_list)
            self.pager=ContentPager(self.pdb, columns_in_page, words_in_line)
            self.pager.go_chapter(self.chapter)
            self.old_rect=rect
            self.recalc=False
        s=self.pager.get_current_page()

        # draw chapter indicator
        cx.save()
        seg=rect.width/self.pdb.chapters
        x=rect.width-(self.pager.get_current_chapter()+1)*seg
        cx.set_source_rgb( 1.0, 0, 0 )
        cx.move_to( x, 0 )
        cx.line_to( x+seg, 0 )
        cx.stroke()
        cx.restore()

        # draw page/chapter indicator
        cx.save()
        seg=rect.width/self.pager.count_chapter_pages(self.pager.get_current_chapter())
        x=rect.width-(self.pager.get_current_page_in_chapter()+1)*seg
        cx.set_source_rgb( 1.0, 0, 0 )
        cx.move_to( x, rect.height-1 )
        cx.line_to( x+seg, rect.height-1 )
        cx.stroke()
        cx.restore()

        # draw text
        cx.save()
        cx.set_source_rgb( 0, 0, 0 )
        cx.select_font_face( self.font_name )
        cx.set_font_size( self.font_size)
        pos=0
        for x in self.x_pos_list:
            for y in self.y_pos_list:
                if pos>=len(s):
                    break
                if s[pos]==u'\u000d': # skip 0x0d0x0a
                    pos=pos+2
                    break
                elif s[pos]==u'\u3000':
                    pos=pos+1
                    continue
                cx.move_to( x, y )
                cx.show_text( s[pos] )
                pos=pos+1
        
        cx.restore()

        return False

    def scroll_event(self, widget, event):
        if not self.pdb:
            return False

        if event.direction==gtk.gdk.SCROLL_UP:
            self.pager.go_previous()
        elif event.direction==gtk.gdk.SCROLL_DOWN:
            self.pager.go_next()
        self.chapter=self.pager.get_current_chapter()
        self.redraw_canvas()
        return True

class MainWindow:
    DEFAULT_WIDTH = 640
    DEFAULT_HEIGHT = 480
    DEFAULT_SHELF_PATH = "~/download/"
    ENTRY_SHELF_PATH = "bookshelf_path"
    ENTRY_WIDTH = "width"
    ENTRY_HEIGHT = "height"
    DEFAULT_CONFIG_CONTENT = """
[mbook]
%s = %s
%s = %d
%s = %d
""" % ( ENTRY_SHELF_PATH, DEFAULT_SHELF_PATH, 
        ENTRY_WIDTH, DEFAULT_WIDTH, 
        ENTRY_HEIGHT, DEFAULT_HEIGHT )
    CONFIG_FILENAME = "~/.config/pymbook.conf"
    SECTION = 'mbook'

    def __init__(self):
        self.pdb = None
        self.pdb_filename = None
        self.font_name = '文泉驛微米黑'
        self.font_size = 16
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
        self.window.set_title( APP )
        self.window.set_position( gtk.WIN_POS_CENTER )

        self.act_quit = self.builder.get_object("act_quit")
        self.notebook=self.builder.get_object("notebook1")
      
        # Add index tab
        self.pdb_index=PDBIndex()
        self.pdb_index.set_size_request( 
                self.config.getint( self.SECTION, self.ENTRY_WIDTH ), 
                self.config.getint( self.SECTION, self.ENTRY_HEIGHT ) )
        frame=gtk.Frame()
        frame.show()
        frame.add( self.pdb_index )
        label = gtk.Label( _("Index") )
        self.notebook.append_page( frame, label )
        self.pdb_index.show()

        # Add content tab
        self.pdb_canvas=PDBCanvas()
        frame=gtk.Frame()
        frame.set_size_request(
                self.config.getint( self.SECTION, self.ENTRY_WIDTH ), 
                self.config.getint( self.SECTION, self.ENTRY_HEIGHT ) )
        frame.show()
        frame.add(self.pdb_canvas)
        label = gtk.Label(_("Content"))
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
        dialog.set_name( APP )
        dialog.set_version( VERSION )
        dialog.set_authors( ['Yan-ren Tsai'] )
        dialog.set_comments( COMMENT )
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
        elif response==gtk.RESPONSE_CANCEL:
            pass
        dialog.destroy()

    def act_font_activate_cb(self, b):
        dialog=gtk.FontSelectionDialog(_("Choose font"))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_font_name( "%s %d" % (self.font_name, self.font_size) )
        response=dialog.run()
        if response==gtk.RESPONSE_OK:
            self.font_name=dialog.get_font_name()
            self.pdb_index.set_font(self.font_name)
            self.pdb_canvas.set_font(self.font_name)
        elif response==gtk.RESPONSE_CANCEL:
            pass
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
        if result==0:
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

def find_pdbs(path):
    """Find all pdb/updb files according the specified path(absolute path).
    And return the filename lists which contain full path.
    """
    import glob
    import os
    return glob.glob( os.path.join( path, "*.pdb" ) ) + glob.glob( os.path.join( path, "*.updb" ) )

def main():
    window=MainWindow()
    gtk.main()

if __name__ == "__main__":
    main()

# TODO: Index paging.
# TODO: Shelf function.
# TODO: configuration.

