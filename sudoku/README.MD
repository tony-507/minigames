# Sudoku

This folder contains a Sudoku solver that repeatedly applies candidate-elimination and single-cell deduction strategies.

The solver does not guess or backtrack, so it may stop with unsolved cells when its implemented strategies cannot make further progress. It does not check whether a puzzle has a unique solution.

## Input and usage

The board must be a square 2-D list whose side length is itself a square (for example, 4×4 or 9×9). Use `0` for an empty cell and values from `1` through the board side length for clues. The solver infers the box dimensions from the board size.

From the repository root, run a puzzle with:

```sh
python -m sudoku.solver solve '[[1,0,0,4],[0,4,1,0],[0,1,4,0],[4,0,0,1]]'
```

The program displays the board as values are placed; `?` represents an unresolved cell. The current command-line and `solve()` entry points are interactive: press Enter at the `$>` prompt after each placement to continue. Use `-v` before `solve` to enable detailed elimination logging:

```sh
python -m sudoku.solver -v solve '[[1,0,0,4],[0,4,1,0],[0,1,4,0],[4,0,0,1]]'
```

## Strategies

Strategies run in two phases whenever a value is placed.

### Candidate elimination

- **Peer elimination:** remove the placed value from other cells in its row, column, and box.
- **Subset elimination:** when *k* values have the same *k* candidate positions in a unit, restrict those cells to those values and remove them from the other cells in the unit. This covers naked and hidden subsets.
- **Pointing candidates:** when a value's candidates in a box all lie in one row or column, remove that value from the rest of that row or column outside the box.

Here, a *unit* means a row, column, or box. The solver applies subset elimination within each row, column, and box, and pointing-candidate elimination from the box containing each newly placed value.

### Deductions

- **Naked single:** fill a cell with its only remaining candidate.
- **Hidden single:** fill a value in a unit when it is a candidate in only one cell of that unit.
