# nextrelease

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
    - uses: dropseed/nextrelease@master
      with:
        prepare_cmd: |
          sed -i -e "s/version = \"[^\"]*\"/version = \"$VERSION\"/g" pyproject.toml
        publish_cmd: |
          git tag -a v$VERSION_MAJOR -m v$VERSION_MAJOR -f && git push origin v$VERSION_MAJOR -f
        github_token: ${{ secrets.GITHUB_TOKEN }}
        tag_prefix: v  # default
        next_branch: nextrelease  # default
```
