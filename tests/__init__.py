import json 
from pathlib import Path
FIXTURE_DIR_PATH = Path(__file__).parent.joinpath("fixtures")
FILES_TEST_PATH = Path(__file__).parent.joinpath("files")

def load_fixture(filename):
    with FIXTURE_DIR_PATH.joinpath(filename).open("r") as f:
        return json.load(f)
    
def load_files(filename):
    with FIXTURE_DIR_PATH.joinpath(filename).open("r") as f:
        return f


def get_fixture_path(filename):
    return FIXTURE_DIR_PATH.joinpath(filename)

def get_test_file(filename):
    with open(FILES_TEST_PATH.joinpath(filename),"rb") as f:
        return f


def get_test_file_path(filename):
    return FILES_TEST_PATH.joinpath(filename)