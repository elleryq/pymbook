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

"""DataSource"""

class DataSource(object):
    """
    Source, the bridge of data and widget.
    """
    def __init__(self, lines_in_page, glyphs_in_line, source ):
        """
        lines_in_page: also mean the column.
        glyphs_in_line: the words in a line.
        source: usually is a list or a string.
        """
        self.lines_in_page = lines_in_page
        self.glyphs_in_line = glyphs_in_line
        self.pages = []
        self.source = source
        self.process()

    def __getitem__(self, index):
        return self.pages[ index ]

    def process(self):
        page = []
        count = 0
        for item in self.extract_items_from_source():
            line = item[0:self.glyphs_in_line]
            page.append( line )
            count = count+1
            if count >= self.lines_in_page:
                self.pages.append( page )
                page = []
                count = 0
        if count>0:
            self.pages.append( page )

    def extract_items_from_source(self):
        pass

class ShelfDataSource(DataSource):
    """
    ShelfDataSource
    """
    def extract_items_from_source(self):
        return [book_name for book_name, pdb_filename in self.source]

class ContentDataSource(DataSource):
    """
    ContentDataSource
    """
    def extract_items_from_source(self):
        return self.source.contents

class ChapterDataSource(DataSource):
    """
    ChapterDataSource
    """
    def extract_items_from_source(self):
        pass

    def process(self):
        self.current=0
        self.pages=[]
        for num in range(self.source.chapters):
            content = self.source.chapter(num)
            columns=0
            words=0
            page=[]
            num_in_chapter=0
            for c in content:
                if c==u'\u000a' or words>=self.glyphs_in_line:
                    columns=columns+1
                    words=0
                if c!='\u000d' and c!='\u000a':
                    words=words+1
                page.append( c )
                if columns>=self.lines_in_page:
                    self.pages.append( (num, num_in_chapter, page) )
                    num_in_chapter=num_in_chapter+1
                    page=[]
                    columns=0
                    words=0
            self.pages.append( (num, num_in_chapter, page) )

if __name__ == '__main__':
    from utils import find_pdbs
    from pdb import PDBFile

    def dump_source( source, convert_func ):
        index = 1
        for page in source:
            print( "Page %d" % index )
            index = index + 1
            for line in page:
                print( convert_func(line) )

    print("ShelfDataSource:")
    source = ShelfDataSource(1, 25, find_pdbs('..'))
    dump_source( source, lambda l: l.encode('utf-8') )

    pdb = PDBFile("../65e.pdb").parse() 
    print("ContentDataSource:")
    source = ContentDataSource(1, 25, pdb )
    dump_source( source, lambda l: l.encode('utf-8') )

    source = ChapterDataSource(80, 25, pdb )
    dump_source( source, lambda x: x )
