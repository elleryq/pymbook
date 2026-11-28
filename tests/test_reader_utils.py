import os
import tempfile
import unittest

from pymbook.config import Config, ENTRY_WIDTH
from pymbook.pageddatasource import PagedDataSource
from pymbook.utils import (
    convert_columns_to_pages, convert_pdb_to_pages, find_page_for_offset,
)


class FakeBook:
    chapters = 1

    def chapter(self, chapter_number):
        return "甲乙丙丁"


class ReaderUtilityTests(unittest.TestCase):
    def test_config_persists_integer_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, "pymbook.conf")
            config = Config(filename)
            config.load()
            config[ENTRY_WIDTH] = 800
            config.save()

            restored = Config(filename)
            restored.load()
            self.assertEqual(restored[ENTRY_WIDTH], 800)

    def test_page_source_moves_and_clamps_at_page_boundaries(self):
        source = PagedDataSource([["first"], ["second"]])

        source.go_previous()
        self.assertEqual(source.current_page, 0)
        source.go_next()
        source.go_next()
        self.assertEqual(source.get_current_page(), ["second"])

    def test_text_pagination_keeps_unicode_and_page_order(self):
        pages = convert_pdb_to_pages(FakeBook(), 2, 2)

        self.assertEqual(pages, [(0, 0, [["甲", "乙"], ["丙", "丁"]], 0)])
        self.assertEqual(convert_columns_to_pages([1, 2, 3], 2),
                         [[1, 2], [3]])

    def test_reflow_finds_page_containing_the_same_text_offset(self):
        class LongBook:
            chapters = 1
            text = "甲乙丙丁戊己庚辛壬癸子丑寅卯" * 20

            def chapter(self, chapter_number):
                return self.text

        book = LongBook()
        old_pages = convert_pdb_to_pages(book, 2, 2)
        new_pages = convert_pdb_to_pages(book, 1, 3)
        old_text_offset = old_pages[2][3]

        new_page_index = find_page_for_offset(
            new_pages, 0, old_text_offset)
        new_page = new_pages[new_page_index]

        self.assertLessEqual(new_page[3], old_text_offset)
        if new_page_index + 1 < len(new_pages):
            self.assertGreater(
                new_pages[new_page_index + 1][3], old_text_offset)


if __name__ == "__main__":
    unittest.main()
