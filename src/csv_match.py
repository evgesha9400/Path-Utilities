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


def get_csv_files(directory="."):
    """Find all CSV files in the specified directory."""
    csv_files = []
    for file in Path(directory).glob("*.csv"):
        if file.is_file():
            csv_files.append(str(file))
    return sorted(csv_files)


def get_csv_columns(filename):
    """Get column names from CSV file with encoding detection."""
    encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

    for encoding in encodings:
        try:
            with open(filename, "r", encoding=encoding) as f:
                reader = csv.reader(f)
                headers = next(reader)
                return headers, encoding
        except UnicodeDecodeError:
            if encoding == encodings[-1]:
                print(
                    "❌ Could not decode the file with any of the attempted encodings."
                )
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


def read_csv_with_multi_columns(filename, match_col_indices):
    """Read CSV and create composite keys from multiple columns."""
    encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

    for encoding in encodings:
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
                    match_components = []
                    for col_idx in match_col_indices:
                        if col_idx < len(row):
                            match_components.append(row[col_idx].strip())
                        else:
                            match_components.append("")

                    match_key = "§§§".join(match_components)
                    if any(comp for comp in match_components):
                        match_values.add(match_key)

                return data, headers, match_values
        except UnicodeDecodeError:
            if encoding == encodings[-1]:
                print(
                    f"❌ Could not decode {filename} with any of the attempted encodings."
                )
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
    file1_data, file1_headers, file1_match_values = read_csv_with_multi_columns(
        file1, col1_indices
    )
    file2_data, file2_headers, file2_match_values = read_csv_with_multi_columns(
        file2, col2_indices
    )

    # Get column names for reference
    col1_names = get_column_names(file1_headers, col1_indices)
    col2_names = get_column_names(file2_headers, col2_indices)

    print("Matching on:")
    if len(col1_indices) == 1:
        print(f"  File 1 column: {col1_names[0]}")
    else:
        print(f"  File 1 columns: {' + '.join(col1_names)} (combined in order)")

    if len(col2_indices) == 1:
        print(f"  File 2 column: {col2_names[0]}")
    else:
        print(f"  File 2 columns: {' + '.join(col2_names)} (combined in order)")

    print(f"  Exporting from: {'File 1' if export_from == 'file1' else 'File 2'}")
    print(
        "  Column order: Preserved as specified (important for multi-column matching)"
    )
    print()

    # Determine which file's data and headers to use for export
    if export_from == "file1":
        export_data = file1_data
        export_headers = file1_headers
        export_match_indices = col1_indices
        reference_match_values = file2_match_values
        export_file_name = file1
    else:
        export_data = file2_data
        export_headers = file2_headers
        export_match_indices = col2_indices
        reference_match_values = file1_match_values
        export_file_name = file2

    # Calculate matching and non-matching counts
    matching_count = 0
    non_matching_count = 0

    for row in export_data:
        # Create composite match key from export file
        row_values = list(row.values())
        match_components = []
        for col_idx in export_match_indices:
            if col_idx < len(row_values):
                match_components.append(row_values[col_idx].strip())
            else:
                match_components.append("")

        match_key = "§§§".join(match_components)

        # Check if this key exists in reference file
        if match_key and match_key in reference_match_values:
            matching_count += 1
        else:
            non_matching_count += 1

    # Show summary if requested or in summary_only mode
    if show_summary in ["true", "summary_only"]:
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

    # Exit early if this is summary_only mode
    if show_summary == "summary_only":
        return

    if output_type == "matching":
        # Find rows in export file that have matching values in reference file
        matching_rows = []

        for row in export_data:
            # Create composite match key from export file
            row_values = list(row.values())
            match_components = []
            for col_idx in export_match_indices:
                if col_idx < len(row_values):
                    match_components.append(row_values[col_idx].strip())
                else:
                    match_components.append("")

            match_key = "§§§".join(match_components)

            # Check if this key exists in reference file
            if match_key and match_key in reference_match_values:
                matching_rows.append(row)

        if matching_rows:
            # Create filename with source file basename
            source_basename = export_file_name.replace(".csv", "").replace("./", "")
            output_file = f"{source_basename}_matching_rows.csv"
            write_csv_from_dict_list(output_file, matching_rows, export_headers)
            print(
                f"✓ Created {output_file} with {len(matching_rows)} matching rows from {export_file_name}"
            )
        else:
            print(f"No matching rows found in {export_file_name}.")
            sys.exit(0)

    else:  # non_matching
        # Find rows in export file that do NOT have matching values in reference file
        non_matching_rows = []

        for row in export_data:
            # Create composite match key from export file
            row_values = list(row.values())
            match_components = []
            for col_idx in export_match_indices:
                if col_idx < len(row_values):
                    match_components.append(row_values[col_idx].strip())
                else:
                    match_components.append("")

            match_key = "§§§".join(match_components)

            # Check if this key does NOT exist in reference file
            if not match_key or match_key not in reference_match_values:
                non_matching_rows.append(row)

        if non_matching_rows:
            # Create filename with source file basename
            source_basename = export_file_name.replace(".csv", "").replace("./", "")
            output_file = f"{source_basename}_non_matching_rows.csv"
            write_csv_from_dict_list(output_file, non_matching_rows, export_headers)
            print(
                f"✓ Created {output_file} with {len(non_matching_rows)} non-matching rows from {export_file_name}"
            )
        else:
            print(f"All rows in {export_file_name} have matches in the other file.")
            sys.exit(0)


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
    selected_files = select_multiple_files(
        "CSV File Selection", 2, 2, "*.csv", ".", False
    )
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

    # Get column count for file 1
    headers1, _ = get_csv_columns(file1)
    num_cols1 = len(headers1)

    print("Select column(s) from File 1 to match on:")
    print("  • For single column: enter column number (e.g.: 3)")
    print("  • For multiple columns: enter comma-separated numbers (e.g.: 1,3,5)")
    print("  • Column order matters: matching will preserve the order you specify")
    print()

    while True:
        col1_choice = input(f"Column selection for File 1 (1-{num_cols1}): ").strip()
        if validate_column_selection(col1_choice, num_cols1):
            # Remove spaces and store
            col1_choice = col1_choice.replace(" ", "")
            break
        else:
            print(
                f"❌ Invalid selection. Please enter valid column numbers between 1 and {num_cols1}."
            )
            print("   Examples: '3' for single column, '1,3,5' for multiple columns")

    # Get column count for file 2
    headers2, _ = get_csv_columns(file2)
    num_cols2 = len(headers2)

    print()
    print("Select column(s) from File 2 to match on:")
    print("  • For single column: enter column number (e.g.: 2)")
    print("  • For multiple columns: enter comma-separated numbers (e.g.: 2,4,6)")
    print("  • Column order matters: matching will preserve the order you specify")
    print()

    while True:
        col2_choice = input(f"Column selection for File 2 (1-{num_cols2}): ").strip()
        if validate_column_selection(col2_choice, num_cols2):
            # Remove spaces and store
            col2_choice = col2_choice.replace(" ", "")
            break
        else:
            print(
                f"❌ Invalid selection. Please enter valid column numbers between 1 and {num_cols2}."
            )
            print("   Examples: '2' for single column, '2,4,6' for multiple columns")

    print()

    # Prompt for which file to export from
    print("Choose which file to export rows from:")
    print(f"  1) Export from File 1: {Path(file1).name}")
    print(f"  2) Export from File 2: {Path(file2).name}")
    print()

    while True:
        choice = input("Enter your choice (1-2): ").strip()
        if choice == "1":
            export_from = "file1"
            break
        elif choice == "2":
            export_from = "file2"
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

    print()

    # Prompt for output type
    print("Choose output type:")
    print("  1) Export matching rows (rows that have matches in the other file)")
    print(
        "  2) Export non-matching rows (rows that do NOT have matches in the other file)"
    )
    print()

    while True:
        choice = input("Enter your choice (1-2): ").strip()
        if choice == "1":
            output_type = "matching"
            break
        elif choice == "2":
            output_type = "non_matching"
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

    print()

    # Generate base name for output file
    base_name = longest_common_substring(file1, file2)

    print("📝 Processing files...")
    print(
        f"   Export from: {Path(file1).name if export_from == 'file1' else Path(file2).name}"
    )
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
    while True:
        proceed_choice = (
            input("Do you want to proceed with the export? (y/n): ").strip().lower()
        )
        if proceed_choice in ["y", "yes"]:
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
            break
        elif proceed_choice in ["n", "no"]:
            print("Export cancelled.")
            sys.exit(0)
        else:
            print("❌ Invalid choice. Please enter 'y' for yes or 'n' for no.")


if __name__ == "__main__":
    main()
