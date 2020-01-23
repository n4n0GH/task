#!/usr/bin/env python

# this is a really hacky way to implement a notification setup for KDE and other
# systems that have notify-send installed. you can set it up via cronjob, or use
# KDE's 'notifications' manager to add a command to be executed whenever the
# screensaver is closed so you get a digest for what you have to work on today

# import system modules
import os
import re
import json
import time
import argparse
import subprocess


# set up terminal help text and argparse
parser = argparse.ArgumentParser(description="""
                                 This is a notification service for task.
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
unixDay = 86400                                     # Used to generate timestamp


def timegrab():
    return int(time.time())


def jsonRead(content):
    idCounter = 1
    group = ""
    with open(content) as objects:
        data = json.load(objects)
    if idCounter <= 1:
        idCounter = data["settings"][0]["idCounter"]
    for item in data["tasks"]:
        try:
            days = int(item["due"]) - timegrab()
            days = int(days/24/60/60+1)
            if days <= 1 and days > 0:
                group = group + "\n" + item["task"]
        except BaseException:
            pass
    if group is not "":
        subprocess.call(['notify-send', "Due Today", group])


jsonRead(targetFile)
