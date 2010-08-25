#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Reference: http://www.haodoo.net/?M=hd&P=mPDB22#P

import sys
import os
import locale

PDB_HEADER_SIZE = 78
PDB_HEADER_RECORD = 76
PDB_HEADER_BOOK_TYPE = 64
PDB_HEADER_BOOK_TYPE_LEN = 4
PDB_CHAPTER_OFFSET = 78

class PDBException(BaseException):
    """The exception throwed by PDBFile."""
    def __init__(self, value ):
        self.value = value
    def __str__(self):
        return repr(self.value)

class BaseOperation:
    """Use template pattern to extract base operation.  The real implementation is in UnicodeOperation and DblByteOperation."""
    def __init__( self ):
        pass

    def parseBasicInformation( self, pdb, content ):
        content[0:8]=[]
        basic_inf=self.empty_str.join(content).split( chr(27) )
        pdb.book_name = self.convert2unicode(basic_inf[0])
        pdb.chapters = self.extractChapters(basic_inf[3])
        pdb.chapter_titles = [ self.convert2unicode(s) for s in basic_inf[4:4+pdb.chapters] ]
    
    def processString(self, file):
        pass

    def convert2unicode( self, str ):
        pass

    def extractChapters( self, str ):
        pass

class UnicodeOperation( BaseOperation ):
    """Handle mUpdb file."""
    empty_str = u""
    
    def __init__( self ):
        pass
    
    def processString(self, raw_str):
        content = []
        i = 0
        while True:
            ch = [ ord(c) for c in raw_str[i:i+2] ]
            if not ch or (ch[0]==0 and ch[1]==0):
                break
            content.append( unichr( (ch[1]<<8) + ch[0] ))
            i+=2
        return content

    def convert2unicode( self, str ):
        return str

    def extractChapters( self, str ):        
        tmp_list = []
        i = ord( str )
        tmp_list.append( chr(i & 0x00ff) )
        tmp_list.append( chr( i>>8 ) )
        return int( self.empty_str.join(tmp_list), 10 )

class DblByteOperation( BaseOperation ):
    """Handle double byte pdb file."""
    empty_str = ""
    
    def __init__( self ):
        pass
    
    def processString(self, raw_str):
        content = []
        for ch in raw_str:
            if ord(ch)==0:
                break
            content.append( ch )
        return content

    def convert2unicode( self, str ):
        return unicode( str, "cp950" )

    def extractChapters( self, str ):
        return int( self.empty_str.join(str), 10 )
 
class PDBFile:
    """The major class to read PDB file."""
    records = 0
    pdb_filename = ""
    is_unicode = False
    chapter_start_offsets = []
    chapter_end_offsets = []
    book_name = ""
    chapter_titles = []
    chapters = 0

    def __init__( self, pdb_filename ):
        self.pdb_filename = pdb_filename

    def __parseHeader( self, file ):
        # parse file header
        header = file.read( PDB_HEADER_SIZE )
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
        
    def __parseChapterOffsets(self, file):
        # get the offset of every chapters.
        file.seek( PDB_CHAPTER_OFFSET, os.SEEK_SET )
        for i in range( self.records+1 ):
            offset_record = file.read( 8 )
            if len(offset_record)!=8:
                raise PDBException( "Offset record size is not enough(8). %d" % i )
            offset = (ord(offset_record[0])<<24) + (ord(offset_record[1])<<16) + (ord(offset_record[2])<<8) + ord(offset_record[3])
            self.chapter_start_offsets.append( offset )
        self.chapter_end_offsets = self.chapter_start_offsets[1:]
        file.seek( 0, os.SEEK_END )
        self.chapter_end_offsets.append( file.tell()+1 )

    def __parseBasicInformation(self, file):
        file.seek( self.chapter_start_offsets[0], os.SEEK_SET )
        content = self.operation.processString( file.read( self.chapter_end_offsets[0] - self.chapter_start_offsets[0] ) )
        self.operation.parseBasicInformation( self, content )

    def parse( self ):
        """Must call parse() first to get PDB."""
        try:
            file = open( self.pdb_filename, "rb" )
            self.__parseHeader(file)
            self.__parseChapterOffsets(file)
            self.__parseBasicInformation(file)
        except PDBException, e:
            print e
        finally:
            file.close()
        return self

    def chapter(self, num ):
        """Read specified chapters."""
        content=""
        chap=num+1
        if chap>self.chapters:
            return ""
        try:
            file = open( self.pdb_filename, "rb" )
            file.seek( self.chapter_start_offsets[chap], os.SEEK_SET )
            raw_str = file.read( self.chapter_end_offsets[chap]-self.chapter_start_offsets[chap] )
            content = self.operation.processString( raw_str )
            result = self.operation.convert2unicode( self.empty_str.join(content) )
        finally:
            file.close()
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
        
    pdb = PDBFile( "66d.updb" ).parse()
    print( "Book name: %s " % pdb.book_name.encode( encoding ) )
    print( "Total %d chapters." % pdb.chapters )
    for chapter_title in pdb.chapter_titles:
        print( chapter_title.encode(encoding) )
    print( pdb.chapter(0).encode(encoding) )