import csv
from collections import defaultdict


INPUT_FILE = "timetables_filtered.csv"
OUTPUT_FILE = "timetables_final.csv"

MONDAY_8_GROUP = "∞"

EVENING_START = 18 * 60 + 30       # 18:30
ONE_HOUR = 60


def time_to_minutes(value):
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def minutes_to_time(value):
    return f"{value // 60:02d}:{value % 60:02d}"


# ------------------------------------------------------------
# Loading
# ------------------------------------------------------------

def load_timetables(filename):
    with open(filename, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        plans = defaultdict(list)

        for row in reader:
            plans[row["timetable_id"]].append(row)

    return plans


# ------------------------------------------------------------
# Merging group-only differences
# ------------------------------------------------------------

def merge_rows(rows):
    """
    Merge rows which represent the same class occurrence
    and differ only in their group.

    Class name is deliberately part of the key.
    Therefore different classes are NEVER merged.
    """

    merged = {}

    for row in rows:

        day = row["day"]
        start = row["time"]
        end = row["end_time"]
        class_type = row["type"]
        name = row["name"]
        classroom = row["classroom"]

        # Monday at 08:00:
        # group is completely irrelevant.
        monday_8 = (
            day == "Poniedziałek"
            and time_to_minutes(start) == 8 * 60
        )

        if monday_8:
            key = (
                day,
                start,
                end,
                class_type,
                name,
                classroom,
            )

        else:
            # Normal merging:
            # group is intentionally NOT part of the key.
            key = (
                day,
                start,
                end,
                class_type,
                name,
                classroom,
            )

        if key not in merged:
            new_row = dict(row)

            if monday_8:
                new_row["group"] = MONDAY_8_GROUP

            merged[key] = new_row

        else:
            # Monday 08:00 is already ∞.
            if monday_8:
                continue

            existing_group = merged[key]["group"]
            new_group = row["group"]

            groups = set()

            if existing_group:
                groups.update(
                    x.strip()
                    for x in existing_group.split("-")
                    if x.strip()
                )

            if new_group:
                groups.add(new_group.strip())

            # Sort numerically when possible.
            def group_sort_key(x):
                try:
                    return (0, int(x))
                except ValueError:
                    return (1, x)

            merged[key]["group"] = "-".join(
                sorted(groups, key=group_sort_key)
            )

    return list(merged.values())


# ------------------------------------------------------------
# Scoring
# ------------------------------------------------------------

def calculate_score(rows):
    """
    Score:

    +1 for every full hour of free time between classes.
    +1 for every full hour after 18:30.

    Lower score = better.
    """

    score = 0

    by_day = defaultdict(list)

    for row in rows:
        by_day[row["day"]].append(row)

    for day, day_rows in by_day.items():

        day_rows.sort(
            key=lambda r: time_to_minutes(r["time"])
        )

        # ---- Gaps between classes ----

        for previous, current in zip(day_rows, day_rows[1:]):

            previous_end = time_to_minutes(
                previous["end_time"]
            )

            current_start = time_to_minutes(
                current["time"]
            )

            gap = current_start - previous_end

            if gap > 0:
                score += gap // ONE_HOUR

        # ---- Evening penalty ----

        for row in day_rows:

            start = time_to_minutes(row["time"])
            end = time_to_minutes(row["end_time"])

            # Count each full hour occurring after 18:30.
            evening_start = max(start, EVENING_START)

            if end > evening_start:
                score += (end - evening_start) // ONE_HOUR

    return score


# ------------------------------------------------------------
# Canonical representation
# ------------------------------------------------------------

def plan_signature(rows):
    """
    Used to detect plans that became identical after group merging.

    Group is excluded because group differences are exactly
    what we're trying to collapse.
    """

    values = []

    for row in rows:
        values.append((
            row["day"],
            row["time"],
            row["end_time"],
            row["type"],
            row["name"],
            row["classroom"],
        ))

    return tuple(sorted(values))


# ------------------------------------------------------------
# Main filtering / merging
# ------------------------------------------------------------

def process(plans):
    unique_plans = {}

    for old_id, rows in plans.items():

        # First merge group-only differences.
        rows = merge_rows(rows)

        # Calculate score after merging.
        score = calculate_score(rows)

        # Remove duplicate plans which became identical.
        signature = plan_signature(rows)

        if signature not in unique_plans:
            unique_plans[signature] = {
                "rows": rows,
                "score": score,
            }

    result = list(unique_plans.values())

    # Highest/worst score first.
    # Therefore lowest/best score ends up at the bottom.
    result.sort(
        key=lambda plan: plan["score"],
        reverse=True,
    )

    return result


# ------------------------------------------------------------
# CSV output
# ------------------------------------------------------------

def save_plans(filename, plans):

    if not plans:
        print("No plans remain.")
        return

    output_columns = [
        "timetable_id",
        "score",
        "day",
        "time",
        "end_time",
        "type",
        "name",
        "group",
        "classroom",
        "week",
    ]

    with open(
        filename,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=output_columns,
        )

        writer.writeheader()

        for new_id, plan in enumerate(plans, 1):

            rows = sorted(
                plan["rows"],
                key=lambda r: (
                    time_to_minutes(r["time"]),
                    r["day"],
                    r["name"],
                ),
            )

            # Better sorting for actual timetable display:
            day_order = {
                "Poniedziałek": 0,
                "Wtorek": 1,
                "Środa": 2,
                "Czwartek": 3,
                "Piątek": 4,
                "Sobota": 5,
                "Niedziela": 6,
            }

            rows.sort(
                key=lambda r: (
                    day_order.get(r["day"], 999),
                    time_to_minutes(r["time"]),
                )
            )

            for row in rows:

                writer.writerow({
                    "timetable_id": new_id,
                    "score": plan["score"],
                    "day": row["day"],
                    "time": row["time"],
                    "end_time": row["end_time"],
                    "type": row["type"],
                    "name": row["name"],
                    "group": row["group"],
                    "classroom": row["classroom"],
                    "week": row["week"],
                })


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print(f"Reading: {INPUT_FILE}")

    original_plans = load_timetables(INPUT_FILE)

    print(
        f"Original plans: {len(original_plans)}"
    )

    plans = process(original_plans)

    print(
        f"Plans after merging: {len(plans)}"
    )

    if plans:
        scores = [p["score"] for p in plans]

        print(f"Best score:  {min(scores)}")
        print(f"Worst score: {max(scores)}")

    save_plans(
        OUTPUT_FILE,
        plans,
    )

    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
