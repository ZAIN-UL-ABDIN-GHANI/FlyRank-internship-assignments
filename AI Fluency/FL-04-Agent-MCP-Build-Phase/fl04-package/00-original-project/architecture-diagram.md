# Architecture Diagram

```
                 +-------------------+
                 |       User        |
                 |  (types a topic)  |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |        n8n        |
                 |  (orchestrator)   |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |     Search API     |
                 |  (Tavily / SerpAPI)|
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |        LLM         |
                 |  (Claude / OpenAI) |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |  Markdown Generator |
                 |     (Code node)     |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |    Google Drive    |
                 |   (report storage) |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |        Gmail        |
                 |   (notification)     |
                 +-------------------+
```

See `docs/architecture.md` for the full component-by-component explanation and the deployment topology diagram.
