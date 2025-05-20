# ruff: noqa
# fmt: off
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import re
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).absolute().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# -- Project information -----------------------------------------------------

project = "wwvb"
copyright = "2021, Jeff Epler"
author = "Jeff Epler"

# The full version, including alpha/beta/rc tags
final_version = ""
git_describe = subprocess.run(
    ["git", "describe", "--tags", "--dirty"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    encoding="utf-8", check=False,
)
if git_describe.returncode == 0:
    git_version = re.search(
        r"^\d(?:\.\d){0,2}(?:\-(?:alpha|beta|rc)\.\d+){0,1}",
        str(git_describe.stdout),
    )
    if git_version:
        final_version = git_version[0]
else:
    print("Failed to retrieve git version:", git_describe.stdout)

version = release = final_version


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx_mdinclude",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

autodoc_typehints = "description"
autodoc_class_signature = "separated"

default_role = "any"

intersphinx_mapping = {'py': ('https://docs.python.org/3', None)}

# SPDX-FileCopyrightText: 2021-2024 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only
