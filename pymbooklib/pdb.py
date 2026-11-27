#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reader for Haodoo PDB and uPDB files."""

import os
import sys

PDB_HEADER_SIZE = 78
PDB_HEADER_RECORD = 76
PDB_HEADER_BOOK_TYPE = 64
PDB_HEADER_BOOK_TYPE_LEN = 4
PDB_CHAPTER_OFFSET = 78


class PDBException(Exception):
    """Raised when a PDB/uPDB file cannot be parsed."""


class BaseOperation:
    """Format-specific conversion helpers used by :class:`PDBFile`."""

    escape_char = b""

    def parse_basic_information(self, pdb, raw_text):
        fields = raw_text[8:].split(self.escape_char)
        if len(fields) < 5:
            raise PDBException("PDB metadata record is incomplete")

        pdb.book_name = self.convert_to_unicode(self.process_string(fields[0]))
        pdb.chapters = int(self.convert_to_unicode(
            self.process_string(fields[3])))
        pdb.contents = self.extract_contents(fields[4:])
        if pdb.chapters < 1:
            raise PDBException("PDB contains no chapters")

    def process_string(self, raw_text):
        raise NotImplementedError

    def convert_to_unicode(self, raw_text):
        raise NotImplementedError

    def extract_contents(self, raw_list):
        raise NotImplementedError


class UnicodeOperation(BaseOperation):
    """Decode uPDB text stored as little-endian UTF-16."""

    escape_char = b"\x1b\x00"

    def process_string(self, raw_text):
        units = []
        for index in range(0, len(raw_text) - 1, 2):
            unit = raw_text[index:index + 2]
            if unit == b"\x00\x00":
                break
            units.append(unit)
        return b"".join(units).decode("utf-16le")

    def convert_to_unicode(self, text):
        return text

    def extract_contents(self, raw_list):
        contents = []
        for raw_text in raw_list:
            text = self.process_string(raw_text)
            contents.extend(text.split("\r\n"))
        return contents


class DblByteOperation(BaseOperation):
    """Decode Haodoo PDB text using CP950."""

    escape_char = b"\x1b"

    def process_string(self, raw_text):
        return raw_text.split(b"\x00", 1)[0]

    def convert_to_unicode(self, raw_text):
        return raw_text.decode("cp950", errors="ignore")

    def extract_contents(self, raw_list):
        return [
            self.convert_to_unicode(self.process_string(raw_text))
            for raw_text in raw_list
        ]


class PDBFile:
    """Parse metadata and lazily read chapters from a PDB/uPDB file."""

    def __init__(self, pdb_filename):
        self.pdb_filename = os.fspath(pdb_filename)
        self.records = 0
        self.is_unicode = False
        self.chapter_start_offsets = []
        self.chapter_end_offsets = []
        self.book_name = ""
        self.contents = []
        self.chapters = 0
        self.operation = None

    def _parse_header(self, file_obj):
        header = file_obj.read(PDB_HEADER_SIZE)
        if len(header) != PDB_HEADER_SIZE:
            raise PDBException("PDB header is incomplete")

        book_type = header[
            PDB_HEADER_BOOK_TYPE:
            PDB_HEADER_BOOK_TYPE + PDB_HEADER_BOOK_TYPE_LEN
        ]
        if book_type == b"MTIU":
            self.is_unicode = True
            self.operation = UnicodeOperation()
        elif book_type == b"MTIT":
            self.operation = DblByteOperation()
        else:
            raise PDBException("Not a PDB or uPDB")

        self.records = int.from_bytes(
            header[PDB_HEADER_RECORD:PDB_HEADER_RECORD + 2], "big")
        if self.records < 1:
            raise PDBException("PDB contains no records")

    def _parse_chapter_offsets(self, file_obj):
        file_obj.seek(PDB_CHAPTER_OFFSET, os.SEEK_SET)
        for record_number in range(self.records):
            offset_record = file_obj.read(8)
            if len(offset_record) != 8:
                raise PDBException(
                    "Offset record size is not enough(8). %d" % record_number)
            self.chapter_start_offsets.append(
                int.from_bytes(offset_record[:4], "big"))

        file_obj.seek(0, os.SEEK_END)
        file_size = file_obj.tell()
        if any(offset >= file_size for offset in self.chapter_start_offsets):
            raise PDBException("PDB record offset is outside the file")
        if self.chapter_start_offsets != sorted(self.chapter_start_offsets):
            raise PDBException("PDB record offsets are not ordered")

        self.chapter_end_offsets = self.chapter_start_offsets[1:] + [file_size]

    def _parse_basic_information(self, file_obj):
        start = self.chapter_start_offsets[0]
        end = self.chapter_end_offsets[0]
        file_obj.seek(start, os.SEEK_SET)
        raw_text = file_obj.read(end - start)
        self.operation.parse_basic_information(self, raw_text)

        if self.chapters + 1 > self.records:
            raise PDBException("PDB chapter count exceeds record count")

    def parse(self):
        """Parse and return this file object."""
        self.chapter_start_offsets = []
        self.chapter_end_offsets = []
        with open(self.pdb_filename, "rb") as file_obj:
            self._parse_header(file_obj)
            self._parse_chapter_offsets(file_obj)
            self._parse_basic_information(file_obj)
        return self

    def chapter(self, num):
        """Read a chapter by its zero-based index."""
        if num < 0 or num >= self.chapters:
            return ""

        record_number = num + 1
        start = self.chapter_start_offsets[record_number]
        end = self.chapter_end_offsets[record_number]
        with open(self.pdb_filename, "rb") as file_obj:
            file_obj.seek(start, os.SEEK_SET)
            raw_text = file_obj.read(end - start)
        return self.operation.convert_to_unicode(
            self.operation.process_string(raw_text))

    def __str__(self):
        book_type = "uPDB" if self.is_unicode else "PDB"
        return (
            "\nFilename: %s (%s)\nRecords: %d\nChapters: %d\n" %
            (self.pdb_filename, book_type, self.records, self.chapters)
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Need at least 1 argument.\nUsage: %s pdb_filename [chapter]" %
              sys.argv[0])
        sys.exit(2)

    chapter_number = int(sys.argv[2]) if len(sys.argv) == 3 else 0
    try:
        book = PDBFile(sys.argv[1]).parse()
        print("Book name: %s" % book.book_name)
        print("Total %d chapters." % book.chapters)
        for title in book.contents:
            print(title)
        print(book.chapter(chapter_number))
    except (OSError, PDBException, ValueError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
