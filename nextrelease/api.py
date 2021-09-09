from requests import Session
from urllib.parse import urljoin


class APISession(Session):
    def __init__(self, base_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = base_url

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.base_url, url)
        response = super().request(method, url, *args, **kwargs)
        print(f"API url={response.url} method={method} status={response.status_code}")
        return response
