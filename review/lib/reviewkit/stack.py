"""Canonical stack issues. Semantic identity is reviewed, never guessed from prose."""
from __future__ import annotations

import functools
import hashlib
import json
import re
import subprocess
from pathlib import Path


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def ancestor(repo: Path, older: str, newer: str) -> bool:
    result = subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', older, newer], capture_output=True)
    if result.returncode not in (0, 1):
        raise ValueError('Cannot establish commit ancestry')
    return result.returncode == 0


def issue_id(repository: str, key: str) -> str:
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,99}', key):
        raise ValueError('issue_key must be a stable root-cause name')
    return 'issue-' + hashlib.sha256((repository + ':' + key).encode()).hexdigest()[:16]


def consolidate(repository: str, repo: Path, layers: list[dict], occurrences: list[dict], decisions: list[dict]) -> dict:
    """Validate explicit root-cause groups and assign one owner per issue.

    A decision must account for every observation exactly once. Git validates the
    proposed introduction and publication membership; it cannot decide semantic
    equivalence. Baseline issues and unresolved attribution are never charged to
    the first open PR. Only observed affected revisions receive inherited links.
    """
    @functools.lru_cache(None)
    def revision_ancestors(revision):
        return set(git(repo, 'rev-list', revision).splitlines())

    def contains(older, newer):
        return older in revision_ancestors(newer)

    @functools.lru_cache(None)
    def introduction(revision):
        resolved = git(repo, 'rev-parse', '--verify', revision + '^{commit}')
        files = git(repo, 'diff-tree', '--root', '--no-commit-id', '--name-only', '-r', resolved).splitlines()
        return resolved, files

    by_pr = {p['number']: p for p in layers}
    if len(by_pr) != len(layers) or not layers:
        raise ValueError('Duplicate or empty layer snapshot')
    by_id = {o['id']: o for o in occurrences}
    if len(by_id) != len(occurrences):
        raise ValueError('Duplicate occurrence identity')
    for o in occurrences:
        if o['pr'] not in by_pr or o['head'] != by_pr[o['pr']]['head']:
            raise ValueError('Occurrence is stale or outside the snapshot')
    consumed = set()
    keys = set()
    issues = []
    for decision in decisions:
        key = decision['issue_key']
        uid = issue_id(repository, key)
        if key in keys:
            raise ValueError('Root cause appears in more than one group')
        keys.add(key)
        ids = decision['occurrences']
        if not ids or len(ids) != len(set(ids)) or consumed.intersection(ids) or not set(ids).issubset(by_id):
            raise ValueError('Missing, duplicate or unknown occurrence in grouping')
        consumed.update(ids)
        members = [by_id[i] for i in ids]
        status = decision.get('status', 'open')
        if status not in ('open', 'baseline', 'unattributed', 'resolved', 'reference'):
            raise ValueError('Invalid issue status')
        rationale = decision.get('origin_evidence', '').strip()
        if not rationale:
            raise ValueError('Ownership requires inspected introduction evidence')
        owner = decision.get('owner_pr')
        intro = decision.get('introduced_commit')
        origin_file = decision.get('origin_file')
        if status in ('open', 'baseline'):
            if not intro or not origin_file:
                raise ValueError('Missing introducing commit or source path')
            intro, changed = introduction(intro)
            # The named source must actually change in the attributed commit.
            if origin_file not in changed:
                raise ValueError('Introducing commit does not change the origin file')
            eligible = [p for p in layers if contains(intro, p['head']) and not contains(intro, p['base'])]
            if status == 'open':
                if owner not in {p['number'] for p in eligible}:
                    raise ValueError('Owner does not introduce this commit relative to its base')
                # Explicit ancestry takes precedence over PR creation order. A
                # subsequently amended lower PR can have a divergent head; the
                # introduction remains shared, so creation order breaks that tie.
                candidates = [p for p in eligible if not any(q['number'] != p['number'] and
                              q['head'] != p['head'] and contains(q['head'], p['head']) for q in eligible)]
                earliest = min(candidates, key=lambda p: (p.get('created_at', ''), p['number']))
                if owner != earliest['number']:
                    raise ValueError(f'Issue belongs to earlier PR #{earliest["number"]}')
            elif owner is not None or eligible:
                raise ValueError('Baseline attribution conflicts with an open introducing PR')
            for member in members:
                if not contains(intro, member['head']):
                    raise ValueError('Affected revision does not contain the introduction; inspect copies separately')
        elif owner is not None:
            raise ValueError('Unattributed/resolved issues cannot acquire a new owner')
        tracking = decision.get('tracking_pr')
        if tracking is not None and (tracking not in {m['pr'] for m in members} or status not in ('baseline', 'unattributed')):
            raise ValueError('Tracking location must be an observed PR, not claimed ownership')
        reference = decision.get('canonical_reference')
        if status == 'reference' and not reference:
            raise ValueError('Cross-repository reference requires a canonical target')
        blocking = any(m['finding'].get('blocking') for m in members)
        for m in members:
            if m['finding'].get('blocking') and not (m['finding'].get('evidence') and m['finding'].get('failure_mode')):
                raise ValueError('Blocking observation lacks reproduction evidence')
        issues.append(dict(id=uid, issue_key=key, title=decision['title'], status=status,
                           owner_pr=owner, tracking_pr=tracking, canonical_reference=reference, introduced_commit=intro, origin_file=origin_file,
                           origin_evidence=rationale, blocking=blocking, occurrences=members,
                           affected_prs=sorted({m['pr'] for m in members}),
                           regression_of=decision.get('regression_of')))
    if consumed != set(by_id):
        raise ValueError('Every observation needs an explicit disposition')
    all_keys = {i['issue_key']: i for i in issues}
    for issue in issues:
        previous = issue['regression_of']
        if previous:
            if previous not in all_keys or previous == issue['issue_key'] or issue['introduced_commit'] == all_keys[previous]['introduced_commit']:
                raise ValueError('A regression needs its own introducing change and prior issue')
    return dict(schema_version='stack_review.v1', repository=repository, layers=layers, issues=issues,
                unique_blockers=sum(i['blocking'] and i['status'] == 'open' for i in issues),
                unique_questions=sum(not i['blocking'] and i['status'] == 'open' for i in issues),
                attribution_pending=sum(i['status'] == 'unattributed' for i in issues))


def render(plan: dict, review_urls: dict[int, str], canonical_urls: dict[str, str] | None = None) -> dict[int, str]:
    """Full issue text only on its owner; affected peers get canonical links."""
    bodies = {}
    canonical_urls = canonical_urls or {}
    slug = plan['repository']
    for layer in plan['layers']:
        pr = layer['number']
        owned = [i for i in plan['issues'] if i['status'] == 'open' and i['owner_pr'] == pr]
        inherited = [i for i in plan['issues'] if i['status'] == 'open' and i['owner_pr'] != pr and pr in i['affected_prs']]
        other = [i for i in plan['issues'] if i['status'] != 'open' and pr in i['affected_prs']]
        lines = [f'<!-- openclinai-stack-review:{slug}#{pr} -->', '## Consolidated source review',
                 f'Examined snapshot: `{layer["head"]}`; base `{layer["base"]}`.', '',
                 f'**Owned here: {sum(i["blocking"] for i in owned)} blockers, {sum(not i["blocking"] for i in owned)} questions.** '
                 f'Inherited references: {len(inherited)}. These are not additional defects.', '',
                 'This replaces the earlier repeated findings. Questions are not verified blockers. '
                 'A comment review is not approval or deployed acceptance. No product fixes were made during consolidation.']
        for issue in owned:
            lines += ['', f'### {issue["issue_key"]}', '**Blocking**' if issue['blocking'] else '**Question**', issue['title'],
                      f'Introduction: [{issue["introduced_commit"][:8]}](https://github.com/{slug}/commit/{issue["introduced_commit"]}). '+issue['origin_evidence']]
            # One actionable description, with evidence retained in the local ledger.
            occurrence = min(issue['occurrences'], key=lambda o: (not o['finding'].get('blocking'), o['pr'] != pr))
            f = occurrence['finding']
            lines += ['', f"Observed on #{occurrence['pr']} at `{occurrence['head']}`: "+f['finding']]
            location = f"https://github.com/{slug}/blob/{occurrence['head']}/{f['file']}#L{f['line']}"
            lines += [f"[Source location]({location})"]
            if occurrence.get('consumer_head'): lines += ['Supplied consumer revision: `'+occurrence['consumer_head']+'`.']
            if f.get('evidence'): lines += ['Evidence: '+f['evidence']]
            if f.get('suggestion'): lines += ['Requested change: '+f['suggestion']]
            threads = sorted({o['finding']['thread'] for o in issue['occurrences'] if o['finding'].get('thread')})
            if threads: lines += ['Existing discussions: '+', '.join(f'[thread {n+1}]({url})' for n,url in enumerate(threads))+'.']
            lines += ['', 'Known affected PRs: '+', '.join(f'#{p}' for p in issue['affected_prs'])+'.']
        if inherited:
            lines += ['', '### Inherited issues — follow the owning PR']
            for issue in inherited:
                if issue['owner_pr'] not in review_urls:
                    raise ValueError('Missing canonical review URL')
                lines += [f'- [{issue["issue_key"]}]({review_urls[issue["owner_pr"]]}): {issue["title"]} '
                          f'({"blocking" if issue["blocking"] else "question"}; owner #{issue["owner_pr"]}).']
        if other:
            lines += ['', '### Baseline, resolved or attribution pending']
            for issue in other:
                if issue['status'] == 'reference':
                    target = issue['canonical_reference']
                    if target not in canonical_urls: raise ValueError('Unresolved canonical cross-repository target')
                    lines += [f"- [{issue['title']}]({canonical_urls[target]}): same issue tracked in its introducing repository."]
                    continue
                tracking = issue.get('tracking_pr')
                if tracking is not None and tracking != pr:
                    if tracking not in review_urls: raise ValueError('Missing tracking review URL')
                    lines += [f"- [{issue['title']}]({review_urls[tracking]}): {issue['status']}; tracking location only, introduction is not assigned to this PR."]
                    continue
                lines += [f'- **{issue["status"]} — {issue["issue_key"]}:** {issue["title"]} '+issue['origin_evidence']]
                if tracking == pr:
                    f = issue['occurrences'][0]['finding']
                    lines += ['  '+f['finding']]
                    if f.get('evidence'): lines += ['  Evidence: '+f['evidence']]
        bodies[pr] = '\n'.join(lines)+'\n'
    return bodies


def merge_ledger(path: Path, plan: dict) -> None:
    """Serialize repository-wide identity updates; never infer absence is resolution."""
    import fcntl
    import os
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ledger = json.loads(path.read_text()) if path.exists() else {'repository': plan['repository'], 'issues': {}}
        if ledger['repository'] != plan['repository']:
            raise ValueError('Ledger repository mismatch')
        for issue in plan['issues']:
            previous = ledger['issues'].get(issue['issue_key'])
            if previous and previous['introduced_commit'] != issue['introduced_commit']:
                raise ValueError('Existing issue identity changed; reconcile the rebase or use a separate regression key')
            record = dict(issue)
            observations = {(o['pr'], o['head'], o['id']): o for o in (previous or {}).get('occurrences', [])}
            observations.update({(o['pr'], o['head'], o['id']): o for o in issue['occurrences']})
            record['occurrences'] = list(observations.values())
            ledger['issues'][issue['issue_key']] = record
        with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as output:
            json.dump(ledger, output, indent=2)
            temporary = output.name
        os.replace(temporary, path)


def canonical_links(plans: list[dict], review_urls: dict[tuple[str, int], str]) -> dict[str, str]:
    """Resolve cross-repository aliases only to an existing, owned issue."""
    issues = {p['repository']+':'+i['issue_key']: (p['repository'], i)
              for p in plans for i in p['issues']}
    links = {}
    for key, (repository, issue) in issues.items():
        if issue['status'] == 'open':
            target = (repository, issue['owner_pr'])
            if target not in review_urls:
                raise ValueError('Missing owning review URL')
            links[key] = review_urls[target]
    for _, issue in issues.values():
        if issue['status'] == 'reference' and issue['canonical_reference'] not in links:
            raise ValueError('Cross-repository target must be an owned issue, not an alias or missing issue')
    return links
