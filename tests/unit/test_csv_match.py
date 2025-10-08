"""
Unit tests for csv_match.py
"""

import os
import tempfile
import unittest
from pathlib import Path

from src.csv_match import (
    create_match_key,
    filter_rows_by_match,
    get_column_names,
    match_csv_files,
    parse_column_indices,
    read_csv_with_multi_columns,
)


class TestCSVMatch(unittest.TestCase):
    """Test cases for CSV Match functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = Path(__file__).parent.parent / "data" / "csv_match" / "input"
        self.expected_output_dir = Path(__file__).parent.parent / "data" / "csv_match" / "expected_output"
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

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

    def run_match_test(
        self, file1_name, file2_name, col1_indices, col2_indices, output_type, export_from, expected_output_name
    ):
        """
        Generic test runner for match scenarios.

        :param file1_name: Name of first input file
        :param file2_name: Name of second input file
        :param col1_indices: Column indices for file1 (1-based, comma-separated string)
        :param col2_indices: Column indices for file2 (1-based, comma-separated string)
        :param output_type: "matching" or "non_matching"
        :param export_from: "file1" or "file2"
        :param expected_output_name: Name of expected output file
        """
        file1 = str(self.test_data_dir / file1_name)
        file2 = str(self.test_data_dir / file2_name)

        # Change to temp directory to capture output
        original_dir = os.getcwd()
        os.chdir(self.temp_dir)

        try:
            match_csv_files(
                file1,
                file2,
                col1_indices,
                col2_indices,
                output_type,
                export_from,
                "test",  # base_name
                "export_only",  # show_summary
            )

            # Find the generated output file (created in same dir as input)
            export_file = file1 if export_from == "file1" else file2
            source_basename = Path(export_file).stem
            suffix = "matching_rows" if output_type == "matching" else "non_matching_rows"
            # Files are created in the input directory, not temp
            actual_output = str(self.test_data_dir / f"{source_basename}_{suffix}.csv")

            # Compare with expected output
            expected_output = str(self.expected_output_dir / expected_output_name)
            self.compare_csv_files(actual_output, expected_output)

            # Clean up the generated file
            if os.path.exists(actual_output):
                os.remove(actual_output)

        finally:
            os.chdir(original_dir)

    # Core Functionality Tests

    def test_single_column_matching_basic(self):
        """Test basic single column matching."""
        self.run_match_test(
            "file1_basic.csv",
            "file2_basic.csv",
            "1",  # id column
            "1",  # user_id column
            "matching",
            "file1",
            "file1_basic_matching_rows.csv",
        )

    def test_multi_column_matching(self):
        """Test multiple column composite key matching."""
        self.run_match_test(
            "file1_multi_col.csv",
            "file2_multi_col.csv",
            "1,2",  # first_name, last_name
            "1,2",  # fname, lname
            "matching",
            "file1",
            "file1_multi_col_matching_rows.csv",
        )

    def test_matching_rows_export(self):
        """Test exporting only matching rows."""
        self.run_match_test(
            "file1_basic.csv", "file2_basic.csv", "1", "1", "matching", "file1", "file1_basic_matching_rows.csv"
        )

    def test_non_matching_rows_export(self):
        """Test exporting only non-matching rows."""
        self.run_match_test(
            "file1_basic.csv", "file2_basic.csv", "1", "1", "non_matching", "file1", "file1_basic_non_matching_rows.csv"
        )

    def test_export_from_file1(self):
        """Test exporting from first file."""
        self.run_match_test(
            "file1_basic.csv", "file2_basic.csv", "1", "1", "matching", "file1", "file1_basic_matching_rows.csv"
        )

    def test_export_from_file2(self):
        """Test exporting from second file."""
        self.run_match_test(
            "file1_basic.csv", "file2_basic.csv", "1", "1", "matching", "file2", "file2_basic_matching_rows.csv"
        )

    # Special Conditions Tests

    def test_special_characters_in_headers(self):
        """Test special characters in column headers."""
        self.run_match_test(
            "file1_special_chars.csv",
            "file2_special_chars.csv",
            "1",  # user@id
            "1",  # id@user
            "matching",
            "file1",
            "file1_special_chars_matching_rows.csv",
        )

    def test_special_characters_in_values(self):
        """Test special characters in data values."""
        # Same test as above, verifies values are preserved
        self.run_match_test(
            "file1_special_chars.csv",
            "file2_special_chars.csv",
            "1",
            "1",
            "matching",
            "file1",
            "file1_special_chars_matching_rows.csv",
        )

    def test_spaces_in_headers(self):
        """Test handling of spaces in column headers."""
        # Headers with leading/trailing spaces should still work
        file1 = str(self.test_data_dir / "file1_spaces.csv")
        file2 = str(self.test_data_dir / "file2_spaces.csv")

        data1, headers1, _ = read_csv_with_multi_columns(file1, [0])
        data2, headers2, _ = read_csv_with_multi_columns(file2, [0])

        # Verify headers are read correctly (even with spaces)
        self.assertIn("name", [h.strip() for h in headers1])
        self.assertIn("name", [h.strip() for h in headers2])

    def test_spaces_in_values(self):
        """Test space trimming in match values."""
        self.run_match_test(
            "file1_spaces.csv",
            "file2_spaces.csv",
            "1",  # name column (with spaces)
            "1",  # name column (with spaces)
            "matching",
            "file1",
            "file1_spaces_matching_rows.csv",
        )

    def test_multiline_values(self):
        """Test handling of newlines in CSV fields."""
        self.run_match_test(
            "file1_multiline.csv",
            "file2_multiline.csv",
            "1",  # id
            "1",  # user_id
            "matching",
            "file1",
            "file1_multiline_matching_rows.csv",
        )

    def test_empty_lines_handling(self):
        """Test that empty lines are read as rows with empty values."""
        file1 = str(self.test_data_dir / "file1_empty_lines.csv")
        file2 = str(self.test_data_dir / "file2_empty_lines.csv")

        data1, _, _ = read_csv_with_multi_columns(file1, [0])
        data2, _, _ = read_csv_with_multi_columns(file2, [0])

        # CSV reader reads empty lines as rows
        # This is expected behavior - empty lines become rows with empty values
        self.assertGreater(len(data1), 0)
        self.assertGreater(len(data2), 0)

    def test_unicode_characters(self):
        """Test Unicode character handling and encoding."""
        self.run_match_test(
            "file1_unicode.csv",
            "file2_unicode.csv",
            "1",  # id
            "1",  # user_id
            "matching",
            "file1",
            "file1_unicode_matching_rows.csv",
        )

    def test_headers_only_files(self):
        """Test files with only headers (and possible trailing newline)."""
        file1 = str(self.test_data_dir / "file1_headers_only.csv")
        file2 = str(self.test_data_dir / "file2_headers_only.csv")

        data1, headers1, _ = read_csv_with_multi_columns(file1, [0])
        data2, headers2, _ = read_csv_with_multi_columns(file2, [0])

        # Should have headers
        self.assertGreater(len(headers1), 0)
        self.assertGreater(len(headers2), 0)
        # May have 0 or 1 row (if trailing newline creates empty row)
        self.assertLessEqual(len(data1), 1)
        self.assertLessEqual(len(data2), 1)

    def test_single_row_files(self):
        """Test minimal CSV files with just one data row (plus possible trailing newline)."""
        file1 = str(self.test_data_dir / "file1_single_row.csv")
        file2 = str(self.test_data_dir / "file2_single_row.csv")

        data1, _, match_values1 = read_csv_with_multi_columns(file1, [0])
        data2, _, match_values2 = read_csv_with_multi_columns(file2, [0])

        # Each should have 1 or 2 rows (if trailing newline creates empty row)
        self.assertGreaterEqual(len(data1), 1)
        self.assertLessEqual(len(data1), 2)
        self.assertGreaterEqual(len(data2), 1)
        self.assertLessEqual(len(data2), 2)

        # They should have matching ids (both have id=1)
        self.assertTrue(len(match_values1 & match_values2) > 0)

    def test_composite_key_order(self):
        """Test that multi-column order is preserved in composite keys."""
        # Test that John§§§Doe matches, but Doe§§§John would not
        data, _, match_values = read_csv_with_multi_columns(
            str(self.test_data_dir / "file1_multi_col.csv"),
            [0, 1],  # first_name, last_name
        )

        # Create expected composite key
        expected_key = "John§§§Doe"
        self.assertIn(expected_key, match_values)

        # Reversed order should NOT be in match values (unless it exists in data)
        reversed_key = "Doe§§§John"
        self.assertNotIn(reversed_key, match_values)

    def test_empty_columns(self):
        """Test handling of completely empty columns."""
        # file1_spaces has some rows with empty/whitespace-only values
        file1 = str(self.test_data_dir / "file1_spaces.csv")
        data, headers, _ = read_csv_with_multi_columns(file1, [2])  # phone column

        # Should handle empty values gracefully
        self.assertGreater(len(data), 0)

    def test_whitespace_vs_empty(self):
        """Test distinction between whitespace-only and truly empty values."""
        # Whitespace should be stripped in match keys
        row_values1 = ["  John Doe  ", "test@example.com"]
        row_values2 = ["John Doe", "test@example.com"]

        key1 = create_match_key(row_values1, [0])
        key2 = create_match_key(row_values2, [0])

        # After stripping, they should match
        self.assertEqual(key1, key2)

    # Helper Function Tests

    def test_parse_column_indices(self):
        """Test parsing of column indices from string."""
        # Single column
        indices = parse_column_indices("1")
        self.assertEqual(indices, [0])  # 0-based

        # Multiple columns
        indices = parse_column_indices("1,3,5")
        self.assertEqual(indices, [0, 2, 4])  # 0-based

        # With spaces
        indices = parse_column_indices("1, 2, 3")
        self.assertEqual(indices, [0, 1, 2])

    def test_create_match_key(self):
        """Test creation of composite match keys."""
        row_values = ["John", "Doe", "john@example.com"]

        # Single column key
        key = create_match_key(row_values, [0])
        self.assertEqual(key, "John")

        # Multi-column key
        key = create_match_key(row_values, [0, 1])
        self.assertEqual(key, "John§§§Doe")

        # All columns
        key = create_match_key(row_values, [0, 1, 2])
        self.assertEqual(key, "John§§§Doe§§§john@example.com")

    def test_filter_rows_by_match(self):
        """Test filtering rows based on match criteria."""
        export_data = [
            {"id": "1", "name": "John"},
            {"id": "2", "name": "Jane"},
            {"id": "3", "name": "Bob"},
        ]
        reference_match_values = {"1", "3"}

        # Test matching filter (include_matches=True)
        matching = filter_rows_by_match(export_data, [0], reference_match_values, True)
        self.assertEqual(len(matching), 2)
        self.assertEqual(matching[0]["id"], "1")
        self.assertEqual(matching[1]["id"], "3")

        # Test non-matching filter (include_matches=False)
        non_matching = filter_rows_by_match(export_data, [0], reference_match_values, False)
        self.assertEqual(len(non_matching), 1)
        self.assertEqual(non_matching[0]["id"], "2")

    def test_get_column_names(self):
        """Test retrieval of column names from headers."""
        headers = ["id", "name", "email", "status"]

        # Single column
        names = get_column_names(headers, [0])
        self.assertEqual(names, ["id"])

        # Multiple columns
        names = get_column_names(headers, [1, 3])
        self.assertEqual(names, ["name", "status"])

        # Out of range index (should return placeholder)
        names = get_column_names(headers, [10])
        self.assertEqual(names, ["Column_11"])  # 1-based for display


if __name__ == "__main__":
    unittest.main()
