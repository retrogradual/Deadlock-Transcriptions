import subprocess
import json
import difflib
import sys

def get_git_command_output(command):
    """Executes a Git command and returns its output."""
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.stdout
    except FileNotFoundError:
        print("Error: 'git' command not found. Is Git installed and in your PATH?", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        # This error is common if the commit hash doesn't exist or the file isn't in the commit.
        # We return None and let the calling function handle it gracefully.
        return None

def extract_text_from_json(json_data):
    """
    Extracts the display text from the parsed JSON data.

    It first checks for a top-level 'text' field. If not found,
    it concatenates the 'text' fields from the 'segments' array.
    """
    if 'text' in json_data and json_data['text']:
        return json_data['text']
    
    if 'segments' in json_data and isinstance(json_data['segments'], list):
        # Join the text from all segments to form a single string
        segment_texts = [
            segment.get('text', '') for segment in json_data['segments']
            if isinstance(segment, dict)
        ]
        return " ".join(segment_texts).strip()
        
    return ""

def compare_json_files(commit1="HEAD~1", commit2="HEAD"):
    """
    Compares .json files between two commits and prints the diff for the text content.
    """
    print(f"--- Comparing JSON text changes between {commit1} and {commit2} ---\n")
    
    # Get a list of files that were MODIFIED (M) between the two commits.
    # This ignores added (A), deleted (D), etc.
    diff_command = ["git", "diff", "--name-only", "--diff-filter=M", commit1, commit2]
    
    modified_files_output = get_git_command_output(diff_command)
    if modified_files_output is None:
        print(f"Could not get diff between {commit1} and {commit2}. Are they valid commits?", file=sys.stderr)
        return

    # Filter for .json files
    json_files = [
        line for line in modified_files_output.strip().split('\n') 
        if line.endswith('.json') and line
    ]

    if not json_files:
        print("No modified .json files found between the two commits.")
        return

    changed_count = 0
    # Process each modified JSON file
    for file_path in json_files:
        # Get the content of the file from the first commit
        old_content_str = get_git_command_output(["git", "show", f"{commit1}:{file_path}"])
        
        # Get the content of the file from the second commit
        new_content_str = get_git_command_output(["git", "show", f"{commit2}:{file_path}"])

        if old_content_str is None or new_content_str is None:
            # This could happen in complex git histories (e.g., renames)
            print(f"Warning: Could not retrieve content for '{file_path}' from one of the commits. Skipping.")
            continue

        try:
            # Parse the JSON content
            old_json = json.loads(old_content_str)
            new_json = json.loads(new_content_str)
            
            # Extract the relevant text using our logic
            old_text = extract_text_from_json(old_json)
            new_text = extract_text_from_json(new_json)

            # Compare the extracted text and print the changes if it has changed
            if old_text != new_text:
                changed_count += 1
                print(f"Found changes in: {file_path}")
                print("-" * (20 + len(file_path)))
                
                # Print the old and new text on separate lines for clarity
                print(f"OLD: {old_text}")
                print(f"NEW: {new_text}")
                print("\n") # Add a newline for better separation between files

        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON for '{file_path}'. Skipping.", file=sys.stderr)
            continue

    if changed_count == 0:
        print("No changes found in the text content of modified .json files.")


if __name__ == "__main__":
    # You can optionally pass two commit hashes as command-line arguments
    # Example: python your_script_name.py <commit_hash_1> <commit_hash_2>
    commit_args = sys.argv[1:3]
    if len(commit_args) == 2:
        compare_json_files(commit_args[0], commit_args[1])
    else:
        # Default behavior: compare the last commit with the current one
        compare_json_files()
