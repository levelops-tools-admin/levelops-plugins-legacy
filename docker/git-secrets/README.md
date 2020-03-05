# Build

    export LGS_VERSION=<git-secrets version e.g. 1.2.0> ; docker build --build-arg branch=${LGS_VERSION} -t levelops/levelops-git-secrets:v${LGS_VERSION} .

# Usage:
    docker run --rm -v path/to/repo:/code levelops/levelops-git-secrets:v0.1 /bin/levelops-git-secrets new current /code

# Options:
* Type of git-secrets installation:
  * new: the repo hasn't been initialized with git-secrets
  * existing: the repo has been initialized with git-secrets
* Type of scans:
  * current: scans only the currently checked out branch.
  * historic: scans the history of the repo, not just the currently checked out branch.

Examples:

    levelops-git-secrets new current <path to repo> 
    levelops-git-secrets new historic <path to repo>
    levelops-git-secrets existing current <path to repo>
    levelops-git-secrets existing historic <path to repo>

# About
[Levelops'](https://levelops.io) container that facilitates the use of [git-secrets](https://github.com/awslabs/git-secrets).
The container can be used in repositories that have or have not been initialized with git-secrets.