#!/usr/bin/env python3

"""
CSV Column Merge Script
Merges two columns in CSV files with conflict resolution options
"""

import argparse
import csv
import os
import sys
from pathlib import Path

from shared.file_selector import select_single_file


def list_csv_files():
    """List CSV files in current directory."""
    csv_files = []
    for file in os.listdir("."):
        if file.lower().endswith(".csv"):
            csv_files.append(file)

    csv_files.sort()

    if not csv_files:
        print("No CSV files found in the current directory.")
        sys.exit(1)

    print("CSV files found:")
    for i, file in enumerate(csv_files, 1):
        print(f"{i:2d}) {file}")

    return csv_files


def get_columns(filename):
    """Get column names from CSV file."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            # Detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter

            reader = csv.reader(f, delimiter=delimiter)
            headers = next(reader)

            print("Columns:")
            for i, header in enumerate(headers, 1):
                print(f"{i:2d}) {header.strip()}")

            return headers, delimiter

    except Exception as e:
        print(f"Error reading CSV file: {e}", file=sys.stderr)
        sys.exit(1)


def analyze_conflicts(filename, col1_idx, col2_idx):
    """Analyze conflicts between two columns."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            # Detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter

            reader = csv.reader(f, delimiter=delimiter)
            headers = next(reader)

            conflicts = []
            total_rows = 0

            for row_idx, row in enumerate(reader):
                total_rows += 1

                # Ensure row has enough columns
                while len(row) <= max(col1_idx, col2_idx):
                    row.append("")

                val1 = row[col1_idx].strip() if col1_idx < len(row) else ""
                val2 = row[col2_idx].strip() if col2_idx < len(row) else ""

                # Conflict: both non-empty with different values
                if val1 and val2 and val1 != val2:
                    conflicts.append(row_idx)

            col1_name = headers[col1_idx].strip()
            col2_name = headers[col2_idx].strip()

            print(f'Merging columns: "{col1_name}" and "{col2_name}"')
            print()
            print("Conflict analysis:")
            print(f"Total data rows: {total_rows}")
            print(f"Rows with conflicts: {len(conflicts)}")

            if len(conflicts) == 0:
                print("No conflicts detected - columns can be merged safely")
            else:
                print(
                    f"Found {len(conflicts)} rows where both columns have different non-empty values"
                )

            return conflicts, total_rows, col1_name, col2_name

    except Exception as e:
        print(f"Error analyzing conflicts: {e}", file=sys.stderr)
        sys.exit(1)


def resolve_conflict_interactive(row_idx, val1, val2, col1_name, col2_name):
    """Interactively resolve conflict between two values."""
    print(f"\nConflict in row {row_idx + 2}:")  # +2 because row 1 is header
    print(f'Column "{col1_name}": "{val1}"')
    print(f'Column "{col2_name}": "{val2}"')
    print("1) Use Column 1 value")
    print("2) Use Column 2 value")
    print("3) Enter custom value")

    while True:
        try:
            choice = input("Choose resolution (enter number): ").strip()
            if choice == "1":
                return val1
            elif choice == "2":
                return val2
            elif choice == "3":
                custom_value = input("Enter custom value: ")
                return custom_value
            else:
                print("Please enter 1, 2, or 3")
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            sys.exit(0)


def merge_columns(
    filename, col1_idx, col2_idx, method, new_col_name, output_file, conflict_rows
):
    """Perform the column merge."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            # Detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter

            reader = csv.reader(f, delimiter=delimiter)
            headers = next(reader)
            data = list(reader)

        col1_name = headers[col1_idx].strip()
        col2_name = headers[col2_idx].strip()

        # Create new headers (remove one column, rename the other)
        new_headers = headers.copy()
        # Remove the higher index first to maintain lower index validity
        higher_idx = max(col1_idx, col2_idx)
        lower_idx = min(col1_idx, col2_idx)

        new_headers.pop(higher_idx)
        new_headers[lower_idx] = new_col_name

        # Process data
        new_data = []

        for row_idx, row in enumerate(data):
            new_row = row.copy()

            # Ensure row has enough columns
            while len(new_row) <= max(col1_idx, col2_idx):
                new_row.append("")

            val1 = new_row[col1_idx].strip()
            val2 = new_row[col2_idx].strip()

            # Determine merged value
            if row_idx in conflict_rows and method == "prompt_per_conflict":
                merged_value = resolve_conflict_interactive(
                    row_idx, val1, val2, col1_name, col2_name
                )
            elif val1 and val2 and val1 != val2:  # Conflict
                if method == "col1_precedence":
                    merged_value = val1
                elif method == "col2_precedence":
                    merged_value = val2
                elif method == "prompt_per_conflict":
                    merged_value = resolve_conflict_interactive(
                        row_idx, val1, val2, col1_name, col2_name
                    )
                else:
                    merged_value = val1  # fallback
            elif val1:
                merged_value = val1
            elif val2:
                merged_value = val2
            else:
                merged_value = ""

            # Create new row with merged column
            new_row[lower_idx] = merged_value
            new_row.pop(higher_idx)

            new_data.append(new_row)

        # Save the result
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(new_headers)
            writer.writerows(new_data)

        print(f'Merge completed! New column: "{new_col_name}"')
        print(f"CSV now has {len(new_headers)} columns")

    except Exception as e:
        print(f"Error during merge: {e}", file=sys.stderr)
        sys.exit(1)


def select_csv_file(csv_files):
    """Select a CSV file from the list."""
    print("CSV Column Merge Tool", file=sys.stderr)
    print("==========================", file=sys.stderr)
    print(file=sys.stderr)

    # Display CSV files
    print("CSV files found:", file=sys.stderr)
    for i, file in enumerate(csv_files, 1):
        print(f"{i:2d}) {file}", file=sys.stderr)

    if len(csv_files) == 0:
        print("No CSV files found in the current directory.", file=sys.stderr)
        sys.exit(1)

    # Get user selection
    while True:
        print(file=sys.stderr)
        choice = input("Select a CSV file (enter number): ")

        if choice.isdigit() and 1 <= int(choice) <= len(csv_files):
            selected_file = csv_files[int(choice) - 1]
            print(file=sys.stderr)
            print(f"Selected file: {selected_file}", file=sys.stderr)
            return selected_file
        else:
            print(
                f"Please enter a number between 1 and {len(csv_files)}", file=sys.stderr
            )


def select_columns(headers):
    """Select two columns for merging."""
    if len(headers) < 2:
        print("Error: Need at least 2 columns to merge", file=sys.stderr)
        sys.exit(1)

    # Select first column
    while True:
        print(file=sys.stderr)
        col1_choice = input("Select first column to merge (enter number): ")

        if col1_choice.isdigit() and 1 <= int(col1_choice) <= len(headers):
            col1_idx = int(col1_choice) - 1
            col1_name = headers[col1_idx].strip()
            break
        else:
            print(
                f"Please enter a number between 1 and {len(headers)}", file=sys.stderr
            )

    # Select second column
    while True:
        col2_choice = input("Select second column to merge (enter number): ")

        if col2_choice.isdigit() and 1 <= int(col2_choice) <= len(headers):
            col2_idx = int(col2_choice) - 1
            col2_name = headers[col2_idx].strip()

            if col1_idx == col2_idx:
                print("Please select two different columns", file=sys.stderr)
                continue
            break
        else:
            print(
                f"Please enter a number between 1 and {len(headers)}", file=sys.stderr
            )

    return col1_idx, col2_idx


def select_merge_method(col1_name, col2_name):
    """Select merge method."""
    print(file=sys.stderr)
    print("Merge methods:", file=sys.stderr)
    print(f"1) '{col1_name}' takes precedence over '{col2_name}'", file=sys.stderr)
    print(f"2) '{col2_name}' takes precedence over '{col1_name}'", file=sys.stderr)
    print("3) Prompt at every conflict (choose per conflict)", file=sys.stderr)

    while True:
        print(file=sys.stderr)
        method_choice = input("Select merge method (enter number): ")

        if method_choice == "1":
            return "col1_precedence"
        elif method_choice == "2":
            return "col2_precedence"
        elif method_choice == "3":
            return "prompt_per_conflict"
        else:
            print("Please enter 1, 2, or 3", file=sys.stderr)


def select_column_name(col1_name, col2_name):
    """Select column name."""
    print()
    print("Column naming options:")
    print(f"1) Keep Column 1 name: '{col1_name}'")
    print(f"2) Keep Column 2 name: '{col2_name}'")
    print("3) Enter a custom name")

    while True:
        print()
        name_choice = input("Select naming option (enter number): ")

        if name_choice == "1":
            return col1_name
        elif name_choice == "2":
            return col2_name
        elif name_choice == "3":
            while True:
                custom_name = input("Enter custom column name: ")
                if custom_name:
                    return custom_name
                else:
                    print("Column name cannot be empty")
        else:
            print("Please enter 1, 2, or 3")


def count_data_rows(filename):
    """Count data rows in CSV file."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            return sum(1 for row in reader)
    except Exception:
        return 0


def main():
    """Main script execution."""
    parser = argparse.ArgumentParser(description="CSV Column Merge Tool")
    parser.add_argument(
        "file",
        nargs="?",
        help="CSV file to process (optional - will scan directory if not provided)",
    )
    args = parser.parse_args()

    # Select CSV file
    if args.file:
        selected_file = args.file
        if not os.path.exists(selected_file):
            print(f"Error: File '{selected_file}' not found.", file=sys.stderr)
            sys.exit(1)
        print(f"Using file: {selected_file}", file=sys.stderr)
    else:
        selected_file = select_single_file(
            "Select CSV file to merge columns", "*.csv", ".", True
        )
        if not selected_file:
            sys.exit(1)

    # Load CSV data and get total rows
    headers, delimiter = get_columns(selected_file)
    total_rows = len(headers)
    data_rows = count_data_rows(selected_file)

    print(f"Loaded CSV with {total_rows} columns and {data_rows} rows")

    while True:
        # Select columns to merge
        col1_idx, col2_idx = select_columns(headers)

        print()

        # Analyze conflicts
        conflicts, total_data_rows, col1_name, col2_name = analyze_conflicts(
            selected_file, col1_idx, col2_idx
        )

        # Select merge method
        method = select_merge_method(col1_name, col2_name)

        # Select column name
        new_col_name = select_column_name(col1_name, col2_name)

        # Generate output filename
        base_name = Path(selected_file).stem
        output_file = f"{base_name}_Merged.csv"

        print()

        # Perform merge
        merge_columns(
            selected_file,
            col1_idx,
            col2_idx,
            method,
            new_col_name,
            output_file,
            conflicts,
        )

        # Update selected_file to the merged file for potential next iteration
        selected_file = output_file

        # Get updated headers for next iteration
        headers, delimiter = get_columns(selected_file)

        # Ask if user wants to merge more columns
        print()
        while True:
            continue_choice = input(
                "Do you want to merge two more columns? (y/n): "
            ).lower()
            if continue_choice in ["y", "yes"]:
                # Check if enough columns remain
                remaining_cols = len(headers)
                if remaining_cols < 2:
                    print("Not enough columns left to merge (need at least 2)")
                    continue_choice = "n"
                break
            elif continue_choice in ["n", "no"]:
                break
            else:
                print("Please enter 'y' or 'n'")

        if continue_choice in ["n", "no"]:
            break

        print()
        print(f"Current file: {selected_file}")

    print()
    print(f"Final merged CSV saved as: {output_file}")


if __name__ == "__main__":
    main()
