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

"""PDBContents"""
import gobject
import gtk
from pdbwidget import PDBWidget
from utils import find_pdbs
from pageddatasource import PagedDataSource

class BookshelfWidget(gtk.DrawingArea):
    __gsignals__ = dict(book_selected=(gobject.SIGNAL_RUN_FIRST,
                                      gobject.TYPE_NONE,
                                      (gobject.TYPE_INT,)))

    def __init__( self, shelf_path ):
        super(BookshelfWidget, self).__init__()
        self.books = find_pdbs( shelf_path )
        self.old_rect=None
        self.recalc=True

        self.add_events( gtk.gdk.BUTTON_PRESS_MASK | 
                        gtk.gdk.BUTTON_RELEASE_MASK | 
                        gtk.gdk.POINTER_MOTION_MASK |
                        gtk.gdk.KEY_PRESS_MASK )

        self.connect("expose_event", self.expose)
        self.connect("scroll-event", self.scroll_event )
        self.connect("button_release_event", self.button_release)
        self.connect("motion-notify-event", self.motion_notify)
        self.connect("key-release-event", self.key_release )

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

    def _draw_indicator(self, cx, x, y, seg):
        cx.save()
        cx.set_source_rgb( 1.0, 0, 0 )
        cx.move_to( x, y )
        cx.line_to( x+seg, y )
        cx.stroke()
        cx.restore()

    def _draw_line(self, cx, pos1, pos2):
        """
        Draw line.
        pos1 and pos2 are tutple contain x and y.
        """
        x1, y1 = pos1
        x2, y2 = pos2
        cx.save()
        cx.move_to( x1, y1 )
        cx.line_to( x2, y2 )
        cx.stroke()
        cx.restore()

    def expose(self, widget, event):
        if not self.books:
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
            columns_in_page=len( self.x_pos_list )-1
            self.datasource = PagedDataSource( self.books, columns_in_page )
            self.old_rect=rect
            self.recalc=False

        # draw grid
        cx.set_source_rgb( 0, 0, 0 )
        for x in self.x_pos_list:
            self._draw_line( cx, (x, self.y_pos_list[0]),
                    (x, self.y_pos_list[-1]) )
        for y in self.y_pos_list:
            self._draw_line( cx, (self.x_pos_list[0], y),
                    (self.x_pos_list[-1], y) )

        # draw page indicator
        if self.datasource.count_pages()>1:
            seg = rect.width/self.datasource.count_pages()
            x = rect.width-(self.datasource.current_page+1)*seg
            self._draw_indicator( cx, x, rect.height-1, seg )

        # Show shelf
        cx.save()
        if self.font_name and self.font_size:
            cx.select_font_face( self.font_name )
            cx.set_font_size( self.font_size)
        start_x = 1
        start_y = 0
        columns_in_page=len( self.x_pos_list )
        try:
            for book_name, pdb_filename in self.datasource.get_current_page():
                x = self.x_pos_list[ start_x ] + cell_width/4
                y = self.y_pos_list[ start_y ] + cell_height
                for c in book_name:
                    cx.move_to( x, y )
                    cx.show_text( c )
                    y = y + cell_height
                    if y>self.y_pos_list[ -1 ]:
                        break
                start_x = start_x + 1
                if start_x>columns_in_page:
                    start_x = 1
        except IndexError, e:
            print start_x, len(self.x_pos_list), columns_in_page, \
    len(self.get_current_page())
        cx.restore()

        return False

    def redraw_later(self):
        import glib
        if self.timer:
            glib.source_remove( self.timer )
        self.timer = glib.timeout_add( 500, self.redraw_canvas )

    def scroll_event(self, widget, event):
        if not self.books:
            return False

        if event.direction==gtk.gdk.SCROLL_UP:
            self.datasource.go_previous()
        elif event.direction==gtk.gdk.SCROLL_DOWN:
            self.datasource.go_next()
        self.redraw_later()
        return True

    def button_release(self, widget, event):
        if not self.books:
            return False
        self.emit("book_selected", self.which_book(event.x, event.y ))
        return False
    
    def motion_notify(self, widget, event):
        if not self.books:
            return False
        # TODO:
        #print("which chapter? %d" % self.which_chapter(event.x, event.y) )
        return False

    def key_release(self, widget, event ):
        if not self.books:
            return False
        if event.keyval==gtk.gdk.keyval_from_name("Page_Up"):
            self.datasource.go_previous()
        elif event.keyval==gtk.gdk.keyval_from_name("Page_Down"):
            self.datasource.go_next()
        elif event.keyval==gtk.gdk.keyval_from_name("Up"):
            self.datasource.go_previous()
        elif event.keyval==gtk.gdk.keyval_from_name("Down"):
            self.datasource.go_next()
        self.redraw_later()
        return False

    def which_book(self, x, y):
        selected=0
        for r in self.regions:
            if r.point_in( int(x), int(y) ):
                break
            selected=selected+1
        if self.datasource.current_page>0:
            for page in self.pages[:self.datasource.current_page]:
                selected = selected + len(page)
        book = selected
        if book>=len(self.books):
            book = -1
        return book

    def get_book( self, idx ):
        return self.books[ idx ]
