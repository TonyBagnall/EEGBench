"""Download the CC0 Chailloux2020 release to a separate source cache."""
import argparse
from pathlib import Path
from tools.download_openneuro_release import download
from tools.prepare_small_moabb import fetch
from tools.prepare_moabb import dump

REVISION='153d0a1633adbf7d079eeabc866a2ad727bcff46'
MOABB_REVISION='bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5'


def prepare_sources(root=Path('D:/Data/EEGSources/Chailloux2020'),pilot=False):
    root=Path(root)
    result=download('ds003190',REVISION,root,'CC0',['sub-01','sub-019'] if pilot else None)
    fetch(f'https://raw.githubusercontent.com/NeuroTechX/moabb/{MOABB_REVISION}/moabb/datasets/chailloux2020.py',root/'moabb-chailloux2020.py')
    if not pilot:dump(Path(__file__).resolve().parents[1]/'docs/symbol-attention-source-lock.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('D:/Data/EEGSources/Chailloux2020'));p.add_argument('--pilot',action='store_true');a=p.parse_args();prepare_sources(a.root,a.pilot)
