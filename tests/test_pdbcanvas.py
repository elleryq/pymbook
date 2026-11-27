import unittest
from types import SimpleNamespace

try:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GLib, Gtk

    from pymbooklib.pdbcanvas import PDBCanvas
except (ImportError, ValueError):
    Gdk = GLib = Gtk = PDBCanvas = None


class LongBook:
    chapters = 2
    text = "甲乙丙丁戊己庚辛壬癸子丑寅卯" * 200

    def chapter(self, chapter_number):
        return self.text


@unittest.skipIf(Gtk is None, "GTK 3/PyGObject are unavailable")
class PDBCanvasResizeTests(unittest.TestCase):
    def settle_gtk(self):
        loop = GLib.MainLoop()
        GLib.timeout_add(250, loop.quit)
        loop.run()

    def test_resize_keeps_the_same_text_position_visible(self):
        initialized, _ = Gtk.init_check([])
        if not initialized:
            self.skipTest("No GTK display is available")

        window = Gtk.OffscreenWindow()
        self.addCleanup(window.destroy)
        canvas = PDBCanvas()
        canvas.set_size_request(640, 480)
        window.add(canvas)
        window.show_all()
        self.settle_gtk()
        self.addCleanup(
            lambda: GLib.source_remove(canvas.timer) if canvas.timer else None)

        book = LongBook()
        canvas.set_pdb(book)
        canvas.set_chapter(1)
        canvas.scroll_event(
            canvas, SimpleNamespace(direction=Gdk.ScrollDirection.DOWN))
        self.settle_gtk()

        current_page = canvas.source[canvas.datasource.current_page]
        chapter, text_offset = current_page[0], current_page[3]
        old_allocation = canvas.get_allocation()

        canvas.set_size_request(360, 300)
        window.set_size_request(360, 300)
        window.resize(360, 300)
        self.settle_gtk()

        new_allocation = canvas.get_allocation()
        current_page = canvas.source[canvas.datasource.current_page]
        self.assertNotEqual(
            (old_allocation.width, old_allocation.height),
            (new_allocation.width, new_allocation.height))
        self.assertEqual(current_page[0], chapter)
        self.assertLessEqual(current_page[3], text_offset)
        following_pages = [
            page[3] for page in
            canvas.source[canvas.datasource.current_page + 1:]
            if page[0] == chapter
        ]
        if following_pages:
            self.assertGreater(following_pages[0], text_offset)
        else:
            self.assertLess(text_offset, len(book.chapter(chapter)))
