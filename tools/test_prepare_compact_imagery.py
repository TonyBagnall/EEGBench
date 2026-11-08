"""Native order, crop precision and imagery marker safeguards."""
import numpy as np
import pytest
from tools import prepare_compact_imagery as c


def test_mimed_native_names_and_exact_local_crop():
    block=np.arange(1152*14,dtype=np.float64).reshape(1152,14)
    d=dict(channel=c.MIMED_CHANNELS,Fs=128,joined_data=[block]*4)
    x,names,original=c.mimed_block(d,2)
    assert x.shape==(14,512) and x.dtype==np.float64
    assert np.array_equal(x,block[384:896].T)
    assert np.array_equal(original,block) and names==c.MIMED_CHANNELS
    d['channel']=list(reversed(c.MIMED_CHANNELS))
    with pytest.raises(ValueError,match='order'):c.mimed_block(d,0)


def test_mimed_rejects_truncated_or_wrong_rate():
    d=dict(channel=c.MIMED_CHANNELS,Fs=128,joined_data=[np.zeros((895,14))])
    with pytest.raises(ValueError,match='Incomplete'):c.mimed_block(d,0)
    d['Fs']=256
    with pytest.raises(ValueError,match='rate'):c.mimed_block(d,0)


def test_moving_keeps_rest_and_imagination_excludes_execution():
    class Annotations:
        onset=np.arange(17)*8.0
        duration=np.zeros(17)
        description=['Trigger#'+str(i) for i in range(1,18)]
    class Raw:
        annotations=Annotations();first_time=0;n_times=70000
        def time_as_index(self,t,use_rounding):return np.array([round(t*500)])
    events=c.moving_events(Raw())
    assert [e[2] for e in events]==['Trigger#1','Trigger#3','Trigger#7','Trigger#9','Trigger#13','Trigger#15']
    assert [e[3] for e in events]==['1','2','1','3','1','4']
    Raw.n_times=1000
    with pytest.raises(ValueError,match='Incomplete'):c.moving_events(Raw())


def test_zhang_shortest_cue_and_left_censored_fragment():
    values=np.r_[np.full(40,2),np.zeros(3000),np.full(3960,8),np.zeros(10)]
    kept,excluded=c.zhang_intervals(values)
    assert kept==[(1,3040,7000,8)]
    assert excluded[0]['start']==0 and excluded[0]['stop']==40
    with pytest.raises(ValueError,match='Unexpected short'):c.zhang_intervals(np.r_[np.zeros(100),np.full(40,2)])


def test_zhang_subject_split_uses_numeric_native_ids():
    people=sorted('H'+str(i) for i in range(1,13))
    assert c.SPECS['zhang']['splitter'](people,[])=={'H'+str(i) for i in range(1,10)}
    assert c.SPECS['zhang']['validation_updates']['channel_order_verified_all_recordings'] is False


def test_published_demographics_keep_original_zero_padded_id(tmp_path):
    rows=''.join(f'<tr><td>H{i:02d}</td><td>M</td><td>{20+i}</td><td>Right</td></tr>' for i in range(1,13))
    p=tmp_path/'article.xml';p.write_text('<article><table-wrap id="pone.0188293.t002"><table>'+rows+'</table></table-wrap></article>',encoding='utf-8')
    people=c.zhang_participants(p)
    assert people[0]['participant_id']=='H1' and people[0]['published_participant_id']=='H01'
    assert people[-1]['participant_id']=='H12' and people[0]['age_years']==21
