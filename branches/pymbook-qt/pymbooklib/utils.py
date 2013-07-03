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

"""Utilities"""
from pdb import PDBFile


def find_pdbs(path):
    """Find all pdb/updb files according the specified path(absolute path).
    And return the filename lists which contain full path.
    """
    import glob
    import os
    pdbfiles = glob.glob(os.path.join(path, "*.pdb"))+glob.glob(
        os.path.join(path, "*.updb"))
    books = []
    for pdb_filename in pdbfiles:
        try:
            books.append((
                PDBFile(pdb_filename).parse().book_name,
                pdb_filename))
        except Exception, e:
            print pdb_filename, ':',  e
    return sorted(books)


def get_font_tuple(font_name):
    import pango
    fontdesc = pango.FontDescription(font_name)
    font_name = fontdesc.get_family()
    font_size = fontdesc.get_size()/pango.SCALE
    return (font_name, font_size)


def convert_columns_to_pages(columns, columns_in_page):
    pages = []
    page_len = len(columns)/columns_in_page+1
    for i in range(page_len):
        pages.append(columns[columns_in_page*i:columns_in_page*(i+1)])
    return pages


def convert_pdb_to_pages(pdb, columns_in_page, glyphs_in_column):
    def convert_text_to_pages(chapter_num, text, columns_in_page,
                              glyphs_in_column):
        pages = []
        column = []
        column_count = 0
        glyphs = 0
        page = []
        num_in_chapter = 0
        for c in text:
            if column_count >= columns_in_page:
                pages.append((chapter_num, num_in_chapter, page))
                num_in_chapter = num_in_chapter+1
                page = []
                column_count = 0
                glyphs = 0
            if c == u'\u000d':
                continue
            elif c == u'\u000a' or glyphs >= glyphs_in_column:
                column_count = column_count + 1
                page.append(column)
                column = []
                glyphs = 0
                if c == u'\u000a':
                    continue
            if c == u'\u3000':  # replace
                c = u' '
            column.append(c)
            glyphs = glyphs + 1
        if len(column) > 0:
            page.append(column)
        pages.append((chapter_num, num_in_chapter, page))
        return pages
    pages = []
    for chapter_num in range(pdb.chapters):
        content = pdb.chapter(chapter_num)
        pages.extend(convert_text_to_pages(
            chapter_num, content, columns_in_page, glyphs_in_column))
    return pages

if __name__ == "__main__":
    print find_pdbs("")
