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
          sed -i -e "s/version = \"[^\"]*\"/version = \"$VERSION\"/g" pyproject.toml
        publish_cmd: |
          poetry publish --build
        github_token: ${{ secrets.GITHUB_TOKEN }}
        tag_prefix: v  # default
        next_branch: nextrelease  # default
```

Notes:

- If you haven't tagged/released anything yet, any version strings in your files should be "0.0.0".
- You could also run this on a `schedule` instead of every commit to main/master, but the list of commits you see in the PR could be outdated.
- You can trigger the tagging/publishing by pushing a commit titled "Release version \<version\>" manually. Just don't forget to do any pre-tagging steps like update your package.json, etc.
- Regular merge commits (i.e. not squash or rebase) haven't been tested. I'd strongly recommend squash commits anyway as it will make the history much simpler.
