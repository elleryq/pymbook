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
    current=0
    pages=[]

    def __init__(self, pdb, width, height):
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
            self.current=self.current+1
            if chap==chapter:
                break

    def go_previous(self):
        self.current=self.current-1
        if self.current<0:
            self.current=0

    def go_next(self):
        self.current=self.current+1
        if self.current>=len(self.pages):
            self.current=len(self.pages)-1

class PDBCanvas(gtk.DrawingArea):
    font_name = '文泉驛微米黑'
    font_size = 16
    pdb=None
    old_rect=None
    pager=None

    def __init__(self):
        super(PDBCanvas, self).__init__()
        self.set_events(gtk.gdk.SCROLL_MASK)

        self.connect("expose_event", self.expose)
        self.connect("scroll-event", self.scroll_event )

    def set_pdb(self, pdb):
        self.pdb=pdb
        self.page=0
        self.chapter=0

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

        cell_width=self.font_size+self.font_size/4
        cell_height=self.font_size+self.font_size/3

        if not self.old_rect and self.old_rect!=rect:
            self.x_pos_list=range(rect.width-cell_width*2, rect.x+cell_width, -cell_width)
            self.y_pos_list=range(cell_height, rect.height, cell_height)
            columns_in_page=len( self.x_pos_list )
            words_in_line=len(self.y_pos_list)
            current_chapter=None
            if self.pager:
                current_chapter=self.pager.current_chapter()
            self.pager=Pager(self.pdb, columns_in_page, words_in_line)
            if current_chapter:
                self.pager.go_chapter(current_chapter)
            self.old_rect=rect
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

    def redraw_canvas(self):
        if self.window:
            alloc=self.get_allocation()
            rect=gtk.gdk.Rectangle(0, 0, alloc.width, alloc.height)
            self.window.invalidate_rect(rect, True)
            self.window.process_updates(True)

    def scroll_event(self, widget, event):
        if not self.pdb:
            return False

        if event.direction==gtk.gdk.SCROLL_UP:
            self.pager.go_previous()
        elif event.direction==gtk.gdk.SCROLL_DOWN:
            self.pager.go_next()
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
    		ui_filename = "main_window.glade"
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

