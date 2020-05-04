import sys
import copy
import time

# Running script: given code can be run with the command:
# python file.py, ./path/to/init_state.txt ./output/output.txt

class Sudoku(object):
    FAILURE = -1
    def __init__(self, puzzle):
        # you may add more attributes if you need
        self.puzzle = puzzle # self.puzzle is a list of lists
        self.ans = copy.deepcopy(puzzle) # self.ans is a list of lists
        self.domains = {}
        self.empty = []

        # for experiment
        self.nodes_explored = 0
        self.preprocessing_time = 0
        self.time_taken = 0

        for i in range(9):
            for j in range(9):
                current_val = self.ans[i][j]
                if current_val == 0:
                    self.domains[(i,j)] = range(1, 10)
                    self.empty.append((i,j))
                else:
                    self.domains[(i,j)] = [current_val]
                    
    def solve(self, isInitial=True, emptyIndex=0):
        if isInitial:
            initial_inf_time = time.time()
            self.initial_inf()
            self.preprocessing_time = time.time() - initial_inf_time
           
        self.nodes_explored += 1
        start_time = time.time()
        if len(self.empty) <= emptyIndex:
            self.time_taken = time.time() - start_time
            return self.ans
        empty_tile = self.empty[emptyIndex]
        for i in self.domains[empty_tile]:
            # if self.assignment_is_consistent(empty_tile, i):
            self.ans[empty_tile[0]][empty_tile[1]] = i
            old_domain_vals = self.domains[empty_tile]
            self.domains[empty_tile] = [i]
            inferred = self.inf(empty_tile)
            if (inferred[1] != self.FAILURE):
                if self.solve(isInitial=False, emptyIndex=emptyIndex + 1):
                    self.time_taken = time.time() - start_time
                    return self.ans
            self.restore_domain_vals(inferred[0])
            self.ans[empty_tile[0]][empty_tile[1]] = 0
            self.domains[empty_tile] = old_domain_vals
        return False

    def restore_domain_vals(self, removed_domain_values):
        for (tile, domain_val) in removed_domain_values:
            self.domains[tile].append(domain_val)

    def find_empty(self):
        for i in range(9):
            for j in range(9):
                if self.ans[i][j] == 0:
                    return (i, j)
        return None
    
    def get_all_neighbour_arcs_from(self, arc_set, var):
        row, col = var
        square_top_left_row = (row // 3) * 3
        square_top_left_col = (col // 3) * 3
        for i in range(9):
            if col != i:
                arc_set.add((row, col, row, i))
        for i in range(9):
            if row != i:
                arc_set.add((row, col, i, col))
        for i in range(square_top_left_row, square_top_left_row + 3):
            for j in range(square_top_left_col, square_top_left_col + 3):
                if (i, j) != (row, col):
                    arc_set.add((row, col, i, j))      

    def get_all_neighbour_arcs_to(self, arc_set, var, excluded):
        row, col = var
        square_top_left_row = (row // 3) * 3
        square_top_left_col = (col // 3) * 3
        for i in range(9):
            if col != i and excluded != (row, i):
                arc_set.add((row, i, row, col))
        for i in range(9):
            if row != i and excluded != (i, col):
                arc_set.add((i, col, row, col))
        for i in range(square_top_left_row, square_top_left_row + 3):
            for j in range(square_top_left_col, square_top_left_col + 3):
                if (i, j) != (row, col) and excluded != (i, j):
                    arc_set.add((i, j, row, col))

    def inf(self, var):
        queue = set()
        self.get_all_neighbour_arcs_to(queue, var, None)
        removed_domains = []
        while len(queue) != 0:
            a,b,c,d = queue.pop()
            start = (a,b)
            end = (c,d)
            if (self.revise(start, end, removed_domain_values=removed_domains)):
                if (len(self.domains[start])) == 0:
                    return removed_domains, self.FAILURE
                self.get_all_neighbour_arcs_to(queue, start, end)
        return removed_domains, None


    def initial_inf(self):
        queue = set()
        for empty_tile in self.empty:
            self.get_all_neighbour_arcs_from(queue, empty_tile)
        # print(queue)
        while len(queue) != 0:
            a,b,c,d = queue.pop()
            start = (a,b)
            end = (c,d)
            if self.revise(start, end):
                if len(self.domains[start]) == 0:
                    return self.FAILURE # won't be reached since all puzzles guaranteed to be well formed and to have at least one solution
                self.get_all_neighbour_arcs_to(queue, start, end)

    def revise(self, start, end, removed_domain_values=None):
        start_domain = self.domains[start]
        end_domain = self.domains[end]
        if len(end_domain) > 1:
            return False
        only_val_in_end = end_domain[0]
        for i in range(len(start_domain)):
            if start_domain[i] == only_val_in_end:
                popped = start_domain.pop(i)
                if removed_domain_values != None:
                    removed_domain_values.append((start, popped))
                return True

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

    def get_statistics(self):
        return {'nodes': self.nodes_explored, 'time taken': self.time_taken, 'pre-process': self.preprocessing_time}
    
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

    print(ans)
    with open(sys.argv[2], 'a') as f:
         for i in range(9):
             for j in range(9):
                 f.write(str(ans[i][j]) + " ")
             f.write("\n")
