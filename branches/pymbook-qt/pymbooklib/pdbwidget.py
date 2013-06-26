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


class PDBWidget(QWidget):
    def __init__(self, parent=None):
        super(PDBWidget, self).__init__()
        self.pdb = None

    def setFont(self, font):
        super(PDBWidget, self).setFont(font)
        if self.pdb:
            self.do_calc()

    def set_pdb(self, pdb):
        self.pdb = pdb
        self.do_calc()

    def do_calc(self):
        pass


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
