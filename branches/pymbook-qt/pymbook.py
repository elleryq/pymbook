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
import os
import logging

from PySide.QtGui import QApplication
from PySide.QtGui import QMainWindow
from PySide.QtGui import QMessageBox
from PySide.QtGui import QTabWidget
from pymbooklib.pdb import PDBFile
from pymbooklib.pdb import PDBException
from pymbooklib.bookshelf import BookshelfWidget
from pymbooklib.pdbcanvas import PDBCanvas
from pymbooklib.pdbcontents import PDBContents

from pymbooklib.state import ContentState
from ui_mainwindow import Ui_MainWindow


class State(object):
    """Base state"""
    def __init__(self, window):
        super(State, self).__init__()

    def enter(self):
        pass

class BookshelfState(State):
    """The state for selecting books."""
    def __init__(self, window):
        super(BookshelfState, self).__init__(window)


class ContentState(State):
    """The state for select chapters (show content)."""
    pass


class ReadingState(State):
    """The state for reading."""
    pass


class StateMachine(object):
    """State machine"""
    def __init__(self, window):
        super(StateMachine, self).__init__()
        self.initializeStates(window)
        self.currentState.enter()

    def initializeStates(self, window):
        self.bookshelfState = BookshelfState(window)
        self.contentState = ContentState(window)
        self.readingState = ReadingState(window)
        self.currentState = self.bookshelfState


class TabWidget(QTabWidget):
    def __init__(self, parent=None):
        super(TabWidget, self).__init__(parent)
        self.setTabsClosable(False)
        self.tabBar().setVisible(False)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.tab = TabWidget()

        #self.ui.pdbcanvas = PDBCanvas()
        #self.pdbfile = PDBFile(os.path.realpath("D55d.pdb")).parse()
        #self.ui.pdbcanvas.set_pdb(self.pdbfile)
        #self.ui.tab.addTab(self.ui.pdbcanvas, "")

        self.initTabs(self.ui.tab)
        self.ui.verticalLayout.addWidget(self.ui.tab)

        self.ui.actionE_xit.triggered.connect(self.close)

        self.sm = StateMachine(self.ui)

    def initTabs(self, tabControl):
        # Add bookshelf tab
        #self.ui.bookshelf = BookshelfWidget(
        #   self.config[config.ENTRY_SHELF_PATH])
        self.ui.bookshelf = BookshelfWidget(None, ".")
        #self.ui.bookshelf.set_font(font)
        tabControl.addTab(self.ui.bookshelf, "Bookshelf")

        # Add contents tab
        self.ui.contents = PDBContents()
        tabControl.addTab(self.ui.contents, "Contents")

        # Add text tab
        self.ui.canvas = PDBCanvas()
        tabControl.addTab(self.ui.canvas, "Reading")

        self.ui.bookshelf.book_selected.connect(self.bookshelfBookSelected)
        self.ui.contents.chapter_selected.connect(self.contentsChapterSelected)
        #self.ui.canvas.connect(
        #    "tell_callback", self.pdb_canvas_tell_callback)

    def open_pdb(self, pdb_filename):
        #import urlparse
        try:
            self.pdb = PDBFile(pdb_filename).parse()
            self.ui.contents.set_pdb(self.pdb)
            self.ui.contents.redraw_canvas()
            self.ui.canvas.set_pdb(self.pdb)
            self.ui.canvas.redraw_canvas()
        except PDBException, ex:
            logging.error("Cannot open specified pdb: %s", repr(ex))
            QMessageBox.warning(self, "", "Cannot open specified pdb.")
            return False
        except BaseException, ex:
            logging.error("Other exception: %s" % repr(ex))
            return False
        #self.window.set_title("%s - %s" % (APP_NAME, self.pdb.book_name))
        #uri = urlparse.urljoin("file://", pdb_filename.encode('utf-8'))
        #self.recent.add_full(uri, {'mime_type': 'application/octet-stream',
        #                           'app_name': APP_NAME,
        #                           'app_exec': 'pymbook',
        #                           'group': 'pymbook',
        #                           'display_name': self.pdb.book_name.encode(
        #                               'utf-8')})
        return True

    def bookshelfBookSelected(self, book_item):
        book_name, pdb_filename = book_item
        logging.debug("(%s, %s) is selected" % (book_name, pdb_filename))
        if self.open_pdb(pdb_filename):
            self.pdb_filename = pdb_filename
            self.ui.contents.set_pdb(self.pdb)
            self.ui.contents.redraw_canvas()
            #self.state = ContentState().enter()
            self.ui.tab.setCurrentIndex(1)
            #self.state.save()

    def contentsChapterSelected(self, chapter):
        if chapter == -1:
            QMessageBox.warning(self, "", "No such chapter.")
            return
        logging.debug("chapter={0}".format(chapter))
        self.ui.canvas.redraw_canvas()
        self.ui.canvas.set_chapter(chapter)
        self.ui.tab.setCurrentIndex(2)
        #self.state = ReadingState().enter()
        #self.state.save()


    def hello(self):
        QMessageBox.information(self, "Hello", "Hello")


def main(args):
    app = QApplication(args)
    frame = MainWindow()
    frame.show()
    app.exec_()


if __name__ == "__main__":
    main(sys.argv[1:])
