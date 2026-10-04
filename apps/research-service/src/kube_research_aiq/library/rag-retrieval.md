---
title: Retrieval and grounding for research agents
url: https://docs.tavily.com/documentation/api-reference/endpoint/search
topics: retrieval, rag, search, grounding, citations, sources, bm25, ranking, tavily, web search
---
Retrieval-augmented generation grounds a model's answer in documents fetched at query time, which reduces unsupported claims and makes citations possible. A research agent typically issues several focused searches, one per sub-question, rather than a single broad search.

Lexical ranking functions such as BM25 score passages by how often query terms appear, weighted by how rare those terms are across the collection, and they need no embeddings or GPUs. Dense vector retrieval captures meaning beyond exact words, and many systems combine both in hybrid search.

Web search APIs built for agents, such as Tavily, return titles, URLs, short content extracts and relevance scores ready to feed into a prompt. Numbering sources and asking the writer to cite them inline as [1], [2] keeps every statement traceable to its origin.

Deduplicating sources across sub-questions and capping the number passed to the writer keeps prompts small and reports focused.
