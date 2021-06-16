from CSP import Constraint, ConstraintSatisfactionProblem, print_sudoku
from typing import Dict, List, Optional
import time
import json


# A map constraint is a two way constraint between two variables
class MapConstraint(Constraint[str, str]):
    def __init__(self, place1: str, place2: str) -> None:
        super().__init__([place1, place2])
        self.place1: str = place1
        self.place2: str = place2

    def is_satisfied(self, assignment: Dict[str, str]) -> bool:
        # If either place is not in the assignment then it is not
        # yet possible for their colors to be conflicting
        if self.place1 not in assignment or self.place2 not in assignment:
            return True
        # check the color assigned to place1 is not the same as the
        # color assigned to place2
        return assignment[self.place1] != assignment[self.place2]


# A sudoku constraint is shared between 9 variables. It is not directional, so all 9 variables actually share this
class SudokuConstraint(Constraint[str, int]):
    def __init__(self, places: List[str]):
        super().__init__(places)

    def is_satisfied(self, assignment: Dict[str, int]) -> bool:
        # For each assigned variable
        for index in range(len(self.variables)):
            variable = self.variables[index]
            if variable in assignment:
                # Every other variable in the row/cell
                # We only check the values forward from the current index since previous
                # indices have already been checked for equality
                for i in range(index + 1, len(self.variables)):
                    variable_2 = self.variables[i]
                    if variable_2 in assignment:
                        # If the domain of the variables are the same
                        if assignment[variable] == assignment[variable_2]:
                            # Constraint is not satisfied
                            return False
        return True


# A method used to parse the json, specify the domains and add the constraints
def createMapCSP() -> ConstraintSatisfactionProblem:
    csp: ConstraintSatisfactionProblem[str, str] = None
    with open('gcp.json', 'r') as f:
        data = json.load(f)
        print(data)
        variables: List[str] = []
        domains: Dict[str, List[str]] = {}
        for key in data['points']:
            variables.append(key)
            domains[key] = ["red", "green", "blue", "purple"]
        csp = ConstraintSatisfactionProblem(variables, domains)
        for edge in data['edges']:
            csp.add_constraint(MapConstraint(str(edge[0]), str(edge[1])))
    return csp


# A method to parse the json, specify the domains, specify the initial assignment and add the constraints
# There is not 2d array or anything like that that makes up the sudoku board
# The board's structure is dictated simply by the constraints and saved in a list of variables
# with variable values in the format '##' where the first number is the column and the second is the row
def createSudokuCSP() -> ConstraintSatisfactionProblem:
    csp: ConstraintSatisfactionProblem = None
    with open('sudoku.json', 'r') as f:
        table = json.load(f)
        variables = []
        domains: Dict[str, List[int]] = {}
        assignments: Dict[str, int] = {}
        # For each column
        for col in range(0, 9):
            # For each row
            for row in range(0, 9):
                # The key is '##' where 1 <= # <= 9 and it's '[col][row]'
                key = str(col + 1) + str(row + 1)
                # Add this key to the list of all variables
                variables.append(key)
                # The domain of a pre-assigned space is that one value (not necessary, but just for consistency)
                # The domain of a non-assigned space is 1-9
                if table[col][row] != 0:
                    domains[key] = [table[col][row]]
                    assignments[key] = table[col][row]
                else:
                    domains[key] = list(range(1, 10))

        csp = ConstraintSatisfactionProblem(variables, domains, initial_assignments=assignments, sudoku= True)
        # Horizontal Constraints
        for col in range(len(table)):
            row_list: List[str] = []
            for row in range(len(table)):
                row_list.append(str(col + 1) + str(row + 1))
            csp.add_constraint(SudokuConstraint(row_list))

        # Vertical Constraints
        for row in range(len(table)):
            col_list = []
            for col in range(len(table)):
                col_list.append(str(col + 1) + str(row + 1))
            csp.add_constraint(SudokuConstraint(col_list))

        # Cell Constraints
        for cell_row in range(0, 3):
            for cell_col in range(0, 3):
                cell_list = []
                for row in range(0, 3):
                    for col in range(0, 3):
                        cell_list.append(str(3 * cell_row + row + 1) + str(3 * cell_col + col + 1))
                csp.add_constraint(SudokuConstraint(cell_list))
    return csp


if __name__ == "__main__":
    variables: List[str] = []
    csp = createSudokuCSP()
    start = time.time()
    solution: Optional[Dict[str, int]] = csp.solve()
    print("Time: " + str(time.time() - start))
    if solution is None:
        print("No solution found!")
    else:
        print_sudoku(solution)
        print("Solution Found")
        print(solution)

    csp = createMapCSP()
    start = time.time()
    solution: Optional[Dict[str, str]] = csp.solve()
    print("Time: " + str(time.time() - start))
    if solution is None:
        print("No solution found!")
    else:
        print("Solution Found")
        print(solution)
