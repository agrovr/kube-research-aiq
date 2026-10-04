---
title: The NVIDIA AI-Q research agent blueprint
url: https://github.com/NVIDIA-AI-Blueprints/aiq
topics: aiq, research agent, shallow, deep, orchestration, planning, citations, report, nvidia, agents
---
NVIDIA's AI-Q blueprint is a reference design for research agents that produce cited answers and report-style research. An orchestration step classifies each query and routes it to either a shallow researcher or a deep researcher.

The shallow researcher runs a bounded, fast loop of tool calls and returns a concise answer with sources. The deep researcher plans the investigation, runs researcher workers over the planned questions, gathers sources and hands them to a writing role that assembles a long-form report.

AI-Q connects agents to several knowledge layers, including web search through providers such as Tavily and enterprise retrieval over private documents. Citation integrity is a design goal: every claim in a report should trace back to a retrieved source.

Separating planning, retrieval and writing into distinct roles makes each step observable and testable, and it lets a platform choose a different model for each role.
