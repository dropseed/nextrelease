import re

import semver

from .settings import (
    RELEASE_COMMIT_MSG_PREFIX,
    MAJOR_LABEL,
    MINOR_LABEL,
    PATCH_LABEL,
    PRERELEASE_LABEL,
    PR_TITLE_VERSION_PLACEHOLDER,
)


class PullRequest:
    def __init__(self, data, requests_session):
        self.data = data
        self.requests_session = requests_session

    @property
    def title(self):
        return self.data["title"]

    @property
    def body(self):
        return self.data["body"]

    @property
    def number(self):
        return self.data["number"]

    @property
    def node_id(self):
        return self.data["node_id"]

    @property
    def draft(self):
        return self.data["draft"]

    @property
    def label_names(self):
        return [x["name"] for x in self.data["labels"]]

    @property
    def release_version(self):
        matches = re.findall(RELEASE_COMMIT_MSG_PREFIX + r"(\S+)", self.title)
        if matches:
            match = matches[0]
            if match != PR_TITLE_VERSION_PLACEHOLDER:
                return match

    @staticmethod
    def generate_body(last_version, commits_since_last_tag):
        if last_version:
            heading = f"These commits are new since version {last_version}:"
        else:
            heading = "There are no tags/releases on this repo yet. These commits can be released:"

        commits_list = "\n".join([f"- {x}" for x in commits_since_last_tag])
        body = f"""{heading}

{commits_list}

To release the new version:

- [ ] Label this PR (ex. `release: major`)
- [ ] Update the changelog on this branch (optional)
- [ ] Merge this PR (commit message should start with `{RELEASE_COMMIT_MSG_PREFIX}{{version}}`)
"""
        return body

    def get_next_semver(self, last_version):
        if not any([x.startswith("release: ") for x in self.label_names]):
            return None

        last_semver = semver.VersionInfo.parse(last_version or "0.0.0")
        next_semver = last_semver

        if MAJOR_LABEL in self.label_names:
            next_semver = next_semver.bump_major()

        if MINOR_LABEL in self.label_names:
            next_semver = next_semver.bump_minor()

        if PATCH_LABEL in self.label_names:
            next_semver = next_semver.bump_patch()

        if PRERELEASE_LABEL in self.label_names:
            if last_semver == next_semver and not next_semver.prerelease:
                return None
            next_semver = next_semver.bump_prerelease()

        return str(next_semver)

    def set_draft(self, draft):
        # TODO integration permission issue...
        # can you give the default token permission? another app? has to be a user account?
        mutation = (
            "convertPullRequestToDraft" if draft else "markPullRequestReadyForReview"
        )
        query = """
        mutation($input:%sInput!) {
            %s(input: $input) {
                clientMutationId
            }
        }
        """ % (
            mutation[:1].upper() + mutation[1:],  # capfirst
            mutation,
        )
        variables = {
            "input": {
                "pullRequestId": self.node_id,
            }
        }
        response = self.requests_session.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
        )
        response.raise_for_status()
        print(response.json())
        if response.json().get("errors"):
            raise Exception(f"GraphQL errors:\n{response.json()}")

    def update(self, last_version, commits_since_last_tag):
        patch_json = {}

        next_version = (
            self.get_next_semver(last_version) or PR_TITLE_VERSION_PLACEHOLDER
        )
        if next_version != self.release_version:
            patch_json["title"] = f"{RELEASE_COMMIT_MSG_PREFIX}{next_version}"

        body = self.generate_body(last_version, commits_since_last_tag)
        if self.data["body"] != body:
            patch_json["body"] = body

        if patch_json:
            response = self.requests_session.patch(self.data["url"], json=patch_json)
            response.raise_for_status()
            self.data = response.json()

        # Do this after title change, so self.data is updated
        # if self.release_version and self.draft:
        #     self.set_draft(False)
        # elif not self.release_version and not self.draft:
        #     self.set_draft(True)

    @classmethod
    def get(cls, repo, head, base, requests_session):
        org_name = repo.split("/")[0]
        response = requests_session.get(
            f"/repos/{repo}/pulls",
            params={
                "state": "open",
                "head": f"{org_name}:{head}",  # should never be on a fork
                "base": base,
            },
        )
        response.raise_for_status()

        if response.json():
            return cls(
                data=response.json()[0],
                requests_session=requests_session,
            )

        return None

    @classmethod
    def create(cls, repo, head, base, body, requests_session):
        response = requests_session.post(
            f"/repos/{repo}/pulls",
            json={
                "head": head,
                "base": base,
                "title": f"{RELEASE_COMMIT_MSG_PREFIX}{PR_TITLE_VERSION_PLACEHOLDER}",
                "body": body,
                # "draft": True,
            },
        )
        response.raise_for_status()

        return cls(
            data=response.json(),
            requests_session=requests_session,
        )

    @classmethod
    def get_or_create(cls, repo, head, base, body, requests_session):
        existing_pull = cls.get(repo, head, base, requests_session)
        if existing_pull:
            return existing_pull

        return cls.create(repo, head, base, body, requests_session)
