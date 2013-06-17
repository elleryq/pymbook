#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2010-2013 elleryq@gmail.com
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
"""PDBFile"""
import sys
import os
import locale

PDB_HEADER_SIZE = 78
PDB_HEADER_RECORD = 76
PDB_HEADER_BOOK_TYPE = 64
PDB_HEADER_BOOK_TYPE_LEN = 4
PDB_CHAPTER_OFFSET = 78

class PDBException(BaseException):
    """
    The exception throwed by PDBFile.
    """
    def __init__(self, value ):
        self.value = value
    def __str__(self):
        return repr(self.value)

class BaseOperation(object):
    """
    Use template pattern to extract base operation.  The real implementation is in UnicodeOperation and DblByteOperation.
    """
    def __init__( self ):
        self.empty_str = None
        self.escape_char = None

    def parseBasicInformation( self, pdb, raw_text ):
        raw_text = raw_text[8:]
        basic_inf=raw_text.split( self.escape_char )
        pdb.book_name = self.convert2unicode(
                self.empty_str.join(self.processString(basic_inf[0])) )
        pdb.chapters = self.extractChapters(basic_inf[3])
        pdb.contents = self.extractContents( basic_inf[4:] )
    
    def processString(self, file):
        pass

    def convert2unicode( self, str ):
        pass

    def extractChapters( self, str ):
        return int( self.empty_str.join(str), 10 )

    def extractContents( self, raw_list ):
        pass

    def skipBytesCount( self ):
        return 0

class UnicodeOperation(BaseOperation):
    """
    Handle updb(unicode pdb) file.
    """
    
    def __init__( self ):
        super(UnicodeOperation, self).__init__()
        self.empty_str = u""
        self.escape_char = "\x1b\x00"
    
    def processString(self, raw_str):
        converted_text = []
        count = len(raw_str)/2
        for i in range(count):
            ch = [ ord(c) for c in raw_str[i*2:i*2+2] ]
            if not ch or len(ch)<2 or (ch[0]==0 and ch[1]==0):
                break
            converted_text.append( unichr( (ch[1]<<8) + ch[0] ))
        return converted_text

    def convert2unicode( self, str ):
        return str

    def extractContents( self, raw_list ):
        # workaround: len(raw_list) is 1, but we expect more.
        # So we split it ourself.
        contents = self.processString( raw_list[0] )
        return self.empty_str.join(contents).split( u"\r\n" )

class DblByteOperation( BaseOperation ):
    """
    Handle double byte pdb file.  For now, the pdb files provided by haodoo are encoded with cp950.
    """
    
    def __init__( self ):
        super(DblByteOperation, self).__init__()
        self.empty_str = ""
        self.escape_char = "\x1b"
    
    def processString(self, raw_str):
        converted_text = []
        for ch in raw_str:
            if ord(ch)==0:
                break
            converted_text.append( ch )
        return converted_text

    def convert2unicode( self, s ):
        result=""
        try:
            result=unicode( s, "cp950", errors='ignore' )
        except BaseException, e:
            #print map( lambda c: "%x" % ord(c), str )
            raise e
        return result

    def extractContents( self, raw_list ):
        contents = []
        for s in raw_list:
            contents.append( self.convert2unicode(
                        self.empty_str.join(self.processString(s) ) ) )
        return contents

class PDBFile:
    """
    The major class to read PDB file.
    """
    def __init__( self, pdb_filename ):
        self.records = 0
        self.pdb_filename = ""
        self.is_unicode = False
        self.chapter_start_offsets = []
        self.chapter_end_offsets = []
        self.book_name = ""
        self.contents = []
        self.chapters = 0
        self.pdb_filename = pdb_filename

    def __parseHeader( self, f ):
        # parse file header
        header = f.read( PDB_HEADER_SIZE )
        book_type = header[PDB_HEADER_BOOK_TYPE:PDB_HEADER_BOOK_TYPE+PDB_HEADER_BOOK_TYPE_LEN]
        if book_type == "MTIU":
            self.is_unicode = True
            self.operation = UnicodeOperation()
            self.empty_str = u""
        elif book_type == "MTIT":
            self.is_unicode = False
            self.operation = DblByteOperation()
            self.empty_str = ""
        else:
            raise PDBException("Not a PDB or uPDB")
        self.records = (ord(header[PDB_HEADER_RECORD])<<8) + ord(header[PDB_HEADER_RECORD+1])
        
    def __parseChapterOffsets(self, f):
        # get the offset of every chapters.
        f.seek( PDB_CHAPTER_OFFSET, os.SEEK_SET )
        for i in range( self.records ):
            offset_record = f.read( 8 )
            if len(offset_record)!=8:
                raise PDBException( "Offset record size is not enough(8). %d" % i )
            offset = (ord(offset_record[0])<<24) + (ord(offset_record[1])<<16) + (ord(offset_record[2])<<8) + ord(offset_record[3])
            self.chapter_start_offsets.append( offset )
        self.chapter_end_offsets = self.chapter_start_offsets[1:]
        f.seek( 0, os.SEEK_END )
        self.chapter_end_offsets.append( f.tell()+1 )

    def __parseBasicInformation(self, f):
        f.seek( self.chapter_start_offsets[0], os.SEEK_SET )
        raw_text = f.read( self.chapter_end_offsets[0] - self.chapter_start_offsets[0] ) 
        self.operation.parseBasicInformation( self, raw_text )

    def parse( self ):
        """Must call parse() first to get PDB."""
        f = None
        try:
            f = open( self.pdb_filename, "rb" )
            self.__parseHeader(f)
            self.__parseChapterOffsets(f)
            self.__parseBasicInformation(f)
        except BaseException, e:
            raise e
        finally:
            if f:
                f.close()
        return self

    def chapter(self, num ):
        """Read specified chapters."""
        result = ""
        chap = num + 1
        if chap>self.chapters:
            return ""
        f = None
        try:
            f = open( self.pdb_filename, "rb" )
            f.seek( self.chapter_start_offsets[chap], os.SEEK_SET )
            count=self.chapter_end_offsets[chap]-self.chapter_start_offsets[chap] 
            raw_str = f.read( count )
            text = self.empty_str.join( 
                    self.operation.processString( raw_str ) )
            result = self.operation.convert2unicode( text )
        except BaseException, e:
            print e
        finally:
            if f:
                f.close()
        return result
    
    def __str__(self):
        book_type="PDB"
        if self.is_unicode:
            book_type="uPDB"
        return """
Filename: %s (%s)
Records: %d
Chapters: %d
""" % (self.pdb_filename, book_type, self.records, self.chapters )

if __name__ == "__main__":
    loc = locale.getdefaultlocale()
    if loc[1]:
        encoding = loc[1]
    
    argc = len( sys.argv )
    chapter = 0
    if argc<2:
        print( """Need at least 1 argument.
Usage: %s pdb_filename [chapter]""" % sys.argv[0] )
        sys.exit(-1)
    elif argc==3:
        chapter=int(sys.argv[2])
    
    try:
        pdb = PDBFile( sys.argv[1] ).parse()
        print( "Book name: %s " % pdb.book_name.encode( encoding ) )
        print( "Total %d chapters." % pdb.chapters )
        for chapter_title in pdb.contents:
            print( chapter_title.encode(encoding) )
        print( pdb.chapter( chapter ).encode(encoding) )
    except BaseException, e:
        print e

