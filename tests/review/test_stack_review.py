"""Canonical issues follow introducing changes, not repeated wording or line numbers."""
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'review/lib'))
from reviewkit.stack import consolidate, merge_ledger, render


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


@pytest.fixture
def stack(tmp_path):
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'user.name', 'Fixture')
    git(tmp_path, 'config', 'user.email', 'fixture@example.test')
    def commit(value):
        (tmp_path / 'calc.py').write_text(value)
        git(tmp_path, 'add', '.')
        git(tmp_path, 'commit', '-qm', 'fixture')
        return git(tmp_path, 'rev-parse', 'HEAD')
    base = commit('def calculate(x): return x\n')
    one = commit('def calculate(x): return x / 0\n')
    two = commit('# line moved\ndef calculate(x): return x / 0\n')
    three = commit('# repaired\ndef calculate(x): return x\n')
    four = commit('# regression\ndef calculate(x): return x / 0\n')
    layers = [dict(number=i+1, head=h, base=base, created_at=str(i)) for i,h in enumerate([one,two,three,four])]
    f = dict(file='calc.py', line=1, finding='Zero denominator crashes.', blocking=True,
             failure_mode='Request raises ZeroDivisionError', evidence='calculate(1) raised ZeroDivisionError', suggestion='Use the intended denominator.')
    occurrences = [dict(id='a',pr=1,head=one,finding=f),dict(id='b',pr=2,head=two,finding={**f,'line':2,'finding':'A shifted line still divides by zero.'})]
    decision = dict(issue_key='zero-denominator',title='Zero denominator',owner_pr=1,
                    introduced_commit=one,origin_file='calc.py',origin_evidence='The introducing diff replaces x with x / 0.',occurrences=['a','b'])
    return tmp_path,layers,occurrences,decision,base


def plan(stack, decisions=None):
    repo,layers,observations,d,_=stack
    return consolidate('owner/repo',repo,layers,observations,decisions or [d])


def test_reworded_moved_finding_has_one_owner_and_descendant_link(stack):
    p=plan(stack); bodies=render(p,{1:'https://example.test/review/1'})
    assert p['unique_blockers']==1 and len(p['issues'])==1
    assert '### zero-denominator' in bodies[1]
    assert '[zero-denominator](https://example.test/review/1)' in bodies[2]
    assert 'ZeroDivisionError' not in bodies[2]
    assert 'zero-denominator' not in bodies[3]  # repaired head is not inferred affected


def test_distinct_causes_in_one_file_are_not_fuzzy_merged(stack):
    repo,layers,obs,d,base=stack
    other={**d,'issue_key':'wrong-contract','title':'Different contract defect','occurrences':['b']}
    p=plan(stack,[{**d,'occurrences':['a']},other])
    assert p['unique_blockers']==2


@pytest.mark.parametrize('change', ['later_owner','missing_occurrence','duplicate_occurrence','unknown_pr','wrong_head','unrelated_origin','no_evidence'])
def test_invalid_attribution_is_rejected(stack,change):
    repo,layers,obs,d,base=copy.deepcopy(stack)
    if change=='later_owner':d['owner_pr']=2
    elif change=='missing_occurrence':d['occurrences']=['a']
    elif change=='duplicate_occurrence':d['occurrences']=['a','a','b']
    elif change=='unknown_pr':obs[1]['pr']=99
    elif change=='wrong_head':obs[1]['head']=base
    elif change=='unrelated_origin':d['introduced_commit']=layers[-1]['head']
    elif change=='no_evidence':d['origin_evidence']=''
    with pytest.raises(ValueError):consolidate('owner/repo',repo,layers,obs,[d])


def test_baseline_and_unattributed_are_not_charged_to_first_pr(stack):
    repo,layers,obs,d,base=stack
    p=plan(stack,[{**d,'status':'baseline','owner_pr':None,'introduced_commit':base}])
    assert p['unique_blockers']==0
    assert 'Owned here: 0 blockers' in render(p,{})[1]
    p=plan(stack,[{**d,'status':'unattributed','owner_pr':None,'introduced_commit':None}])
    assert p['attribution_pending']==1 and p['unique_blockers']==0


def test_regression_has_separate_owner_and_does_not_reopen_fixed_layer(stack):
    repo,layers,obs,d,base=stack
    obs.append(dict(id='c',pr=4,head=layers[3]['head'],finding=obs[0]['finding']))
    regression={**d,'issue_key':'zero-denominator-reintroduced','owner_pr':4,
                'introduced_commit':layers[3]['head'],'occurrences':['c'],'regression_of':d['issue_key']}
    p=plan(stack,[d,regression])
    assert p['unique_blockers']==2
    assert p['issues'][1]['owner_pr']==4
    assert p['issues'][0]['affected_prs']==[1,2]


def test_ledger_retains_identity_and_rejects_reassignment(stack,tmp_path):
    p=plan(stack);path=tmp_path/'ledger/issues.json'
    merge_ledger(path,p);merge_ledger(path,p)
    data=json.loads(path.read_text())
    assert len(data['issues'])==1
    assert len(data['issues']['zero-denominator']['occurrences'])==2
    bad=copy.deepcopy(p);bad['issues'][0]['introduced_commit']=p['layers'][1]['head']
    with pytest.raises(ValueError):merge_ledger(path,bad)
    assert json.loads(path.read_text())==data


def test_repository_namespace_and_missing_canonical_link(stack):
    a=plan(stack)
    repo,layers,obs,d,_=stack
    b=consolidate('other/repo',repo,layers,obs,[d])
    assert a['issues'][0]['id']!=b['issues'][0]['id']
    with pytest.raises(ValueError):render(a,{})


def test_divergent_lower_head_retains_introduction_ownership(stack):
    repo,layers,obs,d,base=stack
    git(repo,'checkout','-q',layers[0]['head'])
    (repo/'unrelated.txt').write_text('lower PR amended after upper branch was cut')
    git(repo,'add','.')
    git(repo,'commit','-qm','amend lower PR')
    layers[0]['head']=git(repo,'rev-parse','HEAD')
    obs[0]['head']=layers[0]['head']
    assert plan(stack)['issues'][0]['owner_pr']==1


def test_cross_repository_reference_resolves_only_to_owned_issue(stack):
    from reviewkit.stack import canonical_links
    p=plan(stack)
    q=copy.deepcopy(p);q['repository']='owner/consumer'
    q['issues'][0].update(status='reference',owner_pr=None,canonical_reference='owner/repo:zero-denominator')
    links=canonical_links([p,q],{('owner/repo',1):'https://example.test/review/1'})
    assert 'same issue tracked' in render(q,{},links)[1]
    q['issues'][0]['canonical_reference']='owner/consumer:zero-denominator'
    with pytest.raises(ValueError):canonical_links([p,q],{('owner/repo',1):'https://example.test/review/1'})


def test_baseline_has_one_tracking_location_without_false_ownership(stack):
    repo,layers,obs,d,base=stack
    p=plan(stack,[{**d,'status':'baseline','owner_pr':None,'introduced_commit':base,'tracking_pr':1}])
    bodies=render(p,{1:'https://example.test/review/1'})
    assert 'ZeroDivisionError' in bodies[1]
    assert 'ZeroDivisionError' not in bodies[2]
    assert 'tracking location only' in bodies[2]


def test_discovery_detects_amended_lower_branch_instead_of_silently_omitting_it(stack,monkeypatch):
    import runpy
    from types import SimpleNamespace
    repo,layers,obs,d,base=stack
    git(repo,'update-ref','refs/remotes/origin/main',base)
    original=layers[0]['head']
    git(repo,'checkout','-q',original)
    (repo/'amendment').write_text('amended lower PR')
    git(repo,'add','.')
    git(repo,'commit','-qm','amended lower')
    lower=git(repo,'rev-parse','HEAD')
    api=runpy.run_path(str(Path(__file__).resolve().parents[2]/'review/bin/review.py'))
    state=api['stack'].__globals__
    prs=[dict(number=n,title='fixture',headRefName=f'branch-{n}',baseRefName='main',baseRefOid=base,createdAt=str(n)) for n in [1,2]]
    original_run=subprocess.run
    def run(args,**kwargs):
        if args[0]=='gh':return SimpleNamespace(stdout=json.dumps(prs))
        return original_run(args,**kwargs)
    monkeypatch.setattr(subprocess,'run',run)
    monkeypatch.setitem(state,'fetch_pr',lambda checkout,remote,n: lower if n==1 else layers[1]['head'])
    with pytest.raises(SystemExit,match='divergent'):
        api['stack'](repo,'origin','owner/repo','owner',2,layers[1]['head'])
