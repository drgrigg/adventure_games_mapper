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

import regex
import sqlite3

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


folder = os.path.normpath(sys.argv[0])
folder_bits = os.path.split(folder)
my_folder = folder_bits[0]
sql_statements = []

with open(os.path.join(".", "create_new.sql"), "r") as sfile:
    sql_statements = sfile.readlines()
    sfile.close()

db_folder = my_folder
db_path = ""
if len(sys.argv) > 1:
    db_path = sys.argv[1]

rooms: List[Room] = []
directions: List[Direction] = []
paths: List[Path] = []
# combos: List[ttk.Combobox] = []

def room_names() -> list:
    ret_list = ["0: NEW ROOM"]
    for room in rooms:
        ret_list.append(f"{room.id}: {room.name}")
    return ret_list


def room_names_no_new() -> list:
    ret_list = ["0: Nowhere"]
    for room in rooms:
        ret_list.append(f"{room.id}: {room.name}")
    return ret_list


def direction_names() -> list:
    ret_list = ["None"]
    for direction in directions:
        ret_list.append(f"{direction.id}: {direction.name}")
    return ret_list


LIGHT_GRAY = "#A0A0A0"
DARK_GRAY = "#808080"
BLACK = "#000000"

window = Tk()
window.geometry("1000x800+200+200")
window.title("Adventure Game Mapper")
window.config(bg=LIGHT_GRAY)

current_room: Room = None
db_lab: Label = None
name_lab: Label = None
name_entry: Entry = None
desc_text: Text = None
button_pane: Frame = None
new_path_pane: Frame = None
data_pane: Frame = None
direction_var = StringVar()
room_var = StringVar()
room_var_2 = StringVar()


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
    global rooms, directions, paths
    conn = sqlite3.connect(path_to_db)
    cursor = conn.cursor()
    rooms = []
    paths = []
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
    toolmenu.add_command(label="Show Map", command=make_map_window)
    toolmenu.add_command(label="Generate Navigation", command=show_textpath_window)
    menubar.add_cascade(label="Tools", menu=toolmenu)

    helpmenu = Menu(menubar, tearoff=0)
    helpmenu.add_command(label="Help Index", command=do_nothing)
    helpmenu.add_command(label="About...", command=do_nothing)
    menubar.add_cascade(label="Help", menu=helpmenu)

    window.config(menu=menubar)

def update_room_details():
    if current_room:
        temp_name = name_entry.get()
        temp_desc = desc_text.get('1.0', END)
        # only rewrite if changed.
        if (not current_room.name == temp_name) or (not current_room.description == temp_desc):
            current_room.name = temp_name
            current_room.description = temp_desc
            sql = f'UPDATE ROOMS SET Name = "{temp_name}", Description = "{temp_desc}" WHERE Id = {current_room.id}'
            db_execute(sql)


def draw_controls(window: Tk):
    global db_lab, name_lab, name_entry, desc_text, button_pane, new_path_pane, data_pane

    db_lab = Label(window, text="Game file: none selected", bg=LIGHT_GRAY)
    db_lab.pack(side=TOP, pady=5, fill=X)

    data_pane = Frame(window, bg=LIGHT_GRAY, height=600, highlightbackground=DARK_GRAY, highlightthickness=1)
    
    room_pane = Frame(data_pane, bg=LIGHT_GRAY, height=500, highlightbackground=DARK_GRAY, highlightthickness=1)
    entry_pane = Frame(room_pane, bg=LIGHT_GRAY, highlightbackground=DARK_GRAY, highlightthickness=1)
    name_lab = Label(entry_pane, text="Room:", bg=LIGHT_GRAY)
    name_lab.pack(side=LEFT, padx=5)
    name_entry = Entry(entry_pane, width=25)
    name_entry.pack(side=LEFT, pady=5)
    entry_pane.pack(side=TOP, pady=5)

    desc_text = Text(room_pane, width=60, height=10)
    desc_text.pack(side=TOP, pady=5)

    update_but = Button(room_pane, text="Update", command=update_room_details)
    update_but.pack(side=TOP, pady=5)

    room_pane.pack(side=LEFT, padx=5)

    # we'll fill this with buttons representing the directions we can go
    button_pane = Frame(data_pane, bg=LIGHT_GRAY, height=500, highlightbackground=DARK_GRAY, highlightthickness=1)
    button_pane.pack(side=LEFT, padx=5)
    data_pane.pack(side=TOP, padx=5, fill=X)

    new_path_pane = Frame(window, bg=LIGHT_GRAY, height=200, highlightbackground=DARK_GRAY, highlightthickness=1)
    new_path_pane.pack(side=TOP, pady=5)
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

def get_outward_paths(room_id: int) -> list:
    path_list = []
    for path in paths:
        if path.from_room:
            if path.from_room.id == room_id:
                path_list.append(path)
    return path_list


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
    # we need to place it geometrically in a different area until we update it with a new path to it
    fudge = int(get_max_room_distance()) + 50.0
    sql = f'INSERT INTO ROOMS (Name, Description, X, Y, Z) VALUES ("New Room", "Description", {fudge}, {fudge}, {0.0})'
    new_id = db_execute_get_id(sql)
    new_room = Room(new_id, "New Room", "Description")
    new_room.set_position(fudge, fudge, 0.0)
    rooms.append(new_room)
    update_room_details()  #updates current room
    go_to_room(new_id)


def add_path_to_room(from_id: int, direct_str: str, room_str: str, mutual: bool = False):
    direct_id = 0
    to_id = 0
    match = regex.search(r"^(\d+):", direct_str)
    if match:
        direct_id = int(match.group(1))
    else:
        return
    match = regex.search(r"^(\d+):", room_str)
    if match:
       to_id = int(match.group(1))
    else:
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
    if recurse_depth > 2 or recurse_depth < 0:
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


def draw_new_path_controls(room_id: id):
    global new_path_pane
    if new_path_pane:
        label0 = Label(new_path_pane, text="Add new path or room", bg=LIGHT_GRAY)
        label0.pack(side=TOP, pady=5)
        inside_pane = Frame(new_path_pane, bg=LIGHT_GRAY, height=100, highlightbackground=DARK_GRAY, highlightthickness=1)
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
        button = Button(inside_pane, text="Create 1-Way Path", command=lambda: add_path_to_room(room_id, direction_var.get(), room_var.get()))
        button.pack(side=LEFT, padx=5, fill=X)
        button3 = Button(inside_pane, text="Create 2-Way Paths", command=lambda: add_path_to_room(room_id, direction_var.get(), room_var.get(), mutual=True))
        button3.pack(side=LEFT, padx=5, fill=X)
        new_room_but = Button(new_path_pane, text="Create Unconnected Room", command=add_unconnected_room)
        new_room_but.pack(side=TOP, padx=5)
        map_but = Button(new_path_pane, text="Show Map", command=make_map_window)
        map_but.pack(side=TOP, pady=5)

def go_to_room_from_combo(event):
    room_str = room_var_2.get()
    match = regex.search(r"^(\d+):", room_str)
    if match:
       to_id = int(match.group(1))
       go_to_room(to_id)
    else:
        return

def go_to_room(room_id):
    global window, button_pane, new_path_pane, data_pane, current_room, room_var_2, name_lab, name_entry
    next_room = get_room_from_id(room_id)
    if next_room:
        current_room = next_room
        if name_lab:
            new_text = f'Room {room_id}:'
            name_lab.config(text=new_text)
        if name_entry:
            name_entry.delete(0, END)
            name_entry.insert(0, next_room.name)
        if desc_text:
            desc_text.delete('1.0', END)
            desc_text.insert('1.0', next_room.description)
    else:
        return
    if button_pane:
        button_pane.destroy()
    button_pane = Frame(data_pane, bg=LIGHT_GRAY, height=500, highlightbackground=DARK_GRAY, highlightthickness=1)
    button_pane.pack(side=LEFT, padx=5)
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
    new_path_pane.pack(side=TOP, pady=5)
    draw_new_path_controls(room_id)

    # navig_button = Button(window, text="Get Navigation Commands", command=show_textpath_window, tags="navbutton")
    # navig_button.pack(side=TOP, pady=5)

def delete_path(path: Path, path_pane: Frame):
    sql = f'DELETE FROM PATHS WHERE DIRECTIONID = {path.direction.id} AND FROMID = {path.from_room.id} AND TOID = {path.to_room.id}'
    db_execute(sql)
    paths.remove(path)
    path_pane.destroy()


def place_buttons(path):
    global button_pane
    path_pane = Frame(button_pane, bg=LIGHT_GRAY, highlightbackground=DARK_GRAY, highlightthickness=1)
    label = Label(path_pane, bg=LIGHT_GRAY, text=f"{path.direction.id}: {path.direction.name}: ")
    label.pack(side=LEFT, padx=5)
    go_button = Button(path_pane, text=f"{path.to_room.id}: {path.to_room.name}", relief=RAISED, command=lambda: go_to_room(path.to_room.id))
    go_button.pack(side=LEFT, padx=5)
    delete_button = Button(path_pane, text="X", relief=RAISED, command=lambda: delete_path(path, path_pane))
    delete_button.pack(side=LEFT, padx=5)
    path_pane.pack(side=TOP, pady=5)
        

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

    canvas.create_line(150,50,250,50,fill=directions[0].colour, width=2)
    canvas.create_line(150,70,250,70,fill=directions[2].colour, width=2)
    canvas.create_line(150,90,250,90,fill=directions[7].colour, width=2)
    canvas.create_line(150,110,250,110,fill=directions[1].colour, width=2)
    canvas.create_line(150,130,250,130,fill=directions[8].colour, width=2)
    canvas.create_line(150,150,250,150,fill=directions[10].colour, width=2)
    canvas.create_line(150,170,250,170,fill=directions[16].colour, width=2)


def make_map_window():
    global map_window, map_canvas, current_map_room
    map_window = Tk()
    map_window.geometry("1500x1000")
    map_window.title("Map")
    map_canvas = Canvas(map_window, bg='#EEEEEE', width=1490, height=950)
    draw_legend(map_canvas)
    map_canvas.pack(fill=BOTH)
    map_canvas.bind("<Button>", map_clicked)
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

        if path.direction.id >= 9 and path.direction.id <= 12:  # up, down, enter, leave - draw dashed line
            map_canvas.create_line(start_x, start_y, end_x, end_y, fill=path.direction.colour, arrow=FIRST, dash=(3,2), width=2)
        else:
            map_canvas.create_line(start_x, start_y, end_x, end_y, fill=path.direction.colour, arrow=FIRST, width=2)
        path.drawn = True


def draw_rooms(do_draw: bool = False):
    global map_canvas
    for room in rooms:   
        if (room.visited):
            x, y = factored_point((room.xpos, room.ypos))
            # create text so we can measure it
            myText = map_canvas.create_text(x, y, anchor=CENTER, justify=CENTER,text=room.name, tags="roomtext")
            bounds = map_canvas.bbox(myText)
            if do_draw:
                map_canvas.create_oval(bounds[0] - 10, bounds[1] - 20, bounds[2] + 10, bounds[3] + 20, fill="white")
            room.bubble_bounds = (bounds[0] - 10, bounds[1] - 20, bounds[2] + 10, bounds[3] + 20)
            # now write text again
            map_canvas.delete(myText)
            if do_draw:
               myText = map_canvas.create_text(x, y, anchor=CENTER, justify=CENTER,text=room.name, tags="roomtext")


results_text: scrolledtext.ScrolledText = None
nav_stack: List[Path] = []
solutions = []

def search_outward(from_id: int, wanted_id: int):
    global nav_stack, search_success, rooms
    out_paths = get_unvisited_paths(from_id)  # also rejects deadend rooms
    if not out_paths:  # we've reached a deadend, mark it as such
        from_room = get_room_from_id(from_id)
        from_room.deadend = True
        print("reached dead end")
        nav_stack.pop()
        return
        
    # pick one path at random
    if len(out_paths) <= 1:
        path = out_paths[0]
    else:
        index = randint(0, len(out_paths)-1)
        path = out_paths[index]
    nav_stack.append(path)
    print(f"checking {path.from_room.name} -> {path.to_room.name}")
    
    if path.to_room.id == wanted_id:
        print("found!")
        search_success = True
        return
    else:
        path.to_room.visited = True
        search_outward(path.to_room.id, wanted_id) # recursive!!
        

def reveal_solution(solution: list):
    nav_str = ""
    for found_path in solution:
        nav_str += f"{found_path.direction.name} to {found_path.to_room.name}\n"
    results_text.delete("1.0", END)
    results_text.insert(END, nav_str)


def generate_navigation(from_room_str: str, to_room_str: str):
    global search_success, nav_stack
    
    match = regex.search(r"^(\d+):", from_room_str)
    if match:
        from_id = int(match.group(1))
    else:
        return
    match = regex.search(r"^(\d+):", to_room_str)
    if match:
       to_id = int(match.group(1))
    else:
        return
    from_room = get_room_from_id(from_id)
    
    solutions = []
    
    for room in rooms:
        room.deadend = False
    
    # loop through this lots of times (random walks)
    for _ in range(0, 20):
        nav_stack = []
        for room in rooms:
            room.visited = False
        from_room.visited = True
        search_success = False
        search_outward(from_id, to_id)
        if search_success:
            temp = [] # need to COPY values
            for path in nav_stack:
                temp.append(path)
            solutions.append(temp) 
        
    
    if solutions:
        # find shortest one
        best = solutions[0]
        shortest = 10000
        for solution in solutions:
            if len(solution) < shortest:
                shortest = len(solution)
                best = solution
        reveal_solution(best)
    else:
        results_text.delete("1.0", END)
        results_text.insert(END, "No path exists")


def show_textpath_window():
    global results_text
    text_window = Tk()
    text_window.geometry("700x250+250+250")
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
    to_label = Label(combo_panel, text="From Room:", bg=LIGHT_GRAY)
    to_label.pack(side=LEFT, padx=5)
    to_combo = ttk.Combobox(combo_panel, width=20, textvariable=to_str)
    to_combo.config(values=room_names_no_new())
    to_combo.pack(side=LEFT, padx=5)
    to_combo.current(0)
    combo_panel.pack(side=TOP, fill=X, pady=5)
    get_text_but = Button(text_window, text="Get Commands", command=lambda: generate_navigation(from_combo.get(), to_combo.get()))
    get_text_but.pack(side=TOP, pady=5)

    results_text = scrolledtext.ScrolledText(text_window, width=40, height=10)

    # results_text = Text(text_window, width=60, height=5)
    results_text.pack(side=TOP, pady=5)
    text_window.mainloop()


draw_menu(window)
draw_controls(window)
if db_path:  # passed as argument
    open_existing(from_args=True)

window.mainloop()
