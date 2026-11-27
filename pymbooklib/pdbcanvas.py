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

"""PDBCanvas"""
import logging

from gi.repository import Gdk, GObject

from .pdbwidget import PDBWidget
from .pageddatasource import PagedDataSource
from .utils import convert_pdb_to_pages, find_page_for_offset

class PDBCanvas(PDBWidget):
    __gsignals__ = dict(tell_callback=(GObject.SignalFlags.RUN_FIRST,
                                      GObject.TYPE_NONE,
                                      (GObject.TYPE_INT, GObject.TYPE_INT)))

    def __init__(self):
        super(PDBCanvas, self).__init__()
        self.old_rect = None
        self.datasource = None
        self.source = []
        self.pdb = None
        self.chapter = 0
        self.page = 0

        self.connect("draw", self.expose)
        self.connect("scroll-event", self.scroll_event)
        self.connect("key-press-event", self.key_press)
        self.connect("size-allocate", self.configure)

    def set_pdb(self, pdb):
        self.datasource = None
        self.source = []
        self.chapter = 0
        self.page = 0
        super(PDBCanvas, self).set_pdb(pdb)

    def set_chapter(self, chapter):
        self.chapter=chapter

        if not self.pdb:
            return

        if not self.datasource:
            self.do_calc()

        page = self._search_chapter(chapter)
        if not page:
            page = 0
        logging.debug( "chapter %d is in page %d" % (
                    self.chapter,
                    page ) )
        self.set_page( page )

    def set_page(self, page):
        self.page=page
        if self.datasource:
            self.datasource.current_page=page
            self.redraw_canvas()

    def do_calc(self):
        current_position = None
        if self.datasource and self.source:
            current_page = self.datasource.current_page
            if 0 <= current_page < len(self.source):
                page = self.source[current_page]
                current_position = page[0], page[3]

        # get canvas size
        rect=self.get_allocation()
        cell_width = self.font_size + self.font_size // 4
        cell_height = self.font_size + self.font_size // 3
        if rect.width <= cell_width * 2 or rect.height <= cell_height:
            return

        self.x_pos_list = range(
            rect.width - cell_width * 2, rect.x + cell_width, -cell_width)
        self.y_pos_list = range(
            cell_height, rect.height - cell_height, cell_height)
        columns_in_page = max(1, len(self.x_pos_list))
        glyphs_in_column = max(1, len(self.y_pos_list))
        self.source = convert_pdb_to_pages(
            self.pdb, columns_in_page, glyphs_in_column)
        self.datasource = PagedDataSource(self.source)
        target_page = None
        if current_position:
            chapter, text_offset = current_position
            target_page = find_page_for_offset(
                self.source, chapter, text_offset)
            self.chapter = chapter

        if target_page is None:
            target_page = self._search_chapter(self.chapter)
            if self.page:
                target_page = min(self.page, len(self.source) - 1)
        if target_page is None:
            target_page = 0
        self.datasource.current_page = target_page
        self.page = target_page
        self.old_rect=rect
        self.chapter_seg = rect.width // self.pdb.chapters

    def configure(self, widget, event):
        if self.pdb:
            self.do_calc()

    def expose(self, widget, cx):
        if not self.pdb:
            return False

        rect = self.get_allocation()

        # TODO: Is here a better place?
        self._tell()

        logging.debug("pdbcanvas.expose: current_page=%d" % self.datasource.current_page )
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
        cx.select_font_face(self.font_name)
        cx.set_font_size(self.font_size)
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
                cx.show_text(column[pos])
                pos = pos+1
            col = col+1
        
        cx.restore()

        return False

    def _tell(self):
        chapter = self.source[self.datasource.current_page][0]
        self.chapter = chapter
        self.emit("tell_callback", chapter, self.datasource.current_page)

    def _count_chapter_pages(self, chapter):
        if not self.source:
            return -1
        pages = [page for page in self.source if page[0] == chapter]
        return len(pages)

    def _search_chapter(self, chapter):
        """
        According the specified page number to search chapter.
        Return the chapter number if found, else return None.
        """
        found = None
        page_count = 0
        for chap, _, _, _ in self.source:
            if chap == chapter:
                found = page_count
                break
            page_count = page_count + 1
        return found

    def scroll_event(self, widget, event):
        if not self.pdb:
            return False

        if event.direction == Gdk.ScrollDirection.UP:
            self.datasource.go_previous()
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.datasource.go_next()
        self.page = self.datasource.current_page
        self.redraw_later()
        return True

    def key_press(self, widget, event ):
        flag = False
        if not self.pdb:
            return flag
        flag = True
        prev_list = [
            Gdk.keyval_from_name("Page_Up"),
            Gdk.keyval_from_name("Up"),
            Gdk.keyval_from_name("k"),
            Gdk.keyval_from_name("K"),
        ]
        next_list = [
            Gdk.keyval_from_name("Page_Down"),
            Gdk.keyval_from_name("Space"),
            Gdk.keyval_from_name("Down"),
            Gdk.keyval_from_name("j"),
            Gdk.keyval_from_name("J"),
        ]
        if event.keyval in prev_list:
            self.datasource.go_previous()
        elif event.keyval in next_list:
            self.datasource.go_next()
        else:
            flag = False
        self.page = self.datasource.current_page
        self.redraw_later()
        return flag

