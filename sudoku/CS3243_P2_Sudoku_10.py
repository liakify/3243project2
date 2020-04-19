import sys
import copy
import time

# Running script: given code can be run with the command:
# python file.py, ./path/to/init_state.txt ./output/output.txt

# initial_inf = 0

class Sudoku(object):
    FAILURE = -1
    def __init__(self, puzzle):
        # you may add more attributes if you need
        self.puzzle = puzzle # self.puzzle is a list of lists
        self.ans = copy.deepcopy(puzzle) # self.ans is a list of lists
        self.domains = {}
        self.empty = []
        self.filled_at_start = []
        self.nodes_explored = 0
        for i in range(9):
            for j in range(9):
                current_val = self.ans[i][j]
                if current_val == 0:
                    self.domains[(i,j)] = range(1, 10)
                    self.empty.append((i,j))
                else:
                    self.domains[(i,j)] = [current_val]
                    self.filled_at_start.append((i,j))
    def solve(self, isInitial=True):
        if isInitial:
            intial_inf_time = time.time()
            self.initial_inf()
            print("Time taken for pre-processing: "+ str(time.time() - intial_inf_time))
        self.nodes_explored += 1
        if len(self.empty) == 0:
            return self.ans
        empty_tile = self.select_most_constrained_variable()
        for i in self.domains[empty_tile]:
            self.ans[empty_tile[0]][empty_tile[1]] = i
            old_domain_vals = self.domains[empty_tile]
            self.domains[empty_tile] = [i]
            inferred = self.inf(empty_tile)
            if (inferred[1] != self.FAILURE):
                if self.solve(isInitial=False):
                    return self.ans
            self.restore_domain_vals(inferred[0])
            self.ans[empty_tile[0]][empty_tile[1]] = 0
            self.domains[empty_tile] = old_domain_vals
        self.empty.append(empty_tile)
        return False
        # TODO: Write your code here

    def restore_domain_vals(self, removed_domain_values):
        for (tile, domain_val) in removed_domain_values:
            self.domains[tile].append(domain_val)

    def eliminate_used_number(self, filled_tile):
        row, col = filled_tile
        value = self.ans[row][col]
        square_top_left_row = (row // 3) * 3
        square_top_left_col = (col // 3) * 3
        for i in range(9):
            current = (row, i)
            current_domains = self.domains[current]
            if current != filled_tile and len(current_domains) != 1 and value in current_domains:
                current_domains.remove(value)
                if len(current_domains) == 1:
                    self.ans[current[0]][current[1]] = current_domains[0]
                    self.filled_at_start.append(current)
        for i in range(9):
            current = (i, col)
            current_domains = self.domains[current]
            if current != filled_tile and len(current_domains) != 1 and value in current_domains:
                current_domains.remove(value)
                if len(current_domains) == 1:
                    self.ans[current[0]][current[1]] = current_domains[0]
                    self.filled_at_start.append(current)
        for i in range(square_top_left_row, square_top_left_row + 3):
            for j in range(square_top_left_col, square_top_left_col + 3):
                current = (i, j)
                current_domains = self.domains[current]
                if current != filled_tile and len(current_domains) != 1 and value in current_domains:
                    current_domains.remove(value)
                    if len(current_domains) == 1:
                        self.ans[current[0]][current[1]] = current_domains[0]
                        self.filled_at_start.append(current)
                        
    def initial_inf(self):
        for filled_tile in self.filled_at_start:
            self.eliminate_used_number(filled_tile)
    
    def inf(self, tile):
        self.filled_at_start = [tile]
        removed_domains = []
        for filled_tile in self.filled_at_start:
            row, col = filled_tile
            value = self.domains[filled_tile][0]
            square_top_left_row = (row // 3) * 3
            square_top_left_col = (col // 3) * 3
            for i in range(9):
                current = (row, i)
                current_domains = self.domains[current]
                if current != filled_tile and value in current_domains:
                    current_domains.remove(value)
                    removed_domains.append((current, value))
                    if len(current_domains) == 1:
                        self.filled_at_start.append(current)
                    elif len(current_domains) == 0:
                        return removed_domains, self.FAILURE
            for i in range(9):
                current = (i, col)
                current_domains = self.domains[current]
                if current != filled_tile and value in current_domains:
                    current_domains.remove(value)
                    removed_domains.append((current, value))
                    if len(current_domains) == 1:
                        self.filled_at_start.append(current)
                    elif len(current_domains) == 0:
                        return removed_domains, self.FAILURE
            for i in range(square_top_left_row, square_top_left_row + 3):
                for j in range(square_top_left_col, square_top_left_col + 3):
                    current = (i, j)
                    current_domains = self.domains[current]
                    if current != filled_tile and value in current_domains:
                        current_domains.remove(value)
                        removed_domains.append((current, value))
                        if len(current_domains) == 1:
                            self.filled_at_start.append(current)
                        elif len(current_domains) == 0:
                            return removed_domains, self.FAILURE
        return removed_domains, None
    def assignment_is_consistent(self, var, value):
        # Need to perform 3 * 8 = 24 checks (within row, col and 3x3 square)
        row, col = var
        square_top_left_row = (row // 3) * 3
        square_top_left_col = (col // 3) * 3
        # Row check
        for i in range(9):
            if i != col and self.ans[row][i] == value:
                return False

        # Col check
        for i in range(9):
            if i != row and self.ans[i][col] == value:
                return False

        # 3x3 square check
        for i in range(square_top_left_row, square_top_left_row + 3):
            for j in range(square_top_left_col, square_top_left_col + 3):
                if (i, j) != var and self.ans[i][j] == value:
                    return False
        return True

    def select_most_constrained_variable(self):
        var_index = -1
        # most_constrained_dom_size = 10 # just an arbitary number larger than the possible domain size. This means that it will eventually be updated
        # for i in range(len(self.empty)):
        #     empty_tile = self.empty[i]
        #     new_dom_size = len(self.domains[empty_tile]) 
        #     if new_dom_size < most_constrained_dom_size:
        #         var_index = i
        #         most_constrained_dom_size = new_dom_size
        return self.empty.pop(var_index)
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
    start_time = time.time()

    sudoku = Sudoku(puzzle)
    ans = sudoku.solve()
    
    print("Total time taken: " + str(time.time() - start_time))
    print("Nodes explored: "+ str(sudoku.nodes_explored))

    # print(ans)
    with open(sys.argv[2], 'a') as f:
         for i in range(9):
             for j in range(9):
                 f.write(str(ans[i][j]) + " ")
             f.write("\n")
