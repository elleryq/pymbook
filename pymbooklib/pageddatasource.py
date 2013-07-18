#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2013 elleryq@gmail.com
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
        self.current_page = 0

    def go_previous(self):
        self.current_page = self.current_page - 1
        if self.current_page < 0:
            self.current_page = 0

    def go_next(self):
        self.current_page = self.current_page + 1
        if self.current_page >= len(self.pages):
            self.current_page = len(self.pages) - 1

    def get_current_page(self):
        return self.pages[self.current_page]

    def get_current_chapter(self):
        return self.get_current_page()[0] + 1

    def set_current_page_by_chapter(self, chapter):
        self.current_page = self._search_chapter(chapter - 1)

    def _search_chapter(self, chapter):
        """
        According the specified page number to search chapter.
        Return the chapter number if found, else return None.
        """
        found = 0
        page_count = 0
        for chap, n_in_page, page in self.pages:
            if chap == chapter:
                found = page_count
                break
            page_count = page_count + 1
        return found

    def count_pages(self):
        return len(self.pages)