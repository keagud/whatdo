import re, sys, os, argparse, pathlib
from collections import namedtuple

parser = argparse.ArgumentParser(add_help=False)


parser.add_argument('--help', action='help', help='show this help message and exit')


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
    help="Open a todo item by number. If EDITOR is set to vim or nvim, also open to the specific line",
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

parser.add_argument('-h', '--hidden', action='store_true', help='Search inside hidden directories and files ')
parser.add_argument(
    "--gitignore",
    action="store_true",
    help="Only search in files that do not match a .gitignore pattern. If this is not a git repository, does nothing",
)



def FilePathGenerator(root_path: os.PathLike | str = "", recurse: bool = True, ignore_hidden:bool=True):

    # set the root path

    if not root_path:
        root_path = os.getcwd()

    if isinstance(root_path, str):
        root_path = os.fspath(root_path)

    local_dirs: list[os.DirEntry] = []

    dir_contents = os.scandir(root_path)

    fs_object: os.DirEntry
    for fs_object in dir_contents:

        if fs_object.name.startswith('.') and ignore_hidden:
            continue

        if fs_object.is_dir():
            local_dirs.append(fs_object)
            continue

        yield fs_object

    if recurse:
        for local_dir in local_dirs:
            sub_generator = FilePathGenerator(root_path=local_dir)

            for subitem in sub_generator:
                yield subitem
    return



def main():

    args = parser.parse_args()


if __name__ == "__main__":
    main()
