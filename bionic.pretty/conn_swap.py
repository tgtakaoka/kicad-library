"""Point a project's Bionic connectors at the populated header models.

    cd <repo>/schematics && python3 ~/kicad-library/bionic.pretty/conn_swap.py

In every board directory below the current one, the Bionic-P135/P245 SMT
and THT footprints (board copies and bionic.pretty) get
${KIPRJMOD}/bionic.pretty/Bionic-{SMT,THT}_1x24.step in place of KiCad's
full 1x24 header, and the STEP is copied in. The _Vertical footprints,
which have all 24 pins, are left alone.
"""
import re,glob,os,shutil
LIB=os.path.expanduser('~/kicad-library/bionic.pretty')
NEW={'SMT':'${KIPRJMOD}/bionic.pretty/Bionic-SMT_1x24.step','THT':'${KIPRJMOD}/bionic.pretty/Bionic-THT_1x24.step'}
OLD={'SMT':r'PinHeader_1x24_P2\.54mm_Vertical_SMD_Pin1Right\.(?:step|wrl)','THT':r'PinHeader_1x24_P2\.54mm_Vertical\.(?:step|wrl)'}
def fix_block(blk,kind):
    return re.sub(r'\(model "\$\{[A-Z0-9_]+\}/Connector_PinHeader_2\.54mm\.3dshapes/'+OLD[kind]+'"','(model "'+NEW[kind]+'"',blk)
def blocks(s):
    for m in re.finditer(r'\(footprint "[^"]*Bionic-P(?:135|245)_(SMT|THT)"',s):
        j=m.start(); d=0; k=j
        while True:
            if s[k]=='(': d+=1
            elif s[k]==')':
                d-=1
                if d==0: break
            k+=1
        yield m.group(1),j,k+1
total={}
for d in sorted(glob.glob('*/')):
    used=set(); n=0
    for pcb in glob.glob(d+'*.kicad_pcb'):
        s=open(pcb).read(); out=[]; last=0
        for kind,a,b in blocks(s):
            nb=fix_block(s[a:b],kind)
            if nb!=s[a:b]: n+=1
            out.append(s[last:a]); out.append(nb); last=b; used.add(kind)
        out.append(s[last:]); ns=''.join(out)
        if ns!=s: open(pcb,'w').write(ns)
    for kind in sorted(used):
        for fp in glob.glob(d+f'bionic.pretty/Bionic-P*_{kind}.kicad_mod'):
            s=open(fp).read(); ns=fix_block(s,kind)
            if ns!=s: open(fp,'w').write(ns)
        shutil.copy(f'{LIB}/Bionic-{kind}_1x24.step', d+'bionic.pretty/')
    if n: total[d.rstrip('/')]=(n,sorted(used))
for k,v in total.items(): print(k,v)
print(len(total),'dirs')
