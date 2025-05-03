[ADVICE]
please run server.py
[GOAL]
fix test_endpoints.py
[PROBLEM]
Paper info result cannot found the filene one_89c5.pdf  however the file is present in the RAG system

[CONTEXT]
this is my current result when run test_endpoints.py
```

$ python test_endpoints.py
Connected to server!
Available tools: ['rag_deepsearch', 'rag_get_paper_info', 'rag_list_papers', 'search_papers']
Paper list result: {"papers": ["one_89c5.pdf"], "paper_count": 1, "collection_info": {"name": "yani-one", "vector_size"...
Search result length: 998 characters
Deep search result: {"query": "paper", "results_count": 3, "search_time_ms": 391, "strategy": "similarity", "tier": "bot...
Paper info result: {"found": false, "message": "No paper found with filename: one_89c5.pdf"}...
Note: paper sections resource would be accessed via a different method
(scientific_rag)

```

this is some content of the RAG system

this is the METADATA
```
{
  "source": "one_89c5.pdf",
  "chunk_type": "paragraph",
  "headings": [
    "1.5. The logical route of the research"
  ],
  "section": "1.5. The logical route of the research",
  "original_filename": "one.pdf",
  "source_path": "/Users/agalan/Downloads/yani-one/one.pdf",
  "chunk_size": 512,
  "processed_date": "2025-04-25 19:44:17",
  "tier": "paragraph",
  "vector_size": 1024,
  "file_content_hash": "ff7caccbd21b25fee8b00c3ea0cbca9f",
  "content_hash": "49066487e9ff81a4bdd83f4aa29fd97f"
}
```

[INSTRUCTION]
dont list .venv unless necessary
