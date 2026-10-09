from typing import List

from .solver import *

def test_eliminate_naked_pairs() -> None:
    """
    [1, 2] occurs at position 0 and 2, forming a naked pair.

    Therefore, the values [1, 2] can be eliminated from other positions in the list.
    """
    x: List[List[int] | int] = [[1, 2], [1, 2, 3, 4], [1, 2], [1, 2, 3, 4]]
    res = eliminate_pairs(x, "test")
    assert res == [(1, [1, 2]), (3, [1, 2])], f"Unexpected result: {res}"

def test_eliminate_hidden_pairs() -> None:
    """
    [2, 4] forms a hidden pair at positions 3 and 4.

    Therefore, the values [2, 4] can be eliminated from other positions in the list.
    """
    x: List[List[int] | int] = [[5, 6], [3, 5, 6], 1, [2, 4, 5, 6], [2, 3, 4, 6, 7], [3, 5, 7], 9, [5, 7], 8]
    res = eliminate_pairs(x, "test")
    assert res == [(3, [5, 6]), (4, [3, 6, 7])], f"Unexpected result: {res}"

def test_entry_with_single_possibility() -> None:
    """Test deduce function with an entry that has only one possible value"""
    x: List[List[int] | int] = [[1, 2, 3], [3], [1, 2]]
    res = deduce(x, "test")
    assert res == {(1, 3, DeductionReason.DIRECT_SCANNING)}, f"Unexpected result: {res}"

def test_unique_value_in_list() -> None:
    """Test deduce function with a unique value in the list"""
    x: List[List[int] | int] = [[1, 2], [1, 3], [1, 3]]
    res = deduce(x, "test")
    assert res == {(0, 2, DeductionReason.UNIQUE_VALUE)}, f"Unexpected result: {res}"

def test_unique_value_in_list_2() -> None:
    """
    The second entry seems to have unique value after first entry is deduced,
    but this should not trigger a signal.
    """
    x: List[List[int] | int] = [[1], [1, 2, 3], [2, 3]]
    res = deduce(x, "test")
    assert res == {(0, 1, DeductionReason.DIRECT_SCANNING)}, f"Unexpected result: {res}"

def test_search_unique_val() -> None:
    """Test search_unique_val function"""
    x = [{1, 2}, {1, 3}, {1, 3}]
    res = search_unique_val(x)
    assert res == [(0, 2)], f"Unexpected result: {res}"

def test_sudoku_remove() -> None:
    """Test eliminate_row function"""
    sudoku = Sudoku(2)
    sudoku.remove(0, 0, 1)  # Example of removing a value from the Sudoku

    cell = sudoku.m[0][0]
    assert isinstance(cell, list), f"Unexpected cell type: {type(cell)}"
    assert 1 not in cell

def test_sudoku_add_number() -> None:
    """Test add_number function"""
    sudoku = Sudoku(2)
    sudoku.add_number(0, 0, 1, DeductionReason.USER_INPUT)  # Example of adding a value to the Sudoku
    sudoku.solve()

    cell = sudoku.m[0][0]
    assert isinstance(cell, int), f"Unexpected cell type: {type(cell)}"
    assert cell == 1

def test_sudoku_eliminate_combined_row() -> None:
    """
    In the first group, 3 is only possible on the second row,
    so it should be eliminated from cells of other groups in the same row.
    """
    sudoku = Sudoku(2)
    sudoku.m = [
        [1, [2, 4], [2, 3, 4], [3, 4]],
        [[2, 3, 4], [2, 3, 4], [1, 2, 3], [1, 2, 4]],
        [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]],
        [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]],
    ]

    res = sudoku.eliminate_masked(0, 0)

    print(res)

    assert len(res) == 2, f"Unexpected result length: {len(res)}"
    assert (1, 2, 3,  EliminationReason.MASKED_SCANNING) in res
    assert (1, 3, 3, EliminationReason.MASKED_SCANNING) in res
