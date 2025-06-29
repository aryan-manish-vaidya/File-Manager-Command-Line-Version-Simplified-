import os
import shutil
import sys
from datetime import datetime
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, scrolledtext


class TextEditorWindow(tk.Toplevel):
    """A Toplevel window that serves as a simple text editor."""

    def __init__(self, master, file_path):
        super().__init__(master)
        self.file_path = file_path
        self.title(f"Editor - {os.path.basename(file_path)}")
        self.geometry("700x500")

        self.text_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, undo=True)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Button(button_frame, text="Save", command=self.save_content).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Save & Close", command=self.save_and_close).pack(side=tk.RIGHT)

        self.load_content()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_content(self):
        """Loads the file content into the text area."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.text_area.insert(tk.END, f.read())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {e}", parent=self)
            self.destroy()

    def save_content(self):
        """Saves the text area content back to the file."""
        try:
            content = self.text_area.get(1.0, tk.END)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.master.status_var.set(f"Saved '{os.path.basename(self.file_path)}'")
            # Refresh the tree in the main app to show new size/date
            self.master.populate_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}", parent=self)

    def save_and_close(self):
        self.save_content()
        self.destroy()

    def on_close(self):
        # Check if there are unsaved changes
        try:
            current_content = self.text_area.get(1.0, tk.END)
            with open(self.file_path, 'r', encoding='utf-8') as f:
                saved_content = f.read()

            if current_content.strip() != saved_content.strip():
                if messagebox.askyesno("Unsaved Changes",
                                       "You have unsaved changes. Do you want to save before closing?", parent=self):
                    self.save_content()
        except FileNotFoundError:
            # File might be new or deleted, check if there is content in editor
            if self.text_area.get(1.0, tk.END).strip():
                if messagebox.askyesno("Unsaved Changes",
                                       "You have unsaved changes. Do you want to save before closing?", parent=self):
                    self.save_content()
        except Exception:
            pass  # Ignore other errors on close, just destroy window

        self.destroy()


class FileManagerApp(tk.Tk):
    """The main application class for the GUI File Manager."""

    def __init__(self):
        super().__init__()
        self.title("Python GUI File Manager")
        self.geometry("900x600")

        # --- State Variables ---
        self.current_path = os.path.abspath(os.path.expanduser("~"))
        self.clipboard = {"action": None, "path": None}  # For copy/paste

        # --- UI Setup ---
        self.create_widgets()
        self.populate_tree()

    def create_widgets(self):
        """Creates and arranges all the widgets in the window."""

        # --- Top Frame: Address Bar and Up Button ---
        top_frame = ttk.Frame(self, padding=5)
        top_frame.pack(fill=tk.X)

        self.up_button = ttk.Button(top_frame, text="↑ Up", command=self.go_up)
        self.up_button.pack(side=tk.LEFT, padx=(0, 5))

        self.path_var = tk.StringVar(value=self.current_path)
        self.path_entry = ttk.Entry(top_frame, textvariable=self.path_var, font=("Segoe UI", 10))
        self.path_entry.pack(fill=tk.X, expand=True)
        self.path_entry.bind("<Return>", self.navigate_from_address_bar)

        # --- Main Frame: Treeview ---
        main_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        tree_container = ttk.Frame(main_pane, padding=5)
        main_pane.add(tree_container)

        columns = ("#1", "#2", "#3", "#4")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.heading("#1", text="Name")
        self.tree.heading("#2", text="Date Modified")
        self.tree.heading("#3", text="Type")
        self.tree.heading("#4", text="Size")

        self.tree.column("#1", width=300, stretch=tk.YES)
        self.tree.column("#2", width=150, stretch=tk.YES)
        self.tree.column("#3", width=100, stretch=tk.NO)
        self.tree.column("#4", width=100, stretch=tk.NO, anchor=tk.E)

        scrollbar = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self.on_item_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)

        # --- Status Bar ---
        self.status_var = tk.StringVar(value=f"Current Path: {self.current_path}")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=2)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Context Menu ---
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Open", command=self.open_item, font=("Segoe UI", 9, "bold"))
        self.context_menu.add_command(label="Edit", command=self.edit_item)
        self.context_menu.add_command(label="Rename", command=self.rename_item)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy", command=self.copy_item)
        self.context_menu.add_command(label="Cut", command=self.cut_item)
        self.context_menu.add_command(label="Paste", command=self.paste_item, state=tk.DISABLED)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Clear Content", command=self.clear_content)
        self.context_menu.add_command(label="Delete", command=self.delete_item)

        self.empty_space_menu = tk.Menu(self, tearoff=0)
        self.empty_space_menu.add_command(label="New Folder", command=self.create_folder)
        self.empty_space_menu.add_command(label="New File", command=self.create_file)
        self.empty_space_menu.add_command(label="Paste", command=self.paste_item, state=tk.DISABLED)

    # --- Tree Population and Navigation ---

    def populate_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            items = os.listdir(self.current_path)
            folders = sorted([i for i in items if os.path.isdir(os.path.join(self.current_path, i))], key=str.lower)
            files = sorted([i for i in items if os.path.isfile(os.path.join(self.current_path, i))], key=str.lower)

            for item_name in folders + files:
                self.insert_item(item_name)

            self.path_var.set(self.current_path)
            self.status_var.set(f"Loaded {len(items)} items.")
        except PermissionError:
            messagebox.showerror("Permission Denied", f"Cannot access '{self.current_path}'.")
            self.go_up()
        except FileNotFoundError:
            messagebox.showerror("Not Found", f"The path '{self.current_path}' does not exist.")
            self.current_path = os.path.expanduser("~")
            self.populate_tree()

    def insert_item(self, item_name):
        item_path = os.path.join(self.current_path, item_name)
        try:
            stat_info = os.stat(item_path)
            mod_time = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M')

            if os.path.isdir(item_path):
                self.tree.insert("", "end", values=(item_name, mod_time, "Folder", ""), tags=('folder',))
            else:
                ext = os.path.splitext(item_name)[1].lower()
                item_type = f"{ext.upper()} File" if ext else "File"
                size = self.get_human_readable_size(stat_info.st_size)
                # Tag text files for specific actions
                tag = 'textfile' if ext in ['.txt', '.py', '.json', '.xml', '.html', '.css', '.js', '.md'] else 'file'
                self.tree.insert("", "end", values=(item_name, mod_time, item_type, size), tags=(tag,))
        except (FileNotFoundError, PermissionError):
            pass

    def navigate_to_path(self, path):
        if os.path.isdir(path):
            self.current_path = os.path.abspath(path)
            self.populate_tree()
        else:
            messagebox.showerror("Invalid Path", f"'{path}' is not a directory.")

    def navigate_from_address_bar(self, event=None):
        self.navigate_to_path(self.path_var.get())

    def go_up(self):
        self.navigate_to_path(os.path.dirname(self.current_path))

    # --- Event Handlers ---

    def on_item_double_click(self, event):
        item_id = self.tree.selection()
        if not item_id: return
        self.open_item(item_id=item_id[0])

    def open_item(self, item_path=None, item_id=None):
        if item_path is None:
            if item_id is None:
                selection = self.tree.selection()
                if not selection: return
                item_id = selection[0]
            item_name = self.tree.item(item_id, "values")[0]
            item_path = os.path.join(self.current_path, item_name)

        if os.path.isdir(item_path):
            self.navigate_to_path(item_path)
        else:  # Is a file
            item_tags = self.tree.item(item_id, "tags")
            if 'textfile' in item_tags:
                self.edit_item(item_path)  # Open text files in internal editor
            else:
                self.open_with_default_app(item_path)

    def open_with_default_app(self, item_path):
        """Opens a file with the system's default application."""
        try:
            if sys.platform == "win32":
                os.startfile(item_path)
            elif sys.platform == "darwin":
                os.system(f'open "{item_path}"')
            else:
                os.system(f'xdg-open "{item_path}"')
            self.status_var.set(f"Opened '{os.path.basename(item_path)}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open the file: {e}")

    # --- Context Menu Actions ---

    def show_context_menu(self, event):
        selection_id = self.tree.identify_row(event.y)
        if selection_id:
            self.tree.selection_set(selection_id)
            item_tags = self.tree.item(selection_id, "tags")

            # Disable/enable menu items based on selection type
            if 'folder' in item_tags:
                self.context_menu.entryconfig("Edit", state=tk.DISABLED)
                self.context_menu.entryconfig("Clear Content", state=tk.DISABLED)
            else:
                self.context_menu.entryconfig("Edit", state=tk.NORMAL)
                self.context_menu.entryconfig("Clear Content", state=tk.NORMAL)

            self.context_menu.entryconfig("Paste", state=tk.NORMAL if self.clipboard["path"] else tk.DISABLED)
            self.context_menu.post(event.x_root, event.y_root)
        else:
            self.empty_space_menu.entryconfig("Paste", state=tk.NORMAL if self.clipboard["path"] else tk.DISABLED)
            self.empty_space_menu.post(event.x_root, event.y_root)

    def get_selected_item_path(self):
        selection = self.tree.selection()
        if not selection: return None
        item_name = self.tree.item(selection[0], "values")[0]
        return os.path.join(self.current_path, item_name)

    def edit_item(self, item_path=None):
        if item_path is None:
            item_path = self.get_selected_item_path()
        if not item_path or os.path.isdir(item_path): return

        TextEditorWindow(self, item_path)

    def clear_content(self):
        src_path = self.get_selected_item_path()
        if not src_path or os.path.isdir(src_path): return

        if messagebox.askyesno("Confirm Clear",
                               f"Are you sure you want to clear all content from '{os.path.basename(src_path)}'? This cannot be undone."):
            try:
                open(src_path, 'w').close()
                self.status_var.set(f"Cleared content of '{os.path.basename(src_path)}'.")
                self.populate_tree()  # Refresh to show size change
            except Exception as e:
                messagebox.showerror("Error", f"Could not clear file: {e}")

    def create_folder(self):
        name = simpledialog.askstring("New Folder", "Enter folder name:")
        if name:
            try:
                os.mkdir(os.path.join(self.current_path, name))
                self.status_var.set(f"Folder '{name}' created.")
                self.populate_tree()
            except Exception as e:
                messagebox.showerror("Error", f"Could not create folder: {e}")

    def create_file(self):
        name = simpledialog.askstring("New File", "Enter file name (e.g., file.txt):")
        if name:
            if not os.path.splitext(name)[1]:
                messagebox.showwarning("Invalid Name", "Please provide a file extension.")
                return
            try:
                open(os.path.join(self.current_path, name), 'a').close()
                self.status_var.set(f"File '{name}' created.")
                self.populate_tree()
            except Exception as e:
                messagebox.showerror("Error", f"Could not create file: {e}")

    def rename_item(self):
        src_path = self.get_selected_item_path()
        if not src_path: return

        old_name = os.path.basename(src_path)
        new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=old_name)

        if new_name and new_name != old_name:
            dest_path = os.path.join(self.current_path, new_name)
            try:
                shutil.move(src_path, dest_path)
                self.populate_tree()
            except Exception as e:
                messagebox.showerror("Error", f"Could not rename: {e}")

    def delete_item(self):
        src_path = self.get_selected_item_path()
        if not src_path: return

        item_name = os.path.basename(src_path)
        is_dir = os.path.isdir(src_path)

        confirm_msg = f"Are you sure you want to permanently delete '{item_name}'?"
        if is_dir:
            try:
                if os.listdir(src_path):
                    confirm_msg += "\n\nWARNING: The folder is not empty!"
            except Exception:
                pass

        if messagebox.askyesno("Confirm Deletion", confirm_msg):
            try:
                if is_dir:
                    shutil.rmtree(src_path)
                else:
                    os.remove(src_path)
                self.populate_tree()
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete: {e}")

    def copy_item(self):
        src_path = self.get_selected_item_path()
        if src_path:
            self.clipboard = {"action": "copy", "path": src_path}
            self.status_var.set(f"Copied '{os.path.basename(src_path)}'.")

    def cut_item(self):
        src_path = self.get_selected_item_path()
        if src_path:
            self.clipboard = {"action": "cut", "path": src_path}
            self.status_var.set(f"Cut '{os.path.basename(src_path)}'.")

    def paste_item(self):
        if not self.clipboard["path"]: return

        src_path = self.clipboard["path"]
        action = self.clipboard["action"]
        dest_path = os.path.join(self.current_path, os.path.basename(src_path))

        if src_path == self.current_path or os.path.abspath(src_path) == os.path.abspath(dest_path):
            self.status_var.set("Cannot paste item into itself.")
            return

        try:
            if action == "copy":
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dest_path)
                else:
                    shutil.copy2(src_path, dest_path)
            elif action == "cut":
                shutil.move(src_path, dest_path)
                self.clipboard = {"action": None, "path": None}  # Clear clipboard

            self.populate_tree()
        except FileExistsError:
            if messagebox.askyesno("Confirm Replace", f"'{os.path.basename(dest_path)}' already exists. Replace it?"):
                if os.path.isdir(dest_path):
                    shutil.rmtree(dest_path)
                else:
                    os.remove(dest_path)
                self.paste_item()
        except Exception as e:
            messagebox.showerror("Error", f"Could not paste: {e}")

    # --- Utility Methods ---

    @staticmethod
    def get_human_readable_size(size_bytes):
        if size_bytes == 0: return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = min(len(size_name) - 1, int(size_bytes.bit_length() / 10))
        p = 1024 ** i
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"


if __name__ == "__main__":
    app = FileManagerApp()
    app.mainloop()

