import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import json
import os
import threading

def is_mostly_uppercase(text, threshold=0.60):
    """
    Checks if a string is composed of a certain percentage of uppercase letters.
    Ignores non-alphabetic characters.
    """
    if not isinstance(text, str) or not text.strip():
        return False
    
    alpha_chars = [char for char in text if char.isalpha()]
    if not alpha_chars:
        return False
        
    upper_chars = [char for char in alpha_chars if char.isupper()]
    
    return len(upper_chars) / len(alpha_chars) >= threshold

def to_sentence_case(text):
    """
    Converts a string to sentence case, capitalizing words with an 's suffix.
    This is a special rule to handle possessives and contractions correctly.
    """
    if not isinstance(text, str) or not text.strip():
        return text

    # Strip leading/trailing whitespace
    s = text.strip()
    
    # Split the text into words
    words = s.split(' ')
    
    if not words:
        return ""
        
    # Process all words: lowercase them, but capitalize words ending in 's
    processed_words = []
    for word in words:
        # Remove trailing punctuation to check the ending accurately
        cleaned_word = word.upper().rstrip('.,!?')
        if cleaned_word.endswith("'S"):
            # Use capitalize() on the original word with punctuation
            # e.g., "BOB'S," -> "Bob's,"
            processed_words.append(word.capitalize())
        else:
            # Otherwise, just lowercase the word
            # e.g., "CAR" -> "car"
            processed_words.append(word.lower())
            
    # Join the words back into a string
    result = " ".join(processed_words)
    
    # Finally, ensure the very first letter of the entire sentence is capitalized
    if result:
        result = result[0].upper() + result[1:]
        
    return result

def process_json_data(data):
    """
    Recursively traverses a JSON object (or list) and converts mostly
    uppercase string values to sentence case, ONLY if the key is 'text'.
    """
    modified = False
    if isinstance(data, dict):
        for key, value in data.items():
            # Check if the current key is 'text' and its value is a string
            if key == 'text' and isinstance(value, str):
                if is_mostly_uppercase(value):
                    data[key] = to_sentence_case(value)
                    modified = True
            # If the value is another dict or a list, recurse into it
            elif isinstance(value, (dict, list)):
                if process_json_data(value):
                    modified = True
    elif isinstance(data, list):
        # If the data is a list, iterate over its items
        for item in data:
            # If an item in the list is a dict or another list, recurse
            if isinstance(item, (dict, list)):
                if process_json_data(item):
                    modified = True
    return modified

class JsonFixerApp:
    """A GUI application to fix JSON files in a directory."""
    def __init__(self, root):
        self.root = root
        self.root.title("JSON Uppercase Fixer")
        self.root.geometry("600x450")
        self.root.configure(bg="#f0f0f0")

        # --- UI Elements ---
        self.main_frame = tk.Frame(root, padx=15, pady=15, bg="#f0f0f0")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Directory Selection
        self.dir_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.dir_label = tk.Label(self.dir_frame, text="No directory selected.", bg="#ffffff", anchor="w", padx=10, relief="groove", borderwidth=2)
        self.dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        
        self.browse_button = tk.Button(self.dir_frame, text="Browse...", command=self.browse_directory, bg="#007bff", fg="white", relief="flat", padx=10)
        self.browse_button.pack(side=tk.RIGHT, padx=(10, 0))

        # Start Button
        self.start_button = tk.Button(self.main_frame, text="Start Fixing JSON Files", command=self.start_processing_thread, state=tk.DISABLED, bg="#28a745", fg="white", relief="flat", pady=10)
        self.start_button.pack(fill=tk.X, pady=10)

        # Log Area
        self.log_area = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, state=tk.DISABLED, bg="#ffffff", relief="groove", borderwidth=2)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        self.directory_path = ""

    def browse_directory(self):
        """Opens a dialog to select a directory."""
        path = filedialog.askdirectory()
        if path:
            self.directory_path = path
            self.dir_label.config(text=path)
            self.start_button.config(state=tk.NORMAL)
            self.log("Directory selected: " + path)

    def log(self, message):
        """Adds a message to the log area."""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.config(state=tk.DISABLED)
        self.log_area.see(tk.END)

    def start_processing_thread(self):
        """Starts the file processing in a separate thread to keep the GUI responsive."""
        if not self.directory_path:
            messagebox.showerror("Error", "Please select a directory first.")
            return
        
        self.start_button.config(state=tk.DISABLED)
        self.browse_button.config(state=tk.DISABLED)
        self.log("\n--- Starting Scan ---")
        
        # Run the potentially long-running task in a new thread
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()

    def process_files(self):
        """Walks through the directory and processes each JSON file."""
        files_processed = 0
        files_modified = 0
        
        for root_dir, _, files in os.walk(self.directory_path):
            for filename in files:
                if filename.endswith(".json"):
                    file_path = os.path.join(root_dir, filename)
                    self.log(f"Scanning: {filename}")
                    files_processed += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        if process_json_data(data):
                            self.log(f"  -> MODIFIED: Found and fixed uppercase text.")
                            files_modified += 1
                            with open(file_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)
                        else:
                            self.log(f"  -> OK: No changes needed.")

                    except json.JSONDecodeError:
                        self.log(f"  -> ERROR: Could not decode JSON from {filename}.")
                    except Exception as e:
                        self.log(f"  -> ERROR: An unexpected error occurred with {filename}: {e}")

        # Update GUI from the main thread after processing is done
        self.root.after(0, self.on_processing_complete, files_processed, files_modified)

    def on_processing_complete(self, processed_count, modified_count):
        """Updates the GUI after the background thread is finished."""
        self.log("\n--- Scan Complete ---")
        self.log(f"Total files scanned: {processed_count}")
        self.log(f"Total files modified: {modified_count}")
        
        messagebox.showinfo("Success", f"Finished processing!\n\nScanned: {processed_count}\nModified: {modified_count}")
        
        self.start_button.config(state=tk.NORMAL)
        self.browse_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = JsonFixerApp(root)
    root.mainloop()
