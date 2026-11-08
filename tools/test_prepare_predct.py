"""Case identity, phenotype splitting and source delimiter regression tests."""
import json
import numpy as np
import pytest
from tools.prepare_predct import clinical_csv,group_split,make_cases,window_bounds,spec_for,rest_intervals,original_label_fields
from tools import prepare_predct
from tools.predct_inspect import xlsx_rows

def test_windows_never_pad_or_overlap():
    assert window_bounds(71,6072)==[(71,2071),(2071,4071),(4071,6071)]
    assert window_bounds(0,1999)==[]
    with pytest.raises(ValueError):window_bounds(-1,3000)

def test_rest_marker_gap_does_not_become_an_extra_resting_period():
    events=[dict(sample=s,description='S  3') for s in [10,100000,100500,101000,101500]]
    intervals,groups=rest_intervals(events,110000)
    assert intervals==[(10,510,'eyes_closed'),(100000,102000,'eyes_closed')]
    assert [bounds for a,b,_ in intervals for bounds in window_bounds(a,b)]==[(100000,102000)]
    assert len(groups[0]['samples'])==1

def test_subject_split_preserves_string_ids_and_both_groups():
    rows=[dict(participant_id=p,label=l) for p,l in [('001','1'),('002','1'),('003','1'),('004','1'),('Control001','2'),('Control002','2'),('Control003','2'),('Control004','2')]]
    train=group_split([r['participant_id'] for r in rows],[(None,rows)])
    assert train=={'001','002','003','Control001','Control002','Control003'}
    with pytest.raises(ValueError,match='inconsistent'):group_split([],[(None,rows+[dict(participant_id='001',label='2')])])

def test_literal_and_real_tab_clinical_tables(tmp_path):
    for sep in ['\t','\\t']:
        p=tmp_path/'clinical.csv';p.write_text(sep.join(['Group','Pedal_ID'])+'\n'+sep.join(['Control','001'])+'\n')
        assert clinical_csv(p)==[{'Group':'Control','Pedal_ID':'001'}]

def test_case_rows_trace_exact_native_samples_and_half_open_events():
    a=np.arange(10000,dtype=np.float32).reshape(2,5000)
    x,rows,names=make_cases(a,['A','B'],'001','unknown','original.cnt','1',[(10,4010,'task')],{'group':'high'},
        [dict(sample=10,description='a'),dict(sample=2010,description='b'),dict(sample=4010,description='c')])
    np.testing.assert_array_equal(x[0],a[:,10:2010]);np.testing.assert_array_equal(x[1],a[:,2010:4010])
    assert x.dtype==np.float64 and rows[1]['participant_id']=='001'
    assert rows[0]['end_sample']==rows[1]['start_sample']==2010
    assert json.loads(rows[0]['native_events_in_window'])==[{'sample':10,'description':'a'}]
    assert rows[0]['source_trial_id']==''
    assert rows[0]['source_event_sample']==rows[0]['source_epoch_index']==''

def test_data_licence_and_student_label_are_not_software_or_diagnosis():
    s=spec_for('Gruendler2009')
    assert s['licence']=='PDDL-1.0' and 'symptoms' in s['labels']['1']
    assert s['moabb_revision'] is None

def test_original_clinical_labels_are_preserved_and_encoded_consistently():
    assert original_label_fields('Singh2020',{'clinical_variables':'{"Group":"PDwithFOG"}','label':'1'})['source_label']=='PDwithFOG'
    assert original_label_fields('Gruendler2009',{'OCI':'021','label':'1'})['source_label']=='021'
    with pytest.raises(ValueError,match='differs'):original_label_fields('Gruendler2009',{'OCI':'20','label':'1'})

def test_removed_pair_audit_links_original_sensor_to_exact_exported_case(tmp_path):
    import csv
    from tools.prepare_predct import removal_pair_audit
    from tools.prepare_wang import digest_case
    cache=tmp_path/'cache';folder=tmp_path/'out';(cache/'classification-intermediate').mkdir(parents=True);folder.mkdir()
    x=np.array([[[1.,2.,3.,4.],[0.,0.,0.,0.],[5.,6.,7.,8.]],[[2.,3.,4.,5.],[1.,2.,3.,4.],[6.,7.,8.,9.]]])
    np.savez_compressed(cache/'classification-intermediate/recording-0000.npz',X=x)
    rows=[dict(source_file='native.cnt',event_index=str(i),example_id=f'case{i}',split='TRAIN',row=str(i),participant_id='001',start_sample=str(i*4),end_sample=str((i+1)*4),label='1',signal_sha256=digest_case(x[i,[0,2]])) for i in range(2)]
    def tables():
        for split,values in [('train',rows),('test',[])]:
            with (folder/f'cases_{split}.tsv').open('w',newline='') as f:
                writer=csv.DictWriter(f,list(rows[0]),delimiter='\t');writer.writeheader();writer.writerows(values)
    tables()
    metadata=dict(channel_names=['A','C'],recordings=[dict(source_file='native.cnt',source_eeg_indices=[0,1,2])],channel_quality=dict(source_channel_names=['A','B','C'],removed_indices=[1],effectively_flat_case_counts=[0,1,0]))
    report=removal_pair_audit(cache,folder,metadata)
    assert report['pairs']==report['affected_cases']==1 and report['source_to_export_hash_verified']
    assert 'native.cnt' in (folder/report['file']).read_text()
    rows[0]['signal_sha256']='incorrect';tables()
    with pytest.raises(ValueError,match='hash mismatch'):removal_pair_audit(cache,folder,metadata)

def test_duplicate_oci_headers_preserve_raw_columns(monkeypatch,tmp_path):
    original=[{'A':'ID','B':'OCI','J':'OCI'}, {'A':'001','B':'30','J':'10'}, {'A':'summary','B':'2'}]
    monkeypatch.setattr(prepare_predct,'xlsx_rows',lambda *args:original)
    recovered=prepare_predct.gruendler_demo(tmp_path)
    assert recovered=={'001':{'A':'001','B':'30','J':'10'}}
    assert float(recovered['001']['B'])>=21 and float(recovered['001']['J'])<21

def test_xlsx_sheet_relationship_and_sparse_string_cells(tmp_path):
    import zipfile
    p=tmp_path/'table.xlsx'
    with zipfile.ZipFile(p,'w') as z:
        z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="SELECT" r:id="rId3"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships><Relationship Id="rId3" Target="worksheets/sheet7.xml"/></Relationships>')
        z.writestr('xl/sharedStrings.xml','<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>001</t></si></sst>')
        z.writestr('xl/worksheets/sheet7.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c r="A1" t="s"><v>0</v></c><c r="J1"><v>21</v></c></row></sheetData></worksheet>')
    assert xlsx_rows(p,'SELECT')==[{'A':'001','J':'21'}]
    with pytest.raises(ValueError):xlsx_rows(p,'other')
