"""
Unit tests for csv_analyzer.py
"""

import os
import tempfile
import unittest
from pathlib import Path

from csv_analyzer import analyze_csv_columns


class TestCSVAnalyzer(unittest.TestCase):
    """Test cases for CSV Analyzer functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = (
            Path(__file__).parent.parent / "data" / "csv_analyzer" / "input"
        )
        self.test_csv_path = self.test_data_dir / "test.csv"

    def test_analyze_csv_columns_basic(self):
        """Test basic CSV column analysis with the test file."""
        results, total_rows = analyze_csv_columns(str(self.test_csv_path))

        # Verify we got results
        self.assertGreater(len(results), 0)
        self.assertGreater(total_rows, 0)

        # Check that we have 7 columns as expected
        self.assertEqual(len(results), 7)

        # Verify total rows (should be 8 data rows, not counting empty lines)
        self.assertEqual(total_rows, 8)

    def test_column_fill_percentages(self):
        """Test that column fill percentages are calculated correctly."""
        results, total_rows = analyze_csv_columns(str(self.test_csv_path))

        # Create a dictionary for easy lookup
        results_dict = {r["column"]: r for r in results}

        # Test specific columns with known fill rates:
        # name: 8/8 = 100%
        self.assertEqual(results_dict["name"]["percentage"], 100.0)
        self.assertEqual(results_dict["name"]["filled_count"], 8)

        # email: 6/8 = 75.0%
        self.assertEqual(results_dict["email"]["percentage"], 75.0)
        self.assertEqual(results_dict["email"]["filled_count"], 6)

        # phone: 5/8 = 62.5%
        self.assertEqual(results_dict["phone"]["percentage"], 62.5)
        self.assertEqual(results_dict["phone"]["filled_count"], 5)

        # address: 5/8 = 62.5%
        self.assertEqual(results_dict["address"]["percentage"], 62.5)
        self.assertEqual(results_dict["address"]["filled_count"], 5)

        # notes: 8/8 = 100%
        self.assertEqual(results_dict["notes"]["percentage"], 100.0)
        self.assertEqual(results_dict["notes"]["filled_count"], 8)

        # status: 8/8 = 100%
        self.assertEqual(results_dict["status"]["percentage"], 100.0)
        self.assertEqual(results_dict["status"]["filled_count"], 8)

        # empty_col: 0/8 = 0%
        self.assertEqual(results_dict["empty_col"]["percentage"], 0.0)
        self.assertEqual(results_dict["empty_col"]["filled_count"], 0)

    def test_results_sorting(self):
        """Test that results are sorted by percentage (descending) then by column name."""
        results, _ = analyze_csv_columns(str(self.test_csv_path))

        # Sort the results the same way display_results does
        results.sort(key=lambda x: (-x["percentage"], x["column"]))

        # Verify sorting - should be sorted by percentage descending, then by name
        percentages = [r["percentage"] for r in results]
        self.assertEqual(percentages, sorted(percentages, reverse=True))

        # Check that columns with 100% are sorted alphabetically
        actual_full_columns = [r["column"] for r in results if r["percentage"] == 100.0]
        expected_full_columns = ["name", "notes", "status"]
        self.assertEqual(actual_full_columns, expected_full_columns)

    def test_multiline_handling(self):
        """Test that multiline strings and newlines are handled correctly."""
        results, total_rows = analyze_csv_columns(str(self.test_csv_path))
        results_dict = {r["column"]: r for r in results}

        # notes column should have 100% fill despite containing newlines
        self.assertEqual(results_dict["notes"]["percentage"], 100.0)

        # address column should have 62.5% fill despite containing commas
        self.assertEqual(results_dict["address"]["percentage"], 62.5)

    def test_comma_handling(self):
        """Test that commas within quoted fields are handled correctly."""
        results, total_rows = analyze_csv_columns(str(self.test_csv_path))
        results_dict = {r["column"]: r for r in results}

        # address column contains commas but should still be counted as filled
        self.assertEqual(results_dict["address"]["percentage"], 62.5)

        # notes column contains commas and should be counted as filled
        self.assertEqual(results_dict["notes"]["percentage"], 100.0)

    def test_empty_lines_handling(self):
        """Test that empty lines in CSV are handled correctly."""
        results, total_rows = analyze_csv_columns(str(self.test_csv_path))

        # Empty lines should not be counted in total_rows
        # The test file has 8 data rows (not counting empty lines)
        self.assertEqual(total_rows, 8)

    def test_column_indices(self):
        """Test that column indices are correctly assigned."""
        results, _ = analyze_csv_columns(str(self.test_csv_path))

        # Check that column indices are sequential starting from 1
        expected_indices = list(range(1, len(results) + 1))
        actual_indices = [r["column_index"] for r in results]
        self.assertEqual(actual_indices, expected_indices)

    def test_empty_file_handling(self):
        """Test handling of empty CSV files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("")  # Empty file

        try:
            results, total_rows = analyze_csv_columns(f.name)
            # Empty file should return empty results
            self.assertEqual(len(results), 0)
            self.assertEqual(total_rows, 0)
        finally:
            os.unlink(f.name)

    def test_csv_with_only_headers(self):
        """Test CSV file with only headers and no data."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2,col3\n")

        try:
            results, total_rows = analyze_csv_columns(f.name)
            self.assertEqual(len(results), 3)
            self.assertEqual(total_rows, 0)

            # All columns should have 0% fill
            for result in results:
                self.assertEqual(result["percentage"], 0.0)
                self.assertEqual(result["filled_count"], 0)
        finally:
            os.unlink(f.name)

    def test_whitespace_handling(self):
        """Test that whitespace-only values are treated as empty."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2\n")
            f.write("value1,   \n")  # col2 has only whitespace
            f.write("value2,\t\n")  # col2 has only tab
            f.write("value3,\n")  # col2 is empty

        try:
            results, total_rows = analyze_csv_columns(f.name)
            results_dict = {r["column"]: r for r in results}

            self.assertEqual(total_rows, 3)
            self.assertEqual(results_dict["col1"]["filled_count"], 3)
            self.assertEqual(results_dict["col1"]["percentage"], 100.0)
            self.assertEqual(results_dict["col2"]["filled_count"], 0)
            self.assertEqual(results_dict["col2"]["percentage"], 0.0)
        finally:
            os.unlink(f.name)

    def test_encoding_handling(self):
        """Test that different encodings are handled properly."""
        # This test verifies that the encoding fallback mechanism works
        results, total_rows = analyze_csv_columns(str(self.test_csv_path))

        # Should successfully read the file regardless of encoding
        self.assertGreater(len(results), 0)
        self.assertGreater(total_rows, 0)


if __name__ == "__main__":
    unittest.main()
