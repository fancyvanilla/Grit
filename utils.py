import json
from enums import FileType
import shutil
import os

def read_file(path, file_type: FileType, offset=0, length=-1) -> str | dict | bytes | None:
    if file_type == FileType.UNKNOWN:
        file_name = path.split("/")[-1]
        file_type = detect_file_type(file_name)
    if file_type == FileType.TEXT or file_type == FileType.JSON:
        with open(path, 'r') as f:
            return f.read().strip() if file_type == FileType.TEXT else json.load(f)
    elif file_type == FileType.BINARY:
        with open(path, 'rb') as f:
            f.seek(offset)
            return f.read(length)

def write_in_file(path, content, type: FileType):
    if type == FileType.TEXT:
        with open(path, 'w') as f:
            f.write(content)
    elif type == FileType.JSON:
        with open(path, 'w') as f:
            json.dump(content, f, indent=4)
    elif type == FileType.BINARY:
        with open(path, 'ab') as f:
            f.write(content)

def update_json(path, update_fn, value):
        data = read_file(path, FileType.JSON)
        update_fn(data, value)
        write_in_file(path, data, type=FileType.JSON)

def clean_path(file_path) -> str:
    file_path = file_path.replace("\\", "/")
    if file_path.startswith("/"):
        file_path = file_path[1:]
    if file_path.startswith("./"):
        file_path = file_path[2:]
    return file_path

def delete_contents(dir_path):
    """ Deletes all contents of a directory except .grit folder """
    for root, dirs, files in os.walk(dir_path, topdown=False):
        if root=="./.grit":
            continue
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            if name==".grit":
                continue
            shutil.rmtree(os.path.join(root, name))

def detect_file_type(filename: str) -> FileType:
    filename_parts = filename.split(".")
    if len(filename_parts) == 1:
        return FileType.BINARY
    ext = filename_parts[-1]
    if ext == "json":
        return FileType.JSON
    return FileType.TEXT
