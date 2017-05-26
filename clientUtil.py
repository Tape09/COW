from util import  *
from cowAgents import make_decision
from cowAgents import before_each_round

import socket
import select
from lxml import etree
import time
import sys;
import  sharedMemory as sm



def create_action_message(type, id):
    root = etree.Element("message", type="action")
    action = etree.Element("action", type=type, id=id)
    root.append(action);
    prefix = '<?xml version="1.0" encoding="UTF-8"?>'
    str = etree.tostring(root).decode("UTF-8");
    str = prefix + str;
    str = str.encode("UTF-8")
    str = str + b'\0'
    return str;


def create_auth_message(user, pw):
    root = etree.Element("message", type="auth-request")
    auth = etree.Element("authentication", password=pw, username=user)
    root.append(auth);
    prefix = '<?xml version="1.0" encoding="UTF-8"?>'
    str = etree.tostring(root).decode("UTF-8");
    str = prefix + str;
    str = str.encode("UTF-8")
    str = str + b'\0'
    return str;


def handle_raw_message(data, agent_index):
    root = etree.fromstring(data);

    response = None;
    # determine message type
    if (root.attrib["type"] == "request-action"):
        id = handle_ra(root, agent_index);
        print("HANDLING REQUEST", id);
        move = make_decision(agent_index);
        string_move = sm.shared.move_to_string[move];
        response = create_action_message(string_move, id);
    # print(data);
    # print(response)
    # print();
    elif (root.attrib["type"] == "sim-start"):
        handle_simstart(root);
    elif (root.attrib["type"] == "auth-response"):
        print("Authenticated!")
    elif (root.attrib["type"] == "sim-end"):
        handle_simend(root);
        response = "end";
    else:
        # nothing?
        print(data)
        print("ERROR: bad message")

    return response;


def handle_simend(root):
    # global sm.shared;
    sim = root.getchildren()[0];
    sm.shared.final_score = float(sim.attrib["averageScore"]);
    sm.shared.final_result = sim.attrib["result"];


def handle_simstart(root):
    # global sm.shared;
    sim = root.getchildren()[0];
    width = int(sim.attrib["gsizex"]);
    height = int(sim.attrib["gsizey"]);
    x0 = int(sim.attrib["corralx0"]);
    x1 = int(sim.attrib["corralx1"]);
    y0 = int(sim.attrib["corraly0"]);
    y1 = int(sim.attrib["corraly1"]);

    sm.shared = sm.SharedMemory(width, height, 20);
    sm.shared.set_my_corral(x0, x1, y0, y1);
    print("SIMULATION STARTED")
    print(sm.shared)


def handle_ra(root, agent_index):  # HANDLE DISTANCE TO CORRAL CALCULATIONS HERE?
    # global sm.shared;
    perception = root.getchildren()[0];
    x_agent = int(perception.attrib["posx"]);
    y_agent = int(perception.attrib["posy"]);

    id = perception.attrib["id"];

    sm.shared.agents[agent_index] = (x_agent, y_agent);
    sm.shared.cows_in_corral = int(perception.attrib["cowsInCorral"]);
    cells = perception.getchildren();

    for c in cells:  # NEED TO CONSIDER IMERFECT VISION !!!
        features = [0] * len(sm.shared.types);
        features[0] = 1;  # mark as explored
        features[10] = -1;  # mark as unreachable

        x = int(c.attrib["x"]) + x_agent;
        y = int(c.attrib["y"]) + y_agent;
        stuff = c.getchildren();
        for s in stuff:
            stype = s.tag;
            if (stype == "fence"):
                if (s.attrib["open"] == "true"):
                    features[sm.shared.types["open_fence"]] = 1;
                else:
                    features[sm.shared.types["closed_fence"]] = 1;
            elif (stype == "agent"):
                if (s.attrib["type"] == "ally"):
                    features[sm.shared.types["my_agent"]] = 1;
                else:
                    features[sm.shared.types["enemy_agent"]] = 1;
            elif (stype == "obstacle"):
                features[sm.shared.types["tree"]] = 1;
            elif (stype == "cow"):
                cow_id = int(s.attrib["ID"]) + 1;
                if (cow_id in sm.shared.cows):
                    sm.shared.modmap(sm.shared.cows[cow_id], "cow", 0);
                sm.shared.cows[cow_id] = (x, y);
                features[sm.shared.types["cow"]] = cow_id;
            elif (stype == "corral"):
                if (s.attrib["type"] == "ally"):
                    features[sm.shared.types["my_corral"]] = 1;
                    features[sm.shared.types["corral_dist"]] = 0;
                else:
                    features[sm.shared.types["enemy_corral"]] = 1;
            elif (stype == "switch"):
                features[sm.shared.types["button"]] = 1;
                fence = [];
                found_fence = False;
                # find fence
                # up
                fx, fy = x, y - 1;
                if (sm.shared.feature_at((fx, fy), "open_fence") or sm.shared.feature_at((fx, fy), "closed_fence")):
                    while (sm.shared.feature_at((fx, fy), "open_fence") or sm.shared.feature_at((fx, fy), "closed_fence")):
                        fence.append((fx, fy));
                        fy -= 1;
                        found_fence = True;

                fx, fy = x, y + 1;
                if (not found_fence):
                    if (sm.shared.feature_at((fx, fy), "open_fence") or sm.shared.feature_at((fx, fy), "closed_fence")):
                        while (
                            sm.shared.feature_at((fx, fy), "open_fence") or sm.shared.feature_at((fx, fy), "closed_fence")):
                            fence.append((fx, fy));
                            fy += 1;
                            found_fence = True;

                fx, fy = x - 1, y;
                if (not found_fence):
                    if (sm.shared.feature_at((fx, fy), "open_fence") or sm.shared.feature_at((fx, fy), "closed_fence")):
                        while (
                            sm.shared.feature_at((fx, fy), "open_fence") or sm.shared.feature_at((fx, fy), "closed_fence")):
                            fence.append((fx, fy));
                            fx -= 1;
                            found_fence = True;

                fx, fy = x + 1, y;
                if (not found_fence):
                    if (sm.shared.feature_at((fx, fy), "open_fence") or sm.shared.feature_at((fx, fy), "closed_fence")):
                        while (
                            sm.shared.feature_at((fx, fy), "open_fence") or sm.shared.feature_at((fx, fy), "closed_fence")):
                            fence.append((fx, fy));
                            fx += 1;
                            found_fence = True;

                if (found_fence):
                    sm.shared.buttons[(x, y)] = fence;

        sm.shared.setmap(x, y, features);

    if not id in sm.shared.request_ids:  # only once per round               
        sm.shared.iteration += 1;        
        sm.shared.request_ids.add(id);
    return id;

def main():
    n_agents = 20;
    if (len(sys.argv) < 3):
        print("USAGE: cowAgents_old.py user_prefix password")
        sys.exit()

    password = sys.argv[2];
    user_prefix = sys.argv[1];

    sockets = [];
    usernames = [];
    for i in range(n_agents):
        usernames.append(user_prefix + str(i + 1));
        sockets.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM));
        # sockets[-1].setblocking(0);
        sockets[-1].connect(("localhost", 12300));
        sockets[-1].send(create_auth_message(usernames[-1], password));
        print("Connecting ", usernames[-1])

    counter = dict();
    while True:
        readable, writable, exceptional = select.select(sockets, sockets, []);
        time.sleep(0.01);
        for s in readable:
            data = s.recv(2 ** 15);
            if (data):
                # print(data);
                agent_index = sockets.index(s);
                print("RECEIVED MESSAGE FOR AGENT", agent_index);
                # response = handle_raw_message(data, agent_index);
                ###
                time.sleep(0.005);
                root = etree.fromstring(data);
                # response = None;
                # determine message type
                if (root.attrib["type"] == "request-action"):
                    id = handle_ra(root, agent_index);
                    print("HANDLING REQUEST", id);
                    
                    if(id in counter):
                        counter[id] += 1;
                    else:
                        counter[id] = 1;
                        
                    if(counter[id] == 20):
                        before_each_round(); 
                        for i in range(20):
                            move = make_decision(i);
                            string_move = sm.shared.move_to_string[move];
                            response = create_action_message(string_move, id);
                            sockets[i].send(response);
                            # print(response)
                            print("RESPONSE SENT")
                # print(data);
                # print(response)
                # print();
                elif (root.attrib["type"] == "sim-start"):
                    handle_simstart(root);
                elif (root.attrib["type"] == "auth-response"):
                    print("Authenticated!")
                elif (root.attrib["type"] == "sim-end"):
                    handle_simend(root);
                    response = "end";
                else:
                    # nothing?
                    print(data)
                    print("ERROR: bad message")
                ###
                

if __name__ == '__main__':
    main()
