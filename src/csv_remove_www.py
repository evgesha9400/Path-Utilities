#!/usr/bin/env python3

import argparse
import csv
import os
import re
import sys
from pathlib import Path


def get_csv_files():
    """Find all CSV files in the current directory."""
    csv_files = []
    for file in Path(".").glob("*.csv"):
        if file.is_file():
            csv_files.append(str(file))
    return sorted(csv_files)


def get_columns(filename):
    """Get column names from CSV file."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            return headers
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)


def display_columns(filename):
    """Display numbered list of columns."""
    headers = get_columns(filename)
    for i, header in enumerate(headers):
        print(f"{i + 1:2d}) {header.strip()}")


def analyze_www_occurrences(filename, col_idx):
    """Analyze CSV and count rows with 'www.' in specified column."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)

            if col_idx >= len(headers):
                print(
                    f"❌ Column index {col_idx + 1} is out of range. File has {len(headers)} columns."
                )
                sys.exit(1)

            total_rows = 0
            matching_rows = 0
            matching_examples = []

            for row_num, row in enumerate(
                reader, 2
            ):  # Start from 2 since we already read header
                total_rows += 1

                # Pad row if it has fewer columns than headers
                while len(row) < len(headers):
                    row.append("")

                if col_idx < len(row):
                    cell_value = row[col_idx].strip()
                    # Check for www. in a case-insensitive way using regex
                    if re.search(r"(https?://)?(www\.)", cell_value, re.IGNORECASE):
                        matching_rows += 1
                        # Store first few examples
                        if len(matching_examples) < 3:
                            matching_examples.append(cell_value)

            # Show examples
            if matching_examples:
                print('Examples of URLs with "www.":')
                for example in matching_examples:
                    print(f"  - {example}")

            return total_rows, matching_rows, headers[col_idx].strip()

    except Exception as e:
        print(f"❌ Error analyzing file: {e}")
        sys.exit(1)


def remove_www_from_csv(filename, col_idx):
    """Remove 'www.' from CSV column and create new file."""
    try:
        # Read the original file
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)

            if col_idx >= len(headers):
                print(
                    f"❌ Column index {col_idx + 1} is out of range. File has {len(headers)} columns."
                )
                sys.exit(1)

            # Prepare output filename
            base_name = filename.replace(".csv", "")
            output_filename = f"{base_name}_Removed_www.csv"

            # Read all rows
            rows = []
            modified_count = 0
            examples = []

            for row in reader:
                # Pad row if it has fewer columns than headers
                while len(row) < len(headers):
                    row.append("")

                # Check if this row has 'www.' in the specified column
                if col_idx < len(row):
                    original_value = row[col_idx]

                    if re.search(r"(https?://)?(www\.)", original_value, re.IGNORECASE):
                        # Store original value for example (up to 3)
                        if len(examples) < 3:
                            examples.append((original_value, None))

                        # Remove 'www.' substring while preserving http:// or https:// if present
                        modified_value = re.sub(
                            r"(https?://)?www\.",
                            r"\1",
                            original_value,
                            flags=re.IGNORECASE,
                        )
                        row[col_idx] = modified_value
                        modified_count += 1

                        # Update the example with the modified value
                        if len(examples) > 0 and examples[-1][0] == original_value:
                            examples[-1] = (original_value, modified_value)

                rows.append(row)

            # Write the modified data to new file
            with open(output_filename, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)

            # Display results
            print(f"✓ Created {output_filename}")
            print(f"✓ Modified {modified_count:,} rows")
            print(f"✓ Original file: {filename}")
            print(f"✓ New file: {output_filename}")

            # Display examples if available
            if examples:
                print("Examples of changes:")
                for i, (before, after) in enumerate(examples):
                    if before and after:
                        print(f"Example {i + 1}: '{before}' → '{after}'")

    except Exception as e:
        print(f"❌ Error processing file: {e}")
        sys.exit(1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="CSV Remove www Script - Removes www. substring from URLs in specified columns"
    )
    parser.add_argument("--help-extended", action="help", help="Show extended help")

    # Parse arguments (though the script doesn't use command line args for file selection)
    args = parser.parse_args()

    print("🔍 Scanning for CSV files in current directory...")

    # Find all CSV files
    csv_files = get_csv_files()
    num_files = len(csv_files)

    if num_files == 0:
        print("❌ No CSV files found in current directory.")
        sys.exit(1)
    elif num_files == 1:
        print("📁 Found 1 CSV file:")
        print(f"   {csv_files[0]}")
        selected_file = csv_files[0]
    else:
        print(f"📁 Found {num_files} CSV files:")
        for i, file in enumerate(csv_files):
            print(f"   {i + 1}) {file}")
        print()

        # Get file selection
        while True:
            try:
                file_choice = input(f"Select file number (1-{num_files}): ").strip()
                file_choice = int(file_choice)
                if 1 <= file_choice <= num_files:
                    selected_file = csv_files[file_choice - 1]
                    break
                else:
                    print(
                        f"❌ Invalid choice. Please enter a number between 1 and {num_files}."
                    )
            except ValueError:
                print(
                    f"❌ Invalid choice. Please enter a number between 1 and {num_files}."
                )

    print()
    print(f"📋 Selected file: {selected_file}")
    print()

    # Check if file is readable
    if not os.access(selected_file, os.R_OK):
        print(f"❌ Cannot read {selected_file}")
        sys.exit(1)

    # Show headers
    print("📋 File headers:")
    display_columns(selected_file)
    print()

    # Get column count
    headers = get_columns(selected_file)
    num_cols = len(headers)

    # Get column selection
    while True:
        try:
            col_choice = input(
                f"Select column number to remove 'www.' from (1-{num_cols}): "
            ).strip()
            col_choice = int(col_choice)
            if 1 <= col_choice <= num_cols:
                col_idx = col_choice - 1  # Convert to 0-based indexing
                break
            else:
                print(
                    f"❌ Invalid choice. Please enter a number between 1 and {num_cols}."
                )
        except ValueError:
            print(f"❌ Invalid choice. Please enter a number between 1 and {num_cols}.")

    print()

    # Analyze the file and show summary
    print("🔍 Analyzing file for 'www.' occurrences...")
    print()

    # Run analysis
    total_rows, matching_rows, column_name = analyze_www_occurrences(
        selected_file, col_idx
    )

    # Add an empty line for better readability
    print()

    # Display summary
    print("📊 Summary:")
    print(f"   File: {selected_file}")
    print(f"   Column: {column_name}")
    print(f"   Total rows: {total_rows:,}")
    print(f"   Rows with 'www.': {matching_rows:,}")
    if total_rows > 0:
        percentage = (matching_rows * 100) / total_rows
        print(f"   Percentage: {percentage:.1f}%")
    else:
        print("   Percentage: 0.0%")
    print()

    if matching_rows == 0:
        print("ℹ️  No rows found with 'www.' in the selected column.")
        print("   No action needed.")
        sys.exit(0)

    # Prompt user to proceed
    print(
        f"⚠️  This will create a new file with 'www.' removed from {matching_rows:,} rows."
    )
    print(
        "   Example: 'www.example.com' → 'example.com' and 'https://www.example.com' → 'https://example.com'"
    )
    print("   Original file will remain unchanged.")
    print()

    while True:
        proceed_choice = input("Do you want to proceed? (y/n): ").strip().lower()
        if proceed_choice in ["y", "yes"]:
            print()
            print("📝 Processing file...")
            remove_www_from_csv(selected_file, col_idx)
            print()
            print("🎉 Process completed successfully!")
            break
        elif proceed_choice in ["n", "no"]:
            print("❌ Operation cancelled.")
            sys.exit(0)
        else:
            print("❌ Please enter 'y' or 'n'.")


if __name__ == "__main__":
    main()
