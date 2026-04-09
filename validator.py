import csv

REQUIRED_COLUMNS = ["timestamp", "status"]


def validate_file(file_path):
    try:
        with open(file_path, "r") as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames:
                return False, "ERROR: File is empty or has no header row."

            missing = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
            if missing:
                return False, f"ERROR: Missing required columns: {missing}"

            gaps = []
            for i, row in enumerate(reader, start=2):  # row 1 is header
                empty = [col for col in REQUIRED_COLUMNS if not (row.get(col) or "").strip()]
                if empty:
                    gaps.append(f"  Row {i}: missing values for {empty}")

            if gaps:
                report = "WARNING: Data gaps found:\n" + "\n".join(gaps[:20])
                if len(gaps) > 20:
                    report += f"\n  ... and {len(gaps) - 20} more."
                return False, report

        return True, "Validation passed: file structure is valid."

    except FileNotFoundError:
        return False, f"ERROR: File not found: {file_path}"
    except Exception as e:
        return False, f"ERROR: Could not read file: {e}"
