import os
import tempfile
import unittest

from pymbooklib.pdb import PDBException, PDBFile


def build_book(book_type, name, titles, chapters):
    if book_type == b"MTIT":
        escape = b"\x1b"
        encode = lambda text: text.encode("cp950")
        title_fields = [encode(title) for title in titles]
    else:
        escape = b"\x1b\x00"
        encode = lambda text: text.encode("utf-16le")
        title_fields = [encode("\r\n".join(titles))]

    metadata = b"\x00" * 8 + escape.join(
        [encode(name), encode("author"), encode(""), encode(str(len(chapters)))]
        + title_fields
    )
    chapter_records = []
    for text in chapters:
        data = encode(text)
        if book_type == b"MTIT":
            data += b"\x00"
        else:
            data += b"\x00\x00"
        chapter_records.append(data)

    records = [metadata] + chapter_records
    header = bytearray(78)
    header[64:68] = book_type
    header[76:78] = len(records).to_bytes(2, "big")

    first_offset = len(header) + len(records) * 8
    offsets = []
    next_offset = first_offset
    for record in records:
        offsets.append(next_offset.to_bytes(4, "big") + b"\x00" * 4)
        next_offset += len(record)

    return bytes(header) + b"".join(offsets) + b"".join(records)


class PDBFileTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def write_book(self, content):
        filename = os.path.join(self.temp_dir.name, "book.pdb")
        with open(filename, "wb") as file_obj:
            file_obj.write(content)
        return filename

    def test_reads_cp950_pdb_metadata_and_chapters(self):
        filename = self.write_book(build_book(
            b"MTIT", "測試書", ["第一章", "第二章"], ["第一段", "第二段"]))

        book = PDBFile(filename).parse()

        self.assertFalse(book.is_unicode)
        self.assertEqual(book.book_name, "測試書")
        self.assertEqual(book.contents, ["第一章", "第二章"])
        self.assertEqual(book.chapter(0), "第一段")
        self.assertEqual(book.chapter(1), "第二段")

    def test_reads_utf16le_updb_metadata_and_chapters(self):
        filename = self.write_book(build_book(
            b"MTIU", "測試書", ["第一章", "第二章"], ["第一段", "第二段"]))

        book = PDBFile(filename).parse()

        self.assertTrue(book.is_unicode)
        self.assertEqual(book.book_name, "測試書")
        self.assertEqual(book.contents, ["第一章", "第二章"])
        self.assertEqual(book.chapter(0), "第一段")
        self.assertEqual(book.chapter(1), "第二段")

    def test_rejects_unknown_file_type(self):
        header = bytearray(78)
        header[64:68] = b"NOPE"
        filename = self.write_book(bytes(header))

        with self.assertRaises(PDBException):
            PDBFile(filename).parse()

    def test_out_of_range_chapters_are_empty(self):
        filename = self.write_book(build_book(
            b"MTIT", "Test", ["Chapter"], ["Text"]))
        book = PDBFile(filename).parse()

        self.assertEqual(book.chapter(-1), "")
        self.assertEqual(book.chapter(1), "")


if __name__ == "__main__":
    unittest.main()
