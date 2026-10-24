#!/usr/bin/env python3
import numpy as np

classes = {
    "u":"systemy bezzałogowe",
    "i":"uczenie maszynowe",
    "e":"systemy wbudowane",
    "t":"technologie internetowe",
    "m":"aplikacje mobilne",
    "c":"sieci korporacyjne",
    "p":"modele językowe",
    "r":"routing ip",
    "d":"pracownia dyplomowa"
    }

def print_tables(tables):
    for table_id, a in tables:
        a = np.asarray(a)

        if a.ndim == 1:
            a = a.reshape(1, -1)

        widths = [
            max(len(str(a[i, j])) for i in range(a.shape[0])) + 2
            for j in range(a.shape[1])
        ]

        border = "+" + "+".join("-" * w for w in widths) + "+"

        print(f"\n[{table_id}]")
        print(border)

        for row in a:
            print("|" + "|".join(
                f" {str(x):<{w-1}}" for x, w in zip(row, widths)
            ) + "|")
            print(border)


def main():
    pass


if __name__ == "__main__":
    main()
