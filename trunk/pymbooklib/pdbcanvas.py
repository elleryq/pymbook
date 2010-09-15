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

class TextPager:
    def __init__(self, pdb, columns_in_page, glyphs_in_column):
        self.current = 0
        self.pages = []
        for chapter_num in range(pdb.chapters):
            content = pdb.chapter(chapter_num)
            self.pages.extend( 
                    self.__split_to_pages( 
                        chapter_num, content, 
                        columns_in_page, glyphs_in_column ) )

    def __split_to_pages(self, chapter_num, s, columns_in_page, glyphs_in_column):
        pages = []
        column = []
        column_count = 0
        glyphs = 0
        page = []
        num_in_chapter=0
        for c in s:
            if column_count>=columns_in_page:
                pages.append( (chapter_num, num_in_chapter, page) )
                num_in_chapter=num_in_chapter+1
                page=[]
                column_count=0
                glyphs=0
            if c==u'\u000d':
                continue
            elif c==u'\u000a' or glyphs>=glyphs_in_column:
                column_count = column_count + 1
                page.append( column )
                column = []
                glyphs=0
                if c==u'\u000a':
                    continue
            if c==u'\u3000': # replace
                c = u' '
            column.append( c )
            glyphs = glyphs + 1
        if len(column)>0:
            page.append( column )
        pages.append( (chapter_num, num_in_chapter, page) )
        return pages

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

class PDBCanvas(PDBWidget):
    def __init__(self):
        super(PDBCanvas, self).__init__()
        self.old_rect=None
        self.pager=None
        self.recalc=True
        self.pdb=None
        self.chapter=0

        self.add_events(gtk.gdk.SCROLL_MASK |
                        gtk.gdk.KEY_PRESS_MASK )

        self.connect("expose_event", self.expose)
        self.connect("scroll-event", self.scroll_event )
        self.connect("key-release-event", self.key_release )

    def set_pdb(self, pdb):
        super(PDBCanvas, self).set_pdb( pdb )
        self.page=0
        self.chapter=0

    def set_chapter(self, chapter):
        self.chapter=chapter
        self.recalc=True

    def __draw_chapter_indicator(self, cx, x, y, seg):
        """draw chapter indicator"""
        cx.save()
        cx.set_source_rgb( 1.0, 0, 0 )
        cx.move_to( x, y )
        cx.line_to( x+seg, y )
        cx.stroke()
        cx.restore()

    def __draw_page_indicator(self, cx, x, y, seg):
        """draw page/chapter indicator"""
        cx.save()
        cx.set_source_rgb( 1.0, 0, 0 )
        cx.move_to( x, y )
        cx.line_to( x+seg, y )
        cx.stroke()
        cx.restore()

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
            self.y_pos_list=range(cell_height, rect.height-cell_height, cell_height)
            columns_in_page=len( self.x_pos_list )
            glyphs_in_column=len(self.y_pos_list)
            self.pager=TextPager(self.pdb, columns_in_page, glyphs_in_column)
            self.pager.go_chapter(self.chapter)
            self.old_rect=rect
            self.chapter_seg = rect.width/self.pdb.chapters
            self.recalc=False

        x = rect.width-(self.pager.get_current_chapter()+1)*self.chapter_seg
        self.__draw_chapter_indicator( cx, x, 0, self.chapter_seg )

        seg = rect.width/self.pager.count_chapter_pages(self.pager.get_current_chapter())
        x = rect.width-(self.pager.get_current_page_in_chapter()+1)*seg
        self.__draw_page_indicator( cx, x, rect.height-1, seg )

        # draw text
        cx.save()
        cx.set_source_rgb( 0, 0, 0 )
        cx.select_font_face( self.font_name )
        cx.set_font_size( self.font_size)
        page = self.pager.get_current_page()
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

    def scroll_event(self, widget, event):
        if not self.pdb:
            return False

        if event.direction==gtk.gdk.SCROLL_UP:
            self.pager.go_previous()
        elif event.direction==gtk.gdk.SCROLL_DOWN:
            self.pager.go_next()
        self.chapter=self.pager.get_current_chapter()
        self.redraw_later()
        return True

    def key_release(self, widget, event ):
        if not self.pdb:
            return False
        if event.keyval==gtk.gdk.keyval_from_name("Page_Up"):
            self.pager.go_previous()
        elif event.keyval==gtk.gdk.keyval_from_name("Page_Down"):
            self.pager.go_next()
        elif event.keyval==gtk.gdk.keyval_from_name("Up"):
            self.pager.go_previous()
        elif event.keyval==gtk.gdk.keyval_from_name("Down"):
            self.pager.go_next()
        self.redraw_later()
        return False

