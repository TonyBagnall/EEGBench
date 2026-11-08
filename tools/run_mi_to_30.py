"""Resume the authorised MI queue unattended, stopping on any failed gate.

Run with the scientific dependencies in requirements-moabb.txt and pyxdf.
Existing pilot workers may finish in the background. Completed original files
are verified again; existing final arrays are never overwritten.
"""
import argparse
import json
from pathlib import Path
import time
import traceback
import uuid

from tools.download_mi_to_30 import download,CONFIG
from tools.prepare_mi_to_30 import prepare
from tools.prepare_moabb import dump,sha
from tools.update_dataset_sidecars import finish

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'docs/mi-to-30-progress.json'


def verify_final(result):
    folder=Path(result['path']);manifest=json.loads((folder/(result['dataset']+'_manifest.json')).read_text(encoding='utf-8'))
    for relative,expected in manifest['artifacts'].items():
        p=(folder/relative).resolve()
        if not p.is_relative_to(folder.resolve()) or p.stat().st_size!=expected['bytes'] or sha(p)!=expected['sha256']:raise ValueError('Final artifact differs '+str(p))
    return result


def refresh_final(result,key,cache_root=None,clear_intermediates=False):
    verify_final(result)
    folder=Path(result['path']);name=result['dataset'];m=json.loads((folder/(name+'_metadata.json')).read_text(encoding='utf-8'))
    if clear_intermediates:
        cache=(Path(cache_root)/CONFIG[key]['source']).resolve();intermediate=(cache/'classification-intermediate-full').resolve()
        if not intermediate.is_relative_to(cache):raise ValueError('Unsafe derived cache directory')
        removed_bytes=0
        for p in intermediate.glob('recording-*.npz'):
            if p.resolve().parent!=intermediate or not p.is_file():raise ValueError('Unsafe derived cache member')
            removed_bytes+=p.stat().st_size;p.unlink()
        m['intermediate_format']='Rebuildable per-recording compressed NPZ float64 case/channel/time; temporary full intermediates cleared only after complete numeric and artifact verification. Original source files and validated .ts outputs retained.'
        m['intermediate_cache_status']='Cleared after validation to preserve disk space; regenerate deterministically from pinned native sources'
        print(key,'released validated temporary NPZ bytes',removed_bytes,flush=True)
    docs=['mi-to-30-preparation.md',key+'-to-30-source-lock.json']
    if key.startswith('pan'):docs+=['pan-full-native-identity-audit.json']
    code=['prepare_mi_to_30.py','mi_to_30_native.py','download_mi_to_30.py','download_original_ranges.py','lock_daly_release.py','audit_pan_identity.py']
    result=finish(result,m,docs,code,dict(source_revision=json.loads((ROOT/'docs'/(key+'-to-30-source-lock.json')).read_text())['source_revision']))
    dump(ROOT/'docs'/(key+'-to-30-conversion-result.json'),result)
    return verify_final(result)


def wait_worker(key,action):
    path=ROOT/'.openeegbench/mi-to-30'/(key+'-'+action+'.json')
    if not path.exists():return False
    deadline=time.time()+24*3600
    while True:
        j=json.loads(path.read_text(encoding='utf-8'))
        if j['status']=='complete':return True
        if j['status']=='error':raise RuntimeError(f'{key} {action} failed; inspect native worker log')
        if time.time()>deadline:raise TimeoutError('Worker did not complete within24hours; inspect before resuming')
        time.sleep(10)


def run(keys,cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG')):
    progress=dict(status='running',keys=keys,completed={},active=None,registered_by_this_runner=False)
    dump(STATE,progress)
    try:
        for key in keys:
            progress['active']=dict(key=key,stage='pilot/source gates');dump(STATE,progress)
            result_path=ROOT/'docs'/(key+'-to-30-conversion-result.json')
            if result_path.exists():
                result=refresh_final(verify_final(json.loads(result_path.read_text(encoding='utf-8'))),key,cache_root,True)
            else:
                # A separately launched full Pan job owns these destinations.
                # Wait for its result; inspect its error file rather than race it.
                if key.startswith('pan') and (ROOT/'.openeegbench/mi-to-30/run-pan-full.py').exists():
                    deadline=time.time()+8*3600
                    while not result_path.exists():
                        error=ROOT/'.openeegbench/mi-to-30/pan-full.err'
                        if error.exists() and 'Traceback' in error.read_text(encoding='utf-8'):raise RuntimeError('Existing Pan full worker failed; inspect its log')
                        if time.time()>deadline:raise TimeoutError('Existing Pan full conversion did not finish')
                        time.sleep(10)
                    result=refresh_final(verify_final(json.loads(result_path.read_text(encoding='utf-8'))),key,cache_root,True)
                else:
                    pilot_result=ROOT/'docs'/(key+'-to-30-pilot-result.json')
                    if not pilot_result.exists():
                        if not wait_worker(key,'download-pilot'):download(key,cache_root,pilot=True)
                        prepare(key,cache_root,output,pilot=True)
                    progress['active']=dict(key=key,stage='full source download');dump(STATE,progress)
                    wait_worker(key,'download-full')
                    download(key,cache_root,pilot=False)
                    progress['active']=dict(key=key,stage='full conversion and validation');dump(STATE,progress)
                    result=refresh_final(prepare(key,cache_root,output,pilot=False),key,cache_root,True)
            progress['completed'][key]=result;progress['active']=None;dump(STATE,progress)
            print(key,'VALIDATED FULL OUTPUT',result['path'],flush=True)
        from tools.register_mi_to_30 import register
        register(progress['completed'])
        for key,result in progress['completed'].items():progress['completed'][key]=refresh_final(result,key)
        progress['registered_by_this_runner']=True
        import pytest
        status=pytest.main(['-q','-p','no:cacheprovider','--basetemp='+str(ROOT/'.openeegbench'/('mi-final-tests-'+uuid.uuid4().hex)),str(ROOT/'tools/test_prepare_mi_to_30.py'),str(ROOT/'tools/test_prepare_open_moabb.py'),str(ROOT/'eegbench/tests/test_datasets.py')])
        if status:raise RuntimeError('Final registry/conversion tests failed: '+str(status))
        progress['status']='complete_registered_and_verified';dump(STATE,progress)
        checkpoint=ROOT/'.openeegbench/current-batch-checkpoint.json'
        if checkpoint.exists():
            c=json.loads(checkpoint.read_text());c.update(status='mi_to_30_complete',completed=[r['dataset'] for r in progress['completed'].values()],active_keys=[],batch_runner_pid=None,next='All five converted, registered locally and verified; inspect metadata before any release');dump(checkpoint,c)
        handover=ROOT/'DATASET_CONVERSION_HANDOVER.md';text=handover.read_text(encoding='utf-8')
        message='## MI queue completed\n\nAll five full preparations passed and were registered locally. Read [current progress](docs/assimilation-progress.json), [batch results](docs/mi-to-30-progress.json) and [summary](docs/mi-to-30-summary.json). Original paper arrays/results unchanged; no uploads or pushes. Active-queue text below is historical.\n\n'
        handover.write_text(text.replace('## Active MI queue towards thirty',message+'## Previous active MI queue towards thirty',1),encoding='utf-8')
        return progress
    except BaseException as exc:
        progress.update(status='stopped_for_review',error=str(exc),traceback=traceback.format_exc());dump(STATE,progress);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--datasets',nargs='+',choices=CONFIG,default=['pan25','pan23','rozado','daly','cho']);p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));a=p.parse_args();run(a.datasets,a.cache_root,a.output)
