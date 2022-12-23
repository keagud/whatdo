import re, os, argparse
from dataclasses import dataclass
from itertools import count

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


@dataclass
class TodoItem:
    """Represents a single todo item"""

    line_num: int
    content: str
    index: int = 0


@dataclass
class TodosFile:
    """Represents todos within a single file"""

    filename: str
    items: list[TodoItem]
    index: int = 0


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


def todos_from_file(
    file_path: os.PathLike,
    patterns: list[str | re.Pattern] = [r"^\W*\s*TODO"],
):

    try:
        with open(file_path, "r", encoding='utf-8') as infile:
            file_lines = infile.readlines()
    except UnicodeDecodeError:
        # kind of a hacky way to ensure binary files are skipped
        # but if it's stupid and it works it ain't stupid!
        return None

    counter = count(1)

    # convert any lines matching a pattern to a TodoItem dataclass
    matches = [
        TodoItem(num, line, index=next(counter))
        for num, line in enumerate(file_lines, start=1)
        if match_any(patterns, line)
    ]

    if not any(matches):
        return None

    file_todos = TodosFile(str(file_path), matches)

    return file_todos


def todos_generator(
    root_path: os.PathLike | str = "",
    recurse: bool = True,
    ignore_hidden: bool = True,
    patterns: list[str | re.Pattern] = [r"^\W*\s*TODO"],
):

    files = file_path_generator(
        root_path=root_path, recurse=recurse, ignore_hidden=ignore_hidden
    )

    counter = count(1)

    for file_path in files:
        if (file_todos := todos_from_file(file_path, patterns=patterns)) is None:
            continue

        file_todos.index = next(counter)
        yield file_todos

    return



def main():

    tgen = todos_generator(root_path='..')

    for f in tgen:
        print(str(f))
        print("")

    editor: str = "vim"
    if "EDITOR" in os.environ:
        editor = os.environ["EDITOR"]

main()
