#!/usr/bin/env python3

"""
CSV Analyzer Script
Analyzes the percentage of filled rows for each column in a CSV file
Outputs results sorted from most filled to least filled columns
"""

import argparse
import csv
import os
import sys

from shared.file_selector import select_single_file


def analyze_csv_columns(csv_file):
    """Analyze CSV column fill percentages."""
    # Try different encodings
    encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

    for encoding in encodings:
        try:
            with open(csv_file, "r", encoding=encoding) as f:
                reader = csv.reader(f)
                try:
                    headers = next(reader)
                except StopIteration:
                    # Empty file
                    return [], 0

                # Initialize counters for each column
                total_rows = 0
                filled_counts = [0] * len(headers)

                # Process each row
                for row in reader:
                    # Skip completely empty rows
                    if not row or all(not cell.strip() for cell in row):
                        continue

                    total_rows += 1

                    # Check each column in this row
                    for col_idx in range(len(headers)):
                        # Get the value, handling rows with fewer columns
                        value = row[col_idx] if col_idx < len(row) else ""

                        # Count as filled if not empty after stripping whitespace
                        if value.strip():
                            filled_counts[col_idx] += 1

                # Calculate percentages and create results
                results = []
                for col_idx, header in enumerate(headers):
                    filled_count = filled_counts[col_idx]
                    percentage = (filled_count / total_rows * 100) if total_rows > 0 else 0
                    results.append(
                        {
                            "column": header.strip(),
                            "filled_count": filled_count,
                            "total_rows": total_rows,
                            "percentage": percentage,
                            "column_index": col_idx + 1,
                        }
                    )

                return results, total_rows

        except UnicodeDecodeError:
            if encoding == encodings[-1]:  # Last encoding attempt
                print(f"❌ Could not decode {csv_file} with any of the attempted encodings.")
                sys.exit(1)
            continue  # Try next encoding

    return [], 0


def display_results(results, total_rows, csv_file):
    """Display the analysis results in a formatted table."""
    if not results:
        print("❌ No data found in the CSV file.")
        sys.exit(1)

    # Sort by percentage (descending), then by column name for ties
    results.sort(key=lambda x: (-x["percentage"], x["column"]))

    print("📊 CSV Column Fill Analysis")
    print("==================================")
    print(f"File: {csv_file}")
    print(f"Total rows analyzed: {total_rows:,}")
    print(f"Total columns: {len(results)}")
    print()

    # Find the longest column name for formatting
    max_col_width = max(len(result["column"]) for result in results)
    max_col_width = max(max_col_width, 10)  # Minimum width

    # Display results in a formatted table
    print(f"{'Column':<{max_col_width}} | {'Index':<6} | {'Filled':<10} | {'Total':<10} | {'Percentage':<10}")
    print("-" * (max_col_width + 6 + 10 + 10 + 10 + 12))

    for result in results:
        col_name = result["column"]
        if len(col_name) > max_col_width:
            col_name = col_name[: max_col_width - 3] + "..."

        print(
            f"{col_name:<{max_col_width}} | {result['column_index']:<6} | {result['filled_count']:<10,} | {result['total_rows']:<10,} | {result['percentage']:<10.1f}%"
        )

    print()

    # Summary statistics
    filled_percentages = [r["percentage"] for r in results]
    avg_fill = sum(filled_percentages) / len(filled_percentages)
    min_fill = min(filled_percentages)
    max_fill = max(filled_percentages)

    completely_filled = sum(1 for r in results if r["percentage"] == 100.0)
    empty_columns = sum(1 for r in results if r["percentage"] == 0.0)

    print("📈 Summary Statistics:")
    print(f"  Average fill percentage: {avg_fill:.1f}%")
    print(f"  Highest fill percentage: {max_fill:.1f}%")
    print(f"  Lowest fill percentage: {min_fill:.1f}%")
    print(
        f"  Completely filled columns: {completely_filled}/{len(results)} ({completely_filled / len(results) * 100:.1f}%)"
    )
    if empty_columns > 0:
        print(f"  Empty columns: {empty_columns}/{len(results)} ({empty_columns / len(results) * 100:.1f}%)")

    # Show top and bottom performers
    print()
    print("🏆 Top 3 Most Filled Columns:")
    for i, result in enumerate(results[:3]):
        print(f"  {i + 1}. {result['column']} ({result['percentage']:.1f}%)")

    if len(results) > 3:
        print()
        print("⚠️  Bottom 3 Least Filled Columns:")
        for i, result in enumerate(results[-3:]):
            print(f"  {len(results) - 2 + i}. {result['column']} ({result['percentage']:.1f}%)")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Analyzes the percentage of filled rows for each column in a CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Analyze CSV files in current directory
  %(prog)s data.csv          # Analyze specific CSV file
        """,
    )

    parser.add_argument(
        "csv_file",
        nargs="?",
        help="CSV file to analyze (if not provided, will scan current directory)",
    )

    args = parser.parse_args()

    # Determine which CSV file to analyze
    if args.csv_file:
        # Use provided file
        csv_file = args.csv_file
        if not os.path.exists(csv_file):
            print(f"❌ File not found: {csv_file}")
            sys.exit(1)
        if not csv_file.lower().endswith(".csv"):
            print(f"❌ File is not a CSV file: {csv_file}")
            sys.exit(1)
    else:
        # Scan current directory for CSV files
        print("🔍 Scanning for CSV files in current directory...")

        # Use the unified file selector
        csv_file = select_single_file("CSV File Selection for Analysis", "*.csv", ".", False)
        if not csv_file:
            sys.exit(1)

    print(f"📁 Selected file: {os.path.basename(csv_file)}")
    print()

    # Check if file is readable
    if not os.access(csv_file, os.R_OK):
        print(f"❌ Cannot read {csv_file}")
        sys.exit(1)

    print("📝 Analyzing CSV file...")
    print()

    # Perform the analysis
    results, total_rows = analyze_csv_columns(csv_file)

    # Display results
    display_results(results, total_rows, csv_file)

    print()
    print("🎉 Analysis completed successfully!")


if __name__ == "__main__":
    main()
