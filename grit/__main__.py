import typer
from grit.core import GritRepository
from grit.config import hide_grit

def pre_check(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        print("Welcome to Grit! Use `grit --help` to see available commands.")
        raise typer.Exit()

app = typer.Typer(callback=pre_check, invoke_without_command=True, help="Grit: A simple version control system made with ❤️")

def repo_required(fn):
    def wrapper(*args, **kwargs):
        if not GritRepository.is_current_grit_repo():
            print("Not a Grit repository. Run 'grit init' first.")
            raise typer.Exit(code=1)
        return fn(*args, **kwargs)
    return wrapper

@app.command()
def init(path: str = typer.Argument("./", help="Path to initialize repository")):
    """Initialize a new Grit repository."""
    GritRepository.init(path)
    hide_grit()

@repo_required
@app.command()
def add(
    paths: list[str] = typer.Argument(None, help="Files or directories to add"),
    lines: str = typer.Option(
        None, "--lines", help="Line range in the format start-end (1-based) to add from a single file"
    ),
):
    """Add files or directories to the staging area."""
    if not paths:
        paths = ["./"]
    if lines:
        if len(paths) != 1:
            print("When --lines is provided, provide exactly one file path.")
            raise typer.Exit(code=1)
        try:
            line_start, line_end = map(int, lines.split("-"))
            GritRepository.add_file_section(paths[0], line_start, line_end)
        except ValueError as e:
            print(str(e))
            raise typer.Exit(code=1)
        #improve error handling the Exception is too general
        # except Exception:
        #     print("Invalid line range format. Use start-end (e.g., 5-10).")
        #     raise typer.Exit(code=1)
        return
    for p in paths:
        GritRepository.add(p)

@repo_required
@app.command()
def commit(message: str = typer.Option(..., "-m", "--message", help="Commit message")):
    """Commit staged changes with a message."""
    GritRepository.commit(message)

@repo_required
@app.command()
def log():
    """Show commit history."""
    GritRepository.log()

@repo_required
@app.command()
def cat_file(
    p: str = typer.Option(..., "-p", help="Key to show content for")
):
    """Show content for a given key."""
    content = GritRepository.read_from_key(p)
    if content is not None:
        print(content)
    else:
        print(f"No content found for {p}")

@repo_required
@app.command()
def diff(commit1: str, commit2: str):
    """Show differences between two commits."""
    try:
      files, files_diff = GritRepository.diff(commit1, commit2)
      print("Files changed:")
      for file in files:
        print("*", file)
      print("\nDifferences:")
      if files_diff:
        for file, content in files_diff.items():
            print(f"* {file}:\n{content}\n")
      else:
        print("No differences found.")
    except ValueError as e:
        print(str(e))
        raise typer.Exit(code=1)
    
@repo_required
@app.command()
def branch(branch_name: str = typer.Argument(None, help="List the branches or create a new branch if branch name is provided")):
    """List branches or create a new branch."""
    if branch_name:
        GritRepository.branch(branch_name)
    else:
        GritRepository.list_branches()

@repo_required
@app.command()
def checkout(branch_name: str = typer.Argument(..., help="Branch name to checkout or commit ID")):
    """Checkout a branch or commit."""
    GritRepository.checkout(branch_name)

def main():
    app()

if __name__ == "__main__":
    main()