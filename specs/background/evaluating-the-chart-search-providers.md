# Evaluating the chart search providers

OpenMRS chart search can answer a clinician's question in two ways, and its
built-in way can run its model in two places. This page explains both choices,
how a plain ChartSearchAI installation makes them, and how the OpenClinAI
evaluation makes them, so a published result can be read for what it compares.

## Two separate choices

**Which provider answers.** ChartSearchAI chooses a provider for each request
(`chartsearchai.providers.enabled`, for example `bundled,hub`).

- The **bundled** provider is ChartSearchAI itself. It reads the chart from
  QueryStore, builds the prompt, calls a model once, then runs its own drug-safety
  checks and turns the reply into an answer with citations.
- The **Hub** provider hands the question to med-agent-hub and relays what comes
  back. The Hub reads QueryStore, builds its own prompts, makes its own model calls
  and checks, and returns the answer with its confidence and In-Depth.
  ChartSearchAI's answer pipeline is not used.

**Where the bundled provider's model runs.** This is ChartSearchAI's engine
setting, `chartsearchai.llm.engine`, and it applies to the bundled provider only.

- **Local**, the default: ChartSearchAI starts a llama-server as a child process
  of the OpenMRS server and loads the model file named by
  `chartsearchai.llm.modelFilePath`.
- **Remote**: ChartSearchAI sends the same model call to an OpenAI-compatible
  server at `chartsearchai.llm.remote.endpointUrl`.

Either way the bundled pipeline is the same; only the destination of its one
model call changes. Choosing the remote engine does not make the bundled provider
external. The Hub has its own model address and does not read the engine setting.

| | Who builds the answer | Where the model runs |
| --- | --- | --- |
| Bundled, local engine | ChartSearchAI | A llama-server inside the OpenMRS server |
| Bundled, remote engine | ChartSearchAI | Any OpenAI-compatible server |
| Hub | med-agent-hub | The Hub's configured model server |

## How a plain installation runs the bundled provider

The [ChartSearchAI README](https://github.com/openmrs/openmrs-module-chartsearchai#readme)
describes two ready-made installations. Both use the local engine with Gemma 4
E4B (Q4_K_M, about 5 GB) and the module's default settings, including the whole
chart in every prompt.

- **Docker** (`docker compose up`) downloads the model and runs it on the CPU. The
  README notes that Docker is always CPU-only, even on an Apple Silicon Mac,
  because the container cannot reach the Mac's GPU.
- **The macOS standalone** runs natively and uses the Mac's GPU automatically.
  Its Linux and Windows builds run on the CPU.

## How the OpenClinAI evaluation runs them

The research stack runs OpenMRS in Docker on a Mac.
`make chartsearch-research-setup` leaves every ChartSearchAI setting at the
module default except the engine: the bundled provider uses the remote engine,
pointed at the llama-router that runs natively on the Mac with GPU access. The
Hub uses the same router. During a full evaluation, both providers' model calls
pass through a small recording proxy to the same model on that router, so every
request each provider sent is kept with the run.

Reports published before 22 October 2026 ran the bundled provider with
query-scoped context (`chartsearchai.chartMode=queryScoped`, 12 similarity
records) instead of its whole-chart default, which left some records out of its
prompts.

### What this tests and what it does not

| Part of the bundled provider | Exercised by the evaluation |
| --- | --- |
| Chart retrieval, prompt, drug-safety checks, answer and citation handling | Yes |
| The model | Yes, but the shared model on the router, not the E4B file on the server's CPU |
| Starting, authenticating and stopping its own llama-server | No |
| Its own context size (`chartsearchai.llm.contextSize`) | No; the router's context size applies |
| Per-chart warmup and saved chart caches | No |
| Unloading the model when idle | No |
| Exact prompt-token counting with its local engine | Not confirmed |

### Differences that are real

With the bundled provider on its defaults, a remaining gap between the providers
comes from what each can do, not from a setting. In the October evaluations three
such gaps showed:

- The bundled prompt does not state the current date, so it cannot place
  appointments or measurements relative to today. The Hub gives its model the
  date and a table of every chart date's distance from it.
- The bundled provider has no guideline knowledge base; the Hub can cite WHO
  guidance records.
- The Hub checks dates in an answer against the chart's dated records and
  corrects or marks a wrong one; the bundled provider does not.

## Three ways to compare

1. **Bundled as shipped.** The bundled provider on the local engine with the E4B
   file, on the CPU inside Docker, every setting at its default. This is the only
   setup that exercises the rows marked "No" above. Its speed is CPU speed, so it
   is compared with the others on answer quality, not latency. Not yet automated.
2. **Same model, both providers.** The bundled provider on the remote engine and
   the Hub, both on the router serving E4B. The router's E4B file is the same file
   ChartSearchAI ships (sha256 `85a896a0…cd1fab87` in its model manifest). If its
   bundled answers match setup 1's, the remote engine is a faithful stand-in and
   any gap between the providers is capability. Needs a Hub E4B answer profile.
3. **12B, both providers.** The current default full evaluation: the bundled
   provider and the Hub's `single-12b-answer` profile (one answer call with the
   date, citation and drug-safety checks, no model review or In-Depth) on Gemma 4
   12B. A larger model than a plain installation runs, used to compare the
   providers on equal footing.

Run the default full evaluation from the umbrella root after
`make chartsearch-research-setup`:

```sh
make review FULL=1
```

Add a Hub profile as a further arm with `PROFILES=`, for example
`PROFILES=single-12b-checked` for the Hub's checked answer with review and
In-Depth. Each judged run is published with its dashboard at
[reports.openclinai.org](https://reports.openclinai.org/).
