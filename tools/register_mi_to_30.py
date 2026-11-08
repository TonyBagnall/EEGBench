"""Register only completely validated MI preparations; never modify paper data."""
import importlib
import json
from pathlib import Path
import re

from tools.prepare_moabb import dump

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'Blink','ButtonPress','Sleep','EpilepticSeizures'}


def register(results):
    from eegbench import datasets
    importlib.reload(datasets)
    old=len(datasets.eegbench);old_local=len(datasets.local_only);old_selected=len((ROOT/'eeg.txt').read_text().splitlines())
    entries=[]
    for key,r in results.items():
        if r['dataset'].endswith('Pilot'):raise ValueError('Cannot register a pilot')
        folder=Path(r['path']);m=json.loads((folder/(r['dataset']+'_metadata.json')).read_text(encoding='utf-8'))
        if m['name']!=r['dataset'] or not r['train_cases'] or not r['test_cases']:raise ValueError('Inconsistent final registration')
        row=(r['dataset'],r['channels'],r['classes'],r['timepoints'],r['subjects'],r['train_cases'],r['test_cases'],r['frequency'],'BCI')
        existing=[v for v in datasets._TABLE if v[0]==r['dataset']]
        if existing and existing!=[row]:raise ValueError('Existing registry row differs; review required')
        if not existing:entries.append(row);datasets._TABLE.append(row)
    if not entries:return
    datasets._TABLE.sort(key=lambda r:r[0]);count=len(datasets._TABLE);local=count-30;selected=sorted(r[0] for r in datasets._TABLE if r[0] not in EXCLUDED)
    p=ROOT/'eegbench/datasets.py';text=p.read_text(encoding='utf-8');marker='_TABLE.sort(key=lambda row: row[0])'
    if text.count(marker)!=1:raise ValueError('Registry insertion marker changed')
    text=text.replace(marker,'_TABLE += '+repr(entries)+'\n\n'+marker).replace(f'and {old_local} additional local preparations',f'and {local} additional local preparations').replace(f'All {old} prepared classification',f'All {count} prepared classification');p.write_text(text,encoding='utf-8')
    importlib.reload(datasets) # Recompute local_only and availability before rendering.
    p=ROOT/'eeg.txt';p.write_text('\n'.join(selected)+'\n',encoding='utf-8')
    p=ROOT/'README.md';text=p.read_text(encoding='utf-8')
    for a,b in [(f'archive of {old} EEG',f'archive of {count} EEG'),(f'of the {old} datasets',f'of the {count} datasets'),(f'The {old_local}\nnewer preparations',f'The {local}\nnewer preparations'),(f'All {old} are in',f'All {count} are in'),(f'requests all {old} and',f'requests all {count} and')]:text=text.replace(a,b)
    p.write_text(text,encoding='utf-8')
    p=ROOT/'eegbench/tests/test_datasets.py';text=p.read_text(encoding='utf-8').replace(f'All {old} problems',f'All {count} problems').replace(f'len(set(eegbench)) == {old}',f'len(set(eegbench)) == {count}').replace(f'len(local_only) == {old_local}',f'len(local_only) == {local}');p.write_text(text,encoding='utf-8')
    p=ROOT/'docs/datasets.md';text=p.read_text(encoding='utf-8');text=re.sub(r'(?s)(<!-- DATASETS:START -->).*?(<!-- DATASETS:END -->)',lambda m:m[1]+'\n\n'+datasets.metadata_markdown()+'\n\n'+m[2],text)
    text=text.replace(f'contains {old} prepared',f'contains {count} prepared').replace(f'contains {old_selected} problems',f'contains {len(selected)} problems')
    descriptions=[];provenance=[]
    for key,r in results.items():
        name=r['dataset'];folder=Path(r['path']);m=json.loads((folder/(name+'_metadata.json')).read_text(encoding='utf-8'))
        description=(f'### {name} ({m["source_dataset"]})\n\n'
          f'{r["subjects"]} participants; {r["train_cases"]} training and {r["test_cases"]} test cases, {r["channels"]} channels x {r["timepoints"]} samples at {r["frequency"]} Hz. '
          f'Classes: '+', '.join(m['label_mapping'].values())+'.\n\n'
          f'{m["split_definition"]}. No separate validation archive. {m["source_and_conversion_notes"]}\n\n'
          f'Original source [{m["source_doi"]}]({m["original_source_url"]}), {m["licence"]}. '
          f'{m.get("channel_identity_status", "See ordered native sensor table")}. '
          f'Array-aligned case tables, sensor information, source receipts and all quality exclusions accompany `D:/Data/EEG/{name}`. '
          f'Native and documented/inferred metadata are distinguished. See [{key} source lock]({key}-to-30-source-lock.json) and [conversion result]({key}-to-30-conversion-result.json).\n')
        descriptions.append(description)
        provenance.append(f'### {name}\n\nOriginal/source aliases: **{m["source_dataset"]}**. [{m["source_doi"]}]({m["original_source_url"]}); {m["reference"]}. '
          f'Data grant: {m["licence"]}. Revision: {m["source_revision"]}. '
          f'{r["subjects"]} native participant IDs; {r["channels"]} x {r["timepoints"]}, {r["frequency"]} Hz, {r["classes"]} classes, {r["train_cases"]}/{r["test_cases"]} TRAIN/TEST. '
          f'{m["split_definition"]}. {m["source_and_conversion_notes"]} '
          f'Match original source file IDs/hashes and native case indices using [{key} source lock]({key}-to-30-source-lock.json); repository aliases do not establish different recordings. '
          +(f'Both complete Pan releases passed the [native waveform comparison](pan-full-native-identity-audit.json); participant identity across studies remains unestablished. ' if key.startswith('pan') else '')+'\n')
    text+='\n## Further motor imagery preparations\n\n'+'\n'.join(descriptions);p.write_text(text,encoding='utf-8')
    p=ROOT/'docs/dataset-provenance.md';p.write_text(p.read_text(encoding='utf-8')+'\n## Further motor imagery source identities\n\n'+'\n'.join(provenance),encoding='utf-8')
    p=ROOT/'docs/assimilation-progress.json';progress=json.loads(p.read_text(encoding='utf-8'));progress.update(registered=count,selected=len(selected),motor_imagery_problems=progress['motor_imagery_problems']+len(entries),scalp_eeg_motor_imagery_problems=progress['scalp_eeg_motor_imagery_problems']+len(entries),completed_latest=[r['dataset'] for r in results.values()],in_progress={},completion_report='docs/mi-to-30-preparation.md',next_candidate=None)
    progress['latest_batch']=dict(problems=progress['completed_latest'],locations={r['dataset']:r['path'] for r in results.values()},report='docs/mi-to-30-progress.json',manifest_artifacts_verified=True)
    for key in ['pan23','cho']:
        if key in results:progress['flags'][results[key]['dataset']]='Anatomical names absent from native MAT; opaque original column identifiers and source positions/mapping evidence retained, no invented labels'
    dump(p,progress)
    fields=['dataset','train_cases','test_cases','subjects','channels','timepoints','classes','frequency','size_GB','licence']
    summary=[{k:r[k] for k in fields} for r in results.values()];dump(ROOT/'docs/mi-to-30-summary.json',summary)
    p=ROOT/'docs/mi-to-30-preparation.md';text=p.read_text(encoding='utf-8')+'\n## Completed full preparations\n\n| '+' | '.join(fields)+' |\n|'+'---|'*len(fields)+'\n'
    text+='\n'.join('| '+' | '.join(f'{r[k]:.3f}' if k=='size_GB' else str(r[k]) for k in fields)+' |' for r in summary)+'\n';p.write_text(text,encoding='utf-8')
    dump(ROOT/'docs/mi-to-30-metadata-completeness.json',{key:json.loads((Path(r['path'])/'metadata-completeness.json').read_text()) for key,r in results.items()})
