from enum import Enum

class GritFileType(Enum):
    OBJECTS_TREE = "objects_tree"
    HEAD = "head"
    INDEX_TABLE = "index_table"
    COMMIT_TREE = "commit_tree"
    OBJECTS = "objects"
    BRANCHES = "branches"
    CURRENT_BRANCH = "current_branch"

class FileType(Enum):
    TEXT = "text"
    JSON = "json"
    BINARY = "binary"
    UNKNOWN = "unknown"