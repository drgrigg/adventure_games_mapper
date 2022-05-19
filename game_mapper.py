#!/usr/bin/env python3

import os
import sys
from datetime import datetime, timedelta
from typing import List, Tuple
from enum import Enum
from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
import regex
import sqlite3

class Direction():
    id = 0
    name = ""
    x = 0.0
    y = 0.0
    z = 0.0
    def __init__(self, id: int, name: str, x: float, y: float, z: float):
        self.id = id
        self.name = name
        self.x = x
        self.y = y
        self.z = z


class Room():
    id = 0
    name = ""
    description = ""
    xpos = 0.0
    ypos = 0.0
    zpos = 0.0
    def __init__(self, id: int, name: str, desc: str = ""):
        self.id = id
        self.name = name


class Path():
    direction: Direction = None
    to_room: Room = None
    from_room: Room = None

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
rooms: List[Room] = []
directions: List[Direction] = []
paths: List[Path] = []
combos: List[ttk.Combobox] = []

def room_names() -> list:
    ret_list = ["0: NEW ROOM"]
    for room in rooms:
        ret_list.append(f"{room.id}: {room.name}")
    return ret_list


def room_names_no_new() -> list:
    ret_list = []
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
        aroom.xpos = row[4]
        aroom.ypos = row[5]
        aroom.zpos = row[6]
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
        direction = Direction(id, name, x, y, z)
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

def open_existing():
    global db_path
    db_path = get_existing_file(my_folder)
    if db_path:
        if db_lab:
            db_lab.config(text=f"Game file: {db_path}")
        load_data(db_path)
        go_to_room(1)


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

    helpmenu = Menu(menubar, tearoff=0)
    helpmenu.add_command(label="Help Index", command=do_nothing)
    helpmenu.add_command(label="About...", command=do_nothing)
    menubar.add_cascade(label="Help", menu=helpmenu)

    window.config(menu=menubar)

def update_room_details():
    if current_room:
        current_room.name = name_entry.get()
        current_room.description = desc_text.get('1.0', END)
        sql = f'UPDATE ROOMS SET Name = "{name}", Description = "{desc}" WHERE Id = {current_room.id}'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()


def draw_controls(window: Tk):
    global db_lab, name_entry, desc_text, button_pane, new_path_pane, data_pane

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

def get_paths_for_room(room_id: int) -> list:
    path_list = []
    for path in paths:
        if path.from_room:
            if path.from_room.id == room_id:
                path_list.append(path)
    return path_list

def add_unconnected_room():
    # it's a new room, create an empty one first
    sql = f'INSERT INTO ROOMS (Name, Description) VALUES ("New Room", "Description")'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    new_id = cursor.lastrowid
    new_room = Room(new_id, "New Room", "Description")
    rooms.append(new_room)
    update_room_details()  #updates current room
    go_to_room(new_id)


def add_path_to_room(from_id: int, direct_str: str, room_str: str):
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
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        to_id = cursor.lastrowid
        new_room = Room(to_id, "New Room", "Description")
        rooms.append(new_room)

    sql = f'INSERT INTO PATHS (DirectionID, FromID, ToID) VALUES({direct_id}, {from_id}, {to_id});'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    direction = get_direction_from_id(direct_id)
    to_room = get_room_from_id(to_id)
    from_room = get_room_from_id(from_id)
    path = Path(direction=direction, to_room=to_room, from_room=from_room)
    paths.append(path)
    update_room_details()
    go_to_room(to_id)


def draw_new_path_controls(room_id: id):
    global new_path_pane
    if new_path_pane:
        label0 = Label(new_path_pane, text="Add new path or room", bg=LIGHT_GRAY)
        label0.pack(side=TOP, pady=5)
        label1 = Label(new_path_pane, text="Direction: ", bg=LIGHT_GRAY)
        label1.pack(side=LEFT, padx=5)
        direction_combo = ttk.Combobox(new_path_pane, width=20, textvariable=direction_var)
        direction_combo.config(values=direction_names())
        direction_combo.current(0)
        direction_combo.pack(side=LEFT, padx=5)
        label2 = Label(new_path_pane, text="Room: ", bg=LIGHT_GRAY)
        label2.pack(side=LEFT, padx=5)
        rooms_combo = ttk.Combobox(new_path_pane, width=20, textvariable=room_var)
        rooms_combo.config(values=room_names())
        rooms_combo.current(0)
        rooms_combo.pack(side=LEFT, padx=5)
        button = Button(new_path_pane, text="Create Path", command=lambda: add_path_to_room(room_id, direction_var.get(), room_var.get()))
        button.pack(side=LEFT, padx=5)
        new_room_but = Button(window, text="Create Unconnected Room", command=add_unconnected_room)
        new_room_but.pack(side=TOP, padx=5)

def go_to_room_from_combo(event):
    room_str = room_var_2.get()
    match = regex.search(r"^(\d+):", room_str)
    if match:
       to_id = int(match.group(1))
       go_to_room(to_id)
    else:
        return

def go_to_room(room_id):
    global window, button_pane, new_path_pane, data_pane, current_room, room_var_2
    room = get_room_from_id(room_id)
    if room:
        current_room = room
        if name_entry:
            name_entry.delete(0, END)
            name_entry.insert(0, room.name)
        if desc_text:
            desc_text.delete('1.0', END)
            desc_text.insert('1.0', room.description)
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
    path_list = get_paths_for_room(room_id=room.id)
    for path in path_list:
        path_pane = Frame(button_pane, bg=LIGHT_GRAY, highlightbackground=DARK_GRAY, highlightthickness=1)
        path_pane.pack(side=TOP, pady=5)
        label = Label(path_pane, bg=LIGHT_GRAY, text=f"{path.direction.name}: ")
        label.pack(side=LEFT, padx=5)
        button = Button(path_pane, text=path.to_room.name, relief=RAISED, command=lambda: go_to_room(path.to_room.id))
        button.pack(side=LEFT, padx=5)
    if new_path_pane:
        new_path_pane.destroy()
    new_path_pane = Frame(window, bg=LIGHT_GRAY, height=200, highlightbackground=DARK_GRAY, highlightthickness=1)
    new_path_pane.pack(side=TOP, pady=5)
    draw_new_path_controls(room_id)
        

draw_menu(window)
draw_controls(window)

window.mainloop()
