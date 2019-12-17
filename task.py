#!/usr/bin/env python

# import modules
import os
import re
import json
import time
from sys import stdout
from sys import exit as byebye

# global variables for reuse
appName = "Task"                                    # Name of the application
dirName = "hello-task"                              # Directory name
homeDir = os.path.expanduser("~")                   # Use home as base
targetDir = homeDir + "/.local/share/" + dirName    # Determine target directory
targetFile = targetDir + "/tasks.json"              # Construct full path
data = {}                                           # JSON written to file
data["tasks"] = []
data["settings"] = []
updateMsg = ""                                      # Feedback messages
idCounter = 1                                       # Used to generate task id
unixDay = 86400                                     # Used to generate timestamp


# function is used by read and write functions
def timeGrab():
    return int(time.time())


# check if JSON exists, execute creation if not
def jsonCheck():
    try:
        f = open(targetFile)
        taskList(targetFile)
    except:
        jsonCreate()


# create JSON file and directory
def jsonCreate():
    if not os.path.exists(targetDir):
        os.mkdir(targetDir, 0o755)
    data["settings"].append({
        "idCounter": idCounter,
        "lvl": 3
    })
    with open(targetFile, "w") as taskfile:
        json.dump(data, taskfile)
    taskList(targetFile)


# write new content to JSON file
def jsonWrite(n):
    global updateMsg
    global data
    global idCounter
    # it's important to 'try' otherwise entries that don't end in
    # the search string will cause massive errors
    try:
        dueTime = re.search(r'(in\s+(\d+?)\s+day(s\b|\b))$', n, re.M|re.I)
        dueTemp = re.search(r'(\d+)', dueTime.group(), re.M|re.I)
        task = n[:-(len(dueTime.group())+1)]
        data["tasks"].append({
            "id": idCounter,
            "task": task,
            # we need to reduce the due time by one second to prevent
            # the timer showing a wrong due date right after creation
            "due": timeGrab()+(int(dueTemp.group())*unixDay-1)
        })
    # if there's no due date supplied, write the task to json without
    # the due key/value pair
    except:
        data["tasks"].append({
            "id": idCounter,
            "task": n
        })
    idCounter += 1
    data["settings"][0]["idCounter"] = idCounter
    updateMsg = "[+] Added new task to list!"
    with open(targetFile, "w") as outfile:
        json.dump(data, outfile)
    taskList(targetFile)


# remove item from JSON file
def jsonRemove(n):
    global updateMsg
    # we need to make sure that we're dealing with a number
    try:
        check = int(n)
        for i in range(len(data["tasks"])):
            if data["tasks"][i]["id"] == check:
                data["tasks"].pop(i)
                with open (targetFile, "w") as outfile:
                    json.dump(data, outfile)
                updateMsg = "[-] Removed task id " + n
                break
            else:
                updateMsg = "[!] Unable to find task id " + n
    except ValueError:
        updateMsg = "[!] Please use the id of the task"
    taskList(targetFile)


# read JSON file into memory and print to stdout as sorted groups
def jsonRead(content):
    global data
    global idCounter
    global updateMsg
    group = {}
    gkey = ""
    gval = ""
    glvl = 0
    with open(content) as objects:
        data = json.load(objects)
    if idCounter <= 1:
        idCounter = data["settings"][0]["idCounter"]
    # let's get things sorted
    for o in data["tasks"]:
        # try if it's possible to grab the due key and assign o to a group
        try:
            days = int(o["due"]) - timeGrab()
            days = days/24/60/60+1
            if days < 0:
                gid = 1
                gkey = "overdue"
                gval = "Expired"
                glvl = 3
            elif days < 1:
                gid = 3
                gkey = "today"
                gval = "Due today"
                glvl = 1
            elif days < 2:
                gid = 4
                gkey = "tomorrow"
                gval = "Due tomorrow"
                glvl = 1
            else:
                gid = 5
                gkey = str(int(days))
                gval = "Due in " + gkey + " days"
                glvl = 3  
        # if there's no timestamp to use, put o into the "whenever" group
        except:
            gid = 2
            gkey = "whenever"
            gval = "Whenever you feel like it"
            glvl = 2
        # create groups dynamically based on the existence of keys
        if gkey not in group:
            group[gkey] = []
            group[gkey].append({
                "gid": gid,
                "due": gval,
                "lvl": glvl,
                "item": []
            })
        # add tasks to their group keys
        group[gkey][0]["item"].append(str(o["id"]) + ": " + str(o["task"]))
    # and finally print everything to the terminal
    for (k, v) in group.items():
        for o in v:
            print(o["due"])
            for t in o["item"]:
                print(t)
            print("")

# display JSON content as task list 
def taskList(tasks):
    clearScreen()
    jsonRead(tasks)
    stdout.write("\x1b]2;" + appName + "\x07")
    if not updateMsg == "":
        print(updateMsg)
    userInput()


# await user input and add or remove tasks
def userInput():
    global updateMsg
    print("Type ':help' or ':?' for more info")
    choice = input("> ").strip()
    if (choice == ":help") or (choice == ":?"):
        userHelp()
    elif choice == ":reset":
        settingsUpdate(2, "foo")
    elif (choice == ":quit") or (choice == ":exit"):
        byebye
    elif choice.startswith(":d"):
        jsonRemove(choice[2:].strip())
    elif choice.startswith(":lvl"):
        settingsUpdate(1, choice[4:5])
    elif choice == "":
        updateMsg = "[?] Not sure what to do"
        taskList(targetFile)
    else:
        jsonWrite(choice)


# update user settings
def settingsUpdate(m, n):
    global updateMsg
    if m == 1:
        # change items shown depending on view level
        updateMsg = "[+] View level at " + n
    elif m == 2:
        # grab the last used id inside the JSON
        # and set counter to that +1
        updateMsg = "[+] Counter reset"
    taskList(targetFile)


# short help print
def userHelp():
    clearScreen()
    print("""
   I8                         ,dPYb,    
   I8                         IP'`Yb    
88888888                      I8  8I    
   I8                         I8  8bgg, 
   I8     ,gggg,gg    ,g,     I8 dP" "8 
   I8    dP"  "Y8I   ,8'8,    I8d8bggP" 
  ,I8,  i8'    ,8I  ,8'  Yb   I8P' "Yb, 
 ,d88b,,d8,   ,d8b,,8'_   8) ,d8    `Yb,
 8P""Y8P"Y8888P"`Y8P' "YY8P8P88P      Y8
    """)
    print("A todo list application\n")
    print("Task allows you to quickly create to-do lists by typing them without any additional frizz. Write anything into the input field and see it added as a new item.")
    print("Task understands you. By using a natural suffix like 'in 3 days', Task will automatically create a timestamp and sort the added task according to it's due date.")
    print("Once a task is finished, you can use it's id and delete it by typing ':d id' where 'id' would be the number displayed with the task.")
    print("""\nAvailable commands are:
        
        :d(id)        - Remove a task by ID
        :help, :?     - View this screen
        :quit, :exit  - exit the application""")
    input("\nPress return to go back...")
    taskList(targetFile)


# clear screen buffer
def clearScreen():
    os.system("cls" if os.name == "nt" else "clear")


# execute program
jsonCheck()
