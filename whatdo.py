#!/usr/bin/env python
import os
import subprocess
import sys

import argparse
from re import split
from string import punctuation, whitespace

from dataclasses import dataclass
from itertools import count, dropwhile
from typing import Iterable

import logging

parser = argparse.ArgumentParser(add_help=False)


parser.add_argument("--help", action="help", help="show this help message and exit")


parser.add_argument("-d", "--dir", type=str, help="Root directory to start searching")

parser.add_argument(
    "-c",
    "--count",
    action="store_true",
    help="Only display the total number of todos and suppress details",
)

parser.add_argument(
    "-g",
    "--goto",
    type=str,
    nargs="?",
    default="",
    const="FIRST",
    help="Open a todo item by number in EDITOR (defaults to vim if not set). Only works for programs that follow the CLI syntax 'program +line filename': this includes (n)vim and nano",
)


parser.add_argument(
    "-s",
    "--search",
    type=str,
    help="Set a custom string for the search. Lines are selected if they begin with the search string, ignoring whitespace and punctuation. Defaults to 'TODO'",
)

parser.add_argument(
    "-n",
    "--norecurse",
    action="store_true",
    help="Only search in files directly inside DIR, not subdirectories",
)

parser.add_argument(
    "-h",
    "--hidden",
    action="store_true",
    help="Search inside hidden directories and files ",
)

parser.add_argument("--debug", action="store_true", help="Enable debug logging")


@dataclass
class TodoItem:
    """Represents a single todo item."""

    line_num: int
    content: str
    index: int = 0


@dataclass
class TodosFile:
    """Represents todos within a single file."""

    filename: str
    items: list[TodoItem]
    index: int = 0


def colorize(text: str, color: str) -> str:
    """Wrapper around ANSI terminal codes for colorized output"""
    ansi_esc = "\033["
    color_codes = {
        "BLACK": 90,
        "RED": 91,
        "GREEN": 92,
        "YELLOW": 93,
        "BLUE": 94,
        "MAGENTA": 95,
        "CYAN": 96,
        "WHITE": 97,
    }

    return "{}{}m{}{}0m".format(ansi_esc, color_codes[color.upper()], text, ansi_esc)


def file_path_generator(
    root_path: os.PathLike | str = "", recurse: bool = True, ignore_hidden: bool = True
) -> Iterable[str]:
    """
    Returns an iterator over all files within the given root path
    recurse and ignore_hidden params determine if subdirectories are also searched recursively,
    and to count hidden files and directories ('dotfiles'), respectively.

    """

    # set the root path

    if not root_path:
        root_path = os.getcwd()

    if not isinstance(root_path, str):
        root_path = str(os.fspath(root_path))

    if os.path.isfile(root_path):
        yield root_path
        return

    local_dirs: list[os.DirEntry] = []

    dir_contents = os.scandir(root_path)

    fs_object: os.DirEntry
    for fs_object in dir_contents:

        if fs_object.name.startswith(".") and ignore_hidden:
            continue

        if fs_object.is_dir():

            local_dirs.append(fs_object)
            continue

        yield fs_object.path

    if recurse:
        for local_dir in local_dirs:
            sub_generator = file_path_generator(root_path=local_dir)

            for subitem in sub_generator:
                yield subitem


def todos_generator(
    files_iter: Iterable[os.PathLike | str],
    command_start: str = "TODO",
    ignore_chars: str = (whitespace + punctuation),
) -> Iterable[TodosFile]:

    """
    Takes an iterable over file path objects (os.PathLike), and an optional string defining the start of a TODO line, (default is TODO)
    Returns an iterable that, for each file containing at least one line matching starting with that sequence, yields a TodosFile dataclass containing those matching lines.
    Whitespace and punctuation at the start of a line are ignored

    """

    files_processed_counter = count(1)

    for file_path in files_iter:

        if not isinstance(file_path, str):
            file_path = str(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as infile:
                file_lines = infile.readlines()
        except UnicodeDecodeError:
            # kind of a hacky way to ensure binary files are skipped
            # but if it's stupid and it works it ain't stupid!
            continue

        matched_line_counter = count(1)

        matches = [
            TodoItem(num, line, index=next(matched_line_counter))
            for num, line in enumerate(file_lines, start=1)
            if line.strip(ignore_chars).startswith(command_start)
        ]

        if not any(matches):
            continue

        rel_file_path = os.path.relpath(file_path)

        yield TodosFile(str(rel_file_path), matches, next(files_processed_counter))


def open_at_index(
    index: str, todos_iter: Iterable[TodosFile], editor_command: str = "vim"
):
    """
    Takes an iterable over TodosFile dataclasses, and an index string containing 2 numbers delimited by a non-digit character. Optionally takes the name of a text editor executable in the current PATH (defaults to vim since it's POSIX-guaranteed)

    For example, open_at_index("2.3", iter) opens the second TodosFile in the iterable to the third line matching a todo pattern.

    If the index is valid, the text editor process replaces this script and so nothing is returned. If invalid, raises a KeyError.

    """
    file_index, item_index = (int(s) for s in split(r"\D", index, maxsplit=2))

    for file_todo in dropwhile(lambda x: x.index != file_index, todos_iter):
        logging.debug("%(message)s")
        for todo_item in dropwhile(lambda x: x.index != item_index, file_todo.items):

            line_jump_command = "+" + str(todo_item.line_num)
            logging.debug(f"Opening {file_todo.filename} to item {todo_item.content}")
            logging.debug(f"{editor_command} {line_jump_command} {file_todo.filename}")
            subprocess.call((editor_command, line_jump_command, file_todo.filename))
            sys.exit(0)

    raise KeyError("Could not match '{}' to an indexed location".format(index))


def count_todos(todos_iter: Iterable[TodosFile]):
    """
    Takes an iterable over TodosFile dataclasses
    Returns a list of tuples containing (filename, todos count) for each file,
    and the overall sum, in a tuple.

    """

    items_sums = [(file.filename, len(file.items)) for file in todos_iter]
    total_sum = sum([file_sum for filename, file_sum in items_sums])
    return items_sums, total_sum


def display_todos(todos_iter: Iterable[TodosFile]):
    def print_file_todos(file: TodosFile, file_index_counter=count(1)):
        file_index = next(file_index_counter)
        for item_index, item in enumerate(file.items, start=1):
            print(f"{file_index}.{item_index}\t{item}")

    for todo_file in todos_iter:
        print_file_todos(todo_file)


def main():
    """Parses CLI args, and executes main program logic accordingly."""

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.ERROR
    logging.basicConfig(level=log_level)

    editor: str = "vim"
    if "EDITOR" in os.environ:
        editor = os.environ["EDITOR"]

    start_dir: str = os.getcwd() if not args.dir else args.dir

    count_only: bool = args.count

    search_str: str = args.search if args.search else "TODO"

    recurse = not bool(args.norecurse)
    ignore_hidden = not bool(args.hidden)

    files_iter = file_path_generator(start_dir, recurse, ignore_hidden=ignore_hidden)

    todos_iter = todos_generator(files_iter, command_start=search_str)

    if count_only:
        items_sums, total_sum = count_todos(todos_iter)

        map(lambda x: print(f"{x[0]} items in file {x[1]}"), items_sums)

        print("\n {} total todo items in {} files".format(total_sum, len(items_sums)))
        sys.exit()

    if args.goto != "":

        goto_index:str =  "1.1" if args.goto == "FIRST" else args.goto

        open_at_index(goto_index, todos_iter, editor_command=editor)

    display_todos(todos_iter)


if __name__ == "__main__":
    main()
