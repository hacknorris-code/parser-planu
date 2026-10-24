import csv


INPUT_FILE = "timetables.csv"
OUTPUT_FILE = "timetables_filtered.csv"


TARGET_DAY = "Środa"
TARGET_START = 9 * 60 + 45       # 09:45
TARGET_END = 10 * 60 + 45        # 10:45
MAX_END = 20 * 60                # 20:00


def time_to_minutes(value):
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def timetable_is_valid(rows):
    wednesday_9_45_filled = False

    for row in rows:
        end = time_to_minutes(row["end_time"])

        # Reject anything finishing after 20:00.
        if end > MAX_END:
            return False

        # Check whether Wednesday 09:45-10:45 is continuously occupied.
        if row["day"] == TARGET_DAY:
            start = time_to_minutes(row["time"])

            if start <= TARGET_START and end >= TARGET_END:
                wednesday_9_45_filled = True

    return wednesday_9_45_filled


def filter_timetables(input_file, output_file):
    kept = 0
    discarded = 0

    with open(input_file, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        rows_by_timetable = {}

        for row in reader:
            timetable_id = row["timetable_id"]
            rows_by_timetable.setdefault(timetable_id, []).append(row)

    valid_timetables = []

    for timetable_id, rows in rows_by_timetable.items():
        if timetable_is_valid(rows):
            valid_timetables.append(rows)
            kept += 1
        else:
            discarded += 1

    if not valid_timetables:
        print("No timetables passed the filter.")
        return

    fieldnames = list(valid_timetables[0][0].keys())

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for rows in valid_timetables:
            for row in rows:
                writer.writerow(row)

    print(f"Original timetables: {kept + discarded}")
    print(f"Kept:               {kept}")
    print(f"Discarded:           {discarded}")
    print(f"Saved to:            {output_file}")


def main():
    filter_timetables(INPUT_FILE, OUTPUT_FILE)


if __name__ == "__main__":
    main()
