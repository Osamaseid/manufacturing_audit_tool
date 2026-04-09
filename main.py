import argparse

from file_parser import parse_file
from analayzer import calculate_idle_time
from validator import validate_file


def main():
    arg_parser = argparse.ArgumentParser(description="Manufacturing Audit Tool")
    arg_parser.add_argument("file", help="Path to CSV log file")
    arg_parser.add_argument("--validate", action="store_true", help="Pre-scan file for issues before analysis")

    args = arg_parser.parse_args()

    if args.validate:
        valid, message = validate_file(args.file)
        print(message)
        if not valid and "ERROR:" in message:
            # Hard errors (missing columns, file not found) abort the run
            return

    data, skipped = parse_file(args.file)
    idle_percentage = calculate_idle_time(data)

    print("\n=== Audit Summary ===")
    print(f"Valid Records:   {len(data)}")
    print(f"Skipped Records: {skipped}")
    print(f"Idle Time:       {idle_percentage:.2f}%")


if __name__ == "__main__":
    main()
