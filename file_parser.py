import csv
from utils import normalize_timestamp

VALID_STATUSES = {"RUNNING", "IDLE", "BROKEN"}


def parse_file(file_path):
    valid_rows = []
    skipped = 0

    with open(file_path, "r") as file:
        reader = csv.DictReader(file)

        for row in reader:
            try:
                ts = normalize_timestamp(row.get("timestamp", ""))
                status = (row.get("status") or "").strip()

                if not ts or status not in VALID_STATUSES:
                    raise ValueError(f"Invalid timestamp or status: '{status}'")

                valid_rows.append({"timestamp": ts, "status": status})

            except Exception:
                skipped += 1
                continue

    return valid_rows, skipped