import os
import shutil
import sys
from datetime import datetime


def print_feedback(message, level="info"):
    """
    Provides formatted feedback to the user.
    Levels: 'info' (blue), 'success' (green), 'error' (red), 'warning' (yellow).
    """
    colors = {
        "info": "\033[94m",  # Blue
        "success": "\033[92m",  # Green
        "error": "\033[91m",  # Red
        "warning": "\033[93m",  # Yellow
        "endc": "\033[0m",  # End color
    }
    # On Windows, color codes don't work by default in cmd.exe
    if sys.platform == "win32":
        os.system('color')  # Enables color support on Windows
    color = colors.get(level, colors["info"])
    print(f"{color}[*] {message}{colors['endc']}")


def get_human_readable_size(size_bytes):
    """Converts a size in bytes to a human-readable format (KB, MB, GB)."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = min(len(size_name) - 1, int(size_bytes.bit_length() / 10))
    p = 1024 ** i
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def list_directory_contents(path="."):
    """
    Lists the contents of the specified directory with detailed information.
    """
    try:
        abs_path = os.path.abspath(path)
        print_feedback(f"Contents of '{abs_path}'", "info")
        print("-" * 80)
        print(f"{'Type':<10} {'Name':<40} {'Size':<15} {'Modified':<20}")
        print("-" * 80)

        items = os.listdir(path)
        if not items:
            print("Directory is empty.")
        else:
            for item in sorted(items, key=lambda x: x.lower()):
                item_path = os.path.join(path, item)
                try:
                    stat_info = os.stat(item_path)
                    is_dir = os.path.isdir(item_path)

                    item_type = "Folder" if is_dir else "File"
                    item_name = item + "/" if is_dir else item
                    size = get_human_readable_size(stat_info.st_size) if not is_dir else ""
                    mod_time = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

                    print(f"{item_type:<10} {item_name:<40} {size:<15} {mod_time:<20}")
                except (FileNotFoundError, PermissionError):
                    # Item might be a broken link or inaccessible, skip it
                    print_feedback(f"Cannot access: {item_name}", "warning")
                    continue
        print("-" * 80)
    except FileNotFoundError:
        print_feedback(f"Directory not found: {path}", "error")
    except PermissionError:
        print_feedback(f"Permission denied to access: {path}", "error")


def change_directory(new_path):
    """Changes the current working directory."""
    try:
        os.chdir(new_path)
        print_feedback(f"Current directory changed to: {os.getcwd()}", "success")
    except FileNotFoundError:
        print_feedback(f"Directory not found: {new_path}", "error")
    except PermissionError:
        print_feedback(f"Permission denied to access: {new_path}", "error")
    except NotADirectoryError:
        print_feedback(f"Not a directory: {new_path}", "error")


def create_directory(name):
    """Creates a new directory."""
    try:
        os.mkdir(name)
        print_feedback(f"Directory '{name}' created successfully.", "success")
    except FileExistsError:
        print_feedback(f"Directory '{name}' already exists.", "error")
    except PermissionError:
        print_feedback("Permission denied to create directory here.", "error")


def create_file(name):
    """Creates a new empty file. Enforces file extension."""
    # --- CHANGE: Enforce file extension ---
    if not os.path.splitext(name)[1]:
        print_feedback("File creation requires an extension (e.g., 'myfile.txt').", "error")
        return

    try:
        with open(name, 'a'):
            os.utime(name, None)
        print_feedback(f"File '{name}' created successfully.", "success")
    except PermissionError:
        print_feedback("Permission denied to create file here.", "error")


def read_file_contents(name):
    """Reads and displays the content of a text file."""
    try:
        with open(name, 'r', encoding='utf-8', errors='ignore') as f:
            print_feedback(f"Contents of '{name}':", "info")
            print("-" * 80)
            print(f.read())
            print("-" * 80)
    except FileNotFoundError:
        print_feedback(f"File not found: {name}", "error")
    except IsADirectoryError:
        print_feedback(f"'{name}' is a directory, not a file.", "error")
    except PermissionError:
        print_feedback(f"Permission denied to read file: {name}", "error")


def write_to_file(name, content):
    """Writes content to a file, overwriting existing content. Enforces file extension."""
    # --- CHANGE: Enforce file extension ---
    if not os.path.splitext(name)[1]:
        print_feedback("Writing to a file requires an extension (e.g., 'myfile.txt').", "error")
        return

    try:
        with open(name, 'wb') as f:  # Open in binary write mode
            f.write(content.encode('utf-8'))  # Encode string to bytes
        print_feedback(f"Content written to '{name}'.", "success")
    except IsADirectoryError:
        print_feedback(f"Cannot write to a directory: '{name}'.", "error")
    except PermissionError:
        print_feedback(f"Permission denied to write to file: {name}", "error")


def append_to_file(name, content):
    """Appends content to a file. Enforces file extension."""
    # --- CHANGE: Enforce file extension ---
    if not os.path.splitext(name)[1]:
        print_feedback("Appending to a file requires an extension (e.g., 'myfile.txt').", "error")
        return

    try:
        with open(name, 'ab') as f:  # Open in binary append mode
            f.write(content.encode('utf-8'))
        print_feedback(f"Content appended to '{name}'.", "success")
    except FileNotFoundError:
        print_feedback(f"File not found: {name}", "error")
    except IsADirectoryError:
        print_feedback(f"Cannot write to a directory: '{name}'.", "error")
    except PermissionError:
        print_feedback(f"Permission denied to write to file: {name}", "error")


def clear_file(name):
    """Clears all content from a file, making it empty."""
    try:
        open(name, 'w').close()
        print_feedback(f"File '{name}' has been cleared.", "success")
    except FileNotFoundError:
        print_feedback(f"File not found: {name}", "error")
    except IsADirectoryError:
        print_feedback(f"Cannot clear a directory: '{name}'.", "error")
    except PermissionError:
        print_feedback(f"Permission denied to modify file: {name}", "error")


def remove_item(name):
    """Removes a file or an empty directory."""
    try:
        if os.path.isfile(name):
            os.remove(name)
            print_feedback(f"File '{name}' removed successfully.", "success")
        elif os.path.isdir(name):
            if not os.listdir(name):  # Check if directory is empty
                os.rmdir(name)
                print_feedback(f"Empty directory '{name}' removed successfully.", "success")
            else:
                print_feedback(f"Directory '{name}' is not empty. Use 'rmtree' to delete it.", "warning")
        else:
            print_feedback(f"Item not found: {name}", "error")
    except PermissionError:
        print_feedback(f"Permission denied to remove: {name}", "error")


def remove_directory_tree(name):
    """Recursively removes a directory and all its contents. THIS IS DESTRUCTIVE."""
    if not os.path.isdir(name):
        print_feedback(f"'{name}' is not a directory.", "error")
        return

    confirm = input(
        f"\033[91m[!] Are you sure you want to permanently delete '{name}' and all contents? (y/n): \033[0m").lower()
    if confirm == 'y':
        try:
            shutil.rmtree(name)
            print_feedback(f"Directory tree '{name}' removed successfully.", "success")
        except PermissionError:
            print_feedback(f"Permission denied to remove: {name}", "error")
    else:
        print_feedback("Deletion cancelled.", "info")


def copy_item(source, destination):
    """Copies a file or directory."""
    try:
        if os.path.isfile(source):
            shutil.copy2(source, destination)
            print_feedback(f"File '{source}' copied to '{destination}'.", "success")
        elif os.path.isdir(source):
            shutil.copytree(source, destination)
            print_feedback(f"Directory '{source}' copied to '{destination}'.", "success")
        else:
            print_feedback(f"Source item not found: {source}", "error")
    except Exception as e:
        print_feedback(f"An error occurred during copy: {e}", "error")


def move_item(source, destination):
    """Moves/renames a file or directory."""
    try:
        shutil.move(source, destination)
        print_feedback(f"Moved '{source}' to '{destination}'.", "success")
    except Exception as e:
        print_feedback(f"An error occurred during move: {e}", "error")


def print_help():
    """Prints the help menu."""
    print_feedback("Python File Manager Help", "info")
    commands = {
        "ls": "List contents of the current directory.",
        "cd <path>": "Change current directory. Use '..' to go up.",
        "mkdir <name>": "Create a new directory.",
        "touch <name.ext>": "Create a new empty file (extension required).",
        "cat <name.ext>": "Display the contents of a file.",
        "write <file.ext> \"content\"": "Write content to a file, overwriting it (extension required).",
        "append <file.ext> \"content\"": "Append content to a file (extension required).",
        "clear <file.ext>": "Clear all content from a file.",
        "rm <name.ext>": "Remove a file or an EMPTY directory.",
        "rmtree <name>": "DANGEROUS: Recursively delete a directory.",
        "cp <src> <dest>": "Copy a file or directory.",
        "mv <src> <dest>": "Move/Rename a file or directory.",
        "help": "Show this help menu.",
        "exit": "Exit the file manager.",
    }
    for cmd, desc in commands.items():
        print(f"  \033[92m{cmd:<30}\033[0m{desc}")


def main():
    """The main loop of the file manager."""
    print_feedback("Welcome to the Python File Manager. Type 'help' for commands.", "success")

    try:
        os.chdir(os.path.expanduser("~"))
    except Exception:
        pass

    while True:
        current_path = os.getcwd()
        prompt_path = current_path.replace(os.path.expanduser("~"), "~")
        try:
            command_input = input(f"\n\033[1;34m{prompt_path}\033[0m \033[1;32m$ \033[0m").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not command_input:
            continue

        parts = command_input.split()
        command = parts[0].lower()
        args = parts[1:]

        try:
            if command == "exit":
                print_feedback("Goodbye!", "info")
                break
            elif command == "help":
                print_help()
            elif command == "ls":
                list_directory_contents("." if not args else args[0])
            elif command == "cd":
                change_directory(args[0] if args else os.path.expanduser("~"))
            elif command == "mkdir":
                if args:
                    create_directory(args[0])
                else:
                    print_feedback("Usage: mkdir <directory_name>", "warning")
            elif command == "touch":
                if args:
                    create_file(args[0])
                else:
                    print_feedback("Usage: touch <file_name.ext>", "warning")
            elif command == "cat":
                if args:
                    read_file_contents(args[0])
                else:
                    print_feedback("Usage: cat <file_name.ext>", "warning")
            elif command == "write":
                if len(args) >= 2:
                    content_to_write = " ".join(args[1:]).strip('"\'')
                    write_to_file(args[0], content_to_write)
                else:
                    print_feedback("Usage: write <file.ext> \"content to write\"", "warning")
            elif command == "append":
                if len(args) >= 2:
                    content_to_append = " ".join(args[1:]).strip('"\'')
                    append_to_file(args[0], content_to_append)
                else:
                    print_feedback("Usage: append <file.ext> \"content to append\"", "warning")
            elif command == "clear":
                if args:
                    clear_file(args[0])
                else:
                    print_feedback("Usage: clear <file.ext>", "warning")
            elif command == "rm":
                if args:
                    remove_item(args[0])
                else:
                    print_feedback("Usage: rm <item_name>", "warning")
            elif command == "rmtree":
                if args:
                    remove_directory_tree(args[0])
                else:
                    print_feedback("Usage: rmtree <directory_name>", "warning")
            elif command == "cp":
                if len(args) == 2:
                    copy_item(args[0], args[1])
                else:
                    print_feedback("Usage: cp <source> <destination>", "warning")
            elif command == "mv":
                if len(args) == 2:
                    move_item(args[0], args[1])
                else:
                    print_feedback("Usage: mv <source> <destination>", "warning")
            else:
                print_feedback(f"Unknown command: '{command}'. Type 'help'.", "error")

        except Exception as e:
            print_feedback(f"An unexpected error occurred: {e}", "error")


if __name__ == "__main__":
    main()
