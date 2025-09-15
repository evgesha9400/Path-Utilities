#!/usr/bin/env python3

"""
CSV Extend Script
Extends one CSV file with selected columns from another CSV file by matching on specified columns
Allows matching on multiple columns and selecting which columns to add
"""

import argparse
import csv
import math
import os
import shutil
import sys
from pathlib import Path

from shared.file_selector import select_multiple_files


def get_terminal_width():
    """Get terminal width, defaulting to 80 if unable to determine."""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80


def find_csv_files(directory="."):
    """Find all CSV files in the specified directory."""
    csv_files = []
    for file in Path(directory).glob("*.csv"):
        if file.is_file():
            csv_files.append(str(file))
    return sorted(csv_files)


def get_csv_headers(filename):
    """Get CSV headers from a file."""
    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        return next(reader)


def get_csv_column_count(filename):
    """Get the number of columns in a CSV file."""
    headers = get_csv_headers(filename)
    return len(headers)


def display_columns(filename):
    """Display column names from CSV in multi-column format."""
    headers = get_csv_headers(filename)
    terminal_width = get_terminal_width()

    # Pre-format all items to calculate proper column width
    formatted_items = []
    max_item_len = 0

    for idx, header in enumerate(headers):
        # Format with index number
        item = f"{idx + 1:2d}) {header.strip()}"
        formatted_items.append(item)
        max_item_len = max(max_item_len, len(item))

    # Add padding to ensure good spacing between columns
    col_width = max_item_len + 4  # Add 4 spaces of padding

    # Calculate how many columns can fit
    cols_per_row = max(1, math.floor(terminal_width / col_width))

    # Format and print in multiple columns with proper alignment
    for i in range(0, len(formatted_items), cols_per_row):
        row_items = []
        for j in range(cols_per_row):
            idx = i + j
            if idx < len(formatted_items):
                # Use the pre-formatted item with proper padding
                row_items.append(formatted_items[idx].ljust(col_width))
        print("".join(row_items))


def parse_column_numbers(input_str, max_cols):
    """Parse comma-separated column numbers and validate them."""
    # Split by comma and clean up
    parts = [part.strip() for part in input_str.split(",")]
    columns = []

    for part in parts:
        try:
            col_num = int(part)
            if 1 <= col_num <= max_cols:
                columns.append(col_num)
            else:
                print(f"ERROR: Column {col_num} is out of range (1-{max_cols})")
                return None
        except ValueError:
            print(f'ERROR: "{part}" is not a valid column number')
            return None

    if not columns:
        print("ERROR: No valid columns specified")
        return None

    # Remove duplicates while preserving order
    seen = set()
    unique_columns = []
    for col in columns:
        if col not in seen:
            seen.add(col)
            unique_columns.append(col)

    return unique_columns


def search_columns(filename, search_term):
    """Search for columns containing the search term."""
    headers = get_csv_headers(filename)
    found = False
    for i, header in enumerate(headers):
        if search_term.lower() in header.lower():
            print(f"{i + 1:2d}) {header.strip()} ✓")
            found = True
    if not found:
        print("No matches found")


def read_csv_to_dict(filename):
    """Read CSV file and return data as list of dictionaries."""
    data = []
    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

        for row_num, row in enumerate(reader):
            # Pad row if it has fewer columns than headers
            while len(row) < len(headers):
                row.append("")

            # Create row dict
            row_dict = {}
            for i, header in enumerate(headers):
                row_dict[header.strip()] = row[i] if i < len(row) else ""

            data.append(row_dict)

    return data, [h.strip() for h in headers]


def create_match_key(row, headers, col_indices):
    """Create a match key from row data using specified column indices."""
    key_parts = []
    for col_idx in col_indices:
        if col_idx < len(headers):
            header = headers[col_idx]
            # Clean value by lowercasing and trimming
            value = row.get(header, "").strip().lower()
            key_parts.append(value)
    return "|||".join(key_parts)  # Use unlikely separator


def check_substring_match(target_key, source_keys, bidirectional=False):
    """Check if target_key matches any source_key using substring logic."""
    target_parts = target_key.split("|||")

    for source_key in source_keys:
        source_parts = source_key.split("|||")

        # Both keys must have same number of parts
        if len(target_parts) != len(source_parts):
            continue

        # Check if each part matches according to substring rules
        match = True
        for t_part, s_part in zip(target_parts, source_parts):
            # Skip empty target parts (don't consider them a match)
            if not t_part.strip():
                match = False
                break

            if bidirectional:
                # Bidirectional: either t_part in s_part OR s_part in t_part
                if (t_part not in s_part) and (s_part not in t_part):
                    match = False
                    break
            else:
                # Unidirectional: t_part must be in s_part
                if t_part not in s_part:
                    match = False
                    break

        if match:
            return source_key

    return None


def preview_csv_extension(
    file1,
    file2,
    match_cols1,
    match_cols2,
    extend_file,
    source_cols,
    match_type,
    bidirectional,
):
    """Preview match statistics before extending."""
    # Parse column specifications
    match_cols1 = [x - 1 for x in match_cols1]  # Convert to 0-based
    match_cols2 = [x - 1 for x in match_cols2]  # Convert to 0-based
    source_cols = [x - 1 for x in source_cols]  # Convert to 0-based

    # Read both files
    file1_data, file1_headers = read_csv_to_dict(file1)
    file2_data, file2_headers = read_csv_to_dict(file2)

    print("📊 PREVIEW - Match Analysis")
    print("═══════════════════════════")

    # Display match type
    if match_type == "exact":
        match_type_display = "Exact Match"
    else:
        if bidirectional:
            match_type_display = (
                "Substring Match - Bidirectional (target ⊆ source OR source ⊆ target)"
            )
        else:
            match_type_display = "Substring Match - Unidirectional (target ⊆ source)"
    print(f"Match Type: {match_type_display}")
    print()

    if extend_file == "file1":
        target_data = file1_data
        target_headers = file1_headers
        source_data = file2_data
        source_headers = file2_headers
        target_match_cols = match_cols1
        source_match_cols = match_cols2
        target_file_name = file1
        source_file_name = file2
        print(f"Target file (to extend): {file1}")
        for col_idx in match_cols1:
            if col_idx < len(file1_headers):
                print(f"  → Matching on: {file1_headers[col_idx]}")
        print(f"Source file: {file2}")
        for col_idx in match_cols2:
            if col_idx < len(file2_headers):
                print(f"  → Matching on: {file2_headers[col_idx]}")
    else:
        target_data = file2_data
        target_headers = file2_headers
        source_data = file1_data
        source_headers = file1_headers
        target_match_cols = match_cols2
        source_match_cols = match_cols1
        target_file_name = file2
        source_file_name = file1
        print(f"Target file (to extend): {file2}")
        for col_idx in match_cols2:
            if col_idx < len(file2_headers):
                print(f"  → Matching on: {file2_headers[col_idx]}")
        print(f"Source file: {file1}")
        for col_idx in match_cols1:
            if col_idx < len(file1_headers):
                print(f"  → Matching on: {file1_headers[col_idx]}")

    print()
    print("Columns to be added:")
    for col_idx in source_cols:
        if col_idx < len(source_headers):
            print(f"  → {source_headers[col_idx]}")
    print()

    # Create lookup dictionary from source file
    source_lookup = {}
    source_keys = []
    for row in source_data:
        match_key = create_match_key(row, source_headers, source_match_cols)
        if match_key.strip("|"):  # Only add if not all empty
            source_lookup[match_key] = row
            source_keys.append(match_key)

    # Analyze matches without creating the extended data
    matches_found = 0
    total_target_rows = len(target_data)
    non_empty_match_cols = 0

    print("Analyzing rows...")

    # Process rows without progress bar
    for row in target_data:
        target_key = create_match_key(row, target_headers, target_match_cols)

        # Count non-empty match columns
        if target_key.strip("|"):
            non_empty_match_cols += 1

        if match_type == "exact":
            # Skip empty keys (where all parts are empty)
            if target_key.strip("|") and target_key in source_lookup:
                matches_found += 1
        else:  # substring matching
            if check_substring_match(target_key, source_keys, bidirectional):
                matches_found += 1

    print(f"Analyzed {total_target_rows} rows.")
    print()

    # Calculate statistics
    match_percentage = (
        (matches_found / total_target_rows * 100) if total_target_rows > 0 else 0
    )
    no_match_count = total_target_rows - matches_found

    print("📈 MATCH STATISTICS")
    print("═══════════════════")
    print(f"Total rows in target file: {total_target_rows:,}")
    print(
        f"Rows with non-empty matching columns: {non_empty_match_cols:,} ({non_empty_match_cols / total_target_rows * 100:.1f}%)"
    )
    print(
        f"Rows with empty matching columns: {total_target_rows - non_empty_match_cols:,} ({(total_target_rows - non_empty_match_cols) / total_target_rows * 100:.1f}%)"
    )
    print(f"Rows with matches: {matches_found:,} ({match_percentage:.1f}%)")
    print(f"Rows without matches: {no_match_count:,} ({100 - match_percentage:.1f}%)")
    print(f"Number of columns to be added: {len(source_cols)}")
    print()

    # Show some examples of what will happen
    print("💡 IMPACT PREVIEW")
    print("═════════════════")
    if matches_found > 0:
        print(f"✓ {matches_found:,} rows will get new data added")
    else:
        print("⚠️  NO MATCHES FOUND - All new columns will be empty!")

    if no_match_count > 0:
        print(f"⚠️  {no_match_count:,} rows will have empty values for new columns")

    print()


def extend_csv_files(
    file1,
    file2,
    match_cols1,
    match_cols2,
    extend_file,
    source_cols,
    match_type,
    bidirectional,
):
    """Extend CSV files based on specified columns."""
    # Parse column specifications
    match_cols1 = [x - 1 for x in match_cols1]  # Convert to 0-based
    match_cols2 = [x - 1 for x in match_cols2]  # Convert to 0-based
    source_cols = [x - 1 for x in source_cols]  # Convert to 0-based

    # Read both files
    file1_data, file1_headers = read_csv_to_dict(file1)
    file2_data, file2_headers = read_csv_to_dict(file2)

    # Determine which file is target and which is source
    if extend_file == "file1":
        target_data = file1_data
        target_headers = file1_headers
        source_data = file2_data
        source_headers = file2_headers
        target_match_cols = match_cols1
        source_match_cols = match_cols2
        target_file_name = file1
        source_file_name = file2
    else:
        target_data = file2_data
        target_headers = file2_headers
        source_data = file1_data
        source_headers = file1_headers
        target_match_cols = match_cols2
        source_match_cols = match_cols1
        target_file_name = file2
        source_file_name = file1

    # Create lookup dictionary from source file
    source_lookup = {}
    source_keys = []
    for row in source_data:
        match_key = create_match_key(row, source_headers, source_match_cols)
        if match_key.strip("|"):  # Only add if not all empty
            source_lookup[match_key] = row
            source_keys.append(match_key)

    # Prepare new headers for extended file
    extended_headers = target_headers.copy()
    new_column_names = []

    for col_idx in source_cols:
        if col_idx < len(source_headers):
            source_col_name = source_headers[col_idx]
            # Check if column name already exists in target
            base_name = source_col_name
            counter = 1
            final_name = base_name
            while final_name in extended_headers:
                final_name = f"{base_name}_{counter}"
                counter += 1
            extended_headers.append(final_name)
            new_column_names.append((source_col_name, final_name))

    # Extend target data
    extended_data = []
    matches_found = 0
    non_empty_match_cols = 0
    total_target_rows = len(target_data)

    print("Processing rows...")

    for row in target_data:
        target_key = create_match_key(row, target_headers, target_match_cols)

        # Count non-empty match columns
        if target_key.strip("|"):
            non_empty_match_cols += 1

        # Create new row with existing data
        new_row = row.copy()

        # Find matching source row based on match type
        matched_source_key = None
        if match_type == "exact":
            # Skip empty keys (where all parts are empty)
            if target_key.strip("|") and target_key in source_lookup:
                matched_source_key = target_key
        else:  # substring matching
            matched_source_key = check_substring_match(
                target_key, source_keys, bidirectional
            )

        # Add new columns
        if matched_source_key:
            source_row = source_lookup[matched_source_key]
            matches_found += 1
            for source_col_name, new_col_name in new_column_names:
                new_row[new_col_name] = source_row.get(source_col_name, "")
        else:
            # No match found, add empty values for new columns
            for source_col_name, new_col_name in new_column_names:
                new_row[new_col_name] = ""

        extended_data.append(new_row)

    print(f"Processed {total_target_rows} rows.")
    print()

    # Generate output filename
    target_basename = target_file_name.replace(".csv", "").replace("./", "")
    output_file = f"{target_basename}_extended.csv"

    # Write extended file
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=extended_headers)
        writer.writeheader()
        writer.writerows(extended_data)

    print(f"✓ Successfully created: {output_file}")
    if len(new_column_names) == 1:
        print(f"  Final result: {len(extended_data):,} rows with 1 new column added")
    else:
        print(
            f"  Final result: {len(extended_data):,} rows with {len(new_column_names)} new columns added"
        )

    # Print matching statistics
    print(
        f"  Rows with non-empty matching columns: {non_empty_match_cols:,} ({non_empty_match_cols / total_target_rows * 100:.1f}%)"
    )
    print(
        f"  Rows with matches found: {matches_found:,} ({matches_found / total_target_rows * 100:.1f}%)"
    )

    # Print each added column
    for _, col_name in new_column_names:
        print(f"  → Added column: {col_name}")


def main():
    """Main function to run the CSV extend script."""
    parser = argparse.ArgumentParser(
        description="Extends one CSV file with selected columns from another CSV file by matching on specified columns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Interactive mode - scan current directory for CSV files
  %(prog)s file1.csv file2.csv # Specify files directly
        """,
    )

    parser.add_argument(
        "files",
        nargs="*",
        help="CSV files to process (if not provided, will scan current directory)",
    )

    args = parser.parse_args()

    # If files are provided, use them directly
    if args.files:
        if len(args.files) < 2:
            print("❌ Need at least 2 CSV files to extend data.")
            sys.exit(1)
        csv_files = args.files[:2]  # Take only first 2 files
    else:
        # Scan for CSV files
        print("🔍 Scanning for CSV files in current directory...")
        csv_files = find_csv_files()

        if len(csv_files) == 0:
            print("❌ No CSV files found in current directory.")
            sys.exit(1)

        if len(csv_files) == 1:
            print("❌ Only one CSV file found. Need at least 2 files to extend data.")
            sys.exit(1)

        # Let user select files
        csv_files = select_multiple_files(
            "CSV File Selection", 2, 2, "*.csv", ".", "interactive", False
        )
        if not csv_files:
            sys.exit(1)

    file1, file2 = csv_files[0], csv_files[1]

    print(f"📁 Selected {len(csv_files)} files:")
    for file in csv_files:
        print(f"   {Path(file).name}")
    print()

    # Check if files are readable
    if not os.access(file1, os.R_OK):
        print(f"❌ Cannot read {file1}")
        sys.exit(1)

    if not os.access(file2, os.R_OK):
        print(f"❌ Cannot read {file2}")
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

    # Get number of columns for each file
    num_cols1 = get_csv_column_count(file1)
    num_cols2 = get_csv_column_count(file2)

    # Choose which file to extend
    print("Choose which file to extend (add columns to):")
    print(f"  1) Extend File 1: {Path(file1).name}")
    print(f"  2) Extend File 2: {Path(file2).name}")
    print()

    while True:
        choice = input("Enter your choice (1-2): ").strip()
        if choice == "1":
            extend_file = "file1"
            target_file = file1
            source_file = file2
            target_num_cols = num_cols1
            source_num_cols = num_cols2
            break
        elif choice == "2":
            extend_file = "file2"
            target_file = file2
            source_file = file1
            target_num_cols = num_cols2
            source_num_cols = num_cols1
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

    print()
    print(f"Target file (to extend): {Path(target_file).name}")
    print(f"Source file (to get columns from): {Path(source_file).name}")
    print()

    # Get matching columns for target file
    print(f"Select matching column(s) from target file ({Path(target_file).name}):")
    display_columns(target_file)
    print()

    print(
        "Enter column number(s) or search by name (e.g., 'search email' to find email columns)"
    )
    while True:
        input_str = input(
            f"Enter column number(s) for matching (comma-separated, 1-{target_num_cols}): "
        ).strip()

        # Check if it's a search request
        if input_str.lower().startswith("search "):
            search_term = input_str[7:].strip().lower()
            print(f"Searching for '{search_term}' in target file columns:")
            search_columns(target_file, search_term)
            print("Enter column number(s) or try another search")
            continue

        # Process as normal column selection
        target_match_cols = parse_column_numbers(input_str, target_num_cols)
        if target_match_cols is not None:
            break

    print()

    # Get matching columns for source file
    print(f"Select matching column(s) from source file ({Path(source_file).name}):")
    display_columns(source_file)
    print()

    print(
        "Enter column number(s) or search by name (e.g., 'search email' to find email columns)"
    )
    while True:
        input_str = input(
            f"Enter column number(s) for matching (comma-separated, 1-{source_num_cols}): "
        ).strip()

        # Check if it's a search request
        if input_str.lower().startswith("search "):
            search_term = input_str[7:].strip().lower()
            print(f"Searching for '{search_term}' in source file columns:")
            search_columns(source_file, search_term)
            print("Enter column number(s) or try another search")
            continue

        # Process as normal column selection
        source_match_cols = parse_column_numbers(input_str, source_num_cols)
        if source_match_cols is not None:
            break

    print()

    # Get columns to add from source file
    print(f"Select column(s) to add from source file ({Path(source_file).name}):")
    print(
        "You can select multiple columns by separating numbers with commas (e.g., 1,3,4)"
    )
    display_columns(source_file)
    print()

    print(
        "Enter column number(s) or search by name (e.g., 'search email' to find email columns)"
    )
    while True:
        input_str = input(
            f"Enter column number(s) to add (comma-separated, 1-{source_num_cols}): "
        ).strip()

        # Check if it's a search request
        if input_str.lower().startswith("search "):
            search_term = input_str[7:].strip().lower()
            print(f"Searching for '{search_term}' in source file columns:")
            search_columns(source_file, search_term)
            print("Enter column number(s) or try another search")
            continue

        # Process as normal column selection
        add_cols = parse_column_numbers(input_str, source_num_cols)
        if add_cols is not None:
            break

    print()

    # Choose match type
    print("Choose matching type:")
    print("  1) Exact match (values must be identical)")
    print(
        "  2) Substring match - unidirectional (target value is contained in source value)"
    )
    print("     Example: 'Apple' matches 'Green Apple Inc'")
    print("  3) Substring match - bidirectional (either is substring of the other)")
    print(
        "     Example: 'Apple' matches 'Green Apple Inc' AND 'Green Apple Inc' matches 'Apple'"
    )
    print()

    while True:
        choice = input("Enter your choice (1-3): ").strip()
        if choice == "1":
            match_type = "exact"
            bidirectional = False
            print("Selected: Exact matching")
            break
        elif choice == "2":
            match_type = "substring"
            bidirectional = False
            print("Selected: Unidirectional substring matching (target ⊆ source)")
            break
        elif choice == "3":
            match_type = "substring"
            bidirectional = True
            print(
                "Selected: Bidirectional substring matching (target ⊆ source OR source ⊆ target)"
            )
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

    print()
    print("📝 Analyzing match potential...")
    print()

    # First, show preview of what will happen
    if extend_file == "file1":
        preview_csv_extension(
            file1,
            file2,
            target_match_cols,
            source_match_cols,
            extend_file,
            add_cols,
            match_type,
            bidirectional,
        )
    else:
        preview_csv_extension(
            file1,
            file2,
            source_match_cols,
            target_match_cols,
            extend_file,
            add_cols,
            match_type,
            bidirectional,
        )

    # Ask for confirmation
    print("❓ Do you want to proceed with the extension?")
    print(f"   This will create a new file: {Path(target_file).stem}_extended.csv")
    print()

    while True:
        choice = input("Continue? (y/n): ").strip().lower()
        if choice in ["y", "yes"]:
            print()
            print("📝 Creating extended CSV file...")
            break
        elif choice in ["n", "no"]:
            print("❌ Extension cancelled.")
            sys.exit(0)
        else:
            print("❌ Please enter 'y' for yes or 'n' for no.")

    # Proceed with actual extension
    if extend_file == "file1":
        extend_csv_files(
            file1,
            file2,
            target_match_cols,
            source_match_cols,
            extend_file,
            add_cols,
            match_type,
            bidirectional,
        )
    else:
        extend_csv_files(
            file1,
            file2,
            source_match_cols,
            target_match_cols,
            extend_file,
            add_cols,
            match_type,
            bidirectional,
        )

    print("🎉 CSV extension completed successfully!")


if __name__ == "__main__":
    main()
