#!/usr/bin/env python3
"""
File Selector Module
A unified Python module for interactive file selection across CSV utilities.

This module provides a consistent interface for file selection that can be used
across all CSV processing scripts, replacing the various custom implementations.
"""

from pathlib import Path
from typing import List, Optional


class FileSelector:
    """Unified file selector with multiple selection modes."""

    def __init__(self, directory: str = "."):
        """Initialize the file selector.

        Args:
            directory: Directory to search for files (default: current directory)
        """
        self.directory = Path(directory).resolve()

    def find_files(self, pattern: str = "*.csv") -> List[str]:
        """Find files matching the pattern in the directory.

        Args:
            pattern: File pattern to match (e.g., "*.csv", "*.txt")

        Returns:
            List of file paths sorted by name
        """
        files = []
        for file_path in self.directory.glob(pattern):
            if file_path.is_file():
                files.append(str(file_path))
        return sorted(files)

    def select_files(
        self,
        title: str,
        min_files: int = 1,
        max_files: int = 0,
        pattern: str = "*.csv",
        mode: str = "interactive",
        show_row_counts: bool = False,
    ) -> Optional[List[str]]:
        """Select files using the specified mode.

        Args:
            title: Menu title to display
            min_files: Minimum number of files required (default: 1)
            max_files: Maximum number of files allowed (0 = unlimited, default: 0)
            pattern: File pattern to match (default: "*.csv")
            mode: Selection mode - "simple", "sequential", or "interactive" (default: "interactive")
            show_row_counts: Whether to show row counts for CSV files (default: False)

        Returns:
            List of selected file paths, or None if cancelled
        """
        files = self.find_files(pattern)

        if not files:
            print(f"❌ No files matching '{pattern}' found in {self.directory}.")
            return None

        if len(files) < min_files:
            print(f"❌ Found only {len(files)} files, but {min_files} are required.")
            return None

        if mode == "simple":
            return self._select_simple(
                files, title, min_files, max_files, show_row_counts
            )
        elif mode == "sequential":
            return self._select_sequential(
                files, title, min_files, max_files, show_row_counts
            )
        elif mode == "interactive":
            return self._select_interactive(
                files, title, min_files, max_files, show_row_counts
            )
        else:
            raise ValueError(
                f"Invalid mode: {mode}. Use 'simple', 'sequential', or 'interactive'"
            )

    def _select_simple(
        self,
        files: List[str],
        title: str,
        min_files: int,
        max_files: int,
        show_row_counts: bool,
    ) -> Optional[List[str]]:
        """Simple numbered selection - select one file at a time."""
        print(f"📁 {title}")
        print("=" * 40)

        # Show files with optional row counts
        for i, file_path in enumerate(files, 1):
            filename = Path(file_path).name
            if show_row_counts and file_path.endswith(".csv"):
                try:
                    row_count = self._count_csv_rows(file_path)
                    print(f"{i:2d}) {filename} ({row_count:,} rows)")
                except Exception:
                    print(f"{i:2d}) {filename}")
            else:
                print(f"{i:2d}) {filename}")

        print()

        # Handle single file case
        if len(files) == 1 and min_files == 1:
            return [files[0]]

        # Select files one by one
        selected_files = []
        remaining_files = files.copy()

        for selection_num in range(min_files):
            while True:
                try:
                    if len(remaining_files) == 1 and selection_num < min_files - 1:
                        # Auto-select if only one file left and we need more
                        choice = 1
                    else:
                        prompt = f"Select file #{selection_num + 1}"
                        if selection_num > 0:
                            prompt += f" (remaining: {len(remaining_files)})"
                        prompt += f" (1-{len(remaining_files)}): "

                        choice = int(input(prompt))

                    if 1 <= choice <= len(remaining_files):
                        selected_file = remaining_files[choice - 1]
                        selected_files.append(selected_file)
                        remaining_files.remove(selected_file)
                        print(f"   ✓ Selected: {Path(selected_file).name}")
                        break
                    else:
                        print(
                            f"❌ Invalid choice. Please enter a number between 1 and {len(remaining_files)}."
                        )
                except ValueError:
                    print(
                        f"❌ Invalid choice. Please enter a number between 1 and {len(remaining_files)}."
                    )

        return selected_files

    def _select_sequential(
        self,
        files: List[str],
        title: str,
        min_files: int,
        max_files: int,
        show_row_counts: bool,
    ) -> Optional[List[str]]:
        """Sequential selection - same as simple but with different UI."""
        return self._select_simple(files, title, min_files, max_files, show_row_counts)

    def _select_interactive(
        self,
        files: List[str],
        title: str,
        min_files: int,
        max_files: int,
        show_row_counts: bool,
    ) -> Optional[List[str]]:
        """Interactive multi-select with checkbox-style interface."""
        file_statuses = [False] * len(files)

        # Prepare requirement text
        if min_files == max_files and max_files != 0:
            requirement = f"exactly {min_files}"
        elif max_files == 0:
            requirement = f"at least {min_files}"
        else:
            requirement = f"between {min_files} and {max_files}"

        # Clear screen sequence
        CLEAR_SCREEN = "\033[H\033[J"

        while True:
            # Clear screen and redraw
            print(CLEAR_SCREEN, end="")

            # Display header
            print(f"📁 {title}")
            print("=" * 40)
            print(f"Select {requirement} files:")
            print()

            # Display files with selection status
            for i, file_path in enumerate(files):
                status = "[✓]" if file_statuses[i] else "[ ]"
                filename = Path(file_path).name

                if show_row_counts and file_path.endswith(".csv"):
                    try:
                        row_count = self._count_csv_rows(file_path)
                        print(f"{i + 1:2d}) {status} {filename} ({row_count:,} rows)")
                    except Exception:
                        print(f"{i + 1:2d}) {status} {filename}")
                else:
                    print(f"{i + 1:2d}) {status} {filename}")

            # Count selected files
            selected_count = sum(file_statuses)

            # Display commands and status
            print()
            print("Commands:")
            print(f"  1-{len(files)}: Toggle file selection")
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

            if choice.lower() == "q":
                print("❌ Operation cancelled.")
                return None

            elif choice.lower() == "a":
                file_statuses = [True] * len(files)

            elif choice.lower() == "c":
                file_statuses = [False] * len(files)

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

                # Build selected files list
                selected_files = []
                for i, is_selected in enumerate(file_statuses):
                    if is_selected:
                        selected_files.append(files[i])

                return selected_files

            else:
                # Handle number selection
                try:
                    file_num = int(choice)
                    if 1 <= file_num <= len(files):
                        idx = file_num - 1
                        file_statuses[idx] = not file_statuses[idx]
                    else:
                        print("Invalid file number. Press Enter to continue...")
                        input()
                except ValueError:
                    print("Invalid choice. Press Enter to continue...")
                    input()

    def _count_csv_rows(self, file_path: str) -> int:
        """Count data rows in a CSV file (excluding header)."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # Skip header and count remaining lines
                next(f, None)  # Skip header
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0


# Convenience functions for backward compatibility and ease of use
def select_files(
    title: str,
    min_files: int = 1,
    max_files: int = 0,
    pattern: str = "*.csv",
    directory: str = ".",
    mode: str = "interactive",
    show_row_counts: bool = False,
) -> Optional[List[str]]:
    """Convenience function for file selection.

    Args:
        title: Menu title to display
        min_files: Minimum number of files required (default: 1)
        max_files: Maximum number of files allowed (0 = unlimited, default: 0)
        pattern: File pattern to match (default: "*.csv")
        directory: Directory to search (default: ".")
        mode: Selection mode - "simple", "sequential", or "interactive" (default: "interactive")
        show_row_counts: Whether to show row counts for CSV files (default: False)

    Returns:
        List of selected file paths, or None if cancelled
    """
    selector = FileSelector(directory)
    return selector.select_files(
        title, min_files, max_files, pattern, mode, show_row_counts
    )


def select_single_file(
    title: str = "File Selection",
    pattern: str = "*.csv",
    directory: str = ".",
    show_row_counts: bool = False,
) -> Optional[str]:
    """Convenience function for selecting a single file.

    Args:
        title: Menu title to display
        pattern: File pattern to match (default: "*.csv")
        directory: Directory to search (default: ".")
        show_row_counts: Whether to show row counts for CSV files (default: False)

    Returns:
        Selected file path, or None if cancelled
    """
    files = select_files(title, 1, 1, pattern, directory, "simple", show_row_counts)
    return files[0] if files else None


def select_multiple_files(
    title: str = "File Selection",
    min_files: int = 2,
    max_files: int = 0,
    pattern: str = "*.csv",
    directory: str = ".",
    show_row_counts: bool = False,
) -> Optional[List[str]]:
    """Convenience function for selecting multiple files.

    Args:
        title: Menu title to display
        min_files: Minimum number of files required (default: 2)
        max_files: Maximum number of files allowed (0 = unlimited, default: 0)
        pattern: File pattern to match (default: "*.csv")
        directory: Directory to search (default: ".")
        show_row_counts: Whether to show row counts for CSV files (default: False)

    Returns:
        List of selected file paths, or None if cancelled
    """
    return select_files(
        title, min_files, max_files, pattern, directory, "interactive", show_row_counts
    )


if __name__ == "__main__":
    # Demo usage
    print("File Selector Module Demo")
    print("=" * 30)

    # Test single file selection
    print("\n1. Single file selection:")
    file = select_single_file("Select a CSV file", "*.csv", ".", True)
    if file:
        print(f"Selected: {Path(file).name}")

    # Test multiple file selection
    print("\n2. Multiple file selection:")
    files = select_multiple_files("Select CSV files", 2, 0, "*.csv", ".", True)
    if files:
        print(f"Selected {len(files)} files:")
        for f in files:
            print(f"  - {Path(f).name}")
