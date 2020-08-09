#!/usr/bin/env python

# import modules
import os
import re
import json
import time
import argparse
import readline
from sys import stdout
from sys import exit as byebye


#set up terminal help text and argparse
parser = argparse.ArgumentParser(description="""
                                 Task is a todo list application that allows you
                                 to quickly create task lists by typing them
                                 without any additional frizz. Write anything
                                 into the input field and see it added as a new
                                 item on your list.\n
                                 Task understands you. By using a natural suffix
                                 like 'in 3 days' it will automatically create a
                                 timestamp and sort the added task according to
                                 it's due date.\n
                                 Once a task is finished, you can use it's id
                                 and delete it by typing ':d id' where 'id' is
                                 the number displayed with the task.\n
                                 """)
parser.add_argument("-f", "--file",
                    help="specify an alternative filename to use as default",
                    metavar="(NAME)")
args = parser.parse_args()


# global variables for reuse
if args.file:                                       # Enables user to select a
    fileName = args.file + ".json"                  # different file to store
else:                                               # the tasks in
    fileName = "tasks.json"
appName = "Task"                                    # Name of the application
dirName = "hello-task"                              # Directory name
homeDir = os.path.expanduser("~")                   # Use user's home as base
targetDir = homeDir + "/.local/share/" + dirName    # Determine target directory
targetFile = targetDir + "/" + fileName             # Construct full path
data = {}                                           # JSON written to file
data["tasks"] = []
data["settings"] = []
message = ""                                        # Feedback messages
idCounter = 1                                       # Used to generate task id
unixDay = 86400                                     # Used to generate timestamp

# set up classes for easier color coding
class color:
    black = "\033[30m"          # used when also supplying a background
    red = "\033[31m"            # used for urgent or deletion
    green = "\033[32m"          # used for additions or confirmations
    yellow = "\033[33m"         # used for program questions and semi-urgent
    orange = "\033[214m"        # used to highlight projects
    purple = "\033[128m"        # used to highlight contexts
    white = "\033[37m"          # used when also supplying a background
    reset = "\033[0m"           # resets all color, reverts to default printing


class bgcolor:
    black = "\033[40m"
    red = "\033[41m"


class style:
    bold = "\033[1m"
    underline = "\033[4m"
    reverse = "\033[7m"


def strike(text):
    return "\u0336".join(text) + "\u0336"


# function is used by read and write functions
def timeGrab():
    return int(time.time())


# clear screen buffer
def clearScreen():
    os.system("cls" if os.name == "nt" else "clear")


# fancy lines
def titleLine(message, seperator):
    return print(message.center(int(size[1]), seperator))


# update feedback messages
def updateMsg(msgBody, msgType):
    global message
    hint = [color.yellow + " [!] ",
            color.yellow + " [?] ",
            color.red + " [×] ",
            color.green + " [+] ",
            color.green + " [✓] "]
    message = hint[msgType] + msgBody + " "


# set different mode
def mode(m):
    modes = [color.white + " NORMAL ",
             color.yellow + " HELP ",
             color.red + " DELETION "]
    return modes[m]


# render the modeline
def modeline(v):
    # TODO make reflow work on terminals that support reflow by resize
    size = os.popen('stty size', 'r').read().split()
    escLength = 15
    left = mode(v) + color.white + " "
    right = " #" + str(idCounter-1) + " ~" +\
            str(data["settings"][0]["lvl"]) + " " + message
    # calculate padding and account for escape sequence color codes
    padding = int(size[1]) - len(left) - len(right) + escLength
    output = left + " " * padding + right
    if (len(output) - escLength) > int(size[1]):
        overflow = len(output) - escLength - int(size[1]) + 4
        return print(style.reverse + output[:-overflow] + "... " + color.reset)
    else:
        return print(style.reverse + output + color.reset)


# render filename above task list
def fileline():
    global fileName
    size = os.popen('stty size', 'r').read().split()
    padding = int(size[1]) - len(fileName)
    print(style.reverse + " " + fileName + " " * (padding - 1) + color.reset + "\n")


# check if JSON exists, execute creation if not
def jsonCheck():
    try:
        f = open(targetFile)
        updateMsg("File loaded", 4)
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
    updateMsg("New file storage created", 4)
    taskList(targetFile)


# write new content to JSON file
def jsonWrite(n):
    global data
    global idCounter
    # it's important to 'try' otherwise entries that don't end in
    # the search string will cause massive errors
    try:
        context = re.findall(r'\B@\w+', n)
    except:
        context = ""
    try:
        project = re.findall(r'\B\+\w+', n)
    except:
        project = ""
    try:
        dueTime = re.search(r'(in\s+(\d+?)\s+day(s\b|\b))$', n, re.M|re.I)
        dueTemp = re.search(r'(\d+)', dueTime.group(), re.M|re.I)
        task = n[:-(len(dueTime.group())+1)]
        data["tasks"].append({
            "id": idCounter,
            "task": task,
            # we need to reduce the due time by one second to prevent
            # the timer showing a wrong due date right after creation
            "due": timeGrab()+(int(dueTemp.group())*unixDay-1),
            "done": "false",
            "context": context,
            "project": project
        })
    # if there's no due date supplied, write the task to json without
    # the due key/value pair
    except:
        data["tasks"].append({
            "id": idCounter,
            "task": n,
            "done": "false",
            "context": context,
            "project": project
        })
    idCounter += 1
    data["settings"][0]["idCounter"] = idCounter
    updateMsg("New task added", 3)
    with open(targetFile, "w") as outfile:
        json.dump(data, outfile)
    taskList(targetFile)


# remove item from JSON file
def jsonRemove(n):
    global idCounter
    massRemove = n.split()
    for j in range(len(massRemove)):
        try:
            check = int(massRemove[j])
            for i in range(len(data["tasks"])):
                if data["tasks"][i]["id"] == check:
                    if data["tasks"][i]["done"] == "false":
                        updateMsg("Unable to remove unfinished tasks", 0)
                        break
                    else:
                        data["tasks"].pop(i)
                        # clean up idCounter to next lowest free id
                        if len(data["tasks"]) >= 1:
                            data["settings"][0]["idCounter"] = data["tasks"][-1]["id"]+1
                            idCounter = data["tasks"][-1]["id"]+1
                        else:
                            data["settings"][0]["idCounter"] = 1
                            idCounter = 1
                        with open(targetFile, "w") as outfile:
                            json.dump(data, outfile)
                        updateMsg("Removed task id " + str(check), 2)
                        break
                else:
                    updateMsg("Unable to find task id " + str(check), 0)
        except ValueError:
            updateMsg("Please use the id of the task", 0)
    taskList(targetFile)


# toggle item's done state instead of directly removing it
def doneToggle(n):
    massToggle = n.split()
    for j in range(len(massToggle)):
        try:
            check = int(massToggle[j])
            for i in range(len(data["tasks"])):
                if data["tasks"][i]["id"] == check:
                    if data["tasks"][i]["done"] == "false":
                        data["tasks"][i]["done"] = "true"
                        updateMsg("Marked task as done", 4)
                    else:
                        data["tasks"][i]["done"] = "false"
                        updateMsg("Marked task as not done", 4)
                    with open(targetFile, "w") as outfile:
                        json.dump(data, outfile)
                    break
                else:
                    updateMsg("Unable to find task id " + str(check), 0)
        except ValueError:
            updateMsg("Please use the id of the task", 0)
    taskList(targetFile)


# read JSON file into memory and print to stdout as sorted groups
def jsonRead(content):
    global data
    global idCounter
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
        # try if it's possible to grab the due value and assign o to a group
        try:
            days = int(o["due"]) - timeGrab()
            days = days/24/60/60+1
            if days < 0:
                gkey = 2
                gval = style.bold + color.red + "Overdue"
                glvl = 3
            elif days < 1:
                gkey = 3
                gval = color.red + "Today"
                glvl = 1
            elif days < 2:
                gkey = 4
                gval = color.yellow + "Tomorrow"
                glvl = 1
            else:
                gkey = int(days + 4)
                gval = "In " + str(int(days)) + " days"
                glvl = 4
        # if there's no timestamp to use, put o into the "whenever" group
        except BaseException:
            gkey = 1
            gval = color.white + "Unscheduled"
            glvl = 2
            pass
        # create groups dynamically based on the existence of keys
        if gkey not in group:
            group[gkey] = [{
                "due": gval,
                "lvl": glvl,
                "item": []
                }]
        # add tasks to their group keys
        if str(o["done"]) == "false":
            taskDescription = str(o["task"])
            doneState = '   '
        else:
            taskDescription = strike(str(o["task"]))
            doneState = color.green + ' ✓ ' + color.reset
        idSpacing = (5 - len(str(o["id"]))) * " "
        group[gkey][0]["item"].append(doneState + str(o["id"]) + idSpacing + taskDescription)
    # and finally print everything to the terminal
    # since the sortKey is useless to us, we're only interested in the dueGroups
    # for the output, we still need to query sortKey to get proper sorting
    for (sortKey, dueGroups) in sorted(group.items()):
        for dueGroup in dueGroups:
            # print only the dueGroup that matches current view level settings
            if dueGroup["lvl"] <= data["settings"][0]["lvl"]:
                print("   " + dueGroup["due"] + color.reset + "\n")
                for task in dueGroup["item"]:
                    print(task)
                print("")


# display JSON content as task list
def taskList(tasks):
    clearScreen()
    fileline()
    jsonRead(tasks)
    stdout.write("\x1b]2;" + appName + "\x07")
    modeline(0)
    userInput()


# await user input and add or remove tasks
def userInput():
    # print("Type ':help' or ':?' for more info")
    choice = input("> ").strip()
    if choice in (":help", ":?", ":h"):
        userHelp()
    elif choice in (":exit", ":quit", ":q", ":e"):
        byebye
    elif choice.startswith(":d"):
        doneToggle(choice[2:].strip())
    elif choice.startswith(":f"):
        foresight(choice[2:].strip())
    elif choice.startswith(":p"):
        jsonRemove(choice[2:].strip())
    # catch user input error to prevent creation of unneccesary tasks
    elif choice.lower() in ("quit", "exit"):
        updateMsg("Did you want to quit?", 1)
        taskList(targetFile)
    elif choice == "":
        updateMsg("Not sure what to do", 1)
        taskList(targetFile)
    else:
        jsonWrite(choice)


# update foresight
def foresight(n):
    global data
    global idCounter
    try:
        lvl = int(n)
        if int(lvl) in range(1, 5):
            data["settings"][0]["lvl"] = int(lvl)
            updateMsg("Foresight set to " + str(lvl), 4)
        else:
            raise
        with open(targetFile, "w") as outfile:
            json.dump(data, outfile)
    except:
        clearScreen()
        fileline()
        print("""
        Change amount of tasks to display

   1    tasks due today and tomorrow
   2    same as 1 plus unscheduled
   3    same as 2 plus overdue
   4    same as 3 plus tasks due days after
""")
        modeline(1)
        foresightSelect = input("> ").strip()
        try:
            select = int(foresightSelect)
            foresight(select)
        except:
            updateMsg("Please select a value between 1-4", 0)
    taskList(targetFile)


# short help print
def userHelp():
    clearScreen()
    fileline()
    print("""
   Available commands are

   :d (id)       Mark a task id as done
   :p (id)       Permanently remove a task
   :f (1-4)      Viewing level of tasks
   :help, :?     View this screen
   :quit, :exit  exit the application
""")
    modeline(1)
    input("> Press return to go back...")
    taskList(targetFile)


# execute program only if not imported as module
if __name__ == "__main__":
    jsonCheck()
