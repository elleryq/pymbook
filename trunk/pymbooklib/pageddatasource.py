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

"""PagedDataSource"""

class PagedDataSource(object):
    def __init__(self, source):
        self.pages = source
        self.current_page=0

    def go_previous(self):
        self.current_page=self.current_page-1
        if self.current_page<0:
            self.current_page=0

    def go_next(self):
        self.current_page=self.current_page+1
        if self.current_page>=len(self.pages):
            self.current_page=len(self.pages)-1

    def get_current_page(self):
        return self.pages[self.current_page]

    def count_pages(self):
        return len(self.pages)
