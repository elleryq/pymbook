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
"""Config"""

import os

ENTRY_SHELF_PATH = "bookshelf_path"
ENTRY_WIDTH = "width"
ENTRY_HEIGHT = "height"
ENTRY_FONT_NAME = "font_name"
ENTRY_FONT_SIZE = "font_size"
ENTRY_CURRENT_PDB = "current_pdb"
ENTRY_CURRENT_CHAPTER = "current_chapter"
ENTRY_CURRENT_PAGE = "current_page"

DEFAULT_FONT_NAME = "文泉驛微米黑"
DEFAULT_FONT_SIZE = 16
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
DEFAULT_SHELF_PATH = "~/download/"
DEFAULT_CONFIG_CONTENT = """
[mbook]
%s = %s
%s = %d
%s = %d
%s = %s
%s = %d
""" % ( ENTRY_SHELF_PATH, DEFAULT_SHELF_PATH, 
        ENTRY_WIDTH, DEFAULT_WIDTH, 
        ENTRY_HEIGHT, DEFAULT_HEIGHT,
        ENTRY_FONT_NAME, DEFAULT_FONT_NAME,
        ENTRY_FONT_SIZE, DEFAULT_FONT_SIZE )

SECTION = 'mbook'

CONFIG_FILENAME = "~/.config/pymbook.conf"

class Config(object):
    def __init__(self, filename=CONFIG_FILENAME):
        self.filename = filename
        self.config = None

    def load(self):
        import ConfigParser
        import io
        self.config = ConfigParser.RawConfigParser()
        if os.path.exists( os.path.expanduser( self.filename ) ):
            self.config.readfp( open( os.path.expanduser( CONFIG_FILENAME ) ) )
        else:
            self.config.readfp( io.BytesIO(DEFAULT_CONFIG_CONTENT) )

    def save(self):
        import ConfigParser
        self.config.write( open(os.path.expanduser( CONFIG_FILENAME ), "wt" ) )

    def __getitem__(self, key):
        if not self.config.has_option( SECTION, key ):
            return None
        if key in ( ENTRY_WIDTH, ENTRY_HEIGHT, ENTRY_FONT_SIZE,
                ENTRY_CURRENT_CHAPTER, ENTRY_CURRENT_PAGE ):
            return self.config.getint( SECTION, key )
        else:
            return self.config.get( SECTION, key )

    def __setitem__(self, key, data):
        self.config.set( SECTION, key, data )
