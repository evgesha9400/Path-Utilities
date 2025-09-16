#!/usr/bin/env python3
"""
Job Title Scoring Script
Scores job titles based on keyword matches from a configuration file.
"""

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

import pandas as pd

# Common English stop words to filter out
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
}


class JobTitleScorer:
    def __init__(self, config_file="config.json"):
        """Initialize the scorer with configuration."""
        self.config_file = config_file
        self.keywords = {}
        self.load_config()

    def load_config(self):
        """Load keyword-score pairs from configuration file."""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.keywords = config.get("keywords", {})
                hard_exclude_count = sum(
                    1 for score in self.keywords.values() if score == -100
                )
                hard_include_count = sum(
                    1 for score in self.keywords.values() if score == 100
                )
                print(
                    f"Loaded {len(self.keywords)} keywords ({hard_exclude_count} hard excludes, {hard_include_count} hard includes) from {self.config_file}"
                )
        except FileNotFoundError:
            print(
                f"Config file '{self.config_file}' not found. Creating default config..."
            )
            self.create_default_config()
        except json.JSONDecodeError as e:
            print(f"Error parsing config file: {e}")
            sys.exit(1)

    def create_default_config(self):
        """Create a default configuration file."""
        default_config = {
            "keywords": {
                "CEO": 100,
                "President": 100,
                "volunteer": -100,
                "student": -100,
                "intern": -100,
                "trainee": -100,
                "unpaid": -100,
                "senior": 0.3,
                "lead": 0.25,
                "manager": 0.2,
                "director": 0.4,
                "vice president": 0.5,
                "vp": 0.5,
                "chief": 0.6,
                "head": 0.3,
                "principal": 0.35,
                "architect": 0.3,
                "engineer": 0.15,
                "developer": 0.1,
                "analyst": 0.05,
                "specialist": 0.1,
                "coordinator": 0.05,
                "assistant": -0.1,
                "junior": -0.15,
                "entry level": -0.1,
            },
        }

        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)

        self.keywords = default_config["keywords"]
        print(f"Created default config file: {self.config_file}")

    def _create_keyword_pattern(self, keyword):
        """
        Create regex pattern for keyword matching with wildcard support.
        Supports:
        - keyword (exact word match)
        - *keyword (suffix match)
        - keyword* (prefix match)
        - key*word (middle wildcard)
        - *keyword* (contains match)
        """
        keyword_lower = keyword.lower()

        # Skip stop words
        if keyword_lower in STOP_WORDS:
            return None

        if keyword_lower.startswith("*") and keyword_lower.endswith("*"):
            # *keyword* - contains match
            actual_keyword = keyword_lower[1:-1]
            return re.escape(actual_keyword)
        elif keyword_lower.startswith("*"):
            # *keyword - suffix match
            actual_keyword = keyword_lower[1:]
            return re.escape(actual_keyword) + r"(?=\b|$)"
        elif keyword_lower.endswith("*"):
            # keyword* - prefix match
            actual_keyword = keyword_lower[:-1]
            return r"\b" + re.escape(actual_keyword)
        elif "*" in keyword_lower:
            # key*word - middle wildcard
            parts = keyword_lower.split("*")
            if len(parts) == 2:
                return (
                    r"\b" + re.escape(parts[0]) + r".*?" + re.escape(parts[1]) + r"\b"
                )
            else:
                # Multiple * in middle - treat as contains match
                actual_keyword = keyword_lower.replace("*", "")
                return re.escape(actual_keyword)
        else:
            # keyword - exact word match
            return r"\b" + re.escape(keyword_lower) + r"\b"

    def calculate_score(self, job_title):
        """
        Calculate score for a job title based on keyword matches.
        Returns tuple: (final_score, calculation_details, character_percentage)
        """
        if not job_title or pd.isna(job_title):
            return 0.000, "", 0.0

        job_title_lower = str(job_title).lower()

        # Check for hard excludes first (keywords with score -100)
        for keyword, score in self.keywords.items():
            if score == -100:
                pattern = self._create_keyword_pattern(keyword)
                if pattern and re.search(pattern, job_title_lower):
                    return 0.000, f"hard exclude: {keyword}", 0.0

        # Check for hard includes (keywords with score 100) - but still apply character normalization
        for keyword, score in self.keywords.items():
            if score == 100:
                pattern = self._create_keyword_pattern(keyword)
                if pattern:
                    match = re.search(pattern, job_title_lower)
                    if match:
                        # Calculate character percentage for hard includes
                        normalized_job_title = re.sub(r"[^a-zA-Z0-9]", "", job_title)
                        total_content_characters = len(normalized_job_title)

                        # Extract the matched text and count only alphanumeric characters
                        matched_text = job_title_lower[match.start() : match.end()]
                        normalized_matched_text = re.sub(
                            r"[^a-zA-Z0-9]", "", matched_text
                        )
                        matched_chars = len(normalized_matched_text)

                        character_percentage = (
                            matched_chars / total_content_characters
                            if total_content_characters > 0
                            else 0.0
                        )

                        # Apply character-based normalization to hard include score
                        # Hard includes should be capped at 1.0 regardless of their base score
                        normalized_score = min(1.0, score * character_percentage)
                        return (
                            round(normalized_score, 3),
                            f"hard include: {keyword} × {character_percentage:.2f} (char match)",
                            character_percentage,
                        )

        matched_keywords = []
        total_score = 0.0

        # Sort keywords by length (longest first) to handle overlapping matches
        sorted_keywords = sorted(
            self.keywords.items(), key=lambda x: len(x[0]), reverse=True
        )

        # Track which parts of the title have been matched to avoid double-counting
        matched_positions = set()

        for keyword, score in sorted_keywords:
            pattern = self._create_keyword_pattern(keyword)

            # Skip if pattern is None (stop word)
            if not pattern:
                continue

            # Find all occurrences of the keyword
            for match in re.finditer(pattern, job_title_lower):
                start, end = match.span()

                # Check if this position hasn't been matched by a longer keyword
                if not any(pos in matched_positions for pos in range(start, end)):
                    matched_keywords.append((keyword, score))
                    total_score += score

                    # Mark these positions as matched
                    matched_positions.update(range(start, end))
                    break  # Only count first occurrence of each keyword

        # Calculate character percentage (normalized - only alphanumeric characters)
        # Remove spaces and special characters from job title for content-focused calculation
        normalized_job_title = re.sub(r"[^a-zA-Z0-9]", "", job_title)
        total_content_characters = len(normalized_job_title)

        # Separate positive and negative scores
        positive_score = 0.0
        negative_score = 0.0
        positive_matched_chars = 0
        total_matched_chars = 0

        for keyword, score in matched_keywords:
            pattern = self._create_keyword_pattern(keyword)

            # Skip if pattern is None (stop word)
            if not pattern:
                continue

            # Find all occurrences of the keyword
            for match in re.finditer(pattern, job_title_lower):
                start, end = match.span()
                # Extract the matched text and count only alphanumeric characters
                matched_text = job_title_lower[start:end]
                normalized_matched_text = re.sub(r"[^a-zA-Z0-9]", "", matched_text)
                matched_chars = len(normalized_matched_text)
                total_matched_chars += matched_chars

                if score > 0:
                    positive_score += score
                    positive_matched_chars += matched_chars
                else:
                    negative_score += (
                        score  # Negative scores are not scaled by character percentage
                    )

                break  # Only count first occurrence of each keyword

        # Calculate character percentage only for positive contributions
        positive_character_percentage = (
            positive_matched_chars / total_content_characters
            if total_content_characters > 0 and positive_matched_chars > 0
            else 0.0  # If no positive characters matched, multiplier should be 0
        )

        # Apply character-based normalization to all positive scores
        normalized_positive_score = positive_score * positive_character_percentage
        final_score = max(0.0, normalized_positive_score + negative_score)

        # Create calculation details
        if matched_keywords:
            # Separate positive and negative keywords
            positive_keywords = [
                (keyword, score) for keyword, score in matched_keywords if score > 0
            ]
            negative_keywords = [
                (keyword, score) for keyword, score in matched_keywords if score < 0
            ]
            zero_keywords = [
                (keyword, score) for keyword, score in matched_keywords if score == 0
            ]

            calc_parts = []

            # Add positive keywords
            if positive_keywords:
                positive_part = " + ".join(
                    [f"{keyword} ({score})" for keyword, score in positive_keywords]
                )
                if positive_score > 0:
                    positive_part += (
                        f" × {positive_character_percentage:.2f} (pos char match)"
                    )
                calc_parts.append(positive_part)

            # Add zero keywords (if any)
            if zero_keywords:
                zero_part = " + ".join(
                    [f"{keyword} ({score})" for keyword, score in zero_keywords]
                )
                calc_parts.append(zero_part)

            # Add negative keywords
            if negative_keywords:
                negative_part = " + ".join(
                    [f"{keyword} ({score})" for keyword, score in negative_keywords]
                )
                calc_parts.append(negative_part)

            calc_details = " + ".join(calc_parts)
        else:
            calc_details = "no matches"

        return round(final_score, 3), calc_details, positive_character_percentage

    def process_csv(
        self, input_file, job_title_column, output_file=None, test_mode=False
    ):
        """Process CSV file and add scoring columns."""
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' not found.")
            sys.exit(1)

        # Generate output filename if not provided
        if output_file is None:
            input_path = Path(input_file)
            suffix = "_test" if test_mode else "_scored"
            output_file = (
                input_path.parent / f"{input_path.stem}{suffix}{input_path.suffix}"
            )

        try:
            with open(input_file, "r", encoding="utf-8", newline="") as infile:
                # For complex CSVs with quoted fields containing commas,
                # try comma first (most common), then fall back to sniffer
                delimiter = ","  # Default to comma

                # Try reading with comma delimiter first
                infile.seek(0)
                try:
                    # Test if comma works by trying to read the header
                    sample_line = infile.readline()
                    infile.seek(0)

                    # Count commas in the header line
                    comma_count = sample_line.count(",")
                    if comma_count > 10:  # Reasonable number of columns for CSV
                        delimiter = ","
                    else:
                        # Fall back to sniffer for other delimiters
                        sample = infile.read(1024)
                        infile.seek(0)
                        try:
                            sniffer = csv.Sniffer()
                            delimiter = sniffer.sniff(sample).delimiter
                        except csv.Error:
                            # If sniffer fails, try to detect manually
                            if "\t" in sample and sample.count("\t") > sample.count(
                                ","
                            ):
                                delimiter = "\t"
                            else:
                                delimiter = ","
                except Exception:
                    # If anything fails, default to comma
                    delimiter = ","

                reader = csv.DictReader(infile, delimiter=delimiter)
                fieldnames = reader.fieldnames

                # Check if job title column exists
                if job_title_column not in fieldnames:
                    print(f"Error: Column '{job_title_column}' not found in CSV.")
                    print(f"Available columns: {', '.join(fieldnames)}")
                    sys.exit(1)

                # First pass: Calculate all scores and find maximum (excluding hard includes)
                print("First pass: Calculating scores...")
                rows_data = []
                max_score = 0.0

                for row in reader:
                    job_title = row.get(job_title_column, "")
                    score, calculation, char_percentage = self.calculate_score(
                        job_title
                    )

                    rows_data.append(
                        {
                            "row": row,
                            "score": score,
                            "calculation": calculation,
                            "char_percentage": char_percentage,
                        }
                    )

                    # Only consider scores for normalization if they're not hard includes
                    # Hard includes should maintain their intended score
                    if not calculation.startswith("hard include"):
                        max_score = max(max_score, score)

                # Determine normalization factor
                normalization_factor = 1.0
                if max_score > 1.0:
                    normalization_factor = 1.0 / max_score
                    print(
                        f"Dataset normalization applied: max_score={max_score:.3f}, factor={normalization_factor:.3f}"
                    )
                else:
                    print(f"No dataset normalization needed: max_score={max_score:.3f}")

                # Determine output fieldnames based on test mode
                if test_mode:
                    output_fieldnames = [
                        job_title_column,
                        "job_title_score",
                        "score_calculation",
                    ]
                else:
                    output_fieldnames = fieldnames + [
                        "job_title_score",
                        "score_calculation",
                    ]

                # Second pass: Apply normalization and write output
                print("Second pass: Writing normalized scores...")
                processed_count = 0

                # Apply normalization and prepare data for sorting
                normalized_rows = []
                for row_data in rows_data:
                    # Apply dataset normalization (but not to hard includes)
                    if row_data["calculation"].startswith("hard include"):
                        # Hard includes maintain their intended score
                        normalized_score = row_data["score"]
                    else:
                        # Apply normalization to regular scores
                        normalized_score = row_data["score"] * normalization_factor

                    normalized_score = round(normalized_score, 3)

                    # Store normalized data for sorting
                    normalized_rows.append(
                        {"row_data": row_data, "normalized_score": normalized_score}
                    )

                # Sort by normalized score in descending order
                normalized_rows.sort(key=lambda x: x["normalized_score"], reverse=True)

                with open(output_file, "w", encoding="utf-8", newline="") as outfile:
                    writer = csv.DictWriter(
                        outfile, fieldnames=output_fieldnames, delimiter=delimiter
                    )
                    writer.writeheader()

                    for normalized_row in normalized_rows:
                        row_data = normalized_row["row_data"]
                        normalized_score = normalized_row["normalized_score"]

                        if test_mode:
                            # Only include job title, score, and calculation columns
                            output_row = {
                                job_title_column: row_data["row"].get(
                                    job_title_column, ""
                                ),
                                "job_title_score": normalized_score,
                                "score_calculation": row_data["calculation"],
                            }
                        else:
                            # Include all original columns plus score columns
                            output_row = row_data["row"].copy()
                            output_row["job_title_score"] = normalized_score
                            output_row["score_calculation"] = row_data["calculation"]

                        writer.writerow(output_row)
                        processed_count += 1

                print(f"Successfully processed {processed_count} rows.")
                print(f"Output saved to: {output_file}")

        except Exception as e:
            print(f"Error processing CSV: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Score job titles based on keyword matches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
          python job_title_scorer.py input.csv "Job Title"
          python job_title_scorer.py data.csv "Position" --output scored_data.csv
          python job_title_scorer.py jobs.csv "Title" --config custom_config.json
          python job_title_scorer.py test.csv "jobTitle" --test-mode
        """,
    )

    parser.add_argument("input_file", help="Path to input CSV file")
    parser.add_argument(
        "job_title_column", help="Name of the column containing job titles"
    )
    parser.add_argument(
        "--output", "-o", help="Output CSV file path (default: input_scored.csv)"
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config.json",
        help="Configuration file path (default: config.json)",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Test mode: output only job title, score, and calculation columns",
    )

    args = parser.parse_args()

    # Initialize scorer
    scorer = JobTitleScorer(args.config)

    # Process CSV
    scorer.process_csv(
        args.input_file, args.job_title_column, args.output, args.test_mode
    )


if __name__ == "__main__":
    main()
