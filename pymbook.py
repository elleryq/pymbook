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
"""pymbook"""
import sys
import os

import pygtk
pygtk.require('2.0')
import gtk

from pymbooklib.mainwindow import MainWindow

def main( arg ):
    if len(arg)>0:
        window = MainWindow( arg[0] )
    else:
        window = MainWindow()
    gtk.main()

if __name__ == "__main__":
    main(sys.argv[1:])

