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

"""Custom DrawingArea"""
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib, Gtk

from .utils import get_font_tuple


class CustomDrawingArea(Gtk.DrawingArea):
    """The base widget of BookshelfWidget, PDBContents and PDBCanvas."""
    font_name = '文泉驛微米黑'
    font_size = 16

    def __init__( self ):
        super(CustomDrawingArea, self).__init__()
        self.timer = None

        self.set_can_focus(True)
        self.set_sensitive(True)

        # Handle these events.
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.KEY_PRESS_MASK |
            Gdk.EventMask.SCROLL_MASK
        )

    def set_font(self, font):
        self.font_name, self.font_size = get_font_tuple( font )

    def redraw_canvas(self):
        self.queue_draw()

    def _draw_indicator(self, cx, x, y, seg):
        """
        Draw indicator, it just like scroll bar, but you can not drag it.
        """
        cx.save()
        cx.set_source_rgb( 1.0, 0, 0 )
        cx.move_to( x, y )
        cx.line_to( x+seg, y )
        cx.stroke()
        cx.restore()

    def _draw_line(self, cx, pos1, pos2):
        """
        Draw line.
        pos1 and pos2 are tutple contain x and y.
        """
        x1, y1 = pos1
        x2, y2 = pos2
        cx.save()
        cx.move_to( x1, y1 )
        cx.line_to( x2, y2 )
        cx.stroke()
        cx.restore()

    def redraw_later(self):
        if self.timer:
            GLib.source_remove(self.timer)
        self.timer = GLib.timeout_add(200, self._redraw_later)

    def _redraw_later(self):
        self.timer = None
        self.queue_draw()
        return GLib.SOURCE_REMOVE

