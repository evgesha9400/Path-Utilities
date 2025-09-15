#!/usr/bin/env python3

"""
CSV Fill Script
Fills values in one CSV file based on matching values from another CSV file
"""

import argparse
import csv
import math
import os
import sys
from pathlib import Path

from shared.file_selector import select_files


def get_csv_files(directory="."):
    """Find all CSV files in the specified directory."""
    csv_files = []
    for file in Path(directory).glob("*.csv"):
        if file.is_file():
            csv_files.append(str(file))
    return sorted(csv_files)


def get_columns(file_path):
    """Get column names from CSV in multi-column format."""
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80  # Default if can't determine

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

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


def count_rows(file_path):
    """Count rows in a CSV file (excluding header)."""
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        return sum(1 for _ in reader)


def search_columns(file_path, search_term):
    """Search for columns containing the search term."""
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        found = False
        for i, header in enumerate(headers):
            if search_term in header.lower():
                print(f"{i + 1:2d}) {header.strip()} ✓")
                found = True
        if not found:
            print("No matches found")


def get_column_count(file_path):
    """Get the number of columns in a CSV file."""
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        return len(headers)


def select_column(file_path, prompt_text, num_cols):
    """Interactive column selection with search capability."""
    while True:
        try:
            user_input = input(f"{prompt_text} (1-{num_cols}): ").strip()

            # Check if it's a search request
            if user_input.lower().startswith("search "):
                search_term = user_input[7:].lower()
                print(f"Searching for '{search_term}' in columns:")
                search_columns(file_path, search_term)
                print("Enter a column number or try another search")
                continue

            # Check if it's a valid number
            choice = int(user_input)
            if 1 <= choice <= num_cols:
                return choice
            else:
                print(
                    f"❌ Invalid choice. Please enter a number between 1 and {num_cols}."
                )
        except ValueError:
            print("❌ Invalid input. Please enter a number or 'search <term>'.")
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled.")
            sys.exit(1)


def analyze_data(
    source_file,
    target_file,
    source_match_col,
    target_match_col,
    source_data_col,
    target_fill_col,
):
    """Analyze the data without making changes."""
    # Read source file and create lookup dictionary
    source_data = {}
    with open(source_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Skip headers

        for row in reader:
            if len(row) <= source_match_col or len(row) <= source_data_col:
                continue

            # Use lowercase for matching but preserve original data
            match_key = row[source_match_col].lower().strip()
            if match_key:  # Only add non-empty keys
                source_data[match_key] = row[source_data_col]

    # Read target file and prepare for processing
    matches = 0
    total_rows = 0
    empty_values = 0
    existing_values = 0
    conflicts = 0

    with open(target_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Skip headers

        for row in reader:
            total_rows += 1

            # Ensure row has enough columns
            while len(row) <= max(target_match_col, target_fill_col):
                row.append("")

            # Check for match
            match_key = row[target_match_col].lower().strip()
            has_match = match_key in source_data

            if has_match:
                matches += 1
                target_value = row[target_fill_col].strip()
                source_value = source_data[match_key]

                # Check if target value is empty
                if not target_value:
                    empty_values += 1
                else:
                    existing_values += 1
                    # Count conflicts
                    if target_value != source_value:
                        conflicts += 1

    # Print analysis
    print("\n📊 Analysis:")
    print(f"  Total rows in target CSV: {total_rows}")
    print(f"  Matching rows: {matches} ({(matches / total_rows) * 100:.1f}% of total)")

    if matches > 0:
        print(
            f"  Empty values in matching rows: {empty_values} ({(empty_values / matches) * 100:.1f}% of matches)"
        )
        print(
            f"  Existing values in matching rows: {existing_values} ({(existing_values / matches) * 100:.1f}% of matches)"
        )

        if conflicts > 0:
            print(
                f"  Potential conflicts found: {conflicts} ({(conflicts / existing_values) * 100:.1f}% of existing values)"
            )


def fill_csv_data(
    source_file,
    target_file,
    source_match_col,
    target_match_col,
    source_data_col,
    target_fill_col,
    conflict_mode,
):
    """Fill CSV data based on matching columns."""
    # Read source file and create lookup dictionary
    source_data = {}
    with open(source_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Skip headers

        for row in reader:
            if len(row) <= source_match_col or len(row) <= source_data_col:
                continue

            # Use lowercase for matching but preserve original data
            match_key = row[source_match_col].lower().strip()
            if match_key:  # Only add non-empty keys
                source_data[match_key] = row[source_data_col]

    # Read target file and prepare for processing
    target_rows = []
    target_headers = []
    matches = 0
    total_rows = 0
    empty_values = 0
    existing_values = 0
    modified_rows = 0
    conflicts = 0
    conflict_prompts = 0

    with open(target_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Skip headers

        for row in reader:
            total_rows += 1

            # Ensure row has enough columns
            while len(row) <= max(target_match_col, target_fill_col):
                row.append("")

            # Check for match
            match_key = row[target_match_col].lower().strip()
            has_match = match_key in source_data

            if has_match:
                matches += 1
                target_value = row[target_fill_col].strip()
                source_value = source_data[match_key]

                # Check if target value is empty
                if not target_value:
                    empty_values += 1
                    row[target_fill_col] = source_value
                    modified_rows += 1
                else:
                    existing_values += 1
                    # Handle conflict based on mode
                    if target_value != source_value:
                        conflicts += 1
                        if conflict_mode == "override":
                            row[target_fill_col] = source_value
                            modified_rows += 1
                        elif conflict_mode == "prompt":
                            conflict_prompts += 1
                            print(
                                f"\nConflict in row with match value: {row[target_match_col]}"
                            )
                            print(f"  1) TARGET value: {target_value}")
                            print(f"  2) SOURCE value: {source_value}")

                            while True:
                                try:
                                    choice = input("Choose option (1-2): ").strip()
                                    if choice == "1":
                                        print("Using TARGET value")
                                        break
                                    elif choice == "2":
                                        row[target_fill_col] = source_value
                                        modified_rows += 1
                                        print("Using SOURCE value")
                                        break
                                    else:
                                        print("Invalid choice. Please enter 1 or 2.")
                                except KeyboardInterrupt:
                                    print("\n❌ Operation cancelled.")
                                    sys.exit(1)
                        # For 'skip' mode, do nothing

            target_rows.append(row)

    # Write the updated data back to a new file
    output_file = target_file.replace(".csv", "_filled.csv")
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(target_headers)
        writer.writerows(target_rows)

    # Print analysis
    print("\n📊 Analysis:")
    print(f"  Total rows in target CSV: {total_rows}")
    print(f"  Matching rows: {matches} ({(matches / total_rows) * 100:.1f}% of total)")

    if matches > 0:
        print(
            f"  Empty values in matching rows: {empty_values} ({(empty_values / matches) * 100:.1f}% of matches)"
        )
        print(
            f"  Existing values in matching rows: {existing_values} ({(existing_values / matches) * 100:.1f}% of matches)"
        )

        if conflicts > 0:
            print(
                f"  Conflicts found: {conflicts} ({(conflicts / existing_values) * 100:.1f}% of existing values)"
            )

            if conflict_mode == "override":
                print("  All conflicts resolved by overriding target values")
            elif conflict_mode == "skip":
                print("  All conflicts skipped (kept target values)")
            elif conflict_mode == "prompt":
                print(f"  Conflicts resolved through user prompts: {conflict_prompts}")

    print("\n✅ Summary:")
    print(
        f"  Modified rows: {modified_rows} ({(modified_rows / total_rows) * 100:.1f}% of total)"
    )
    print(f"  Output saved to: {output_file}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Fill values in one CSV file based on matching values from another CSV file"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="CSV files to process (optional - will scan current directory if not provided)",
    )

    parser.parse_args()  # Parse arguments but don't use them yet

    print("🔍 Scanning for CSV files in current directory...")

    # Find all CSV files
    csv_files = get_csv_files(".")

    if len(csv_files) == 0:
        print("❌ No CSV files found in current directory.")
        sys.exit(1)

    if len(csv_files) == 1:
        print("❌ Only one CSV file found. Need at least 2 files to fill data.")
        sys.exit(1)

    # Let user select files
    csv_files = select_files(
        "CSV File Selection", 2, 2, "*.csv", ".", "sequential", True
    )
    if not csv_files:
        sys.exit(1)

    print(f"📁 Selected {len(csv_files)} files:")
    for file in csv_files:
        filename = os.path.basename(file)
        print(f"   {filename}")
    print()

    # Ask which file is the target (to be filled)
    print("Which CSV file do you want to fill?")
    print(f"  1) {os.path.basename(csv_files[0])}")
    print(f"  2) {os.path.basename(csv_files[1])}")
    print()

    while True:
        try:
            choice = int(input("Enter your choice (1-2): "))
            if choice == 1:
                target_file = csv_files[0]
                source_file = csv_files[1]
                break
            elif choice == 2:
                target_file = csv_files[1]
                source_file = csv_files[0]
                break
            else:
                print("❌ Invalid choice. Please enter 1 or 2.")
        except ValueError:
            print("❌ Invalid input. Please enter 1 or 2.")
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled.")
            sys.exit(1)

    print()
    print(f"📋 Target file (to be filled): {os.path.basename(target_file)}")
    print(f"📋 Source file (data source): {os.path.basename(source_file)}")
    print()

    # Show columns for both files with multi-column display
    print(f"Columns in TARGET file ({os.path.basename(target_file)}):")
    get_columns(target_file)
    print()
    print(f"Columns in SOURCE file ({os.path.basename(source_file)}):")
    get_columns(source_file)
    print()

    # Get column counts
    num_cols_target = get_column_count(target_file)
    num_cols_source = get_column_count(source_file)

    # Select column to match from target file
    print(
        "Enter column number or search by name (e.g., 'search email' to find email columns)"
    )
    target_match_col = select_column(
        target_file, "Select column from TARGET file to match on", num_cols_target
    )

    # Select column to match from source file
    print(
        "Enter column number or search by name (e.g., 'search email' to find email columns)"
    )
    source_match_col = select_column(
        source_file, "Select column from SOURCE file to match on", num_cols_source
    )

    print()
    print(
        "👍 Matching will be performed bidirectionally on lowercased strings from both columns"
    )
    print("   (original data will not be modified)")
    print()

    # Select column to fill in target file
    print(
        "Enter column number or search by name (e.g., 'search email' to find email columns)"
    )
    target_fill_col = select_column(
        target_file, "Select column in TARGET file to fill", num_cols_target
    )

    # Select column to use from source file
    print(
        "Enter column number or search by name (e.g., 'search email' to find email columns)"
    )
    source_data_col = select_column(
        source_file,
        "Select column from SOURCE file to use for filling",
        num_cols_source,
    )

    print()
    print("📊 Running analysis...")

    # Run the analysis only (without saving any changes)
    analyze_data(
        source_file,
        target_file,
        source_match_col - 1,
        target_match_col - 1,
        source_data_col - 1,
        target_fill_col - 1,
    )

    print()
    print("Choose how to handle conflicts (when target already has a value):")
    print("  1) Override - Always use the source value")
    print("  2) Skip - Keep the target value")
    print("  3) Prompt - Ask for each conflict")
    print()

    while True:
        try:
            choice = int(input("Enter your choice (1-3): "))
            if choice == 1:
                conflict_mode = "override"
                break
            elif choice == 2:
                conflict_mode = "skip"
                break
            elif choice == 3:
                conflict_mode = "prompt"
                break
            else:
                print("❌ Invalid choice. Please enter a number between 1 and 3.")
        except ValueError:
            print("❌ Invalid input. Please enter a number between 1 and 3.")
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled.")
            sys.exit(1)

    print()
    print("📝 Processing files...")
    print(f"   Conflict resolution mode: {conflict_mode}")
    print()

    # Now perform the actual fill operation with the chosen conflict mode
    fill_csv_data(
        source_file,
        target_file,
        source_match_col - 1,
        target_match_col - 1,
        source_data_col - 1,
        target_fill_col - 1,
        conflict_mode,
    )

    print("🎉 Fill operation completed successfully!")


if __name__ == "__main__":
    main()
