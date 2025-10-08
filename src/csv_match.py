#!/usr/bin/env python3

"""
CSV Match Script
Compares two CSV files with potentially different headers by matching on specified columns
Exports either matching rows or non-matching rows
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path

from shared.file_selector import select_multiple_files

# Constants
MATCH_SEPARATOR = "§§§"
ENCODINGS = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]


def get_csv_files(directory="."):
    """Find all CSV files in the specified directory."""
    csv_files = []
    for file in Path(directory).glob("*.csv"):
        if file.is_file():
            csv_files.append(str(file))
    return sorted(csv_files)


def get_csv_columns(filename):
    """Get column names from CSV file with encoding detection."""
    for encoding in ENCODINGS:
        try:
            with open(filename, "r", encoding=encoding) as f:
                reader = csv.reader(f)
                headers = next(reader)
                return headers, encoding
        except UnicodeDecodeError:
            if encoding == ENCODINGS[-1]:
                print("❌ Could not decode the file with any of the attempted encodings.")
                sys.exit(1)
            continue
    return None, None


def display_columns(filename):
    """Display columns with numbers for user selection."""
    headers, _ = get_csv_columns(filename)
    if headers:
        for i, header in enumerate(headers):
            print(f"{i + 1:2d}) {header.strip()}")


def longest_common_substring(s1, s2):
    """Find longest common substring for output naming."""
    # Remove file extensions for comparison
    s1 = s1.replace(".csv", "")
    s2 = s2.replace(".csv", "")

    max_len = 0
    result = ""

    for i in range(len(s1)):
        for j in range(i + 1, len(s1) + 1):
            substr = s1[i:j]
            if substr in s2 and len(substr) > max_len:
                max_len = len(substr)
                result = substr

    # Clean up the result - remove trailing numbers, underscores, hyphens
    result = re.sub(r"[_\-\s]*[0-9]+[_\-\s]*$", "", result)
    result = result.strip("_- ")

    if result and len(result) >= 3:  # Only use if meaningful length
        return result
    else:
        # Fallback to first part of first filename
        first_part = s1.split("_")[0].split("-")[0].split(" ")[0]
        return first_part if first_part else "match"


def parse_column_indices(indices_str):
    """Parse comma-separated column indices and convert to 0-based list."""
    indices = []
    for idx in indices_str.split(","):
        idx = idx.strip()
        if idx.isdigit():
            indices.append(int(idx) - 1)  # Convert to 0-based
    return indices


def create_match_key(row_values, col_indices):
    """Create composite match key from row values and column indices."""
    match_components = []
    for col_idx in col_indices:
        if col_idx < len(row_values):
            match_components.append(row_values[col_idx].strip())
        else:
            match_components.append("")
    return MATCH_SEPARATOR.join(match_components)


def get_user_choice(prompt, options, input_message):
    """Get validated user choice from a numbered menu."""
    print(prompt)
    for i, option in enumerate(options, 1):
        print(f"  {i}) {option}")
    print()

    while True:
        choice = input(input_message).strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return int(choice)
        else:
            print(f"❌ Invalid choice. Please enter a number between 1 and {len(options)}.")


def read_csv_with_multi_columns(filename, match_col_indices):
    """Read CSV and create composite keys from multiple columns."""
    for encoding in ENCODINGS:
        data = []
        match_values = set()
        try:
            with open(filename, "r", encoding=encoding, newline="") as f:
                reader = csv.reader(f)
                headers = next(reader)

                for row_num, row in enumerate(reader):
                    # Pad row if it has fewer columns than headers
                    while len(row) < len(headers):
                        row.append("")

                    # Build row dict preserving header order
                    row_dict = {}
                    for i, header in enumerate(headers):
                        row_dict[header.strip()] = row[i] if i < len(row) else ""
                    data.append(row_dict)

                    # Composite match key
                    match_key = create_match_key(row, match_col_indices)
                    if match_key.replace(MATCH_SEPARATOR, ""):  # Check if any components exist
                        match_values.add(match_key)

                return data, headers, match_values
        except UnicodeDecodeError:
            if encoding == ENCODINGS[-1]:
                print(f"❌ Could not decode {filename} with any of the attempted encodings.")
                sys.exit(1)
            continue


def write_csv_from_dict_list(filename, data, fieldnames):
    """Write CSV from list of dictionaries."""
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def get_column_names(headers, indices):
    """Get column names for given indices."""
    names = []
    for idx in indices:
        if idx < len(headers):
            names.append(headers[idx].strip())
        else:
            names.append(f"Column_{idx + 1}")
    return names


def validate_column_selection(selection, max_cols):
    """Validate column selection input."""
    # Check if selection contains only numbers, commas, and spaces
    if not re.match(r"^[0-9,\s]+$", selection):
        return False

    # Parse and validate each column number
    cols = [col.strip() for col in selection.split(",")]
    for col in cols:
        if not col.isdigit() or int(col) < 1 or int(col) > max_cols:
            return False
    return True


def get_column_selection(file_path, file_num):
    """Get column selection from user for a specific file."""
    headers, _ = get_csv_columns(file_path)
    num_cols = len(headers)

    print(f"Select column(s) from File {file_num} to match on:")
    print("  • For single column: enter column number (e.g.: 3)")
    print("  • For multiple columns: enter comma-separated numbers (e.g.: 1,3,5)")
    print("  • Column order matters: matching will preserve the order you specify")
    print()

    while True:
        col_choice = input(f"Column selection for File {file_num} (1-{num_cols}): ").strip()
        if validate_column_selection(col_choice, num_cols):
            return col_choice.replace(" ", "")
        else:
            print(f"❌ Invalid selection. Please enter valid column numbers between 1 and {num_cols}.")
            print("   Examples: '3' for single column, '1,3,5' for multiple columns")


def filter_rows_by_match(export_data, export_match_indices, reference_match_values, include_matches):
    """Filter rows based on whether they match reference values."""
    filtered_rows = []

    for row in export_data:
        row_values = list(row.values())
        match_key = create_match_key(row_values, export_match_indices)

        # Include row if it matches criteria
        is_match = match_key and match_key in reference_match_values
        if is_match == include_matches:
            filtered_rows.append(row)

    return filtered_rows


def display_match_summary(
    file1_match_values, file2_match_values, export_data, matching_count, non_matching_count, output_type
):
    """Display summary of matching results."""
    print("📊 SUMMARY:")
    print(f"  Total rows in export file: {len(export_data)}")
    print(f"  Unique match keys in File 1: {len(file1_match_values)}")
    print(f"  Unique match keys in File 2: {len(file2_match_values)}")
    print(f"  Rows with matches: {matching_count}")
    print(f"  Rows without matches: {non_matching_count}")
    if output_type == "matching":
        print(f"  → Will export {matching_count} matching rows")
    else:
        print(f"  → Will export {non_matching_count} non-matching rows")
    print()


def write_output_file(filtered_rows, export_file_name, output_type):
    """Write filtered rows to output file."""
    if not filtered_rows:
        if output_type == "matching":
            print(f"No matching rows found in {export_file_name}.")
        else:
            print(f"All rows in {export_file_name} have matches in the other file.")
        sys.exit(0)

    # Create filename with source file basename
    source_basename = export_file_name.replace(".csv", "").replace("./", "")
    suffix = "matching_rows" if output_type == "matching" else "non_matching_rows"
    output_file = f"{source_basename}_{suffix}.csv"

    # Get headers from first row (stripped)
    headers = [key for key in filtered_rows[0].keys()]
    write_csv_from_dict_list(output_file, filtered_rows, headers)

    print(f"✓ Created {output_file} with {len(filtered_rows)} {suffix.replace('_', ' ')} from {export_file_name}")


def match_csv_files(
    file1,
    file2,
    col1_indices,
    col2_indices,
    output_type,
    export_from,
    base_name,
    show_summary,
):
    """Match CSV files based on specified columns."""
    # Parse column indices
    col1_indices = parse_column_indices(col1_indices)
    col2_indices = parse_column_indices(col2_indices)

    # Read both files
    file1_data, file1_headers, file1_match_values = read_csv_with_multi_columns(file1, col1_indices)
    file2_data, file2_headers, file2_match_values = read_csv_with_multi_columns(file2, col2_indices)

    # Get column names for reference
    col1_names = get_column_names(file1_headers, col1_indices)
    col2_names = get_column_names(file2_headers, col2_indices)

    # Display matching information
    print("Matching on:")
    col1_display = col1_names[0] if len(col1_indices) == 1 else f"{' + '.join(col1_names)} (combined in order)"
    col2_display = col2_names[0] if len(col2_indices) == 1 else f"{' + '.join(col2_names)} (combined in order)"
    print(f"  File 1 column{'s' if len(col1_indices) > 1 else ''}: {col1_display}")
    print(f"  File 2 column{'s' if len(col2_indices) > 1 else ''}: {col2_display}")
    print(f"  Exporting from: {'File 1' if export_from == 'file1' else 'File 2'}")
    print("  Column order: Preserved as specified (important for multi-column matching)")
    print()

    # Determine which file's data to export
    export_data = file1_data if export_from == "file1" else file2_data
    export_match_indices = col1_indices if export_from == "file1" else col2_indices
    reference_match_values = file2_match_values if export_from == "file1" else file1_match_values
    export_file_name = file1 if export_from == "file1" else file2

    # Calculate matching and non-matching counts
    matching_count = sum(
        1 for row in export_data if create_match_key(list(row.values()), export_match_indices) in reference_match_values
    )
    non_matching_count = len(export_data) - matching_count

    # Show summary if requested or in summary_only mode
    if show_summary in ["true", "summary_only"]:
        display_match_summary(
            file1_match_values, file2_match_values, export_data, matching_count, non_matching_count, output_type
        )

    # Exit early if this is summary_only mode
    if show_summary == "summary_only":
        return

    # Filter and write results
    include_matches = output_type == "matching"
    filtered_rows = filter_rows_by_match(export_data, export_match_indices, reference_match_values, include_matches)
    write_output_file(filtered_rows, export_file_name, output_type)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="CSV Match Script - Compare two CSV files by matching on specified columns"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="CSV files to process (if not provided, will scan current directory)",
    )

    parser.parse_args()  # Parse arguments but we don't use them in interactive mode

    print("🔍 Scanning for CSV files in current directory...")

    # Find all CSV files
    all_csv_files = get_csv_files()

    if len(all_csv_files) == 0:
        print("❌ No CSV files found in current directory.")
        sys.exit(1)

    if len(all_csv_files) == 1:
        print("❌ Only one CSV file found. Need at least 2 files for comparison.")
        sys.exit(1)

    # Let user select files
    selected_files = select_multiple_files("CSV File Selection", 2, 2, "*.csv", ".", False)
    if not selected_files:
        sys.exit(1)

    file1 = selected_files[0]
    file2 = selected_files[1]

    print(f"📁 Selected {len(selected_files)} files:")
    for file in selected_files:
        print(f"   {Path(file).name}")
    print()

    # Check if files are readable
    if not os.access(file1, os.R_OK):
        print(f"❌ Cannot read {Path(file1).name}")
        sys.exit(1)

    if not os.access(file2, os.R_OK):
        print(f"❌ Cannot read {Path(file2).name}")
        sys.exit(1)

    # Show headers
    print("📋 File headers:")
    print()
    print(f"File 1: {Path(file1).name}")
    display_columns(file1)
    print()
    print(f"File 2: {Path(file2).name}")
    display_columns(file2)
    print()

    # Get column selections
    col1_choice = get_column_selection(file1, 1)
    print()
    col2_choice = get_column_selection(file2, 2)
    print()

    # Prompt for which file to export from
    export_choice = get_user_choice(
        "Choose which file to export rows from:",
        [f"Export from File 1: {Path(file1).name}", f"Export from File 2: {Path(file2).name}"],
        "Enter your choice (1-2): ",
    )
    export_from = "file1" if export_choice == 1 else "file2"
    print()

    # Prompt for output type
    output_choice = get_user_choice(
        "Choose output type:",
        [
            "Export matching rows (rows that have matches in the other file)",
            "Export non-matching rows (rows that do NOT have matches in the other file)",
        ],
        "Enter your choice (1-2): ",
    )
    output_type = "matching" if output_choice == 1 else "non_matching"

    print()

    # Generate base name for output file
    base_name = longest_common_substring(file1, file2)

    print("📝 Processing files...")
    print(f"   Export from: {Path(file1).name if export_from == 'file1' else Path(file2).name}")
    print(f"   Output type: {output_type}")
    print()

    # Show summary first
    print("Analyzing files for matching preview...")
    match_csv_files(
        file1,
        file2,
        col1_choice,
        col2_choice,
        output_type,
        export_from,
        base_name,
        "summary_only",
    )

    print()
    proceed_choice = input("Do you want to proceed with the export? (y/n): ").strip().lower()
    while proceed_choice not in ["y", "yes", "n", "no"]:
        print("❌ Invalid choice. Please enter 'y' for yes or 'n' for no.")
        proceed_choice = input("Do you want to proceed with the export? (y/n): ").strip().lower()

    if proceed_choice in ["n", "no"]:
        print("Export cancelled.")
        sys.exit(0)

    print()
    print("📝 Exporting matching results...")
    match_csv_files(
        file1,
        file2,
        col1_choice,
        col2_choice,
        output_type,
        export_from,
        base_name,
        "export_only",
    )
    print("🎉 Matching completed successfully!")


if __name__ == "__main__":
    main()
