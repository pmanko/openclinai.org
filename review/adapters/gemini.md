# gemini

Run a review with `make review PR=<n> REPO=<repo> AGENT=gemini [EFFORT=] [ROUNDS=] [STACK=1]`
from the umbrella root. Each role is a fresh `gemini -p` session started by
`review/bin/role.sh` with its brief from `review/briefs/`; answers and round records
land in `work/review/<repo>-<pr>/`. Working in a component checkout yourself, follow
`review/briefs/fixer.md` and let the git hooks in `review/hooks/` probe your push.
