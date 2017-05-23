from util import *
import sharedMemory as sm

class Objective:
    pass


class ObjectiveExplore(Objective):
    def __init__(self, agent_index, posA, posB, moves=None):
        self.agent_index = agent_index;
        if (moves == None):
            self.moves = calc_path(posA, posB);
        else:
            self.moves = moves;
        self.goal = posB;
        self.index = 0;
        self.type = "explore";

    def next_move(self):
        # global sm.shared
        my_pos = sm.shared.agents[self.agent_index];
        if (my_pos == self.moves[self.index - 1]):
            self.index -= 1;

        pos = self.moves[self.index];
        move = (pos[0] - my_pos[0], pos[1] - my_pos[1]);
        if sm.shared.free_at(pos) and valid_move(move):  # if next move is free and valid
            self.index += 1;
            return move;
        else:  # if not free/valid. calc new path
            self.moves, dist = calc_path(my_pos, self.goal);
            if (len(self.moves) == 0):
                return None;  # no path exists

            self.index = 0;
            return self.next_move();

    def complete(self):
        # global sm.shared;

        if (self.index >= len(self.moves)):
            return True;

        return sm.shared.feature_at(self.moves[-1], "explored");


class ObjectiveMove(Objective):
    def __init__(self, agent_index, posA, posB, moves=None):
        self.agent_index = agent_index;
        if (moves == None):
            self.moves = calc_path(posA, posB);
        else:
            self.moves = moves;
        self.goal = self.moves[-1];
        self.index = 0;
        self.type = "move";

    def next_move(self):
        # global sm.shared
        if (self.index >= len(self.moves)):
            return None;
        my_pos = sm.shared.agents[self.agent_index];
        if (my_pos == self.moves[self.index - 1]):
            self.index -= 1;
        pos = self.moves[self.index];
        move = (pos[0] - my_pos[0], pos[1] - my_pos[1]);
        if sm.shared.free_at(pos) and valid_move(move):  # if next move is free and valid
            self.index += 1;
            return move;
        else:  # if not free/valid. calc new path
            self.moves, dist = calc_path(my_pos, self.goal);
            if (len(self.moves) == 0):
                return None;  # no path exists

            self.index = 0;
            return self.next_move();

    def complete(self):
        return (self.index >= len(self.moves));


class ObjectiveButton(Objective):
    def __init__(self, agent_index, posA, posB, button, moves=None):
        self.agent_index = agent_index;
        if (moves == None):
            self.moves = calc_path(posA, posB);
        else:
            self.moves = moves;
        self.goal = self.moves[-1];
        self.index = 0;
        self.button = button;
        self.type = "button";

    def next_move(self):
        my_pos = sm.shared.agents[self.agent_index];
        if (self.index > 0):
            if (my_pos != self.moves[self.index - 1]):
                self.index -= 1;

        if (my_pos == self.goal):
            return (0, 0);

        pos = self.moves[self.index];
        move = (pos[0] - my_pos[0], pos[1] - my_pos[1]);
        if sm.shared.free_at(pos) and valid_move(move):  # if next move is free and valid
            self.index += 1;
            print(self.moves);
            return move;
        else:  # if not free/valid. calc new path
            self.moves, dist = calc_path(my_pos, self.goal);
            if (len(self.moves) == 0):
                return None;  # no path exists

            self.index = 0;
            return self.next_move();

    def complete(self):
        # global sm.shared;
        return False

        # if (not self.button in sm.shared.buttons):
        #     return True;
        # zone = sm.shared.fence_zone(self.button);
        # if (zone == None):
        #     return True;
        #
        # check if any agents in zone, ignore self
        # for pos in sm.shared.agents:
        #     if sm.shared.agents[self.agent_index] == pos:
        #         continue;
        #     if (point_in_zone(pos, zone)):
        #         return False;
        #
        # return True;
