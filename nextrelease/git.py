from subprocess import check_output, check_call, CalledProcessError

import semver

from .settings import RELEASE_COMMIT_MSG_PREFIX, GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL


def is_release_commit():
    return get_current_commit_message().startswith(RELEASE_COMMIT_MSG_PREFIX)


def get_release_commit_version():
    # get the first string after the prefix (can have trailers after, like #<pr_number>)
    return get_current_commit_message()[len(RELEASE_COMMIT_MSG_PREFIX) :].split()[0]


def get_current_commit_message():
    return check_output(["git", "log", "-1", "--pretty=%B"]).strip().decode("utf-8")


def get_previous_commit_sha():
    return check_output(["git", "rev-parse", "HEAD^1"]).strip().decode("utf-8")


def tag_commit(version, tag_prefix="v"):
    version_with_prefix = tag_prefix + version
    check_call(["git", "tag", "-a", version_with_prefix, "-m", version_with_prefix])
    check_call(["git", "push", "origin", "--tags"])
    return version_with_prefix


def checkout_branch(branch_name):
    try:
        check_call(["git", "checkout", branch_name, "--"])
        created = False
    except CalledProcessError:
        check_call(["git", "checkout", "-b", branch_name])
        created = True

    return created


def push_branch(branch_name):
    check_call(["git", "push", "--set-upstream", "origin", branch_name])


def commit(filename, message):
    check_call(["git", "add", filename])
    check_call(["git", "commit", "-m", message])


def set_author():
    check_call(["git", "config", "user.name", GIT_AUTHOR_NAME])
    check_call(["git", "config", "user.email", GIT_AUTHOR_EMAIL])


def empty_commit():
    check_call(
        ["git", "commit", "--allow-empty", "-m", "Empty commit to start nextrelease PR"]
    )


def get_last_semver_tag(tag_prefix="v"):
    tags = check_output(["git", "tag"]).strip().decode("utf-8").splitlines()
    highest_tag = None
    highest_semver = semver.VersionInfo.parse("0.0.0")

    for tag in tags:
        if not tag.startswith(tag_prefix):
            continue

        tag_without_prefix = tag[len(tag_prefix) :]
        if semver.VersionInfo.isvalid(tag_without_prefix):
            semver_version = semver.VersionInfo.parse(tag_without_prefix)
            if semver_version > highest_semver:
                highest_semver = semver_version
                highest_tag = tag

    return highest_tag


def get_current_branch():
    try:
        return (
            check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .strip()
            .decode("utf-8")
        )
    except CalledProcessError:
        return None


def get_commits(from_ref, to_ref=""):
    if from_ref and to_ref:
        revisions = f"{from_ref}..{to_ref}"
    else:
        revisions = from_ref
    return (
        # -- separates revisions from paths
        check_output(["git", "log", "--oneline", revisions, "--"])
        .strip()
        .decode("utf-8")
        .splitlines()
    )
