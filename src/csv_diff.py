#!/usr/bin/env python3

"""
CSV Difference Script
Compares two CSV files and outputs different or similar rows
"""

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Dict, List

from shared.file_selector import select_multiple_files


def get_header(file_path: str) -> str:
    """Get CSV header from file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readline().strip()


def normalize_columns(header: str) -> str:
    """Normalize column names for comparison."""
    columns = [col.strip() for col in header.split(",")]
    columns.sort()
    return ",".join(columns)


def count_rows(file_path: str) -> int:
    """Count rows in a file (excluding header)."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Remove header
    data_lines = lines[1:] if len(lines) > 1 else []

    # Handle files that may not end with newline
    if data_lines and not data_lines[-1].endswith("\n"):
        return len(data_lines)
    else:
        return len(data_lines)


def find_common_columns(header1: str, header2: str) -> List[str]:
    """Find common columns between two headers."""
    cols1 = [col.strip() for col in header1.split(",")]
    cols2 = [col.strip() for col in header2.split(",")]

    common = []
    for col in cols1:
        if col in cols2:
            common.append(col)

    return common


def find_unique_columns(header1: str, header2: str) -> List[str]:
    """Find columns that exist in first header but not in second."""
    cols1 = [col.strip() for col in header1.split(",")]
    cols2 = [col.strip() for col in header2.split(",")]

    unique = []
    for col in cols1:
        if col not in cols2:
            unique.append(col)

    return unique


def make_key(row: Dict[str, str], cols: List[str]) -> str:
    """Create a key from a row based on common columns."""
    return "|".join([str(row.get(col, "")) for col in cols])


def compare_csv(
    file1: str, file2: str, common_cols: List[str], mode: str, output_file: str
) -> None:
    """Compare two CSV files based on common columns."""
    # Read the first file
    rows1 = {}
    with open(file1, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = make_key(row, common_cols)
            rows1[key] = row

    # Read the second file
    rows2 = {}
    with open(file2, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            key = make_key(row, common_cols)
            rows2[key] = row

    # Find common and unique keys
    keys1 = set(rows1.keys())
    keys2 = set(rows2.keys())
    common_keys = keys1.intersection(keys2)
    only_in_file1 = keys1 - keys2
    only_in_file2 = keys2 - keys1

    # Get all fieldnames from both files
    all_fieldnames = set()
    with open(file1, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for field in reader.fieldnames:
            all_fieldnames.add(field)

    with open(file2, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for field in reader.fieldnames:
            all_fieldnames.add(field)

    all_fieldnames = list(all_fieldnames)

    # Process based on mode
    if mode == "diff":
        # Rows in file1 but not in file2
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_fieldnames)
            writer.writeheader()
            for key in only_in_file1:
                writer.writerow(rows1[key])

        print(
            f"{len(only_in_file1)} rows in {os.path.basename(file1)} but not in {os.path.basename(file2)}"
        )

    elif mode == "common":
        # Rows in both files
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_fieldnames)
            writer.writeheader()
            for key in common_keys:
                # Merge the rows from both files
                merged_row = {}
                for field in all_fieldnames:
                    if field in rows1[key]:
                        merged_row[field] = rows1[key][field]
                    elif field in rows2[key]:
                        merged_row[field] = rows2[key][field]
                    else:
                        merged_row[field] = ""
                writer.writerow(merged_row)

        print(f"{len(common_keys)} rows common to both files")

    elif mode == "unique":
        # Rows unique to each file
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_fieldnames)
            writer.writeheader()
            for key in only_in_file1:
                writer.writerow(rows1[key])
            for key in only_in_file2:
                writer.writerow(rows2[key])

        print(f"{len(only_in_file1)} rows only in {os.path.basename(file1)}")
        print(f"{len(only_in_file2)} rows only in {os.path.basename(file2)}")
        print(f"Total: {len(only_in_file1) + len(only_in_file2)} unique rows")

    elif mode == "file2_only":
        # Rows in file2 but not in file1
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_fieldnames)
            writer.writeheader()
            for key in only_in_file2:
                writer.writerow(rows2[key])

        print(
            f"{len(only_in_file2)} rows in {os.path.basename(file2)} but not in {os.path.basename(file1)}"
        )


def find_csv_files(directory: str = ".") -> List[str]:
    """Find all CSV files in the specified directory."""
    csv_files = []
    for file in Path(directory).glob("*.csv"):
        if file.is_file():
            csv_files.append(str(file))

    return sorted(csv_files)


def select_files_interactive(
    csv_files: List[str], title: str, min_files: int, max_files: int
) -> List[str]:
    """Interactive file selection with the same interface as the bash version."""
    if len(csv_files) == 0:
        print("❌ No CSV files found in current directory.")
        sys.exit(1)

    if len(csv_files) < min_files:
        print(f"❌ Found only {len(csv_files)} files, but {min_files} are required.")
        sys.exit(1)

    # Prepare requirement text
    if min_files == max_files and max_files != 0:
        requirement = f"exactly {min_files}"
    elif max_files == 0:
        requirement = f"at least {min_files}"
    else:
        requirement = f"between {min_files} and {max_files}"

    # Initialize selection status
    file_statuses = [False] * len(csv_files)

    while True:
        # Clear screen (simple approach for terminal)
        os.system("clear" if os.name == "posix" else "cls")

        # Display header
        print(f"📁 {title}")
        print("==================================")
        print(f"Select {requirement} files:")
        print()

        # Display files with selection status
        for i, file in enumerate(csv_files):
            status = "[✓]" if file_statuses[i] else "[ ]"
            print(f"{i + 1:2d}) {status} {os.path.basename(file)}")

        # Count selected files
        selected_count = sum(file_statuses)

        # Display commands and status
        print()
        print("Commands:")
        print(f"  1-{len(csv_files)}: Toggle file selection")
        print("  a: Select all files")
        print("  c: Clear all selections")
        print("  d: Done (proceed with selected files)")
        print("  q: Quit")
        print()

        print(f"Selected files: {selected_count}")
        if min_files == max_files:
            print(f"⚠️  Need exactly {min_files} files")
        elif selected_count < min_files:
            print(f"⚠️  Need at least {min_files} files")
        elif max_files != 0 and selected_count > max_files:
            print(f"⚠️  Maximum {max_files} files allowed")
        print()

        choice = input("Enter choice: ").strip()

        if choice.isdigit():
            choice_num = int(choice)
            if 1 <= choice_num <= len(csv_files):
                idx = choice_num - 1
                file_statuses[idx] = not file_statuses[idx]
            else:
                input("Invalid file number. Press Enter to continue...")
        elif choice.lower() == "a":
            file_statuses = [True] * len(csv_files)
        elif choice.lower() == "c":
            file_statuses = [False] * len(csv_files)
        elif choice.lower() == "d":
            # Check if selection meets requirements
            if selected_count < min_files:
                input(f"❌ Need at least {min_files} files. Press Enter to continue...")
                continue

            if max_files != 0 and selected_count > max_files:
                input(
                    f"❌ Maximum {max_files} files allowed. Press Enter to continue..."
                )
                continue

            # Build selected files list
            selected_files = []
            for i, selected in enumerate(file_statuses):
                if selected:
                    selected_files.append(csv_files[i])
            return selected_files
        elif choice.lower() == "q":
            print("❌ Operation cancelled.")
            sys.exit(1)
        else:
            input("Invalid choice. Press Enter to continue...")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Compare two CSV files and output different or similar rows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Note: We don't add input file arguments since the script uses interactive selection
    # This maintains compatibility with the original bash script behavior

    args = parser.parse_args()

    print("🔍 Scanning for CSV files in current directory...")

    # Find all CSV files
    csv_files = find_csv_files(".")

    if len(csv_files) == 0:
        print("❌ No CSV files found in current directory.")
        sys.exit(1)

    if len(csv_files) == 1:
        print("❌ Only one CSV file found. Need at least 2 files for comparison.")
        sys.exit(1)

    # Let user select files using interactive selection
    selected_files = select_multiple_files(
        "CSV File Selection", 2, 2, "*.csv", ".", "interactive", False
    )
    if not selected_files:
        sys.exit(1)

    file1 = selected_files[0]
    file2 = selected_files[1]

    print(f"📁 Selected {len(selected_files)} files:")
    for file in selected_files:
        print(f"   {os.path.basename(file)}")
    print()

    # Check if files are readable
    if not os.access(file1, os.R_OK):
        print(f"❌ Cannot read {file1}")
        sys.exit(1)

    if not os.access(file2, os.R_OK):
        print(f"❌ Cannot read {file2}")
        sys.exit(1)

    # Get and compare headers
    header1 = get_header(file1)
    header2 = get_header(file2)

    print("🔍 Analyzing CSV files...")
    print(f"   File 1: {os.path.basename(file1)}")
    print(f"   File 2: {os.path.basename(file2)}")
    print()

    # Find common columns
    common_columns = find_common_columns(header1, header2)
    if not common_columns:
        print("❌ No common columns found between the files.")
        sys.exit(1)

    # Find unique columns in each file
    unique_to_file1 = find_unique_columns(header1, header2)
    unique_to_file2 = find_unique_columns(header2, header1)

    print("📊 Column Analysis:")
    print(f"   Common columns: {', '.join(common_columns)}")
    print()

    if unique_to_file1:
        print(
            f"   Columns only in {os.path.basename(file1)}: {', '.join(unique_to_file1)}"
        )

    if unique_to_file2:
        print(
            f"   Columns only in {os.path.basename(file2)}: {', '.join(unique_to_file2)}"
        )
    print()

    # Count rows in each file
    rows1 = count_rows(file1)
    rows2 = count_rows(file2)

    print("📝 Row counts:")
    print(f"   {os.path.basename(file1)}: {rows1} data rows")
    print(f"   {os.path.basename(file2)}: {rows2} data rows")
    print()

    # Ask user for comparison mode
    print("Select comparison mode:")
    print("1) Find rows in file 1 that are NOT in file 2")
    print("2) Find rows in file 2 that are NOT in file 1")
    print("3) Find rows that exist in BOTH files")
    print("4) Find rows that are UNIQUE to each file")
    print()

    mode_choice = input("Enter choice (1-4): ").strip()
    print()

    mode = ""
    output_file = ""
    base_name1 = os.path.splitext(os.path.basename(file1))[0]
    base_name2 = os.path.splitext(os.path.basename(file2))[0]

    if mode_choice == "1":
        mode = "diff"
        output_file = f"{base_name1}_not_in_{base_name2}.csv"
    elif mode_choice == "2":
        mode = "file2_only"
        output_file = f"{base_name2}_not_in_{base_name1}.csv"
    elif mode_choice == "3":
        mode = "common"
        output_file = f"{base_name1}_and_{base_name2}_common.csv"
    elif mode_choice == "4":
        mode = "unique"
        output_file = f"{base_name1}_and_{base_name2}_unique.csv"
    else:
        print("❌ Invalid choice.")
        sys.exit(1)

    # Check if output file exists
    if os.path.exists(output_file):
        confirm = input(
            f"⚠️  Output file '{output_file}' already exists. Overwrite? (y/N): "
        ).strip()
        if confirm.lower() not in ["y", "yes"]:
            print("❌ Operation cancelled.")
            sys.exit(1)

    print("🔍 Comparing files based on common columns...")
    print(f"   Using columns: {', '.join(common_columns)}")
    print(f"   Output file: {output_file}")
    print()

    # Perform the comparison
    compare_csv(file1, file2, common_columns, mode, output_file)

    print()
    print(f"✅ Comparison complete! Results saved to {output_file}")


if __name__ == "__main__":
    main()
