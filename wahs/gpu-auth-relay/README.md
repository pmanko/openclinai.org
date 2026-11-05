# WAHS UW GPU Auth Relay (`wahs/gpu-auth-relay`)

Standalone cloud HTTPS authentication relay for the WA Health Summary (WAHS) Interactive Demo ([`landing/wahs/demo/index.html`](../../landing/wahs/demo/index.html)).

## Purpose

Allows whitelisted UW CIRG and OpenClinAI researchers to use the shared UW CIRG LiteLLM GPU server (`https://llm.co.dev.cirg.uw.edu`) directly from `https://wahs-demo.openclinai.org/` in any browser **without running a local Docker stack** and **without exposing the shared LiteLLM API key to client browsers**.

## Architecture

1. **Browser (`landing/wahs/demo/index.html`):**
   - User clicks **Sign in with Google** inside the **UW GPU Server** preset card.
   - Firebase Auth (`clinical-ai-harness.firebaseapp.com`) completes 1-click Google OAuth popup sign-in and returns a Google OAuth / Firebase ID token.
   - Browser sends `X-Google-Auth-Token: <token>` to this Cloud Run HTTPS service (`/v1/auth/status`, `/v1/models`, `/v1/chat/completions`).
   - Browser constructs the full WAHS system prompt (`wahs-kb-guided` or `wahs-raw-unhinted`), condensed chart ledger, and 4-layer clinical KB findings client-side (`buildLiveWahsMessages`).
2. **Cloud Run Relay (`wahs/gpu-auth-relay/app.py`):**
   - Verifies the caller's Google OAuth / Firebase token against Google's token verification endpoints and checks `email.lower()` against `WAHS_AUTH_WHITELIST_EMAILS`.
   - Returns `401` if unauthenticated or `403` if the Google account is not on the whitelist.
   - Attaches `Authorization: Bearer ${WAHS_GPU_API_KEY}` server-side and forwards `/v1/models` and `/v1/chat/completions` (SSE streaming and non-streaming) to `https://llm.co.dev.cirg.uw.edu`.

## Environment Variables

| Variable | Description | Default |
| --- | --- | --- |
| `WAHS_GPU_BASE_URL` | Upstream UW CIRG LiteLLM base URL | `https://llm.co.dev.cirg.uw.edu` |
| `WAHS_GPU_API_KEY` | Upstream LiteLLM bearer key (required in Cloud Run; never committed to git) | *(none)* |
| `WAHS_AUTH_WHITELIST_EMAILS` | Comma-separated whitelisted Google account emails | `piotr.mankowski@gmail.com,pmanko@uw.edu,ivanc@uw.edu,mcjustin@uw.edu,jflow2@uw.edu,lober@uw.edu,ibacher@uw.edu` |
| `WAHS_GOOGLE_CLIENT_ID` | Google OAuth 2.0 Web Client ID | `1043771833056-41q5npi9me4i390i87b2tha58rt5blb9.apps.googleusercontent.com` |
| `WAHS_GPU_MODELS` | Comma-separated Ollama models pulled on the UW GPU server | `ollama/gemma4:12b,ollama/gemma4:e4b,ollama/gemma4:e2b,ollama/mistral:7b,ollama/smollm2:latest` |

## Deployment (Google Cloud Run on `clinical-ai-harness`)

```bash
gcloud run deploy wahs-gpu-auth-relay \
  --source wahs/gpu-auth-relay \
  --region us-west1 \
  --project clinical-ai-harness \
  --allow-unauthenticated \
  --set-env-vars="^;^WAHS_GPU_BASE_URL=https://llm.co.dev.cirg.uw.edu;WAHS_GPU_API_KEY=${WAHS_GPU_API_KEY};WAHS_AUTH_WHITELIST_EMAILS=piotr.mankowski@gmail.com,pmanko@uw.edu,ivanc@uw.edu,mcjustin@uw.edu,jflow2@uw.edu,lober@uw.edu,ibacher@uw.edu"
```
