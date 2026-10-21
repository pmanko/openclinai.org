#!/usr/bin/env python3
"""Collect a pull request, its linked tickets and every review thread into JSON.

  threads.py <owner/name> <pr> <out.json>
"""
import json
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


if __name__ == "__main__":
    data = collect(sys.argv[1], int(sys.argv[2]))
    with open(sys.argv[3], "w") as fh:
        json.dump(data, fh, indent=1)
    waiting = sum(t["awaiting_reply"] for t in data["threads"])
    print(f"{data['repo']}#{data['pr']}: {len(data['threads'])} threads, {waiting} awaiting a reply")
