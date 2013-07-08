#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import unittest
from PySide.QtGui import QApplication
from PySide.QtTest import QTest
from PySide.QtCore import Qt
from pymbooklib.pdbcanvas import PDBCanvas
from pymbooklib.pdb import PDBFile


class PDBCanvasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    def tell_func(chapter, current_page):
        print(chapter, current_page)

    def setUp(self):
        #self.app = QApplication(sys.argv)
        self.widget = PDBCanvas()
        self.pdbfile = PDBFile(os.path.realpath("1287.pdb")).parse()
        self.widget.set_pdb(self.pdbfile)
        self.widget.tell.connect(self.tell_func)

    def test_first(self):
        self.assertEqual(self.widget.page, 0)

    def test_pagedown(self):
        QTest.keyClick(self.widget, Qt.Key_J)
        print(self.widget.page)
        self.assertEqual(self.widget.page, 1)

    def test_pageup(self):
        QTest.keyClick(self.widget, Qt.Key_J)
        QTest.keyClick(self.widget, Qt.Key_K)
        print(self.widget.page)
        self.assertEqual(self.widget.page, 0)

if __name__ == "__main__":
    unittest.main()
