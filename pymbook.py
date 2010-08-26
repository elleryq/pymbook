#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import locale, gettext

import pygtk
pygtk.require('2.0')
import gtk
import math
import cairo

import pdb

APP="pymbook"
DIR="/usr/share/locale"

class Pager:
    def __init__(self, content, width, height):
        self.content=content
        words=len(self.content)
        self.pages=[]
        words_in_a_page=width*height
        i=0
        pages=words/words_in_a_page
        if (words%words_in_a_page)>0:
            pages=pages+1
        for i in range(pages+1):
            self.pages.append( content[i*words_in_a_page:((i+1)*words_in_a_page)] )

    def get_page(self, page):
        return self.pages[page]

    def get_total_pages( self ):
        return len(self.pages)

class PDBCanvas(gtk.DrawingArea):
    font_name = '文泉驛微米黑'
    font_size = 16
    pdb=None
    page=0

    def __init__(self):
        super(PDBCanvas, self).__init__()
        self.set_events(gtk.gdk.SCROLL_MASK)

        self.connect("expose_event", self.expose)
        self.connect("scroll-event", self.scroll_event )

    def set_pdb(self, pdb):
        self.pdb=pdb
        page=0

    def set_font(self, font):
        t=font.split(' ')
        self.font_name = t[0]
        self.font_size = int(t[-1])

    def expose(self, widget, event):
        if not self.pdb:
            return False

        cx=widget.window.cairo_create()

        # get canvas size
        rect=self.get_allocation()

        # draw rectangle for verify
        cx.save()
        cx.set_source_rgb(.6, 0, 0)
        cx.rectangle( 0, 0, rect.width, rect.height )
        cx.stroke()
        cx.restore()

        print rect
        cell_width=self.font_size+self.font_size/4
        cell_height=self.font_size+self.font_size/2

        columns_in_page=len(range(rect.width-cell_width*2, rect.y,
                    -cell_width))
        words_in_line=len(range(cell_height, rect.height, cell_height))
        self.pager=Pager(self.pdb.chapter(0), columns_in_page, words_in_line)
        s=self.pager.get_page(self.page)

        cx.save()
        cx.set_source_rgb( 0, 0, 0 )
        cx.select_font_face( self.font_name )
        cx.set_font_size( self.font_size)

        pos=0
        for x in range( rect.width-cell_width*2, rect.y, -cell_width ):
            for y in range( cell_height, rect.height, cell_height ):
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

    def redraw_canvas(self):
        if self.window:
            alloc=self.get_allocation()
            rect=gtk.gdk.Rectangle(0, 0, alloc.width, alloc.height)
            self.window.invalidate_rect(rect, True)
            self.window.process_updates(True)

    def scroll_event(self, widget, event):
        if not self.pdb:
            return False

        print event.direction
        if event.direction==gtk.gdk.SCROLL_UP:
            if self.page>0:
                self.page=self.page-1
        elif event.direction==gtk.gdk.SCROLL_DOWN:
            self.page=self.page+1
            if self.page>self.pager.get_total_pages():
                self.page=self.pager.get_total_pages()
        self.redraw_canvas()
        return True

class MainWindow:
    pdb=None
    pdb_filename=None
    font_name=None

    def __init__(self):
    	self.initializeComponent()

    def initializeComponent(self):
    	try:
    		self.builder = gtk.Builder()
    		ui_filename = "main_window.xml"
    		self.builder.add_from_file( ui_filename )
    	except Exception, e:
    		print e
    		return
    	self.window = self.builder.get_object("window1")
        self.window.set_position( gtk.WIN_POS_CENTER )
        self.act_quit = self.builder.get_object("act_quit")
        self.vbox1 = self.builder.get_object("vbox1")
        self.pdb_canvas=PDBCanvas()
        self.pdb_canvas.set_size_request( 800, 600 )
        self.vbox1.pack_start( self.pdb_canvas, False, False, 0)
    	self.builder.connect_signals(self)
        self.pdb_canvas.show()
    	self.window.show()

    def window1_delete_event_cb(self, widget, event, data=None):
        self.act_quit.activate()

    def act_quit_activate_cb(self, b):
    	gtk.main_quit()
    
    def act_about_activate_cb(self, b):
        dialog=gtk.AboutDialog()
        dialog.set_name('')
        dialog.set_version('')
        dialog.set_authors( [''] )
        dialog.set_comments('')
        dialog.set_license('Distributed under the GPL3.')
        dialog.run()
        dialog.destroy()

    def act_open_activate_cb(self, b):
        dialog=gtk.FileChooserDialog( "Open...",
                None,
                gtk.FILE_CHOOSER_ACTION_OPEN,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                 gtk.STOCK_OPEN, gtk.RESPONSE_OK) )
        dialog.set_default_response(gtk.RESPONSE_OK)

        filter=gtk.FileFilter()
        filter.set_name("PDB/uPDB files")
        filter.add_pattern("*.pdb")
        filter.add_pattern("*.updb")
        dialog.add_filter(filter)
    
        response=dialog.run()
        if response==gtk.RESPONSE_OK:
            self.pdb_filename=dialog.get_filename()
            self.pdb=pdb.PDBFile(self.pdb_filename).parse()
            self.pdb_canvas.set_pdb( self.pdb )
            self.pdb_canvas.redraw_canvas()
        elif response==gtk.RESPONSE_CANCEL:
            pass
        dialog.destroy()

    def act_font_activate_cb(self, b):
        dialog=gtk.FontSelectionDialog('Choose font')
        dialog.set_default_response(gtk.RESPONSE_OK)
        response=dialog.run()
        if response==gtk.RESPONSE_OK:
            self.font_name=dialog.get_font_name()
            self.pdb_canvas.set_font(self.font_name)
        elif response==gtk.RESPONSE_CANCEL:
            pass
        dialog.destroy()
        self.pdb_canvas.redraw_canvas()

def tr( s ):
    return s

def main():
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
    window=MainWindow()
    gtk.main()

if __name__ == "__main__":
    main()

