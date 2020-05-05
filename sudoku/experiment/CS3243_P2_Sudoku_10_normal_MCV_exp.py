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
        self.empty_tiles = []
        self.filled_tiles = []
        
        # for experiment
        self.nodes_explored = 0
        self.preprocessing_time = 0
        self.time_taken = 0
        
        for i in range(9):
            for j in range(9):
                current_val = self.ans[i][j]
                if current_val == 0:
                    self.domains[(i,j)] = range(1, 10)
                    self.empty_tiles.append((i,j))
                else:
                    self.domains[(i,j)] = [current_val]
                    self.filled_tiles.append((i,j))
    
    def solve(self, isInitial=True, emptyIndex=0):
        start_time = time.time()
        if isInitial:
            # Pre processing using initial_inf
            initial_inf_time = time.time()
            self.initial_inf()
            self.preprocessing_time = time.time() - initial_inf_time
        
        self.nodes_explored += 1
        if len(self.empty_tiles) <= emptyIndex:
            self.time_taken = time.time() - start_time
            return self.ans
        self.reposition_most_constrained_variable(emptyIndex)
        chosen_tile = self.empty_tiles[emptyIndex]
        for i in self.domains[chosen_tile]:
            # save reference to old domain_vals for chosen tile
            old_domain_vals = self.domains[chosen_tile]
            self.domains[chosen_tile] = [i]
            self.ans[chosen_tile[0]][chosen_tile[1]] = i
            
            removed_domain_values, inference_status = self.inf(chosen_tile)
            if (inference_status != self.FAILURE):
                if self.solve(isInitial=False, emptyIndex=emptyIndex + 1):
                    self.time_taken = time.time() - start_time
                    return self.ans
            # If we reach here means we have reached an error and we must backtrack
            self.restore_domain_vals(removed_domain_values)
            self.ans[chosen_tile[0]][chosen_tile[1]] = 0
            self.domains[chosen_tile] = old_domain_vals
        return False

    def restore_domain_vals(self, removed_domain_values):
        # For when we reach an error state, we need to restore all the removed domain values
        for (tile, domain_val) in removed_domain_values:
            self.domains[tile].append(domain_val)
                        
    def initial_reduce_domain(self, tile, filled_tile, value):
        current_domains = self.domains[tile]
        # in the preprocessing inference step we dont need to check if a tile reaches an inconsistent state
        # (i,e having a tile of domain length 1 reducing to domain length 0). This is because as long as the
        # initial puzzle is guaranteed to be solvable, we will not change the puzzle into an inconsistent state
        # during pre-processing as we are only making inferences and not any guesses, which is only done later.
        # This is just an optimization
        if tile != filled_tile and len(current_domains) != 1 and value in current_domains:
            current_domains.remove(value)
            # If the domain of a tile is reduced to only one possible value, assign that value to the tile
            if len(current_domains) == 1:
                # We can safely assign  the single value in the domain as the answer for the same reason as above
                self.ans[tile[0]][tile[1]] = current_domains[0]
                self.filled_tiles.append(tile)

    def initial_inf(self):
        # The intuition here is that we only need to check arc consistency for any neighbours to filled tiles
        # and only once for each filled tile. As we infer new filled tiles (i.e. tiles that have their domains
        # reduced to one during the preprocessing domain reduction step), we only need to check the arc consistency
        # with the neighbours of the newly filled_tiles. This is essentially a version of AC-3 optimized for sudoku
        # as we are not performing redundant checks. Even though we append to filled tiles in the initial_reduce_domain
        # fn, it is guaranteed to terminate as a tile can only change from unfilled to filled state and not vice versa
        # in preprocessing
        for filled_tile in self.filled_tiles:
            row, col = filled_tile
            value = self.ans[row][col]
            square_top_left_row = (row // 3) * 3
            square_top_left_col = (col // 3) * 3
            
            # Reduce the domains of tiles in the same row as the filled tile
            for i in range(9):
                current = (row, i)
                self.initial_reduce_domain(current, filled_tile, value)
                
            # Reduce the domains of tiles in the same col as the filled tile
            for i in range(9):
                current = (i, col)
                self.initial_reduce_domain(current, filled_tile, value)
            
            # Reduce the domains of tiles in the same square as the filled tile
            for i in range(square_top_left_row, square_top_left_row + 3):
                for j in range(square_top_left_col, square_top_left_col + 3):
                    current = (i, j)
                    self.initial_reduce_domain(current, filled_tile, value)
    
    def inf(self, tile):
        # Intution is very similar to initial_inf. Similar to AC-3, we only need to initially infer
        # using the newly guessed tile at this step of backtracking. Subsequently we check using tiles
        # that had their domains reduced to 1 in the reduce_domain step. Unlike the preprocessing step
        # there is a possibility of reducing a domain to zero here. If that happens, we throw a failure.
        # One additional thing we need to do is store a list of all the removed domains and the tile
        # coordinate as well in the removed_domains list so we can restore the removed domains if we 
        # ever reach an error state here on in one of the descendant states.
        self.filled_tiles = [tile]
        removed_domains = []
        for filled_tile in self.filled_tiles:
            row, col = filled_tile
            value = self.domains[filled_tile][0]
            square_top_left_row = (row // 3) * 3
            square_top_left_col = (col // 3) * 3
            
            # Reduce the domains of tiles in the same row as tile just filled
            for i in range(9):
                current = (row, i)
                result = self.reduce_domain(current, filled_tile, value, removed_domains)
                if len(self.domains[current]) == 0:
                    return removed_domains, self.FAILURE

            # Reduce the domains of tiles in the same col as tile just filled
            for i in range(9):
                current = (i, col)
                result = self.reduce_domain(current, filled_tile, value, removed_domains)
                if len(self.domains[current]) == 0:
                    return removed_domains, self.FAILURE
            
            # Reduce the domains of tiles in the same wquare as tile just filled
            for i in range(square_top_left_row, square_top_left_row + 3):
                for j in range(square_top_left_col, square_top_left_col + 3):
                    current = (i, j)
                    result = self.reduce_domain(current, filled_tile, value, removed_domains)
                    if len(self.domains[current]) == 0:
                        return removed_domains, self.FAILURE
        
        return removed_domains, None
    
    def reduce_domain(self, tile, filled_tile, value, removed_domains):
        current_domains = self.domains[tile]
        if tile != filled_tile and value in current_domains:
            current_domains.remove(value)
            removed_domains.append((tile, value))
            # If domain of tile is reduced to only one value, we will need to infer using this tile as well
            # so we add it to the list of filled tiles so we can check it in the infer function
            if len(current_domains) == 1:
                self.filled_tiles.append(tile)

    # Select the most constrained variable and positions it at emptyIndex
    def reposition_most_constrained_variable(self, emptyIndex):
        var_index = emptyIndex
        most_constrained_dom_size = 10
        for i in range(var_index, len(self.empty_tiles)):
            new_dom_size = len(self.domains[self.empty_tiles[i]]) 
            if new_dom_size < most_constrained_dom_size:
                var_index = i
                most_constrained_dom_size = new_dom_size
        # Do in place swap with chosen tile coords and that of emptyIndex
        temp = self.empty_tiles[var_index]
        self.empty_tiles[var_index] = self.empty_tiles[emptyIndex]
        self.empty_tiles[emptyIndex] = temp

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

    # print(ans)
    with open(sys.argv[2], 'a') as f:
         for i in range(9):
             for j in range(9):
                 f.write(str(ans[i][j]) + " ")
             f.write("\n")