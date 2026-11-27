# Copilot instructions

## Build, run, and verify

- The application requires Python 3.8+, GTK 3, PyGObject and Pycairo.
- Run from the repository root with `./pymbook [path/to/book.pdb]`. The optional argument opens a PDB/uPDB book at startup.
- Install from source with `python3 -m pip install .`. Building translations and the desktop entry requires `msgfmt` and `intltool-merge`.
- Run tests with `python3 -m unittest discover -v`; run one parser test with `python3 -m unittest tests.test_pdb.PDBFileTests.test_reads_cp950_pdb_metadata_and_chapters -v`.
- For a parser smoke check on one book, run `python3 pymbooklib/pdb.py path/to/book.pdb [chapter-number]`.

## Architecture

- `pymbook` is the GTK entry point. It opens `pymbooklib.mainwindow.MainWindow`, which loads the Glade UI, connects GTK signals, manages the active book, and coordinates the reader widgets.
- `pymbooklib/pdb.py` parses Haodoo PDB/uPDB files. It reads binary headers and chapter offsets, recognizes `MTIT` (CP950) and `MTIU` (UTF-16LE), and exposes decoded metadata and chapter text.
- The main window composes three custom GTK drawing areas: `BookshelfWidget` lists books discovered from the configured directory, `PDBContents` displays selectable chapters, and `PDBCanvas` renders book text. `PDBWidget` and `CustomDrawingArea` provide shared drawing, font, and redraw behavior.
- `utils.py` turns chapters into columns and pages using the drawing area's dimensions. `PagedDataSource` provides the shared page navigation used by the shelf, contents, and reading views.
- `state.py` models bookshelf, contents, and reading modes. State transitions update the active tab and controls; state save/load persists the open book and reading position through `config.py`.
- UI definitions are loaded at runtime from `pymbooklib/main_window.glade` and `preference_dialog.glade`; `setup.py` explicitly packages these along with the logo. Keep runtime UI resources included in package data when adding or renaming them.

## Repository-specific conventions

- Use explicit package-relative imports in `pymbooklib`; the root `pymbook` script is the executable entry point.
- Keep book data as bytes until the format-specific parser decodes it: MTIT is CP950 and MTIU is UTF-16LE. Do not conflate file offsets/record tables with decoded text.
- GTK widgets use PyGObject GTK 3 draw callbacks; drawing code receives its Cairo context from the `draw` signal, and `size-allocate` recalculates page layout.
- User-visible strings use the `_()` translation function. Translation catalogs live in `po/`; desktop-entry strings are marked for gettext in `data/pymbook.desktop.in`.
- `setup.py` and `pyproject.toml` define Python packaging; Debian uses `pybuild`/`dh_python3` and the RPM spec uses Python 3 macros. Keep GTK 3/PyGObject/Pycairo dependencies consistent across all three.
