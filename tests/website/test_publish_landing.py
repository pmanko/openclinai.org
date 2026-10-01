"""Exercise publication modes with all cloud/network commands stubbed."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def publisher(tmp_path):
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    for name in ('publish-landing.sh', 'cloud-lib.sh'):
        shutil.copy2(ROOT / 'scripts' / name, scripts / name)
    shutil.copytree(ROOT / 'landing', tmp_path / 'landing')
    shutil.copytree(ROOT / 'compose/website', tmp_path / 'compose/website')
    (tmp_path / '.env.website').write_text('CADDY_SITE=website.example.invalid\n')
    key = tmp_path / 'test-key'
    key.write_text('stub only')
    binaries = tmp_path / 'bin'
    binaries.mkdir()
    trace = tmp_path / 'trace.txt'
    bodies = {
        'python3': 'import sys\nsys.exit(0)\n',
        'gcloud': '''import sys
args = ' '.join(sys.argv[1:])
if '--format=value(name)' in args: print('test-vm')
elif '--format=value(status)' in args: print('RUNNING')
elif '--format=value(networkInterfaces[0].accessConfigs[0].natIP)' in args: print('192.0.2.1')
else: raise SystemExit('unexpected gcloud call: ' + args)
''',
        'ssh': '''import os, sys
with open(os.environ['TEST_LOG'], 'a') as trace: trace.write('ssh ' + ' '.join(sys.argv[1:]) + '\\n')
''',
        'rsync': '''import os, sys
with open(os.environ['TEST_LOG'], 'a') as trace: trace.write('rsync ' + ' '.join(sys.argv[1:]) + '\\n')
if '--itemize-changes' in sys.argv and os.environ.get('CONFIG_CHANGED') == '1': print('>f+++++++++ Caddyfile')
''',
        'curl': '''import os, sys
from pathlib import Path
url = next(arg for arg in sys.argv if arg.startswith('https://'))
if os.environ.get('FAIL_MEDIA') == '1' and '/media/' in url and 'catalyst.openelis-global.org' in url: raise SystemExit(22)
if '-o' not in sys.argv:
    relative = url.split('website.example.invalid/', 1)[1]
    sys.stdout.buffer.write((Path(os.environ['TEST_ROOT']) / 'landing' / relative).read_bytes())
''',
        'git': 'raise SystemExit("publication must not resolve Git sources")\n',
        'docker': 'raise SystemExit("local product deployment must not run")\n',
    }
    for name, body in bodies.items():
        binary = binaries / name
        binary.write_text(f'#!{sys.executable}\n' + body)
        binary.chmod(0o755)

    def run(mode='full', fail_media=False, config_changed=True):
        result = subprocess.run(
            ['/bin/bash', str(scripts / 'publish-landing.sh'), mode],
            cwd=tmp_path, capture_output=True, text=True,
            env={**os.environ, 'PATH': f'{binaries}:/usr/bin:/bin',
                 'GCP_SSH_USER': 'test-user', 'GCP_SSH_KEY': str(key),
                 'GCP_REMOTE_REPO': 'openclinai.org',
                 'CADDY_SITE': 'website.example.invalid', 'TEST_ROOT': str(tmp_path),
                 'TEST_LOG': str(trace), 'FAIL_MEDIA': str(int(fail_media)),
                                  'CONFIG_CHANGED': str(int(config_changed))},
        )
        return result, trace.read_text() if trace.exists() else ''
    return run


def test_full_publication_deploys_only_the_independent_static_proxy(publisher):
    result, trace = publisher()
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'compose/website/services.yml' in trace
    assert '--project-name openclinai-website' in trace
    assert 'up -d --no-deps --force-recreate proxy' in trace
    assert 'openmrs-2.8-refapp' not in trace
    assert 'HUB_BUILD_REVISION' not in trace
    assert 'targets/' not in trace
    assert result.stdout.rstrip().endswith('==> published: https://website.example.invalid/')


def test_unchanged_configuration_starts_the_proxy_without_forcing_recreation(publisher):
    result, trace = publisher(config_changed=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'proxy config unchanged; ensuring the proxy is running' in result.stdout
    assert 'up -d --no-deps proxy' in trace
    assert '--force-recreate' not in trace
    assert '--project-name openclinai-website' in trace
    assert 'openmrs-2.8-refapp' not in trace
    assert 'targets/' not in trace


def test_static_proxy_restarts_after_docker_or_host_reboot():
    compose = yaml.safe_load((ROOT / 'compose/website/services.yml').read_text())
    assert compose['services']['proxy']['restart'] == 'unless-stopped'
    assert set(compose['services']) == {'proxy'}


def test_landing_only_never_changes_proxy_configuration_or_services(publisher):
    result, trace = publisher('--landing-only')
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'rsync -avz --delete' in trace
    assert 'compose/' not in trace
    assert 'docker' not in trace


def test_missing_remote_media_aborts_before_any_upload_or_remote_mutation(publisher):
    result, trace = publisher(fail_media=True)
    assert result.returncode == 22, result.stdout + result.stderr
    assert trace == ''
    assert '==> published:' not in result.stdout
