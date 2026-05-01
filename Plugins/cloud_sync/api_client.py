import io
import json

import requests


class CloudApiClient:

    def __init__(self, server_url: str, login: str, password: str):
        self._base_url = server_url.rstrip("/")
        self._login = login
        self._password = password
        self._token: str | None = None
        self._session = requests.Session()

    def _url(self, action: str) -> str:
        return f"{self._base_url}/index.php?action={action}"

    def authenticate(self) -> str:
        resp = self._session.post(
            self._url("auth"),
            json={"login": self._login, "password": self._password},
            timeout=15,
        )
        if resp.status_code >= 400:
            body = resp.text[:300]
            raise RuntimeError(f"HTTP {resp.status_code}: {body}")
        data = resp.json()
        if "error" in data:
            raise RuntimeError(data["error"])
        if "token" not in data:
            raise RuntimeError(f"Неожиданный ответ сервера: {json.dumps(data, ensure_ascii=False)[:300]}")
        self._token = data["token"]
        self._session.headers["X-Auth-Token"] = self._token
        return self._token

    def push_changes(self, data: dict, files: dict | None = None) -> dict:
        form_data = {"data": json.dumps(data, ensure_ascii=False)}
        req_files = []
        if files:
            for name, content in files.items():
                req_files.append(
                    ("files[]", (name, io.BytesIO(content), "application/octet-stream"))
                )
        resp = self._session.post(
            self._url("sync") + "&sub=push",
            data=form_data,
            files=req_files if req_files else None,
            timeout=120,
        )
        resp.raise_for_status()
        result = resp.json()
        if "error" in result:
            raise RuntimeError(result["error"])
        return result

    def pull_changes(self, since: str) -> dict:
        params = {"sub": "pull"}
        if since:
            params["since"] = since
        resp = self._session.get(
            self._url("sync"),
            params=params,
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
        if "error" in result:
            raise RuntimeError(result["error"])
        return result

    def download_file(self, sync_uuid: str) -> bytes:
        resp = self._session.get(
            self._url("sync"),
            params={"sub": "file", "uuid": sync_uuid},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.content

    def delete_records(self, uuids: list[str]) -> dict:
        resp = self._session.post(
            self._url("sync") + "&sub=delete",
            json={"uuids": uuids},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
