#!/usr/bin/env python3

import argparse
import csv
import os
import sys
from pathlib import Path

from shared.file_selector import select_single_file


def get_header(file_path):
    """Get CSV header from file."""
    with open(file_path, "r") as f:
        reader = csv.reader(f)
        return next(reader)


def count_data_rows(file_path):
    """Count data rows (excluding header) in CSV file."""
    try:
        with open(file_path, "r") as f:
            reader = csv.reader(f)
            rows = list(reader)
            return len(rows) - 1
    except Exception:
        return 0


def validate_csv_file(file_path):
    """Validate if file is a proper CSV."""
    if not os.path.exists(file_path):
        print(f"❌ File '{file_path}' does not exist.")
        return False

    if not os.access(file_path, os.R_OK):
        print(f"❌ Cannot read file '{file_path}'.")
        return False

    if not os.path.getsize(file_path) > 0:
        print(f"❌ File '{file_path}' is empty.")
        return False

    # Check if it has at least one line
    with open(file_path, "r") as f:
        if not f.readline():
            print(f"❌ File '{file_path}' appears to be empty.")
            return False

    return True


def scan_csv_files():
    """Scan current directory for CSV files and return list."""
    csv_files = []
    current_dir = Path(".")

    for file_path in sorted(current_dir.glob("*.csv")):
        if file_path.is_file():
            csv_files.append(str(file_path))

    return csv_files


def show_menu():
    """Display the split options menu."""
    print("📊 CSV Split Options:")
    print()
    print("1) Split into N files with even row distribution")
    print("   - You choose the number of output files")
    print("   - Script calculates optimal rows per file")
    print()
    print("2) Split by maximum rows per file")
    print("   - You set maximum rows per file")
    print("   - Script calculates number of output files needed")
    print()
    print("q) Quit")
    print()


def split_by_count(input_file, num_files, base_name):
    """Split CSV into N files with even distribution."""
    total_rows = count_data_rows(input_file)
    header = get_header(input_file)

    if total_rows == 0:
        print("❌ No data rows found in the CSV file (only header).")
        return False

    # Calculate rows per file
    base_rows = total_rows // num_files
    extra_rows = total_rows % num_files

    print("📊 Split calculation:")
    print(f"   Total data rows: {total_rows}")
    print(f"   Number of files: {num_files}")
    print(f"   Base rows per file: {base_rows}")
    print(f"   Extra rows to distribute: {extra_rows}")
    print()

    # Show distribution
    print("📁 Output files and row mapping:")
    for i in range(1, num_files + 1):
        rows_in_file = base_rows
        if i <= extra_rows:
            rows_in_file = base_rows + 1
        print(f"   {base_name} - Part {i}.csv: {rows_in_file} rows")
    print()

    proceed = input("Proceed with split? (y/N): ").strip().lower()
    if proceed != "y":
        print("❌ Operation cancelled.")
        return False

    print("✂️  Splitting file...")

    # Read all data
    with open(input_file, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)

    header = rows[0]
    data_rows = rows[1:]

    current_row = 0
    for i in range(1, num_files + 1):
        output_file = f"{base_name} - Part {i}.csv"

        # Calculate rows for this file
        rows_in_file = base_rows
        if i <= extra_rows:
            rows_in_file = base_rows + 1

        # Write file
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)

            if rows_in_file > 0:
                end_row = current_row + rows_in_file
                writer.writerows(data_rows[current_row:end_row])
                current_row = end_row

        print(f"   ✓ Created {output_file} with {rows_in_file} data rows")

    print()
    print(f"🎉 Successfully split {input_file} into {num_files} files!")
    return True


def split_by_max_rows(input_file, max_rows, base_name):
    """Split CSV by maximum rows per file."""
    total_rows = count_data_rows(input_file)
    header = get_header(input_file)

    if total_rows == 0:
        print("❌ No data rows found in the CSV file (only header).")
        return False

    # Calculate number of files needed
    num_files = (total_rows + max_rows - 1) // max_rows  # Ceiling division

    print("📊 Split calculation:")
    print(f"   Total data rows: {total_rows}")
    print(f"   Maximum rows per file: {max_rows}")
    print(f"   Number of files needed: {num_files}")
    print()

    # Show distribution
    print("📁 Output files and row mapping:")
    for i in range(1, num_files + 1):
        start_row = (i - 1) * max_rows + 1
        end_row = min(i * max_rows, total_rows)
        rows_in_file = end_row - start_row + 1
        print(f"   {base_name} - Part {i}.csv: {rows_in_file} rows")
    print()

    proceed = input("Proceed with split? (y/N): ").strip().lower()
    if proceed != "y":
        print("❌ Operation cancelled.")
        return False

    print("✂️  Splitting file...")

    # Read all data
    with open(input_file, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)

    header = rows[0]
    data_rows = rows[1:]

    for i in range(1, num_files + 1):
        output_file = f"{base_name} - Part {i}.csv"
        start_row = (i - 1) * max_rows
        end_row = min(i * max_rows, total_rows)
        rows_in_file = end_row - start_row

        # Write file
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)

            if rows_in_file > 0:
                writer.writerows(data_rows[start_row:end_row])

        print(f"   ✓ Created {output_file} with {rows_in_file} data rows")

    print()
    print(f"🎉 Successfully split {input_file} into {num_files} files!")
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="CSV Split Utility")
    parser.add_argument("input_file", nargs="?", help="Input CSV file (optional)")
    args = parser.parse_args()

    print("✂️  CSV Split Utility")
    print("==================")
    print()

    # Get input file
    if args.input_file:
        input_file = args.input_file
        if not os.path.exists(input_file):
            print(f"❌ File '{input_file}' not found in current directory.")
            sys.exit(1)
    else:
        input_file = select_single_file("Select CSV file to split", "*.csv", ".", True)
        if not input_file:
            sys.exit(1)

    # Validate input file
    if not validate_csv_file(input_file):
        sys.exit(1)

    # Get base name for output files (remove extension and path)
    base_name = os.path.splitext(os.path.basename(input_file))[0]

    # Show file info
    total_rows = count_data_rows(input_file)
    header = get_header(input_file)
    print(f"📄 Input file: {input_file}")
    print(f"   Total data rows: {total_rows}")
    print(f"   Header: {', '.join(header)}")
    print()

    if total_rows == 0:
        print("❌ No data rows to split (file contains only header).")
        sys.exit(1)

    # Show menu and get choice
    show_menu()
    choice = input("Choose option (1, 2, or q): ").strip()

    if choice == "1":
        print()
        try:
            num_files = int(input("Enter number of files to create: "))
            if num_files < 1:
                print("❌ Invalid number of files. Must be a positive integer.")
                sys.exit(1)

            if num_files > total_rows:
                print(
                    f"❌ Cannot create more files ({num_files}) than data rows ({total_rows})."
                )
                sys.exit(1)

            print()
            split_by_count(input_file, num_files, base_name)
        except ValueError:
            print("❌ Invalid number of files. Must be a positive integer.")
            sys.exit(1)

    elif choice == "2":
        print()
        try:
            max_rows = int(input("Enter maximum rows per file: "))
            if max_rows < 1:
                print("❌ Invalid number of rows. Must be a positive integer.")
                sys.exit(1)

            print()
            split_by_max_rows(input_file, max_rows, base_name)
        except ValueError:
            print("❌ Invalid number of rows. Must be a positive integer.")
            sys.exit(1)

    elif choice.lower() == "q":
        print("❌ Operation cancelled.")
        sys.exit(0)

    else:
        print("❌ Invalid choice.")
        sys.exit(1)


if __name__ == "__main__":
    main()
