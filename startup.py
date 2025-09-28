import os
import sys
def normalize_directory():
    # this cursedass code makes sure the main program knows where it's looking lol
    caller_path = sys._getframe(1).f_globals['__file__']
    os.chdir(os.path.dirname(os.path.abspath(caller_path)))

def check_dirs():
    for i in range(9):
        dirname = f"level{i}"
        assert os.path.isdir(dirname), f"Directory '{dirname}' not found in {os.getcwd()}. Did you forget to unzip colored.zip?"

def print_art():
    with open("art.txt") as f:
        print(f.read())

def startup_procedure():
    normalize_directory()
    check_dirs()
    print_art()