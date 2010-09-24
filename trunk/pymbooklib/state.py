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

SHELF_TAB = 0
CONTENT_TAB = 1
CONTEXT_TAB = 2

class State( object ):
    def __init__(self, window):
        self.window = window

    def enter(self):
        return self

    def leave(self):
        return self

    def __repr__(self):
        return "State"

class ShelfState( State ):
    def __init__(self, window):
        super(ShelfState, self).__init__(window)

    def enter(self):
        self.window.btn_shelf.set_sensitive( True )
        self.window.btn_content.set_sensitive( False )
        self.window.btn_return.set_sensitive( False )
        self.window.notebook.set_current_page(SHELF_TAB)
        return super(ShelfState, self).enter()

    def __repr__(self):
        return "ShelfState"

class ShelfCanBackState( ShelfState ):
    def __init__(self, window):
        super(ShelfCanBackState, self).__init__(window)

    def enter(self):
        self.window.btn_return.set_sensitive( True )
        return super(ShelfCanBackState, self).enter()

    def __repr__(self):
        return "ShelfCanBackState"

class ContentState( State ):
    def __init__(self, window):
        super(ContentState, self).__init__(window)

    def enter(self):
        self.window.btn_shelf.set_sensitive( True )
        self.window.btn_content.set_sensitive( False )
        self.window.btn_return.set_sensitive( False )
        self.window.notebook.set_current_page(CONTENT_TAB)
        return super(ContentState, self).enter()

    def __repr__(self):
        return "ContentState"

class ContentCanBackState( ContentState ):
    def __init__(self, window):
        super(ContentCanBackState, self).__init__(window)

    def enter(self):
        self.window.btn_return.set_sensitive( True )
        return super(ContentCanBackState, self).enter()

    def __repr__(self):
        return "ContentCanBackState"

class ReadingState( State ):
    def __init__(self, window):
        super(ReadingState, self).__init__(window)

    def enter(self):
        self.window.btn_shelf.set_sensitive( True )
        self.window.btn_content.set_sensitive( True )
        self.window.btn_return.set_sensitive( False )
        self.window.notebook.set_current_page(CONTEXT_TAB)
        return super(ReadingState, self).enter()

    def __repr__(self):
        return "ReadingState"

