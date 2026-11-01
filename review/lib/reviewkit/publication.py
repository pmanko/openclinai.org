"""Update existing review bodies with optimistic concurrency and retry safety."""
import hashlib


def digest(body):
    return hashlib.sha256(body.encode()).hexdigest()


def apply_updates(entries, api, *, authorized=False):
    if not authorized:
        raise ValueError('Explicit publication authorization is required')
    login = api('user')['login']
    def inspect(entry):
        prefix = f'repos/{entry["repo"]}/pulls/{entry["pr"]}'
        pr = api(prefix)
        if pr['state'] != 'open' or pr['head']['sha'] != entry['head'] or pr['base']['sha'] != entry['base']:
            raise ValueError('PR head or base changed; rebuild the consolidation plan')
        path = f'{prefix}/reviews/{entry["review_id"]}'
        review = api(path)
        if review['user']['login'] != login or review['state'] != 'COMMENTED':
            raise ValueError('Only your existing comment reviews may be consolidated')
        if digest(entry['body']) != entry['body_sha256']:
            raise ValueError('Planned body was modified')
        if review['body'] != entry['body'] and digest(review['body']) != entry['expected_body_sha256']:
            raise ValueError('Existing review changed; inspect before overwriting')
        return path, review
    # Validate the entire batch before the first write, then each item again.
    targets = [(entry['repo'], entry['pr'], entry['review_id']) for entry in entries]
    if len(targets) != len(set(targets)):
        raise ValueError('Duplicate review target in publication batch')
    for entry in entries:
        inspect(entry)
    receipts = []
    for entry in entries:
        path, review = inspect(entry)
        reused = review['body'] == entry['body']
        if not reused:
            # On an ambiguous network result the next run reads before writing.
            api(path, method='PUT', body={'body': entry['body']})
        check = api(path)
        if check['body'] != entry['body'] or check['id'] != entry['review_id']:
            raise ValueError('Review update readback failed')
        receipts.append(dict(repo=entry['repo'], pr=entry['pr'], id=check['id'],
                             url=check['html_url'], sha256=digest(check['body']), reused=reused))
    return receipts
