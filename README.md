# nextrelease

```yml
name: nextrelease
on:
  workflow_dispatch: {}
  push:
    branches: [master]
  pull_request:
    branches: [nextrelease]
    on: [labeled, edited]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
      with:
        fetch-depth: 0  # all branches and tags
    - uses: dropseed/nextrelease@v1
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        prepare_cmd: ""
        publish_cmd: poetry build && poetry publish
        tag_prefix: v
        next_branch: next
```
