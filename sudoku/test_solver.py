import pytest
from typing import List

from .solver import *

PAIR_ELIMINATION_TEST_CASES: List[Tuple[List[Cell], List[Tuple[int, List[int]]]]] = [
    (
        [[1, 2], [1, 2, 3, 4], [1, 2], [1, 2, 3, 4]],
        [(1, [1, 2]), (3, [1, 2])]
    ),
    (
        [[5, 6], [3, 5, 6], 1, [2, 4, 5, 6], [2, 3, 4, 6, 7], [3, 5, 7], 9, [5, 7], 8],
        [(3, [5, 6]), (4, [3, 6, 7])]
    )
]

@pytest.mark.parametrize("testcase", PAIR_ELIMINATION_TEST_CASES)
def test_eliminate_pairs(testcase: Tuple[List[Cell], List[Tuple[int, List[int]]]]) -> None:
    x, expected = testcase
    res = eliminate_pairs(x, "test")
    assert res == expected, f"Unexpected result: {res}"

DEDUCTION_TEST_CASES: List[Tuple[List[Cell], int, int, DeductionReason]] = [
    ([[1, 2, 3], [3], [1, 2]], 1, 3, DeductionReason.DIRECT_SCANNING),
    ([[1, 2], [1, 3], [1, 3]], 0, 2, DeductionReason.UNIQUE_VALUE),
    ([[1], [1, 2, 3], [2, 3]], 0, 1, DeductionReason.DIRECT_SCANNING)
]

@pytest.mark.parametrize("testcase", DEDUCTION_TEST_CASES)
def test_deduce(testcase: Tuple[List[Cell], int, int, DeductionReason]) -> None:
    x, row, col, expected = testcase
    res = deduce(x, "test")

    assert res == {(row, col, expected)}, f"Unexpected result: {res}"

def test_search_unique_val() -> None:
    """Test search_unique_val function"""
    x = [{1, 2}, {1, 3}, {1, 3}]
    res = search_unique_val(x)
    assert res == [(0, 2)], f"Unexpected result: {res}"

def test_add_number() -> None:
    """Test add_number function"""
    sudoku = Sudoku(2)
    sudoku.add_number(0, 0, 1, DeductionReason.USER_INPUT)  # Example of adding a value to the Sudoku
    sudoku.solve()

    cell = sudoku.m[0][0]
    assert isinstance(cell, int), f"Unexpected cell type: {type(cell)}"
    assert cell == 1

def test_remove_possibility() -> None:
    """Possibility can be removed from a cell"""
    sudoku = Sudoku(2)
    sudoku.remove(0, 0, 1, EliminationReason.DIRECT_SCANNING)  # Example of removing a value from the Sudoku

    cell = sudoku.m[0][0]
    assert isinstance(cell, list), f"Unexpected cell type: {type(cell)}"
    assert 1 not in cell

def test_hidden_pairs_in_same_group() -> None:
    """
    After adding the number 1 to the cell (0, 0), in the first group,
    3 is only possible on the second row,
    so it should be eliminated from cells of other groups in the same row.
    """
    sudoku = Sudoku(2)
    sudoku.m = [
        [[1, 3], [2, 4], [2, 3, 4], [3, 4]],
        [[2, 3, 4], [2, 3, 4], [1, 2, 3], [1, 2, 4]],
        [[2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]],
        [[2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]],
    ]
    sudoku.add_number(0, 0, 1, DeductionReason.USER_INPUT)
    sudoku.solve()

    assert sudoku.m[1][2] == [1, 2]
    assert sudoku.m[1][3] == [1, 2, 4]

def test_hidden_pairs_in_diff_group() -> None:
    """
    After adding the number 4 to the cell (1, 2), in the first group,
    [2, 3] must be on the second row, so it should be eliminated from other cells in the same group.
    """
    sudoku = Sudoku(2)
    sudoku.m = [
        [[1, 2, 3, 4], [1, 2, 3, 4], [2, 3], [2, 3]],
        [[2, 3, 4], [2, 3, 4], [2, 3, 4], 1],
        [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3], [2, 3, 4]],
        [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3], [2, 3, 4]],
    ]
    sudoku.add_number(1, 2, 4, DeductionReason.USER_INPUT)
    sudoku.solve()

    assert sudoku.m[0][0] == [1, 4]
    assert sudoku.m[0][1] == [1, 4]
