"""Check FIF metadata recovery, duplicate aliases, timing and corrected labels."""

import csv
import datetime
import hashlib
import json

import numpy as np
import pytest

from tools.prepare_kalunga import CHANNELS, LABELS, NAME, RECORD, audit_sources, convert


def fixture_source(tmp_path, subjects=(1,2), duplicate=False, wrong_channels=False):
    import mne
    cache=tmp_path/"source";cache.mkdir()
    for subject in subjects:
        rng=np.random.default_rng(1 if duplicate else subject)
        data=rng.normal(0,1e-6,(9,42000));data[-1]=0
        for i in range(32):data[-1,256+i*1280]=i%4+1
        names=CHANNELS.copy()
        if wrong_channels:names[3],names[4]=names[4],names[3]
        info=mne.create_info(names+["STI 014"],256,["eeg"]*8+["stim"])
        info["subject_info"]=dict(id=subject,his_id=f"S{subject}")
        raw=mne.io.RawArray(data,info,verbose="ERROR")
        raw.set_meas_date(datetime.datetime(2015,1,subject,tzinfo=datetime.timezone.utc))
        raw.save(cache/f"subject{subject:02d}_run1_raw.fif",overwrite=True,verbose="ERROR")
    files=[dict(key=p.name,size=p.stat().st_size,checksum="md5:"+hashlib.md5(p.read_bytes()).hexdigest(),links={"self":"https://example.invalid/"+p.name}) for p in cache.glob("*.fif")]
    (cache/f"zenodo-record-{RECORD}.json").write_text(json.dumps(dict(id=RECORD,metadata=dict(license={"id":"cc-by-4.0"},creators=[]),files=files)))
    (cache/"moabb-kalunga-loader.py").write_text("# Test evidence\n")
    return cache


def test_full_case_alignment_corrected_labels_and_timebounds(tmp_path):
    metadata,validation=convert(fixture_source(tmp_path),tmp_path/"out",subjects=(1,2),train=(1,),download=False,smoke=False)
    assert metadata["shapes"]=={"train":[32,8,512],"test":[32,8,512]}
    assert metadata["channel_names"]==CHANNELS
    assert metadata["label_map"]=={"1":"rest","2":"13Hz","3":"21Hz","4":"17Hz"}
    assert validation["duplicate_signal_cases_remaining"]==0
    with (tmp_path/"out"/NAME/"cases_train.tsv").open(newline="") as file:rows=list(csv.DictReader(file,delimiter="\t"))
    assert rows[0]["participant_id"]=="01" and rows[0]["source_subject_id"]=="S1"
    assert rows[0]["event_sample"]=="256" and rows[0]["start_sample"]=="768" and rows[0]["end_sample"]=="1280"
    assert rows[2]["label_description"]==LABELS[3]=="21Hz"
    assert rows[0]["session_id"].startswith("2015-01-01")
    assert rows[0]["loader_session_id"]=="0"


def test_numeric_duplicate_with_different_participant_headers_is_flagged(tmp_path):
    _,audit=audit_sources(fixture_source(tmp_path,subjects=(3,7),duplicate=True),download=False)
    assert len(audit["signal_duplicate_groups"])==1
    assert [r["file"] for r in audit["files"] if r["retained"]]==["subject03_run1_raw.fif"]
    assert audit["files"][1]["duplicate_of"]=="subject03_run1_raw.fif"


def test_changed_fif_sensor_order_rejected(tmp_path):
    with pytest.raises(ValueError,match="channel order"):
        audit_sources(fixture_source(tmp_path,wrong_channels=True),download=False)


def test_modified_fif_fails_publisher_checksum(tmp_path):
    cache=fixture_source(tmp_path)
    with (cache/"subject01_run1_raw.fif").open("ab") as file:file.write(b"modified")
    with pytest.raises(ValueError,match="modified source"):
        audit_sources(cache,download=False)
