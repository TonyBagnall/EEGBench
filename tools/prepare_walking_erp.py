"""Native epoched walking ERP -> WalkingTargets, preserving official splits."""
import argparse
import ast
import copy
from collections import Counter
import json
from pathlib import Path
import re
import shutil

import numpy as np
from scipy.io import loadmat
from tools import prepare_open_moabb as core
from tools.predct_inspect import xlsx_rows
from tools.prepare_wang import digest_case

ROOT=Path(__file__).resolve().parents[1]
LOCK=ROOT/'docs/walking-targets-source-lock.json'
SCALP='Fp1 Fp2 AFz F7 F3 Fz F4 F8 FC5 FC1 FC2 FC6 C3 Cz C4 CP5 CP1 CP2 CP6 P7 P3 Pz P4 P8 PO7 PO3 POz PO4 PO8 O1 Oz O2'.split()
EOG='HEOGL HEOGR VEOGU VEOGL'.split()
EAR='L1 L2 L4 L5 L6 L7 L9 L10 R1 R2 R4 R5 R7 R8'.split()
IMU='AccX AccY AccZ GyroX GyroY GyroZ'.split()
ALL=SCALP+EOG+EAR+IMU
EEG_INDICES=list(range(32))+list(range(36,50))
PHASES=[('training','epo_tr',180,0),('validation','epo_val',60,180),('test','epo_te',60,240)]

def archive_partition(row):
    return {'training':'TRAIN','validation':'TRAIN','test':'TEST'}[row['original_partition']]

def excel_column(number):
    result=''
    while number:number,r=divmod(number-1,26);result=chr(65+r)+result
    return result

def test_answers(path):
    rows=xlsx_rows(path,'Track5');answers={}
    for column,value in rows[0].items():
        match=re.fullmatch(r'Data_sample(\d{2})',value,re.I)
        if not match:continue
        number=0
        for ch in column:number=number*26+ord(ch)-64
        label_column=excel_column(number+1)
        if rows[1].get(column)!='Trial #' or rows[1].get(label_column)!='True Label':raise ValueError('Unknown answer-sheet schema')
        labels=[]
        for trial,row in enumerate(rows[2:],1):
            if int(row[column])!=trial or row[label_column] not in ['0','1']:raise ValueError('Unordered/invalid organizer test label')
            labels.append(int(row[label_column]))
        if len(labels)!=60:raise ValueError('Incomplete organizer answers')
        answers[match[1]]=dict(labels=labels,trial_column=column,label_column=label_column)
    if len(answers)!=15:raise ValueError('Missing subject answer columns')
    return answers

def native_labels(epoch):
    names=[str(n) for n in epoch['className']];y=np.asarray(epoch['y'])
    if y.ndim!=2 or y.shape[0]!=2 or not np.isin(y,[0,1]).all() or not (y.sum(axis=0)==1).all():raise ValueError('Not valid one-hot source labels')
    target=[i for i,n in enumerate(names) if 'target' in n.lower() and 'non' not in n.lower()]
    if len(target)!=1:raise ValueError('Unidentified target class')
    labels=np.where(y[target[0]],2,1)
    if not np.array_equal(labels,np.asarray(epoch['event']['desc'])):raise ValueError('Native event codes disagree with one-hot label mapping')
    return labels,names

def source_records(cache,spec):
    answers=test_answers(cache/'test/Track5_Answer Sheet_Test.xlsx')
    tree=ast.parse((cache/'moabb-walking-erp.py').read_text(encoding='utf-8'))
    pinned=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.AnnAssign) and getattr(n.target,'id',None)=='_TEST_LABELS_RUN2')
    for person,answer in answers.items():
        if tuple(answer['labels'])!=pinned[int(person)]:raise ValueError('Original organizer answers differ from pinned independent loader')
    standing={}
    for phase,key,count,offset in PHASES:
        for p in sorted((cache/phase).glob('Data_Sample*.mat')):
            person=re.fullmatch(r'Data_Sample(\d{2})\.mat',p.name)[1]
            if spec.get('subjects') and person not in spec['subjects']:continue
            d=loadmat(p,simplify_cells=True);e=d[key];names=[str(n) for n in e['clab']]
            if names!=ALL or e['fs']!=100 or e['x'].shape!=(100,56,count) or not np.array_equal(e['t'],np.arange(-190,801,10)):raise ValueError(f'Unknown native shape/timing/sensors: {p}')
            if [str(n) for n in d['mnt']['clab']]!=names:raise ValueError('Native montage does not match numeric channel rows')
            if phase=='test':labels=np.array(answers[person]['labels'])+1;class_names=[str(n) for n in e['className']]
            else:labels,class_names=native_labels(e)
            data=np.ascontiguousarray(np.transpose(e['x'][:,EEG_INDICES,:],(2,1,0)),dtype='<f8')
            standing_hash=digest_case(np.asarray(e['x_s'],dtype='<f8'))
            if person in standing and standing[person]!=standing_hash:raise ValueError('Standing calibration differs across source partitions; review source role')
            standing[person]=standing_hash
            file=p.relative_to(cache).as_posix();rows=[]
            for i,label in enumerate(labels):
                original=str(answers[person]['labels'][i]) if phase=='test' else str(int(e['event']['desc'][i]))
                row=core.base_row(person,'unknown','unknown',file,i,0,100,100,original,str(label))
                row.update(original_partition=phase,sample_reference='Native epoch-local samples; original continuous offsets unavailable',
                    source_array_index=f'{key}.x[:,{EEG_INDICES},{i}].T',source_event_sample=19,
                    source_event_sample_evidence='Native epo.t==0, local epoch index; not an original continuous sample',
                    original_trial_number_1based=offset+i+1,original_trial_id_evidence='Ordinal inferred from documented 180/60/60 sequential split; not an embedded acquisition ID',
                    original_recording_id=f'walking-subject-{person}',original_recording_id_evidence='Assigned grouping for documented participant walking sequence; original raw filename unavailable',
                    epoch_time_start_ms=-190,epoch_last_sample_ms=800,epoch_time_end_exclusive_ms=810,
                    source_class_name=next(n for n in class_names if ('non' not in n.lower())==(label==2)),
                    label_evidence='Organizer True Label answer sheet, 0=NonTarget/1=Target; independently matches pinned MOABB labels' if phase=='test' else 'Native one-hot className lookup and matching event.desc, 1=NonTarget/2=Target',
                    source_label_vector='' if phase=='test' else json.dumps(e['y'][:,i].tolist()),
                    answer_sheet_label_cell=answers[person]['label_column']+str(i+3) if phase=='test' else '',
                    original_continuous_start_sample='',original_continuous_end_sample='')
                rows.append(row)
            info=dict(source_file=file,source_file_sha256=core.sha(p),participant_id=person,session_id='unknown',
                native_channel_names=names,native_channel_types=['EEG']*32+['EOG']*4+['EEG']*14+['IMU']*6,
                source_eeg_indices=EEG_INDICES,original_partition=phase,source_epoch_count=count,native_dtype=str(e['x'].dtype),
                native_epoch_time_ms=e['t'],native_sampling_frequency_hz=e['fs'],native_class_names=class_names,
                native_montage=d['mnt'],coordinates_evidence='Native mnt, only scalp finite; source axes/units unspecified, no additional standard montage or ear positions assigned',
                standing_calibration_shape=list(e['x_s'].shape),standing_calibration_sha256=standing_hash,
                standing_calibration_role='Same participant standing array repeated in training/validation/test files; not exported as classification cases')
            yield data,rows,[names[i] for i in EEG_INDICES],info

SPEC=dict(name='WalkingTargets',source='BCIComp2020WalkingERP / 2020 International BCI Competition Track5',cache='WalkingERP',
    hz=100,points=100,classes=2,train_subjects=0,labels={'1':'NonTarget_XXX','2':'Target_OOO'},
    case_splitter=archive_partition,allow_subject_overlap=True,
    subject_overlap_reason='Original within-participant temporal protocol: first180 training, next60 validation, final60 test. Training+validation merged; all15 people intentionally occur in both archive partitions.',
    doi='10.3389/fnhum.2022.898300',paper='Jeong et al. (2022), 2020 International brain-computer interface competition: A review, Frontiers in Human Neuroscience 16:898300, Data Set-E',
    note='Preserve native 100-sample epochs at100Hz (-190 to+800ms inclusive). Native float64 numerical values unchanged; presumed microvolt scale, physical unit not explicitly embedded in supplied MAT/PDF. No additional filter, baseline, resampling or reference change. Select32 scalp and14 ear EEG by original PDF and embedded clab order; exclude4 EOG and6 IMU. Preserve source mnt coordinates without unit/individual-geometry claims; ear coordinates missing. Use native one-hot labels/events for training/validation and original organizer True Label workbook for test, independently cross-checked with pinned loader. Root answer_sheet_tract5.xlsx is a prediction-submission template, not ground truth. Never flatten epochs or include repeated standing calibration arrays. Merge all training files then all validation files, subjects01-15 in each, native epoch order; preserve final test partition. Subject overlap15 is intentional. Original continuous offsets and visit/run IDs unavailable; scalp reference position recovered from the PDF diagram, nominal FCz inferred; ear reference unresolved.',
    evidence_files=['walking-targets-source-lock.json','walking-targets-licence-evidence.json','walking-targets-preparation.md'],
    cache_evidence_files=['Data_description(Track5).pdf','test/Track5_Answer Sheet_Test.xlsx','answer_sheet_tract5.xlsx','original-osf-project.json','original-osf-licence.json','moabb-walking-erp.py'],
    conversion_files=['prepare_walking_erp.py','download_walking_erp.py','predct_inspect.py','prepare_predct.py'],
    validation_updates=dict(cross_split_overlapping_intervals=None,original_continuous_interval_overlap='Not verifiable from epoched source: continuous offsets absent',source_sensor_identity='All included native clab arrays match original PDF56-channel layout; select native EEG indices, preserve order'),
    metadata_updates=dict(original_partition='Organizer-defined training/validation/test temporal partitions',validation_partition=None,
        split_definition='First180 original trials/person plus next60 validation trials form TRAIN; last60 form TEST. Native within-partition order retained. All15 participants shared intentionally.',
        case_order='All original training files subjects01-15, then validation files subjects01-15; test subjects01-15. Native epoch order within each file.',
        source_doi=None,reference_paper_doi='10.3389/fnhum.2022.898300',original_source_url='https://osf.io/pq7vb/',
        original_sampling_frequency_hz=None,distributed_sampling_frequency_hz=100,original_frequency_evidence='Supplied MAT fs100Hz verified; pre-distribution acquisition rate not independently established',
        unit_evidence='Presumed microvolt scale from source MATLAB/EEG-loader convention and physiological amplitudes; no explicit unit field recovered. Numerical scale factor1, no archive rescaling.',
        reference='Scalp diagram shows REF between FC1/FC2 (nominal FCz position inferred), GND between Fp1/Fp2 (nominal Fpz inferred); ear reference unspecified',recording_count=15,distributed_epoch_file_count=45,
        recording_count_scope='Documented walking sequences, one/person; record entries enumerate45 distributed split files. Original continuous file identifiers unavailable.',
        native_input_channels=56,native_eeg_channels=46,excluded_channel_types={'EOG':EOG,'IMU':IMU},
        missing_or_inconsistent_metadata=['Original continuous offsets and acquisition file IDs unavailable; epoch/sample indices are local',
            'Original visit/run IDs unknown; source splits are temporal partitions, not three independently recorded runs',
            'Physical unit, ear reference, original acquisition rate and pre-distribution filtering not explicitly recovered; unit interpretation and nominal scalp reference names are inferred',
            'Native scalp montage coordinates have unspecified units/frame; ear geometry is absent; no individual measured geometry claimed',
            'Test targets are from the published True Label workbook, not the separate prediction-probability submission template',
            'Nominal target fraction0.2 is approximate in supplied data; subject11 has64 targets across300 trials; labels are preserved as published'],
        metadata_evidence=dict(direct='MAT arrays, clab/fs/t/className/y/events/mnt; native XLSX cell labels and source filenames',
            documented='Sensor types, protocol, participant demographics aggregate and temporal split from organizer PDF',
            assigned='Encoded labels, inferred global trial ordinals and walking-recording grouping; unspecified native visit/run IDs remain unknown',
            inferred='Microvolt unit interpretation; no numerical scale change; geometry units/physical reference not invented')))

def prepare(cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),subjects=None,pilot=False):
    spec=copy.deepcopy(SPEC)
    if subjects:
        spec['subjects']=subjects;spec['metadata_updates'].update(recording_count=len(subjects),distributed_epoch_file_count=3*len(subjects))
    if pilot:spec['name']='WalkingTargetsPilot';spec['note']='Subject01 pilot subset. '+spec['note']
    core.SPECS['walking']=spec;core.READERS['walking']=source_records
    result=core.prepare('walking',cache_root,output)
    return finish_sidecars(result,cache_root)

def finish_sidecars(result,cache_root=Path('D:/Data/EEGSources')):
    import csv
    from tools.prepare_predct import removal_pair_audit
    folder=Path(result['path']);cache=Path(cache_root)/'WalkingERP';name=result['dataset']
    path=folder/f'{name}_metadata.json';m=json.loads(path.read_text());changed=[]
    m['reference']=SPEC['metadata_updates']['reference']
    m['source_and_conversion_notes']=SPEC['note']
    m['missing_or_inconsistent_metadata']=SPEC['metadata_updates']['missing_or_inconsistent_metadata']
    m['scalp_reference_evidence']='Original PDF page2 diagram: REF at midline between FC1/FC2 and GND between Fp1/Fp2. FCz/Fpz are nominal positional inferences, not native named reference fields; ear reference not inferred.'
    m['standing_source_role']='6000x56 standing array per person, repeated identically across3 split files; not exported as cases. Total original device-file count is not available.'
    m['aliases']=['BCIComp2020WalkingERP','2020 International BCI Competition Track5','NEMAR nm000184 (mirror ID declared by pinned loader)']
    first=m['recordings'][0]['native_montage'];sensors=m['sensors']
    for sensor in sensors:
        j=ALL.index(sensor['name']);sensor.update(native_channel_index=j,location_role='scalp' if j<32 else 'ear',
            units_evidence='Presumed microvolts; native numeric values unchanged, explicit unit field absent',
            source_x=first['x'][j],source_y=first['y'][j],source_pos3d_x=first['pos_3d'][0][j],
            source_pos3d_y=first['pos_3d'][1][j],source_pos3d_z=first['pos_3d'][2][j],
            coordinate_units='Source units/frame unspecified; values retained without physical rescaling')
    if m['channel_quality']['removed_indices']:
        m['channel_quality']['removal_pair_audit']=removal_pair_audit(cache,folder,m);changed.append(folder/'channel-removal-audit.tsv')
    indices=[ALL.index(n) for n in m['channel_names']]
    for recording in m['recordings']:recording['exported_native_channel_indices']=indices
    core.dump(path,m);changed.append(path)
    p=folder/'channels.tsv'
    with p.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,list(sensors[0]),delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(sensors)
    changed.append(p)
    for split in ['train','test']:
        p=folder/f'cases_{split}.tsv';rows=core.table(p);fields=list(rows[0])
        if 'exported_native_channel_indices' not in fields:fields.append('exported_native_channel_indices')
        for r in rows:r['exported_native_channel_indices']=json.dumps(indices,separators=(',',':'))
        with p.open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fields,delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(rows)
        changed.append(p)
    completeness=folder/'metadata-completeness.json'
    core.dump(completeness,dict(direct='Native IDs, epoch arrays, y/events/className/clab/t/fs/mnt and original True Label cells',
        documented='Sensor roles, trial protocol, aggregate demographics and split from organizer PDF',
        inferred='Global trial ordinals, walking grouping, presumed microvolt scale and nominal scalp reference position names',
        missing=m['missing_or_inconsistent_metadata']));changed.append(completeness)
    for file in SPEC['evidence_files']:
        p=folder/'source_metadata'/file;shutil.copy2(ROOT/'docs'/file,p);changed.append(p)
    attribution=folder/'ATTRIBUTION.txt'
    attribution.write_text(f'{SPEC["source"]}. Original data: https://osf.io/pq7vb/ (no dataset DOI established).\nReference paper: {SPEC["paper"]}; https://doi.org/{SPEC["doi"]}.\nData licence: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/.\nChanges: select EEG in native order, remove globally flat sensors, merge official training and validation, preserve test and export float64 .ts. Source numerical scale unchanged; microvolt interpretation inferred. See metadata and source lock.\n',encoding='utf-8');changed.append(attribution)
    readme=folder/f'README_{name}.md'
    readme.write_text(f'# {name}\n\nTarget OOO versus non-target XXX visual stimuli during treadmill walking. {len(m["channel_names"])} EEG channels, 100 samples at 100 Hz. Native float64 numerical values preserved; microvolt units are inferred, not embedded in source files.\n\nOfficial training and validation are merged, followed in native partition/file/epoch order. Test is unchanged; participants intentionally occur in both splits. No archived validation split. Remove a sensor globally if any case is constant or effectively flat under the archive policy; see channel-removal-audit.tsv. No additional filtering, resampling or reference change.\n\nCase TSV rows match .ts case order. Read identifiers as strings. Original continuous offsets, visit/run IDs, ear reference and pre-distribution acquisition frequency are unknown. Sidecars distinguish native metadata from protocol documentation and inferences.\n',encoding='utf-8');changed.append(readme)
    for file in ['prepare_walking_erp.py','download_walking_erp.py','prepare_open_moabb.py','prepare_predct.py']:
        p=folder/'conversion_code'/file;shutil.copy2(ROOT/'tools'/file,p);changed.append(p)
    p=folder/f'{name}_manifest.json';manifest=json.loads(p.read_text());manifest['source_doi']=None
    manifest.update(reference_paper_doi=SPEC['doi'],original_source_url='https://osf.io/pq7vb/',
        licence_url='https://creativecommons.org/licenses/by/4.0/',label_mapping=SPEC['labels'],
        split_definition=m['split_definition'],subject_overlap_intentional=True,unit_evidence=m['unit_evidence'])
    for file in changed:manifest['artifacts'][file.relative_to(folder).as_posix()]=dict(bytes=file.stat().st_size,sha256=core.sha(file))
    core.dump(p,manifest)
    result['channel_quality']=m['channel_quality'];result['size_GB']=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())/1e9
    report=ROOT/'docs/open-moabb-conversion-results.json';results=json.loads(report.read_text());results['walking']=result;core.dump(report,results)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));p.add_argument('--pilot',action='store_true');a=p.parse_args();prepare(a.cache_root,a.output,['01'] if a.pilot else None,a.pilot)
