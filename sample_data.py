import csv
import random
from datetime import datetime, timedelta


def generate_sample(file_name="sample.csv", rows=10000, malformed_pct=0.05):
    with open(file_name, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "status"])

        base_time = datetime.now()
        malformed_count = 0

        for i in range(rows):
            if random.random() < malformed_pct:
                # Inject a malformed row (bad timestamp, missing field, garbage)
                bad = random.choice([
                    ["NOT_A_TIMESTAMP", "RUNNING"],
                    ["", "IDLE"],
                    [base_time.isoformat()],          # missing status column
                    ["9999-99-99T99:99:99", "IDLE"],  # invalid ISO date
                    [base_time.isoformat(), "UNKNOWN_STATUS"],
                ])
                writer.writerow(bad)
                malformed_count += 1
            else:
                ts = int(base_time.timestamp()) if random.random() > 0.5 else base_time.isoformat()
                status = random.choice(["RUNNING", "IDLE", "BROKEN"])
                writer.writerow([ts, status])

            base_time += timedelta(seconds=60)

    print(f"Generated {rows} rows ({malformed_count} malformed) -> {file_name}")


if __name__ == "__main__":
    generate_sample()


