#!/usr/bin/env python3

"""
CSV Column Deletion Script
Analyzes fill percentage of columns in CSV files and allows selective column deletion
"""

import argparse
import csv
import os
import sys
from pathlib import Path

from shared.file_selector import select_single_file


def is_empty_value(value):
    """Check if a value is considered empty."""
    if not value:
        return True
    return str(value).strip() == ""


def find_csv_files(directory="."):
    """Find all CSV files in the specified directory."""
    csv_files = []
    for file in Path(directory).glob("*.csv"):
        if file.is_file():
            csv_files.append(str(file))

    return sorted(csv_files)


def analyze_fill_percentage(filename):
    """Analyze fill percentage for CSV columns."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            # Detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter

            reader = csv.reader(f, delimiter=delimiter)
            headers = next(reader)

            # Initialize counters
            total_rows = 0
            non_empty_counts = {header.strip(): 0 for header in headers}

            # Count non-empty values for each column
            for row in reader:
                total_rows += 1

                # Pad row if it has fewer columns than headers
                while len(row) < len(headers):
                    row.append("")

                for i, header in enumerate(headers):
                    header = header.strip()
                    value = row[i] if i < len(row) else ""
                    if not is_empty_value(value):
                        non_empty_counts[header] += 1

            # Calculate and display fill percentages
            print(f"📊 Fill Analysis for: {filename}")
            print(f"Total rows: {total_rows:,}")
            print("=" * 80)
            print(f"{'#':<3} {'Column Name':<40} {'Fill %':<8} {'Non-empty':<12}")
            print("-" * 80)

            # Sort columns by fill percentage (ascending)
            fill_data = []
            for header in headers:
                header = header.strip()
                if total_rows > 0:
                    fill_percent = (non_empty_counts[header] / total_rows) * 100
                    fill_data.append((header, fill_percent, non_empty_counts[header]))
                else:
                    fill_data.append((header, 0.0, 0))

            fill_data.sort(key=lambda x: x[1])  # Sort by fill percentage

            for i, (column, fill_percent, non_empty_count) in enumerate(fill_data, 1):
                # Truncate long column names for display
                display_name = column[:38] + ".." if len(column) > 40 else column
                print(
                    f"{i:<3} {display_name:<40} {fill_percent:>6.2f}% {non_empty_count:>10,}"
                )

            return fill_data, total_rows, delimiter

    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")
        sys.exit(1)


def parse_column_selection(user_input, max_cols):
    """Parse user input for column selection."""
    input_str = user_input.strip().lower()

    if input_str == "none":
        return []
    elif input_str == "all":
        return list(range(1, max_cols + 1))

    try:
        # Parse comma-separated numbers and ranges
        parts = [part.strip() for part in input_str.split(",")]
        selected = set()  # Use set to avoid duplicates

        for part in parts:
            if "-" in part:
                # Handle range (e.g., '5-10')
                range_parts = part.split("-")
                if len(range_parts) != 2:
                    print(
                        f'ERROR: Invalid range format "{part}". Use format like "5-10"'
                    )
                    return None

                try:
                    start = int(range_parts[0].strip())
                    end = int(range_parts[1].strip())

                    if start > end:
                        print(f'ERROR: Invalid range "{part}". Start must be <= end')
                        return None

                    if start < 1 or end > max_cols:
                        print(f'ERROR: Range "{part}" is out of bounds (1-{max_cols})')
                        return None

                    # Add all numbers in the range
                    for num in range(start, end + 1):
                        selected.add(num)

                except ValueError:
                    print(f'ERROR: Invalid range "{part}". Both parts must be numbers')
                    return None
            else:
                # Handle single number
                try:
                    col_num = int(part)
                    if 1 <= col_num <= max_cols:
                        selected.add(col_num)
                    else:
                        print(f"ERROR: Column {col_num} is out of range (1-{max_cols})")
                        return None
                except ValueError:
                    print(f'ERROR: "{part}" is not a valid number')
                    return None

        if selected:
            # Sort the selected columns and return as list
            return sorted(list(selected))
        else:
            return []

    except Exception:
        print(
            'ERROR: Invalid input. Please enter numbers separated by commas, ranges (e.g., 5-10), "none", or "all"'
        )
        return None


def delete_columns_from_csv(filename, columns_to_delete, delimiter):
    """Delete specified columns from CSV file."""
    if not columns_to_delete:
        print("No columns selected for deletion.")
        return

    # Generate output filename
    base_name = filename.replace(".csv", "")
    output_filename = f"{base_name}_Delete_Columns.csv"

    try:
        # Read original file to get headers and data
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=delimiter)
            headers = [h.strip() for h in next(reader)]

            # Determine columns to keep
            columns_to_keep = [col for col in headers if col not in columns_to_delete]

            if not columns_to_keep:
                print("❌ Cannot delete all columns. At least one column must remain.")
                sys.exit(1)

            # Read all data
            f.seek(0)
            reader = csv.DictReader(f, delimiter=delimiter)
            rows = list(reader)

        # Write filtered CSV
        with open(output_filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns_to_keep, delimiter=delimiter)
            writer.writeheader()

            for row in rows:
                filtered_row = {col: row.get(col, "") for col in columns_to_keep}
                writer.writerow(filtered_row)

        print(f"✓ Successfully created: {output_filename}")
        print(
            f"  Deleted {len(columns_to_delete)} column(s): {', '.join(columns_to_delete)}"
        )
        print(f"  Remaining {len(columns_to_keep)} column(s)")
        print(f"  Total rows: {len(rows):,}")

    except Exception as e:
        print(f"❌ Error creating output file: {e}")
        sys.exit(1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="CSV Column Analysis & Deletion Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Analyze CSV files in current directory
  %(prog)s data.csv          # Analyze specific CSV file
        """,
    )

    parser.add_argument(
        "file",
        nargs="?",
        help="CSV file to analyze (optional, will scan current directory if not provided)",
    )

    args = parser.parse_args()

    print("🔍 CSV Column Analysis & Deletion Tool")
    print("======================================")

    # Determine which file to analyze
    if args.file:
        # Use provided file
        if not os.path.exists(args.file):
            print(f"❌ File '{args.file}' not found.")
            sys.exit(1)

        if not args.file.lower().endswith(".csv"):
            print(f"❌ File '{args.file}' is not a CSV file.")
            sys.exit(1)

        selected_file = args.file
        print(f"📄 Analyzing file: {selected_file}")
    else:
        # Find CSV files in current directory
        csv_files = find_csv_files()

        if not csv_files:
            print("❌ No CSV files found in current directory.")
            sys.exit(1)

        # Select file to analyze
        selected_file = select_single_file(
            "Select CSV file to analyze", "*.csv", ".", True
        )
        if not selected_file:
            sys.exit(1)

    print()

    # Check if file is readable
    if not os.access(selected_file, os.R_OK):
        print(f"❌ Cannot read {selected_file}")
        sys.exit(1)

    # Analyze fill percentage
    print("📊 Analyzing column fill percentages...")
    print()

    fill_data, total_rows, delimiter = analyze_fill_percentage(selected_file)

    if not fill_data:
        print("❌ Failed to analyze the CSV file.")
        sys.exit(1)

    if total_rows == 0:
        print("❌ CSV file has no data rows.")
        sys.exit(1)

    print()

    # Ask if user wants to delete columns
    print("❓ Do you want to delete any columns?")
    while True:
        proceed = input("Continue with column deletion? (y/n): ").strip().lower()
        if proceed in ["y", "yes"]:
            break
        elif proceed in ["n", "no"]:
            print("✅ Analysis complete. No columns were deleted.")
            sys.exit(0)
        else:
            print("Please enter 'y' or 'n'")

    print()
    print("🗑️  Column Deletion Selection")
    print("=============================")
    print("Select columns to delete (you can choose multiple):")
    print()

    # Display numbered column list
    for i, (column, fill_percent, _) in enumerate(fill_data, 1):
        print(f"{i:2d}) {column} ({fill_percent:.2f}% fill)")

    print()
    print("Commands:")
    print("  Enter numbers separated by commas (e.g., 1,3,5)")
    print("  Enter ranges using dashes (e.g., 1-10, 15-20)")
    print("  Mix both formats (e.g., 1,3,5-10,15,20-25)")
    print("  Enter 'none' to skip deletion")
    print("  Enter 'all' to delete all columns")
    print()

    # Get user selection
    while True:
        user_input = input("Enter your selection: ")
        selected_columns = parse_column_selection(user_input, len(fill_data))

        if selected_columns is None:
            continue
        else:
            break

    if not selected_columns:
        print("✅ No columns selected for deletion.")
        sys.exit(0)

    # Convert column numbers to column names
    columns_to_delete = []
    for num in selected_columns:
        column_name = fill_data[num - 1][0]  # Get column name from fill_data
        columns_to_delete.append(column_name)

    # Confirm deletion
    print()
    print(f"⚠️  You are about to delete {len(columns_to_delete)} column(s):")
    for col in columns_to_delete:
        # Find fill percentage for this column
        for column, fill_percent, _ in fill_data:
            if column == col:
                print(f"   • {col} ({fill_percent:.2f}% fill)")
                break

    print()
    while True:
        confirm = input("Proceed with deletion? (y/n): ").strip().lower()
        if confirm in ["y", "yes"]:
            break
        elif confirm in ["n", "no"]:
            print("❌ Column deletion cancelled.")
            sys.exit(0)
        else:
            print("Please enter 'y' or 'n'")

    # Check if output file exists
    base_name = os.path.splitext(selected_file)[0]
    output_file = f"{base_name}_Delete_Columns.csv"

    if os.path.exists(output_file):
        print()
        while True:
            overwrite = (
                input(
                    f"⚠️  Output file '{output_file}' already exists. Overwrite? (y/n): "
                )
                .strip()
                .lower()
            )
            if overwrite in ["y", "yes"]:
                break
            elif overwrite in ["n", "no"]:
                print("❌ Operation cancelled.")
                sys.exit(0)
            else:
                print("Please enter 'y' or 'n'")

    print()
    print("📝 Creating modified CSV file...")

    # Perform deletion
    delete_columns_from_csv(selected_file, columns_to_delete, delimiter)

    print()
    print("🎉 Column deletion completed successfully!")
    print(f"   Original file: {selected_file}")
    print(f"   New file: {output_file}")


if __name__ == "__main__":
    main()
