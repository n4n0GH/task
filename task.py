#!/usr/bin/env python

# import modules
import os
import re
import json
import time
from sys import stdout
from sys import exit as byebye

# global variables for reuse
appName = "Task"
dirName = "hello-task"
homeDir = os.path.expanduser("~")
targetDir = homeDir + "/.local/share/" + dirName
targetFile = targetDir + "/tasks.json"
data = {}
data["tasks"] = []
data["settings"] = []
updateMsg = ""
idCounter = 1
unixDay = 86400


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
        dueTime = re.search(r'in\s+(.+?)\s+day(s\b|\b)', n, re.M|re.I)
        dueTemp = re.search(r'(\d+)', dueTime.group(), re.M|re.I)
        task = n[:-(len(dueTime.group())+1)]
        data["tasks"].append({
            "id": idCounter,
            "task": task,
            # we need to reduce the due time by one second to prevent
            # the timer showing a wrong due date after creation
            "due": timeGrab()+(int(dueTemp.group())*unixDay-1)
        })
    except:
        task = n
        data["tasks"].append({
            "id": idCounter,
            "task": task
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


# read JSON file into memory
def jsonRead(content):
    global data
    global idCounter
    global updateMsg
    with open(content) as objects:
        data = json.load(objects)
    if idCounter <= 1:
        idCounter = data["settings"][0]["idCounter"]
    for o in data["tasks"]:
        print(("[" + str(o["id"]) + "] " + o["task"]))
        try:
            days = int(o["due"]) - timeGrab()
            days = days/24/60/60+1
            if days < 0:
                print("Overdue\n")
            elif days < 1:
                print("Due today\n")
            elif days < 2:
                print("Due in 1 day\n")
            else:
                print(("Due in " + str(int(days)) + " days\n"))
        except:
            print("Whenever you feel like it\n")


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
    print("Type 'help' or '?' for more info")
    choice = input("> ").strip()
    if (choice.lower() == "help") or (choice == "?"):
        userHelp()
    elif (choice.lower() == "quit") or (choice.lower() == "exit"):
        byebye
    elif choice.startswith(":d"):
        jsonRemove(choice[2:].strip())
    elif choice.startswith(":lvl"):
        settingsUpdate(choice[4:5])
    elif choice == "":
        updateMsg = "[?] Not sure what to do"
        taskList(targetFile)
    else:
        jsonWrite(choice)


# update user settings
def settingsUpdate(n):
    global updateMsg
    updateMsg = "[+] View level at " + n
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
        
        :d(id)    - Remove a task by ID
        help/?    - View this screen
        quit/exit - exit the application""")
    input("\nPress return to go back...")
    taskList(targetFile)


# clear screen buffer
def clearScreen():
    os.system("cls" if os.name == "nt" else "clear")


# execute program
jsonCheck()
