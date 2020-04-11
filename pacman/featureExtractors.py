# featureExtractors.py
# --------------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


"Feature extractors for Pacman game states"

from game import Directions, Actions
import util
import heapq

class FeatureExtractor:
    def getFeatures(self, state, action):
        """
          Returns a dict from features to counts
          Usually, the count will just be 1.0 for
          indicator functions.
        """
        util.raiseNotDefined()

class IdentityExtractor(FeatureExtractor):
    def getFeatures(self, state, action):
        feats = util.Counter()
        feats[(state,action)] = 1.0
        return feats

class CoordinateExtractor(FeatureExtractor):
    def getFeatures(self, state, action):
        feats = util.Counter()
        feats[state] = 1.0
        feats['x=%d' % state[0]] = 1.0
        feats['y=%d' % state[0]] = 1.0
        feats['action=%s' % action] = 1.0
        return feats

def closestFood(pos, food, walls):
    """
    closestFood -- this is similar to the function that we have
    worked on in the search project; here its all in one place
    """
    fringe = [(pos[0], pos[1], 0)]
    expanded = set()
    while fringe:
        pos_x, pos_y, dist = fringe.pop(0)
        if (pos_x, pos_y) in expanded:
            continue
        expanded.add((pos_x, pos_y))
        # if we find a food at this location then exit
        if food[pos_x][pos_y]:
            return dist
        # otherwise spread out from the location to its neighbours
        nbrs = Actions.getLegalNeighbors((pos_x, pos_y), walls)
        for nbr_x, nbr_y in nbrs:
            fringe.append((nbr_x, nbr_y, dist+1))
    # no food found
    return None

class SimpleExtractor(FeatureExtractor):
    """
    Returns simple features for a basic reflex Pacman:
    - whether food will be eaten
    - how far away the next food is
    - whether a ghost collision is imminent
    - whether a ghost is one step away
    """

    def getFeatures(self, state, action):
        # extract the grid of food and wall locations and get the ghost locations
        food = state.getFood()
        walls = state.getWalls()
        ghosts = state.getGhostPositions()

        features = util.Counter()

        features["bias"] = 1.0

        # compute the location of pacman after he takes the action
        x, y = state.getPacmanPosition()
        dx, dy = Actions.directionToVector(action)
        next_x, next_y = int(x + dx), int(y + dy)

        # count the number of ghosts 1-step away
        features["#-of-ghosts-1-step-away"] = sum((next_x, next_y) in Actions.getLegalNeighbors(g, walls) for g in ghosts)

        # if there is no danger of ghosts then add the food feature
        if not features["#-of-ghosts-1-step-away"] and food[next_x][next_y]:
            features["eats-food"] = 1.0

        dist = closestFood((next_x, next_y), food, walls)
        if dist is not None:
            # make the distance a number less than one otherwise the update
            # will diverge wildly
            features["closest-food"] = float(dist) / (walls.width * walls.height)
        features.divideAll(10.0)
        return features

class NewExtractor(FeatureExtractor):
    """
    Design you own feature extractor here. You may define other helper functions you find necessary.
    """

    def nearestEdibleScaredGhost(self, pacmanPos, state, walls):
        ghostPositions = state.getGhostPositions()
        ghostStates = state.getGhostStates()

        initialEvaluation = self.closestGhostEval(pacmanPos, ghostPositions, 0)

        # Format of tuple: (f(n), g(n), position)
        fringe = [(initialEvaluation, 0, pacmanPos)]
        expanded = set()
        while fringe:
            f, g, currentPos = heapq.heappop(fringe)

            if currentPos in expanded:
                # Do not need to expand the node again if it has been expanded
                continue

            expanded.add(currentPos)

            for ghostPos in ghostPositions:
                if currentPos[0] == int(ghostPos[0]) and currentPos[1] == int(ghostPos[1]):
                    for ghost in ghostStates:
                        if ghostPos == ghost.getPosition() and ghost.scaredTimer > g:
                            return (g, ghost)

            nbrs = Actions.getLegalNeighbors(currentPos, walls)
            for nbr_x, nbr_y in nbrs:
                newPos = (nbr_x, nbr_y)
                if newPos not in expanded:
                    # If the node has not been expanded before, we will add it into the
                    # fringe. Need not worry about repeated nodes since the PQ will give the
                    # smallest value of f(n) of the repeated nodes priority.
                    new_g = g + 1
                    new_f = self.closestGhostEval(newPos, ghostPositions, new_g)
                    heapq.heappush(fringe, (new_f, new_g, newPos))

        return (None, None)

    def nearestPosition(self, start, targets, walls):
        fringe = [(start[0], start[1], 0)]
        expanded = set()
        while fringe:
            pos_x, pos_y, dist = fringe.pop(0)
            if (pos_x, pos_y) in expanded:
                continue
            expanded.add((pos_x, pos_y))
            # if we find a target at this location then exit
            if (pos_x, pos_y) in targets:
                return dist
            # otherwise spread out from the location to its neighbours
            nbrs = Actions.getLegalNeighbors((pos_x, pos_y), walls)
            for nbr_x, nbr_y in nbrs:
                fringe.append((nbr_x, nbr_y, dist+1))
        # no target found
        return None
    
    def closestGhostMD(self, pacmanPos, safeGhostPositions):
        distances = []
        for safeGhostPos in safeGhostPositions:
            manhattanDist = util.manhattanDistance(pacmanPos, safeGhostPos)
            distances.append(manhattanDist)
        return min(distances)

    def closestGhostEval(self, pacmanPos, safeGhostPositions, currentCost):
        return self.closestGhostMD(pacmanPos, safeGhostPositions) + currentCost

    def generateNeighbours(self, pos, walls, steps):
        fringe = [(pos, 0)]
        expanded = set()

        while fringe:
            pos, dist = fringe.pop()
            if pos in expanded:
                continue
            expanded.add(pos)



    def numOfGhostInTwoUnits(self, pacmanPos, dangerousGhostPositions, walls):
        fringe = [(pacmanPos, 0)]
        ghostPossibleNextPos = []
        for ghostPos in dangerousGhostPositions:
            ghostPossibleNextPos += Actions.getLegalNeighbors(ghostPos, walls)

        expanded = set()
        count = 0

        while fringe:
            pos, dist = fringe.pop(0)
            if pos in expanded:
                continue
            expanded.add(pos)
            # if we find a food at this location then exit
            if pos in ghostPossibleNextPos:
                count += 1
            # otherwise spread out from the location to its neighbours
            if dist < 2:
                nbrs = Actions.getLegalNeighbors(pos, walls)
                for new_pos in nbrs:
                    fringe.append((new_pos, dist + 1))
        # no food found
        return count

    def analyseSafePaths(self, pacmanPos, dangerousGhostPositions, walls):
        numOfPacman = 1
        numOfSafeRoutes = 0
        distOfSafeRoutes = 0
        fringe = []
        for ghost in dangerousGhostPositions:
            fringe.append((ghost, 0, 'ghost'))
        fringe.append((pacmanPos, 0, 'pacman'))

        expanded = set()
        ghostExpanded = set()

        while numOfPacman > 0:
            pos, dist, identity = fringe.pop(0)
            if identity is 'pacman':
                numOfPacman -= 1
                if pos in expanded:
                    continue

                expanded.add(pos)
                pacmanNeighbors = Actions.getLegalNeighbors(pos, walls)
                clearSurroundings = 0
                for neighbour in pacmanNeighbors:
                    if neighbour not in ghostExpanded:
                        clearSurroundings += 1
                        fringe.append((neighbour, dist + 1, 'pacman'))
                        numOfPacman += 1
                if clearSurroundings > 2:
                    numOfSafeRoutes += 1
                    distOfSafeRoutes += dist
                # 2 safe routes per dangerous ghost, can terminate
                if numOfSafeRoutes > 2 * len(dangerousGhostPositions):
                    return (numOfSafeRoutes, distOfSafeRoutes)
            else:
                if pos in ghostExpanded:
                    continue
                ghostExpanded.add(pos)
                ghostNeighbors = Actions.getLegalNeighbors(pos, walls)
                for neighbor in ghostNeighbors:
                    fringe.append((neighbor, dist + 1, 'ghost'))

        return (numOfSafeRoutes, distOfSafeRoutes)

    def getFeatures(self, state, action):
        "*** YOUR CODE HERE ***"
        # extract the grid of food and wall locations and get the ghost locations
        food = state.getFood()
        walls = state.getWalls()
        ghostStates = state.getGhostStates()
        capsules = state.getCapsules()
        capsuleList = list(capsules)
        dangerousGhostPositions = list((g.getPosition() for g in ghostStates if g.scaredTimer <= 1))
        safeGhostPositions = list((g.getPosition() for g in ghostStates if g.scaredTimer > 0))

        features = util.Counter()

        features["bias"] = 1.0

        # compute the location of pacman after he takes the action
        x, y = state.getPacmanPosition()
        dx, dy = Actions.directionToVector(action)
        next_x, next_y = int(x + dx), int(y + dy)
        next_pos = (next_x, next_y)

        
        # check if next_pos has dangerous ghost
        if next_pos in dangerousGhostPositions:
            features["ghosts-in-next-pos"] = 1.0

        # count the number of ghosts 1-step away that dangerous
        features["#-of-ghosts-1-step-away"] = sum( next_pos in Actions.getLegalNeighbors(g.getPosition(), walls) for g in ghostStates if g.scaredTimer <= 1)

        dist = closestFood(next_pos, food, walls)
        if dist is not None:
            features["closest-food"] = float(dist) / (walls.width * walls.height)
        
        if not features["#-of-ghosts-1-step-away"]:
            # if there is no danger of ghosts then add the food feature
            if food[next_x][next_y]:
                features["eats-food"] = 1.0
            
            nearestScaredGhostDist, nearestScaredGhost = self.nearestEdibleScaredGhost(next_pos, state, walls)
            if nearestScaredGhostDist is not None:
                features["closest-scared-ghost"] = 1.0 - float(nearestScaredGhostDist) / (walls.width * walls.height)
            
            # if there is no danger of ghosts then add the food feature
            if next_pos in safeGhostPositions:
                distFromRespawn = nearestScaredGhost.start.getPosition()
                features["eats-ghost"] = 1.0
            
            nearestCapsuleDist = self.nearestPosition(next_pos, capsuleList, walls)
            if nearestCapsuleDist is not None:
                features["closest-capsule"] = 1.0 - float(nearestCapsuleDist) / (walls.width * walls.height)
            
            if next_pos in capsuleList:
                features["eats-capsule"] = len(dangerousGhostPositions)
        '''
        numSafeRoutes, sumOfSafeRoutesDist = self.analyseSafePaths(next_pos, dangerousGhostPositions, walls)
        if numSafeRoutes == 0:
            features["dist-safe-paths"] = 1.0
        else:
            features["dist-safe-paths"] = float(sumOfSafeRoutesDist) / (numSafeRoutes * walls.width * walls.height)
        '''
        features.divideAll(10.0)
        return features
