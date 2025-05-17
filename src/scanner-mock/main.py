import csv
import random
import time
import os
import uuid
import argparse
from io import StringIO
import signal
import sys


# Attempt to import reportlab components.
# reportlab is an external dependency.
# If not installed, the script will fall back to creating .txt files.
try:
    from reportlab.pdfgen import canvas as rl_canvas  # Renamed to avoid conflict
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch

    REPORTLAB_AVAILABLE = True
except ImportError:
    print("Warning: reportlab library not found. Please install it using 'pip install reportlab' for PDF generation.")
    print("The script will fall back to creating .txt files instead of PDFs.")
    REPORTLAB_AVAILABLE = False
    # Define dummy variables if reportlab is not found, to avoid NameErrors later if logic accidentally tries to use them.
    # However, the main logic path will check REPORTLAB_AVAILABLE.
    rl_canvas = None
    letter = None
    inch = None

# The CSV data provided by the user, embedded as a multiline string.
CSV_DATA = """UUID Ending,kind,doc_id_val,doc_id_score,doc_date_sic_val,doc_date_sic_score,doc_date_parsed,doc_subject_val,doc_subject_score
10,INVOICE,DOC123,0.99,2024-01-01,0.9,2024-01-01T10:00:00Z,KFZ Reparatur,0.8
11,INVOICE,DOC124,0.89,2025-03-12,0.7,2025-03-12T00:00:00Z,Ihr Einkauf vielen Dank,0.8
12,INVOICE,DOC125,0.79,2025-03-13,0.6,2025-03-13T00:00:00Z,Ihr Einkauf vielen Dank,0.7
13,INVOICE,DOC126,0.69,2025-03-13,0.5,2025-03-13T00:00:00Z,Ihr Einkauf vielen Dank,0.6
14,INVOICE,DOC127,0.59,2025-02-12,0.5,2025-02-12T00:00:00Z,Ihr Einkauf vielen Dank,0.5
15,INVOICE,DOC128,0.49,2025-01-11,0.4,2025-01-11T00:00:00Z,Ihr Einkauf vielen Dank,0.4
17,INVOICE,DOC129,0.39,2024-12-10,0.3,2024-12-10T00:00:00Z,Ihr Einkauf vielen Dank,0.3
18,INVOICE,DOC130,0.29,2024-11-11,0.2,2024-11-11T00:00:00Z,Ihr Einkauf vielen Dank,0.2
19,INVOICE,DOC131,0.19,2024-10-09,0.1,2024-10-09T00:00:00Z,Ihr Einkauf vielen Dank,0.1
20,STATEMENT,DE92 1234 5678 9123 87,0.99,2025-04-01,0.9,2025-04-01T00:00:00Z,Kontoauszug 3-25,0.7
21,STATEMENT,DE92 1234 5678 9123 87,0.89,2025-03-01,0.9,2025-03-01T00:00:00Z,Kontoauszug 2-25,0.7
22,STATEMENT,DE92 1234 5678 9123 87,0.79,2025-02-01,0.9,2025-02-01T00:00:00Z,Kontoauszug 1-25,0.7
23,STATEMENT,DE92 1234 5678 9123 87,0.69,2025-01-01,0.9,2025-01-01T00:00:00Z,Kontoauszug 12-24,0.7
24,STATEMENT,DE92 1234 5678 9123 87,0.59,2024-12-01,0.9,2024-12-01T00:00:00Z,Kontoauszug 11-24,0.7
25,STATEMENT,DE92 1234 5678 9123 87,0.49,2024-11-01,0.9,2024-11-01T00:00:00Z,Kontoauszug 10-24,0.7
26,STATEMENT,DE92 1234 5678 9123 87,0.39,2024-10-01,0.9,2024-10-01T00:00:00Z,Kontoauszug 09-24,0.7
27,STATEMENT,DE92 1234 5678 9123 87,0.29,2024-09-01,0.9,2024-09-01T00:00:00Z,Kontoauszug 08-24,0.7
28,STATEMENT,DE92 1234 5678 9123 87,0.19,2024-08-01,0.9,2024-08-01T00:00:00Z,Kontoauszug 07-24,0.7
29,STATEMENT,DE92 1234 5678 9123 87,0.09,2024-07-01,0.9,2024-07-01T00:00:00Z,Kontoauszug 06-24,0.7
30,LETTER,K7-22389,0.99,2025-04-21,0.99,2025-04-21T00:00:00Z,Versicherungsfall 4711,0.7
31,LETTER,K7-22389,0.89,2025-04-01,0.89,2025-04-01T00:00:00Z,Versicherungsfall 4711,0.7
32,LETTER,K7-22389,0.79,2025-03-11,0.79,2025-03-11T00:00:00Z,Beitragsanpassung,0.7
33,LETTER,B-2025-SSA-KGA,0.69,2025-01-12,0.69,2025-01-12T00:00:00Z,Kindergeld Bertram,0.7
34,LETTER,Klasse 7b,0.59,2024-12-22,0.59,2024-12-22T00:00:00Z,Einladung zum Elternabend,0.7
35,LETTER,Wandern,0.49,2024-11-10,0.49,2024-11-10T00:00:00Z,Wanderfreunde Bergisch-Gladbach,0.7
36,LETTER,Lotto-DE,0.39,2024-10-01,0.39,2024-10-01T00:00:00Z,Hxx-123-so-aaaayxy,0.2
37,LETTER,,0.29,2024-09-01,0.29,2024-09-01T00:00:00Z,,0.0
38,LETTER,,0.19,2024-08-01,0.19,2024-08-01T00:00:00Z,,0.0
39,LETTER,,0.09,2024-07-01,0.09,2024-07-01T00:00:00Z,,0.0
"""


def load_data():
    """Loads the CSV data from the string into a list of dictionaries."""
    # Use StringIO to treat the string data as a file
    f = StringIO(CSV_DATA)
    reader = csv.DictReader(f)
    data = list(reader)
    return data


def generate_uuid_ending_with(suffix_str):
    """
    Generates a standard UUID v4 string and replaces its ending part
    with the provided suffix.

    Args:
        suffix_str (str): The string to append as the suffix.

    Returns:
        str: A UUID string ending with the suffix.
    """
    base_uuid = str(uuid.uuid4())  # Generates a UUID like 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx' (36 chars)
    suffix = str(suffix_str)  # Ensure suffix is a string

    # Ensure the suffix is not longer than the UUID itself.
    if len(suffix) >= len(base_uuid):
        # If suffix is too long, truncate it or return as is (based on desired behavior)
        # For this case, let's truncate the suffix to fit.
        return suffix[:len(base_uuid)]

        # Calculate how much of the original UUID's prefix to keep.
    prefix_len = len(base_uuid) - len(suffix)

    # Construct the new UUID string.
    new_uuid_str = base_uuid[:prefix_len] + suffix
    return new_uuid_str


def create_output_file(data_row, output_filepath):
    """
    Creates an output file (PDF if reportlab is available, otherwise TXT)
    with the data from the row. Applies corruption to specified fields.

    Args:
        data_row (dict): A dictionary representing a row from the CSV data.
        output_filepath (str): The full path for the output file (e.g., ".../uuid.pdf").
    """
    # Prepare the content, applying corruption where needed
    content_lines = []

    # Get original values and their scores for corruption
    doc_id_val = data_row.get('doc_id_val', '')
    doc_id_score = data_row.get('doc_id_score', '1.0')  # Default to 1.0 if score missing

    doc_date_sic_val = data_row.get('doc_date_sic_val', '')
    doc_date_sic_score = data_row.get('doc_date_sic_score', '1.0')

    doc_subject_val = data_row.get('doc_subject_val', '')
    doc_subject_score = data_row.get('doc_subject_score', '1.0')

    for key, value in data_row.items():
        content_lines.append(f"{key}: {value}")

    # Write to PDF if reportlab is available
    if REPORTLAB_AVAILABLE:
        try:
            # Ensure output_filepath ends with .pdf for PDF generation
            if not output_filepath.lower().endswith(".pdf"):
                output_filepath += ".pdf"

            c = rl_canvas.Canvas(output_filepath, pagesize=A4)
            textobject = c.beginText()
            textobject.setFont("Helvetica", 10)  # Basic font
            # Set text origin (x, y) from bottom-left of the page
            textobject.setTextOrigin(inch, 10.5 * inch)  # Start 1 inch from left, 10.5 inches from bottom

            for line in content_lines:
                textobject.textLine(line)  # Adds a line and moves to the next

            c.drawText(textobject)
            c.save()
            print(f"Created PDF: {output_filepath}")
        except Exception as e:
            print(f"Error creating PDF {output_filepath}: {e}. Falling back to TXT if possible.")
            # Fallback to TXT if PDF creation failed for some reason other than reportlab not being available initially
            create_txt_fallback(content_lines, output_filepath)
    else:
        # Fallback to TXT if reportlab was never available
        create_txt_fallback(content_lines, output_filepath)


def create_txt_fallback(content_lines, pdf_filepath):
    """Helper function to create a .txt file as a fallback."""
    txt_output_filepath = pdf_filepath.lower().replace(".pdf", ".txt")
    try:
        with open(txt_output_filepath, "w", encoding="utf-8") as f:
            f.write("--- TEXT FALLBACK (reportlab not available or PDF creation failed) ---\n")
            for line in content_lines:
                f.write(line + "\n")
        print(f"Created TXT fallback: {txt_output_filepath}")
    except Exception as e_txt:
        print(f"Error creating TXT fallback {txt_output_filepath}: {e_txt}")


def main_loop(output_folder_path, time_p_pdf):
    """Main loop for the mock scanner application."""
    # Ensure the output folder exists, create if not.
    if not os.path.isdir(output_folder_path):
        try:
            os.makedirs(output_folder_path)
            print(f"Created output folder: {output_folder_path}")
        except OSError as e:
            print(f"Error: Could not create output folder '{output_folder_path}'. {e}")
            return  # Exit if folder cannot be created

    document_data_rows = load_data()
    if not document_data_rows:
        print("Error: No data loaded from CSV_DATA. Exiting.")
        return

    print(f"Mock scanner started. Writing files to: {output_folder_path} every {time_p_pdf} seconds.")
    if not REPORTLAB_AVAILABLE:
        print("Reminder: reportlab is not installed, so .txt files will be generated.")

    try:
        while True:
            # Randomly select a row from the loaded data
            selected_row_data = random.choice(document_data_rows)

            # Get the 'UUID Ending' for the filename suffix
            uuid_suffix = selected_row_data.get('UUID Ending')
            if not uuid_suffix:  # Handle cases where 'UUID Ending' might be missing or empty for a row
                print(f"Warning: Row found with missing or empty 'UUID Ending'. Using a generic suffix.")
                uuid_suffix = "unknown_id"

                # Generate the base filename (UUID ending with the suffix)
            base_filename = generate_uuid_ending_with(uuid_suffix)

            # Determine filename based on whether PDF or TXT will be created
            # The create_output_file function will adjust if it's PDF and path doesn't end with .pdf
            # or call create_txt_fallback which changes extension.
            # For consistency, we'll aim for .pdf initially for the path.
            output_filename = f"{base_filename}.pdf"
            full_output_filepath = os.path.join(output_folder_path, output_filename)

            # Create the PDF (or TXT fallback)
            create_output_file(selected_row_data, full_output_filepath)

            # Wait for (time_p_pdf) second before processing the next file
            time.sleep(time_p_pdf)
    except Exception as e:
        print(f"\nAn unexpected error occurred in the main loop: {e}")

# Signal handler function
def graceful_shutdown_handler(signum, frame):
    """Handles SIGINT and SIGTERM for graceful shutdown."""
    signal_name = signal.Signals(signum).name
    print(f"\nCaught signal {signal_name} ({signum}). Shutting down mock scanner gracefully...")
    # Perform any necessary cleanup here if needed in the future
    sys.exit(0) # Exit cleanly

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Mock Scanner: Generates PDF (or TXT) files from CSV data.")
    parser.add_argument("-o", "--outpath",
                        dest="outpath",
                        required=True,
                        type=str,
                        help="The folder where the generated files will be saved.")
    parser.add_argument("-t", "--time",
                        dest="time_p_pdf",
                        required=False,
                        default=1,
                        type=int,
                        help="seconds between two pdf")

    args = parser.parse_args()

    # Register signal handlers for SIGINT (Ctrl+C) and SIGTERM (docker stop)
    signal.signal(signal.SIGINT, graceful_shutdown_handler)
    signal.signal(signal.SIGTERM, graceful_shutdown_handler)

    # Start the main loop with the provided output folder
    main_loop(args.outpath, args.time_p_pdf)
