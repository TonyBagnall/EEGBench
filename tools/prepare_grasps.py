"""Original Track4 MAT epochs -> ImaginedGrasps, official session split."""
import argparse
import ast
import copy
import json
from pathlib import Path
import re

import numpy as np
from scipy.io import loadmat
from tools import prepare_open_moabb as core
from tools.predct_inspect import xlsx_rows
from tools.prepare_walking_erp import excel_column
from tools.update_dataset_sidecars import finish

ROOT=Path(__file__).resolve().parents[1]
CHANNELS='Fp1 AF7 AF3 AFz F7 F5 F3 F1 Fz FT7 FC5 FC3 FC1 T7 C5 C3 C1 Cz TP7 CP5 CP3 CP1 CPz P7 P5 P3 P1 Pz PO7 PO3 POz Fp2 AF4 AF8 F2 F4 F6 F8 FC2 FC4 FC6 FT8 C2 C4 C6 T8 CP2 CP4 CP6 TP8 P2 P4 P6 P8 PO4 PO8 O1 Oz O2 Iz'.split()
CLASSES=['Cylindrical','Spherical','Lumbrical']
PHASES=[('training','day1'),('validation','day2'),('test','day3')]


def archive_partition(row):return {'training':'TRAIN','validation':'TRAIN','test':'TEST'}[row['original_partition']]


def answers(path):
    rows=xlsx_rows(path,'Track4');result={}
    for column,value in rows[0].items():
        match=re.fullmatch(r'Data_sample(\d{2})',value)
        if not match:continue
        n=0
        for c in column:n=26*n+ord(c)-64
        label_column=excel_column(n+1)
        if rows[1].get(column)!='Trial #' or rows[1].get(label_column)!='True Label':raise ValueError('Not an original true-label workbook')
        labels=[]
        for i,row in enumerate(rows[2:],1):
            if row.get(column)!=str(i) or row.get(label_column) not in ['0','1','2']:raise ValueError('Unknown/unordered original test label')
            labels.append(int(row[label_column]))
        if len(labels)!=150:raise ValueError('Incomplete original test labels')
        result[match[1]]=dict(labels=labels,label_column=label_column)
    if len(result)!=15:raise ValueError('Incomplete original participant answers')
    return result


def imagery(epoch):
    if list(epoch['clab'])!=CHANNELS or int(epoch['fs'])!=250 or epoch['x'].shape!=(2501,60,150) or not np.array_equal(epoch['t'],np.arange(-6000,4001,4)):raise ValueError('Changed native channel/timing/shape schema')
    # t=0 is MI onset, local index1500. Cue mask is outside this window.
    return np.ascontiguousarray(np.transpose(epoch['x'][1500:2500],(2,1,0)),dtype='<f8')


def onehot_labels(epoch):
    if list(epoch['className'])!=CLASSES:raise ValueError('Native class order differs from original class table')
    y=np.asarray(epoch['y'])
    if y.shape!=(3,150) or not np.isin(y,[0,1]).all() or not (y.sum(axis=0)==1).all():raise ValueError('Invalid native one-hot labels')
    return y.argmax(axis=0)


def records(cache,spec):
    sheet=answers(cache/'test/Track4_Answer Sheet_Test.xlsx')
    tree=ast.parse((cache/'moabb-upper-limb.py').read_text(encoding='utf-8'))
    independent=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.AnnAssign) and getattr(n.target,'id',None)=='_TEST_LABELS_DAY3')
    for person,a in sheet.items():
        if tuple(a['labels'])!=independent[int(person)]:raise ValueError('Original answer sheet disagrees with pinned independent loader')
    for phase,day in PHASES:
        for path in sorted((cache/phase).glob('sample*.mat')):
            person=re.fullmatch(r'sample(\d{2})\.mat',path.name)[1]
            if spec.get('subjects') and person not in spec['subjects']:continue
            d=loadmat(path,simplify_cells=True);e=d['epo'];x=imagery(e)
            if list(e['className'])!=CLASSES or list(d['mnt']['clab'])!=CHANNELS:raise ValueError('Class/montage names disagree with actual arrays')
            labels=np.asarray(sheet[person]['labels']) if phase=='test' else onehot_labels(e)
            if phase=='test' and not np.all(e['x'][750:1500]==0):raise ValueError('New test source no longer has documented cue mask; review source version')
            source=path.relative_to(cache).as_posix();rows=[]
            for i,label in enumerate(labels):
                row=core.base_row(person,day,'unknown',source,i,1500,1000,250,str(int(label)),str(int(label)+1))
                row.update(original_partition=phase,sample_reference='Native epoch-local samples; original continuous offsets unavailable',
                    source_array_index=f'epo.x[1500:2500,:,{i}].T',source_event_sample=1500,
                    source_event_sample_evidence='Native epo.t==0 at local index1500, not original continuous sample',
                    original_continuous_start_sample='',original_continuous_end_sample='',native_source_file_field=str(e['file']),
                    original_class_name=CLASSES[int(label)],source_one_hot_label='' if phase=='test' else json.dumps(e['y'][:,i].tolist()),
                    label_evidence='Original True Label workbook0/1/2, matches independent pinned loader' if phase=='test' else 'Derived row index0/1/2 from native one-hot y; original vector retained',
                    answer_sheet_label_cell=sheet[person]['label_column']+str(i+3) if phase=='test' else '',
                    native_epoch_first_time_ms=-6000,native_window_start_time_ms=0,native_window_last_time_ms=3996,native_window_end_exclusive_ms=4000,
                    indexed_time_reference='start/end_time_seconds are from stored epoch-array origin; native epo.t uses MI onset zero separately',
                    session_id_evidence='Organiser folder maps training/day1,validation/day2,test/day3; original calendar dates absent')
                rows.append(row)
            info=dict(source_file=source,source_file_sha256=core.sha(path),participant_id=person,session_id=day,run_id='unknown',original_partition=phase,
                native_channel_names=list(e['clab']),channel_types_documented=['EEG']*60,source_eeg_indices=list(range(60)),native_class_names=list(e['className']),
                native_sampling_frequency_hz=int(e['fs']),native_epoch_time_ms=e['t'],native_source_file_field=str(e['file']),native_montage=d['mnt'],
                native_epoch_shape=list(e['x'].shape),native_dtype=str(e['x'].dtype),selected_native_sample_slice=[1500,2500],
                native_test_resolution=e.get('resolution'),resolution_evidence='Test resolution vector retained but not applied: length differs from60 selected inputs and physical semantics not established',
                test_cue_all_zero=bool(np.all(e['x'][750:1500]==0)),source_case_count=len(rows),
                coordinate_evidence='Native mnt coordinates retained; units/frame and individual measurement status unspecified')
            yield x,rows,CHANNELS,info


SPEC=dict(name='ImaginedGrasps',source='BCIComp2020UpperLimb / 2020 BCI Competition Track4',cache='BCIComp2020UpperLimb',hz=250,points=1000,classes=3,train_subjects=0,
    labels={'1':'Cylindrical','2':'Spherical','3':'Lumbrical'},doi=None,paper='Jeong et al.(2022),2020 International brain-computer interface competition:A review; DOI10.3389/fnhum.2022.898300,Track4',
    case_splitter=archive_partition,allow_subject_overlap=True,subject_overlap_reason='Original session-transfer protocol: day1 training plus day2 validation form TRAIN; day3 remains TEST. All15 participants intentionally shared, three days7days apart.',
    note='Preserve native60 EEG order and float64 numbers, presumed microvolt units with no rescaling. Crop only four-second MI t0..3996ms, native indices1500:2500 of2501-point epochs spanning-6000..4000ms. Test cue mask750:1500 excluded consistently from all phases; no synthetic Raw timeline or added preprocessing. True test labels from original organiser workbook, matched to pinned independent loader. Native mnt retained without invented coordinate units or dates. Official day1+day2 TRAIN,day3 TEST; no validation archive.',
    evidence_files=['imagined-grasps-preparation.md','imagined-grasps-source-lock.json'],
    cache_evidence_files=['Data description (Track4).pdf','test/ReadMe.txt','test/Track4_Answer Sheet_Test.xlsx','answer_sheet_track4.xlsx','original-osf-project.json','original-osf-licence.json','moabb-upper-limb.py'],
    conversion_files=['prepare_grasps.py','download_grasps.py','predct_inspect.py','prepare_walking_erp.py','update_dataset_sidecars.py'],
    validation_updates=dict(cross_split_overlapping_intervals=None,original_continuous_interval_overlap='Not computable from epoched source; continuous offsets absent',source_sensor_identity='Every native epo.clab/mnt.clab checked against organiser60-channel table; exact array order preserved'),
    metadata_updates=dict(original_source_url='https://osf.io/pq7vb/',source_doi=None,reference_paper_doi='10.3389/fnhum.2022.898300',original_partition='Official training/validation/test recording days',
        split_definition='Original day1 training files followed by day2 validation files form TRAIN; original day3 test unchanged; all15 people shared intentionally',
        case_order='Original training files subjects01-15, then validation subjects01-15; TEST subjects01-15. Native epoch order within file.',
        reference='FCz, original organiser PDF',ground='Fpz, original organiser PDF',native_epoch_samples=2501,native_epoch_time_bounds_ms=[-6000,4000],
        unit_evidence='Microvolt interpretation inferred from preprocessed MATLAB EEG convention/amplitudes; explicit native physical unit absent; original float64 numbers unchanged',
        preprocessing='Source documentation:250Hz acquisition and60Hz notch, already epoched. Archive selectsMI native1500:2500, float64 unchanged, global flat policy only; no extra filter/resampling/reference/baseline.',
        missing_or_inconsistent_metadata=['Original continuous offsets, actual calendar dates and native run IDs unavailable; session days come from organiser phase mapping',
            'Physical units not explicit; test resolution vector length does not match60 selected EEG, so it is retained but not used as a guessed calibration',
            'Native montage coordinate units/frame and individual measurement status unknown',
            'Original PDF says15 subjects in introduction/file list but10 in one recording paragraph; actual full source lists15 per split',
            'Original handedness sentence is internally awkward; no individual handedness/age/sex is invented',
            'Narrative electrode paragraph differs from actual channel table; embedded clab and numbered table agree and determine order',
            'Test visual-cue interval deliberately zeroed; archive uses only actual motor imagery segment, not zero-padded cue samples'],
        metadata_evidence=dict(direct='Native epo.x/y/clab/fs/t/file,mnt and true-label workbook cells; test resolution/cue mask retained as evidence',
            documented='Original participant/session protocol,60EEG identity,FCz reference/Fpz ground,250Hz and60Hz notch from organiserPDF',
            assigned='Encoded1-3 labels and day labels linked to official folders; unknown calendar/run IDs stay unknown',
            inferred='Presumed microvolt scale only, factor1; coordinate units and original continuous offsets not invented')))


def prepare(cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),pilot=False):
    spec=copy.deepcopy(SPEC)
    # Ordinal recording caches differ between a one-subject pilot and the cohort.
    # Never reuse the pilot's recording-0001 for full-cohort training subject02.
    spec['intermediate_directory']='classification-intermediate-full'
    if pilot:spec.update(name='ImaginedGraspsPilot',subjects=['01'],intermediate_directory='classification-intermediate-pilot')
    core.SPECS['grasps']=spec;core.READERS['grasps']=records
    return finish_sidecars(core.prepare('grasps',cache_root,output))


def finish_sidecars(result):
    folder=Path(result['path']);name=result['dataset'];m=json.loads((folder/(name+'_metadata.json')).read_text(encoding='utf-8'));mnt=m['recordings'][0]['native_montage']
    same_positions=all(r['native_montage']==mnt for r in m['recordings']);m['native_positions_consistent_all_recordings']=same_positions
    for sensor in m['sensors']:
        i=CHANNELS.index(sensor['name']);sensor.update(native_channel_index=i,source_x=mnt['x'][i] if same_positions else None,source_y=mnt['y'][i] if same_positions else None,source_pos3d=[mnt['pos_3d'][j][i] for j in range(3)] if same_positions else None,
            coordinate_evidence='All native layouts agree, frame/units unspecified; no individual measurement claim' if same_positions else 'Native layouts vary; see per-recording native_montage, no single geometry asserted',units_evidence=m['unit_evidence'])
    indices=[s['native_channel_index'] for s in m['sensors']]
    for r in m['recordings']:r['exported_native_channel_indices']=indices
    m['aliases']=['BCIComp2020UpperLimb','2020 International BCI Competition Track4'];m['source_case_count']=sum(r['source_case_count'] for r in m['recordings'])
    if result['train_cases']+result['test_cases']!=m['source_case_count']:raise ValueError('Native epoch/export accounting mismatch')
    return finish(result,m,SPEC['evidence_files'],SPEC['conversion_files'],dict(source_doi=None,reference_paper_doi=SPEC['metadata_updates']['reference_paper_doi'],original_source_url=m['original_source_url'],
        label_mapping=SPEC['labels'],split_definition=m['split_definition'],licence_url='https://creativecommons.org/licenses/by/4.0/',unit_evidence=m['unit_evidence']),
        readme=f'# {name}\n\nThree imagined grasp classes, native EEG order; four-second motor-imagery samples only. Original float64 values unchanged, presumed microvolt units (inferred). Official days1+2 train,day3 test; participants intentionally shared. Read IDs as strings. See metadata/source PDF for scope, reference, unknown continuous times and exact sensor positions.\n',
        attribution='Original data: OSF pq7vb Track4, CC BY4.0 https://creativecommons.org/licenses/by/4.0/. Dataset DOI not independently established. Reference paper: Jeong et al.(2022), DOI10.3389/fnhum.2022.898300. Changes: MI epoch crop, train+validation merge, global flat policy and .ts/metadata export. Native numeric scale unchanged; units inferred.\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));p.add_argument('--pilot',action='store_true');a=p.parse_args();prepare(a.cache_root,a.output,a.pilot)
