---
title: Evaluating research agent output
url: https://github.com/NVIDIA-AI-Blueprints/aiq
topics: evaluation, quality, benchmark, citations, grounding, scoring, testing, agents
---
Research agents need evaluation beyond unit tests because their output is prose whose quality varies with models, prompts and sources. Useful automatic signals include citation coverage, the share of sections that cite at least one source, and source diversity across distinct documents.

A fixed benchmark set of questions run on a schedule catches regressions when a model or prompt changes. Deterministic offline modes, where retrieval and writing run without external services, keep continuous integration fast and reproducible.

Human review remains the final check for factual accuracy, and capturing reviewer feedback alongside each report builds a dataset for future tuning.
