import httpx

from kube_research_aiq.settings import Settings


class LlmError(RuntimeError):
    pass


class LlmClient:
    """Minimal client for OpenAI-compatible chat completions (NVIDIA NIM, vLLM and others)."""

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport
        self.calls = 0

    async def complete(self, *, model: str, system: str, user: str, max_tokens: int = 900) -> str:
        if not self.settings.nvidia_api_key:
            raise LlmError("No model API key is configured.")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }
        headers = {"Authorization": f"Bearer {self.settings.nvidia_api_key}"}
        url = f"{self.settings.llm_base_url.rstrip('/')}/chat/completions"
        self.calls += 1
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.request_timeout_seconds, transport=self.transport
            ) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            raise LlmError(f"{model} returned HTTP {exc.response.status_code}.") from exc
        except httpx.HTTPError as exc:
            raise LlmError(f"Could not reach {model}: {exc.__class__.__name__}.") from exc
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise LlmError(f"{model} returned an unexpected response.") from exc
        return (content or "").strip()
