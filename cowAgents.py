import sharedMemory as sm
from util import  *
from objectives import *
import random


sm.shared = None;


def make_decision(agent_index):
    # global sm.shared;

    x, y = sm.shared.agents[agent_index];
    moves = sm.shared.valid_moves(agent_index);

    # has_objective = (sm.shared.objectives[agent_index] != None) and (not sm.shared.objectives[agent_index].complete());

    if (sm.shared.objectives[agent_index] != None):
        if (sm.shared.objectives[agent_index].type == "button"):
            print(sm.shared.objectives[agent_index].complete());

    # iterate over buttons
    for button in sm.shared.buttons:
        zone = sm.shared.fence_zone(button);
        skip = False;
        if (zone == None):
            continue;
        if (len(sm.shared.buttons[button]) == 0):
            continue;
        if (not sm.shared.feature_at(sm.shared.buttons[button][0], "closed_fence")):
            continue;

        for objective in sm.shared.objectives:
            if objective == None:
                continue;
            if objective.type == "button":
                if objective.button == button:
                    skip = True;
                    break;

        if (skip):
            continue;

        # if close to a closed fence
        if (point_in_zone((x, y), zone)):
            # check if other agents in zone
            push_button = False;
            for i, apos in enumerate(sm.shared.agents):
                if (i == agent_index):
                    continue;
                if (point_in_zone(apos, zone)):
                    push_button = True;
                    break;

            if (push_button):
                # select nearest agent to corresponding button
                path, dist = sm.shared.find_nearest(button, "my_agent", limit=50);
                if (len(path) == 0):
                    continue;
                agent_pos = path[-1];
                path = path[:-1];
                path.reverse();

                if (len(path) == 0):
                    continue;

                end_point = path[-1];
                if (not (end_point[0] == button[0] or end_point[1] == button[1])):
                    new_ends = [(end_point[0] + 1, end_point[1]), (end_point[0] - 1, end_point[1]),
                                (end_point[0], end_point[1] + 1), (end_point[0], end_point[1] - 1)];
                    good_end = False;
                    for new_end in new_ends:
                        if (sm.shared.feature_at(new_end, "closed_fence") or sm.shared.feature_at(new_end, "open_fence")):
                            continue;
                        if (new_end[0] == button[0] or new_end[1] == button[1]):
                            good_end = True;
                            path.append(new_end);
                    if (not good_end):
                        continue;
                agent_idx = sm.shared.get_agent_idx(agent_pos);
                if (agent_idx == None):
                    continue;
                # set selected agents objective to "button"
                sm.shared.objectives[agent_idx] = ObjectiveButton(agent_idx, agent_pos, path[-1], button, moves=path);

                for i, pos in enumerate(sm.shared.agents):  # check if another agent is already going for this btton
                    if (i == agent_index):
                        continue;
                    if (sm.shared.objectives[i] != None):
                        if (sm.shared.objectives[i].type == "button"):
                            if (sm.shared.objectives[i].button == button):
                                sm.shared.objectives[i] == None;

    has_objective = (sm.shared.objectives[agent_index] != None) and (not sm.shared.objectives[agent_index].complete());

    # try explore
    if (not has_objective):
        nearest_unexplored_path, dist = sm.shared.find_nearest((x, y), "explored", True, 50);
        if (len(nearest_unexplored_path) > 0):
            sm.shared.objectives[agent_index] = ObjectiveExplore(agent_index, (x, y), nearest_unexplored_path[-1],
                                                              moves=nearest_unexplored_path);
            has_objective = True;

    # can add other objectives here


    if (sm.shared.objectives[agent_index] != None):
        if (sm.shared.objectives[agent_index].type == "button"):
            print(agent_index, (x, y), sm.shared.objectives[agent_index].index, sm.shared.objectives[agent_index].moves)

    if (not has_objective):  # failed to explore
        my_move = random.choice(moves);
    else:  # has objective
        my_move = sm.shared.objectives[agent_index].next_move();

    # if(sm.shared.objectives[agent_index] != None):
    # if(sm.shared.objectives[agent_index].type == "button"):
    # print(my_move)

    # something went wrong (path blocked or something) and objective became impossible
    if (my_move == None):
        my_move = random.choice(moves);
        sm.shared.objectives[agent_index] = None;  # should be something smarter

    # my_move = random.choice(moves);
    # if(my_move == (0,0)):
    # if(sm.shared.objectives[agent_index] != None):
    # if(sm.shared.objectives[agent_index].type == "button"):
    # print((x,y),sm.shared.objectives[agent_index].index,sm.shared.objectives[agent_index].moves )


    return my_move;



