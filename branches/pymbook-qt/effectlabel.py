#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PySide.QtCore import Qt
from PySide.QtGui import QLabel
from PySide.QtGui import QPen
from PySide.QtGui import QPainter
from PySide.QtCore import QPoint


class EffectLabel(QLabel):
    PLAIN = 0
    SUNKEN = 1
    RAISED = 2

    def __init__(self, parent=None):
        self.effect_ = EffectLabel.PLAIN
        super(EffectLabel, self).__init__(parent)

    def drawTextEffect(self, painter, offset):
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.drawText(self.rect().translated(
            offset), self.alignment(), self.text())
        painter.setPen(QPen(Qt.GlobalColor.gray))
        painter.drawText(self.rect(), self.alignment(), self.text())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(self.font())
        if self.effect_ == EffectLabel.PLAIN:
            super(EffectLabel, self).paintEvent(event)
        elif self.effect_ == EffectLabel.SUNKEN:
            self.drawTextEffect(painter, QPoint(0, -1))
        elif self.effect_ == EffectLabel.RAISED:
            self.drawTextEffect(painter, QPoint(0, 1))

    def setEffect(self, effect):
        self.effect_ = effect


if __name__ == "__main__":
    from PySide.QtGui import QApplication
    from PySide.QtGui import QMainWindow

    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)
            self.label = EffectLabel(self)
            self.label.setText("Hello world!!")
            #self.label.setEffect(EffectLabel.RAISED)
            self.label.setEffect(EffectLabel.SUNKEN)
            self.move(QPoint(10, 10))

    app = QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    app.exec_()
