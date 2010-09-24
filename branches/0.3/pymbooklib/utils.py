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

"""Utilities"""
from pdb import PDBFile

def find_pdbs( path ):
    """Find all pdb/updb files according the specified path(absolute path).
    And return the filename lists which contain full path.
    """
    import glob
    import os
    pdbfiles = glob.glob( os.path.join( path, "*.pdb" ) ) + glob.glob( os.path.join( path, "*.updb" ) )
    books = [ ( PDBFile( pdb_filename ).parse().book_name, pdb_filename ) for pdb_filename in pdbfiles ]
    return sorted( books )

if __name__ == "__main__":
    print find_pdbs( "" )

