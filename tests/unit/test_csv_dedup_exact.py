"""
Unit tests for csv_dedup_exact.py
"""

import os
import tempfile
import unittest
from pathlib import Path

from src.csv_dedup.csv_dedup_exact import (
    analyze_exact_duplicates,
    auto_deduplication,
    read_csv_data,
    write_csv_data,
)


class TestCSVDedupExact(unittest.TestCase):
    """Test cases for CSV Exact Deduplication functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = (
            Path(__file__).parent.parent / "data" / "csv_dedup" / "exact" / "input"
        )
        self.expected_output_dir = (
            Path(__file__).parent.parent
            / "data"
            / "csv_dedup"
            / "exact"
            / "expected_output"
        )

    def compare_csv_files(self, actual_file, expected_file):
        """Compare two CSV files line by line."""
        with open(actual_file, "r", encoding="utf-8") as f:
            actual_lines = f.readlines()
        with open(expected_file, "r", encoding="utf-8") as f:
            expected_lines = f.readlines()

        self.assertEqual(
            len(actual_lines),
            len(expected_lines),
            f"File line count mismatch: {len(actual_lines)} vs {len(expected_lines)}",
        )

        for i, (actual_line, expected_line) in enumerate(
            zip(actual_lines, expected_lines)
        ):
            self.assertEqual(
                actual_line.strip(),
                expected_line.strip(),
                f"Line {i + 1} mismatch:\nActual: {actual_line.strip()}\nExpected: {expected_line.strip()}",
            )

    def test_read_csv_data_basic(self):
        """Test basic CSV data reading functionality."""
        # Create a test CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,email,phone\n")
            f.write("John,john@example.com,555-1234\n")
            f.write("Jane,jane@example.com,555-5678\n")

        try:
            data, headers = read_csv_data(f.name)

            self.assertEqual(headers, ["name", "email", "phone"])
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0][0], ["John", "john@example.com", "555-1234"])
            self.assertEqual(data[1][0], ["Jane", "jane@example.com", "555-5678"])
            # Check line numbers (1-based after header)
            self.assertEqual(data[0][1], 2)
            self.assertEqual(data[1][1], 3)
        finally:
            os.unlink(f.name)

    def test_read_csv_data_with_empty_values(self):
        """Test CSV reading with empty values."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,email,phone\n")
            f.write("John,,555-1234\n")
            f.write(",jane@example.com,\n")
            f.write("Bob,bob@test.com,\n")

        try:
            data, headers = read_csv_data(f.name)

            self.assertEqual(len(data), 3)
            self.assertEqual(data[0][0], ["John", "", "555-1234"])
            self.assertEqual(data[1][0], ["", "jane@example.com", ""])
            self.assertEqual(data[2][0], ["Bob", "bob@test.com", ""])
        finally:
            os.unlink(f.name)

    def test_read_csv_data_with_multiline_strings(self):
        """Test CSV reading with multiline strings."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,notes\n")
            f.write('John,"Single line notes"\n')
            f.write('Jane,"Multi-line\nnotes with\nnewlines"\n')
            f.write('Bob,"Notes with, comma, inside"\n')

        try:
            data, headers = read_csv_data(f.name)

            self.assertEqual(len(data), 3)
            self.assertEqual(data[0][0], ["John", "Single line notes"])
            self.assertEqual(data[1][0], ["Jane", "Multi-line\nnotes with\nnewlines"])
            self.assertEqual(data[2][0], ["Bob", "Notes with, comma, inside"])
        finally:
            os.unlink(f.name)

    def test_read_csv_data_with_special_characters(self):
        """Test CSV reading with special characters."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,special_chars\n")
            f.write('John,"@#$%^&*()"\n')
            f.write('Jane,"Unicode: éñçü"\n')
            f.write('Bob,"Tabs:\tand\nnewlines"\n')

        try:
            data, headers = read_csv_data(f.name)

            self.assertEqual(len(data), 3)
            self.assertEqual(data[0][0], ["John", "@#$%^&*()"])
            self.assertEqual(data[1][0], ["Jane", "Unicode: éñçü"])
            self.assertEqual(data[2][0], ["Bob", "Tabs:\tand\nnewlines"])
        finally:
            os.unlink(f.name)

    def test_read_csv_data_with_whitespace(self):
        """Test CSV reading with whitespace handling."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,email,phone\n")
            f.write(" John , john@example.com , 555-1234 \n")
            f.write("\tJane\t,\tjane@example.com\t,\t555-5678\t\n")
            f.write("  Bob  ,  bob@test.com  ,  555-9999  \n")

        try:
            data, headers = read_csv_data(f.name)

            self.assertEqual(len(data), 3)
            # Note: read_csv_data doesn't strip whitespace from individual cells
            self.assertEqual(data[0][0], [" John ", " john@example.com ", " 555-1234 "])
            self.assertEqual(
                data[1][0], ["\tJane\t", "\tjane@example.com\t", "\t555-5678\t"]
            )
            self.assertEqual(
                data[2][0], ["  Bob  ", "  bob@test.com  ", "  555-9999  "]
            )
        finally:
            os.unlink(f.name)

    def test_write_csv_data(self):
        """Test CSV data writing functionality."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,email\n")

        try:
            headers = ["name", "email"]
            rows = [["John", "john@example.com"], ["Jane", "jane@example.com"]]

            write_csv_data(f.name, rows, headers)

            # Read back and verify
            with open(f.name, "r", encoding="utf-8") as f_read:
                content = f_read.read()
                expected = "name,email\nJohn,john@example.com\nJane,jane@example.com\n"
                self.assertEqual(content, expected)
        finally:
            os.unlink(f.name)

    def test_analyze_exact_duplicates_no_duplicates(self):
        """Test analysis when no exact duplicates exist."""
        test_file = self.test_data_dir / "no_duplicates.csv"

        # Capture print output
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            duplicate_count = analyze_exact_duplicates(str(test_file))

        self.assertEqual(duplicate_count, 0)
        output_str = output.getvalue()
        self.assertIn("No exact duplicates found!", output_str)
        self.assertIn("All 3 rows are unique.", output_str)

    def test_analyze_exact_duplicates_with_duplicates(self):
        """Test analysis when exact duplicates exist."""
        test_file = self.test_data_dir / "basic_duplicates.csv"

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            duplicate_count = analyze_exact_duplicates(str(test_file))

        self.assertEqual(duplicate_count, 2)  # 2 duplicate rows
        output_str = output.getvalue()
        self.assertIn("Total duplicate rows to remove: 2", output_str)
        self.assertIn("Final row count after deduplication: 3", output_str)

    def test_analyze_exact_duplicates_with_whitespace_differences(self):
        """Test that whitespace differences are ignored in duplicate detection."""
        test_file = self.test_data_dir / "whitespace_differences.csv"

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            duplicate_count = analyze_exact_duplicates(str(test_file))

        self.assertEqual(duplicate_count, 1)  # 1 duplicate row (whitespace ignored)
        output_str = output.getvalue()
        self.assertIn("Total duplicate rows to remove: 1", output_str)

    def test_auto_deduplication_keep_first(self):
        """Test automatic deduplication keeping first occurrence."""
        input_file = self.test_data_dir / "basic_duplicates.csv"
        expected_output = self.expected_output_dir / "basic_duplicates_first.csv"

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_output:
            output_file = temp_output.name

        try:
            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                auto_deduplication(str(input_file), output_file)

            # Compare with expected output
            self.compare_csv_files(output_file, str(expected_output))

            # Check output message
            output_str = output.getvalue()
            self.assertIn("Rows removed: 2", output_str)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_auto_deduplication_with_multiline_strings(self):
        """Test automatic deduplication with multiline strings."""
        input_file = self.test_data_dir / "multiline_strings.csv"
        expected_output = self.expected_output_dir / "multiline_strings_first.csv"

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_output:
            output_file = temp_output.name

        try:
            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                auto_deduplication(str(input_file), output_file)

            # Compare with expected output
            self.compare_csv_files(output_file, str(expected_output))
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_auto_deduplication_with_special_characters(self):
        """Test automatic deduplication with special characters."""
        input_file = self.test_data_dir / "special_characters.csv"
        expected_output = self.expected_output_dir / "special_characters_first.csv"

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_output:
            output_file = temp_output.name

        try:
            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                auto_deduplication(str(input_file), output_file)

            # Compare with expected output
            self.compare_csv_files(output_file, str(expected_output))
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_empty_file_handling(self):
        """Test handling of empty CSV files."""
        test_file = self.test_data_dir / "empty_file.csv"

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            duplicate_count = analyze_exact_duplicates(str(test_file))

        self.assertEqual(duplicate_count, 0)

    def test_csv_with_only_headers(self):
        """Test CSV file with only headers and no data."""
        test_file = self.test_data_dir / "headers_only.csv"

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            duplicate_count = analyze_exact_duplicates(str(test_file))

        self.assertEqual(duplicate_count, 0)
        output_str = output.getvalue()
        self.assertIn("No exact duplicates found!", output_str)
        self.assertIn("All 0 rows are unique.", output_str)

    def test_encoding_handling(self):
        """Test that different encodings are handled properly."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("name,email\n")
            f.write("John,john@example.com\n")
            f.write("José,josé@example.com\n")  # Unicode characters
            f.write("John,john@example.com\n")  # Duplicate

        try:
            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                duplicate_count = analyze_exact_duplicates(f.name)

            self.assertEqual(duplicate_count, 1)
        finally:
            os.unlink(f.name)

    def test_large_duplicate_groups(self):
        """Test handling of large groups of duplicates."""
        test_file = self.test_data_dir / "large_duplicate_groups.csv"

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            duplicate_count = analyze_exact_duplicates(str(test_file))

        self.assertEqual(duplicate_count, 4)  # 4 duplicate rows (5 total - 1 unique)
        output_str = output.getvalue()
        self.assertIn("Total duplicate rows to remove: 4", output_str)
        self.assertIn("Final row count after deduplication: 2", output_str)
