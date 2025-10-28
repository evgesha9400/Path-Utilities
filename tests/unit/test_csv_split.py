"""
Unit tests for csv_split.py
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.csv_split import split_by_count, split_by_max_rows


class TestCSVSplit(unittest.TestCase):
    """Test cases for CSV Split functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = Path(__file__).parent.parent / "data" / "csv_split" / "input"
        self.expected_output_dir = Path(__file__).parent.parent / "data" / "csv_split" / "expected_output"
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        # Remove any files created in temp_dir
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                os.unlink(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)

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

        for i, (actual_line, expected_line) in enumerate(zip(actual_lines, expected_lines)):
            self.assertEqual(
                actual_line.strip(),
                expected_line.strip(),
                f"Line {i + 1} mismatch:\nActual: {actual_line.strip()}\nExpected: {expected_line.strip()}",
            )

    @patch("builtins.input", return_value="y")
    def test_split_by_count_2_files_contiguous(self, mock_input):
        """Test splitting CSV into 2 files with contiguous distribution."""
        input_file = str(self.test_data_dir / "basic_split.csv")
        base_name = os.path.join(self.temp_dir, "basic_split")

        result = split_by_count(input_file, 2, base_name, "contiguous")
        self.assertTrue(result)

        # Compare outputs
        for i in range(1, 3):
            actual_file = f"{base_name} - Part {i}.csv"
            expected_file = self.expected_output_dir / f"basic_split_2_contiguous_part{i}.csv"
            self.assertTrue(os.path.exists(actual_file))
            self.compare_csv_files(actual_file, str(expected_file))

    @patch("builtins.input", return_value="y")
    def test_split_by_count_2_files_interleaved(self, mock_input):
        """Test splitting CSV into 2 files with interleaved distribution."""
        input_file = str(self.test_data_dir / "basic_split.csv")
        base_name = os.path.join(self.temp_dir, "basic_split")

        result = split_by_count(input_file, 2, base_name, "interleaved")
        self.assertTrue(result)

        # Compare outputs
        for i in range(1, 3):
            actual_file = f"{base_name} - Part {i}.csv"
            expected_file = self.expected_output_dir / f"basic_split_2_interleaved_part{i}.csv"
            self.assertTrue(os.path.exists(actual_file))
            self.compare_csv_files(actual_file, str(expected_file))

    @patch("builtins.input", return_value="y")
    def test_split_by_count_3_files_contiguous(self, mock_input):
        """Test splitting CSV into 3 files with contiguous distribution."""
        input_file = str(self.test_data_dir / "basic_split.csv")
        base_name = os.path.join(self.temp_dir, "basic_split")

        result = split_by_count(input_file, 3, base_name, "contiguous")
        self.assertTrue(result)

        # Compare outputs
        for i in range(1, 4):
            actual_file = f"{base_name} - Part {i}.csv"
            expected_file = self.expected_output_dir / f"basic_split_3_contiguous_part{i}.csv"
            self.assertTrue(os.path.exists(actual_file))
            self.compare_csv_files(actual_file, str(expected_file))

    @patch("builtins.input", return_value="y")
    def test_split_by_count_3_files_interleaved(self, mock_input):
        """Test splitting CSV into 3 files with interleaved distribution."""
        input_file = str(self.test_data_dir / "basic_split.csv")
        base_name = os.path.join(self.temp_dir, "basic_split")

        result = split_by_count(input_file, 3, base_name, "interleaved")
        self.assertTrue(result)

        # Compare outputs
        for i in range(1, 4):
            actual_file = f"{base_name} - Part {i}.csv"
            expected_file = self.expected_output_dir / f"basic_split_3_interleaved_part{i}.csv"
            self.assertTrue(os.path.exists(actual_file))
            self.compare_csv_files(actual_file, str(expected_file))

    @patch("builtins.input", return_value="y")
    def test_split_by_max_rows_contiguous(self, mock_input):
        """Test splitting CSV by max rows with contiguous distribution."""
        input_file = str(self.test_data_dir / "large_split.csv")
        base_name = os.path.join(self.temp_dir, "large_split")

        result = split_by_max_rows(input_file, 5, base_name, "contiguous")
        self.assertTrue(result)

        # Compare outputs
        for i in range(1, 5):
            actual_file = f"{base_name} - Part {i}.csv"
            expected_file = self.expected_output_dir / f"large_split_maxrows5_contiguous_part{i}.csv"
            self.assertTrue(os.path.exists(actual_file))
            self.compare_csv_files(actual_file, str(expected_file))

    @patch("builtins.input", return_value="y")
    def test_split_by_max_rows_interleaved(self, mock_input):
        """Test splitting CSV by max rows with interleaved distribution."""
        input_file = str(self.test_data_dir / "large_split.csv")
        base_name = os.path.join(self.temp_dir, "large_split")

        result = split_by_max_rows(input_file, 5, base_name, "interleaved")
        self.assertTrue(result)

        # Compare outputs
        for i in range(1, 5):
            actual_file = f"{base_name} - Part {i}.csv"
            expected_file = self.expected_output_dir / f"large_split_maxrows5_interleaved_part{i}.csv"
            self.assertTrue(os.path.exists(actual_file))
            self.compare_csv_files(actual_file, str(expected_file))

    @patch("builtins.input", return_value="n")
    def test_split_by_count_cancelled(self, mock_input):
        """Test that split can be cancelled by user."""
        input_file = str(self.test_data_dir / "basic_split.csv")
        base_name = os.path.join(self.temp_dir, "basic_split")

        result = split_by_count(input_file, 2, base_name, "contiguous")
        self.assertFalse(result)

        # Verify no files were created
        for i in range(1, 3):
            actual_file = f"{base_name} - Part {i}.csv"
            self.assertFalse(os.path.exists(actual_file))

    @patch("builtins.input", return_value="y")
    def test_interleaved_distribution_ensures_even_sampling(self, mock_input):
        """Test that interleaved distribution provides even sampling across file."""
        input_file = str(self.test_data_dir / "large_split.csv")
        base_name = os.path.join(self.temp_dir, "large_split")

        result = split_by_count(input_file, 4, base_name, "interleaved")
        self.assertTrue(result)

        # Verify that each file gets rows from throughout the source
        # For 20 rows split into 4 files with interleaved:
        # Part 1: rows 1, 5, 9, 13, 17
        # Part 2: rows 2, 6, 10, 14, 18
        # Part 3: rows 3, 7, 11, 15, 19
        # Part 4: rows 4, 8, 12, 16, 20

        import csv

        for i in range(1, 5):
            actual_file = f"{base_name} - Part {i}.csv"
            with open(actual_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
                # Check that we have 5 data rows plus header
                self.assertEqual(len(rows), 6)  # 5 data rows + 1 header

                # Verify row IDs are distributed correctly
                row_ids = [int(row[0]) for row in rows[1:]]  # Skip header
                expected_ids = list(range(i, 21, 4))  # i, i+4, i+8, i+12, i+16
                self.assertEqual(row_ids, expected_ids)

    @patch("builtins.input", return_value="y")
    def test_split_preserves_headers(self, mock_input):
        """Test that all split files preserve the header."""
        input_file = str(self.test_data_dir / "basic_split.csv")
        base_name = os.path.join(self.temp_dir, "basic_split")

        split_by_count(input_file, 3, base_name, "contiguous")

        import csv

        for i in range(1, 4):
            actual_file = f"{base_name} - Part {i}.csv"
            with open(actual_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                self.assertEqual(header, ["id", "name", "score", "category"])
