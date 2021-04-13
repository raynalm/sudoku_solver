#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: Maxime Raynal <maxime.raynal@protonmail.com>
# LICENSE: MIT


import subprocess
import os
from itertools import combinations


def grid_from_file(filename):
    """Reads a grid stored in a file"""
    # read lines of file
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
    # fill up grid (and pad to make sure dimensions are 9x9)
    grid = []
    for line in lines:
        if len(line) < 9:
            line += " " * (9 - len(line))
        grid += [[int(c) if c != ' ' else None for c in line]]
    if len(grid) < 9:
        grid += [[None for _ in range(9)] for __ in range(9 - len(grid))]
    return grid


def constraints_from_grid(grid):
    """
    Models the sudoku into boolean constraints.
    Variable 'x_i_j_k' is true iff the number k is in the cell (i,j).
    Preceded by a '-' if the variable is negated.
    So we have 9x9x9 = 729 variables.
    All constraints wiil be expressed deirectly as FNCs.
    Stored as list(product) of lists(clauses).
    The principle of the pigeon hole (théorème des tiroirs) is used extensively
    to simplify the constraints expression.
    """
    constraints = []
    # Write grid information as constraints
    for i in range(9):
        for j in range(9):
            if grid[i][j] is not None:
                constraints += [[f"x_{i}_{j}_{grid[i][j]}"]]
    #  There must be one number in each cell
    constraints += [
        [f"x_{i}_{j}_{k}" for k in range(1, 10)]
        for j in range(9)
        for i in range(9)
    ]
    # There cannot be two number at once in a cell
    constraints += [
        [f"-x_{i}_{j}_{k1}", f"-x_{i}_{j}_{k2}"]
        for k1, k2 in combinations(range(1, 10), 2)
        for j in range(9)
        for i in range(9)
    ]
    # Each digit between 1 and 9 appears at least once on each row/column
    # rows
    constraints += [
        [f"x_{i}_{j}_{k}" for j in range(9)]
        for i in range(9) for k in range(1, 10)
    ]
    # columns
    constraints += [
        [f"x_{i}_{j}_{k}" for i in range(9)]
        for j in range(9) for k in range(1, 10)
    ]
    # Each digit appears at least once in each subsquare
    constraints += [
        [f"x_{shift_i + i}_{shift_j + j}_{k}"
         for i in range(3) for j in range(3)]
        for shift_i in range(0, 9, 3) for shift_j in range(0, 9, 3)
        for k in range(1, 10)
    ]
    return constraints


def dimacs_string_from_constraints(constraints):
    """Numbering rule: (i, j, k) --> 100*i + 10*j + k."""
    def to_int(var_name):
        k, j, i = tuple(int(var_name.split('_')[-i]) for i in range(1, 4))
        return (100 * i + 10 * j + k) * (-1 if var_name.startswith('-') else 1)

    num_clauses, num_variables = len(constraints), 100*8 + 10*8 + 9
    return f"p cnf {num_variables} {num_clauses}\n" + '\n'.join(
        ' '.join(str(to_int(var_name)) for var_name in constraint) + ' 0'
        for constraint in constraints
    )


def solution_from_dimacs_string(dimacs_str):
    # write the dimacs into a file
    with open("constraints.dimacs.tmp", 'w') as f:
        f.write(dimacs_str)
    # run a solver (here minisat)
    subprocess.run(["minisat", "constraints.dimacs.tmp", "out.tmp"])
    with open("out.tmp", 'r') as output:
        solution_as_str = output.read().splitlines()

    os.remove("constraints.dimacs.tmp")
    os.remove("out.tmp")

    if solution_as_str[0] == 'UNSAT':
        return "UNSAT"
    # else
    solution_as_str = {int(i) for i in solution_as_str[1].split()}
    solution_grid = [[None for _ in range(9)] for __ in range(9)]
    for i in range(9):
        for j in range(9):
            for k in range(1, 10):
                if 100 * i + 10 * j + k in solution_as_str:
                    solution_grid[i][j] = k
    return solution_grid
