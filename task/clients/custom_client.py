import json
import aiohttp
import requests

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class CustomDialClient(BaseClient):
    _endpoint: str
    _api_key: str

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        self._endpoint = DIAL_ENDPOINT + f"/openai/deployments/{deployment_name}/chat/completions"

    def get_completion(self, messages: list[Message]) -> Message:
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json",
        }
        request_data = {
            "messages": [message.to_dict() for message in messages],
        }

        response = requests.post(
            self._endpoint,
            headers=headers,
            json=request_data,
        )

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        content = response.json()["choices"][0]["message"]["content"]
        print(content)
        return Message(Role.AI, content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json",
        }
        request_data = {
            "stream": True,
            "messages": [message.to_dict() for message in messages],
        }
        contents: list[str] = []

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self._endpoint,
                json=request_data,
                headers=headers,
            ) as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {response_text}")

                done = False
                while not done:
                    raw_chunk = await response.content.readline()
                    if not raw_chunk:
                        break

                    chunk = raw_chunk.decode("utf-8").strip()
                    if not chunk:
                        continue

                    print(chunk)
                    if chunk == "data: [DONE]":
                        done = True
                        continue

                    content_snippet = self._get_content_snippet(chunk)
                    if content_snippet:
                        contents.append(content_snippet)

        return Message(Role.AI, "".join(contents))

    @staticmethod
    def _get_content_snippet(chunk: str) -> str:
        data_prefix = "data: "
        if not chunk.startswith(data_prefix):
            return ""

        payload = chunk[len(data_prefix):]
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return ""

        choices = data.get("choices", [])
        if not choices:
            return ""

        delta = choices[0].get("delta", {})
        return delta.get("content", "") or ""

