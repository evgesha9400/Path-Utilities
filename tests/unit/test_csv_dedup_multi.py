"""
Unit tests for csv_dedup_multi.py
"""

import os
import tempfile
import unittest
from pathlib import Path

from src.csv_dedup.csv_dedup_multi import (
    analyze_multi_duplicates,
    auto_deduplication,
    count_filled_columns,
)


class TestCSVDedupMulti(unittest.TestCase):
    """Test cases for CSV Multi-Column Deduplication functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = (
            Path(__file__).parent.parent / "data" / "csv_dedup" / "multi" / "input"
        )
        self.expected_output_dir = (
            Path(__file__).parent.parent
            / "data"
            / "csv_dedup"
            / "multi"
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
        row1 = ["John", "Doe", "john@example.com", "555-1234"]
        self.assertEqual(count_filled_columns(row1), 4)

        # Test with some empty columns
        row2 = ["Jane", "", "jane@example.com", ""]
        self.assertEqual(count_filled_columns(row2), 2)

        # Test with whitespace-only columns
        row3 = ["Bob", "   ", "\t", "555-9999"]
        self.assertEqual(count_filled_columns(row3), 2)  # Only "Bob" and "555-9999"

        # Test with all empty columns
        row4 = ["", "", "", ""]
        self.assertEqual(count_filled_columns(row4), 0)

    def test_analyze_multi_duplicates_no_duplicates(self):
        """Test analysis when no multi-column duplicates exist."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("first_name,last_name,email,phone\n")
            f.write("John,Doe,john@example.com,555-1234\n")
            f.write("Jane,Smith,jane@example.com,555-5678\n")
            f.write("Bob,Johnson,bob@example.com,555-9999\n")

        try:
            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                duplicate_count = analyze_multi_duplicates(
                    f.name, [0, 1]
                )  # first_name + last_name

            self.assertEqual(duplicate_count, 0)
            output_str = output.getvalue()
            self.assertIn("No duplicates found!", output_str)
            self.assertIn(
                "All 3 rows have unique combinations of the selected columns.",
                output_str,
            )
        finally:
            os.unlink(f.name)

    def test_analyze_multi_duplicates_with_duplicates(self):
        """Test analysis when multi-column duplicates exist."""
        test_file = self.test_data_dir / "basic_duplicates.csv"

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            duplicate_count = analyze_multi_duplicates(
                str(test_file), [0, 1]
            )  # first_name + last_name

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
                    str(input_file), [0, 1], "first", output_file
                )  # first_name + last_name

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
                    str(input_file), [0, 1], "best", output_file
                )  # first_name + last_name

            # Compare with expected output
            self.compare_csv_files(output_file, str(expected_output))

            output_str = output.getvalue()
            self.assertIn("Strategy: best", output_str)
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
            duplicate_count = analyze_multi_duplicates(str(test_file), [0, 1])

        self.assertEqual(duplicate_count, 0)

    def test_large_duplicate_groups(self):
        """Test handling of large groups of duplicates."""
        test_file = self.test_data_dir / "large_duplicate_groups.csv"

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            duplicate_count = analyze_multi_duplicates(
                str(test_file), [0, 1]
            )  # first_name + last_name

        self.assertEqual(duplicate_count, 4)  # 4 duplicate rows (5 total - 1 unique)
        output_str = output.getvalue()
        self.assertIn("Total duplicate rows to remove: 4", output_str)
        self.assertIn("Final row count after deduplication: 2", output_str)
