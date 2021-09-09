from nextrelease.pullrequest import PullRequest


def test_pr_release_version():
    pr = PullRequest({"title": "Release version <next>"}, None)
    assert pr.release_version is None

    pr = PullRequest({"title": "Release version 1.0.0"}, None)
    assert pr.release_version == "1.0.0"

    pr = PullRequest({"title": "Release version 1.0.0-beta"}, None)
    assert pr.release_version == "1.0.0-beta"

    pr = PullRequest({"title": "Release version 1.0.0-beta ok"}, None)
    assert pr.release_version == "1.0.0-beta"


def test_pr_body():
    pr = PullRequest(None, None)
    assert (
        pr.generate_body("1.0.0", ["Update x", "Update y"])
        == """These commits are new since version 1.0.0:

- Update x
- Update y

To release the new version:

- [ ] Label this PR (ex. `release: major`)
- [ ] Update the changelog on this branch (optional)
- [ ] Merge this PR (commit message should start with `Release version {version}`)
"""
    )


def test_pr_body_prerelease():
    pr = PullRequest(None, None)
    assert (
        pr.generate_body("1.0.0-beta", ["Update x", "Update y"])
        == """These commits are new since version 1.0.0-beta:

- Update x
- Update y

To release the new version:

- [ ] Label this PR (ex. `release: major`)
- [ ] Update the changelog on this branch (optional)
- [ ] Merge this PR (commit message should start with `Release version {version}`)
"""
    )


def test_pr_next_semver():
    pr = PullRequest({"labels": [{"name": "release: major"}]}, None)
    assert pr.get_next_semver("1.0.0") == "2.0.0"

    pr = PullRequest({"labels": [{"name": "release: minor"}]}, None)
    assert pr.get_next_semver("1.0.0") == "1.1.0"

    pr = PullRequest({"labels": [{"name": "release: prerelease"}]}, None)
    assert pr.get_next_semver("1.0.0") == None

    pr = PullRequest(
        {"labels": [{"name": "release: prerelease"}, {"name": "release: major"}]}, None
    )
    assert pr.get_next_semver("1.0.0") == "2.0.0-rc.1"

    pr = PullRequest(
        {"labels": [{"name": "release: prerelease"}, {"name": "release: minor"}]}, None
    )
    assert pr.get_next_semver("1.0.0") == "1.1.0-rc.1"

    pr = PullRequest({"labels": [{"name": "release: prerelease"}]}, None)
    assert pr.get_next_semver("1.0.0-rc.1") == "1.0.0-rc.2"
