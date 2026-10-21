#!/usr/bin/env python3
"""Collect a pull request, its linked tickets and every review thread into JSON.

  threads.py <owner/name> <pr> <out.json> [--until ISO-8601]

`--until` drops every comment made after that instant, so a reviewer can be measured
against a round it has not seen. The PR a closed one named as its replacement ("replaced
by #<pr>" in a closing comment) contributes its threads under "previous": the asks a
maintainer made on the earlier PR are part of this one's review.
"""
import json
import re
import subprocess
import sys

QUERY = """query($owner:String!,$name:String!,$pr:Int!){repository(owner:$owner,name:$name){
 pullRequest(number:$pr){number title body url author{login} baseRefName headRefName
  headRefOid state closingIssuesReferences(first:10){nodes{number title body url}}
  comments(first:100){nodes{author{login} createdAt body url}}
  reviewThreads(first:100){nodes{id isResolved isOutdated path line originalLine
   comments(first:100){nodes{author{login} createdAt body url}}}}}}}"""


def collect(slug: str, pr: int) -> dict:
    owner, name = slug.split("/")
    out = subprocess.run(["gh", "api", "graphql", "-f", f"query={QUERY}", "-F",
                          f"owner={owner}", "-F", f"name={name}", "-F", f"pr={pr}"],
                         capture_output=True, text=True, check=True).stdout
    p = json.loads(out)["data"]["repository"]["pullRequest"]
    author = p["author"]["login"]

    def comments(nodes):
        return [{"by": c["author"]["login"] if c["author"] else None, "at": c["createdAt"],
                 "body": c["body"], "url": c["url"]} for c in nodes]

    threads = []
    for t in p["reviewThreads"]["nodes"]:
        cs = comments(t["comments"]["nodes"])
        threads.append({"id": t["id"], "path": t["path"], "line": t["line"] or t["originalLine"],
                        "resolved": t["isResolved"], "outdated": t["isOutdated"],
                        "url": cs[0]["url"] if cs else None,
                        "awaiting_reply": bool(cs) and not t["isResolved"] and cs[-1]["by"] != author,
                        "comments": cs})
    return {"repo": slug, "pr": p["number"], "title": p["title"], "body": p["body"],
            "url": p["url"], "author": author, "state": p["state"], "base": p["baseRefName"],
            "head_branch": p["headRefName"], "head": p["headRefOid"],
            "tickets": p["closingIssuesReferences"]["nodes"],
            "conversation": comments(p["comments"]["nodes"]), "threads": threads}


def filter_until(data: dict, until: str | None) -> dict:
    """The PR as it stood at `until`: later comments, and threads opened later, are dropped."""
    if not until:
        return data
    data = dict(data)
    data["conversation"] = [c for c in data["conversation"] if c["at"] <= until]
    threads = []
    for t in data["threads"]:
        cs = [c for c in t["comments"] if c["at"] <= until]
        if cs:
            threads.append(dict(t, comments=cs, resolved=False if len(cs) < len(t["comments"]) else t["resolved"]))
    data["threads"] = threads
    data["until"] = until
    return data


def superseded_prs(slug: str, pr: int) -> list[int]:
    """Closed PRs of the repository whose last comment names this one as their replacement."""
    out = subprocess.run(["gh", "pr", "list", "-R", slug, "--state", "closed", "--limit", "80",
                          "--json", "number,comments"], capture_output=True, text=True)
    if out.returncode:
        return []
    previous = []
    for p in json.loads(out.stdout):
        bodies = " ".join(c.get("body", "") for c in p.get("comments", []))
        if re.search(rf"[Rr]eplaced by #{pr}\b", bodies) and p["number"] != pr:
            previous.append(p["number"])
    return sorted(previous)


def with_previous(data: dict, previous: list[dict]) -> dict:
    """Attach the superseded PRs' threads; a reviewer reads their asks as this PR's."""
    data = dict(data)
    data["previous"] = [{"pr": p["pr"], "url": p["url"], "title": p["title"],
                         "threads": p["threads"]} for p in previous]
    return data


if __name__ == "__main__":
    until = sys.argv[sys.argv.index("--until") + 1] if "--until" in sys.argv else None
    slug, pr, out_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    data = filter_until(collect(slug, pr), until)
    data = with_previous(data, [filter_until(collect(slug, n), until) for n in superseded_prs(slug, pr)])
    with open(out_path, "w") as fh:
        json.dump(data, fh, indent=1)
    waiting = sum(t["awaiting_reply"] for t in data["threads"])
    carried = sum(len(p["threads"]) for p in data["previous"])
    print(f"{data['repo']}#{data['pr']}: {len(data['threads'])} threads, {waiting} awaiting a reply, "
          f"{carried} carried from {[p['pr'] for p in data['previous']]}")
