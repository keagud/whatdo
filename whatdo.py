import re, sys, os, argparse, pathlib
from collections import namedtuple
from itertools import chain

parser = argparse.ArgumentParser(add_help=False)


parser.add_argument("--help", action="help", help="show this help message and exit")


parser.add_argument("-d", "--dir", help="Root directory to start searching")
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
    "-l", "--list", action="store_true", help="List and number all found todos"
)

parser.add_argument(
    "-p", "--pattern", type=str, help="Set a custom regex pattern for use in the search"
)

parser.add_argument(
    "-n",
    "--no-recurse",
    action="store_true",
    help="Only search in files directly inside DIR, not subdirectories (default is false)",
)

parser.add_argument(
    "-h",
    "--hidden",
    action="store_true",
    help="Search inside hidden directories and files ",
)


def file_path_generator(
    root_path: os.PathLike | str = "", recurse: bool = True, ignore_hidden: bool = True
):

    # set the root path

    if not root_path:
        root_path = os.getcwd()

    if isinstance(root_path, str):
        root_path = os.fspath(root_path)

    local_dirs: list[os.DirEntry] = []

    dir_contents = os.scandir(root_path)

    fs_object: os.DirEntry
    for fs_object in dir_contents:

        if fs_object.name.startswith(".") and ignore_hidden:
            continue

        if fs_object.is_dir():

            local_dirs.append(fs_object)
            continue

        yield fs_object

    if recurse:
        for local_dir in local_dirs:
            sub_generator = file_path_generator(root_path=local_dir)

            for subitem in sub_generator:
                yield subitem
    return


def match_any(patterns: list[str | re.Pattern], text: str):
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False


def get_file_todos(
    file_path: os.PathLike,
    patterns: list[str | re.Pattern] = [r"^\W*\s*TODO"],
):

    with open(file_path, "r") as infile:
        file_lines = infile.readlines()

    # return a list of tuples
    # first value is the line number of the match, second is the content
    matches = [
        (num, line.strip())
        for num, line in enumerate(file_lines, start=1)
        if match_any(patterns, line)
    ]

    return matches


def main():

    files_generator = file_path_generator(".")
    total_todos = [
        (f.path, file_results)
        for f in files_generator
        if (file_results := get_file_todos(f))
    ]

    editor: str = "vim"
    if "EDITOR" in os.environ:
        editor = os.environ["EDITOR"]

    for file_summary in total_todos:
        file_path, todos_list = file_summary
        print(file_path)

        for todo_item in todos_list:
            line_number, todo_content = todo_item
            print("(line {}) {}".format(line_number, todo_content))

    args = parser.parse_args()


main()
