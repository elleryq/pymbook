#!/usr/bin/env python3
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

"""Bookshelf widget"""
import logging

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GObject, Gtk

from .utils import find_pdbs
from .utils import convert_columns_to_pages
from .customdrawingarea import CustomDrawingArea
from .pageddatasource import PagedDataSource
from .translation import _

class BookshelfWidget(CustomDrawingArea):
    __gsignals__ = dict(book_selected=(GObject.SignalFlags.RUN_FIRST,
                                      GObject.TYPE_NONE,
                                      (GObject.TYPE_INT,)))

    def __init__( self, shelf_path ):
        super(BookshelfWidget, self).__init__()
        self.books = find_pdbs( shelf_path )

        self.connect("draw", self.expose)
        self.connect("scroll-event", self.scroll_event)
        self.connect("button-release-event", self.button_release)
        self.connect("motion-notify-event", self.motion_notify)
        self.connect("key-press-event", self.key_press)
        self.connect("size-allocate", self.configure)

    def get_cell_size(self):
        return (self.font_size * 2, self.font_size + self.font_size // 3)

    def reload(self, shelf_path):
        self.books = find_pdbs(shelf_path, strict=True)
        self.do_calc()
        self.redraw_canvas()

    def do_calc(self):
        rect = self.get_allocation()
        cell_width, cell_height = self.get_cell_size()
        self.x_pos_list = range(
            rect.width - cell_width * 2, rect.x + cell_width, -cell_width)
        self.y_pos_list = range(0, rect.height, max(1, rect.height - 1))
        if not self.x_pos_list:
            self.x_pos_list = [max(0, rect.width - cell_width)]
        if not self.y_pos_list:
            self.y_pos_list = [0]
        self.regions = [ 
            (x, self.y_pos_list[0], cell_width,
             max(1, self.y_pos_list[-1] - self.y_pos_list[0]))
            for x in self.x_pos_list[1:]
        ]
        columns_in_page = max(1, len(self.x_pos_list) - 1)
        self.datasource = PagedDataSource( convert_columns_to_pages(
                    self.books, columns_in_page ) )
    
    def draw_string(self, cx, s, x, y, limit):
        cell_width, cell_height = self.get_cell_size()
        for c in s:
            cx.move_to( x, y )
            cx.show_text( c )
            y = y + cell_height
            if y > limit:
                break

    def configure(self, widget, allocation):
        if not self.books:
            return

        self.do_calc()

    def expose(self, widget, cx):
        if not self.books:
            layout = self.create_pango_layout(_("No books found."))
            Gtk.render_layout(self.get_style_context(), cx, 10, 10, layout)
            return False

        # get canvas size
        rect=self.get_allocation()

        cell_width, cell_height = self.get_cell_size()

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
            cx.select_font_face(self.font_name)
            cx.set_font_size(self.font_size)
        start_x = 1
        start_y = 0
        columns_in_page=len( self.x_pos_list )
        try:
            padding_left = cell_width/4
            for book_name, pdb_filename in self.datasource.get_current_page():
                self.draw_string( cx, book_name, 
                        self.x_pos_list[start_x] + padding_left,
                        self.y_pos_list[start_y] + cell_height, 
                        self.y_pos_list[-1] )
                start_x = start_x + 1
                if start_x>columns_in_page:
                    start_x = 1
        except IndexError as e:
            logging.error( e )
            logging.debug( 
                "start_x=%d len(x_pos_list)=%d columns_in_page=%d len(datasource.get_current_page())" % (
                    start_x, len(self.x_pos_list),
                    columns_in_page, 
                    len(self.datasource.get_current_page()) ) )
        cx.restore()

        return False

    def scroll_event(self, widget, event):
        if not self.books:
            return False

        if event.direction == Gdk.ScrollDirection.UP:
            self.datasource.go_previous()
        elif event.direction == Gdk.ScrollDirection.DOWN:
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

    def key_press(self, widget, event ):
        if not self.books:
            return False
        flag = True
        if event.keyval == Gdk.keyval_from_name("Page_Up"):
            self.datasource.go_previous()
        elif event.keyval in (
                Gdk.keyval_from_name("Page_Down"),
                Gdk.keyval_from_name("Space")):
            self.datasource.go_next()
        elif event.keyval == Gdk.keyval_from_name("Up"):
            self.datasource.go_previous()
        elif event.keyval == Gdk.keyval_from_name("Down"):
            self.datasource.go_next()
        else:
            flag = False
        self.redraw_later()
        return flag

    def which_book(self, x, y):
        selected=0
        for region_x, region_y, width, height in self.regions:
            if (region_x <= int(x) < region_x + width and
                    region_y <= int(y) < region_y + height):
                break
            selected=selected+1
        if self.datasource.current_page>0:
            for page in self.datasource.pages[:self.datasource.current_page]:
                selected = selected + len(page)
        book = selected
        if book>=len(self.books):
            book = -1
        return book

    def get_book( self, idx ):
        return self.books[ idx ]
