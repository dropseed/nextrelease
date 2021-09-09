RELEASE_COMMIT_MSG_PREFIX = "Release version "
GIT_AUTHOR_NAME = "github-actions"
GIT_AUTHOR_EMAIL = "github-actions@github.com"
MAJOR_LABEL = "release: major"
MINOR_LABEL = "release: minor"
PATCH_LABEL = "release: patch"
PRERELEASE_LABEL = "release: prerelease"
GITHUB_LABELS = [
    {"name": MAJOR_LABEL, "color": "187795"},
    {
        "name": MINOR_LABEL,
        "color": "38686A",
    },
    {
        "name": PATCH_LABEL,
        "color": "A3B4A2",
    },
    {
        "name": PRERELEASE_LABEL,
        "color": "CDC6AE",
    },
]
PR_TITLE_VERSION_PLACEHOLDER = "<next>"
