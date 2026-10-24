import csv
import re
from collections import defaultdict


INPUT_FILE = "schedule.csv"
OUTPUT_FILE = "timetables.csv"

# Assume every class lasts 90 minutes.
# Change this if your schedule uses a different duration.
CLASS_DURATION = 90

# If False:
#   18:30-20:00 and 19:15-20:45 overlap.
#
# If True:
#   classes marked "parzyste" and "nieparzyste" may occupy
#   the same physical time because they happen in different weeks.
ALLOW_ODD_EVEN_OVERLAP = False


DAYS = {
    "Poniedziałek": 0,
    "Wtorek": 1,
    "Środa": 2,
    "Czwartek": 3,
    "Piątek": 4,
    "Sobota": 5,
    "Niedziela": 6,
}


def time_to_minutes(value):
    """Convert HH:MM into minutes since midnight."""
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def extract_course_name(name):
    """
    Turn e.g.

        /raz na dwa tygodnie - nieparzyste/
        Inżynieria wiedzy i maszynowe uczenie - Laboratorium

    into:

        Inżynieria wiedzy i maszynowe uczenie
    """

    name = name.strip()

    # Anything before the final "/" is scheduling information.
    if "/" in name:
        parts = [p.strip() for p in name.split("/") if p.strip()]
        name = parts[-1]

    # Remove lecture/lab suffix.
    name = re.sub(
        r"\s*-\s*(Laboratorium|Wykład)\s*$",
        "",
        name,
        flags=re.IGNORECASE,
    )

    return name.strip()


def get_week_type(name):
    """Return 'odd', 'even', or None."""
    if "nieparzyste" in name.lower():
        return "odd"

    if "parzyste" in name.lower():
        return "even"

    return None


def load_schedule(filename):
    classes = []

    with open(filename, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            course = extract_course_name(row["name"])

            start = time_to_minutes(row["time"])
            end = start + CLASS_DURATION

            classes.append({
                "day": row["day"],
                "day_index": DAYS.get(row["day"], 999),

                "time": row["time"],
                "start": start,
                "end": end,

                "group": row["group"],
                "name": course,
                "type": row["type"].strip().lower(),

                "classroom": row["classroom"],
                "week": get_week_type(row["name"]),
            })

    return classes


def overlaps(a, b):
    """Return True if two classes overlap."""
    if a["day"] != b["day"]:
        return False

    # Optional handling of alternating weeks.
    if ALLOW_ODD_EVEN_OVERLAP:
        if (
            a["week"] is not None
            and b["week"] is not None
            and a["week"] != b["week"]
        ):
            return False

    return (
        a["start"] < b["end"]
        and b["start"] < a["end"]
    )


def build_class_groups(classes):
    """
    Create one group for every:

        (type, actual course name)

    Example:

        ('lab', 'Systemy wbudowane')
        ('lecture', 'Systemy wbudowane')
    """

    groups = defaultdict(list)

    for cls in classes:
        key = (cls["type"], cls["name"])
        groups[key].append(cls)

    return groups


def generate_timetables(groups):
    """
    Backtracking search.

    For every [type, course] group, choose exactly one
    available class occurrence.

    Any choice overlapping an already selected class
    is rejected immediately.
    """

    # Process classes with fewer possibilities first.
    # This makes the search considerably faster.
    ordered_groups = sorted(
        groups.items(),
        key=lambda item: len(item[1]),
    )

    timetable = []

    def search(index):
        if index == len(ordered_groups):
            yield list(timetable)
            return

        class_key, options = ordered_groups[index]

        for option in options:

            # Check against everything already selected.
            if any(overlaps(option, selected)
                   for selected in timetable):
                continue

            timetable.append(option)

            yield from search(index + 1)

            timetable.pop()

    yield from search(0)


def sort_timetable(timetable):
    return sorted(
        timetable,
        key=lambda x: (
            x["day_index"],
            x["start"],
            x["type"],
            x["name"],
        ),
    )


def save_timetables(filename, timetables):
    """
    Save all timetables into one CSV.

    Each timetable gets its own timetable_id.
    """

    columns = [
        "timetable_id",
        "day",
        "time",
        "end_time",
        "type",
        "name",
        "group",
        "classroom",
        "week",
    ]

    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()

        for timetable_id, timetable in enumerate(timetables, 1):
            for cls in sort_timetable(timetable):
                end_hour = cls["end"] // 60
                end_minute = cls["end"] % 60

                writer.writerow({
                    "timetable_id": timetable_id,
                    "day": cls["day"],
                    "time": cls["time"],
                    "end_time": f"{end_hour:02d}:{end_minute:02d}",
                    "type": cls["type"],
                    "name": cls["name"],
                    "group": cls["group"],
                    "classroom": cls["classroom"],
                    "week": cls["week"] or "",
                })


def main():
    classes = load_schedule(INPUT_FILE)

    groups = build_class_groups(classes)

    print(f"Loaded {len(classes)} schedule entries.")
    print(f"Required classes: {len(groups)}")
    print()

    for key, options in groups.items():
        class_type, name = key
        print(f"{class_type:8} | {name}")
        print(f"         {len(options)} possible occurrence(s)")

    print()
    print("Generating timetables...")

    timetables = list(generate_timetables(groups))

    print(f"Found {len(timetables)} possible timetable(s).")

    save_timetables(OUTPUT_FILE, timetables)

    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
