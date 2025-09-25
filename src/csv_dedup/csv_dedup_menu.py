#!/usr/bin/env python3

"""
CSV Deduplication Menu
Entry point for selecting the appropriate deduplication script
"""

import argparse
import subprocess
import sys
from pathlib import Path


def show_help():
    """Show detailed help information"""
    print("═══════════════════════════════════════════════════════════════════════════════════")
    print("DETAILED HELP")
    print("═══════════════════════════════════════════════════════════════════════════════════")
    print()
    print("🔍 EXACT DUPLICATES (dedup_exact)")
    print("   Use when: You have rows that are byte-for-byte identical")
    print("   How it works: Compares entire rows, removes completely identical ones")
    print("   Speed: Fastest")
    print("   Example scenarios:")
    print("     • Data exported multiple times with duplicate entries")
    print("     • Copy-paste errors creating identical rows")
    print("     • Import errors that duplicated records")
    print()
    print("🔍 SINGLE-COLUMN DUPLICATES (dedup_single)")
    print("   Use when: You want to keep only one record per unique value in one column")
    print("   How it works: Groups by one column, lets you choose which duplicate to keep")
    print("   Speed: Fast")
    print("   Automatic strategies:")
    print("     • First: Keep the first occurrence")
    print("     • Last: Keep the last occurrence (most recent)")
    print("     • Best: Keep the row with most filled columns")
    print("   Manual mode: Review each duplicate group and choose which to keep")
    print("   Example scenarios:")
    print("     • Customer list with duplicate email addresses")
    print("     • Product catalog with duplicate SKUs")
    print("     • User database with duplicate IDs")
    print()
    print("🔍 MULTI-COLUMN DUPLICATES (dedup_multi)")
    print("   Use when: You want to remove duplicates based on a combination of columns")
    print("   How it works: Creates composite keys from multiple columns")
    print("   Speed: Moderate (depends on number of columns)")
    print("   Same automatic strategies and manual mode as single-column")
    print("   Example scenarios:")
    print("     • People database: firstName + lastName + birthDate")
    print("     • Address list: street + city + zipCode")
    print("     • Product inventory: brand + model + size")
    print("     • Event registrations: eventID + participantEmail")
    print()
    print("💡 TIPS FOR CHOOSING:")
    print("   • Start with exact duplicates if you suspect identical rows")
    print("   • Use single-column for simple ID/email/SKU deduplication")
    print("   • Use multi-column when no single field is unique enough")
    print("   • Manual mode gives you full control but takes longer")
    print("   • 'Best' strategy prioritizes keeping the most complete records")
    print()
    print("═══════════════════════════════════════════════════════════════════════════════════")
    print()


def run_dedup_script(script_name):
    """Run the specified deduplication script"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    script_path = script_dir / f"csv_{script_name}.py"

    if not script_path.exists():
        print(f"❌ Error: Could not find {script_path}")
        sys.exit(1)

    # Run the script
    try:
        subprocess.run([str(script_path)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}: {e}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)


def main():
    """Main menu loop"""
    parser = argparse.ArgumentParser(description="CSV Deduplication Tools Menu")
    args = parser.parse_args()

    print("🔍 CSV DEDUPLICATION TOOLS")
    print("════════════════════════════════════════════════════════════════")
    print("Choose the right deduplication method for your needs:")
    print("════════════════════════════════════════════════════════════════")
    print()

    print("Available deduplication methods:")
    print()
    print("1) EXACT DUPLICATES (dedup_exact)")
    print("   • Removes rows that are completely identical across ALL columns")
    print("   • Fastest method for simple exact duplicates")
    print("   • Example: Two rows with exactly the same data in every field")
    print()
    print("2) SINGLE-COLUMN DUPLICATES (dedup_single)")
    print("   • Removes rows with duplicate values in ONE selected column")
    print("   • Choose automatic (first/last/best) or manual selection")
    print("   • Example: Remove duplicate email addresses, keeping one person per email")
    print()
    print("3) MULTI-COLUMN DUPLICATES (dedup_multi)")
    print("   • Removes rows with duplicate combinations across MULTIPLE columns")
    print("   • Choose automatic (first/last/best) or manual selection")
    print("   • Example: Remove duplicates based on firstName + lastName combination")
    print()
    print("4) HELP - Show detailed explanations")
    print()
    print("5) EXIT")
    print()

    while True:
        try:
            choice = input("Enter your choice (1-5): ").strip()

            if choice == "1":
                print()
                print("🚀 Launching EXACT duplicate removal...")
                print("   Running: csv_dedup_exact")
                print()
                run_dedup_script("dedup_exact")
                break
            elif choice == "2":
                print()
                print("🚀 Launching SINGLE-COLUMN duplicate removal...")
                print("   Running: csv_dedup_single")
                print()
                run_dedup_script("dedup_single")
                break
            elif choice == "3":
                print()
                print("🚀 Launching MULTI-COLUMN duplicate removal...")
                print("   Running: csv_dedup_multi")
                print()
                run_dedup_script("dedup_multi")
                break
            elif choice == "4":
                print()
                show_help()
                print("Press Enter to return to main menu...")
                input()
                print()
                print("🔍 CSV DEDUPLICATION TOOLS")
                print("════════════════════════════════════════════════════════════════")
                print("Choose the right deduplication method for your needs:")
                print("════════════════════════════════════════════════════════════════")
                print()
                print("Available deduplication methods:")
                print()
                print("1) EXACT DUPLICATES (dedup_exact)")
                print("   • Removes rows that are completely identical across ALL columns")
                print("   • Fastest method for simple exact duplicates")
                print("   • Example: Two rows with exactly the same data in every field")
                print()
                print("2) SINGLE-COLUMN DUPLICATES (dedup_single)")
                print("   • Removes rows with duplicate values in ONE selected column")
                print("   • Choose automatic (first/last/best) or manual selection")
                print("   • Example: Remove duplicate email addresses, keeping one person per email")
                print()
                print("3) MULTI-COLUMN DUPLICATES (dedup_multi)")
                print("   • Removes rows with duplicate combinations across MULTIPLE columns")
                print("   • Choose automatic (first/last/best) or manual selection")
                print("   • Example: Remove duplicates based on firstName + lastName combination")
                print()
                print("4) HELP - Show detailed explanations")
                print()
                print("5) EXIT")
                print()
            elif choice == "5":
                print()
                print("👋 Goodbye!")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, 4, or 5.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
