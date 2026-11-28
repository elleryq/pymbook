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

"""Utilities"""
import logging
import os

from .pdb import PDBFile


def find_pdbs(path, *, strict=False):
    """Find all pdb/updb files according the specified path(absolute path).
    And return the filename lists which contain full path.
    """
    path = os.path.expanduser(path)
    try:
        with os.scandir(path or ".") as entries:
            pdbfiles = [
                os.path.join(path, entry.name) for entry in entries
                if not entry.name.startswith(".")
                and entry.name.endswith((".pdb", ".updb"))
            ]
    except OSError as error:
        if strict:
            raise
        logging.warning("Cannot read bookshelf folder %s: %s", path, error)
        return []
    books = []
    for pdb_filename in pdbfiles:
        try:
            books.append((
                PDBFile(pdb_filename).parse().book_name,
                pdb_filename))
        except Exception as e:
            logging.warning("Skipping unreadable book %s: %s",
                            pdb_filename, e)
    return sorted(books)


def get_font_tuple(font_name):
    from gi.repository import Pango

    font_description = Pango.FontDescription(font_name)
    return (font_description.get_family(),
            int(font_description.get_size() / Pango.SCALE))


def convert_columns_to_pages(columns, columns_in_page):
    if columns_in_page < 1:
        raise ValueError("columns_in_page must be positive")
    if not columns:
        return [[]]
    return [
        columns[index:index + columns_in_page]
        for index in range(0, len(columns), columns_in_page)
    ]


def convert_pdb_to_pages(pdb, columns_in_page, glyphs_in_column):
    def convert_text_to_pages(chapter_num, text, columns_in_page,
            glyphs_in_column):
        pages = []
        column = []
        column_count = 0
        glyphs = 0
        page = []
        num_in_chapter=0
        page_start_offset = 0
        for text_offset, c in enumerate(text):
            if column_count>=columns_in_page:
                pages.append((
                    chapter_num, num_in_chapter, page, page_start_offset))
                num_in_chapter=num_in_chapter+1
                page=[]
                column_count=0
                glyphs=0
                page_start_offset = text_offset
            if c=='\u000d':
                continue
            elif c=='\u000a' or glyphs>=glyphs_in_column:
                column_count = column_count + 1
                page.append( column )
                column = []
                glyphs=0
                if c=='\u000a':
                    continue
            if c=='\u3000': # replace
                c = ' '
            column.append( c )
            glyphs = glyphs + 1
        if len(column)>0:
            page.append( column )
        pages.append((
            chapter_num, num_in_chapter, page, page_start_offset))
        return pages
    pages = []
    for chapter_num in range(pdb.chapters):
        content = pdb.chapter(chapter_num)
        pages.extend(
                convert_text_to_pages(
                    chapter_num, content,
                    columns_in_page, glyphs_in_column))
    return pages


def find_page_for_offset(pages, chapter, text_offset):
    chapter_pages = [
        (index, page_offset)
        for index, (page_chapter, _, _, page_offset) in enumerate(pages)
        if page_chapter == chapter
    ]
    eligible_pages = [
        index for index, page_offset in chapter_pages
        if page_offset <= text_offset
    ]
    if eligible_pages:
        return eligible_pages[-1]
    return chapter_pages[0][0] if chapter_pages else None

if __name__ == "__main__":
    print(find_pdbs(""))
