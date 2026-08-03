# LangGraph Best Practices

## State Design
- Keep the state TypedDict small and explicit. Every field should have a clear owner node.
- Avoid storing derived data in state if it can be recomputed from existing fields.

## Node Granularity
- One responsibility per node (retrieve, plan, review). Do not combine unrelated steps into a single node.
- Nodes should be pure functions of state where possible, so they can be unit tested without running the whole graph.

## Edges and Control Flow
- Use conditional edges for branching (e.g. requirements incomplete vs ready) instead of branching logic inside a node.
- Keep graphs shallow at first; add loops or parallel branches only once the linear flow is proven correct.

## Testing
- Test each node function directly with a hand-built state dict before testing the compiled graph.
- Mock external calls (LLM, retrievers) in node-level tests so tests run without network access or API keys.
