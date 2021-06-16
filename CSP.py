import sys
from collections import deque
from typing import Generic, TypeVar, Dict, List, Optional

Variable = TypeVar('Variable')
Domain = TypeVar('Domain')


def print_sudoku(assignment: [Dict[str, str]]):
    for row in range(1, 10):
        if not row == 1 and (row - 1) % 3 == 0:
            print("----------------------")
        print(str(assignment.get('1' + str(row), ' ')) + " " +
              str(assignment.get('2' + str(row), ' ')) + " " +
              str(assignment.get('3' + str(row), ' ')) + " | " +
              str(assignment.get('4' + str(row), ' ')) + " " +
              str(assignment.get('5' + str(row), ' ')) + " " +
              str(assignment.get('6' + str(row), ' ')) + " | " +
              str(assignment.get('7' + str(row), ' ')) + " " +
              str(assignment.get('8' + str(row), ' ')) + " " +
              str(assignment.get('9' + str(row), ' ')))
    print()


class Constraint(Generic[Variable, Domain]):

    # A constraint is between any number of variables, so I use a list
    def __init__(self, variables: List[Variable]) -> None:
        # These variables will all share this constraint
        self.variables = variables

    # Gets all variables in this constraint that are not the provided variable
    def get_neighbors(self, variable):
        neighbors = []
        for potential_neighbor in self.variables:
            if potential_neighbor != variable:
                neighbors.append(potential_neighbor)
        return neighbors

    # Abstract Method
    def is_satisfied(self, assignment: Dict[Variable, Domain]) -> bool:
        ...


class ConstraintSatisfactionProblem(Generic[Variable, Domain]):
    def __init__(self, variables: List[Variable], initial_domains: Dict[Variable, List[Domain]], initial_assignments: Dict[Variable, Domain] = {}, sudoku: bool = False):
        # Enable infinite loop checking
        self.loop_check = False
        # Enable sudoku-specific print statements
        self.sudoku = sudoku
        # Enable forward checking (mutually exclusive with ac3)
        self.forward = True
        # Enable ac3 (mututally exclusive with forward checking)
        self.ac3 = False
        # Enable the minimum value remaining heuristic
        self.min_remain = True
        # Enable the degree heuristic (requires min_remain)
        self.degree = True
        # Toggle between the degree being based off remaining variables or assigned variables
        # In my report, True is the traditional definition and False is my definition
        self.degree_remaining = False
        # A list of all variables in the CSP
        self.variables = variables
        # Optional initial assignments (sudoku for example) is a dictionary where the key is a variable and the value is an assigned value (domain)
        self.initial_assignments = initial_assignments
        # Non-optional initial domains is a dictionary where the key is a variable and the value is a list of values that make up its domain
        self.initial_domains = initial_domains
        # A dictionary where a variable is a key to a list of constraints on that variable
        self.constraints: Dict[Variable, List[Constraint[Variable, Domain]]] = {}
        # The list of all previous assignments used when loop_check is enabled
        self.assignments_list = []

        # Create entries for each variable in the constraints dictionary initialized to empty lists.
        for variable in self.variables:
            self.constraints[variable] = []
            if variable not in self.initial_domains:
                print("Missing variable in domain")
                sys.exit(1)

    # A function that, for each variable in the constraint, adds a reference to this constraint to the constraints dictionary
    def add_constraint(self, constraint: Constraint[Variable, Domain]) -> None:
        # For every member of this constraint
        for variable in constraint.variables:

            # Check if the variable is valid
            if variable in self.variables:

                # Add a reference to the constraint into the list of constraints for this variable in the dictionary of constraints
                self.constraints[variable].append(constraint)
            else:
                print("Constraint uses variable not within the CSP")
                sys.exit(1)

    # Checks if a variable is consistent with ALL of its constraints
    # returns True if the assignment is consistent with this variable's constraints, False if inconsistent
    def consistent(self, variable: Variable, assignment: Dict[Variable, Domain]) -> bool:
        # For every constraint in the list of constraints for this variable
        for constraint in self.constraints[variable]:

            # If the constraint isn't satisfied, return False
            if not constraint.is_satisfied(assignment):
                return False

        # Returns True when all constraints are satisfied
        return True

    # Solves this CSP by starting the recursive call
    def solve(self) -> Optional[Dict[Variable, Domain]]:

        if self.forward:
            # Do a preliminary forward for all initial assignments
            for variable in self.initial_assignments:
                self.forward_check(variable, self.initial_assignments, self.initial_domains)

        if self.ac3:
            # Do a preliminary ac3 for all initial assignments
            for variable in self.initial_assignments:
                self.ac3_check(variable, self.initial_assignments, self.initial_domains)

        print("Initial Domains: " + str(self.initial_domains))
        # Return the final assignments
        result = self.backtracking_search(self.initial_domains, self.initial_assignments)

        success = True
        # Double check that all variables' constraints are satisfied
        for variable in self.variables:
            if not self.consistent(variable, result):
                success = False

        print("Success: " + str(success))
        return result

    # A helper function to count the degree of a variable given some assignments
    # The degree is the number of constraints on REMAINING values
    def count_degree(self, assignments: Dict[Variable, Domain], variable: Variable):
        degree = 0
        # For every constraint of this variable
        for constraint in self.constraints[variable]:

            # For every neighbor in the constraint
            for neighbor in constraint.get_neighbors(variable):

                # If the neighbor is not yet assigned, add to the degree
                if self.degree_remaining:
                    if neighbor not in assignments:
                        degree += 1
                # If the neighbor is already assigned, add to the degree
                else:
                    if neighbor in assignments:
                        degree += 1
        return degree

    # Returns a list of all UNASSIGNED neighboring variables from the specified variable
    def get_unassigned_neighbors(self, assignments: Dict[Variable, Domain], variable: Variable):
        unassigned_neighbors = []
        # For every constraint in the variable's list of constraints
        for constraint in self.constraints[variable]:
            # Get a list of every neighbor for that constraint
            neighbors = constraint.get_neighbors(variable)
            # Add every neighbor to the list of neighbors if they aren't already there
            for neighbor in neighbors:
                if neighbor not in assignments and neighbor not in unassigned_neighbors:
                    unassigned_neighbors.append(neighbor)
        # Return all unassigned neighbors
        return unassigned_neighbors

    # The backtracking recursive call
    # the domains and the assignments up to this point of recursion are parameters
    def backtracking_search(self, domains: Dict[Variable, List[Domain]],
                            assignments: Dict[Variable, Domain]) -> Optional[Dict[Variable, Domain]]:
        if self.sudoku:
            print_sudoku(assignments)

        # If the assignments are all done, the base case is reached and we return the assignments
        if len(assignments) == len(self.variables):
            print("Everything is Assigned")
            return assignments

        # Chooses the next variable based on which heuristics are enabled
        cur_variable: Variable = None
        if self.min_remain:
            # For each unassigned variable
            for v in self.variables:
                if v not in assignments:
                    # If it's the first loop, assign the variable regardless or its properties
                    if cur_variable is None:
                        cur_variable = v
                    else:
                        # Choose the variable with the least remaining values
                        if len(domains[v]) < len(domains[cur_variable]):
                            cur_variable = v
                        elif self.degree:
                            # If there is a tie
                            if len(domains[v]) == len(domains[cur_variable]):
                                # As a tie breaker, use the variable with the most constraints on remaining variables
                                if self.count_degree(assignments, v) > self.count_degree(assignments, cur_variable):
                                    cur_variable = v

        else:
            # Pick the variables in order. Pretty much random
            for v in self.variables:
                if v not in assignments:
                    cur_variable = v
                    break

        # For every value in the domain of this variable
        for value in domains[cur_variable]:

            # Create a copy of the assignments so the original assignments are in tact when we backtrack
            local_assignments = assignments.copy()

            # Try adding this value to this variable into the assignments
            local_assignments[cur_variable] = value

            if self.loop_check:
                # If this assignment if not already been tried (not within the list of previous assignments)
                if local_assignments not in self.assignments_list:
                    # Add it to the list of previous assignments
                    self.assignments_list.append(local_assignments)

                else:
                    # This assignment has already been tried before, so there must be a loop
                    print("LOOPED: " + str(local_assignments))
                    sys.exit()

            # If this value is consistent with the variable's constraints
            if self.consistent(cur_variable, local_assignments):

                # Make a copy of the domains so the original domains are in tact when we backtrack
                local_domains = domains.copy()

                # Manually deepcopy the lists inside the domain dictionary because copy.deepcopy() is SUPER slow
                for key, domain_list in local_domains.items():
                    local_domains[key] = domain_list.copy()

                if self.forward:
                    # Remove the conflicting values from the domains for variables that share constraints with this one
                    self.forward_check(cur_variable, local_assignments, local_domains)

                if self.ac3:
                    # Propagate constraints and eliminate all possible conflicts that this new variable assignment causes
                    # If this new assignment causes ac3 to determine that no solution can be made from here, immediately backtrack
                    if not self.ac3_check(cur_variable, local_assignments, local_domains):
                        return None

                # Recurse with the new assignments and updated domains
                result: Optional[Dict[Variable, Domain]] = self.backtracking_search(local_domains, local_assignments)

                # If we found the result, propagate the value back to the original call
                if result is not None:
                    return result

        if self.sudoku:
            print_sudoku(assignments)

        # If no solutions can be found with the assignments given to us, let the caller know that this variable has no assignments that work
        return None

    # Function that removes the domains from all variables that would break a constraint given this new assignment
    # parameters: the newly assigned variable, its new assignment, and the domains of all variables
    # Edits the domains parameter in-place
    def forward_check(self, variable: Variable, assignments: Dict[Variable, Domain], domains: Dict[Variable, List[Domain]]):

        # For every unassigned neighbor to this variable
        for neighbor in self.get_unassigned_neighbors(assignments, variable):
            domains_to_delete: List[Domain] = []

            # Make a copy of the current assignments (assignments should be read-only)
            possible_assignments = assignments.copy()

            # For every remaining value in the domain of this neighbor
            for possible_domain in domains[neighbor]:

                # Make a hypothetical assignment using this value
                possible_assignments[neighbor] = possible_domain

                # If the addition of this assignment breaks a constraint
                if not self.consistent(neighbor, possible_assignments):

                    # Mark it for removal
                    domains_to_delete.append(possible_domain)

            # Remove all values in this neighbor's domain that are not consistent (in-place)
            for domain in domains_to_delete:
                domains[neighbor].remove(domain)

    # Propagate constraint satisfaction based on a newly assigned variable
    # Returns False if we detect a failure early
    # Edits the domain in-place
    def ac3_check(self, starting_variable: Variable, assignments: Dict[Variable, Domain], domains: Dict[Variable, List[Domain]]) -> bool:
        # Queue that contains a list of two values: [variable_to_check, against_variable]
        #                                                      -------->--------
        queue = deque()

        # Initially add arcs to the queue
        # where each neighbor of the newly changed variable is checked against the newly changed variable
        # Neighbor ----->----- starting_variable
        neighbors = self.get_unassigned_neighbors(assignments, starting_variable)
        for neighbor in neighbors:
            queue.append([neighbor, starting_variable])

        # While there are still arcs to check
        while len(queue) > 0:
            # Take an arc off the end of the queue
            arc = queue.popleft()

            # If there is an inconsistency detected and the domain for arc[0] is updated
            if self.remove_inconsistent(assignments, domains, variable_to_check=arc[0], against_variable=arc[1]):

                # If the domain is empty, we detected a failure > return False
                if len(domains[arc[0]]) == 0:
                    return False

                # Add arcs to the queue from the updated variable's neighbors to itself
                # (excluding the variable that caused this neighbor to update(arc[1]))
                # Neighbor ----->----- Updated Variable
                neighbors = self.get_unassigned_neighbors(assignments, arc[0])
                for neighbor in neighbors:
                    if neighbor != arc[1]:
                        queue.append((neighbor, starting_variable))
        # If we reach this point, that means potentially updated domains and no failure was detected
        return True

    # We are checking the arc consistency between variable_to_check ----->----- against_variable
    # A value in check_variable is consistent if there exists at least one value in against_variable that satisfies all constraints
    def remove_inconsistent(self, assignments: Dict[Variable, Domain], domains: Dict[Variable, List[Domain]],
                            variable_to_check: Variable, against_variable: Variable):
        domain_modified = False

        # For every value in the domain of variable_to_check (we could potentially remove every value in the domain)
        for value_to_check in domains[variable_to_check]:

            # Create a copy of the assignments
            local_assignments = assignments.copy()

            # Make a hypothetical assignment with the value to check
            local_assignments[variable_to_check] = value_to_check

            has_consistent = True
            # Test it against every value in the domain of against_variable
            for against_value in domains[against_variable]:

                # Make a hypothetical assignment with the value we want to test against
                local_assignments[against_variable] = against_value

                inconsistency_found = False
                # Test if variable_to_check's constraints are satisfied given these two hypothetical assignments
                # Loop through variable_to_check's constraints
                for constraint in self.constraints[variable_to_check]:

                    # If against_value shares this constraint and it's not satisfied with the against_value
                    if against_variable in constraint.get_neighbors(variable_to_check) and not constraint.is_satisfied(local_assignments):

                        # There is an inconsistency with the current constraint, so this particular assignment of
                        # against_variable is inconsistent
                        inconsistency_found = True
                        break

                # If none of the constraints were inconsistent for this value, then there exists at least one value that
                # is consistent with the original value we are checking against
                if not inconsistency_found:
                    has_consistent = True
                    break

            # If there is no value in the domain of against_variable that satisfies the constraints for the value we
            # are checking, then we can remove the value we are checking from the domain of variable_to_check
            if not has_consistent:
                domains[value_to_check].remove(value_to_check)
                domain_modified = True

        # If we made any modifications to the domain of the variable we checked, then return True
        return domain_modified
