# Grit

**Grit** is a minimal Python implementation of Git. It is a simple version control system that allows users to track changes in files and directories.

Grit provides basic functionalities such as:

- Initializing a repository
- Adding files and sections of files
- Committing changes
- Viewing logs
- Viewing content based on a blob key
- Showing the difference between two commits
- Checking out commits or branches

## Build & Install

1. In the root of the repo, build a distribution:

```bash
python -m build
```

2. Then, you can install it locally using the .whl file:
```bash
pip install dist/grit-0.1.0-py3-none-any.whl
```

3. You can now run the CLI with:
```bash
grit --help
````

## Next Steps

- Handle merging branches
- Improve error handling and user feedback
- Implement remote repository support (push, pull, clone)

For anyone looking to collaborate, feel free to contribute to any of the above areas or suggest new features!

