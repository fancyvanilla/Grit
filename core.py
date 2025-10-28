import datetime
import os
import zlib
import json
import hashlib
import copy
import difflib
from utils import clean_path, detect_file_type, read_file, write_in_file, delete_contents, update_json
from enums import GritFileType, FileType
from typing import Tuple

class GritRepository:
    
    GRIT_DIR_NAME = ".grit"
    DEFAULT_BRANCH = "main"

    """ Class methods for file paths """
    @classmethod
    def grit_dir(cls, repo) -> str:
        if repo is None:
            repo = os.getcwd()
        return os.path.join(repo, cls.GRIT_DIR_NAME)

    @classmethod
    def objects_tree_path(cls, repo=None) -> str:
        return os.path.join(cls.grit_dir(repo), "objects_tree.json")
    @classmethod
    def objects_path(cls, repo=None) -> str:
        return os.path.join(cls.grit_dir(repo), "objects")

    @classmethod
    def index_table_path(cls, repo=None) -> str:
        return os.path.join(cls.grit_dir(repo), "index_table.json")

    @classmethod
    def commit_tree_path(cls, repo=None) -> str:
        return os.path.join(cls.grit_dir(repo), "commit_tree.json")

    @classmethod
    def head_path(cls, repo=None) -> str:
        return os.path.join(cls.grit_dir(repo), "HEAD.txt")

    @classmethod
    def gritignore_path(cls, repo=None) -> str:
        return os.path.join(os.getcwd(), ".gritignore")
    
    @classmethod
    def branches_path(cls, repo=None) -> str:
        return os.path.join(cls.grit_dir(repo), "branches.json")
    
    @classmethod
    def current_branch_path(cls, repo=None) -> str:
        return os.path.join(cls.grit_dir(repo), "current_branch.txt")
    
    @classmethod
    def load_current_branch(cls) -> str:
        return read_file(cls.current_branch_path(), FileType.TEXT)
    
    @classmethod
    def load_head(cls) -> str:
        return read_file(cls.head_path(), FileType.TEXT)
    
    @classmethod
    def set_head(cls, head_value: str):
        write_in_file(cls.head_path(), head_value, type=FileType.TEXT)

    """ Class methods for Grit repository operations """
    @classmethod
    def init(cls, repo_path):
        if not os.path.exists(repo_path):
            print(f"[Error] Path does not exist: {repo_path}")
            return
        grit_dir_path = clean_path(os.path.join(repo_path, cls.GRIT_DIR_NAME))
        if os.path.exists(grit_dir_path):
            print("A Grit repository exists in the specified path. This will override the current repository.")
        else:
            os.makedirs(grit_dir_path, exist_ok=True)
        files = [ GritFileType.OBJECTS_TREE, GritFileType.HEAD, GritFileType.INDEX_TABLE, GritFileType.COMMIT_TREE, GritFileType.OBJECTS, GritFileType.BRANCHES, GritFileType.CURRENT_BRANCH ]
        for file_type in files:
            cls._initialize_file(file_type, repo_path)
        print(f"Initialized empty Grit repository at {repo_path}")

    @classmethod
    def add(cls, path):
        path=cls.validate_path(path)
        if path is None:
            return
        cls.add_dir_to_staged_area(path)
        cls.detect_removes()

    @classmethod
    def commit(cls, message):
        commit_id, new_commit = cls.generate_commit(message)
        commits_tree=read_file(cls.commit_tree_path(), FileType.JSON)
        head=cls.load_head()
        if head:
            previous_commit = commits_tree["commits"][head]
            files_changed, _ = cls.diff(previous_commit["objects_tree"]["tree"], new_commit["objects_tree"]["tree"])
            if len(files_changed) > 0:
                print(f"{len(files_changed)} files changed")
                for change in files_changed:
                    print(f" - {change}")
            else:
                print("No changes to commit.")
                return
            
        commits_tree["commits"][commit_id] = new_commit
        write_in_file(cls.commit_tree_path(), commits_tree, FileType.JSON)
        cls.set_head(commit_id)

        def update_branch(branches, commit_id):
            branches["branches"][cls.load_current_branch()] = commit_id
        update_json(cls.branches_path(), update_branch, commit_id)
   
    @classmethod
    def branch(cls, branch_name=None):
        if branch_name is None or branch_name.strip() == "":
            cls.list_branches()
        commits = read_file(cls.commit_tree_path(), FileType.JSON)
        branch_commit = list(commits["commits"].keys())[-1] if commits["commits"] else None

        def branch_updater(branches, value):
            if branch_name in branches["branches"]:
                print(f"Branch {branch_name} already exists.")
                return
            branches["branches"][branch_name] = value

        update_json(cls.branches_path(), branch_updater, branch_commit)
    
    @classmethod
    def log(cls):
        head = cls.load_head()
        commit_tree = read_file(cls.commit_tree_path(), FileType.JSON)
        if len(commit_tree["commits"]) == 0:
            print("No commits found.")
        for commit in commit_tree["commits"]:
            if head == commit:
                print(f"commit: {commit} (HEAD)")
            else:
                print(f"commit: {commit}")
            print(f"Date: {commit_tree['commits'][commit]['timestamp']}")
            print(f"      {commit_tree['commits'][commit]['message']}\n")

    @classmethod
    def checkout_commit(cls, commit_id):
        delete_contents("./")
        commits = read_file(cls.commit_tree_path(), FileType.JSON)
        if commit_id not in commits["commits"]:
            print(f"Commit {commit_id} not found.")
            return
        objects_tree = commits["commits"][commit_id]["objects_tree"]
        GritRepository._check_out(objects_tree["tree"], "./")
        cls.set_head(commit_id)
    
    @classmethod
    def checkout(cls, branch_name):
        """Checkout a specific branch by its name or commit ID"""
        branches = read_file(cls.branches_path(), FileType.JSON)
        if branch_name not in branches["branches"]:
            cls.checkout_commit(branch_name)
        else:
            commit_id = branches["branches"][branch_name]
            cls.checkout_commit(commit_id)
            write_in_file(cls.current_branch_path(), branch_name, type=FileType.TEXT)

    @classmethod
    def list_branches(cls):
        branches = read_file(cls.branches_path(), FileType.JSON)
        current_branch = cls.load_current_branch()
        for branch in branches["branches"]:
            if branch == current_branch:
                print(f"* {branch}")
            else:
                print(f"  {branch}")
    @classmethod
    def read_from_key(cls, key, file_type: FileType=FileType.TEXT):
        """ Read content from objects based on the blob key """
        objects = read_file(cls.index_table_path(), FileType.JSON)
        for obj in objects['objects']:
            if obj['hash'] == key:
                offset = obj['offset']
                length = obj['length']
                content = read_file(cls.objects_path(), FileType.BINARY, offset, length)
                return cls.decompress_content(content, file_type)

    """ Grit helper methods """
    
    @classmethod
    def _initialize_file(cls, file_type: GritFileType, repo_path: str):
        """Initialize a file of given GritFileType with default content"""
        paths = {
            GritFileType.OBJECTS_TREE: clean_path(cls.objects_tree_path(repo_path)),
            GritFileType.HEAD: clean_path(cls.head_path(repo_path)),
            GritFileType.INDEX_TABLE: clean_path(cls.index_table_path(repo_path)),
            GritFileType.COMMIT_TREE: clean_path(cls.commit_tree_path(repo_path)),
            GritFileType.OBJECTS: clean_path(cls.objects_path(repo_path)),
            GritFileType.BRANCHES: clean_path(cls.branches_path(repo_path)),
            GritFileType.CURRENT_BRANCH: clean_path(cls.current_branch_path(repo_path))
        }
        default_contents = {
            GritFileType.OBJECTS_TREE: {"tree": {}},
            GritFileType.HEAD: "",
            GritFileType.INDEX_TABLE: {"objects": []},
            GritFileType.COMMIT_TREE: {"commits": {}},
            GritFileType.OBJECTS: b"",
            GritFileType.BRANCHES: {
                "branches": {
                    cls.DEFAULT_BRANCH: None
                }},
            GritFileType.CURRENT_BRANCH: cls.DEFAULT_BRANCH
        }
        if file_type == GritFileType.OBJECTS:
            mode = FileType.BINARY
        elif file_type == GritFileType.HEAD or file_type == GritFileType.CURRENT_BRANCH:
            mode = FileType.TEXT
        else:
            mode = FileType.JSON
        write_in_file(paths[file_type], default_contents[file_type], mode)

    @classmethod
    def diff(cls, commit1, commit2):
        files_changed = []
        files_diff = {}
        GritRepository.compare_commits(
            commit1,
            commit2,
            files_changed,
            files_diff
        )
        return files_changed, files_diff

    @classmethod
    def get_blob_key(cls, file_path):
        if not os.path.exists(file_path):
            print(f"File does not exist at {file_path}.")
            return None
        objects_tree = read_file(cls.objects_tree_path(), FileType.JSON)
        file_path = clean_path(file_path)
        file_path_parts = file_path.split("/")
        current_level = objects_tree['tree']
        idx = 0
        while idx < len(file_path_parts):
            if file_path_parts[idx] in current_level:
                if current_level[file_path_parts[idx]].get("tree", -1) == -1:
                    return current_level[file_path_parts[idx]]
                current_level = current_level[file_path_parts[idx]]['tree']
                idx += 1
            else:
                return None
        return None
    
    @classmethod
    def update_objects_tree(cls, path, blob_key):
        objects_tree = read_file(cls.objects_tree_path(), FileType.JSON)
        path = clean_path(path)
        path_parts = path.split("/")
        current_level = objects_tree['tree']
        GritRepository._update_objects_tree(current_level, path_parts, 0, blob_key)
        return objects_tree
    
    @staticmethod
    def _update_objects_tree(current_level, path_parts, idx, blob_key):
        if idx >= len(path_parts):
            return
        if idx == len(path_parts) - 1: # file level
            current_level[path_parts[idx]] = {"blob_key": blob_key}
        else:
            if path_parts[idx] not in current_level: # folder level that does not exist
                current_level[path_parts[idx]] = {"tree": {}}
            current_level = current_level[path_parts[idx]]['tree']
            return GritRepository._update_objects_tree(current_level, path_parts, idx + 1, blob_key)

    # IMPROVEMENT: if the objects size is large, this will become REALLY slow. 
    # We can save the size in a separate file and increment it in each write.
    @classmethod
    def update_index_table(cls, blob_key, compressed_content):
        object_length = len(compressed_content)
        content = read_file(cls.objects_path(), FileType.BINARY)
        offset = len(content)
        objects = read_file(cls.index_table_path(), FileType.JSON)
        objects['objects'].append({
                "hash": blob_key,
                "offset": offset,
                "length": object_length
            })
        write_in_file(cls.index_table_path(),objects,FileType.JSON)
       
    @classmethod
    def create_blob(cls, file_path):
        compressed_content = cls.compress_file(file_path)
        blob_key = hashlib.sha1(compressed_content).hexdigest()
        current_file_tree = cls.get_blob_key(file_path)
        if (current_file_tree is not None and current_file_tree.get("blob_key") == blob_key):
            print(f"No changes detected for file {file_path}")
        else:
            new_objects_tree = cls.update_objects_tree(file_path, blob_key)
            write_in_file(cls.objects_tree_path(), new_objects_tree, type=FileType.JSON)
            cls.update_index_table(blob_key, compressed_content)
            write_in_file(cls.objects_path(), compressed_content, type=FileType.BINARY)
            print(f"Detected changes for file {file_path}.")
        
    @classmethod
    def detect_removes(cls):
        with open(cls.objects_tree_path(), 'r+') as f:
            objects_tree = json.load(f)
            new_objects_tree = copy.deepcopy(objects_tree)
            cls._detect_remove(objects_tree['tree'], "./", new_objects_tree['tree'])
            f.seek(0)
            json.dump(new_objects_tree, f, indent=4)
            f.truncate()

    @staticmethod
    def _detect_remove(level, path, new_objects_tree):
        for item in list(level.keys()):
            current_path = os.path.join(path, item).replace("\\", "/")
            if not os.path.exists(current_path):
                print(f"Detected removal of: {current_path}")
                del new_objects_tree[item]
            elif level[item].get("tree", -1) != -1:
                GritRepository._detect_remove(level[item]["tree"], current_path, new_objects_tree[item]["tree"])

    @classmethod
    def compare_commits(cls, commit1, commit2, files_changed, files_diff, path=""):
        for item in commit1.keys():
            current_path = os.path.join(path, item)
            if item not in commit2:
                if "tree" in commit1[item]:
                    cls._mark_all_as_changed(commit1[item]["tree"], files_changed, current_path)
                else:
                    files_changed.append(current_path)
            else:
                cls._compare_commit_items(commit1[item], commit2[item], files_changed, files_diff, current_path)
        for item in commit2.keys():
            current_path = os.path.join(path, item)
            if item not in commit1:
                files_changed.append(current_path)
                if "tree" in commit2[item]:
                    cls._mark_all_as_changed(commit2[item]["tree"], files_changed, current_path)

    @classmethod
    def _mark_all_as_changed(cls, tree, files_changed, path):
        for item in tree:
            current_path = os.path.join(path, item)
            if "tree" in tree[item]:
                cls._mark_all_as_changed(tree[item]["tree"], files_changed, current_path)
            else:
              files_changed.append(current_path)


    @classmethod
    def _compare_commit_items(cls, item1, item2, files_changed, files_diff, current_path):
        if "blob_key" in item1 and "blob_key" in item2:
            if item1.get("blob_key") != item2.get("blob_key"):
                file1_content = cls.read_from_key(item1["blob_key"], detect_file_type(current_path.split("/")[-1]))
                file2_content = cls.read_from_key(item2["blob_key"], detect_file_type(current_path.split("/")[-1]))
                diff = difflib.unified_diff(
                    file1_content.splitlines(),
                    file2_content.splitlines(),
                    fromfile=current_path,
                    tofile=current_path
                )
                files_diff[current_path] = "\n".join(list(diff))
                files_changed.append(current_path)
        elif "tree" in item1 and "tree" in item2:
            cls.compare_commits(item1["tree"], item2["tree"], files_changed, files_diff, current_path)

    @classmethod
    def _check_out(cls, level, path):
        for item in level:
            if level[item].get("blob_key", -1) != -1:  # item is a file
                file_type=detect_file_type(item)
                content = cls.read_from_key(level[item]["blob_key"], file_type)
                if content is not None:
                    write_in_file(os.path.join(path, item).replace("\\", "/"), content, file_type)
            else:
                current_path = os.path.join(path, item).replace("\\", "/")  # item is a dir
                if not os.path.exists(current_path):
                    os.makedirs(current_path)
                cls._check_out(level[item]["tree"], current_path)

    @staticmethod
    def validate_path(path: str) -> str | None:
        path = clean_path(path)
        if not os.path.exists(path):
            print(f"[Error] Path does not exist: {path}")
            return None
        return path

    @staticmethod
    def generate_commit_id(message: str) -> str:
        return hashlib.sha1((message + str(datetime.datetime.now())).encode('utf-8')).hexdigest()

    @classmethod
    def get_ignored_files_and_folders(cls) -> Tuple[list[str], list[str]]:
        """Return list of files and folders to ignore from .gritignore"""
        files_to_ignore = []
        folders_to_ignore = []
        if os.path.exists(cls.gritignore_path()):
            ignored = read_file(cls.gritignore_path(), FileType.TEXT)
            for line in ignored.splitlines():
                if line.strip() and not line.startswith('#'):
                    if line.endswith('/'):
                        folders_to_ignore.append(line.strip()[:-1])
                    else:
                        files_to_ignore.append(line.strip())
        return (files_to_ignore, folders_to_ignore)

    @classmethod
    def add_dir_to_staged_area(cls, dir_path: str):
        files_to_ignore, folders_to_ignore = cls.get_ignored_files_and_folders()
        for root, _, files in os.walk(dir_path):
            root = root.replace("\\", "/")
            root = clean_path(root)
            if any(root.startswith(folder) for folder in folders_to_ignore):
                continue
            # Skip empty directories
            if len(files) == 0:
                continue
            for file in files:
                file_path = clean_path(os.path.join(root, file))
                # Skip ignored files
                if file_path in files_to_ignore:
                    continue
                cls.create_blob(file_path)

    @staticmethod
    def is_current_grit_repo() -> bool:
        grit_path = os.path.join(os.getcwd(), GritRepository.GRIT_DIR_NAME)
        return os.path.exists(grit_path) and os.path.isdir(grit_path)
    
    @classmethod
    def generate_commit(cls, message):
        objects_tree = read_file(cls.objects_tree_path(), FileType.JSON)
        commit_id = cls.generate_commit_id(message)
        new_commit = {
            "previous_hash": cls.load_head(),
            "message": message,
            "timestamp": datetime.datetime.now().isoformat(),
            "objects_tree": objects_tree,
        }
        return commit_id, new_commit
    
    @staticmethod
    def compress_file(file_path):
        content = read_file(file_path, FileType.UNKNOWN)
        if isinstance(content, bytes):
            return content
        if isinstance(content, dict):
            content = json.dumps(content)
        content = content.encode("utf-8")
        return zlib.compress(content)
    
    @staticmethod
    def decompress_content(compressed_content, file_type: FileType):
        if file_type == FileType.BINARY:
            return compressed_content
        decompressed = zlib.decompress(compressed_content).decode('utf-8')
        if file_type == FileType.JSON:
            return json.loads(decompressed)
        return decompressed