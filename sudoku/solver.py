"""
A Sudoku solver following human-like strategies.

Note it can't solve Sudoku puzzles that require guessing.
"""

import argparse
import ast
from dataclasses import dataclass, field
from enum import Enum
import logging
import math
import sys
from typing import Dict, List, Set, Tuple, Union

from common.styles import RED, RESET

logger = logging.getLogger(__name__)

UNKNOWN_CHAR = '?'

def configure_logging(level: int) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(message)s'))
    handler.setLevel(level)
    logger.addHandler(handler)
    logger.setLevel(level)

class DeductionReason(Enum):
    USER_INPUT = 1
    DIRECT_SCANNING = 2
    UNIQUE_VALUE = 3

class EliminationReason(Enum):
    DIRECT_SCANNING = 1
    MASKED_SCANNING = 2

@dataclass
class SudokuInput:
    row: int
    col: int
    val: int
    reason: DeductionReason = field(compare=False)

class Sudoku:
    m: List[List[Union[List[int], int]]]
    last_updated: Tuple[int, int]
    jobs: List[SudokuInput]
    size: int
    interactive: bool

    def __init__(self, n: int, interactive: bool = False) -> None:
        """Build a board with all possible values"""
        self.m = []
        self.jobs = []
        self.size = n
        self.interactive = interactive
        self.last_updated = (-1, -1)
        for _ in range(n * n):
            newRow: List[Union[List[int], int]] = []
            for _ in range(n * n):
                newRow.append(list(range(1, n * n + 1)))
            self.m.append(newRow)

    def solve(self) -> None:
        """Solve the Sudoku puzzle using human-like strategies."""
        if not self.jobs:
            logger.info("Nothing to solve")
            return
        while self.jobs:
            job = self.jobs.pop(0)
            logger.info(f"Due to {job.reason.name}, ({job.row}, {job.col}) = {job.val}")
            try:
                self.work(job.row, job.col, job.val)
            except Exception as e:
                logger.error(f"Error processing job '({job.row}, {job.col}) = {job.val}': {e}")
                break

    def add_number(self, row: int, col: int, val: int, reason: DeductionReason) -> None:
        """Add a number to the Sudoku board and update possibilities."""
        newJob = SudokuInput(row, col, val, reason)
        if newJob not in self.jobs:
            self.jobs.append(newJob)

    def work(self, row: int, col: int, val: int) -> None:
        """
        Write val to (row, col).

        Eliminate impossible values from the board.
        """
        n = self.size * self.size
        if row not in range(n + 1):
            raise Exception(f"Invalid row {row}")

        if col not in range(n + 1):
            raise Exception(f"Invalid column {col}")

        if not (0 < val <= n):
            raise Exception(f"Invalid value {val}")

        if isinstance(self.m[row][col], int):
            # Defensive
            if self.m[row][col] != val:
                raise Exception(f"Cell ({row}, {col}) is already filled with {self.m[row][col]}")
            # Early exit
            else:
                return

        self.m[row][col] = val
        self.last_updated = (row, col)

        self.display()

        if self.interactive:
            input("$>")

        # Elimination phase
        self.eliminate_phase(row, col, val)

        g_row = row // self.size
        g_col = col // self.size

        # Deduction phase
        for i in range(n):
            self.row_deduce(i)
            self.col_deduce(i)
        group_vals = [self.m[g_row * self.size + i][g_col * self.size + j] for i in range(self.size) for j in range(self.size)]
        self.group_deduce(g_row, g_col, group_vals)

    def eliminate_phase(self, row: int, col: int, val: int) -> None:
        """
        Eliminate impossible values from the entire board.
        """
        res: List[Tuple[int, int, int, EliminationReason]] = []
        res.extend(self.eliminate_row(row, col, val))
        res.extend(self.eliminate_col(row, col, val))
        res.extend(self.eliminate_group(row, col, val))

        for (r, c, v, reason) in res:
            logger.debug(f"Eliminating ({r}, {c}) != {v} due to {reason}")
            self.remove(r, c, v)

        for (r, c, v, reason) in self.eliminate_masked(row, col):
            logger.debug(f"Eliminating ({r}, {c}) != {v} due to {reason}")
            self.remove(r, c, v)

    def eliminate_row(self, row: int, col: int, val: int) -> List[Tuple[int, int, int, EliminationReason]]:
        """Check and eliminate the value from the row."""
        n = self.size * self.size
        res: List[Tuple[int, int, int, EliminationReason]] = []
        for i in range(n):
            if i == col:
                continue
            res.append((row, i, val, EliminationReason.DIRECT_SCANNING))

        for (idx, vals) in eliminate_pairs(self.m[row], f"row {row}"):
            for val in vals:
                res.append((row, idx, val, EliminationReason.DIRECT_SCANNING))

        return res

    def eliminate_col(self, row: int, col: int, val: int) -> List[Tuple[int, int, int, EliminationReason]]:
        """Check and eliminate the value from the column."""
        n = self.size * self.size
        res: List[Tuple[int, int, int, EliminationReason]] = []
        for i in range(n):
            if i == row:
                continue
            res.append((i, col, val, EliminationReason.DIRECT_SCANNING))

        for (idx, vals) in eliminate_pairs([ r[col] for r in self.m ], f"col {col}"):
            for val in vals:
                res.append((idx, col, val, EliminationReason.DIRECT_SCANNING))

        return res

    def eliminate_group(self, row: int, col: int, val: int) -> List[Tuple[int, int, int, EliminationReason]]:
        """Check and eliminate the value from the group."""
        g_row = row // self.size
        g_col = col // self.size

        res: List[Tuple[int, int, int, EliminationReason]] = []

        for i in range(self.size):
            for j in range(self.size):
                res.append((g_row * self.size + i, g_col * self.size + j, val, EliminationReason.DIRECT_SCANNING))

        group_vals = [self.m[g_row * self.size + i][g_col * self.size + j] for i in range(self.size) for j in range(self.size)]
        for (idx, vals) in eliminate_pairs(group_vals, f"group ({g_row}, {g_col})"):
            mapped_row = idx // self.size
            mapped_col = idx % self.size
            for val in vals:
                res.append((g_row * self.size + mapped_row, g_col * self.size + mapped_col, val, EliminationReason.DIRECT_SCANNING))

        return res

    def eliminate_masked(self, row: int, col: int) -> List[Tuple[int, int, int, EliminationReason]]:
        """
        In a group, if a value is only possible on a row/column,
        eliminate the value from the remaining rows/columns in the group.
        """
        n = self.size * self.size
        g_row = row // self.size
        g_col = col // self.size

        res: List[Tuple[int, int, int, EliminationReason]] = []

        row_union: List[Set[int]] = [set() for _ in range(self.size)]
        col_union: List[Set[int]] = [set() for _ in range(self.size)]
        for idx in range(n):
            mapped_row = idx // self.size
            mapped_col = idx % self.size
            actual_row = g_row * self.size + mapped_row
            actual_col = g_col * self.size + mapped_col
            curr_value = self.m[actual_row][actual_col]
            curr_set: Set[int] = set()
            if not isinstance(curr_value, int):
                curr_set = set(curr_value)
            row_union[mapped_row] |= curr_set
            col_union[mapped_col] |= curr_set

        for (idx, val) in search_unique_val(row_union):
            actual_row = g_row * self.size + idx
            for i in range(n):
                g_idx = i // self.size
                if g_idx != g_col:
                    res.append((actual_row, i, val, EliminationReason.MASKED_SCANNING))

        for (idx, val) in search_unique_val(col_union):
            actual_col = g_col * self.size + idx
            for i in range(n):
                g_idx = i // self.size
                if g_idx != g_row:
                    res.append((i, actual_col, val, EliminationReason.MASKED_SCANNING))

        return res

    def row_deduce(self, row: int) -> None:
        """Check a specific row for possible fills"""
        res = deduce(self.m[row], f"row {row}")
        for (idx, val, reason) in res:
            self.add_number(row, idx, val, reason)

    def col_deduce(self, col: int) -> None:
        """Check a specific column for possible fills"""
        res = deduce([ r[col] for r in self.m ], f"col {col}")
        for (idx, val, reason) in res:
            self.add_number(idx, col, val, reason)

    def group_deduce(self, g_row: int, g_col: int, group_vals: List[Union[List[int], int]]) -> None:
        res = deduce(group_vals, f"group ({g_row}, {g_col})")
        for (i, val, reason) in res:
            mapped_row = i // self.size
            mapped_col = i % self.size
            self.add_number(g_row * self.size + mapped_row, g_col * self.size + mapped_col, val, reason)

    def remove(self, row: int, col: int, val: int) -> None:
        """Remove the possibility of (row, col) to be val"""
        cell = self.m[row][col]
        if isinstance(cell, int):
            return

        if val not in cell:
            return

        cell.remove(val)

    def display(self) -> None:
        """Show the Sudoku"""
        s = ""
        n = self.size * self.size
        for row_idx, row in enumerate(self.m):
            s += "-" * n * 6 + "\n"
            for idx, v in enumerate(row):
                if isinstance(v, int):
                    if (row_idx, idx) == self.last_updated:
                        s += f"|{RED}{v:^5}{RESET}"
                    else:
                        s += f"|{v:^5}"
                else:
                    s += f"|{UNKNOWN_CHAR:^5}"
            s += "|\n"
        s += "-" * n * 6 + "\n"
        print(s)


def deduce(x: List[Union[List[int], int]], id: str) -> Set[Tuple[int, int, DeductionReason]]:
    """
    Scan for possible fills. Return an entry to fill.

    1. If an entry contains a single possible value, write it.

    2. If an entry contains a value not present in other entries, write it.
    """
    res: Set[Tuple[int, int, DeductionReason]] = set()
    unique_entries: Dict[int, int] = {}
    for i, val in enumerate(x):
        if not isinstance(val, int):
            if len(val) == 1:
                res.add((i, val[0], DeductionReason.DIRECT_SCANNING))
            for v in val:
                if v not in unique_entries:
                    unique_entries[v] = i
                else:
                    unique_entries[v] = -1
        else:
            # We should not fill again for entries that are already determined
            if val in unique_entries:
                unique_entries[val] = -1

    for val, pos in unique_entries.items():
        if pos != -1:
            res.add((pos, val, DeductionReason.UNIQUE_VALUE))

    return res

def eliminate_pairs(x: List[Union[List[int], int]], id: str) -> List[Tuple[int, List[int]]]:
    """
    Try to eliminate possibilities based on hidden pairs.

    If a list of N numbers appears exactly N times on the same N positions, those values can be eliminated from other entries.
    """
    possibilities: List[List[int]] = []
    for _ in range(len(x)):
        possibilities.append([])

    for idx, val in enumerate(x):
        if not isinstance(val, int):
            for v in val:
                possibilities[v - 1].append(idx)

    list_counts: Dict[str, int] = {}
    for l in possibilities:
        key = ",".join(map(str, l))
        if key not in list_counts:
            list_counts[key] = 0
        list_counts[key] += 1

    rv: List[Tuple[int, List[int]]] = []
    for key, count in list_counts.items():
        l = list(map(int, key.split(","))) if key else []
        if count == len(l):
            values = [i + 1 for i, p in enumerate(possibilities) if p == l]
            for i in range(len(x)):
                orig_vals = x[i]
                if not isinstance(orig_vals, int):
                    to_eliminate: List[int] = []
                    if i in l:
                        to_eliminate = [v for v in orig_vals if v not in values]
                    else:
                        to_eliminate = [v for v in orig_vals if v in values]

                    if to_eliminate:
                        rv.append((i, to_eliminate))

    return rv

def search_unique_val(x: List[Set[int]]) -> List[Tuple[int, int]]:
    """
    Search for unique values in a list of sets.

    Return a list of tuples (index, value) where the value is unique in the list.
    """
    res: List[Tuple[int, int]] = []
    unique_entries: Dict[int, int] = {}
    for i, val in enumerate(x):
        for v in val:
            if v not in unique_entries:
                unique_entries[v] = i
            else:
                unique_entries[v] = -1

    for val, i in unique_entries.items():
        if i != -1:
            res.append((i, val))

    return res

def parse(args: argparse.Namespace):
    """Solve the Sudoku, and print the result"""
    s = ast.literal_eval(args.sudoku)
    sudoku = solve(s)
    sudoku.display()

def solve(s: List[List[int]]) -> Sudoku:
    n = len(s)
    for row in s:
        if len(row) != n:
            raise Exception(f"Invalid row size {len(row)} != {n}")

    sudoku = Sudoku(int(math.sqrt(n)), True)

    for i, row in enumerate(s):
        for j, val in enumerate(row):
            if val != 0:
                sudoku.add_number(i, j, val, DeductionReason.USER_INPUT)

    sudoku.solve()
    return sudoku

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    subparsers = parser.add_subparsers(title='subcommands', description='valid subcommands', help='additional help')

    solver_parser = subparsers.add_parser('solve', help='Solve a Sudoku puzzle')
    solver_parser.add_argument('sudoku', help='2-D array representing the Sudoku in (row, col) format. Empty field should be represented by 0')
    solver_parser.set_defaults(func=parse)

    args = parser.parse_args()
    configure_logging(logging.DEBUG if args.verbose else logging.INFO)

    args.func(args)
