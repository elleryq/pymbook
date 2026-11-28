import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

try:
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    from pymbooklib import config, mainwindow
    from pymbooklib.bookshelf import BookshelfWidget
    from pymbooklib.translation import _
except (ImportError, ValueError):
    Gtk = None

from tests.test_pdb import build_book


@unittest.skipIf(Gtk is None, "GTK 3/PyGObject are unavailable")
class BookshelfPreferenceTests(unittest.TestCase):
    def setUp(self):
        initialized, _ = Gtk.init_check([])
        if not initialized:
            self.skipTest("No GTK display is available")

        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.old_path = os.path.join(self.temp.name, "old")
        self.new_path = os.path.join(self.temp.name, "new")
        self.empty_path = os.path.join(self.temp.name, "empty")
        for path in (self.old_path, self.new_path, self.empty_path):
            os.mkdir(path)
        self.write_book(self.old_path, "old.pdb", "Old")
        self.write_book(self.new_path, "new.updb", "New", b"MTIU")

        self.window = Gtk.OffscreenWindow()
        self.addCleanup(self.window.destroy)
        self.shelf = BookshelfWidget(self.old_path)
        self.shelf.set_size_request(640, 480)
        self.window.add(self.shelf)
        self.window.show_all()
        while Gtk.events_pending():
            Gtk.main_iteration()

        self.app = mainwindow.MainWindow.__new__(mainwindow.MainWindow)
        self.app.window = self.window
        self.app.bookshelf = self.shelf
        self.app.config = config.Config(os.path.join(self.temp.name, "config"))
        self.app.config.load()
        self.app.config[config.ENTRY_SHELF_PATH] = self.old_path
        self.app.config.save()
        self.app.state = object()

    def write_book(self, directory, name, title, book_type=b"MTIT"):
        with open(os.path.join(directory, name), "wb") as file_obj:
            file_obj.write(build_book(book_type, title, ["Chapter"], ["Text"]))

    def change_preference(self, path, response):
        dialog = MagicMock()
        dialog.run.return_value = response
        chooser = MagicMock()
        chooser.get_filename.return_value = path
        builder = MagicMock()
        builder.get_object.side_effect = lambda name: {
            "dialog1": dialog, "filechooserbutton1": chooser,
        }[name]
        with patch.object(mainwindow.Gtk, "Builder", return_value=builder):
            self.app.act_preference_activate_cb(None)
        dialog.destroy.assert_called_once()

    def test_selecting_new_and_empty_directories_refreshes_shelf(self):
        state = self.app.state
        self.change_preference(self.new_path, Gtk.ResponseType.OK)
        self.assertEqual(self.app.config[config.ENTRY_SHELF_PATH], self.new_path)
        self.assertEqual(self.shelf.books, [
            ("New", os.path.join(self.new_path, "new.updb"))])
        self.assertEqual(self.shelf.datasource.get_current_page(), self.shelf.books)
        self.assertEqual(self.shelf.datasource.current_page, 0)
        self.assertIs(self.app.state, state)
        saved = config.Config(self.app.config.filename)
        saved.load()
        self.assertEqual(saved[config.ENTRY_SHELF_PATH], self.new_path)

        self.change_preference(self.empty_path, Gtk.ResponseType.OK)
        self.assertEqual(self.shelf.books, [])
        self.assertEqual(self.shelf.datasource.get_current_page(), [])
        with patch.object(Gtk, "render_layout") as render:
            self.shelf.expose(self.shelf, MagicMock())
        self.assertEqual(render.call_args.args[4].get_text(), _("No books found."))

        self.change_preference(self.old_path, Gtk.ResponseType.OK)
        self.assertEqual(self.shelf.books, [
            ("Old", os.path.join(self.old_path, "old.pdb"))])
        self.assertEqual(self.shelf.datasource.get_current_page(), self.shelf.books)

    def test_new_shelf_resets_pagination_and_selection(self):
        for index in range(40):
            self.write_book(self.new_path, f"{index:02}.pdb", f"Book {index:02}")
        self.change_preference(self.new_path, Gtk.ResponseType.OK)
        self.shelf.datasource.go_next()
        self.assertGreater(self.shelf.datasource.current_page, 0)

        self.change_preference(self.old_path, Gtk.ResponseType.OK)
        self.assertEqual(self.shelf.datasource.current_page, 0)
        region_x, region_y, _, _ = self.shelf.regions[0]
        selected = self.shelf.which_book(region_x, region_y)
        self.assertEqual(self.shelf.get_book(selected),
                         ("Old", os.path.join(self.old_path, "old.pdb")))

    def test_cancel_keeps_original_shelf_and_setting(self):
        self.change_preference(self.new_path, Gtk.ResponseType.CANCEL)
        self.assertEqual(self.app.config[config.ENTRY_SHELF_PATH], self.old_path)
        self.assertEqual(self.shelf.books, [
            ("Old", os.path.join(self.old_path, "old.pdb"))])

    def test_shelf_path_expands_home_directory(self):
        with patch.dict(os.environ, {"HOME": self.temp.name}):
            shelf = BookshelfWidget("~/old")
        self.assertEqual(shelf.books, [
            ("Old", os.path.join(self.old_path, "old.pdb"))])

    def test_unreadable_directory_preserves_shelf_and_reports_error(self):
        with self.assertLogs(level="ERROR"):
            with patch("pymbooklib.utils.os.scandir",
                       side_effect=PermissionError("Access denied")):
                with patch.object(mainwindow.Gtk, "MessageDialog") as message:
                    self.change_preference(self.new_path, Gtk.ResponseType.OK)
        self.assertEqual(self.app.config[config.ENTRY_SHELF_PATH], self.old_path)
        self.assertEqual(self.shelf.books, [
            ("Old", os.path.join(self.old_path, "old.pdb"))])
        saved = config.Config(self.app.config.filename)
        saved.load()
        self.assertEqual(saved[config.ENTRY_SHELF_PATH], self.old_path)
        message.return_value.run.assert_called_once()
        message.return_value.destroy.assert_called_once()
        message.return_value.format_secondary_text.assert_called_once_with(
            "Access denied")
