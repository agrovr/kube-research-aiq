---
title: Serving LLMs behind OpenAI-compatible APIs
url: https://docs.vllm.ai/en/latest/
topics: inference, llm, vllm, nim, openai compatible, serving, batching, models, latency
---
Inference servers such as vLLM and NVIDIA NIM expose an OpenAI-compatible chat completions API, so the same client code can target a hosted endpoint or a self-hosted model by changing a base URL. vLLM achieves high throughput with PagedAttention, which manages attention key and value memory efficiently, and with continuous batching of incoming requests.

Routing different stages of an agent to different models is a common cost control: a small, fast model classifies and plans, while a larger model writes long-form synthesis. Timeouts, retries with backoff and a bounded max_tokens keep one slow completion from stalling a whole worker.

Hosted endpoints are the fastest way to start because they need no GPUs, while self-hosting trades operational work for data control, predictable cost at scale and freedom to fine-tune.
