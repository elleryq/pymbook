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

"""PDBCanvas"""
import gobject
import gtk
from pdbwidget import PDBWidget
from pageddatasource import PagedDataSource
from utils import convert_pdb_to_pages

class PDBCanvas(PDBWidget):
    __gsignals__ = dict(tell_callback=(gobject.SIGNAL_RUN_FIRST,
                                      gobject.TYPE_NONE,
                                      (gobject.TYPE_INT, gobject.TYPE_INT)))

    def __init__(self):
        super(PDBCanvas, self).__init__()
        self.old_rect=None
        self.datasource=None
        self.recalc=True
        self.pdb=None
        self.chapter=0
        self.page=0

        self.connect("expose_event", self.expose)
        self.connect("scroll-event", self.scroll_event )
        self.connect("key-press-event", self.key_press )

    def set_pdb(self, pdb):
        super(PDBCanvas, self).set_pdb( pdb )
        self.chapter=0

    def set_chapter(self, chapter):
        self.chapter=chapter
        if self.datasource:
            self.set_page( self._search_chapter(chapter) )
            return
        self.recalc=True

    def set_page(self, page):
        self.page=page
        self.recalc=True
        self.redraw_later()

    def _recalc(self):
        rect=self.get_allocation()
        cell_width=self.font_size+self.font_size/4
        cell_height=self.font_size+self.font_size/3

        self.x_pos_list=range(rect.width-cell_width*2, rect.x+cell_width, -cell_width)
        self.y_pos_list=range(cell_height, rect.height-cell_height, cell_height)
        columns_in_page=len( self.x_pos_list )
        glyphs_in_column=len(self.y_pos_list)
        self.source = convert_pdb_to_pages( self.pdb,
                columns_in_page, glyphs_in_column ) 
        self.datasource = PagedDataSource( self.source )
        self.datasource.current_page = self._search_chapter( self.chapter )
        if self.page:
            self.datasource.current_page=self.page
        self.old_rect=rect
        self.chapter_seg = rect.width/self.pdb.chapters
        self.recalc=False

    def expose(self, widget, event):
        if not self.pdb:
            return False

        cx=widget.window.cairo_create()

        # get canvas size
        rect=self.get_allocation()

        # The first time.
        if not self.old_rect:
            self.recalc=True
        # If windows size is changed.
        elif self.old_rect and self.old_rect!=rect:
            self.recalc=True

        if self.recalc:
            self._recalc()

        # TODO: Is here a better place?
        self._tell()

        # draw chapter indicator
        if self.pdb.chapters>1:
            x = rect.width-(self.datasource.get_current_page()[0]+1)*self.chapter_seg
            self._draw_indicator( cx, x, 0, self.chapter_seg )

        # draw page in chapter indicator
        if self.datasource.count_pages()>1:
            seg = rect.width/self._count_chapter_pages(self.datasource.get_current_page()[0])
            x = rect.width-(self.datasource.get_current_page()[1]+1)*seg
            self._draw_indicator( cx, x, rect.height-1, seg )

        # draw text
        cx.save()
        cx.set_source_rgb( 0, 0, 0 )
        cx.select_font_face( self.font_name )
        cx.set_font_size( self.font_size)
        page = self.datasource.get_current_page()[2]
        col = 0
        for x in self.x_pos_list:
            if col>=len(page):
                break
            column = page[col]
            pos = 0
            for y in self.y_pos_list:
                if pos>=len(column):
                    break
                cx.move_to( x, y )
                cx.show_text( column[pos] )
                pos = pos+1
            col = col+1
        
        cx.restore()

        return False

    def _tell(self):
        self.emit("tell_callback", self.chapter, self.datasource.current_page)

    def _count_chapter_pages(self, chapter):
        if not self.source:
            return -1
        pages=[ ch for ch, n_in_p, p in self.source if ch==chapter ]
        return len(pages)

    def _search_chapter(self, chapter):
        found = 0
        for chap, n_in_page, page in self.source:
            if chap==chapter:
                break
            found = found + 1
        return found

    def scroll_event(self, widget, event):
        if not self.pdb:
            return False

        if event.direction==gtk.gdk.SCROLL_UP:
            self.datasource.go_previous()
        elif event.direction==gtk.gdk.SCROLL_DOWN:
            self.datasource.go_next()
        self.redraw_later()
        return True

    def key_press(self, widget, event ):
        flag = False
        if not self.pdb:
            return flag
        flag = True
        if event.keyval==gtk.gdk.keyval_from_name("Page_Up"):
            self.datasource.go_previous()
        elif event.keyval==gtk.gdk.keyval_from_name("Page_Down") or \
            event.keyval==gtk.gdk.keyval_from_name("Space"):
            self.datasource.go_next()
        elif event.keyval==gtk.gdk.keyval_from_name("Up"):
            self.datasource.go_previous()
        elif event.keyval==gtk.gdk.keyval_from_name("Down"):
            self.datasource.go_next()
        else:
            flag = False
        self.redraw_later()
        return flag

