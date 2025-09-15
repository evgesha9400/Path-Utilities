# CSV Utilities Test Suite

This directory contains comprehensive tests for all CSV utility scripts in the project. Tests use the standard Python `unittest` library and follow a structured approach for testing edge cases and various data scenarios.

## Directory Structure

```
tests/
├── README.md                          # This file
├── unit/                              # Unit tests for individual scripts
│   ├── test_csv_analyzer.py           # Tests for csv_analyzer.py (COMPLETE)
│   ├── test_csv_dedup_exact.py        # Tests for csv_dedup_exact.py
│   ├── test_csv_dedup_single.py       # Tests for csv_dedup_single.py
│   ├── test_csv_dedup_multi.py        # Tests for csv_dedup_multi.py
│   ├── test_csv_delete_col.py         # Tests for csv_delete_col.py
│   ├── test_csv_diff.py               # Tests for csv_diff.py
│   ├── test_csv_extend.py             # Tests for csv_extend.py
│   ├── test_csv_fill.py               # Tests for csv_fill.py
│   ├── test_csv_join.py               # Tests for csv_join.py
│   ├── test_csv_match.py              # Tests for csv_match.py
│   ├── test_csv_merge_col.py          # Tests for csv_merge_col.py
│   ├── test_csv_remove_www.py         # Tests for csv_remove_www.py
│   └── test_csv_split.py              # Tests for csv_split.py
└── data/                              # Test data organized by script
    ├── csv_analyzer/                  # Test data for csv_analyzer
    │   ├── input/                     # Input test files
    │   │   └── test.csv               # Comprehensive test CSV with edge cases
    │   └── expected_output/           # Expected output files (when applicable)
    ├── csv_dedup/                     # Test data for deduplication scripts
    │   ├── exact/
    │   │   ├── input/
    │   │   └── expected_output/
    │   ├── multi/
    │   │   ├── input/
    │   │   └── expected_output/
    │   └── single/
    │       ├── input/
    │       └── expected_output/
    ├── csv_delete_col/                # Test data for csv_delete_col
    │   ├── input/
    │   └── expected_output/
    ├── csv_diff/                      # Test data for csv_diff
    │   ├── input/
    │   └── expected_output/
    ├── csv_extend/                    # Test data for csv_extend
    │   ├── input/
    │   └── expected_output/
    ├── csv_fill/                      # Test data for csv_fill
    │   ├── input/
    │   └── expected_output/
    ├── csv_join/                      # Test data for csv_join
    │   ├── input/
    │   └── expected_output/
    ├── csv_match/                     # Test data for csv_match
    │   ├── input/
    │   └── expected_output/
    ├── csv_merge_col/                 # Test data for csv_merge_col
    │   ├── input/
    │   └── expected_output/
    ├── csv_remove_www/                # Test data for csv_remove_www
    │   ├── input/
    │   └── expected_output/
    └── csv_split/                     # Test data for csv_split
        ├── input/
        └── expected_output/
```

## Testing Framework

### Unit Tests (`tests/unit/`)
- Use standard Python `unittest` library
- Test individual functions and classes in isolation
- Each test file corresponds to one source script
- Focus on function-level testing, edge cases, and error handling
- No external dependencies (no pytest, no conftest.py)

## Running Tests

### Prerequisites
No external dependencies required - uses only Python standard library.

### Running All Tests
```bash
# From project root directory
PYTHONPATH=src python3 -m unittest discover tests/unit/
```

### Running Specific Tests
```bash
# Run tests for csv_analyzer (example - fully implemented)
PYTHONPATH=src python3 -m unittest tests.unit.test_csv_analyzer

# Run a specific test method
PYTHONPATH=src python3 -m unittest tests.unit.test_csv_analyzer.TestCSVAnalyzer.test_column_fill_percentages

# Run tests for all deduplication scripts
PYTHONPATH=src python3 -m unittest tests.unit.test_csv_dedup_*
```

### Running Individual Test Files
```bash
# Run a single test file directly
PYTHONPATH=src python3 tests/unit/test_csv_analyzer.py
```

## Comprehensive Edge Case Testing Strategy

Every CSV utility script should be tested against the following comprehensive set of edge cases and scenarios. This ensures robust handling of real-world CSV data variations.

### Required Test Cases for All Scripts

#### 1. **Basic Functionality Tests**
- ✅ Test with standard, well-formed CSV data
- ✅ Verify correct processing of expected input/output
- ✅ Test with various data types (strings, numbers, dates, etc.)

#### 2. **Empty Data Handling**
- ✅ **Empty files**: Files with no content
- ✅ **Header-only files**: CSV files with only column headers
- ✅ **Empty rows**: CSV files containing empty rows
- ✅ **Single row data**: CSV files with only one data row
- ✅ **Single column data**: CSV files with only one column

#### 3. **Whitespace and Formatting**
- ✅ **Leading/trailing whitespace**: Data with spaces before/after values
- ✅ **Whitespace-only values**: Cells containing only spaces or tabs
- ✅ **Mixed whitespace**: Various combinations of spaces, tabs, newlines
- ✅ **Quoted fields**: Fields properly quoted with commas inside
- ✅ **Unquoted fields**: Standard unquoted CSV fields

#### 4. **Special Characters and Encoding**
- ✅ **Commas within quoted fields**: `"Address, City, State"`
- ✅ **Newlines within quoted fields**: Multi-line text in single cells
- ✅ **Quotes within quoted fields**: Escaped quotes `""quoted text""`
- ✅ **Special characters**: `@#$%^&*()[]{}|\\/:;"'<>?`
- ✅ **Unicode characters**: International characters and symbols
- ✅ **Different encodings**: UTF-8, Latin-1, CP1252, ISO-8859-1

#### 5. **Data Variations**
- ✅ **Mixed fill rates**: Columns with varying percentages of filled data (0% to 100%)
- ✅ **Inconsistent row lengths**: Rows with different numbers of columns
- ✅ **Missing values**: Empty cells, null values, undefined data
- ✅ **Very long values**: Extremely long text in single cells
- ✅ **Numeric variations**: Integers, floats, scientific notation, currency

#### 6. **File Structure Edge Cases**
- ✅ **Extra blank lines**: Multiple consecutive empty lines
- ✅ **Trailing commas**: Rows ending with empty columns
- ✅ **Inconsistent quoting**: Mix of quoted and unquoted fields
- ✅ **Malformed CSV**: Invalid CSV structure (graceful handling)
- ✅ **Very large files**: Performance with large datasets

#### 7. **Error Handling**
- ✅ **File not found**: Non-existent file paths
- ✅ **Permission errors**: Read-only files, insufficient permissions
- ✅ **Corrupted files**: Files with invalid encoding or structure
- ✅ **Invalid arguments**: Wrong parameters, invalid options

### Test Data Requirements

Each script's test data should include:

#### **Primary Test File** (`test.csv`)
- **7 columns** with varying fill percentages (0% to 100%)
- **8 data rows** (excluding empty lines)
- **Multiline content** with actual newline characters in quoted fields
- **Commas within quoted fields** to test CSV parsing
- **Empty lines** mixed throughout the file
- **Special characters** and edge case values
- **Mixed data types** (text, numbers, dates, etc.)

#### **Edge Case Test Files** (as needed)
- `empty.csv` - Completely empty file
- `headers_only.csv` - Only column headers
- `single_row.csv` - One data row
- `whitespace.csv` - Various whitespace scenarios
- `unicode.csv` - International characters
- `malformed.csv` - Invalid CSV structure

### Implementation Pattern

Follow the established pattern from `test_csv_analyzer.py`:

```python
import os
import tempfile
import unittest
from pathlib import Path

from <module_name> import <function_name>

class Test<ScriptName>(unittest.TestCase):
    """Test cases for <script_name>.py functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = Path(__file__).parent.parent / "data" / "<script_name>" / "input"
        self.test_csv_path = self.test_data_dir / "test.csv"
    
    def test_basic_functionality(self):
        """Test basic <script_name> functionality."""
        # Test with standard input
        pass
    
    def test_empty_file_handling(self):
        """Test handling of empty CSV files."""
        # Test with empty files
        pass
    
    def test_whitespace_handling(self):
        """Test that whitespace-only values are handled correctly."""
        # Test whitespace scenarios
        pass
    
    # ... additional edge case tests
```

## Test Data Organization

Each script has its own directory under `tests/data/` with:
- `input/` - Test input CSV files
- `expected_output/` - Expected output files for comparison (when applicable)

### Example Test Data Structure
```
tests/data/<script_name>/
├── input/
│   ├── test.csv              # Primary comprehensive test file
│   ├── empty.csv             # Empty file test
│   ├── headers_only.csv      # Header-only test
│   └── edge_cases.csv        # Additional edge case scenarios
└── expected_output/          # Expected results (when applicable)
    ├── test_expected.csv     # Expected output for test.csv
    └── edge_cases_expected.csv
```

## Adding New Tests

### For a New Script
1. **Create test file**: `tests/unit/test_<script_name>.py`
2. **Create data directory**: `tests/data/<script_name>/input/`
3. **Add test CSV files**: Include `test.csv` with comprehensive edge cases
4. **Implement test cases**: Follow the established pattern and cover all required edge cases
5. **Use temporary files**: For tests that need to create/modify files

### Test Implementation Checklist
- [ ] Basic functionality test
- [ ] Empty file handling
- [ ] Header-only file handling  
- [ ] Whitespace handling
- [ ] Special character handling
- [ ] Multiline content handling
- [ ] Comma-in-quotes handling
- [ ] Error handling (file not found, permissions, etc.)
- [ ] Edge case scenarios specific to the script's functionality

## Best Practices

### Test Structure
1. **Use unittest.TestCase**: Standard Python unittest library only
2. **No path hacks**: Use PYTHONPATH environment variable for imports
3. **Clean imports**: Import only what you need from the src modules
4. **Descriptive names**: Use clear, descriptive test method names
5. **One concept per test**: Each test should verify one specific behavior

### Data Management
1. **Temporary files**: Use `tempfile.NamedTemporaryFile()` for test files
2. **Cleanup**: Always clean up temporary files in `finally` blocks
3. **Test data isolation**: Each test should be independent
4. **Realistic data**: Use realistic test data that represents real-world scenarios

### Edge Case Coverage
1. **Empty scenarios**: Test with empty files, empty rows, empty columns
2. **Whitespace variations**: Leading/trailing spaces, tabs, newlines
3. **Special characters**: Commas, quotes, newlines within quoted fields
4. **Encoding issues**: Test with different character encodings
5. **Malformed data**: Graceful handling of invalid CSV structure

### Error Testing
1. **File operations**: Test file not found, permission errors
2. **Invalid input**: Test with malformed or unexpected input
3. **Boundary conditions**: Test with very large or very small datasets
4. **Resource limits**: Test behavior when system resources are limited

## Example: Complete Test Implementation

See `tests/unit/test_csv_analyzer.py` for a complete example of:
- ✅ Proper import structure (no path hacks)
- ✅ Comprehensive edge case testing
- ✅ Temporary file management
- ✅ Error handling tests
- ✅ Clear test organization and naming
- ✅ Realistic test data with actual newlines and commas

## Contributing

When adding new tests:
1. **Follow the pattern**: Use the established structure from `test_csv_analyzer.py`
2. **Cover all edge cases**: Implement all required test scenarios
3. **Use proper imports**: No sys.path manipulation
4. **Add test data**: Create comprehensive test CSV files
5. **Verify functionality**: Ensure all tests pass before submitting
6. **Update documentation**: Update this README if adding new patterns
