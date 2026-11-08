"""Refresh enriched sidecars without changing numeric cases, labels or order."""
import csv
import json
from pathlib import Path
import shutil
from tools.prepare_moabb import dump,sha

ROOT=Path(__file__).resolve().parents[1]


def finish(result,metadata,docs,code,manifest_fields,readme=None,attribution=None):
    folder=Path(result['path']);name=result['dataset'];changed=[]
    path=folder/f'{name}_metadata.json';dump(path,metadata);changed.append(path)
    sensors=metadata['sensors'];indices=[s['native_channel_index'] for s in sensors]
    path=folder/'channels.tsv'
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,list(sensors[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(sensors)
    changed.append(path)
    for split in ['train','test']:
        path=folder/f'cases_{split}.tsv';temp=path.with_suffix('.tsv.updating')
        try:
            with path.open(encoding='utf-8',newline='') as src,temp.open('w',encoding='utf-8',newline='') as dst:
                reader=csv.DictReader(src,delimiter='\t');fields=list(reader.fieldnames)
                if 'exported_native_channel_indices' not in fields:fields.append('exported_native_channel_indices')
                writer=csv.DictWriter(dst,fields,delimiter='\t',lineterminator='\n');writer.writeheader()
                for row in reader:
                    row['exported_native_channel_indices']=json.dumps(indices,separators=(',',':'));writer.writerow(row)
            temp.replace(path)
        finally:
            if temp.exists():temp.unlink()
        changed.append(path)
    for filename in docs:
        path=folder/'source_metadata'/filename;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'docs'/filename,path);changed.append(path)
    for filename in list(dict.fromkeys(code+['update_dataset_sidecars.py','prepare_open_moabb.py'])):
        path=folder/'conversion_code'/filename;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'tools'/filename,path);changed.append(path)
    if readme is not None:
        path=folder/f'README_{name}.md';path.write_text(readme,encoding='utf-8');changed.append(path)
    if attribution is not None:
        path=folder/'ATTRIBUTION.txt';path.write_text(attribution,encoding='utf-8');changed.append(path)
    path=folder/'metadata-completeness.json';dump(path,dict(evidence=metadata['metadata_evidence'],missing_or_inconsistent=metadata['missing_or_inconsistent_metadata']));changed.append(path)
    path=folder/f'{name}_manifest.json';manifest=json.loads(path.read_text(encoding='utf-8'));manifest.update(manifest_fields)
    for p in changed:manifest['artifacts'][p.relative_to(folder).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p))
    dump(path,manifest)
    result['size_GB']=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())/1e9
    report=ROOT/'docs/open-moabb-conversion-results.json';results=json.loads(report.read_text(encoding='utf-8'));results[result['source_key']]=result;dump(report,results)
    return result
