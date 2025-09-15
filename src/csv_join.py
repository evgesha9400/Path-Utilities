#!/usr/bin/env python3

"""
CSV Join Script
Joins CSV files with identical headers in the current directory
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path
from typing import List

from shared.file_selector import select_multiple_files


class CSVJoiner:
    def __init__(self):
        self.selected_files = []

    def get_header(self, filepath: str) -> str:
        """Get CSV header from file"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                first_line = f.readline()
                return first_line.rstrip("\r\n")
        except Exception as e:
            raise Exception(f"Error reading header from {filepath}: {e}")

    def normalize_columns(self, header: str) -> str:
        """Normalize column names for comparison"""
        columns = [col.strip() for col in header.split(",")]
        return ",".join(sorted(columns))

    def find_common_base(self, files: List[str]) -> str:
        """Find longest common substring of all filenames"""
        if not files:
            return "joined"

        # Remove paths and extensions
        basenames = []
        for f in files:
            base = os.path.basename(f).replace(".csv", "")
            basenames.append(base)

        if len(basenames) == 1:
            # Remove trailing numbers and underscores
            result = re.sub(r"[_\-\s]*[0-9]+[_\-\s]*$", "", basenames[0])
            return result.strip("_- ") if result.strip("_- ") else "joined"

        # Find longest common substring among all files
        def longest_common_substring_multiple(strings):
            if not strings:
                return ""

            first = strings[0]
            max_len = 0
            result = ""

            for i in range(len(first)):
                for j in range(i + 1, len(first) + 1):
                    substr = first[i:j]
                    if all(substr in s for s in strings[1:]) and len(substr) > max_len:
                        max_len = len(substr)
                        result = substr

            return result

        common = longest_common_substring_multiple(basenames)

        # Clean up the result
        if common:
            common = re.sub(r"[_\-\s]*[0-9]+[_\-\s]*$", "", common)
            common = common.strip("_- ")

        if common and len(common) >= 3:
            return common
        else:
            # Fallback: use first part of first filename
            first_parts = basenames[0].split("_")[0].split("-")[0].split(" ")[0]
            return first_parts if first_parts and len(first_parts) >= 3 else "joined"

    def count_rows(self, filepath: str) -> int:
        """Count rows in a file (excluding header)"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Remove header and count data rows
            data_lines = [line for line in lines[1:] if line.strip()]
            return len(data_lines)
        except Exception as e:
            print(f"Error counting rows in {filepath}: {e}")
            return 0

    def display_summary(self, files: List[str]) -> bool:
        """Display join summary and get user confirmation"""
        total_data_rows = 0

        print("📊 Join Summary")
        print("==================================")
        print("Files to be joined:")

        for file in files:
            rows = self.count_rows(file)
            total_data_rows += rows
            print(f"   {os.path.basename(file)}: {rows} data rows")

        print()
        print(f"📈 Total data rows in result: {total_data_rows}")
        print(
            f"📝 Result will have: 1 header row + {total_data_rows} data rows = {total_data_rows + 1} total rows"
        )
        print()

        while True:
            confirm = input("Proceed with joining these files? (Y/n): ").strip()
            if confirm.lower() in ["", "y", "yes"]:
                return True
            elif confirm.lower() in ["n", "no"]:
                print("❌ Operation cancelled.")
                return False
            else:
                print("Please enter Y or n")

    def select_files(
        self,
        title: str,
        min_files: int,
        max_files: int,
        file_pattern: str,
        directory: str = ".",
    ) -> bool:
        """Interactive file selection with dynamic rendering"""
        # Validate parameters
        if not title or not file_pattern:
            print(
                "Error: Missing required parameters for file selection", file=sys.stderr
            )
            return False

        if min_files < 1:
            min_files = 1

        # Find all matching files
        directory_path = Path(directory)
        all_files = []

        for file_path in directory_path.glob(file_pattern):
            if file_path.is_file():
                all_files.append(str(file_path))

        all_files.sort()

        # Check if we found any files
        if not all_files:
            print(f"❌ No files matching '{file_pattern}' found in {directory}.")
            return False

        # Check if we have enough files to meet minimum requirement
        if len(all_files) < min_files:
            print(
                f"❌ Found only {len(all_files)} files, but {min_files} are required."
            )
            return False

        # Initialize selection status
        file_statuses = [False] * len(all_files)

        # Prepare requirement text
        if min_files == max_files and max_files != 0:
            requirement = f"exactly {min_files}"
        elif max_files == 0:
            requirement = f"at least {min_files}"
        else:
            requirement = f"between {min_files} and {max_files}"

        while True:
            # Clear screen and redraw (simplified for terminal)
            os.system("clear" if os.name == "posix" else "cls")

            # Display header
            print(f"📁 {title}")
            print("==================================")
            print(f"Select {requirement} files:")
            print()

            # Display files with selection status
            for i, file_path in enumerate(all_files):
                status = "[✓]" if file_statuses[i] else "[ ]"
                print(f"{i + 1:2d}) {status} {os.path.basename(file_path)}")

            # Count selected files
            selected_count = sum(file_statuses)

            # Display commands and status
            print()
            print("Commands:")
            print(f"  1-{len(all_files)}: Toggle file selection")
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
                if 1 <= choice_num <= len(all_files):
                    idx = choice_num - 1
                    file_statuses[idx] = not file_statuses[idx]
                else:
                    print("Invalid file number. Press Enter to continue...")
                    input()
            elif choice.lower() == "a":
                file_statuses = [True] * len(all_files)
            elif choice.lower() == "c":
                file_statuses = [False] * len(all_files)
            elif choice.lower() == "d":
                # Check if selection meets requirements
                if selected_count < min_files:
                    print(
                        f"❌ Need at least {min_files} files. Press Enter to continue..."
                    )
                    input()
                    continue

                if max_files != 0 and selected_count > max_files:
                    print(
                        f"❌ Maximum {max_files} files allowed. Press Enter to continue..."
                    )
                    input()
                    continue

                # Build selected files array
                self.selected_files = [
                    all_files[i] for i, selected in enumerate(file_statuses) if selected
                ]
                return True
            elif choice.lower() == "q":
                print("❌ Operation cancelled.")
                return False
            else:
                print("Invalid choice. Press Enter to continue...")
                input()

    def join_files_same_order(
        self, files: List[str], reference_header: str, output_file: str
    ) -> int:
        """Join files with identical headers in same order"""
        total_rows = 0

        # Write header from reference file
        with open(output_file, "w", encoding="utf-8") as out_f:
            out_f.write(reference_header + "\n")

            # Append data from all files (skip header)
            for file in files:
                rows = self.count_rows(file)
                if rows > 0:
                    with open(file, "r", encoding="utf-8") as in_f:
                        lines = in_f.readlines()
                        for line in lines[1:]:  # Skip header
                            if line.strip():  # Only write non-empty lines
                                out_f.write(line.rstrip("\n\r") + "\n")
                    total_rows += rows
                    print(f"   ✓ Added {rows} rows from {os.path.basename(file)}")
                else:
                    print(f"   ⚠️  No data rows in {os.path.basename(file)}")

        return total_rows

    def reorder_csv_columns(self, input_file: str, chosen_header: str) -> List[str]:
        """Reorder CSV columns to match chosen header"""
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            chosen_cols = [col.strip() for col in chosen_header.split(",")]
            reordered_rows = []

            for row in rows:
                reordered = []
                for col in chosen_cols:
                    val = row.get(col, "")
                    # Handle CSV escaping
                    if "," in val or "\n" in val or '"' in val:
                        val = '"' + val.replace('"', '""') + '"'
                    reordered.append(val)
                reordered_rows.append(",".join(reordered))

            return reordered_rows
        except Exception as e:
            print(f"Error processing file {input_file}: {e}", file=sys.stderr)
            return []

    def join_files_different_order(
        self, files: List[str], chosen_header: str, output_file: str
    ) -> int:
        """Join files with same columns but different orders"""
        total_rows = 0

        with open(output_file, "w", encoding="utf-8") as out_f:
            out_f.write(chosen_header + "\n")

            for file in files:
                file_header = self.get_header(file)

                if file_header == chosen_header:
                    # Same order, just append data
                    rows = self.count_rows(file)
                    if rows > 0:
                        with open(file, "r", encoding="utf-8") as in_f:
                            lines = in_f.readlines()
                            for line in lines[1:]:  # Skip header
                                if line.strip():  # Only write non-empty lines
                                    out_f.write(line.rstrip("\n\r") + "\n")
                        total_rows += rows
                        print(
                            f"   ✓ Added {rows} rows from {os.path.basename(file)} (same order)"
                        )
                else:
                    # Need to reorder columns
                    reordered_rows = self.reorder_csv_columns(file, chosen_header)
                    if reordered_rows:
                        for row in reordered_rows:
                            out_f.write(row + "\n")
                        total_rows += len(reordered_rows)
                        print(
                            f"   ✓ Added {len(reordered_rows)} rows from {os.path.basename(file)} (reordered columns)"
                        )
                    else:
                        print(f"   ⚠️  Error processing {os.path.basename(file)}")

        return total_rows

    def main(self, args):
        """Main function"""
        print("🔍 Scanning for CSV files in current directory...")

        # Find all CSV files
        all_csv_files = []
        for file_path in Path(".").glob("*.csv"):
            if file_path.is_file():
                all_csv_files.append(str(file_path))

        all_csv_files.sort()

        if not all_csv_files:
            print("❌ No CSV files found in current directory.")
            return 1

        if len(all_csv_files) == 1:
            print("❌ Only one CSV file found. Need at least 2 files to join.")
            return 1

        # Let user select files to join
        csv_files = select_multiple_files(
            "CSV File Selection", 2, 0, "*.csv", ".", "interactive", False
        )
        if not csv_files:
            return 1

        print(f"📁 Selected {len(csv_files)} files for joining:")
        for file in csv_files:
            print(f"   {os.path.basename(file)}")
        print()

        # Check if all files are readable and get their headers
        print("🔍 Checking file headers...")

        reference_file = ""
        reference_header = ""
        reference_columns = ""
        all_files_valid = []
        headers_identical = True
        different_order_files = []

        for file in csv_files:
            try:
                current_header = self.get_header(file)
                current_columns = self.normalize_columns(current_header)

                if not reference_file:
                    reference_file = file
                    reference_header = current_header
                    reference_columns = current_columns
                    all_files_valid.append(file)
                    print(f"   ✓ {os.path.basename(file)} (reference)")
                else:
                    if current_columns != reference_columns:
                        print(f"   ❌ {os.path.basename(file)} - Different columns!")
                        print(f"      Reference: {reference_header}")
                        print(f"      This file: {current_header}")
                        print(f"      Reference columns (sorted): {reference_columns}")
                        print(f"      This file columns (sorted): {current_columns}")
                        print()
                        print("Cannot join files with different column sets.")
                        return 1
                    elif current_header != reference_header:
                        headers_identical = False
                        different_order_files.append(file)
                        print(
                            f"   ⚠️  {os.path.basename(file)} - Same columns, different order"
                        )
                        all_files_valid.append(file)
                    else:
                        print(f"   ✓ {os.path.basename(file)} (identical header)")
                        all_files_valid.append(file)
            except Exception as e:
                print(
                    f"⚠️  Warning: Cannot read {os.path.basename(file)}, skipping... ({e})"
                )
                continue

        if len(all_files_valid) < 2:
            print("❌ Need at least 2 valid CSV files to join.")
            return 1

        # Generate output filename
        files_list = "\n".join(all_files_valid)
        base_name = self.find_common_base(all_files_valid)
        output_file = f"{base_name}_joined.csv"

        print()
        print(f"📝 Files to join: {len(all_files_valid)}")
        print(f"   Output file: {output_file}")
        print()

        # Display summary before joining
        if not self.display_summary(all_files_valid):
            return 1

        if headers_identical:
            print("✅ All headers are identical. Proceeding with join...")

            if os.path.exists(output_file):
                while True:
                    confirm = input(
                        f"⚠️  Output file '{output_file}' already exists. Overwrite? (y/N): "
                    ).strip()
                    if confirm.lower() in ["y", "yes"]:
                        break
                    elif confirm.lower() in ["n", "no", ""]:
                        print("❌ Operation cancelled.")
                        return 1
                    else:
                        print("Please enter y or N")

            print()
            print("🔗 Joining files...")

            total_rows = self.join_files_same_order(
                all_files_valid, reference_header, output_file
            )

            print()
            print(f"🎉 Successfully created {output_file} with {total_rows} data rows!")

        else:
            print("⚠️  Files have the same columns but in different orders:")
            print()
            print(f"Order 1 (reference): {reference_header}")
            print(f"   Files: {os.path.basename(reference_file)}")

            for file in all_files_valid:
                if file != reference_file:
                    file_header = self.get_header(file)
                    if file_header == reference_header:
                        print(f"          {os.path.basename(file)}")
            print()

            # Show other orders
            order_num = 2
            processed_headers = [reference_header]

            for file in different_order_files:
                file_header = self.get_header(file)
                already_shown = any(
                    file_header == shown_header for shown_header in processed_headers
                )

                if not already_shown:
                    print(f"Order {order_num}: {file_header}")
                    print(f"   Files: {os.path.basename(file)}")

                    # Find other files with this header
                    for other_file in different_order_files:
                        if other_file != file:
                            other_header = self.get_header(other_file)
                            if other_header == file_header:
                                print(f"          {os.path.basename(other_file)}")

                    processed_headers.append(file_header)
                    order_num += 1
                    print()

            while True:
                try:
                    choice = input(
                        f"Choose column order (1-{order_num - 1}) or 'q' to quit: "
                    ).strip()
                    if choice.lower() == "q":
                        print("❌ Operation cancelled.")
                        return 1

                    choice_num = int(choice)
                    if 1 <= choice_num <= order_num - 1:
                        break
                    else:
                        print("❌ Invalid choice.")
                        continue
                except ValueError:
                    print("❌ Invalid choice.")
                    continue

            # Get chosen header
            if choice_num == 1:
                chosen_header = reference_header
            else:
                chosen_header = processed_headers[choice_num - 1]

            print()
            # Display summary before joining
            if not self.display_summary(all_files_valid):
                return 1

            if os.path.exists(output_file):
                while True:
                    confirm = input(
                        f"⚠️  Output file '{output_file}' already exists. Overwrite? (y/N): "
                    ).strip()
                    if confirm.lower() in ["y", "yes"]:
                        break
                    elif confirm.lower() in ["n", "no", ""]:
                        print("❌ Operation cancelled.")
                        return 1
                    else:
                        print("Please enter y or N")

            print()
            print("🔗 Joining files with chosen column order...")

            total_rows = self.join_files_different_order(
                all_files_valid, chosen_header, output_file
            )

            print()
            print(f"🎉 Successfully created {output_file} with {total_rows} data rows!")

        return 0


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description="Join CSV files with identical headers"
    )

    args = parser.parse_args()

    joiner = CSVJoiner()
    return joiner.main(args)


if __name__ == "__main__":
    sys.exit(main())
