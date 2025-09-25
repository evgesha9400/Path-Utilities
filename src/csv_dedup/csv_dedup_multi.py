#!/usr/bin/env python3

"""
CSV Multi-Column Deduplication Script
Removes duplicate rows based on multiple selected columns
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


def get_columns(input_file):
    """Get column names from CSV"""
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        for i, header in enumerate(headers):
            print(f"{i + 1:2d}) {header.strip()}")


def count_filled_columns(row):
    """Count filled columns in a row"""
    return sum(1 for cell in row if cell.strip())


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
            while len(row) < len(headers):
                row.append("")
            data.append((row, row_num + 2))  # +2 for 1-based line numbers after header

    return data, headers


def write_csv_data(filename, rows, headers):
    """Write CSV data to file"""
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def analyze_multi_duplicates(input_file, column_indices):
    """Analyze multi-column duplicates in CSV file"""
    data, headers = read_csv_data(input_file)
    original_count = len(data)

    # Handle empty files
    if not headers:
        print("📊 File Analysis:")
        print("   Total rows: 0")
        print("   Empty file - no duplicates possible")
        return 0

    column_names = [headers[i].strip() for i in column_indices if i < len(headers)]

    print("📊 File Analysis:")
    print(f"   Total rows: {original_count:,}")
    column_names_quoted = [f'"{name}"' for name in column_names]
    print(f"   Deduplication columns: {', '.join(column_names_quoted)}")
    print(f"   Column combination: {' + '.join(column_names)}")
    print()

    # Group rows by composite key
    duplicate_groups = defaultdict(list)

    for row_data, line_num in data:
        # Create composite key from selected columns
        key_parts = []
        for col_idx in column_indices:
            if col_idx < len(row_data):
                key_parts.append(row_data[col_idx].strip().lower())
            else:
                key_parts.append("")

        composite_key = tuple(key_parts)
        duplicate_groups[composite_key].append((row_data, line_num))

    # Find duplicates
    duplicate_keys = [key for key, rows in duplicate_groups.items() if len(rows) > 1]
    total_duplicates = sum(len(rows) - 1 for rows in duplicate_groups.values() if len(rows) > 1)

    if len(duplicate_keys) == 0:
        print("✅ No duplicates found!")
        print(f"   All {original_count:,} rows have unique combinations of the selected columns.")
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

        for composite_key, rows in duplicate_groups.items():
            if len(rows) <= 1 or shown_groups >= max_groups_to_show:
                continue

            shown_groups += 1

            # Format the composite key for display
            key_display = []
            for i, (col_idx, key_part) in enumerate(zip(column_indices, composite_key)):
                col_name = column_names[i] if i < len(column_names) else f"col_{col_idx}"
                display_value = key_part if len(key_part) <= 30 else key_part[:27] + "..."
                key_display.append(f'{col_name}="{display_value}"')

            print(f"\n   Group {shown_groups}: {len(rows)} rows with {' | '.join(key_display)}")
            print(f"     Found on lines: {', '.join(str(row[1]) for row in rows)}")

            # Show filled column counts for each row
            for row_data, line_num in rows:
                filled_count = count_filled_columns(row_data)
                print(f"     Line {line_num}: {filled_count} filled columns")

        if len(duplicate_keys) > max_groups_to_show:
            remaining = len(duplicate_keys) - max_groups_to_show
            print(f"\n   ... and {remaining} more duplicate group(s)")

        return total_duplicates


def display_row(row, headers, line_num, key_column_indices):
    """Display a single row for manual selection"""
    print(f"     Line {line_num} ({count_filled_columns(row)} filled columns):")
    for i, (header, value) in enumerate(zip(headers, row)):
        if value.strip() or i in key_column_indices:  # Show non-empty values or key columns
            display_value = value[:50] + "..." if len(value) > 50 else value
            marker = " ★" if i in key_column_indices else ""
            print(f"       {header}: {display_value}{marker}")


def manual_deduplication(input_file, column_indices, output_file):
    """Perform manual deduplication with user selection"""
    data, headers = read_csv_data(input_file)
    column_names = [headers[i].strip() for i in column_indices if i < len(headers)]

    # Group rows by composite key
    duplicate_groups = defaultdict(list)
    for row_data, line_num in data:
        key_parts = []
        for col_idx in column_indices:
            if col_idx < len(row_data):
                key_parts.append(row_data[col_idx].strip().lower())
            else:
                key_parts.append("")

        composite_key = tuple(key_parts)
        duplicate_groups[composite_key].append((row_data, line_num))

    # Process duplicates with manual selection
    selected_rows = []
    group_num = 0

    for composite_key, rows in duplicate_groups.items():
        if len(rows) == 1:
            # No duplicates, keep the only row
            selected_rows.append(rows[0])
        else:
            # Duplicates found - manual selection
            group_num += 1

            # Format the composite key for display
            key_display = []
            for i, (col_idx, key_part) in enumerate(zip(column_indices, composite_key)):
                col_name = column_names[i] if i < len(column_names) else f"col_{col_idx}"
                display_value = key_part if len(key_part) <= 30 else key_part[:27] + "..."
                key_display.append(f'{col_name}="{display_value}"')

            print(f"\n🔍 Duplicate Group {group_num} ({len(rows)} rows with {' | '.join(key_display)}):")
            print("=" * 80)
            print("(★ indicates deduplication columns)")

            for i, (row_data, line_num) in enumerate(rows):
                print(f"\n  {i + 1}) ")
                display_row(row_data, headers, line_num, set(column_indices))

            print(f"\n  {len(rows) + 1}) Auto-select best (most filled columns)")
            print(f"  {len(rows) + 2}) Skip this group (keep first occurrence - line {rows[0][1]})")

            while True:
                try:
                    choice = input(f"\nSelect which row to keep (1-{len(rows) + 2}): ").strip()
                    choice_num = int(choice)

                    if 1 <= choice_num <= len(rows):
                        selected_rows.append(rows[choice_num - 1])
                        print(f"✓ Keeping row from line {rows[choice_num - 1][1]}")
                        break
                    elif choice_num == len(rows) + 1:
                        # Auto-select best (most filled)
                        best_row = max(rows, key=lambda x: count_filled_columns(x[0]))
                        selected_rows.append(best_row)
                        print(
                            f"✓ Auto-selected most filled row (line {best_row[1]}, {count_filled_columns(best_row[0])} columns)"
                        )
                        break
                    elif choice_num == len(rows) + 2:
                        selected_rows.append(rows[0])  # Keep first
                        print(f"✓ Keeping first occurrence (line {rows[0][1]})")
                        break
                    else:
                        print(f"❌ Invalid choice. Please enter a number between 1 and {len(rows) + 2}.")
                except (ValueError, KeyboardInterrupt):
                    print(f"❌ Invalid input. Please enter a number between 1 and {len(rows) + 2}.")

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


def auto_deduplication(input_file, column_indices, strategy, output_file):
    """Perform automatic deduplication with specified strategy"""
    data, headers = read_csv_data(input_file)

    # Group rows by composite key
    duplicate_groups = defaultdict(list)
    for row_data, row_num in data:
        key_parts = []
        for col_idx in column_indices:
            if col_idx < len(row_data):
                key_parts.append(row_data[col_idx].strip().lower())
            else:
                key_parts.append("")

        composite_key = tuple(key_parts)
        duplicate_groups[composite_key].append((row_data, row_num))

    def select_row_by_strategy(rows, strategy):
        if strategy == "first":
            return min(rows, key=lambda x: x[1])  # Earliest row number
        elif strategy == "last":
            return max(rows, key=lambda x: x[1])  # Latest row number
        else:  # best
            # Find rows with maximum filled columns
            max_filled = max(count_filled_columns(row[0]) for row in rows)
            best_rows = [row for row in rows if count_filled_columns(row[0]) == max_filled]
            # If tie, keep first
            return min(best_rows, key=lambda x: x[1])

    # Process each group and select based on strategy
    selected_rows = []
    removed_count = 0

    for composite_key, rows in duplicate_groups.items():
        if len(rows) == 1:
            # No duplicates, keep the only row
            selected_rows.append(rows[0])
        else:
            # Duplicates found, select based on strategy
            chosen_row = select_row_by_strategy(rows, strategy)
            selected_rows.append(chosen_row)
            removed_count += len(rows) - 1

    # Sort by original row number to maintain order
    selected_rows.sort(key=lambda x: x[1])
    final_rows = [row for row, row_num in selected_rows]

    # Write result
    write_csv_data(output_file, final_rows, headers)

    print("✅ Automatic deduplication completed!")
    print(f"   Strategy: {strategy}")
    print(f"   Created: {output_file}")
    print(f"   Rows removed: {removed_count:,}")
    print(f"   Final count: {len(final_rows):,}")


def find_csv_files():
    """Find CSV files in current directory"""
    csv_files = []
    for file in Path(".").glob("*.csv"):
        if file.is_file():
            csv_files.append(file)

    return sorted(csv_files)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="CSV Multi-Column Deduplication - Remove duplicates based on multiple columns"
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Input CSV file (optional - will scan current directory if not provided)",
    )
    args = parser.parse_args()

    print("🔍 MULTI-COLUMN DEDUPLICATION")
    print("════════════════════════════════════════════════════════════════")
    print("This script removes rows that have duplicate values across MULTIPLE selected columns.")
    print("• Choose which columns to combine as the duplicate key (e.g., firstName+lastName)")
    print("• Rows with the same combination of values are considered duplicates")
    print("• Automatic modes: keep first, last, or best (most filled) duplicate")
    print("• Manual mode: review each duplicate set and choose which row to keep")
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

    # Show columns
    print("📋 Available columns:")
    get_columns(input_file)
    print()

    # Get column selection
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        num_cols = len(headers)

    print("Select columns to combine for deduplication:")
    print("Enter column numbers separated by commas (e.g., 1,3,5)")
    print("Rows with the same combination of values in these columns will be considered duplicates.")
    print()

    while True:
        try:
            column_input = input("Column numbers: ").strip()

            # Validate column numbers
            try:
                cols = [int(x.strip()) for x in column_input.split(",")]
                valid = all(1 <= col <= num_cols for col in cols)

                if valid and len(cols) >= 2:
                    column_indices = [col - 1 for col in cols]  # Convert to 0-based
                    break
                elif len(cols) < 2:
                    print("❌ Please select at least 2 columns for multi-column deduplication.")
                    print("   (For single-column deduplication, use the 'dedup_single' script instead)")
                else:
                    print(f"❌ Invalid column numbers. Please enter numbers between 1 and {num_cols}.")
            except ValueError:
                print("❌ Invalid input. Please enter column numbers separated by commas.")
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            sys.exit(1)

    print()

    # Analyze duplicates
    duplicate_count = analyze_multi_duplicates(input_file, column_indices)
    print()

    # If no duplicates found, exit
    if duplicate_count == 0:
        print("🎉 No deduplication needed - your file has no duplicates in the selected column combination!")
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
    print("  1) Manual - review each duplicate set and choose which row to keep")
    print("  2) Automatic (first) - keep first occurrence of each duplicate")
    print("  3) Automatic (last) - keep last occurrence of each duplicate")
    print("  4) Automatic (best) - keep row with most filled columns")
    print()

    while True:
        try:
            method_choice = input("Enter your choice (1-4): ").strip()
            if method_choice == "1":
                use_manual = True
                break
            elif method_choice == "2":
                use_manual = False
                strategy = "first"
                break
            elif method_choice == "3":
                use_manual = False
                strategy = "last"
                break
            elif method_choice == "4":
                use_manual = False
                strategy = "best"
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            sys.exit(1)

    # Generate output filename
    base_name = Path(input_file).stem
    if use_manual:
        output_file = f"{base_name}_multi_manual_deduplicated.csv"
    else:
        output_file = f"{base_name}_multi_{strategy}_deduplicated.csv"

    print()
    print("📝 Processing file...")
    print(f"   Input file: {input_file}")
    print(f"   Output file: {output_file}")
    print()

    # Perform deduplication
    try:
        if use_manual:
            manual_deduplication(input_file, column_indices, output_file)
        else:
            auto_deduplication(input_file, column_indices, strategy, output_file)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)

    print()
    print("🎉 Multi-column deduplication completed successfully!")


if __name__ == "__main__":
    main()
