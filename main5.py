import csv
from collections import defaultdict, Counter


INPUT_FILE = "timetables_final.csv"
OUTPUT_FILE = "timetable_stats.txt"


DAY_ORDER = {
    "Poniedziałek": 0,
    "Wtorek": 1,
    "Środa": 2,
    "Czwartek": 3,
    "Piątek": 4,
    "Sobota": 5,
    "Niedziela": 6,
}


def time_to_minutes(value):
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def format_percent(value, total):
    if total == 0:
        return "0.0%"

    return f"{100 * value / total:5.1f}%"


def load_file(filename):
    """
    Read the final timetable CSV.

    Returns:

        {
            timetable_id: {
                "score": int,
                "rows": [...]
            }
        }
    """

    plans = {}

    with open(
        filename,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            timetable_id = row["timetable_id"]
            score = int(row["score"])

            if timetable_id not in plans:
                plans[timetable_id] = {
                    "score": score,
                    "rows": [],
                }

            plans[timetable_id]["rows"].append(row)

    return plans


def split_groups(group):
    """
    Turn:

        1-2-3 -> ["1", "2", "3"]
        ∞     -> ["∞"]
        1     -> ["1"]
    """

    if not group:
        return [""]

    return [
        part.strip()
        for part in group.split("-")
        if part.strip()
    ]


def make_statistics(plans):
    """
    Build statistics separately for every score.
    """

    stats = defaultdict(
        lambda: {
            "plans": 0,

            # class -> number of plans containing it
            "classes": Counter(),

            # (class, group) -> number of plans
            "groups": Counter(),

            # (class, day, time) -> number of plans
            "times": Counter(),

            # (class, group, day, time) -> number of plans
            "group_times": Counter(),
        }
    )

    for plan in plans.values():

        score = plan["score"]
        stats[score]["plans"] += 1

        # Avoid counting the same class twice inside one plan.
        classes_in_plan = set()
        groups_in_plan = set()
        times_in_plan = set()
        group_times_in_plan = set()

        for row in plan["rows"]:

            class_key = (
                row["type"],
                row["name"],
            )

            classes_in_plan.add(class_key)

            # A merged group such as 1-2-3 represents
            # all three possible groups.
            groups = split_groups(row["group"])

            for group in groups:

                groups_in_plan.add(
                    (class_key, group)
                )

                group_times_in_plan.add(
                    (
                        class_key,
                        group,
                        row["day"],
                        row["time"],
                    )
                )

            times_in_plan.add(
                (
                    class_key,
                    row["day"],
                    row["time"],
                )
            )

        for key in classes_in_plan:
            stats[score]["classes"][key] += 1

        for key in groups_in_plan:
            stats[score]["groups"][key] += 1

        for key in times_in_plan:
            stats[score]["times"][key] += 1

        for key in group_times_in_plan:
            stats[score]["group_times"][key] += 1

    return stats


def print_class_statistics(out, score, data):
    total = data["plans"]

    out.write("\n")
    out.write("=" * 80 + "\n")
    out.write(f"SCORE {score}    ({total} plans)\n")
    out.write("=" * 80 + "\n")

    # Sort classes by type/name.
    classes = sorted(
        data["classes"],
        key=lambda x: (x[0], x[1]),
    )

    for class_type, name in classes:

        class_key = (class_type, name)
        count = data["classes"][class_key]

        out.write("\n")
        out.write(
            f"[{class_type}] {name}\n"
        )

        out.write(
            f"  occupied: {count}/{total} "
            f"({format_percent(count, total)})\n"
        )

        # ------------------------------------------------
        # Groups
        # ------------------------------------------------

        group_stats = []

        for (key, group), count in data["groups"].items():

            if key == class_key:
                group_stats.append(
                    (group, count)
                )

        group_stats.sort(
            key=lambda x: (
                x[0] == "∞",
                x[0],
            )
        )

        if group_stats:
            out.write("  groups:\n")

            for group, count in group_stats:

                out.write(
                    f"    group {group:>5}: "
                    f"{count:>5}/{total} "
                    f"({format_percent(count, total)})\n"
                )

        # ------------------------------------------------
        # Times
        # ------------------------------------------------

        time_stats = []

        for (key, day, time), count in data["times"].items():

            if key == class_key:
                time_stats.append(
                    (day, time, count)
                )

        time_stats.sort(
            key=lambda x: (
                DAY_ORDER.get(x[0], 999),
                time_to_minutes(x[1]),
            )
        )

        if time_stats:
            out.write("  times:\n")

            for day, time, count in time_stats:

                out.write(
                    f"    {day:<12} {time}: "
                    f"{count:>5}/{total} "
                    f"({format_percent(count, total)})\n"
                )

        # ------------------------------------------------
        # Group + time
        # ------------------------------------------------

        gt_stats = []

        for (
            key,
            group,
            day,
            time,
        ), count in data["group_times"].items():

            if key == class_key:
                gt_stats.append(
                    (group, day, time, count)
                )

        gt_stats.sort(
            key=lambda x: (
                DAY_ORDER.get(x[1], 999),
                time_to_minutes(x[2]),
                x[0],
            )
        )

        if gt_stats:
            out.write("  group + time:\n")

            for group, day, time, count in gt_stats:

                out.write(
                    f"    group {group:>5} | "
                    f"{day:<12} {time}: "
                    f"{count:>5}/{total} "
                    f"({format_percent(count, total)})\n"
                )


def generate_report(stats):
    """
    Scores are printed from worst to best, matching the CSV.

    Therefore the final section is the best score.
    """

    lines = []

    # Summary first.
    lines.append("TIMETABLE STATISTICS")
    lines.append("=" * 80)
    lines.append("")
    lines.append(
        "Plans by score:"
    )

    for score in sorted(stats, reverse=True):

        count = stats[score]["plans"]

        lines.append(
            f"  score {score:>3}: {count:>6} plans"
        )

    # Detailed statistics.
    class_output = []

    # Use StringIO-like list handling through a temporary
    # text stream.
    import io

    for score in sorted(stats, reverse=True):

        buffer = io.StringIO()

        print_class_statistics(
            buffer,
            score,
            stats[score],
        )

        class_output.append(
            buffer.getvalue()
        )

    lines.extend(class_output)

    return "\n".join(lines)


def main():

    print(f"Reading {INPUT_FILE}...")

    plans = load_file(INPUT_FILE)

    print(
        f"Loaded {len(plans)} timetable plans."
    )

    stats = make_statistics(plans)

    report = generate_report(stats)

    # Screen
    print()
    print(report)

    # File
    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        f.write(report)

    print()
    print(
        f"Statistics saved to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
