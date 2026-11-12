"""Behavior of scripts/publish-landing.sh with every cloud and network command stubbed.

The script runs against a small synthetic landing tree so expectations come from the
fixture, not from current site content. Stubs record each invocation in order; the
tests assert what the script does (clean-tree & fast-forward checks before mutation,
isolated branch previews, what it syncs, which remote service it restarts, what it
verifies), never the script's text.
"""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
MEDIA = 'https://storage.googleapis.com/openclinai-media/catalyst/'
FULL_SITE = 'full.example.invalid'
LANDING_ONLY_SITE = 'landing.example.invalid'
REAL_GIT = shutil.which('git') or '/usr/bin/git'

STUBS = {
    'python3': '''import os, sys
log(['python3', *sys.argv[1:]])
if os.environ.get('FAIL_CHECKS') == '1' and 'pytest' in sys.argv: raise SystemExit(1)
''',
    'gcloud': '''import os, sys
log(['gcloud', *sys.argv[1:]])
args = ' '.join(sys.argv[1:])
if '--format=value(name)' in args: print('test-vm')
elif '--format=value(status)' in args: print(os.environ.get('VM_STATUS', 'RUNNING'))
elif 'natIP' in args: print('192.0.2.1')
else: raise SystemExit('unexpected gcloud call: ' + args)
''',
    'ssh': '''import os, sys
log(['ssh', *sys.argv[1:]])
cmd = sys.argv[-1]
if 'mkdir /tmp/openclinai-publish-landing.lock' in cmd and os.environ.get('LOCK_HELD') == '1':
    raise SystemExit(1)
if 'cat openclinai.org/.landing-deploy-receipt.json' in cmd and os.environ.get('REMOTE_RECEIPT_JSON'):
    print(os.environ['REMOTE_RECEIPT_JSON'])
''',
    'rsync': '''import os, sys
log(['rsync', *sys.argv[1:]])
if '--itemize-changes' in sys.argv and os.environ.get('CONFIG_CHANGED') == '1': print('>f+++++++++ Caddyfile')
''',
    'curl': '''import os, sys
from pathlib import Path
log(['curl', *sys.argv[1:]])
url = next(arg for arg in sys.argv if arg.startswith('https://'))
if url.startswith(('https://catalyst.openelis-global.org/', 'https://storage.googleapis.com/')):
    raise SystemExit('publication must not depend on the demo host or the media bucket')
if '-o' not in sys.argv:
    relative = url.split('/', 3)[3]
    body = (Path(os.environ['TEST_ROOT']) / 'landing' / relative).read_bytes()
    if relative == os.environ.get('STALE_PAGE'): body += b'stale'
    sys.stdout.buffer.write(body)
''',
    'git': f'''import os, sys
log(['git', *sys.argv[1:]])
joined = ' '.join(sys.argv[1:])
for forbidden in ('submodule', 'targets/', 'openmrs'):
    if forbidden in joined:
        raise SystemExit('publication must not inspect product gitlinks: ' + joined)
os.execv({REAL_GIT!r}, [{REAL_GIT!r}, *sys.argv[1:]])
''',
    'docker': 'raise SystemExit("publication must not run local containers")\n',
}
LOGGER = '''import json, os
def log(argv):
    with open(os.environ['TEST_LOG'], 'a') as handle: handle.write(json.dumps(argv) + '\\n')
'''


def git_run(cwd: Path, *args: str) -> str:
    env = {
        **os.environ,
        'GIT_AUTHOR_NAME': 'Test',
        'GIT_AUTHOR_EMAIL': 'test@example.invalid',
        'GIT_COMMITTER_NAME': 'Test',
        'GIT_COMMITTER_EMAIL': 'test@example.invalid',
    }
    res = subprocess.run([REAL_GIT, *args], cwd=cwd, check=True, capture_output=True, text=True, env=env)
    return res.stdout.strip()


def write_landing(root: Path) -> list[str]:
    """A minimal site: two pages referencing three media assets, a stylesheet, a sitemap."""
    pages = {
        'index.html': f'<video poster="{MEDIA}a-poster.jpg"><source src="{MEDIA}a.mp4"></video>',
        'catalyst/questions/index.html': f'<a href="{MEDIA}clips/b.mp4">clip</a>',
        'styles.css': 'body { margin: 0; }',
        'sitemap.xml': '<urlset/>',
    }
    for relative, body in pages.items():
        (root / 'landing' / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / 'landing' / relative).write_text(body)
    return sorted(pages)


@pytest.fixture
def publisher(tmp_path):
    origin = tmp_path / 'origin.git'
    origin.mkdir()
    git_run(origin, 'init', '--bare', '-b', 'main')

    repo = tmp_path / 'repo'
    repo.mkdir()
    git_run(repo, 'init', '-b', 'main')
    git_run(repo, 'remote', 'add', 'origin', str(origin))
    (repo / '.gitignore').write_text('.env.*\ntest-key\nbin/\ncalls.jsonl\n')

    scripts = repo / 'scripts'
    scripts.mkdir()
    for name in ('publish-landing.sh', 'cloud-lib.sh'):
        shutil.copy2(ROOT / 'scripts' / name, scripts / name)
    published = write_landing(repo)
    shutil.copytree(ROOT / 'compose/website', repo / 'compose/website')
    git_run(repo, 'add', '.')
    git_run(repo, 'commit', '-m', 'Initial site')
    git_run(repo, 'push', '-u', 'origin', 'main')

    env_file = repo / '.env.website'
    env_file.write_text(f'CADDY_SITE={FULL_SITE}\n')
    key = repo / 'test-key'
    key.write_text('stub only')
    binaries = repo / 'bin'
    binaries.mkdir()
    for name, body in STUBS.items():
        binary = binaries / name
        binary.write_text(f'#!{sys.executable}\n' + LOGGER + body)
        binary.chmod(0o755)
    log = repo / 'calls.jsonl'

    def run(*args, **conditions):
        log.unlink(missing_ok=True)
        result = subprocess.run(
            ['/bin/bash', str(scripts / 'publish-landing.sh'), *args],
            cwd=repo, capture_output=True, text=True,
            env={**os.environ, 'PATH': f'{binaries}:/usr/bin:/bin',
                 'GCP_SSH_USER': 'test-user', 'GCP_SSH_KEY': str(key),
                 'GCP_REMOTE_REPO': 'openclinai.org', 'CADDY_SITE': LANDING_ONLY_SITE,
                 'TEST_ROOT': str(repo), 'TEST_LOG': str(log),
                 **{name: str(value) for name, value in conditions.items()}},
        )

        calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
        return result, calls

    run.published = published
    run.env_file = env_file
    run.repo = repo
    run.origin = origin
    return run


def commands(calls, name):
    return [call for call in calls if call[0] == name]


def remote_mutations(calls):
    return commands(calls, 'ssh') + commands(calls, 'rsync')


def fetched_urls(calls):
    return [next(arg for arg in call if arg.startswith('https://')) for call in commands(calls, 'curl')]


def compose_command(calls):
    """Return the tokens of the remote `docker compose ... up` invocation."""
    remote = [call[-1] for call in commands(calls, 'ssh') if 'docker compose' in call[-1]]
    assert len(remote) == 1, remote
    return shlex.split(remote[0].split('&&')[-1])


def test_full_publication_syncs_and_restarts_only_the_proxy(publisher):
    result, calls = publisher(CONFIG_CHANGED=1)
    assert result.returncode == 0, result.stdout + result.stderr

    landing_sync = [call for call in commands(calls, 'rsync') if call[-1].endswith(':openclinai.org/landing/')]
    assert len(landing_sync) == 1 and '--delete' in landing_sync[0]
    config_sync = [call for call in commands(calls, 'rsync') if '--itemize-changes' in call]
    assert {Path(arg).name for arg in config_sync[0][-4:-1]} == {'Caddyfile', 'services.yml', '.env.website'}

    up = compose_command(calls)
    assert up[up.index('--project-name') + 1] == 'openclinai-website'
    assert [token for token in up[up.index('up') + 1:] if not token.startswith('-')] == ['proxy']
    assert '--no-deps' in up and '--force-recreate' in up

    verified = {url.split('/', 3)[3] for url in fetched_urls(calls) if url.startswith(f'https://{FULL_SITE}/')}
    assert set(publisher.published) <= verified


def test_unchanged_configuration_starts_the_proxy_without_recreating_it(publisher):
    result, calls = publisher(CONFIG_CHANGED=0)
    assert result.returncode == 0, result.stdout + result.stderr
    up = compose_command(calls)
    assert [token for token in up[up.index('up') + 1:] if not token.startswith('-')] == ['proxy']
    assert '--force-recreate' not in up


def test_landing_only_syncs_pages_and_never_touches_proxy_configuration(publisher):
    publisher.env_file.unlink()
    result, calls = publisher('--landing-only')
    assert result.returncode == 0, result.stdout + result.stderr
    assert all('compose/' not in ' '.join(call) for call in remote_mutations(calls))
    assert all('docker' not in ' '.join(call) for call in commands(calls, 'ssh'))
    verified = {url.split('/', 3)[3] for url in fetched_urls(calls) if url.startswith(f'https://{LANDING_ONLY_SITE}/')}
    assert set(publisher.published) <= verified


def test_failed_landing_checks_abort_before_any_network_or_remote_call(publisher):
    result, calls = publisher(FAIL_CHECKS=1)
    assert result.returncode != 0
    assert not commands(calls, 'curl') and not remote_mutations(calls)


def test_full_publication_requires_the_website_environment_before_mutating(publisher):
    publisher.env_file.unlink()
    result, calls = publisher()
    assert result.returncode != 0
    assert not remote_mutations(calls)


def test_stopped_vm_aborts_before_any_remote_mutation(publisher):
    result, calls = publisher(VM_STATUS='TERMINATED')
    assert result.returncode != 0
    assert not remote_mutations(calls)


def test_a_stale_live_page_fails_publication(publisher):
    result, _ = publisher(STALE_PAGE='catalyst/questions/index.html')
    assert result.returncode != 0


def test_unknown_mode_is_rejected_without_side_effects(publisher):
    result, calls = publisher('--everything')
    assert result.returncode == 2
    assert calls == []


def test_dirty_landing_tree_aborts_production_publish_before_remote_calls(publisher):
    (publisher.repo / 'landing' / 'untracked.html').write_text('<p>draft</p>')
    result, calls = publisher('--landing-only')
    assert result.returncode != 0
    assert not remote_mutations(calls) and not commands(calls, 'curl')


def test_feature_branch_aborts_production_publish_without_force(publisher):
    git_run(publisher.repo, 'checkout', '-b', 'feature/hero-copy')
    (publisher.repo / 'landing' / 'styles.css').write_text('body { margin: 1px; }')
    git_run(publisher.repo, 'add', 'landing/styles.css')
    git_run(publisher.repo, 'commit', '-m', 'Update styles on branch')

    refused, calls = publisher('--landing-only')
    assert refused.returncode != 0
    assert '--preview' in refused.stderr
    assert not remote_mutations(calls)

    forced, forced_calls = publisher('--landing-only', '--force')
    assert forced.returncode == 0, forced.stdout + forced.stderr
    assert any(call[-1].endswith(':openclinai.org/landing/') for call in commands(forced_calls, 'rsync'))


def test_stale_main_behind_origin_aborts_production_publish(publisher, tmp_path):
    peer = tmp_path / 'peer'
    git_run(tmp_path, 'clone', str(publisher.origin), str(peer))
    (peer / 'landing' / 'styles.css').write_text('body { color: #111; }')
    git_run(peer, 'add', 'landing/styles.css')
    git_run(peer, 'commit', '-m', 'Upstream main commit')
    git_run(peer, 'push', 'origin', 'main')

    result, calls = publisher('--landing-only')
    assert result.returncode != 0
    assert not remote_mutations(calls)


def test_remote_receipt_divergence_aborts_clobber_unless_forced(publisher):
    diverged_receipt = json.dumps({
        'commit': 'deadbeef' * 5,
        'branch': 'sibling-pr',
        'deployed_at': '2026-11-11T00:00:00Z',
    })
    refused, calls = publisher('--landing-only', REMOTE_RECEIPT_JSON=diverged_receipt)
    assert refused.returncode != 0
    assert not commands(calls, 'rsync') and not commands(calls, 'curl')

    forced, forced_calls = publisher('--landing-only', '--force', REMOTE_RECEIPT_JSON=diverged_receipt)
    assert forced.returncode == 0, forced.stdout + forced.stderr
    assert commands(forced_calls, 'rsync')


def test_remote_receipt_ancestor_allows_fast_forward_and_writes_new_receipt(publisher):
    ancestor_sha = git_run(publisher.repo, 'rev-parse', 'HEAD')
    (publisher.repo / 'landing' / 'styles.css').write_text('body { padding: 0; }')
    git_run(publisher.repo, 'add', 'landing/styles.css')
    git_run(publisher.repo, 'commit', '-m', 'Advance main')
    git_run(publisher.repo, 'push', 'origin', 'main')
    head_sha = git_run(publisher.repo, 'rev-parse', 'HEAD')

    receipt = json.dumps({'commit': ancestor_sha, 'branch': 'main', 'deployed_at': '2026-11-10T00:00:00Z'})
    result, calls = publisher('--landing-only', REMOTE_RECEIPT_JSON=receipt)
    assert result.returncode == 0, result.stdout + result.stderr

    receipt_writes = [
        call[-1] for call in commands(calls, 'ssh')
        if '.landing-deploy-receipt.json.tmp' in call[-1]
    ]
    assert len(receipt_writes) == 1
    assert head_sha in receipt_writes[0]


def test_concurrent_remote_lock_aborts_before_rsync(publisher):
    result, calls = publisher('--landing-only', LOCK_HELD=1)
    assert result.returncode != 0
    assert not commands(calls, 'rsync') and not commands(calls, 'curl')


def test_preview_mode_publishes_isolated_subdomain_from_feature_branch_even_when_dirty(publisher):
    git_run(publisher.repo, 'checkout', '-b', 'feature/new-layout')
    (publisher.repo / 'landing' / 'styles.css').write_text('body { background: #fff; }')
    demo_dir = publisher.repo / 'wahs' / 'demo'
    demo_dir.mkdir(parents=True)
    (demo_dir / 'index.html').write_text('<h1>Demo preview</h1>')

    result, calls = publisher('--preview', 'new-layout')
    assert result.returncode == 0, result.stdout + result.stderr

    rsync_targets = [call[-1] for call in commands(calls, 'rsync')]
    assert rsync_targets == [
        f'test-user@192.0.2.1:openclinai.org/artifacts/previews/new-layout-preview.{FULL_SITE}/',
        f'test-user@192.0.2.1:openclinai.org/artifacts/previews/new-layout-preview-demo.{FULL_SITE}/',
    ]
    assert all(':openclinai.org/landing/' not in target for target in rsync_targets)
    assert all('.landing-deploy-receipt.json' not in call[-1] for call in commands(calls, 'ssh'))
    assert all('docker' not in call[-1] for call in commands(calls, 'ssh'))

    verified = {
        url.split('/', 3)[3]
        for url in fetched_urls(calls)
        if url.startswith(f'https://new-layout-preview.{FULL_SITE}/')
    }
    assert set(publisher.published) <= verified


def test_preview_slugs_feature_and_feature_demo_use_disjoint_remote_directories(publisher):
    demo_dir = publisher.repo / 'wahs' / 'demo'
    demo_dir.mkdir(parents=True)
    (demo_dir / 'index.html').write_text('<h1>Demo preview</h1>')

    res_a, calls_a = publisher('--preview', 'feature')
    res_b, calls_b = publisher('--preview', 'feature-demo')
    assert res_a.returncode == 0 and res_b.returncode == 0

    targets_a = {call[-1] for call in commands(calls_a, 'rsync')}
    targets_b = {call[-1] for call in commands(calls_b, 'rsync')}
    assert len(targets_a) == 2 and len(targets_b) == 2
    assert targets_a.isdisjoint(targets_b)


@pytest.mark.parametrize('bad_args', [
    ('--preview',),
    ('--preview', '../escape'),
    ('--preview', 'UpperCase'),
    ('--preview', '-leading'),
    ('--preview', 'valid-slug', '--force'),
    ('--landing-only', '--preview', 'valid-slug'),
])
def test_invalid_preview_arguments_are_rejected_without_side_effects(publisher, bad_args):
    result, calls = publisher(*bad_args)
    assert result.returncode == 2
    assert calls == []


def test_publication_never_runs_local_docker_or_product_deployment(publisher):
    """Invariant: landing publication is independent of product checkouts and deployment."""
    result, calls = publisher(CONFIG_CHANGED=1)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not commands(calls, 'docker')
    for call in calls:
        joined = ' '.join(call)
        assert 'targets/' not in joined
        assert 'submodule' not in joined
        assert 'openmrs-2.8-refapp' not in joined


def test_static_proxy_restarts_after_docker_or_host_reboot():
    """Requirement: the website proxy comes back on its own after a reboot."""
    compose = yaml.safe_load((ROOT / 'compose/website/services.yml').read_text())
    assert compose['services']['proxy']['restart'] == 'unless-stopped'
