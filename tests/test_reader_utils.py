import os
import tempfile
import unittest

from pymbooklib.config import Config, ENTRY_WIDTH
from pymbooklib.pageddatasource import PagedDataSource
from pymbooklib.utils import convert_columns_to_pages, convert_pdb_to_pages


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

        self.assertEqual(pages, [(0, 0, [["甲", "乙"], ["丙", "丁"]])])
        self.assertEqual(convert_columns_to_pages([1, 2, 3], 2),
                         [[1, 2], [3]])


if __name__ == "__main__":
    unittest.main()
