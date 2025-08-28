import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os

class FindReplaceApp:
    """
    A GUI application for finding and replacing text in files within a directory.
    """
    def __init__(self, root):
        """
        Initializes the application's user interface.
        """
        self.root = root
        self.root.title("Bulk Find and Replace Tool")
        self.root.geometry("1000x700")
        self.root.minsize(800, 500)

        # --- Member variables ---
        self.target_directory = tk.StringVar()
        self.find_text = tk.StringVar()
        self.replace_text = tk.StringVar()
        self.file_extension = tk.StringVar(value=".txt")
        self.preview_data = [] # To store data for actual replacement

        # --- UI Configuration ---
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)
        
        # --- UI Widgets ---
        self._create_widgets()

    def _create_widgets(self):
        """
        Creates and arranges all the UI widgets in the main window.
        """
        # --- Frame for Inputs ---
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        input_frame.columnconfigure(1, weight=1)

        # Directory Selection
        ttk.Label(input_frame, text="Directory:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.target_directory, state="readonly").grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(input_frame, text="Browse...", command=self._select_directory).grid(row=0, column=2, padx=5, pady=5)

        # Find and Replace Text
        ttk.Label(input_frame, text="Find Text:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.find_text).grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

        ttk.Label(input_frame, text="Replace With:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.replace_text).grid(row=2, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # File Extension
        ttk.Label(input_frame, text="File Extension:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.file_extension, width=10).grid(row=3, column=1, sticky="w", padx=5, pady=5)


        # --- Frame for Buttons ---
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.grid(row=1, column=0, sticky="ew", padx=10)
        
        self.preview_button = ttk.Button(button_frame, text="Preview Changes", command=self._preview_changes)
        self.preview_button.pack(side="left", padx=5)
        
        self.replace_button = ttk.Button(button_frame, text="Replace All", state="disabled", command=self._perform_replace)
        self.replace_button.pack(side="left", padx=5)


        # --- Frame for Preview Treeview ---
        preview_frame = ttk.Frame(self.root, padding="10")
        preview_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        columns = ("file", "line", "original", "new")
        self.tree = ttk.Treeview(preview_frame, columns=columns, show="headings")
        
        # Define headings
        self.tree.heading("file", text="File")
        self.tree.heading("line", text="Line No.")
        self.tree.heading("original", text="Original Text")
        self.tree.heading("new", text="New Text")

        # Configure column widths
        self.tree.column("file", width=200, anchor="w")
        self.tree.column("line", width=80, anchor="center")
        self.tree.column("original", width=300, anchor="w")
        self.tree.column("new", width=300, anchor="w")

        self.tree.grid(row=0, column=0, sticky="nsew")

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # --- Status Bar ---
        self.status_label = ttk.Label(self.root, text="Ready", padding="5")
        self.status_label.grid(row=3, column=0, sticky="ew", padx=10)

    def _select_directory(self):
        """
        Opens a dialog to select a directory and updates the entry widget.
        """
        path = filedialog.askdirectory(title="Select a Folder")
        if path:
            self.target_directory.set(path)
            self.status_label.config(text=f"Selected directory: {path}")

    def _preview_changes(self):
        """
        Finds occurrences of the text and displays them in the preview pane.
        """
        # --- Clear previous results ---
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.preview_data.clear()
        self.replace_button.config(state="disabled")

        # --- Input validation ---
        directory = self.target_directory.get()
        find_str = self.find_text.get()
        ext = self.file_extension.get()

        if not directory:
            messagebox.showerror("Error", "Please select a directory.")
            return
        if not find_str:
            messagebox.showerror("Error", "Please enter the text to find.")
            return
        if not ext.startswith('.'):
            ext = '.' + ext
            self.file_extension.set(ext)

        self.status_label.config(text="Searching for files...")
        self.root.update_idletasks() # Force UI update

        # --- Search for files and content ---
        found_count = 0
        try:
            for root_dir, _, files in os.walk(directory):
                for file in files:
                    if file.endswith(ext):
                        file_path = os.path.join(root_dir, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                for line_num, line in enumerate(f, 1):
                                    if find_str in line:
                                        new_line = line.replace(find_str, self.replace_text.get())
                                        
                                        # Store data for replacement and display
                                        self.preview_data.append({
                                            "path": file_path,
                                        })
                                        
                                        # Insert into Treeview
                                        self.tree.insert("", "end", values=(file, line_num, line.strip(), new_line.strip()))
                                        found_count += 1
                        except Exception as e:
                            print(f"Could not read file {file_path}: {e}")
            
            if found_count > 0:
                self.status_label.config(text=f"Preview generated. Found {found_count} occurrences.")
                self.replace_button.config(state="normal") # Enable replace button
            else:
                self.status_label.config(text="No occurrences found.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.status_label.config(text="Error occurred.")

    def _perform_replace(self):
        """
        Performs the actual file replacements based on the previewed data.
        """
        if not self.preview_data:
            messagebox.showwarning("Warning", "Nothing to replace. Please generate a preview first.")
            return

        if not messagebox.askyesno("Confirm Replace", "Are you sure you want to apply these changes to the files? This action cannot be undone."):
            return
            
        self.status_label.config(text="Replacing text...")
        self.root.update_idletasks()

        # Get unique file paths to process
        files_to_change = sorted(list(set(item['path'] for item in self.preview_data)))
        
        find_str = self.find_text.get()
        replace_str = self.replace_text.get()
        files_changed_count = 0

        try:
            for file_path in files_to_change:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Perform replacement on the whole file content
                    new_content = content.replace(find_str, replace_str)
                    
                    if new_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        files_changed_count += 1
                except Exception as e:
                    print(f"Could not process file {file_path}: {e}")

            messagebox.showinfo("Success", f"Replacement complete! {files_changed_count} files were modified.")
            self.status_label.config(text=f"Replacement complete. {files_changed_count} files modified.")
            
            # Clear preview and disable button after successful replacement
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.preview_data.clear()
            self.replace_button.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during replacement: {e}")
            self.status_label.config(text="Error during replacement.")


if __name__ == "__main__":
    root = tk.Tk()
    app = FindReplaceApp(root)
    root.mainloop()
