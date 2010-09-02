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
#  along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
import gtk

class PDBWidget(gtk.DrawingArea):
    font_name = '¤å¬uÅæ·L¦Ì¶Â'
    font_size = 16
    pdb = None

    def __init__(self):
        super(PDBWidget, self).__init__()
        self.set_flags( gtk.CAN_FOCUS )

    def set_font(self, font):
        t=font.split(' ')
        self.font_name = t[0]
        self.font_size = int(t[-1])

    def redraw_canvas(self):
        if self.window:
            alloc=self.get_allocation()
            rect=gtk.gdk.Rectangle(0, 0, alloc.width, alloc.height)
            self.window.invalidate_rect(rect, True)
            self.window.process_updates(True)

