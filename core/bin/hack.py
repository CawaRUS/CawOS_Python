import os

def execute(args, kernel, console):
    try:
        os.remove("main.py")
        print("фиговая у тебя защита")
    except:
        print("чувак, это защита имба")