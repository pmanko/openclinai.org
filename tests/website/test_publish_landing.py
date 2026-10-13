"""Behavior of scripts/publish-landing.sh with every cloud and network command stubbed.

The script runs against a small synthetic landing tree so expectations come from the
fixture, not from current site content. Stubs record each invocation in order; the
tests assert what the script does (checks before mutation, what it syncs, which
remote service it restarts, what it verifies), never the script's text.
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
MEDIA = 'https://catalyst.openelis-global.org/media/'
FIXTURE_MEDIA = {f'{MEDIA}a.mp4', f'{MEDIA}a-poster.jpg', f'{MEDIA}clips/b.mp4'}
FULL_SITE = 'full.example.invalid'
LANDING_ONLY_SITE = 'landing.example.invalid'

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
    'ssh': '''import sys
log(['ssh', *sys.argv[1:]])
''',
    'rsync': '''import os, sys
log(['rsync', *sys.argv[1:]])
if '--itemize-changes' in sys.argv and os.environ.get('CONFIG_CHANGED') == '1': print('>f+++++++++ Caddyfile')
''',
    'curl': '''import os, sys
from pathlib import Path
log(['curl', *sys.argv[1:]])
url = next(arg for arg in sys.argv if arg.startswith('https://'))
if os.environ.get('FAIL_MEDIA') == '1' and url.startswith('https://catalyst.openelis-global.org/media/'):
    raise SystemExit(22)
if '-o' not in sys.argv:
    relative = url.split('/', 3)[3]
    body = (Path(os.environ['TEST_ROOT']) / 'landing' / relative).read_bytes()
    if relative == os.environ.get('STALE_PAGE'): body += b'stale'
    sys.stdout.buffer.write(body)
''',
    'git': 'raise SystemExit("publication must not resolve Git sources")\n',
    'docker': 'raise SystemExit("publication must not run local containers")\n',
}
LOGGER = '''import json, os
def log(argv):
    with open(os.environ['TEST_LOG'], 'a') as handle: handle.write(json.dumps(argv) + '\\n')
'''


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
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    for name in ('publish-landing.sh', 'cloud-lib.sh'):
        shutil.copy2(ROOT / 'scripts' / name, scripts / name)
    published = write_landing(tmp_path)
    shutil.copytree(ROOT / 'compose/website', tmp_path / 'compose/website')
    env_file = tmp_path / '.env.website'
    env_file.write_text(f'CADDY_SITE={FULL_SITE}\n')
    key = tmp_path / 'test-key'
    key.write_text('stub only')
    binaries = tmp_path / 'bin'
    binaries.mkdir()
    for name, body in STUBS.items():
        binary = binaries / name
        binary.write_text(f'#!{sys.executable}\n' + LOGGER + body)
        binary.chmod(0o755)
    log = tmp_path / 'calls.jsonl'

    def run(mode='full', **conditions):
        log.unlink(missing_ok=True)
        result = subprocess.run(
            ['/bin/bash', str(scripts / 'publish-landing.sh'), *([mode] if mode else [])],
            cwd=tmp_path, capture_output=True, text=True,
            env={**os.environ, 'PATH': f'{binaries}:/usr/bin:/bin',
                 'GCP_SSH_USER': 'test-user', 'GCP_SSH_KEY': str(key),
                 'GCP_REMOTE_REPO': 'openclinai.org', 'CADDY_SITE': LANDING_ONLY_SITE,
                 'TEST_ROOT': str(tmp_path), 'TEST_LOG': str(log),
                 **{name: str(value) for name, value in conditions.items()}},
        )

        calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
        return result, calls

    run.published = published
    run.env_file = env_file
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


def test_full_publication_checks_media_first_then_syncs_and_restarts_only_the_proxy(publisher):
    result, calls = publisher(CONFIG_CHANGED=1)
    assert result.returncode == 0, result.stdout + result.stderr

    first_mutation = calls.index(remote_mutations(calls)[0])
    checked_before = {url for url in fetched_urls(calls[:first_mutation]) if url.startswith(MEDIA)}
    assert checked_before == FIXTURE_MEDIA

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


def test_missing_remote_media_aborts_before_any_upload_or_remote_mutation(publisher):
    result, calls = publisher(FAIL_MEDIA=1)
    assert result.returncode != 0
    assert not remote_mutations(calls)


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


def test_publication_never_runs_local_git_docker_or_product_deployment(publisher):
    """Invariant: landing publication is independent of product checkouts and deployment."""
    result, calls = publisher(CONFIG_CHANGED=1)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not commands(calls, 'git') and not commands(calls, 'docker')
    for call in calls:
        assert 'targets/' not in ' '.join(call)
        assert 'openmrs-2.8-refapp' not in ' '.join(call)


def test_static_proxy_restarts_after_docker_or_host_reboot():
    """Requirement: the website proxy comes back on its own after a reboot."""
    compose = yaml.safe_load((ROOT / 'compose/website/services.yml').read_text())
    assert compose['services']['proxy']['restart'] == 'unless-stopped'
