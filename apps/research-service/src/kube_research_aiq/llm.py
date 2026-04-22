import httpx

from kube_research_aiq.settings import Settings


class LlmClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def complete(self, *, model: str, system: str, user: str) -> str:
        if self.settings.provider == "mock" or not self.settings.nvidia_api_key:
            return self._mock_completion(system=system, user=user, model=model)

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": 1200,
        }
        headers = {"Authorization": f"Bearer {self.settings.nvidia_api_key}"}
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    @staticmethod
    def _mock_completion(*, system: str, user: str, model: str) -> str:
        topic = user.strip().splitlines()[0][:160]
        return (
            f"Mock response from {model}.\n\n"
            f"System intent: {system[:120]}\n\n"
            f"Draft finding for: {topic}\n\n"
            "This offline provider is deterministic so CI and local clusters can run without "
            "external model credentials. Set KRAI_PROVIDER=nvidia and KRAI_NVIDIA_API_KEY to "
            "use NVIDIA-hosted NIM-compatible chat completions."
        )
