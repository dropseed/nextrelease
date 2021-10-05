# nextrelease

<img src="https://user-images.githubusercontent.com/649496/132932159-942f85cc-8f9e-4577-90f4-2315dded6d3f.png" width="150" height="150" align="right" />

**One-click release publishing by merging the nextrelease PR.**

Here's what it does:
- opens a release PR when there are unreleased commits ("Release version \<next\>")
- lists out the commits that would be released
- **\<you choose a semver label\>** ("release: minor")
- renames PR with the semver version ("Release version 1.1.0")
- updates version strings in files (or other "prep" commands)
- **\<you merge the PR\>**
- creates git tag on the merged commit
- publishes the package (can be any "publish" commands)
- creates a GitHub Release

![nextrelease example PR](https://user-images.githubusercontent.com/649496/132930548-537e53ff-e7bc-4e05-8f65-cf03b8cf33e0.png)

## GitHub Action

Save this as `.github/workflows/nextrelease.yml` and tweak as needed:

```yml
name: nextrelease
on:
  push:
    branches: [master]
  pull_request:
    branches: [master]
    types: [labeled, unlabeled, edited, synchronize]

jobs:
  sync:
    if: ${{ github.event_name == 'push' || github.event_name == 'pull_request' && github.head_ref == 'nextrelease' }}
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
      with:
        fetch-depth: 0  # all branches and tags
    - uses: dropseed/nextrelease@v1
      with:
        prepare_cmd: |
          sed -i -e "s/version = \"[^\"]*\"$/version = \"$VERSION\"/g" pyproject.toml
        publish_cmd: |
          poetry publish --build
        github_token: ${{ secrets.GITHUB_TOKEN }}
        tag_prefix: v  # default
        next_branch: nextrelease  # default
        github_release: publish  # or "draft", or "skip"
        release_notes: ""  # or "generate" to use https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes
```

### Using `prepare_cmd`

The `prepare_cmd` is typically used to update the version number (like in `package.json` or `pyproject.toml`).
This is easy enough to do with sed, but you can use anything you like.
**Any file modifications will be committed automatically** and you can use it for other automated tasks like updating changelogs.
If you have a "release prep" step that you can't automate, you can always edit files manually in the release PR.

#### Available env variables

- `VERSION` - the semver name for this release
- `LAST_VERSION` - the semver name for the previous release (or `0.0.0` if this will be the first release)
- `NEXT_VERSION` - the semver name for this release (alias for `VERSION`)

### Using `publish_cmd`

The `publish_cmd` happens after the new version is tagged and the GitHub Release is created.
This is typically used to push your release to a package manager (`npm publish`),
but can also be used for moving tags or uploading assets to your GitHub Release.
*This command will run from your master/main branch and doesn't expect any local file changes, so nothing will be committed automatically.*

#### Available env variables

- `TAG` - the full tag name associated with the release (ex. "v1.2.0-beta+unix")
- `VERSION` - the semver name for this release (ex. "1.2.0-beta+unix")
- `VERSION_MAJOR` - the semver major version for this release (ex. "1")
- `VERSION_MINOR` - the semver minor version for this release (ex. "2")
- `VERSION_PATCH` - the semver patch version for this releaes (ex. "0")
- `VERSION_PRERELEASE` - the semver prerelease name for this release (ex. "beta")
- `VERSION_BUILD` - the semver build name for this release (ex. "unix")

### Other notes

- If you haven't tagged/released anything yet, any version strings in your files should be "0.0.0".
- You could also run this on a `schedule` instead of every commit to main/master, but the list of commits you see in the PR could be outdated.
- You can trigger the tagging/publishing by pushing a commit titled "Release version \<version\>" manually. Just don't forget to do any pre-tagging steps like update your package.json, etc.
- Regular merge commits (i.e. not squash or rebase) haven't been tested. I'd strongly recommend squash commits anyway as it will make the history much simpler.

## Example Workflows

### PyPI using Poetry

```yaml
    - uses: dropseed/nextrelease@v1
      env:
        POETRY_PYPI_TOKEN_PYPI: ${{ secrets.YOUR_PYPI_TOKEN }}
      with:
        prepare_cmd: |
          sed -i -e "s/version = \"[^\"]*\"$/version = \"$VERSION\"/g" pyproject.toml
        publish_cmd: |
          pip3 install -U pip poetry && poetry publish --build --no-interaction
```

### GitHub Action

```yaml
    - uses: dropseed/nextrelease@v1
      with:
        publish_cmd: |
          git tag -a v$VERSION_MAJOR -m v$VERSION_MAJOR -f && git push origin v$VERSION_MAJOR -f
```

### npm

```yaml
    - uses: actions/setup-node@v2
      with:
        node-version: '16'
        registry-url: 'https://registry.npmjs.org'
    - uses: dropseed/nextrelease@v1
      env:
        NODE_AUTH_TOKEN: ${{ secrets.YOUR_NPM_TOKEN }}
      with:
        prepare_cmd: |
          npm version $NEXT_VERSION --no-git-tag-version --allow-same-version
        publish_cmd: |
          npm publish
        github_token: ${{ secrets.GITHUB_TOKEN }}
```
