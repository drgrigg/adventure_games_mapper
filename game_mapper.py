#!/usr/bin/env python3

import os
import sys
import math
from typing import List, Tuple
from random import randint
from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import scrolledtext
import heapq
import numpy as np


import regex
import sqlite3

CANVAS_WIDTH = 1490
CANVAS_HEIGHT = 950

class Direction():
    id = 0
    name = ""
    x = 0.0
    y = 0.0
    z = 0.0
    invert_id = 0
    colour = '#000000'
    def __init__(self, id: int, name: str, x: float, y: float, z: float, invert: int, colour: str = "#000000"):
        self.id = id
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.invert_id = invert
        self.colour = colour


class Room():
    id = 0
    name = ""
    description = ""
    xpos = 0.0
    ypos = 0.0
    zpos = 0.0
    visited = False  # temporary flag
    deadend = False  # temporary flag
    bubble_bounds = (0,0,0,0)
    def __init__(self, id: int, name: str, desc: str = ""):
        self.id = id
        self.name = name
    def __lt__(self, other) -> bool:
        if self.name == other.name:
            if self.id < other.id:
                return True
        else:
            if self.name < other.name:
                return True
        return False     
    def set_position(self, x, y, z):
        self.xpos = x
        self.ypos = y
        self.zpos = z
    def connection_points(self) -> list:
        # midpoints and corners of bounds, plus a set of alternates
        x1, y1, x2, y2 = self.bubble_bounds
        width = x2 - x1
        height = y2 - y1

        nw = (x1 + width/8, y1 + height/8)
        n = (x1 + width/2, y1)
        ne = (x1 + width - (width/8), y1 + height/8)
        w = (x1, y1 + height/2)
        e = (x1 + width, y1 + height/2)
        sw = (x1 + width/8, y1 + height - (height/8))
        s = (x1 + width/2, y1 + height)
        se = (x1 + width - (width/8), y1 + height - (height/8))

        alt_nw = (x1 + width/4, y1)
        alt_n = (x1 + (5*width/8), y1)
        alt_ne = (x1 + (3*width/4), y1)
        alt_w = (x1, y1 + (3*height/8))
        alt_e = (x1 + width, y1 + (3*height/8))
        alt_sw = (x1, y1 + (3*height/4))
        alt_s = (x1 + (5*width/8), y1 + height)
        alt_se = (x1 + width, y1 + (3*height/4))
        return [nw, n, ne, w, e, sw, s, se, alt_nw, alt_n, alt_ne, alt_w, alt_e, alt_sw, alt_s, alt_se]


class Path():
    direction: Direction = None
    to_room: Room = None
    from_room: Room = None

    drawn = False  # flag to say whether we've already drawn this path on map

    def __init__(self, direction: Direction, to_room: Room, from_room: Room) -> None:
        self.direction = direction
        self.to_room = to_room
        self.from_room = from_room


class Object():
    object_id = 0
    name = ""
    found_id = 0
    current_id = 0
    aliases = ""

    def __init__(self, name: str, found_id: int, current_id: int):
        self.object_id = 0
        self.name = name
        self.found_id = found_id
        self.current_id = current_id
    def __lt__(self, other) -> bool:
        if self.name == other.name:
            if self.id < other.id:
                return True
        else:
            if self.name < other.name:
                return True
        return False     

def dijkstra(graph, start, end):
    """
    Find the shortest path between start and end nodes in a graph using Dijkstra's algorithm.
    
    Args:
    - graph: a dictionary representing the graph, where the keys are the nodes and the values
      are lists of tuples representing the edges and their weights, e.g. {'A': [('B', 1), ('C', 4)], ...}
    - start: the starting node
    - end: the ending node
    
    Returns:
    - A list of nodes representing the shortest path between start and end nodes
    """
    predecessors = {node: None for node in graph}
    visited = set()
    pq = [(0, start)] # priority queue of (distance, node)
    while pq:
        (dist, curr_node) = heapq.heappop(pq)
        if curr_node == end:
            # Found the shortest path!
            path = []
            while curr_node != start:
                path.append(curr_node)
                curr_node = predecessors[curr_node]
            path.append(start)
            return path[::-1]
        if curr_node in visited:
            continue
        visited.add(curr_node)
        for (next_node, weight) in graph[curr_node]:
            if next_node not in visited:
                predecessors[next_node] = curr_node
                heapq.heappush(pq, (dist + weight, next_node))
    # No path found
    return []

def generate_graph():
    """
    Generate a graph dictionary suitable for the Dijkstra function.

    Args:
    - obj_list: a list of objects, each with properties `id` and `connections` representing the ID
      of the object and a list of the IDs of objects to which it is connected.

    Returns:
    - A dictionary representing the graph, where the keys are the IDs of the objects and the values
      are lists of tuples representing the edges and their weights.
    """
    graph = {}
    for room in rooms:
        connections = get_outward_rooms(room.id)
        edges = [(conn_id, 1) for conn_id in connections] # Assuming all edges have weight 1
        graph[room.id] = edges
    return graph


folder = os.path.normpath(sys.argv[0])
folder_bits = os.path.split(folder)
my_folder = folder_bits[0]
sql_statements = []

with open(os.path.join(my_folder, "create_new.sql"), "r") as sfile:
    sql_statements = sfile.readlines()
    sfile.close()

db_folder = my_folder
db_path = ""
if len(sys.argv) > 1:
    db_path = sys.argv[1]

rooms: List[Room] = []
directions: List[Direction] = []
paths: List[Path] = []
objs: List[Object] = []
# combos: List[ttk.Combobox] = []

def room_names() -> list:
    ret_list = ["NEW ROOM : 0"]
    for room in sorted(rooms):
        ret_list.append(f"{room.name} : {room.id}")
    return ret_list


def room_names_no_new() -> list:
    ret_list = ["Nowhere : 0"]
    for room in sorted(rooms):
        ret_list.append(f"{room.name} : {room.id}")
    return ret_list


def obj_names() -> list:
    ret_list = []
    obj: Object = None
    for obj in sorted(objs):
        ret_list.append(f"{obj.name} : {obj.object_id}")
    return ret_list


def direction_names() -> list:
    ret_list = ["None"]
    for direction in directions:
        ret_list.append(f"{direction.name} : {direction.id}")
    return ret_list


LIGHT_GRAY = "#BBBBBB"
DARK_GRAY = "#808080"
BLACK = "#000000"
CREAM = "#F8EECB"


def centre_window(win: Tk, width: int, height: int):
    win.title("Add Outline to PDF file")
    win.configure(bg=LIGHT_GRAY)
    win.resizable(False, False)

    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    xpos = int((screen_width/2) - (width/2))
    ypos = int((screen_height/2) - (height/2))
    geom_str = f"{width}x{height}+{xpos}+{ypos}"
    win.geometry(geom_str)


window = Tk()
centre_window(window, 960, 650)
window.title("Adventure Game Mapper")

current_room: Room = None
db_lab: Label = None
name_lab: Label = None
room_name_entry: Entry = None
obj_name_entry: Entry = None
obj_alias_entry: Entry = None
desc_text: Text = None
current_text: Text = None
button_pane: Frame = None
new_path_pane: Frame = None
search_pane : Frame = None
data_pane: Frame = None
direction_var = StringVar()
room_var = StringVar()
room_var_2 = StringVar()
wanted_obj: Object = None
search_combo: ttk.Combobox = None
object_combo: ttk.Combobox = None
found_combo: ttk.Combobox = None
current_combo: ttk.Combobox = None

def logging(string: str):
    pass  # turned off logging
    # with open(os.path.join(db_folder, "log.txt"), "a") as f:
    #     f.write(string + "\n")

def delete_log():
    if os.path.exists(os.path.join(db_folder, "log.txt")):
        os.remove(os.path.join(db_folder, "log.txt"))

def create_new_db(path_to_db: str):
    conn = sqlite3.connect(path_to_db)
    cursor = conn.cursor()
    if sql_statements:
        for statement in sql_statements:
            statement.replace('\\n','')
            cursor.execute(statement)
        conn.commit()
    else:
        print("unable to create new database")
        exit(-1)
    return conn

def get_existing_file(init_folder:str) -> str:
    ftypes = (
    ('Database files', '*.db'),
    ('All files', '*.*')
	)

    gamefile = fd.askopenfilename(
    title="Open existing game database",
    initialdir=init_folder,
    initialfile="game.db",
    filetypes=ftypes)
    return gamefile

def make_new_file(init_folder:str) -> str:
    ftypes = (
    ('Database files', '*.db'),
    ('All files', '*.*')
	)

    gamefile = fd.asksaveasfilename(
    title="Create new game database",
    initialdir=init_folder,
    initialfile="game.db",
    filetypes=ftypes)
    return gamefile

def load_data(path_to_db: str):
    global rooms, directions, paths, objs
    conn = sqlite3.connect(path_to_db)
    cursor = conn.cursor()
    rooms = []
    paths = []
    objs = []
    directions = []
    sql = "SELECT * FROM ROOMS"
    cursor.execute(sql)
    rows = cursor.fetchall()
    for row in rows:
        id = row[0]
        name = row[1]
        aroom = Room(id, name)
        aroom.description = row[2]
        rooms.append(aroom)
    sql = "SELECT * FROM DIRECTIONS "
    cursor.execute(sql)
    rows = cursor.fetchall()
    for row in rows:
        id = row[0]
        name = row[1]
        x = row[2]
        y = row[3]
        z = row[4]
        invert = row[5]
        colour = row[6]
        direction = Direction(id, name, x, y, z, invert, colour)
        directions.append(direction)
    sql = "SELECT * FROM PATHS "
    cursor.execute(sql)
    rows = cursor.fetchall()
    for row in rows:
        direction_id = row[0]
        from_id = row[1]
        to_id = row[2]
        direction = get_direction_from_id(direction_id)
        from_room = get_room_from_id(from_id)
        to_room = get_room_from_id(to_id)
        path = Path(direction, to_room, from_room)
        paths.append(path)
    sql = "SELECT * FROM OBJECTS "
    cursor.execute(sql)
    rows = cursor.fetchall()
    for row in rows:
        obj_name = row[1]
        found_id = row[2]
        current_id = row[3]
        obj = Object(obj_name, found_id, current_id)
        obj.object_id = row[0]
        obj.aliases = row[4]
        objs.append(obj)
    

def clear_combo(combo: ttk.Combobox):
    combo.delete(0,END)
    combo.config(values=["None"])
    combo.current(0)


def do_nothing():
    pass


def open_existing(from_args: bool = False):
    global db_path
    if not from_args:
        db_path = get_existing_file(my_folder)
    if db_path:
        if db_lab:
            db_lab.config(text=f"Game file: {db_path}")
        load_data(db_path)
        go_to_room(1)
        # display_map(10.0)  


def create_new():
    global db_path
    db_path = make_new_file(my_folder)
    if db_path:
        create_new_db(db_path)
        if db_lab:
            db_lab.config(text=f"Game file: {db_path}")
        load_data(db_path)
        go_to_room(1)


def draw_menu(window: Tk):
    menubar = Menu(window)
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="New Game Database", command=create_new)
    filemenu.add_command(label="Open Existing Database", command=open_existing)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=window.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    toolmenu = Menu(menubar, tearoff=0)
    toolmenu.add_command(label="Show Map", command=show_map_window)
    toolmenu.add_command(label="Find Path to Room", command=show_navigation_window)
    toolmenu.add_command(label="Find Path to Object", command=show_find_object_window)
    toolmenu.add_command(label="Search Rooms", command=show_search_window)
    toolmenu.add_command(label="Manage Objects", command=show_manage_objs)

    menubar.add_cascade(label="Tools", menu=toolmenu)

    helpmenu = Menu(menubar, tearoff=0)
    helpmenu.add_command(label="Help Index", command=do_nothing)
    helpmenu.add_command(label="About...", command=do_nothing)
    menubar.add_cascade(label="Help", menu=helpmenu)

    window.config(menu=menubar)


def get_objs_by_name(name: str) -> list:
    # this is tricky because we really need aliases, eg "Coins" for "Bag of Coins"
    # but what do we do when we have "Nasty Knife", "Rusty Knife" etc??
    obj_list = []
    obj: Object = None
    for obj in objs:
        if name.upper() == obj.name.upper():  # try for exact match first
            obj_list.append(obj)
        elif name.upper() in obj.name.upper(): # try for partial match, eg 'Knife' in 'Rusty Knife'
            obj_list.append(obj)
        elif obj.aliases and name.upper() in obj.aliases.upper():
            obj_list.append(obj)
    return obj_list


def remove_current_objs_from_room(room_id: int):
    for obj in objs:
        if obj.current_id == room_id:
            obj.current_id = 0
    sql = f'UPDATE OBJECTS SET CurrentRoom=0 WHERE CurrentRoom={room_id}'
    db_execute(sql)


def place_found_objects(found_str: str, room_id: int):
    global objs
    found_str = found_str.strip()
    test_list = get_found_objs_names(room_id=room_id)
    test_str = ",".join(test_list)
    if test_str == found_str:
        return  #nothing to do
    names = found_str.split(sep=",")
    for name in names:
        name = name.strip()
        name = name.title()
        if not name:
            return
        obj_list = get_objs_by_name(name)
        obj: Object = None
        if len(obj_list) > 1:
            show_obj_select(obj_list)
            obj = wanted_obj
        if obj:
            obj.found_id = room_id
            obj.current_id = room_id
            sql = f'UPDATE OBJECTS SET FoundRoom = {room_id}, CurrentRoom = {room_id} WHERE ID={obj.object_id}'
            db_execute(sql)
        else:
            obj = Object(name, found_id=room_id, current_id=room_id)
            sql = f'INSERT INTO OBJECTS(Name,FoundRoom,CurrentRoom) VALUES("{name}",{room_id},{room_id})'
            obj.object_id = db_execute_get_id(sql)
            objs.append(obj)


def update_object_location(obj: Object, name: str, room_id: int):
        # we may pass None as object to this function
        if obj:
            obj.current_id = room_id
            sql = f'UPDATE OBJECTS SET CurrentRoom = {room_id} WHERE ID={obj.object_id}'
            db_execute(sql)
        else:
            obj = Object(name, found_id=room_id, current_id=room_id)
            sql = f'INSERT INTO OBJECTS(Name,FoundRoom,CurrentRoom) VALUES("{name.title()}",{room_id},{room_id})'
            obj.object_id = db_execute_get_id(sql)
            objs.append(obj)


def place_current_objects(current_str: str, room_id: int):
    global objs
    current_str = current_str.strip()
    test_list = get_current_objs_names(room_id=room_id)
    test_str = ",".join(test_list)
    if test_str == current_str:
        return  #nothing to do
    # tricky thing here is deleting objects REMOVED from the list. So remove them ALL from the room, then add them back.
    remove_current_objs_from_room(room_id)

    names = current_str.split(sep=",")
    for name in names:
        name = name.strip()
        if not name:
            return
        name = name.title()

        obj_list = get_objs_by_name(name) # returns a list of close matches
        if len(obj_list) == 1:  # object found, only one (which is what we want)
            update_object_location(obj_list[0], name, room_id)
        elif len(obj_list) == 0:
            update_object_location(None, name, room_id)
        else:  # have to choose beween possible matches
            show_obj_select(obj_list, name, room_id)


def update_room_details():
    if current_room:
        temp_name = room_name_entry.get()
        temp_desc = desc_text.get('1.0', END)
        # only rewrite if changed.
        if (not current_room.name == temp_name) or (not current_room.description == temp_desc):
            current_room.name = temp_name
            current_room.description = temp_desc
            sql = f'UPDATE ROOMS SET Name = "{temp_name}", Description = "{temp_desc}" WHERE Id = {current_room.id}'
            db_execute(sql)
        current_str = current_text.get('1.0', END)
        place_current_objects(current_str, current_room.id)


def draw_controls(window: Tk):
    global db_lab, name_lab, room_name_entry, desc_text, button_pane, new_path_pane, data_pane, search_pane, current_text

    db_lab = Label(window, text="Game file: none selected", bg=LIGHT_GRAY)
    db_lab.pack(side=TOP, pady=5, fill=X)

    data_pane = Frame(window, bg=LIGHT_GRAY, height=700)
    
    room_pane = Frame(data_pane, bg=LIGHT_GRAY, height=600)
    entry_pane = Frame(room_pane, bg=LIGHT_GRAY)
    name_lab = Label(entry_pane, text="Room:", bg=LIGHT_GRAY)
    name_lab.pack(side=LEFT, padx=5)
    room_name_entry = Entry(entry_pane, width=25)
    room_name_entry.pack(side=LEFT, pady=5)
    entry_pane.pack(side=TOP, pady=15)

    desc_text = Text(room_pane, width=60, height=8)
    desc_text.pack(side=TOP, pady=5)

    objs_pane = Frame(room_pane, bg=LIGHT_GRAY, height=100)
    current_pane = Frame(objs_pane, bg=LIGHT_GRAY, height=50)
    current_label = Label(current_pane, text="Objects here:", bg=LIGHT_GRAY)
    current_label.pack(side=LEFT, padx=5)
    current_text = Text(current_pane, width=50, height=2)
    current_text.pack(side=LEFT, padx=5)
    current_pane.pack(side=TOP, pady=5)
    # found_pane = Frame(objs_pane, bg=LIGHT_GRAY, height=50)
    # objs_label = Label(found_pane, text="Objects found here first:", bg=LIGHT_GRAY)
    # objs_label.pack(side=LEFT, padx=5)
    # found_text = Text(found_pane, width=35, height=1)
    # found_text.pack(side=LEFT, padx=5)
    # found_pane.pack(side=TOP, pady=5)
    objs_pane.pack(side=TOP, pady=5)

    update_but = Button(room_pane, text="Update", width=20, command=update_room_details)
    update_but.pack(side=TOP, pady=15)

    room_pane.pack(side=LEFT, padx=5, fill=Y)

    # we'll fill this with buttons representing the directions we can go
    button_pane = Frame(data_pane, bg=LIGHT_GRAY, height=500)
    button_pane.pack(side=LEFT, padx=5)
    data_pane.pack(side=TOP, padx=5, fill=BOTH)

    new_path_pane = Frame(window, bg=LIGHT_GRAY, height=200, highlightbackground=DARK_GRAY, highlightthickness=1)
    new_path_pane.pack(side=TOP, fill=X, pady=5)
    draw_new_path_controls(1)


def get_room_from_id(id: int) -> Room:
    for room in rooms:
        if room.id == id:
            return room
    return None

def get_direction_from_id(id: int) -> Direction:
    for direction in directions:
        if direction.id == id:
            return direction
    return None

def get_path_from_id(id: int) -> Direction:
    for path in paths:
        if path.id == id:
            return path
    return None

def get_path_from_ends(from_id: int, to_id: int) -> Path:
    for path in paths:
        if path.from_room.id == from_id and path.to_room.id == to_id:
            return path
    return None

def get_outward_paths(room_id: int) -> list:
    path_list = []
    for path in paths:
        if path.from_room:
            if path.from_room.id == room_id:
                path_list.append(path)
    return path_list

def get_outward_rooms(room_id: int) -> list:
    outrooms = []
    for path in paths:
        if path.from_room:
            if path.from_room.id == room_id:
                outrooms.append(path.to_room.id)
    return outrooms

def get_unvisited_paths(room_id: int) -> list:
    path_list = []
    for path in paths:
        if path.from_room.id == room_id and not path.to_room.visited and not path.to_room.deadend:
            path_list.append(path)
    return path_list


def get_inward_paths(room_id: int) -> list:
    path_list = []
    for path in paths:
        if path.to_room:
            if path.to_room.id == room_id:
                path_list.append(path)
    return path_list


def get_found_objs_names(room_id: int) -> list:
    obj_list = []
    for obj in objs:
        if obj.found_id == room_id:
            obj_list.append(obj.name)
    return obj_list


def get_current_objs_names(room_id: int) -> list:
    obj_list = []
    for obj in objs:
        if obj.current_id == room_id:
            obj_list.append(obj.name)
    return obj_list


def distance_between(room1: Room, room2: Room) -> float:
    return math.sqrt((room2.xpos - room1.xpos) ** 2 + (room2.ypos - room1.ypos) ** 2)


def get_max_room_distance() -> float:
    max_distance = 0.0
    for room in rooms:
        distance = math.sqrt(room.xpos ** 2 + room.ypos ** 2)
        if distance > max_distance:
            max_distance = distance
    return max_distance


def add_unconnected_room():
    # it's a new room, create an empty one first
    sql = f'INSERT INTO ROOMS (Name, Description) VALUES ("New Room", "Description")'
    current_id = db_execute_get_id(sql)
    new_room = Room(current_id, "New Room", "Description")
    rooms.append(new_room)
    update_room_details()  #updates current room
    go_to_room(current_id)


def add_path_to_room(from_id: int, direct_str: str, room_str: str, mutual: bool = False):
    direct_id = 0
    to_id = 0

    direct_id = get_id_from_string(direct_str)
    if direct_id < 0:
        return

    to_id = get_id_from_string(room_str)
    if to_id < 0:
        return

    if to_id == 0: # it's a new room, create an empty one first
        sql = f'INSERT INTO ROOMS (Name, Description) VALUES ("New Room", "Description")'
        to_id = db_execute_get_id(sql)
        new_room = Room(to_id, "New Room", "Description")
        rooms.append(new_room)

    direction = get_direction_from_id(direct_id)
    to_room = get_room_from_id(to_id)
    from_room = get_room_from_id(from_id)
    
    # need to test for duplicates
    check_paths = [p for p in paths if (p.direction == direction) and (p.from_room == from_room) and (p.to_room == to_room)]
    if check_paths:  # then we already have an identical path, so get out of the routine
        return

    sql = f'INSERT INTO PATHS (DirectionID, FromID, ToID) VALUES({direct_id}, {from_id}, {to_id});'
    db_execute(sql)

    path = Path(direction=direction, to_room=to_room, from_room=from_room)
    paths.append(path)
    set_room_coordinates(path)
    if mutual:
        reverse_direction = get_direction_from_id(direction.invert_id)
        # need to test for duplicates
        check_paths = [p for p in paths if (p.direction == reverse_direction) and (p.from_room == to_room) and (p.to_room == from_room)]
        if not check_paths:  # OK, no duplicate         
            sql = f'INSERT INTO PATHS (DirectionID, FromID, ToID) VALUES({direction.invert_id}, {to_id}, {from_id});'
            db_execute(sql)
            path = Path(direction=reverse_direction, to_room=from_room, from_room=to_room)
            paths.append(path)
    update_room_details()
    go_to_room(to_id)

def db_execute(sql):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()

def db_execute_get_id(sql) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    return cursor.lastrowid


recurse_depth = 0

def adjust_positions(positions, min_distance, max_distance, max_iterations=1000, distance_tolerance=1e-6):
    """
    Adjusts the positions of objects such that each object is at least
    `min_distance` away from the nearest object, but no more than
    `max_distance` away from the nearest object.

    Args:
        positions (ndarray): A 2D array of shape (N, 2) containing the
            initial positions of the objects.
        min_distance (float): The minimum distance that each object should be
            from its nearest neighbor.
        max_distance (float): The maximum distance that each object should be
            from its nearest neighbor.
        max_iterations (int): The maximum number of iterations to perform.
        distance_tolerance (float): The tolerance level for the distances.

    Returns:
        ndarray: A 2D array of shape (N, 2) containing the adjusted positions
        of the objects.
    """

    num_objects = positions.shape[0]
    new_positions = positions.copy()

    for iteration in range(max_iterations):
        # Compute the distances between the current object and all other objects
        distances = np.linalg.norm(new_positions[:, np.newaxis] - new_positions, axis=2)

        # Set the distance to itself to infinity so it is not selected as the minimum
        np.fill_diagonal(distances, np.inf)

        # Find the nearest object
        nearest = np.argmin(distances, axis=1)

        # Compute the distance to the nearest object
        dist = distances[np.arange(num_objects), nearest]

        # If the distance is less than `min_distance`, move the object away from the
        # nearest object by `min_distance - dist`. If the distance is greater than
        # `max_distance`, move the object towards the nearest object by `dist - max_distance`.
        mask = (dist < min_distance - distance_tolerance) | (dist > max_distance + distance_tolerance)
        if not mask.any():
            break
        for i in np.where(mask)[0]:
            if dist[i] == 0:
                continue
            if dist[i] < min_distance - distance_tolerance:
                direction = (new_positions[i] - new_positions[nearest[i]]) / dist[i]
                new_positions[i] += direction * (min_distance - dist[i])
            elif dist[i] > max_distance + distance_tolerance:
                direction = (new_positions[nearest[i]] - new_positions[i]) / dist[i]
                new_positions[i] += direction * (dist[i] - max_distance)

    return new_positions


def set_room_coordinates(path: Path, outward: bool = True):
    # set room coordinates based on path direction
    direction = path.direction
    to_room = path.to_room
    from_room = path.from_room
    if outward:
        if to_room.visited:
            return
        to_room.xpos = from_room.xpos + direction.x * 10
        to_room.ypos = from_room.ypos + direction.y * 10
        to_room.zpos = from_room.zpos + direction.z * 5
        while get_distance_to_nearest(to_room) < 10.0:               
            to_room.xpos = to_room.xpos + direction.x * 2 + 0.5  # if we're too close move it
            to_room.ypos = to_room.ypos + direction.y * 2 + 0.5  # if we're too close move it
    else:
        if from_room.visited:
            return
        inverse = get_direction_from_id(direction.invert_id)
        from_room.xpos = to_room.xpos + inverse.x * 10
        from_room.ypos = to_room.ypos + inverse.y * 10
        from_room.zpos = to_room.zpos + inverse.z * 5

    #sql=f'UPDATE ROOMS SET X = {to_room.xpos}, Y = {to_room.ypos}, Z = {to_room.zpos} WHERE ID = {to_room.id}'
    #db_execute(sql)


def get_distance_to_nearest(this_room) -> float:
    # check distance from connected rooms
    min_distance = 100000    # has to be smaller than this!!
    for other_room in rooms:
        if not other_room.id == this_room.id:
            if other_room.visited:
                dist = distance_between(other_room, this_room)
                if dist < min_distance:
                    min_distance = dist
    return min_distance


def reset_room_coordinates(room: Room):
    global recurse_depth
    recurse_depth += 1
    if recurse_depth > 4 or recurse_depth < 0:
        return
    # print(f"depth is {recurse_depth} within : {room.name}")
    out_paths = get_outward_paths(room.id)
    for path in out_paths:
        set_room_coordinates(path)
        if not path.to_room.visited:
            # print(f"going to: {path.to_room.name}")
            path.to_room.visited = True
            reset_room_coordinates(path.to_room)  # recursive!
            recurse_depth -= 1
        else:
            # print(f"already visited: {path.to_room.name}")
            pass
    in_paths = get_inward_paths(room.id)
    for path in in_paths:
        set_room_coordinates(path)


def reset_all_room_coordinates(starting_room: Room):
    # clear out current values
    for room in rooms:
        room.set_position(0.0, 0.0, 0.0)  
        room.bubble_bounds = (0,0,0,0)
        room.visited = False

    starting_room.visited = True
    reset_room_coordinates(starting_room)

    positions = np.zeros((len(rooms), 2))
    for i, room in enumerate(rooms):
        positions[i, 0] = room.xpos
        positions[i, 1] = room.ypos
    new_positions = adjust_positions(positions=positions, max_distance=50, min_distance=10)
    for i, room in enumerate(rooms):
        room.xpos = new_positions[i, 0]
        room.ypos = new_positions[i, 1]


def draw_new_path_controls(room_id: id):
    global new_path_pane
    if new_path_pane:
        label0 = Label(new_path_pane, text="Add new path or room", bg=LIGHT_GRAY)
        label0.pack(side=TOP, pady=5)
        inside_pane = Frame(new_path_pane, bg=LIGHT_GRAY, height=100)
        inside_pane.pack(side=TOP, pady=5)
        label1 = Label(inside_pane, text="Direction: ", bg=LIGHT_GRAY)
        label1.pack(side=LEFT, padx=5)
        direction_combo = ttk.Combobox(inside_pane, width=20, textvariable=direction_var)
        direction_combo.config(values=direction_names())
        direction_combo.current(0)
        direction_combo.pack(side=LEFT, padx=5)
        label2 = Label(inside_pane, text="Room: ", bg=LIGHT_GRAY)
        label2.pack(side=LEFT, padx=5)
        rooms_combo = ttk.Combobox(inside_pane, width=20, textvariable=room_var)
        rooms_combo.config(values=room_names())
        rooms_combo.current(0)
        rooms_combo.pack(side=LEFT, padx=5)
        one_way_but = Button(inside_pane, text="Create 1-Way Path", command=lambda: add_path_to_room(room_id, direction_var.get(), room_var.get()))
        one_way_but.pack(side=LEFT, padx=5, fill=X)
        two_way_but = Button(inside_pane, text="Create 2-Way Paths", command=lambda: add_path_to_room(room_id, direction_var.get(), room_var.get(), mutual=True))
        two_way_but.pack(side=LEFT, padx=5, fill=X)
        new_room_but = Button(new_path_pane, text="Create Unconnected Room", width=20, command=add_unconnected_room)
        new_room_but.pack(side=TOP, pady=25)

        # control buttons
        path_buttons_pane = Frame(new_path_pane, bg=LIGHT_GRAY, height=50)
        map_but = Button(path_buttons_pane, text="Show Map", width=20, command=show_map_window)
        map_but.pack(side=LEFT, padx=10)
        nav_but = Button(path_buttons_pane, text="Find Path to Room", width=20, command=show_navigation_window)
        nav_but.pack(side=LEFT, padx=10)
        src_but = Button(path_buttons_pane, text="Find Path to Object", width=20, command=show_find_object_window)
        src_but.pack(side=LEFT, padx=10)       
        path_buttons_pane.pack(side=TOP, pady=25)


def go_to_room_from_combo(event):
    room_str = room_var_2.get()
    to_id = get_id_from_string(room_str)
    if to_id < 0:
        return
    go_to_room(to_id)


def set_combo_to_room_id(combo: ttk.Combobox, room_id: int):
    values = room_names_no_new()
    room = get_room_from_id(room_id)
    if room:
        wanted = values.index(f"{room.name} : {room.id}")
        if wanted >= 0:
            combo.current(wanted)


def set_combo_to_current_room(combo: ttk.Combobox):
    if current_room:
        set_combo_to_room_id(combo, current_room.id)


def go_to_room_from_string(roomstr: str):
    match = regex.search(r": (\d+)$", roomstr)
    if match:
       to_id = int(match.group(1))
       go_to_room(to_id)
    else:
        return


def go_to_room(room_id):
    global current_room, button_pane, new_path_pane, current_text
    next_room = get_room_from_id(room_id)
    if next_room:
        current_room = next_room
        if name_lab:
            new_text = f'Room {room_id}:'
            name_lab.config(text=new_text)
        if room_name_entry:
            room_name_entry.delete(0, END)
            room_name_entry.insert(0, next_room.name)
        if desc_text:
            desc_text.delete('1.0', END)
            desc_text.insert('1.0', next_room.description)
        if current_text:
            current_text.delete('1.0', END)
            currents = get_current_objs_names(room_id)
            current_text.insert('1.0', ",".join(currents))
    else:
        return
    if button_pane:
        button_pane.destroy()
    button_pane = Frame(data_pane, bg=LIGHT_GRAY, height=500)
    button_pane.pack(side=LEFT, padx=25, fill=Y)
    other_rooms_pane = Frame(button_pane, bg=LIGHT_GRAY)
    other_rooms_lab = Label(other_rooms_pane, text="Go direct to:", bg=LIGHT_GRAY)
    other_rooms_lab.pack(side=LEFT, padx=5)
    other_rooms_combo = ttk.Combobox(other_rooms_pane, width=20, textvariable=room_var_2)
    other_rooms_combo.config(values=room_names_no_new())
    other_rooms_combo.current(0)
    other_rooms_combo.bind('<<ComboboxSelected>>', go_to_room_from_combo)
    other_rooms_combo.pack(side=LEFT, padx=5)
    other_rooms_pane.pack(side=TOP, pady=5)
    outward_paths = get_outward_paths(room_id=next_room.id)
    # inward_paths = get_inward_paths(room_id=next_room.id)
   
    for path in outward_paths:
        place_buttons(path)

    if new_path_pane:
        new_path_pane.destroy()
    new_path_pane = Frame(window, bg=LIGHT_GRAY, height=200, highlightbackground=DARK_GRAY, highlightthickness=1)
    new_path_pane.pack(side=TOP, pady=5, fill=X)
    draw_new_path_controls(room_id)


def delete_path(path: Path, path_pane: Frame):
    sql = f'DELETE FROM PATHS WHERE DIRECTIONID = {path.direction.id} AND FROMID = {path.from_room.id} AND TOID = {path.to_room.id}'
    db_execute(sql)
    paths.remove(path)
    path_pane.destroy()


def place_buttons(path):
    global button_pane
    path_pane = Frame(button_pane, bg=LIGHT_GRAY)

    delete_button = Button(path_pane, text="X", relief=RAISED, command=lambda: delete_path(path, path_pane))
    delete_button.pack(side=RIGHT, padx=5)

    go_button = Button(path_pane, text=f"{path.to_room.name}", width=20, relief=RAISED, command=lambda: go_to_room(path.to_room.id))
    go_button.pack(side=RIGHT, padx=5)
 
    label = Label(path_pane, bg=LIGHT_GRAY, text=f"{path.direction.name}: ")
    label.pack(side=RIGHT, padx=5)

    path_pane.pack(side=TOP, fill=X, pady=5)
        

map_window: Tk = None
map_canvas: Canvas = None
current_map_room: Room = None
factor: float = 5.0
offset_x: int = 0
offset_y: int = 0

def factored_point(point: Tuple[float, float]) -> Tuple[float, float]:
    x, y = point
    x_factored = x  * factor * 2 + offset_x
    y_factored = y * factor + offset_y
    return (x_factored, y_factored)


def get_room_at_position(x: int, y: int) -> Room:
    for room in rooms:
        if not room.visited:
            continue
        # print(room.name, room.bubble_bounds)
        if x > room.bubble_bounds[0] and x < room.bubble_bounds[2]:
            # print("matched horizonal")
            if y > room.bubble_bounds[1] and y < room.bubble_bounds[3]:
                # print("matched vertical")
                return room
    return None


def we_overlap(this_room:Room, x: int, y:int) -> bool:
    for room in rooms:
        if not room.visited or this_room == room:
            continue
        if x > room.bubble_bounds[0] and x < room.bubble_bounds[2]:
            # print("matched horizonal")
            if y > room.bubble_bounds[1] and y < room.bubble_bounds[3]:
                # print("matched vertical")
                return True
    return False


def map_clicked(event):
    global current_map_room, map_canvas
    # print(event.x, event.y)
    room = get_room_at_position(event.x, event.y)
    if room:
        current_map_room = room
        map_canvas.delete(ALL)
        display_map()
        return


def draw_legend(canvas: Canvas):
    # draw compass
    canvas.create_text(40, 20, text="LEGEND", anchor=W)
    canvas.create_text(40, 50, text="North-South: ", anchor=W)
    canvas.create_text(40, 70, text="East-West: ", anchor=W)
    canvas.create_text(40, 90, text="N.West-S.East: ", anchor=W)
    canvas.create_text(40, 110, text="N.East-S.West: ", anchor=W)
    canvas.create_text(40, 130, text="Up-Down: ", anchor=W)
    canvas.create_text(40, 150, text="Enter-Leave: ", anchor=W)
    canvas.create_text(40, 170, text="Special/Magic: ", anchor=W)

    canvas.create_line(150,50,200,50,fill=directions[0].colour, width=2)
    canvas.create_line(210,50,260,50,fill=directions[0].colour, dash=(10,1), width=2)

    canvas.create_line(150,70,200,70,fill=directions[2].colour, width=2)
    canvas.create_line(210,70,260,70,fill=directions[2].colour, dash=(10,1), width=2)

    canvas.create_line(150,90,200,90,fill=directions[7].colour, width=2)
    canvas.create_line(210,90,260,90,fill=directions[7].colour, dash=(10,1), width=2)

    canvas.create_line(150,110,200,110,fill=directions[1].colour, width=2)
    canvas.create_line(210,110,260,110,fill=directions[1].colour, dash=(10,1),width=2)

    canvas.create_line(150,130,200,130,fill=directions[8].colour, width=2, dash=(3,2))
    canvas.create_line(210,130,260,130,fill=directions[9].colour, width=3, dash=(2,3))

    canvas.create_line(150,150,200,150,fill=directions[10].colour, width=2, dash=(4,3))
    canvas.create_line(210,150,260,150,fill=directions[11].colour, width=3, dash=(3,4))

    canvas.create_line(150,170,260,170,fill=directions[16].colour, width=3, dash=(1,2))


def key_pressed_in_map(event):
    pass


def show_map_window():
    global map_window, map_canvas, current_map_room
    map_window = Tk()
    centre_window(map_window, 1500, 1000)
    map_window.title("Map")
    map_canvas = Canvas(map_window, bg='#EEEEEE', width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
    draw_legend(map_canvas)
    map_canvas.pack(fill=BOTH)
    map_canvas.bind("<Button>", map_clicked)
    map_canvas.bind("<Key>", key_pressed_in_map)
    current_map_room = current_room
    display_map()
    map_window.mainloop()


def display_map():
    global map_canvas, factor, offset_x, offset_y, recurse_depth
    if not current_map_room:
        return
    recurse_depth = 0
    reset_all_room_coordinates(current_map_room)
    factor = 12.0  # zoom scale
    # offsets move starting point of map to centre of canvas
    offset_x = 750
    offset_y = 500
    draw_rooms(False) # do this here to get bounds
    draw_paths()
    draw_rooms(True) # do this here to overlay paths
    draw_legend(map_canvas)


def get_closest_connection(connects: list, x: float, y: float, use_alternates: bool = False):
    min_dist = 1000000
    standard_connects = connects[0:8]
    alt_connects = connects[8:]
    chosen_point = standard_connects[0]
    saved_index = 0
    for index in range(0,8):
        x1, y1 = standard_connects[index]
        dist = math.sqrt( (x - x1)**2 + (y - y1)**2 )
        if dist < min_dist:
            min_dist = dist
            chosen_point = standard_connects[index]
            saved_index = index

    if not use_alternates:
        return chosen_point
    else:
        return alt_connects[saved_index]

def return_path_exists(current_path: Path) -> bool:
    for path in paths:
        if path == current_path:
            continue  # don't test ourselves!
        if not path.drawn:
            continue  # only interested in paths we've already drawn
        if current_path.to_room == path.from_room:
            if current_path.from_room == path.to_room:
                return True
    return False


def draw_paths():
    global map_canvas
    for path in paths:
        path.drawn = False
    for path in paths:
        if (not path.from_room.visited) or (not path.to_room.visited):
            continue  # only want to draw paths for nearby rooms, "visited" flag is set in repositioning proces
        # from room
        from_x, from_y = factored_point((path.from_room.xpos, path.from_room.ypos))
        # to room
        to_x, to_y = factored_point((path.to_room.xpos, path.to_room.ypos))

        alternate = return_path_exists(path)

        start_connect = get_closest_connection(path.to_room.connection_points(), from_x, from_y, alternate)  # connect points already factored
        end_connect = get_closest_connection(path.from_room.connection_points(), to_x, to_y, alternate)  # connect points already factored
        start_x, start_y = start_connect
        end_x, end_y = end_connect

        if end_x < 50 or end_y < 50 or start_x < 50 or start_y < 50:
            continue
        if end_x > (CANVAS_WIDTH - 50) or end_y > (CANVAS_HEIGHT - 50) or start_x > (CANVAS_WIDTH - 50) or start_y > (CANVAS_HEIGHT - 50):
            continue

        if path.direction.id in [1,2,3,4,13,15]:  # N, NE, E, SE, Port, Afore
            map_canvas.create_line(start_x, start_y, end_x, end_y, fill=path.direction.colour, arrow=FIRST, width=2)
        elif path.direction.id in [5,6,7,8,14,16]: # S, SW, W, NW, Starboard, Astern
            map_canvas.create_line(start_x, start_y, end_x, end_y, fill=path.direction.colour, arrow=FIRST, dash=(10,1), width=2)
        elif path.direction.id == 9:  # up
            map_canvas.create_line(start_x, start_y, end_x, end_y, fill=path.direction.colour, arrow=FIRST, dash=(3,2), width=2)
        elif path.direction.id == 10:  # down
            map_canvas.create_line(start_x, start_y, end_x, end_y, fill=path.direction.colour, arrow=FIRST, dash=(2,2), width=3)
        elif path.direction.id == 11:  # enter
            map_canvas.create_line(start_x, start_y, end_x, end_y, fill=path.direction.colour, arrow=FIRST, dash=(3,4), width=2)
        elif path.direction.id == 12:  # exit - draw dashed line
            map_canvas.create_line(start_x, start_y, end_x, end_y, fill=path.direction.colour, arrow=FIRST, dash=(4,3), width=3)
        elif path.direction.id == 17:  # magic - draw dotted line
            map_canvas.create_line(start_x, start_y, end_x, end_y, fill=path.direction.colour, arrow=FIRST, dash=(1,2), width=3)
        else:
            map_canvas.create_line(start_x, start_y, end_x, end_y, fill=path.direction.colour, arrow=FIRST, width=2)
        path.drawn = True


def draw_rooms(do_draw: bool = False):
    global map_canvas
    for room in rooms:   
        if (room.visited):
            x, y = factored_point((room.xpos, room.ypos))
            if x < 50 or y < 50:
                continue
            if x > CANVAS_WIDTH - 50 or y > CANVAS_HEIGHT - 50:
                continue
            # create text so we can measure it
            myText = map_canvas.create_text(x, y, anchor=CENTER, justify=CENTER,text=room.name, tags="roomtext")
            bounds = map_canvas.bbox(myText)
            if do_draw:
                if not room.id == current_map_room.id:
                    map_canvas.create_oval(bounds[0] - 10, bounds[1] - 20, bounds[2] + 10, bounds[3] + 20, fill="white")
                else: # "You are here"
                    map_canvas.create_oval(bounds[0] - 10, bounds[1] - 20, bounds[2] + 10, bounds[3] + 20, fill=CREAM, outline="red", width=2, tags=f"{current_map_room.id}")
            room.bubble_bounds = (bounds[0] - 10, bounds[1] - 20, bounds[2] + 10, bounds[3] + 20)
            # now write text again
            map_canvas.delete(myText)
            if do_draw:
               myText = map_canvas.create_text(x, y, anchor=CENTER, justify=CENTER,text=room.name, tags="roomtext")


results_text: scrolledtext.ScrolledText = None
nav_stack: List[Path] = []
solutions = []

def list_nav_stack() -> str:
    accum: str = ""
    for path in nav_stack:
        accum += path.from_room.name + "->"
    return accum

# def xx_search_outward(from_id: int, wanted_id: int):
#     global nav_stack, search_success, rooms
#     out_paths = get_unvisited_paths(from_id)  # also rejects deadend rooms
#     if not out_paths:  # we've reached a deadend, mark it as such
#         from_room = get_room_from_id(from_id)
#         from_room.deadend = True
#         logging("Dead end! Tried: " + list_nav_stack())
#         if nav_stack:
#             nav_stack.pop()
#         return
        
#     # pick one path at random
#     if len(out_paths) <= 1:
#         path = out_paths[0]
#     else:
#         index = randint(0, len(out_paths)-1)
#         path = out_paths[index]
#     nav_stack.append(path)
#     # logging(f"checking {path.from_room.name} -> {path.to_room.name}")
    
#     if path.to_room.id == wanted_id:
#         logging("Found!" + list_nav_stack() + "->" + path.to_room.name)
#         search_success = True
#         return
#     else:
#         path.to_room.visited = True
#         xx_search_outward(path.to_room.id, wanted_id) # recursive!!
        

def reveal_solution(solution: list):
    nav_str = ""
    for found_path in solution:
        nav_str += f"{found_path.direction.name} to {found_path.to_room.name}\n"
    results_text.delete("1.0", END)
    results_text.insert(END, nav_str)


def generate_navigation_to_obj(from_room_str: str, to_obj_str: str):
    to_id = get_id_from_string(to_obj_str)
    if to_id < 0:
        return

    # find room where the object currently is
    obj: Object = None
    for obj in objs:
        if obj.object_id == to_id:
            room_id = obj.current_id
            # fudge a call to the room to room navigation
            generate_navigation(from_room_str, f"xxxx : {room_id}")


def generate_navigation(from_room_str: str, to_room_str: str):
    global search_success, nav_stack

    graph = generate_graph()
    
    from_id = get_id_from_string(from_room_str)
    if from_id < 0:
        return

    to_id = get_id_from_string(to_room_str)
    if to_id < 0:
        return
   
    found_path = dijkstra(graph, from_id, to_id)

    if found_path:
        nav_str = ""
        for index in range(0,len(found_path) - 1):
            leg = get_path_from_ends(found_path[index], found_path[index+1])
            if leg:
                nav_str += f"{leg.direction.name} to {leg.to_room.name}\n"
        results_text.delete("1.0", END)
        results_text.insert(END, nav_str)
    else:
        results_text.delete("1.0", END)
        results_text.insert(END, "No path exists")


def search_for(searchtext: str):
    global search_combo
    lcsearch = searchtext.lower()
    found_list = []
    for room in rooms:
        lcname = room.name.lower()
        lcdesc = room.description.lower()
        if lcsearch in lcname or lcsearch in lcdesc:
            found_list.append(f"{room.id}: {room.name}")
    if found_list:
        search_combo.delete(0, END)
        search_combo.config(values=found_list)
        search_combo.current(0)

def get_obj_names_from_list(obj_list) -> list:
    names = []
    obj: Object = None
    for obj in sorted(obj_list):
        names.append(f"{obj.name} : {obj.object_id}")
    return names

def get_object_from_id(id: int) -> Object:
    obj: Object = None
    for obj in objs:
        if obj.object_id == id:
            return obj
    return None


def obj_combo_selected(wanted: str, name: str, room_id: int, win: Tk):
    match = regex.search(f": (\d+)", wanted)
    if match:
        wanted_id = int(match.group(1))
        obj = get_object_from_id(wanted_id)
        update_object_location(obj, name, room_id)
    win.destroy()


def show_obj_select(obj_list: list, name: str, room_id: int):
    select_win = Tk()
    centre_window(select_win, 500, 150)
    select_win.title("Select object")
    select_win.config(bg=LIGHT_GRAY)
    label = Label(select_win, text="Which of these objects do you mean?", bg=LIGHT_GRAY)
    label.pack(side=TOP, pady=5)
    combo_str = StringVar()
    obj_combo = ttk.Combobox(select_win, width=20, textvariable=combo_str)
    obj_combo.pack(side=LEFT, padx=5)
    obj_combo.config(values=get_obj_names_from_list(obj_list))
    obj_combo.current(0)
    obj_combo.pack(side=TOP, pady=5)
    ok_button = Button(select_win, text="OK", bg=LIGHT_GRAY, command=lambda: obj_combo_selected(obj_combo.get(), name, room_id, select_win))
    ok_button.pack(side=TOP, pady=5)
    select_win.mainloop()


def get_obj_names():
    ret_list = []
    obj: Object = None
    for obj in sorted(objs):
        ret_list.append(f'{obj.name} : {obj.object_id}')
    return ret_list


def update_manage_objs_form(event):
    global obj_name_entry, obj_alias_entry, found_combo, current_combo
    if object_combo:
        obj_str = object_combo.get()
        obj_id = get_id_from_string(obj_str)
        if obj_id < 0:
            return
        obj = get_object_from_id(obj_id)
        obj_name_entry.delete(0, END)
        obj_name_entry.insert(0, obj.name)
        obj_alias_entry.delete(0, END)
        if obj.aliases:
            obj_alias_entry.insert(0, obj.aliases)
        set_combo_to_room_id(found_combo, obj.found_id)
        set_combo_to_room_id(current_combo, obj.current_id)


def update_object_details(obj_id_str: str, name: str, alias: str, found_str: str, current_str: str):
    obj_id = get_id_from_string(obj_id_str)
    if obj_id < 0:
        return
    obj = get_object_from_id(obj_id)
    if obj:
        obj.name = name
        obj.aliases = alias
        found_id = get_id_from_string(found_str)
        if found_id >= 0:
            obj.found_id = found_id
        current_id = get_id_from_string(current_str)
        if current_id:
            obj.current_id = current_id
        sql = f'UPDATE OBJECTS SET Name = "{name}", Aliases = "{alias}", FoundRoom = {found_id}, CurrentRoom = {found_id} WHERE ID={obj.object_id}'
        db_execute(sql)


def show_manage_objs():
    global object_combo, obj_name_entry, obj_alias_entry, found_combo, current_combo
    object_win = Tk()
    centre_window(object_win, 500, 350)
    object_win.title("Manage objects")
    object_win.config(bg=LIGHT_GRAY)

    combo_pane = Frame(object_win, bg=LIGHT_GRAY)
    label = Label(combo_pane, text="Select object", bg=LIGHT_GRAY)
    label.pack(side=TOP, pady=5)
    object_combo = ttk.Combobox(combo_pane, width=20)
    object_combo.pack(side=LEFT, padx=5)
    object_combo.config(values=get_obj_names())
    object_combo.current(0)
    object_combo.pack(side=TOP, pady=5)
    combo_pane.pack(side=TOP, pady=5)
    object_combo.bind("<<ComboboxSelected>>", update_manage_objs_form)

    name_pane = Frame(object_win, bg=LIGHT_GRAY)
    name_lab = Label(name_pane, text="Name: ", bg=LIGHT_GRAY)
    name_lab.pack(side=LEFT, padx=5)
    obj_name_entry = Entry(name_pane, width=25)
    obj_name_entry.pack(side=LEFT, padx=5)
    name_pane.pack(side=TOP, pady=5)

    alias_pane = Frame(object_win, bg=LIGHT_GRAY)
    alias_lab = Label(alias_pane, text="Aliases: ", bg=LIGHT_GRAY)
    alias_lab.pack(side=LEFT, padx=5)
    obj_alias_entry = Entry(alias_pane, width=25)
    obj_alias_entry.pack(side=LEFT, padx=5)
    alias_pane.pack(side=TOP, pady=5)

    found_pane = Frame(object_win, bg=LIGHT_GRAY)
    found_lab = Label(found_pane, text="Room First Found: ", bg=LIGHT_GRAY)
    found_lab.pack(side=LEFT, padx=5)
    found_combo = ttk.Combobox(found_pane, width=20)
    found_combo.pack(side=LEFT, padx=5)
    found_combo.config(values=room_names_no_new())
    found_combo.current(0)
    found_pane.pack(side=TOP, pady=5)

    current_pane = Frame(object_win, bg=LIGHT_GRAY)
    current_lab = Label(current_pane, text="Room Now In: ", bg=LIGHT_GRAY)
    current_lab.pack(side=LEFT, padx=5)
    current_combo = ttk.Combobox(current_pane, width=20)
    current_combo.pack(side=LEFT, padx=5)
    current_combo.config(values=room_names_no_new())
    current_combo.current(0)
    current_pane.pack(side=TOP, pady=5)

    ok_button = Button(object_win, text="Update This Object", bg=LIGHT_GRAY, 
        command=lambda: update_object_details(object_combo.get(), obj_name_entry.get(), obj_alias_entry.get(), found_combo.get(), current_combo.get()))
    ok_button.pack(side=TOP, pady=5)

    reset_button = Button(object_win, text="Return All Objects to Starting Positions", bg=LIGHT_GRAY)
    reset_button.pack(side=TOP, pady=25)

    object_win.mainloop()


def show_search_window():
    global search_combo, room_var_2
    search_win = Tk()
    centre_window(search_win, 500, 150)
    search_win.title("Search for text in rooms")
    search_win.config(bg=LIGHT_GRAY)

    searchtext = StringVar()
    # found_room = StringVar(search_win)

    pane = Frame(search_win, bg=LIGHT_GRAY)
    pane.pack(side=TOP, fill=X)
    label = Label(pane, text="Search for: ", bg=LIGHT_GRAY)
    label.pack(side=LEFT, padx=5)
    search_entry = Entry(pane, width=25, textvariable=searchtext)
    search_entry.pack(side=LEFT, padx=5)
    button = Button(pane, text="Search", command=lambda: search_for(search_entry.get()))
    button.pack(side=LEFT, padx=5)
    label2 = Label(search_win, text="Rooms found will appear here. Select one to go there.", bg=LIGHT_GRAY)
    label2.pack(side=TOP, pady=5)
    search_pane = Frame(search_win, bg=LIGHT_GRAY)
    search_combo = ttk.Combobox(search_pane, width=20, textvariable=room_var_2)
    search_combo.config(values= ["0: Nowhere"])
    search_combo.current(0)
    search_combo.bind('<<ComboboxSelected>>', go_to_room_from_combo)
    search_combo.pack(side=LEFT, padx=5)
    go_button = Button(search_pane, text="Go", command=lambda: go_to_room_from_string(search_combo.get()))
    go_button.pack(side=LEFT, padx=5)
    search_pane.pack(side=TOP, pady=5)
    search_win.mainloop()


def swap_rooms_in_combos(combo1: ttk.Combobox, combo2: ttk.Combobox):
    room_str_1 = combo1.get()
    room_str_2 = combo2.get()
    r1_id = get_id_from_string(room_str_1)
    r2_id = get_id_from_string(room_str_2)
    if r1_id >= 0 and r2_id >= 0:
        set_combo_to_room_id(combo2, r1_id)
        set_combo_to_room_id(combo1, r2_id)


def get_id_from_string(idstr: str) -> int:
    match = regex.search(r": (\d+)$", idstr)
    if match:
        id = int(match.group(1))
        return id
    else:
        return -1


def show_navigation_window():
    global results_text
    text_window = Tk()
    centre_window(text_window, 700, 250)
    text_window.title("Get navigation commands")
    text_window.config(bg=LIGHT_GRAY)

    from_str = StringVar()
    to_str = StringVar()

    combo_panel = Frame(text_window, bg=LIGHT_GRAY)
    from_label = Label(combo_panel, text="From Room:", bg=LIGHT_GRAY)
    from_label.pack(side=LEFT, padx=5)
    from_combo = ttk.Combobox(combo_panel, width=20, textvariable=from_str)
    from_combo.pack(side=LEFT, padx=5)
    from_combo.config(values=room_names_no_new())
    from_combo.current(0)
    set_combo_to_current_room(from_combo)
    to_label = Label(combo_panel, text="To Room:", bg=LIGHT_GRAY)
    to_label.pack(side=LEFT, padx=5)
    to_combo = ttk.Combobox(combo_panel, width=20, textvariable=to_str)
    to_combo.config(values=room_names_no_new())
    to_combo.pack(side=LEFT, padx=5)
    to_combo.current(0)
    swap_button = Button(combo_panel, text="Swap", command=lambda: swap_rooms_in_combos(from_combo, to_combo))
    swap_button.pack(side=LEFT, padx=5)
    combo_panel.pack(side=TOP, fill=X, pady=5)
    get_text_but = Button(text_window, text="Get Directions", command=lambda: generate_navigation(from_combo.get(), to_combo.get()))
    get_text_but.pack(side=TOP, pady=5)

    results_text = scrolledtext.ScrolledText(text_window, width=40, height=10)

    # results_text = Text(text_window, width=60, height=5)
    results_text.pack(side=TOP, pady=5)
    text_window.mainloop()


def show_find_object_window():
    global results_text
    text_window = Tk()
    centre_window(text_window, 700, 250)
    text_window.title("Navigate to object")
    text_window.config(bg=LIGHT_GRAY)

    from_str = StringVar()
    to_str = StringVar()

    combo_panel = Frame(text_window, bg=LIGHT_GRAY)
    from_label = Label(combo_panel, text="From Room:", bg=LIGHT_GRAY)
    from_label.pack(side=LEFT, padx=5)
    from_combo = ttk.Combobox(combo_panel, width=20, textvariable=from_str)
    from_combo.pack(side=LEFT, padx=5)
    from_combo.config(values=room_names_no_new())
    from_combo.current(0)
    set_combo_to_current_room(from_combo)
    to_label = Label(combo_panel, text="To Object:", bg=LIGHT_GRAY)
    to_label.pack(side=LEFT, padx=5)
    to_combo = ttk.Combobox(combo_panel, width=20, textvariable=to_str)
    to_combo.config(values=obj_names())
    to_combo.pack(side=LEFT, padx=5)
    to_combo.current(0)
    combo_panel.pack(side=TOP, fill=X, pady=5)
    get_text_but = Button(text_window, text="Get Directions", command=lambda: generate_navigation_to_obj(from_combo.get(), to_combo.get()))
    get_text_but.pack(side=TOP, pady=5)

    results_text = scrolledtext.ScrolledText(text_window, width=40, height=10)

    # results_text = Text(text_window, width=60, height=5)
    results_text.pack(side=TOP, pady=5)
    text_window.mainloop()

delete_log()
draw_menu(window)
draw_controls(window)
if db_path:  # passed as argument
    open_existing(from_args=True)

window.mainloop()
