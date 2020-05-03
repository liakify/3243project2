import sys
import copy
import time

# Running script: given code can be run with the command:
# python file.py, ./path/to/init_state.txt ./output/output.txt

start_time = time.time()
nodes_explored = 0

class Sudoku(object):
    FAILURE = -1
    def __init__(self, puzzle, domain_values=None):
        # you may add more attributes if you need
        self.puzzle = puzzle # self.puzzle is a list of lists
        self.ans = puzzle # self.ans is a list of lists
        self.domain_values = domain_values if domain_values != None else []
        if domain_values == None:
            for i in range(9):
                self.domain_values.append([])
                for j in range(9):
                    if puzzle[i][j] == 0:
                        self.domain_values[i].append(range(1, 10))
                    else:
                        self.domain_values[i].append([puzzle[i][j]])

    def get_unassigned(self):
        return [(i,j) for i in range(9) for j in range(9) if self.puzzle[i][j] == 0]

    def solve(self, flag=True):
        if flag:
            initial_inf_time = time.time()
            inf = self.inference(None)
           
            print("Time taken for pre-processing: " + str(time.time()-initial_inf_time))

            if inf != self.FAILURE:
                new_sudoku = Sudoku(inf[0], domain_values=inf[1])
                result = new_sudoku.solve(flag=False)
                         
                if result != self.FAILURE:
                    return result
        global nodes_explored
        nodes_explored += 1
        unassigned = self.get_unassigned()
        if len(unassigned) == 0:
            return self.ans
        var = self.select_unassigned_variable(unassigned)
        var_row, var_col = var
        ordered_domain_vals = self.get_and_order_domain_vals(var)
        for val in ordered_domain_vals:
            self.ans = copy.deepcopy(self.puzzle)
            #if self.assignment_is_consistent(var, val):
                
            self.ans[var_row][var_col] = val
            self.domain_values[var_row][var_col] = [val]
            inf = self.inference(var)
            if inf != self.FAILURE:
                new_sudoku = Sudoku(inf[0], domain_values=inf[1])
                result = new_sudoku.solve(False)

                if result != self.FAILURE:
                    return result
            
            # If we reach here we need to undo the assignment
            self.ans[var_row][var_col] = 0
            self.domain_values[var_row][var_col] = ordered_domain_vals

        # self.ans is a list of lists
        return self.FAILURE

    # We would not need to perform this if AC-3 is used at every step during inference and as preprocessing
    def assignment_is_consistent(self, var, value):
        # Need to perform 3 * 8 = 24 checks (within row, col and 3x3 square)
        row, col = var
        square_top_left_row = (row // 3) * 3
        square_top_left_col = (col // 3) * 3
        # Row check
        for i in range(9):
            if i == col:
                continue
            dom_values = self.domain_values[row][i]
            # print(dom_values)
            if len(dom_values) == 1 and dom_values[0] == value:
                return False

        # Col check
        for i in range(9):
            if i == row:
                continue
            dom_values = self.domain_values[i][col]
            if len(dom_values) == 1 and dom_values[0] == value:
                return False

        # 3x3 square check
        for i in range(square_top_left_row, square_top_left_row + 3):
            for j in range(square_top_left_col, square_top_left_col + 3):
                if (i, j) == (row, col):
                    continue
                dom_values = self.domain_values[i][j]
                if len(dom_values) == 1 and dom_values[0] == value:
                    return False
        return True
    
    def inference(self, cell):
        # Do inference here such as AC-3
        # Will need to make a deep copy of the domain values while doing inference
        # so that we do not lose the information of the domain values of the
        # other nodes. if we discover a variable for which we have an empty
        # domain, we return FAILURE. Otherwise we can either return the original
        # domains or the reduced domains
        
        domain_vals = copy.deepcopy(self.domain_values) 
        
        if cell == None:
            queue = self.get_arcs()
        else:
            row, col = cell
            queue = set()
      
            for x in self.get_neighbours(row, col, True):
                queue.add((x, cell))
        
        while len(queue) != 0:
            (Xi, Xj) = queue.pop()
            row_i, col_i = Xi

            if (self.revise(domain_vals, Xi, Xj)):
                if (len(domain_vals[row_i][col_i]) == 0):
                    return self.FAILURE
                
                for Xk in self.get_neighbours(row_i, col_i, False):
                    if Xk != Xj:                    
                        queue.add((Xk, Xi))
        
        return (self.ans, domain_vals)
    
    # Get all the arcs in the CSP used when AC-3 done at pre-processing
    def get_arcs(self):
        arcs = set()

        for row in range(9):
            for col in range(9):
                 for (x, y) in self.get_neighbours(row, col, False):
                      arcs.add(((row, col), (x, y)))
    
        return arcs    

    # Get all neighbours of a particular cell in the CSP
    def get_neighbours(self, row, col, signal):
        square_top_row = (row // 3) * 3
        square_left_most_col = (col // 3) * 3
        result = []        

        # Get neighbours in the same row
        for i in range(9):
            if i != col and (not signal or (signal and self.ans[row][i] == 0)):
                 result.append((row, i))

        # Get neighbours in the same col
        for j in range(9):
            if j != row and (not signal or (signal and self.ans[j][col] == 0)):
                result.append((j, col))

        # Get neighbours in the same 3x3 grid
        for i in range(square_top_row, square_top_row + 3):
            for j in range(square_left_most_col, square_left_most_col + 3):
                if (row, col) != (i, j) and (not signal or (signal and self.ans[i][j] == 0)):
                    result.append((i, j))
        
        return result
 
    # Revise function
    def revise(self, domain_vals, Xi, Xj):
        row, col = Xi
        revised = False

        for x in domain_vals[row][col]:
            if not self.found_valid_value(domain_vals, x, Xj):
                 domain_vals[row][col].remove(x)
                 revised = True
        
        return revised

    # Find a valid value in Xj if x was assigned to Xi
    def found_valid_value(self, domain_vals, x, Xj):
        row, col = Xj

        for j in domain_vals[row][col]:
            if j != x:
                return True
        
        return False

    # We can choose a heuristic here for selecting an unassigned variable
    def select_unassigned_variable(self, unassigned):
        # For now just choose first variable
        return unassigned[0]

    def get_and_order_domain_vals(self, var):
        domain_values = self.domain_values[var[0]][var[1]]
        # We can add more stuff here for ordering the values
        return domain_values # Currently no ordering

    # you may add more classes/functions if you think is useful
    # However, ensure all the classes/functions are in this file ONLY
    # Note that our evaluation scripts only call the solve method.
    # Any other methods that you write should be used within the solve() method.

if __name__ == "__main__":
    # STRICTLY do NOT modify the code in the main function here
    if len(sys.argv) != 3:
        print ("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise ValueError("Wrong number of arguments!")

    try:
        f = open(sys.argv[1], 'r')
    except IOError:
        print ("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise IOError("Input file not found!")

    puzzle = [[0 for i in range(9)] for j in range(9)]
    lines = f.readlines()

    i, j = 0, 0
    for line in lines:
        for number in line:
            if '0' <= number <= '9':
                puzzle[i][j] = int(number)
                j += 1
                if j == 9:
                    i += 1
                    j = 0

    sudoku = Sudoku(puzzle)
    ans = sudoku.solve()
    
    print("Total time taken: " + str(time.time() - start_time))
    print("Number of nodes explored: " + str(nodes_explored))

    #print(ans)
    with open(sys.argv[2], 'a') as f:
         for i in range(9):
             for j in range(9):
                 f.write(str(ans[i][j]) + " ")
             f.write("\n")
