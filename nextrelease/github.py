import json
import os


class GitHubAction:
    def __init__(self):
        with open(os.environ["GITHUB_EVENT_PATH"], "r") as f:
            self.event_data = json.load(f)

    @property
    def event_name(self):
        return os.environ["GITHUB_EVENT_NAME"]

    @property
    def repo_full_name(self):
        return self.event_data["repository"]["full_name"]

    @property
    def default_branch(self):
        return self.event_data["repository"]["default_branch"]
