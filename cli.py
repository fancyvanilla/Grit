import typer
from core import GritRepository

def pre_check(ctx: typer.Context):
    if ctx.invoked_subcommand == "init":
        return

    if not GritRepository.is_current_grit_repo():
        print("Not a Grit repository. Run 'grit init' first.")
        raise typer.Exit(code=1)

app = typer.Typer(callback=pre_check, help="Grit: A simple version control system")

@app.command()
def init(path: str = typer.Argument("./", help="Path to initialize repository")):
    GritRepository.init(path)

@app.command()
def add(paths: list[str] = typer.Argument(..., help="Files or directories to add")):
    if not paths:
        paths = ["./"]
    if not GritRepository.is_current_grit_repo():
        print("Not a Grit repository (or any of the parent directories). Please run 'grit init' first.")
        raise typer.Exit(code=1)
    for p in paths:
        GritRepository.add(p)

@app.command()
def commit(message: str = typer.Option(..., "-m", "--message", help="Commit message")):
    GritRepository.commit(message)

@app.command()
def log():
    GritRepository.log()

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

@app.command()
def diff(commit1: str, commit2: str):
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

@app.command()
def branch(branch_name: str = typer.Argument(None, help="List the branches or create a new branch if branch name is provided")):
    if branch_name:
        GritRepository.branch(branch_name)
        print(f"Branch '{branch_name}' created.")
    else:
        GritRepository.list_branches()

@app.command()
def checkout(branch_name: str = typer.Argument(..., help="Branch name to checkout or commit ID")):
    GritRepository.checkout(branch_name)

if __name__ == "__main__":
    app()
