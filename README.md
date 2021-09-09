# nextrelease

- If you haven't tagged/released anything yet, any version strings in your files should be "0.0.0".

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
    - uses: dropseed/nextrelease@v0
      with:
        prepare_cmd: |
          sed -i -e "s/version = \"[^\"]*\"/version = \"$VERSION\"/g" pyproject.toml
        publish_cmd: |
          poetry publish --build
        github_token: ${{ secrets.GITHUB_TOKEN }}
        tag_prefix: v  # default
        next_branch: nextrelease  # default
```

You could also run this on a `schedule` instead of every commit to main/master,
but you run the risk of creating a release that doesn't factor in the latest commits.
