# Stack brief (STACK=1)

Added to the reviewer brief when the PR is one layer of a stack. The prompt lists the
stack's PRs bottom to top and checks out the merged top.

- Read what each layer emits that another consumes: REST and SSE payloads, stored
  rows and their error states, global properties, events, the shape of a turn or a
  fallback. For each, find the consumer in the layers above (and in the frontend
  repository for backend stacks) and check the contract at the merged top.
- Look for a fix in one layer that a later layer undoes, bypasses or duplicates.
- Run the merged top's tests; a test that passes per layer and fails at the top is
  blocking with that evidence.
- Report each finding against the layer that should change, with the same JSON
  contract as the reviewer brief.
