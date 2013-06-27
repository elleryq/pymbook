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

"""PDBWidget"""
from PySide.QtGui import QWidget
from PySide.QtGui import QPen
from PySide.QtCore import QTimer
from PySide.QtCore import Qt


class PDBWidget(QWidget):
    def __init__(self, parent=None):
        super(PDBWidget, self).__init__(parent)
        self.pdb = None
        self.timer = None

    def setFont(self, font):
        super(PDBWidget, self).setFont(font)
        if self.pdb:
            self.do_calc()

    def set_pdb(self, pdb):
        self.pdb = pdb
        self.do_calc()

    def do_calc(self):
        pass

    def redraw_canvas(self):
        print("redraw_canvas")
        self.repaint(self.rect())

    def _draw_indicator(self, painter, x, y, seg):
        """
        Draw indicator, it just like scroll bar, but you can not drag it.
        """
        painter.save()
        pen = QPen()
        pen.setColor(Qt.GlobalColor.red)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(x, y, x+seg, y)
        painter.restore()

    def _draw_line(self, painter, pos1, pos2):
        """
        Draw line.
        pos1 and pos2 are tutple contain x and y.
        """
        x1, y1 = pos1
        x2, y2 = pos2
        painter.save()
        painter.drawLine(x1, y1, x2, y2)
        painter.restore()

    def redraw_later(self):
        if self.timer:
            self.timer.stop()
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.redraw_canvas)
        self.timer.start()


if __name__ == "__main__":
    import sys
    from PySide.QtGui import QApplication
    from PySide.QtGui import QMainWindow
    from PySide.QtCore import QPoint

    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)
            self.widget = PDBWidget(self)
            self.move(QPoint(10, 10))

    app = QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    app.exec_()
