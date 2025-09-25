#!/usr/bin/env python3

"""
CSV Exact Deduplication Script
Removes completely identical rows from a CSV file
"""

import argparse
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path

from shared.file_selector import select_single_file


def get_row_count(input_file):
    """Get total row count from CSV file"""
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        count = sum(1 for row in reader)
    return count


def read_csv_data(filename):
    """Read CSV data and return rows with line numbers"""
    data = []
    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            # Handle completely empty files
            return [], []

        for row_num, row in enumerate(reader):
            # Pad row if it has fewer columns than headers
            while len(row) < len(headers):
                row.append("")
            data.append((row, row_num + 2))  # +2 because we skip header and want 1-based line numbers

    return data, headers


def write_csv_data(filename, rows, headers):
    """Write CSV data to file"""
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def analyze_exact_duplicates(input_file):
    """Analyze exact duplicates in CSV file"""
    data, headers = read_csv_data(input_file)
    original_count = len(data)

    # Handle empty files
    if not headers:
        print("📊 File Analysis:")
        print("   Total rows: 0")
        print("   Empty file - no duplicates possible")
        return 0

    print("📊 File Analysis:")
    print(f"   Total rows: {original_count:,}")
    print()

    # Group rows by exact content
    duplicate_groups = defaultdict(list)

    for row_data, line_num in data:
        # Create key from entire row
        key = tuple(cell.strip() for cell in row_data)
        duplicate_groups[key].append((row_data, line_num))

    # Find duplicates
    duplicate_keys = [key for key, rows in duplicate_groups.items() if len(rows) > 1]
    total_duplicates = sum(len(rows) - 1 for rows in duplicate_groups.values() if len(rows) > 1)

    if len(duplicate_keys) == 0:
        print("✅ No exact duplicates found!")
        print(f"   All {original_count:,} rows are unique.")
        return 0
    else:
        print("📊 Duplicate Summary:")
        print(f"   Unique groups with duplicates: {len(duplicate_keys):,}")
        print(f"   Total duplicate rows to remove: {total_duplicates:,}")
        print(f"   Final row count after deduplication: {original_count - total_duplicates:,}")
        print(f"   Reduction: {(total_duplicates / original_count * 100):.1f}%")
        print()

        # Show examples of duplicates (limit to first 5 groups)
        print("🔍 Duplicate Examples:")

        shown_groups = 0
        max_groups_to_show = 5

        for key, rows in duplicate_groups.items():
            if len(rows) <= 1 or shown_groups >= max_groups_to_show:
                continue

            shown_groups += 1
            print(f"\n   Group {shown_groups}: {len(rows)} identical rows")
            print(f"     Content preview: {str(key)[:100]}..." if len(str(key)) > 100 else f"     Content: {key}")
            print(f"     Found on lines: {', '.join(str(row[1]) for row in rows)}")

        if len(duplicate_keys) > max_groups_to_show:
            remaining = len(duplicate_keys) - max_groups_to_show
            print(f"\n   ... and {remaining} more duplicate group(s)")

        return total_duplicates


def display_row(row, headers, line_num):
    """Display a single row for manual selection"""
    print(f"     Line {line_num}:")
    for i, (header, value) in enumerate(zip(headers, row)):
        if value.strip():  # Only show non-empty values
            display_value = value[:50] + "..." if len(value) > 50 else value
            print(f"       {header}: {display_value}")


def manual_deduplication(input_file, output_file):
    """Perform manual deduplication with user selection"""
    data, headers = read_csv_data(input_file)

    # Group rows by exact content
    duplicate_groups = defaultdict(list)
    for row_data, line_num in data:
        key = tuple(cell.strip() for cell in row_data)
        duplicate_groups[key].append((row_data, line_num))

    # Process duplicates with manual selection
    selected_rows = []
    group_num = 0

    for key, rows in duplicate_groups.items():
        if len(rows) == 1:
            # No duplicates, keep the only row
            selected_rows.append(rows[0])
        else:
            # Duplicates found - manual selection
            group_num += 1
            print(f"\n🔍 Duplicate Group {group_num} ({len(rows)} identical rows):")
            print("=" * 60)

            for i, (row_data, line_num) in enumerate(rows):
                print(f"\n  {i + 1}) ")
                display_row(row_data, headers, line_num)

            print(f"\n  {len(rows) + 1}) Skip this group (keep first occurrence - line {rows[0][1]})")

            while True:
                try:
                    choice = input(f"\nSelect which row to keep (1-{len(rows) + 1}): ").strip()
                    choice_num = int(choice)

                    if 1 <= choice_num <= len(rows):
                        selected_rows.append(rows[choice_num - 1])
                        print(f"✓ Keeping row from line {rows[choice_num - 1][1]}")
                        break
                    elif choice_num == len(rows) + 1:
                        selected_rows.append(rows[0])  # Keep first
                        print(f"✓ Keeping first occurrence (line {rows[0][1]})")
                        break
                    else:
                        print(f"❌ Invalid choice. Please enter a number between 1 and {len(rows) + 1}.")
                except (ValueError, KeyboardInterrupt):
                    print(f"❌ Invalid input. Please enter a number between 1 and {len(rows) + 1}.")

    # Sort by original line number to maintain order
    selected_rows.sort(key=lambda x: x[1])
    final_rows = [row for row, line_num in selected_rows]

    # Write result
    write_csv_data(output_file, final_rows, headers)

    removed_count = len(data) - len(final_rows)
    print("\n✅ Manual deduplication completed!")
    print(f"   Created: {output_file}")
    print(f"   Rows removed: {removed_count:,}")
    print(f"   Final count: {len(final_rows):,}")


def auto_deduplication(input_file, output_file):
    """Perform automatic deduplication (keep first occurrence)"""
    data, headers = read_csv_data(input_file)

    # Track seen rows and keep first occurrence
    seen_rows = set()
    unique_rows = []
    removed_count = 0

    for row_data, row_num in data:
        row_key = tuple(cell.strip() for cell in row_data)

        if row_key not in seen_rows:
            seen_rows.add(row_key)
            unique_rows.append(row_data)
        else:
            removed_count += 1

    # Write result
    write_csv_data(output_file, unique_rows, headers)

    print("✅ Automatic deduplication completed!")
    print(f"   Created: {output_file}")
    print(f"   Rows removed: {removed_count:,}")
    print(f"   Final count: {len(unique_rows):,}")


def find_csv_files():
    """Find CSV files in current directory"""
    csv_files = []
    for file in Path(".").glob("*.csv"):
        if file.is_file():
            csv_files.append(file)

    return sorted(csv_files)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="CSV Exact Deduplication - Remove completely identical rows")
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Input CSV file (optional - will scan current directory if not provided)",
    )
    args = parser.parse_args()

    print("🔍 EXACT DEDUPLICATION")
    print("════════════════════════════════════════════════════════════════")
    print("This script removes rows that are completely identical across ALL columns.")
    print("• Compares entire rows byte-for-byte")
    print("• Default behavior: keeps first occurrence of each duplicate set")
    print("• Optional: manual selection allows you to choose which duplicate to keep")
    print("════════════════════════════════════════════════════════════════")
    print()

    # Find CSV files
    print("🔍 Scanning for CSV files in current directory...")

    csv_files = find_csv_files()
    num_files = len(csv_files)

    # Select file
    input_file = select_single_file("Select CSV file to deduplicate", "*.csv", ".", True)
    if not input_file:
        sys.exit(1)

    print()
    print(f"Selected file: {Path(input_file).name}")

    # Check if file is readable
    if not os.access(input_file, os.R_OK):
        print(f"❌ Cannot read {input_file}")
        sys.exit(1)

    # Get total row count
    total_rows = get_row_count(input_file)
    print(f"Total data rows: {total_rows}")
    print()

    # Analyze duplicates
    duplicate_count = analyze_exact_duplicates(input_file)
    print()

    # If no duplicates found, exit
    if duplicate_count == 0:
        print("🎉 No deduplication needed - your file has no exact duplicates!")
        sys.exit(0)

    # Show deduplication summary and ask for confirmation
    print(f"⚠️  Found {duplicate_count} duplicate rows to remove.")
    print()
    print("📊 DEDUPLICATION SUMMARY:")
    print(f"   • Original file: {input_file}")
    print(f"   • Duplicate rows to remove: {duplicate_count}")
    print(f"   • Final row count: {total_rows - duplicate_count}")
    print("   • Your original file will remain unchanged")
    print("   • A new deduplicated file will be created")
    print()

    try:
        proceed_choice = input("Do you want to proceed with deduplication? (y/N): ").strip()
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)

    print()

    if not proceed_choice.lower().startswith("y"):
        print("❌ Deduplication cancelled by user.")
        sys.exit(0)

    print("Choose deduplication method:")
    print("  1) Automatic - keep first occurrence of each duplicate set")
    print("  2) Manual - review each duplicate set and choose which row to keep")
    print()

    while True:
        try:
            method_choice = input("Enter your choice (1-2): ").strip()
            if method_choice == "1":
                use_manual = False
                break
            elif method_choice == "2":
                use_manual = True
                break
            else:
                print("❌ Invalid choice. Please enter 1 or 2.")
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            sys.exit(1)

    # Generate output filename
    base_name = Path(input_file).stem
    output_file = f"{base_name}_exact_deduplicated.csv"

    print()
    print("📝 Processing file...")
    print(f"   Input file: {input_file}")
    print(f"   Output file: {output_file}")
    print()

    # Perform deduplication
    try:
        if use_manual:
            manual_deduplication(input_file, output_file)
        else:
            auto_deduplication(input_file, output_file)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)

    print()
    print("🎉 Exact deduplication completed successfully!")


if __name__ == "__main__":
    main()
