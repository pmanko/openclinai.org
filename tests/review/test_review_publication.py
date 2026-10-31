"""Publication changes only a current, owned review and retries without duplication."""
import copy
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'review/lib'))
from reviewkit.publication import apply_updates, digest


@pytest.fixture
def publication():
    entry = dict(repo='owner/project',pr=1,head='head',base='base',review_id=7,
                 body='canonical issue and links',expected_body_sha256=digest('old'),
                 body_sha256=digest('canonical issue and links'))
    state = dict(pr=dict(state='open',head={'sha':'head'},base={'sha':'base'}),
                 review=dict(id=7,user={'login':'owner'},state='COMMENTED',body='old',html_url='https://example.test/review/7'))
    writes=[]
    def api(path,method='GET',body=None):
        if path=='user': return {'login':'owner'}
        if method!='GET':
            assert method=='PUT' and path.endswith('/reviews/7')
            writes.append(body)
            state['review']['body']=body['body']
        return copy.deepcopy(state['review'] if '/reviews/' in path else state['pr'])
    return entry,state,writes,api


def test_updates_existing_review_and_retry_does_not_write(publication):
    entry,state,writes,api=publication
    receipts=apply_updates([entry],api,authorized=True)
    assert len(writes)==1 and receipts[0]['id']==7
    assert apply_updates([entry],api,authorized=True)[0]['reused']
    assert len(writes)==1


@pytest.mark.parametrize('failure',['unauthorized','head','base','closed','author','state','body','plan'])
def test_unsafe_update_never_writes(publication,failure):
    entry,state,writes,api=publication
    if failure in ('head','base'): state['pr'][failure]['sha']='moved'
    elif failure=='closed':state['pr']['state']='closed'
    elif failure=='author':state['review']['user']['login']='someone-else'
    elif failure=='state':state['review']['state']='APPROVED'
    elif failure=='body':state['review']['body']='human edited'
    elif failure=='plan':entry['body']='tampered'
    with pytest.raises(ValueError):apply_updates([entry],api,authorized=failure!='unauthorized')
    assert writes==[]


def test_entire_batch_is_checked_before_writes(publication):
    entry,state,writes,api=publication
    second={**entry,'head':'wrong'}
    with pytest.raises(ValueError):apply_updates([entry,second],api,authorized=True)
    assert writes==[]
