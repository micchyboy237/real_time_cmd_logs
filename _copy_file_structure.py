import os
import fnmatch
import argparse
import subprocess
import re
from jet.logger import logger

exclude_files = [
    ".git",
    ".gitignore",
    ".DS_Store",
    "_copy*.py",
    "__pycache__",
    ".vscode",
    "node_modules",
    "*lock.json",
    "public",
    "mocks",
    "base-tutorial",
    ".venv",
    "dream",
]
include_files = [
    "README.md",
    # Client
    "client/package.json",
    "client/*.js"
    # Server
    "server/package.json",
    "server/*.js"
]

include_content = []
exclude_content = []

# base_dir should be actual file directory
file_dir = os.path.dirname(os.path.abspath(__file__))
# Change the current working directory to the script's directory
os.chdir(file_dir)


def find_files(base_dir, include, exclude, include_content_patterns, exclude_content_patterns, case_sensitive=False):
    print("Base Dir:", file_dir)
    print("Finding files:", base_dir, include, exclude)
    include_abs = [
        os.path.abspath(pat) if not os.path.isabs(pat) else pat
        for pat in include
        if os.path.exists(os.path.abspath(pat) if not os.path.isabs(pat) else pat)
    ]

    matched_files = set(include_abs)
    for root, dirs, files in os.walk(base_dir):
        adjusted_include = [
            os.path.relpath(os.path.join(base_dir, pat), base_dir) if not any(
                c in pat for c in "*?") else pat
            for pat in include
        ]
        adjusted_exclude = [
            os.path.relpath(os.path.join(base_dir, pat), base_dir) if not any(
                c in pat for c in "*?") else pat
            for pat in exclude
        ]

        if not case_sensitive:
            adjusted_include = [pat.lower() for pat in adjusted_include]
            adjusted_exclude = [pat.lower() for pat in adjusted_exclude]

        dirs[:] = [d for d in dirs if not any(
            fnmatch.fnmatch(d.lower() if not case_sensitive else d, pat)
            for pat in adjusted_exclude
        )]

        for file in files:
            file_path = os.path.relpath(os.path.join(root, file), base_dir)
            normalized_file_path = file_path.lower() if not case_sensitive else file_path

            if any(fnmatch.fnmatch(normalized_file_path, pat) for pat in adjusted_include) and \
               not any(fnmatch.fnmatch(normalized_file_path, pat) for pat in adjusted_exclude):
                if file_path not in matched_files:
                    matched_files.add(file_path)

    return list(matched_files)


def clean_newlines(content):
    """Removes consecutive newlines from the given content."""
    return re.sub(r'\n\s*\n+', '\n', content)


def clean_comments(content):
    """Removes comments from the given content."""
    return re.sub(r'#.*', '', content)


def clean_logging(content):
    """Removes logging statements from the given content, including multi-line ones."""
    logging_pattern = re.compile(
        r'logging\.(?:info|debug|error|warning|critical|exception|log|basicConfig|getLogger|disable|shutdown)\s*\((?:[^)(]+|\((?:[^)(]+|\([^)(]*\))*\))*\)',
        re.DOTALL
    )
    content = re.sub(logging_pattern, '', content)
    content = re.sub(r'\n\s*\n', '\n', content)
    return content


def clean_print(content):
    """Removes print statements from the given content, including multi-line ones."""
    return re.sub(r'print\(.+?\)(,?.*?\))?', '', content, flags=re.DOTALL)


def clean_content(content: str, file_path: str, shorten_funcs: bool = True):
    """Clean the content based on file type and apply various cleaning operations."""
    if not file_path.endswith(".md"):
        content = clean_comments(content)
    content = clean_logging(content)
    # content = clean_print(content)
    if shorten_funcs and file_path.endswith(".py"):
        content = shorten_functions(content)
    return content


def remove_parent_paths(path: str) -> str:
    return os.path.join(
        *(part for part in os.path.normpath(path).split(os.sep) if part != ".."))


def shorten_functions(content):
    """Keeps only function and class definitions, including those with return type annotations."""
    pattern = re.compile(
        r'^\s*(class\s+\w+\s*:|(?:async\s+)?def\s+\w+\s*\((?:[^)(]*|\([^)(]*\))*\)\s*(?:->\s*[\w\[\],\s]+)?\s*:)', re.MULTILINE
    )
    matches = pattern.findall(content)
    cleaned_content = "\n".join(matches)
    cleaned_content = re.sub(r'\n+', '\n', cleaned_content)
    return cleaned_content.strip()


def get_file_length(file_path, shorten_funcs):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            content = clean_content(content, file_path, shorten_funcs)
        return len(content)
    except (OSError, IOError):
        return 0


def format_file_structure(base_dir, include_files, exclude_files, include_content, exclude_content, case_sensitive=True, shorten_funcs=True, show_file_length=True):
    files: list[str] = find_files(base_dir, include_files, exclude_files,
                                  include_content, exclude_content, case_sensitive)
    # Create a new set for absolute file paths
    absolute_file_paths = set()

    # Iterate in reverse to avoid index shifting while popping
    for file in files:
        if not file.startswith("/"):
            file = os.path.join(file_dir, file)
        absolute_file_paths.add(os.path.relpath(file))

    files = list(absolute_file_paths)

    dir_structure = {}
    total_char_length = 0

    for file in files:
        # Convert to relative path
        file = os.path.relpath(file)

        dirs = file.split(os.sep)
        current_level = dir_structure

        if file.startswith("/"):
            dirs.pop(0)
        if ".." in dirs:
            dirs = [dir for dir in dirs if dir != ".."]

        for dir_name in dirs[:-1]:
            if dir_name not in current_level:
                current_level[dir_name] = {}
            current_level = current_level[dir_name]

        file_path = os.path.join(base_dir, file)
        file_length = get_file_length(file_path, shorten_funcs)
        total_char_length += file_length

        if show_file_length:
            current_level[f"{dirs[-1]} ({file_length})"] = None
        else:
            current_level[dirs[-1]] = None

    def print_structure(level, indent="", is_base_level=False):
        result = ""
        sorted_keys = sorted(level.items(), key=lambda x: (
            x[1] is not None, x[0].lower()))

        if is_base_level:
            for key, value in sorted_keys:
                if value is None:
                    result += key + "\n"
                else:
                    result += key + "/\n"
                    result += print_structure(value, indent + "    ", False)
        else:
            for key, value in sorted_keys:
                if value is None:
                    result += indent + "├── " + key + "\n"
                else:
                    result += indent + "├── " + key + "/\n"
                    result += print_structure(value, indent + "│   ", False)

        return result

    file_structure = print_structure(dir_structure, is_base_level=True)
    # file_structure = f"Base dir: {file_dir}\n" + \
    #     f"\nFile structure:\n{file_structure}"
    print("\n")
    num_files = len(files)
    logger.log("Number of Files:", num_files, colors=["GRAY", "DEBUG"])
    logger.log("Files Char Count:", total_char_length,
               colors=["GRAY", "SUCCESS"])
    return file_structure.strip()


def main():
    global exclude_files, include_files, include_content, exclude_content

    print("Running _copy_for_prompt.py")
    parser = argparse.ArgumentParser(
        description='Generate clipboard content from specified files.')
    parser.add_argument('-b', '--base-dir', default=file_dir,
                        help='Base directory to search files in (default: current directory)')
    parser.add_argument('-if', '--include-files', nargs='*',
                        default=include_files, help='Patterns of files to include')
    parser.add_argument('-ef', '--exclude-files', nargs='*',
                        default=exclude_files, help='Directories or files to exclude')
    parser.add_argument('-ic', '--include-content', nargs='*',
                        default=include_content, help='Patterns of file content to include')
    parser.add_argument('-ec', '--exclude-content', nargs='*',
                        default=exclude_content, help='Patterns of file content to exclude')
    parser.add_argument('-cs', '--case-sensitive', action='store_true',
                        default=False, help='Make content pattern matching case-sensitive')
    parser.add_argument('-fo', '--filenames-only', action='store_true',
                        help='Only copy the relative filenames, not their contents')
    parser.add_argument('-nl', '--no-length', action='store_true',
                        help='Do not show file character length')

    args = parser.parse_args()
    base_dir = args.base_dir
    include = args.include_files
    exclude = args.exclude_files
    include_content = args.include_content
    exclude_content = args.exclude_content
    case_sensitive = args.case_sensitive
    filenames_only = args.filenames_only
    show_file_length = not args.no_length

    print("\nGenerating file structure...")
    file_structure = format_file_structure(
        base_dir, include, exclude, include_content, exclude_content,
        case_sensitive, shorten_funcs=False, show_file_length=show_file_length)

    print(
        f"\n----- START FILES STRUCTURE -----\n{file_structure}\n----- END FILES STRUCTURE -----\n")

    process = subprocess.Popen(
        'pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
    process.communicate(file_structure.encode('utf-8'))

    print(f"\nFile structure copied to clipboard.")


if __name__ == "__main__":
    main()
