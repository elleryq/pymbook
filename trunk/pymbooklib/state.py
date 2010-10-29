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
"""State"""

import config
import logging

SHELF_TAB = 0
CONTENT_TAB = 1
CONTEXT_TAB = 2

class StateErrorException(BaseException):
    """
    The exception throwed by State and inherited classes.
    """
    def __init__(self, state_name ):
        self.state_name = state_name
    def __str__(self):
        return "Insufficent condition to enter '%s'." % self.state_name

class State( object ):
    config = None
    window = None

    def enter(self):
        return self

    def leave(self):
        return self

    def __repr__(self):
        return "State"

    def load(self):
        pass

    def save(self):
        pass

    @staticmethod
    def check_filename(state_name):
        filename = State.config[config.ENTRY_CURRENT_PDB]
        if not filename:
            raise StateErrorException( state_name )

        if len(filename) and State.window.open_pdb( filename ):
            State.window.pdb_filename = filename
        else:
            raise StateErrorException( state_name )

class ShelfState( State ):
    def enter(self):
        self.window.btn_shelf.set_sensitive( True )
        self.window.btn_content.set_sensitive( False )
        self.window.btn_return.set_sensitive( False )
        self.window.notebook.set_current_page(SHELF_TAB)
        self.window.bookshelf.grab_focus()
        return super(ShelfState, self).enter()

    def save(self):
        super(ShelfState, self).save()
        self.config[config.ENTRY_STATE] = config.STATE_BOOKSHELF
        self.config[config.ENTRY_CURRENT_PDB] = ""
        self.config[config.ENTRY_CURRENT_CHAPTER] = -1
        self.config[config.ENTRY_CURRENT_PAGE] = -1
        self.config.save()

    def __repr__(self):
        return "ShelfState"

class ShelfCanBackState( ShelfState ):
    def enter(self):
        self.window.btn_return.set_sensitive( True )
        return super(ShelfCanBackState, self).enter()

    def __repr__(self):
        return "ShelfCanBackState"

class ContentState( State ):
    def enter(self):
        self.window.btn_shelf.set_sensitive( True )
        self.window.btn_content.set_sensitive( False )
        self.window.btn_return.set_sensitive( False )
        self.window.notebook.set_current_page(CONTENT_TAB)
        self.window.pdb_contents.grab_focus()
        return super(ContentState, self).enter()

    def load(self):
        super(ContentState, self).load()
        self.check_filename( repr(self) )

    def save(self):
        super(ContentState, self).save()
        logging.info( self.window.pdb_filename )
        self.config[config.ENTRY_STATE] = config.STATE_CONTENT
        self.config[config.ENTRY_CURRENT_PDB] = self.window.pdb_filename
        self.config[config.ENTRY_CURRENT_CHAPTER] = -1
        self.config[config.ENTRY_CURRENT_PAGE] = -1
        self.config.save()

    def __repr__(self):
        return "ContentState"

class ContentCanBackState( ContentState ):
    def enter(self):
        self.window.btn_return.set_sensitive( True )
        return super(ContentCanBackState, self).enter()

    def __repr__(self):
        return "ContentCanBackState"

class ReadingState( State ):
    def enter(self):
        self.window.btn_shelf.set_sensitive( True )
        self.window.btn_content.set_sensitive( True )
        self.window.btn_return.set_sensitive( False )
        self.window.notebook.set_current_page(CONTEXT_TAB)
        self.window.pdb_canvas.grab_focus()
        return super(ReadingState, self).enter()

    def load(self):
        super(ReadingState, self).load()
        self.check_filename( repr(self) )

        if not self.config[config.ENTRY_CURRENT_CHAPTER] or \
            not self.config[config.ENTRY_CURRENT_PAGE]:
            raise StateErrorException( repr(self) )

        chapter = self.config[config.ENTRY_CURRENT_CHAPTER]
        if chapter < 0:
            chapter = 0
        page = self.config[config.ENTRY_CURRENT_PAGE]
        if page < 0:
            page = 0
        logging.debug( "chapter=%d page=%d" % (chapter, page) )
        self.window.pdb_canvas.set_chapter( chapter )
        self.window.pdb_canvas.set_page( page )

    def save(self):
        super(ReadingState, self).save()
        self.config[config.ENTRY_STATE] = config.STATE_READING
        self.config[config.ENTRY_CURRENT_PDB] = self.window.pdb_filename
        self.config[config.ENTRY_CURRENT_CHAPTER] = self.window.chapter
        self.config[config.ENTRY_CURRENT_PAGE] = self.window.page
        self.config.save()

    def __repr__(self):
        return "ReadingState"

