import os
import subprocess

import semver
import click
import cls_client

from .github import GitHubAction
from . import git
from .api import APISession
from .pullrequest import PullRequest
from .settings import GITHUB_LABELS
from . import __version__


cls_client.set_project_key("cls_pk_9HBrOiOyH1rHmfTsXcPPFT1G")
cls_client.set_project_slug("nextrelease")
cls_client.set_ci_tracking_enabled(True)
cls_client.set_version(__version__)


def release_commit(
    requests_session,
    repo_full_name,
    tag_prefix,
    publish_cmd,
    github_release,
    release_notes,
):
    version = git.get_release_commit_version()
    print(f"Releasing version {version} from commit")
    version_semver = semver.VersionInfo.parse(version)
    tag_name = git.tag_commit(version=version, tag_prefix=tag_prefix)

    if github_release == "skip":
        print("Skipping GitHub release")
    else:
        if release_notes == "generate":
            response = requests_session.post(
                f"/repos/{repo_full_name}/releases/generate-notes",
                json={
                    "tag_name": tag_name,
                    "target_commitish": git.get_previous_commit_sha()  # so we don't include the release PR,
                    # "previous_tag_name": "",
                },
            )
            response.raise_for_status()
            release_notes = response.json()["body"]

        print("Creating GitHub release")
        response = requests_session.post(
            f"/repos/{repo_full_name}/releases",
            json={
                "tag_name": tag_name,
                "prerelease": bool(version_semver.prerelease),
                "body": release_notes,
                "draft": github_release == "draft",
            },
        )
        response.raise_for_status()

    if publish_cmd:
        print(f"Running publish command:\n{publish_cmd}")
        env = os.environ.copy()  # Include existing env variables
        env["TAG"] = tag_name
        env["VERSION"] = version
        env["VERSION_MAJOR"] = str(version_semver.major)
        env["VERSION_MINOR"] = str(version_semver.minor)
        env["VERSION_PATCH"] = str(version_semver.patch)
        env["VERSION_PRERELEASE"] = str(version_semver.prerelease)
        env["VERSION_BUILD"] = str(version_semver.build)
        subprocess.check_call(
            "set -e\n" + publish_cmd,
            shell=True,
            env=env,
        )


def ensure_labels_exist(requests_session, repo_full_name):
    response = requests_session.get(f"/repos/{repo_full_name}/labels")
    response.raise_for_status()
    label_names = [label["name"] for label in response.json()]
    missing_labels = [
        label_data
        for label_data in GITHUB_LABELS
        if label_data["name"] not in label_names
    ]
    for missing_label in missing_labels:
        response = requests_session.post(
            f"/repos/{repo_full_name}/labels", json=missing_label
        )
        response.raise_for_status()


@click.group()
@click.version_option(__version__)
def cli():
    pass


@cli.command()
@click.option("--tag-prefix", default="v", show_default=True)
@click.option(
    "--api-url",
    envvar="GITHUB_API_URL",
    default="https://api.github.com",
)
@click.option("--token", envvar="GITHUB_TOKEN", required=True)
@click.option(
    "--next-branch", default="nextrelease", show_default=True, envvar="NEXT_BRANCH"
)
@click.option("--publish-cmd", envvar="PUBLISH_CMD")
@click.option("--prepare-cmd", envvar="PREPARE_CMD")
@click.option(
    "--github-release",
    default="publish",
    type=click.Choice(["publish", "draft", "skip"]),
    envvar="GITHUB_RELEASE",
)
@click.option(
    "--release-notes",
    default="",
    type=click.Choice(["", "generate"]),
    envvar="RELEASE_NOTES",
)
@cls_client.track_command(include_kwargs=["tag_prefix", "next_branch"])
def ci(
    tag_prefix,
    api_url,
    token,
    next_branch,
    publish_cmd,
    prepare_cmd,
    github_release,
    release_notes,
):

    if "TAG_PREFIX" in os.environ:
        # This way it can be an empty string, which isn't possible with click envvar
        tag_prefix = os.environ["TAG_PREFIX"]

    print("tag_prefix:", tag_prefix)
    print("github_release:", github_release)
    print("release_notes:", release_notes)
    print("api_url:", api_url)
    print("next_branch:", next_branch)
    print("publish_cmd:", publish_cmd)
    print("prepare_cmd:", prepare_cmd)

    requests_session = APISession(base_url=api_url)
    requests_session.headers.update(
        {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "token " + token,
        }
    )

    event_branch = git.get_current_branch()

    gh_action = GitHubAction()

    git.set_author()  # needed for tags and commits

    if (
        gh_action.event_name == "push"
        and event_branch == gh_action.default_branch
        and git.is_release_commit()
    ):
        release_commit(
            requests_session=requests_session,
            repo_full_name=gh_action.repo_full_name,
            tag_prefix=tag_prefix,
            publish_cmd=publish_cmd,
            github_release=github_release,
            release_notes=release_notes,
        )
        return

    last_tag = git.get_last_semver_tag(tag_prefix=tag_prefix)
    if last_tag:
        commits_since_last_tag = git.get_commits(
            last_tag, f"origin/{gh_action.default_branch}"
        )
    else:
        commits_since_last_tag = git.get_commits(f"origin/{gh_action.default_branch}")

    print(f"Commits since last tag: {commits_since_last_tag}")

    if not commits_since_last_tag:
        return

    if last_tag and last_tag.startswith(tag_prefix):
        last_version = last_tag[len(tag_prefix) :]
    else:
        last_version = last_tag

    print(f"Last version: {last_version}")

    if event_branch != next_branch:
        print(f"Checking out {next_branch} branch")
        created_branch = git.checkout_branch(next_branch)

        if not git.get_commits(f"origin/{gh_action.default_branch}", "HEAD"):
            git.empty_commit()  # need at least one commit to open a PR
            git.push_branch(next_branch)
        elif created_branch:
            git.push_branch(next_branch)

    pr = PullRequest.get_or_create(
        repo=gh_action.repo_full_name,
        head=next_branch,
        base=gh_action.default_branch,
        body=PullRequest.generate_body(last_version, commits_since_last_tag),
        requests_session=requests_session,
    )
    pr.update(
        last_version=last_version,
        commits_since_last_tag=commits_since_last_tag,
    )

    ensure_labels_exist(
        requests_session=requests_session, repo_full_name=gh_action.repo_full_name
    )

    if pr.release_version and prepare_cmd:
        env = os.environ.copy()  # Include existing env variables
        env["VERSION"] = pr.release_version  # alias to next
        env["LAST_VERSION"] = last_version or "0.0.0"
        env["NEXT_VERSION"] = pr.release_version
        subprocess.check_call(
            "set -e\n" + prepare_cmd,
            shell=True,
            env=env,
        )
        try:
            git.commit(".", f"Prepare release {pr.release_version}")
            git.push_branch(next_branch)
        except subprocess.CalledProcessError:
            print("No changes to commit")

    if event_branch == next_branch and not pr.release_version:
        click.secho("Choose a version for this PR!", fg="red", err=True)
        exit(1)


if __name__ == "__main__":
    cli()
