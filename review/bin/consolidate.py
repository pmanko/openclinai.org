#!/usr/bin/env python3
"""Validate a curated stack manifest, or publish a previously inspected update plan."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from reviewkit.stack import canonical_links, consolidate, render
from reviewkit.publication import apply_updates


def api(path, method='GET', body=None):
    command = ['gh', 'api', path, '--method', method]
    if body is not None:
        command += ['--input', '-']
    result = subprocess.run(command, input=json.dumps(body) if body is not None else None,
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'apply'])
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--authorize-publication', action='store_true')
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    if args.action == 'plan':
        manifests = data.get('repositories', [data])
        plans = [consolidate(m['repository'], Path(m['checkout']), m['layers'], m['occurrences'], m['decisions']) for m in manifests]
        urls = {(m['repository'], int(k)): v for m in manifests for k, v in m['review_urls'].items()}
        links = canonical_links(plans, urls)
        for plan in plans:
            plan['bodies'] = render(plan, {n: url for (repo, n), url in urls.items() if repo == plan['repository']}, links)
        result = {'plans': plans} if 'repositories' in data else plans[0]
    else:
        result = apply_updates(data, api, authorized=args.authorize_publication)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
