"""Read small native XLSX tables without optional spreadsheet dependencies."""
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

N={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def xlsx_rows(path,sheet=None):
    with zipfile.ZipFile(path) as z:
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            strings=[''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',N)]
        sheets=ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet',N)
        chosen=next((s for s in sheets if sheet is None or s.attrib['name']==sheet),None)
        if chosen is None:raise ValueError('Unknown sheet')
        rid=chosen.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
        rel=next(r for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels')) if r.attrib['Id']==rid)
        target=rel.attrib['Target'];target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
        rows=[]
        for r in ET.fromstring(z.read(target)).findall('m:sheetData/m:row',N):
            cells={}
            for c in r.findall('m:c',N):
                col=''.join(ch for ch in c.attrib['r'] if ch.isalpha());v=c.find('m:v',N)
                value='' if v is None else v.text
                if c.attrib.get('t')=='s':value=strings[int(value)]
                if c.attrib.get('t')=='inlineStr':value=''.join(c.find('m:is',N).itertext())
                cells[col]=value
            rows.append(cells)
        return rows

def xlsx_records(path,sheet=None):
    rows=xlsx_rows(path,sheet);header=rows[0]
    return [{header[k]:v for k,v in r.items() if k in header and header[k]} for r in rows[1:]]

if __name__=='__main__':
    for f in Path('D:/Data/EEGSources/PREDCT').rglob('*.xlsx'):
        print(f, xlsx_rows(f,'SELECT' if f.name=='Info.xlsx' else None)[:5])
