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
"""pymbook"""
import sys

from PySide.QtGui import QMainWindow
from PySide.QtGui import QPushButton
from PySide.QtGui import QApplication
from PySide.QtGui import QMessageBox

from ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.btnHello.clicked.connect(self.hello)
        self.actionE_xit.triggered.connect(self.close)

    def hello(self):
        QMessageBox.information(self, "Hello", "Hello")


def main(args):
    app = QApplication(args)
    frame = MainWindow()
    frame.show()
    app.exec_()


if __name__ == "__main__":
    main(sys.argv[1:])
