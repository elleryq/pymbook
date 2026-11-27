#!/usr/bin/env python3
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
"""MainWindow"""
import os
import logging

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gio, Gtk

from . import pdb
from . import config, version
from .pdb import PDBException
from .version import APP_NAME, APP_VERSION, APP_COMMENT, APP_AUTHORS
from .pdbcontents import PDBContents
from .pdbcanvas import PDBCanvas
from .bookshelf import BookshelfWidget
from .state import (
    ShelfState, ShelfCanBackState, ContentState, ContentCanBackState,
    State, ReadingState,
)
from .translation import _
from .utils import get_font_tuple, convert_pdb_to_pages


class MainWindow:
    """MainWindow"""
    def __init__(self, filename=None):
        self.chapter = -1
        self.page = -1
        self.pdb_filename = None
        self.pdb = None
        self.pref_dlg = None
        self.config = config.Config()
        self.config.load()
        self.initialize_logging()
        self.initialize_component()
        if filename and self.open_pdb(filename):
            self.pdb_filename = filename

    def initialize_logging(self):
        import time
        if self.config[config.ENTRY_LOG_FILENAME]:
            logging.basicConfig(
                filename=self.config[config.ENTRY_LOG_FILENAME],
                level=logging.DEBUG)
        logging.info(">>> Start logging at %s" % time.strftime(
            "%Y-%m-%d %X", time.localtime()))

    def load_ui(self, builder):
        result = True
        try:
            builder.set_translation_domain(APP_NAME)
            glade_file = os.path.join(
                os.path.dirname(version.__file__), 'main_window.glade')
            builder.add_from_file(glade_file)
        except Exception as e:
            logging.error(e)
            err_dialog = Gtk.MessageDialog(
                parent=None,
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CLOSE,
                text=repr(e))
            result = err_dialog.run()
            err_dialog.destroy()
            self.leave()
            result = False
        return result

    def initialize_recent_files(self, builder):
        self.recent = Gtk.RecentManager()
        menu_recent = Gtk.RecentChooserMenu.new_for_manager(self.recent)
        menu_recent.set_limit(10)
        self.file_filter = Gtk.RecentFilter()
        self.file_filter.add_pattern("*.pdb")
        self.file_filter.add_pattern("*.updb")
        menu_recent.set_filter(self.file_filter)
        menu_recent.connect("item-activated", self.select_recent_cb)
        menuitem_recent = builder.get_object("mi_recent_files")
        menuitem_recent.set_submenu(menu_recent)

    def create_state_from_name(self, state_name):
        states = {
            config.STATE_BOOKSHELF: ShelfState(),
            config.STATE_CONTENT: ContentState(),
            config.STATE_READING: ReadingState()
        }
        if not state_name in states:
            return None
        return states[state_name]

    def restore_state(self):
        State.config = self.config
        State.window = self

        self.state = None

        if self.config[config.ENTRY_STATE]:
            self.state = self.create_state_from_name(
                self.config[config.ENTRY_STATE])

        if not self.state:
            self.state = ShelfState()

        try:
            self.state.load()
        except Exception as e:
            logging.warning(e)
            logging.info("Fallback to ShelfState")
            self.state = ShelfState()
            self.state.load()
        self.state.enter()

    def initialize_component(self):
        builder = Gtk.Builder()
        if not self.load_ui(builder):
            return

        self.window = builder.get_object("window1")
        self.window.set_title(APP_NAME)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        # set minimal size
        self.window.set_size_request(
            config.DEFAULT_WIDTH, config.DEFAULT_HEIGHT)
        # resize to saved size
        self.window.resize(
            self.config[config.ENTRY_WIDTH], self.config[config.ENTRY_HEIGHT])

        self.btn_shelf = builder.get_object("btn_shelf")
        self.btn_content = builder.get_object("btn_content")
        self.btn_return = builder.get_object("btn_return")

        self.act_quit = builder.get_object("act_quit")
        self.notebook = builder.get_object("notebook1")

        # Recent files
        self.initialize_recent_files(builder)

        font = "%s %d" % (self.config[config.ENTRY_FONT_NAME],
                          self.config[config.ENTRY_FONT_SIZE])

        # Add bookshelf tab
        self.bookshelf = BookshelfWidget(self.config[config.ENTRY_SHELF_PATH])
        self.bookshelf.set_font(font)
        frame = Gtk.Frame()
        frame.show()
        frame.add(self.bookshelf)
        label = Gtk.Label(_("Bookshelf"))
        self.notebook.append_page(frame, label)
        self.bookshelf.show()

        # Add contents tab
        self.pdb_contents = PDBContents()
        self.pdb_contents.set_font(font)
        frame = Gtk.Frame()
        frame.show()
        frame.add(self.pdb_contents)
        label = Gtk.Label(_("Contents"))
        self.notebook.append_page(frame, label)
        self.pdb_contents.show()

        # Add text tab
        self.pdb_canvas = PDBCanvas()
        frame = Gtk.Frame()
        self.pdb_canvas.set_font(font)
        frame.add(self.pdb_canvas)
        label = Gtk.Label(_("Text"))
        self.notebook.append_page(frame, label)

        self.pdb_canvas.show()
        frame.show()

        self.restore_state()

        # connect signals
        self.bookshelf.connect(
            "book_selected", self.bookshelf_book_selected_cb)
        self.pdb_contents.connect(
            "chapter_selected", self.pdb_contents_chapter_selected_cb)
        self.pdb_canvas.connect(
            "tell_callback", self.pdb_canvas_tell_callback)

        builder.connect_signals(self)
        self.window.show()

    def open_pdb(self, pdb_filename):
        try:
            self.pdb = pdb.PDBFile(pdb_filename).parse()
            self.pdb_contents.set_pdb(self.pdb)
            self.pdb_contents.redraw_canvas()
            self.pdb_canvas.set_pdb(self.pdb)
            self.pdb_canvas.redraw_canvas()
        except PDBException as ex:
            logging.error("Cannot open specified pdb: %s", repr(ex))
            dialog = Gtk.MessageDialog(
                parent=self.window,
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CLOSE,
                text=_("Cannot open specified pdb."))
            result = dialog.run()
            dialog.destroy()
            return False
        except Exception as ex:
            logging.exception("Cannot open specified pdb: %s", ex)
            return False
        self.window.set_title("%s - %s" % (APP_NAME, self.pdb.book_name))
        uri = Gio.File.new_for_path(pdb_filename).get_uri()
        recent_data = Gtk.RecentData()
        recent_data.mime_type = "application/octet-stream"
        recent_data.app_name = APP_NAME
        recent_data.app_exec = "pymbook %u"
        recent_data.display_name = self.pdb.book_name
        self.recent.add_full(uri, recent_data)
        return True

    def leave(self):
        rect = self.window.get_allocation()
        self.config[config.ENTRY_WIDTH] = rect.width
        self.config[config.ENTRY_HEIGHT] = rect.height
        self.config[config.ENTRY_CURRENT_PDB] = self.pdb_filename
        self.config.save()
        Gtk.main_quit()

    def window1_delete_event_cb(self, widget, event, data=None):
        self.state.save()
        self.act_quit.activate()

    def select_recent_cb(self, menu):
        uri = menu.get_current_item().get_uri()
        filename = Gio.File.new_for_uri(uri).get_path()
        if not filename:
            logging.error("Cannot read local path from recent URI: %s", uri)
            return
        if self.open_pdb(filename):
            self.pdb_filename = filename
            self.state = ContentState().enter()

    def act_quit_activate_cb(self, b):
        self.leave()

    def act_about_activate_cb(self, b):
        dialog=Gtk.AboutDialog()
        dialog.set_name( APP_NAME )
        dialog.set_version( APP_VERSION )
        dialog.set_authors( APP_AUTHORS )
        dialog.set_comments( APP_COMMENT )
        dialog.set_license( _("Distributed under the GPL3.") )
        dialog.run()
        dialog.destroy()

    def act_open_activate_cb(self, b):
        dialog = Gtk.FileChooserDialog(
            title=_("Open..."),
            parent=None,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)

        _filter = Gtk.FileFilter()
        _filter.set_name(_("PDB/uPDB files"))
        _filter.add_pattern("*.pdb")
        _filter.add_pattern("*.updb")
        dialog.add_filter(_filter)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.pdb_filename = dialog.get_filename()
            if self.open_pdb(self.pdb_filename):
                self.state = ContentState().enter()
                self.state.save()
        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()

    def act_font_activate_cb(self, b):
        dialog = Gtk.FontChooserDialog(_("Choose font"), None)
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_font("%s %d" % (self.config[config.ENTRY_FONT_NAME],
                                   self.config[config.ENTRY_FONT_SIZE]))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            font_name = dialog.get_font()
            self.bookshelf.set_font(font_name)
            self.pdb_contents.set_font(font_name)
            self.pdb_canvas.set_font(font_name)
            font, font_size = get_font_tuple(font_name)
            self.config[config.ENTRY_FONT_NAME] = font
            self.config[config.ENTRY_FONT_SIZE] = font_size
            self.config.save()
        dialog.destroy()
        self.pdb_contents.redraw_canvas()
        self.pdb_canvas.redraw_canvas()

    def act_index_activate_cb(self, b):
        self.state = ContentCanBackState().enter()
        self.state.save()

    def act_preference_activate_cb(self, b):
        try:
            builder = Gtk.Builder()
            builder.set_translation_domain(APP_NAME)
            glade_file = os.path.join(os.path.dirname(version.__file__),
                                      'preference_dialog.glade')
            pref_dlg = builder.add_from_file(glade_file)
        except Exception as e:
            logging.error(e)
            return
        pref_dlg = builder.get_object("dialog1")
        chooser_btn = builder.get_object("filechooserbutton1")
        shelf_path = os.path.expanduser(
            self.config[config.ENTRY_SHELF_PATH])
        chooser_btn.set_current_folder(shelf_path)

        result = pref_dlg.run()
        # OK
        if result == Gtk.ResponseType.OK:
            selected_path = chooser_btn.get_filename()
            if selected_path:
                self.config[config.ENTRY_SHELF_PATH] = selected_path
                self.config.save()
        pref_dlg.destroy()

    def act_shelf_activate_cb(self, b):
        if isinstance(self.state, ReadingState):
            self.state = ShelfCanBackState().enter()
        else:
            self.state = ShelfState().enter()

    def act_return_activate_cb(self, b):
        self.state = ReadingState().enter()

    def act_export2text_activate_cb(self, b):
        dialog = Gtk.FileChooserDialog(
            title=_("Save..."),
            parent=None,
            action=Gtk.FileChooserAction.SAVE,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE_AS, Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)

        _filter = Gtk.FileFilter()
        _filter.set_name(_("Text files"))
        _filter.add_pattern("*.txt")
        dialog.add_filter(_filter)

        response = dialog.run()
        text_filename = (
            dialog.get_filename()
            if response == Gtk.ResponseType.OK else None
        )
        dialog.destroy()
        if not text_filename:
            return
        pages = convert_pdb_to_pages(self.pdb, 24, 35)
        with open(text_filename, "w", encoding="utf-8") as text_file:
            for chapter_num, num_in_chapter, page, _ in pages:
                for col in page:
                    text_file.write("".join(col))
                    text_file.write("\n")
        dialog = Gtk.MessageDialog(
            parent=self.window,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.CLOSE,
            text=_("Converting is finished.  The file is at '%s'") %
            text_filename)
        result = dialog.run()
        dialog.destroy()

    def pdb_contents_chapter_selected_cb(self, widget, chapter):
        if chapter == -1:
            dialog = Gtk.MessageDialog(
                parent=self.window,
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CLOSE,
                text=_("No such chapter."))
            result = dialog.run()
            dialog.destroy()
            return
        logging.debug("chapter=%d" % chapter)
        self.pdb_canvas.redraw_canvas()
        self.pdb_canvas.set_chapter(chapter)
        self.state = ReadingState().enter()
        self.state.save()

    def bookshelf_book_selected_cb(self, widget, book):
        if book == -1:
            dialog = Gtk.MessageDialog(
                parent=self.window,
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CLOSE,
                text=_("No such book."))
            result = dialog.run()
            dialog.destroy()
            return

        book_name, pdb_filename = self.bookshelf.get_book(book)
        logging.debug("(%s, %s) is selected" % (book_name, pdb_filename))
        if self.open_pdb(pdb_filename):
            self.pdb_filename = pdb_filename
            self.pdb_contents.set_pdb(self.pdb)
            self.pdb_contents.redraw_canvas()
            self.state = ContentState().enter()
            self.state.save()

    def pdb_canvas_tell_callback(self, widget, chapter, page):
        self.chapter = chapter
        self.page = page
        self.state.save()
