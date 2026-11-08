"""Bounded BCI2000 v1.1 native reader; raw sample/state order is unchanged.

Format and calibration: https://www.bci2000.org/mediawiki/index.php/Technical_Reference:BCI2000_File_Format
and User_Reference:DataIOFilter. No default sensor identities or gain values.
"""
from pathlib import Path
import re
from urllib.parse import unquote
import numpy as np


def parameter_list(parameters,key):
    tokens=parameters[key].split();n=int(tokens[0])
    if len(tokens)<n+1:raise ValueError('Incomplete native parameter list '+key)
    return [unquote(t) for t in tokens[1:n+1]]


def read(path):
    path=Path(path)
    with path.open('rb') as f:
        first=f.readline(4096)
        fields=dict((k.decode(),v.decode()) for k,v in re.findall(rb'(\w+)=\s*(\S+)',first))
        nheader=int(fields['HeaderLen']);nch=int(fields['SourceCh']);ns=int(fields['StatevectorLen'])
        if not 0<nheader<=16*1024*1024 or not 0<nch<=2048 or not 0<ns<=4096:raise ValueError('Invalid native dimensions')
        f.seek(0);header=f.read(nheader)
    if len(header)!=nheader:raise ValueError('Truncated native header')
    text=header.decode('latin1');parameters={};states={};section=None
    for line in text.splitlines()[1:]:
        line=line.strip()
        if not line:continue
        if line.startswith('['):section=line;continue
        if section=='[ Parameter Definition ]':
            m=re.match(r'\S+\s+\S+\s+(\w+)=\s*(.*)',line)
            if m:parameters[m[1]]=m[2].split('//',1)[0].strip()
        elif section=='[ State Vector Definition ]':
            t=line.split()
            if len(t)==5:states[t[0]]=dict(bits=int(t[1]),initial=int(t[2]),byte=int(t[3]),bit=int(t[4]))
    dtype={'float32':'<f4','int16':'<i2','int32':'<i4'}.get(fields.get('DataFormat','int16'))
    if dtype is None:raise ValueError('Unsupported native numeric format')
    record=np.dtype([('signal',dtype,(nch,)),('states','u1',(ns,))])
    size=path.stat().st_size-nheader
    if size<=0 or size%record.itemsize:raise ValueError('Incomplete native binary records')
    data=np.memmap(path,mode='r',dtype=record,offset=nheader)
    sfreq=float(parameters['SamplingRate'].split()[0].removesuffix('Hz'))
    gains=np.array([float(x.removesuffix('muV')) for x in parameter_list(parameters,'SourceChGain')],dtype=np.float64)
    offsets=np.array([float(x) for x in parameter_list(parameters,'SourceChOffset')],dtype=np.float64)
    if gains.shape!=(nch,) or offsets.shape!=(nch,) or not np.isfinite(gains).all() or not np.isfinite(offsets).all() or (gains<=0).any():raise ValueError('Invalid explicit native calibration')
    return dict(data=data,parameters=parameters,states=states,frequency=sfreq,gains=gains,offsets=offsets,header=text,n_channels=nch)


def state(recording,name):
    definition=recording['states'][name];bits=definition['bits'];offset=definition['byte']*8+definition['bit']
    if not 0<bits<=32 or offset+bits>recording['data']['states'].shape[1]*8:raise ValueError('Invalid state bit range')
    values=np.zeros(len(recording['data']),dtype=np.uint64)
    for b in range(bits):values|=((recording['data']['states'][:,(offset+b)//8]>>((offset+b)%8))&1).astype(np.uint64)<<b
    return values


def intervals(values):
    values=np.asarray(values)
    edges=np.r_[0,np.flatnonzero(values[1:]!=values[:-1])+1,len(values)]
    return [(int(a),int(b),int(values[a])) for a,b in zip(edges[:-1],edges[1:]) if values[a]!=0]


def calibrated(recording,start,stop):
    # Cast before subtracting offset/multiplying gain, not after float32 math.
    x=np.asarray(recording['data']['signal'][start:stop],dtype=np.float64)
    return np.ascontiguousarray(((x-recording['offsets'])*recording['gains']).T,dtype='<f8')
