"""
Unit tests for csv_dedup_single.py
"""

import os
import tempfile
import unittest
from pathlib import Path

from src.csv_dedup.csv_dedup_single import (
    analyze_single_duplicates,
    auto_deduplication,
    count_filled_columns,
    read_csv_data,
)


class TestCSVDedupSingle(unittest.TestCase):
    """Test cases for CSV Single Column Deduplication functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = (
            Path(__file__).parent.parent / "data" / "csv_dedup" / "single" / "input"
        )
        self.expected_output_dir = (
            Path(__file__).parent.parent
            / "data"
            / "csv_dedup"
            / "single"
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

    def test_count_filled_columns(self):
        """Test counting filled columns functionality."""
        # Test with all filled columns
        row1 = ["John", "john@example.com", "555-1234"]
        self.assertEqual(count_filled_columns(row1), 3)

        # Test with some empty columns
        row2 = ["Jane", "", "555-5678"]
        self.assertEqual(count_filled_columns(row2), 2)

        # Test with whitespace-only columns
        row3 = ["Bob", "   ", "\t", "555-9999"]
        self.assertEqual(count_filled_columns(row3), 2)  # Only "Bob" and "555-9999"

        # Test with all empty columns
        row4 = ["", "", ""]
        self.assertEqual(count_filled_columns(row4), 0)

    def test_read_csv_data_basic(self):
        """Test basic CSV data reading functionality."""
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
        finally:
            os.unlink(f.name)

    def test_analyze_single_duplicates_no_duplicates(self):
        """Test analysis when no single-column duplicates exist."""
        test_file = self.test_data_dir / "no_duplicates.csv"

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            duplicate_count = analyze_single_duplicates(
                str(test_file), 1
            )  # email column

        self.assertEqual(duplicate_count, 0)
        output_str = output.getvalue()
        self.assertIn("No duplicates found!", output_str)
        self.assertIn('All 3 rows have unique values in "email".', output_str)

    def test_analyze_single_duplicates_with_duplicates(self):
        """Test analysis when single-column duplicates exist."""
        test_file = self.test_data_dir / "basic_duplicates.csv"

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            duplicate_count = analyze_single_duplicates(
                str(test_file), 1
            )  # email column

        self.assertEqual(duplicate_count, 1)  # 1 duplicate row
        output_str = output.getvalue()
        self.assertIn("Total duplicate rows to remove: 1", output_str)
        self.assertIn("Final row count after deduplication: 3", output_str)

    def test_auto_deduplication_first_strategy(self):
        """Test automatic deduplication with 'first' strategy."""
        input_file = self.test_data_dir / "basic_duplicates.csv"
        expected_output = self.expected_output_dir / "basic_duplicates_first.csv"

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_output:
            output_file = temp_output.name

        try:
            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                auto_deduplication(
                    str(input_file), 1, "first", output_file
                )  # email column

            # Compare with expected output
            self.compare_csv_files(output_file, str(expected_output))

            output_str = output.getvalue()
            self.assertIn("Strategy: first", output_str)
            self.assertIn("Rows removed: 1", output_str)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_auto_deduplication_best_strategy(self):
        """Test automatic deduplication with 'best' strategy (most filled columns)."""
        input_file = self.test_data_dir / "best_strategy.csv"
        expected_output = self.expected_output_dir / "best_strategy_best.csv"

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_output:
            output_file = temp_output.name

        try:
            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                auto_deduplication(
                    str(input_file), 1, "best", output_file
                )  # email column

            # Compare with expected output
            self.compare_csv_files(output_file, str(expected_output))

            output_str = output.getvalue()
            self.assertIn("Strategy: best", output_str)
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
                auto_deduplication(
                    str(input_file), 2, "first", output_file
                )  # email column

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
                auto_deduplication(
                    str(input_file), 2, "first", output_file
                )  # email column

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
            duplicate_count = analyze_single_duplicates(str(test_file), 0)

        self.assertEqual(duplicate_count, 0)

    def test_csv_with_only_headers(self):
        """Test CSV file with only headers and no data."""
        test_file = self.test_data_dir / "headers_only.csv"

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            duplicate_count = analyze_single_duplicates(
                str(test_file), 1
            )  # email column

        self.assertEqual(duplicate_count, 0)
        output_str = output.getvalue()
        self.assertIn("No duplicates found!", output_str)
        self.assertIn('All 0 rows have unique values in "email".', output_str)

    def test_encoding_handling(self):
        """Test that different encodings are handled properly."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("name,email\n")
            f.write("John,john@example.com\n")
            f.write("José,josé@example.com\n")  # Unicode characters
            f.write("John2,john@example.com\n")  # Duplicate

        try:
            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                duplicate_count = analyze_single_duplicates(f.name, 1)  # email column

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
            duplicate_count = analyze_single_duplicates(
                str(test_file), 1
            )  # email column

        self.assertEqual(duplicate_count, 4)  # 4 duplicate rows (5 total - 1 unique)
        output_str = output.getvalue()
        self.assertIn("Total duplicate rows to remove: 4", output_str)
        self.assertIn("Final row count after deduplication: 2", output_str)
