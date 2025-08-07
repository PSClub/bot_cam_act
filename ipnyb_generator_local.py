import nbformat as nbf
import os
from datetime import datetime

# --- Configuration ---
# The folder where your repository files are located.
# Use "." if the script is in the same folder as the other files.
REPO_PATH = "." 

# The full path to the directory where you want to save the notebook.
OUTPUT_DIR = r"C:\Users\user\OneDrive\Coding_Projects\2507 LincolnInnFieldsTennis"

# List of files from your repository to include in the notebook.
# The order in this list determines the order of the cells in the notebook.
FILES_TO_INCLUDE = [
    "README.md",
    ".github/workflows/book_ca_lif.yaml",
    "requirements.txt",
    "ca_lif_booking_dates.csv",
    "config.py",
    "data_processor.py",
    "browser_actions.py",
    "main.py",
]

def create_notebook():
    """
    Generates a Jupyter Notebook from the repository files.
    """
    # Create a new notebook object
    nb = nbf.v4.new_notebook()
    nb['cells'] = []

    # --- Introductory Markdown Cell ---
    intro_text = """
# Tennis Court Booking Bot - Notebook

This notebook contains the complete code for the `bot_cam_act` repository. 
The cells are ordered logically to allow for inspection and execution.

**Instructions:**
1.  Run the `pip install` cell to install all required packages.
2.  Run the subsequent code cells in order.
3.  The final `main.py` cell has been modified. It now has an `await main()` call at the end, which will start the process.
4.  The browser session from Playwright is returned and assigned to a `browser` variable. You can interact with it after the script runs.
5.  A final, separate cell `await browser.close()` is provided to manually close the browser when you are finished with your debugging.
    """
    nb['cells'].append(nbf.v4.new_markdown_cell(intro_text))

    # --- Process Each File ---
    for file_path in FILES_TO_INCLUDE:
        full_path = os.path.join(REPO_PATH, file_path)
        
        if not os.path.exists(full_path):
            print(f"Warning: File not found at '{full_path}'. Skipping.")
            continue

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # --- Create Cells Based on File Type ---
        if file_path.endswith('.md') or file_path.endswith('.yaml'):
            # Use Markdown cells for documentation and config files
            header = f"### `{file_path}`"
            cell_content = f"{header}\n```\n{content}\n```"
            nb['cells'].append(nbf.v4.new_markdown_cell(cell_content))

        elif file_path.endswith('.txt'):
            # Create a runnable pip install cell for requirements
            header = f"# Install required packages from {file_path}"
            cell_content = f"{header}\n!pip install -r {file_path}"
            nb['cells'].append(nbf.v4.new_code_cell(cell_content))
        
        elif file_path.endswith('.csv'):
            # Create a cell to write the CSV data to a file in the local directory
            # This makes the data available to the other scripts.
            header = f"# Create the data file: {file_path}"
            # Using triple quotes for the f-string to handle file content easily
            cell_content = f'''{header}
file_content = """{content}"""
with open("{file_path}", "w") as f:
    f.write(file_content)
print("'{file_path}' created successfully.")
'''
            nb['cells'].append(nbf.v4.new_code_cell(cell_content))

        elif file_path.endswith('.py'):
            # --- Handle Python Scripts ---
            # Special modifications for main.py for debugging
            if "main.py" in file_path:
                # Remove the original script runner and add a new execution line
                modified_content = content.replace(
                    'if __name__ == "__main__":\n    asyncio.run(main())', ""
                ).strip()
                # Modify the main function to return the browser object
                modified_content = modified_content.replace(
                    'print("Closing browser.")\n            await browser.close()',
                    'print("Browser session retained for debugging.")\n            return browser'
                )

                cell_content = f"# {file_path}\n\n{modified_content}"
                nb['cells'].append(nbf.v4.new_code_cell(cell_content))
                
                # Add the main execution cell
                execution_cell = """
# --- Run the Main Process ---
# This will execute the booking process. The browser object is returned
# and stored so you can interact with it after the run.
browser = await main()
                """
                nb['cells'].append(nbf.v4.new_code_cell(execution_cell))

            else:
                # For other python scripts, just add them as code cells
                cell_content = f"# {file_path}\n\n{content}"
                nb['cells'].append(nbf.v4.new_code_cell(cell_content))
    
    # --- Add Final Cleanup Cell ---
    cleanup_text = """
# --- Cleanup Cell ---
# Run this cell to close the browser session once you're done debugging.
await browser.close()
print("Browser closed.")
    """
    nb['cells'].append(nbf.v4.new_code_cell(cleanup_text))

    # --- Save the Notebook ---
    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Create a versioned filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    notebook_filename = f"booking_bot_v{timestamp}.ipynb"
    output_path = os.path.join(OUTPUT_DIR, notebook_filename)

    with open(output_path, 'w') as f:
        nbf.write(nb, f)

    print(f"\n✅ Successfully created notebook: {output_path}")

if __name__ == "__main__":
    # Ensure necessary package is installed
    try:
        import nbformat
    except ImportError:
        print("nbformat package not found. Please install it by running:")
        print("pip install nbformat")
    else:
        create_notebook()