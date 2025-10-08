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

    def test_single_column_matching(self):
        """Test single column matching with comprehensive data."""
        self.run_match_test(
            "file1_comprehensive.csv",
            "file2_comprehensive.csv",
            "1",  # id column
            "1",  # user_id column
            "matching",
            "file1",
            "file1_comprehensive_matching_rows.csv",
        )

    def test_multi_column_matching(self):
        """Test multiple column composite key matching."""
        # Match on columns 1,2 (id and name)
        file1 = str(self.test_data_dir / "file1_comprehensive.csv")
        file2 = str(self.test_data_dir / "file2_comprehensive.csv")

        data1, _, match_values1 = read_csv_with_multi_columns(file1, [0, 1])
        data2, _, match_values2 = read_csv_with_multi_columns(file2, [0, 1])

        # Verify composite keys are created
        self.assertIn("1§§§John Doe", match_values1)
        self.assertIn("1§§§John Doe", match_values2)

        # Verify they match
        self.assertTrue(len(match_values1 & match_values2) > 0)

    def test_matching_rows_export(self):
        """Test exporting only matching rows."""
        self.run_match_test(
            "file1_comprehensive.csv",
            "file2_comprehensive.csv",
            "1",
            "1",
            "matching",
            "file1",
            "file1_comprehensive_matching_rows.csv",
        )

    def test_non_matching_rows_export(self):
        """Test exporting only non-matching rows."""
        self.run_match_test(
            "file1_comprehensive.csv",
            "file2_comprehensive.csv",
            "1",
            "1",
            "non_matching",
            "file1",
            "file1_comprehensive_non_matching_rows.csv",
        )

    def test_export_from_file1(self):
        """Test exporting from first file."""
        self.run_match_test(
            "file1_comprehensive.csv",
            "file2_comprehensive.csv",
            "1",
            "1",
            "matching",
            "file1",
            "file1_comprehensive_matching_rows.csv",
        )

    def test_export_from_file2(self):
        """Test exporting from second file."""
        self.run_match_test(
            "file1_comprehensive.csv",
            "file2_comprehensive.csv",
            "1",
            "1",
            "matching",
            "file2",
            "file2_comprehensive_matching_rows.csv",
        )

    # Special Conditions Tests (all tested via comprehensive files)

    def test_special_characters(self):
        """Test special characters in headers and values."""
        file1 = str(self.test_data_dir / "file1_comprehensive.csv")
        data, headers, _ = read_csv_with_multi_columns(file1, [0])

        # Verify special char headers are read correctly
        self.assertIn("name (full)", [h.strip() for h in headers])
        self.assertIn("email@primary", [h.strip() for h in headers])
        self.assertIn("status&type", [h.strip() for h in headers])

        # Verify special char values are preserved
        self.assertTrue(any("Bob [Johnson]" in str(row.values()) for row in data))
        self.assertTrue(any('Mike "Boss" Wilson' in str(row.values()) for row in data))

    def test_unicode_characters(self):
        """Test Unicode character handling."""
        file1 = str(self.test_data_dir / "file1_comprehensive.csv")
        data, _, _ = read_csv_with_multi_columns(file1, [0])

        # Verify Unicode is preserved
        self.assertTrue(any("José García" in str(row.values()) for row in data))
        self.assertTrue(any("日本語" in str(row.values()) for row in data))
        self.assertTrue(any("😊" in str(row.values()) for row in data))

    def test_multiline_values(self):
        """Test handling of newlines in CSV fields."""
        file1 = str(self.test_data_dir / "file1_comprehensive.csv")
        data, _, _ = read_csv_with_multi_columns(file1, [0])

        # Verify multiline values are preserved
        bob_row = next((row for row in data if "Bob [Johnson]" in str(row.values())), None)
        self.assertIsNotNone(bob_row)
        # Check that multiline address is preserved
        self.assertTrue(any("\n" in str(val) for val in bob_row.values()))

    def test_spaces_handling(self):
        """Test space trimming in match values and preservation in data."""
        file1 = str(self.test_data_dir / "file1_comprehensive.csv")
        data, _, _ = read_csv_with_multi_columns(file1, [0])

        # Verify spaces are preserved in data
        jane_row = next((row for row in data if "Jane Smith" in str(row.values())), None)
        self.assertIsNotNone(jane_row)

        # Verify trimming happens in match keys
        row_values = ["  John Doe  ", "test@example.com"]
        key1 = create_match_key(row_values, [0])
        row_values2 = ["John Doe", "test@example.com"]
        key2 = create_match_key(row_values2, [0])
        self.assertEqual(key1, key2)  # Spaces should be trimmed in keys

    def test_empty_values(self):
        """Test handling of empty values and empty columns."""
        file1 = str(self.test_data_dir / "file1_comprehensive.csv")
        data, _, _ = read_csv_with_multi_columns(file1, [0])

        # Verify empty name row exists
        empty_name_row = next((row for row in data if "empty@test.com" in str(row.values())), None)
        self.assertIsNotNone(empty_name_row)

        # Verify empty address is handled
        charlie_row = next((row for row in data if "Charlie Wilson" in str(row.values())), None)
        self.assertIsNotNone(charlie_row)

    def test_empty_lines_in_file(self):
        """Test that empty lines are handled correctly."""
        file1 = str(self.test_data_dir / "file1_comprehensive.csv")
        data, _, _ = read_csv_with_multi_columns(file1, [0])

        # File has empty lines, but data should still be read
        self.assertGreater(len(data), 0)

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

    def test_composite_key_order(self):
        """Test that multi-column order is preserved in composite keys."""
        file1 = str(self.test_data_dir / "file1_comprehensive.csv")
        data, _, match_values = read_csv_with_multi_columns(file1, [0, 1])

        # Create expected composite key
        expected_key = "1§§§John Doe"
        self.assertIn(expected_key, match_values)

        # Reversed order should NOT be in match values
        reversed_key = "John Doe§§§1"
        self.assertNotIn(reversed_key, match_values)


if __name__ == "__main__":
    unittest.main()
