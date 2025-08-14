import os, json, hashlib, sys, re
from pathlib import Path

ROOT   = Path(__file__).resolve().parents[1]
PROOFS = ROOT/'proofs'
AUDIT  = ROOT/'audit'/'audit.log'

def canon(o):
    if isinstance(o, dict): return {k: canon(o[k]) for k in sorted(o)}
    if isinstance(o, list): return [canon(x) for x in o]
    return o

def sha256_json(obj:dict)->str:
    s = json.dumps(canon(obj), separators=(',',':')).encode('utf-8')
    return hashlib.sha256(s).hexdigest()

def verify_proofs():
    ok=0; bad=[]
    for p in sorted(PROOFS.glob('*.json')):
        obj = json.loads(p.read_text(encoding='utf-8'))
        obj2 = json.loads(json.dumps(obj)); obj2.pop('sha256', None)
        calc = sha256_json(obj2)
        if calc == obj.get('sha256'): ok+=1
        else: bad.append((p.name, obj.get('sha256'), calc))
    return ok, bad

def verify_audit():
    if not AUDIT.exists(): return True, 0, []
    chain = '0'*64; n=0; bad=[]
    pat = re.compile(r'^([a-f0-9]{64})\s+(.*)$')
    for line in AUDIT.read_text(encoding='utf-8').splitlines():
        m = pat.match(line.strip())
        if not m: bad.append((n,'format')); continue
        head, payload = m.groups()
        ph = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        chain = hashlib.sha256((chain+ph).encode('utf-8')).hexdigest()
        n += 1
        if head != chain: bad.append((n,'mismatch')); break
    return len(bad)==0, n, bad

if __name__=='__main__':
    ok, bad = verify_proofs()
    va, n, bad_a = verify_audit()
    print(f'Proofs OK: {ok}, Bad: {len(bad)}')
    if bad:
        for name, declared, calc in bad[:5]:
            print(f'  - {name}: declared={declared} calc={calc}')
    print(f'Audit chain OK: {va} (lines={n})')
    if bad_a:
        print(f'  Audit errors: {bad_a[:3]}')
    sys.exit(0 if (len(bad)==0 and va) else 1)
