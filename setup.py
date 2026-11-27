#!/usr/bin/env python3
"""Build and install pymbook."""

import glob
import os
from pathlib import Path
import subprocess

from distutils.command.install_data import install_data
from setuptools import setup
from setuptools.command.build import build


class BuildData(build):
    """Build gettext catalogs and the translated desktop entry."""

    def run(self):
        super().run()

        build_dir = Path(self.build_base)
        mo_dir = build_dir / "mo"
        for po_file in sorted(Path("po").glob("*.po")):
            language = po_file.stem
            output_dir = mo_dir / language
            output_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["msgfmt", "-o", str(output_dir / "pymbook.mo"), str(po_file)],
                check=True,
            )

        desktop_dir = build_dir / "data"
        desktop_dir.mkdir(parents=True, exist_ok=True)
        environment = os.environ.copy()
        environment["LC_ALL"] = "C"
        subprocess.run(
            [
                "intltool-merge", "-d", "-u", "-c",
                "po/.intltool-merge-cache", "po",
                "data/pymbook.desktop.in",
                str(desktop_dir / "pymbook.desktop"),
            ],
            check=True,
            env=environment,
        )


class InstallData(install_data):
    """Install generated catalogs and desktop integration."""

    def run(self):
        build_dir = Path(self.get_finalized_command("build").build_base)
        self.data_files.extend(
            [
                (
                    os.path.join("share", "locale", language, "LC_MESSAGES"),
                    [str(mo_file)],
                )
                for mo_file in sorted((build_dir / "mo").glob("*/pymbook.mo"))
                for language in [mo_file.parent.name]
            ]
        )
        self.data_files.append(
            ("share/applications", [str(build_dir / "data/pymbook.desktop")])
        )
        super().run()


setup(
    name="pymbook",
    version="0.4",
    description="Reader for Haodoo PDB/uPDB books",
    author="Yan-ren Tsai",
    author_email="elleryq@gmail.com",
    url="https://www.haodoo.net/",
    license="GPL-3.0-or-later",
    python_requires=">=3.8",
    install_requires=["PyGObject>=3.42", "pycairo>=1.20"],
    scripts=["pymbook"],
    packages=["pymbooklib"],
    data_files=[
        ("share/pixmaps", ["data/icons/48x48/pymbook.png"]),
        (
            "share/icons/hicolor/scalable/apps",
            glob.glob("data/icons/scalable/*.svg"),
        ),
        ("share/icons/hicolor/16x16/apps", glob.glob("data/icons/16x16/*.png")),
        ("share/icons/hicolor/22x22/apps", glob.glob("data/icons/22x22/*.png")),
        ("share/icons/hicolor/24x24/apps", glob.glob("data/icons/24x24/*.png")),
        ("share/icons/hicolor/32x32/apps", glob.glob("data/icons/32x32/*.png")),
        ("share/icons/hicolor/48x48/apps", glob.glob("data/icons/48x48/*.png")),
    ],
    package_data={
        "pymbooklib": [
            "main_window.glade",
            "preference_dialog.glade",
            "haodoo_logo.png",
        ]
    },
    cmdclass={"build": BuildData, "install_data": InstallData},
)
