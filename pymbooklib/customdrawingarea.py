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

"""Custom DrawingArea"""
import gobject
import gtk

class CustomDrawingArea(gtk.DrawingArea):
    """The base widget of BookshelfWidget, PDBContents and PDBCanvas."""
    font_name = '¤å¬uÅæ·L¦Ì¶Â'
    font_size = 16

    def __init__( self ):
        super(CustomDrawingArea, self).__init__()

        # Handle these events.
        self.add_events( gtk.gdk.BUTTON_PRESS_MASK | 
                        gtk.gdk.BUTTON_RELEASE_MASK | 
                        gtk.gdk.POINTER_MOTION_MASK |
                        gtk.gdk.KEY_PRESS_MASK |
                        gtk.gdk.SCROLL_MASK )

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
        import glib
        if self.timer:
            glib.source_remove( self.timer )
        self.timer = glib.timeout_add( 500, self.redraw_canvas )

