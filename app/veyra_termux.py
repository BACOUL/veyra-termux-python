import os, json, time, hashlib, zipfile, io, threading, statistics
from datetime import datetime, timezone
from flask import Flask, request, send_file, jsonify, send_from_directory

ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROOFS = os.path.join(ROOT, 'proofs')
AUDIT  = os.path.join(ROOT, 'audit')
PUBLIC = os.path.join(ROOT, 'public')
EXPORT = os.path.join(ROOT, 'export')
for d in (PROOFS, AUDIT, PUBLIC, EXPORT): os.makedirs(d, exist_ok=True)
AUDIT_LOG   = os.path.join(AUDIT, 'audit.log')
CHECKPOINTS = os.path.join(AUDIT, 'checkpoints.log')

def canonical(o):
    if isinstance(o, dict): return {k: canonical(o[k]) for k in sorted(o)}
    if isinstance(o, list): return [canonical(x) for x in o]
    return o
def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def sha256_json(obj): return sha256_bytes(json.dumps(canonical(obj),separators=(',',':')).encode('utf-8'))

_CHAIN='0'*64
_LOCK=threading.Lock()
def append_audit(payload:dict):
    global _CHAIN
    s=json.dumps(canonical(payload),separators=(',',':'))
    ph=sha256_bytes(s.encode('utf-8'))
    with _LOCK:
        _CHAIN=sha256_bytes((_CHAIN+ph).encode('utf-8'))
        with open(AUDIT_LOG,'a',encoding='utf-8') as f: f.write(f"{_CHAIN} {s}\n")
    return _CHAIN

CATALOG=[
  {"id":"sub.cancel.gym","title":"Résilier GymClub","estimates":{"time_min":9,"gain_eur":18,"proba":0.97,"impact":1.0,"urgence":1.0,"risque":0.10},"expected_proof":["email","pdf"]},
  {"id":"admin.attestation","title":"Envoyer l’attestation manquante","estimates":{"time_min":4,"proba":0.95,"impact":0.8,"urgence":1.2,"risque":0.05},"expected_proof":["accusé"]},
  {"id":"home.depart7","title":"Préparer 'Départ 7 h'","estimates":{"time_min":1,"proba":0.99,"impact":0.6,"urgence":1.5,"risque":0.02},"expected_proof":["journal"]},
  {"id":"bill.pay","title":"Payer une facture (mock)","estimates":{"time_min":1,"proba":0.99,"impact":0.7,"urgence":1.2,"risque":0.05},"expected_proof":["receipt"]}
]
def score(a):
    e=a.get("estimates",{})
    impact=e.get("impact",1); proba=e.get("proba",0.9); urgence=e.get("urgence",1)
    temps=max(1,e.get("time_min",5)); cout=e.get("cout",0); risque=e.get("risque",0)
    return (impact*proba*urgence)/max(1,(temps*(1+cout))) - risque

app = Flask(__name__, static_folder=None)

@app.after_request
def headers(r):
    r.headers['X-Content-Type-Options']='nosniff'
    r.headers['X-Frame-Options']='DENY'
    r.headers['X-XSS-Protection']='0'
    return r

@app.route('/')
def index(): return send_from_directory(PUBLIC,'app.html')
@app.get('/public/<path:path>')
def pub(path): return send_from_directory(PUBLIC,path)
@app.get('/healthz')
def healthz(): return 'OK',200
@app.get('/readyz')
def readyz(): return ('READY',200)
@app.get('/metrics')
def metrics():
    m={"veyra_proofs_total":len([f for f in os.listdir(PROOFS) if f.endswith('.json')]),
       "veyra_chain_head":_CHAIN}
    return jsonify(m)

@app.get('/today')
def today():
    try: n=min(max(int(request.args.get('n','3')),1),5)
    except: n=3
    ranked=sorted([dict(x,score=score(x)) for x in CATALOG], key=lambda k:k['score'], reverse=True)[:n]
    return jsonify({"date":datetime.now().date().isoformat(),"priorities":ranked})

_IDEM={}
def idem_read():
    key=request.headers.get('Idempotency-Key')
    if not key: return None
    now=time.time()
    for k,(t,resp) in list(_IDEM.items()):
        if now-t>86400: _IDEM.pop(k,None)
    return _IDEM.get(key)

@app.post('/run')
def run():
    cached=idem_read()
    if cached: return jsonify(cached[1])
    t0=time.time()
    body=request.json or {}
    cid=body.get('id'); params=body.get('params',{}) or {}
    card=next((c for c in CATALOG if c['id']==cid),None)
    if not card: return jsonify({"error":"card not found"}),404

    # artefacts éventuels (ex: reçu pour bill.pay)
    artifacts=[]
    if cid=='bill.pay':
        rid=f"receipt_{int(time.time())}.txt"
        rpath=os.path.join(PUBLIC,'receipts',rid)
        os.makedirs(os.path.dirname(rpath),exist_ok=True)
        content=[
            "Veyra — Reçu de paiement (MOCK)",
            f"Date: {datetime.now(timezone.utc).isoformat()}",
            f"Facture: {params.get('invoice_id','INV-DEMO')}",
            f"Bénéficiaire: {params.get('payee','Demo SA')}",
            f"Montant: {params.get('amount_eur', '0.00')} EUR",
            "Méthode: sandbox",
            "Statut: success"
        ]
        open(rpath,'w',encoding='utf-8').write('\n'.join(content))
        artifacts.append(f"/public/receipts/{rid}")

    proof={
      "id":f"p_{int(time.time()*1000)}",
      "action_id":cid,
      "title":card["title"],
      "kind":(card.get("expected_proof") or ["receipt"])[0],
      "timestamp":datetime.now(timezone.utc).isoformat(),
      "level":"N1",
      "costs":{"eur":0,"sec":int(max(1,card["estimates"].get("time_min",1))*60)},
      "result":{"status":"success","notes":"Mock execution OK"},
      "params":params if params else None,
      "artifacts":artifacts
    }
    proof["ttv_sec"]=round(time.time()-t0,4)
    proof["sha256"]=sha256_json(proof)

    with open(os.path.join(PROOFS,f"{proof['id']}.json"),'w',encoding='utf-8') as f:
        json.dump(proof,f,ensure_ascii=False,indent=2)

    append_audit({"RUN":{"proof_id":proof["id"],"card_id":cid,"sha256":proof["sha256"],"ttv_sec":proof["ttv_sec"]}})
    resp={"ok":True,"proof_id":proof["id"],"sha256":proof["sha256"],"ttv_sec":proof["ttv_sec"]}
    key=request.headers.get('Idempotency-Key')
    if key: _IDEM[key]=(time.time(),resp)
    return jsonify(resp)

@app.get('/proofs/<pid>')
def proofs_get(pid):
    p=os.path.join(PROOFS,f"{pid}.json")
    if not os.path.exists(p): return jsonify({"error":"not found"}),404
    return send_file(p,mimetype='application/json')

@app.get('/proofs')
def proofs_list():
    items=[]
    for f in sorted([x for x in os.listdir(PROOFS) if x.endswith('.json')],
                    key=lambda n: os.path.getmtime(os.path.join(PROOFS,n)), reverse=True)[:100]:
        try:
            obj=json.load(open(os.path.join(PROOFS,f),'r',encoding='utf-8'))
            items.append({k:obj.get(k) for k in ("id","title","kind","timestamp","sha256","ttv_sec","result","costs","artifacts")})
        except Exception: pass
    return jsonify({"items":items})

@app.get('/bench')
def bench():
    proofs=[]
    for f in os.listdir(PROOFS):
        if not f.endswith('.json'): continue
        try: proofs.append(json.load(open(os.path.join(PROOFS,f),'r',encoding='utf-8')))
        except Exception: pass
    total=len(proofs); succ=sum(1 for p in proofs if p.get("result",{}).get("status")=="success")
    ttv=[p.get("ttv_sec") for p in proofs if isinstance(p.get("ttv_sec"),(int,float))]
    return jsonify({
        "total_proofs": total, "success": succ, "failure": total-succ,
        "vsr_ratio": (succ/total) if total else None,
        "ttv_median": statistics.median(ttv) if ttv else None,
        "ttv_p95": (statistics.quantiles(ttv, n=100)[94] if len(ttv)>=20 else (max(ttv) if ttv else None)),
    })

@app.get('/export.zip')
def export_zip():
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for f in os.listdir(PROOFS):
            if f.endswith('.json'): z.write(os.path.join(PROOFS,f),arcname=f"proofs/{f}")
        if os.path.exists(AUDIT_LOG): z.write(AUDIT_LOG,arcname="audit/audit.log")
        if os.path.exists(CHECKPOINTS): z.write(CHECKPOINTS,arcname="audit/checkpoints.log")
    buf.seek(0)
    return send_file(buf,as_attachment=True,download_name=f"veyra_export_{int(time.time())}.zip",mimetype='application/zip')

if __name__=='__main__':
    app.run(host='0.0.0.0',port=8787)
# --- Serve homepage ---
from flask import send_from_directory as _sfd

@app.get('/')
def home():
    return _sfd('public', 'index.html')

# --- 404 custom page ---
@app.errorhandler(404)
def not_found(e):
    try:
        return _sfd('public','404.html'), 404
    except Exception:
        return 'Not Found', 404

# --- Pretty routes (serve static pages) ---
from flask import send_from_directory as _sfd

@app.get('/app')
def _app(): return _sfd('public','index.html')

@app.get('/benchmarks')
def _bench(): return _sfd('public','benchmarks.html')

@app.get('/demos')
def _demos(): return _sfd('public','demos.html')

@app.get('/kits')
def _kits(): return _sfd('public','kits.html')

@app.get('/business')
def _biz(): return _sfd('public','business.html')

@app.get('/docs')
def _docs(): return _sfd('public','docs.html')

@app.get('/security')
def _sec(): return _sfd('public','security.html')

@app.get('/help')
def _help(): return _sfd('public','help.html')

@app.get('/privacy')
def _prv(): return _sfd('public','privacy.html')

@app.get('/terms')
def _terms(): return _sfd('public','terms.html')

@app.get('/legal')
def _legal(): return _sfd('public','legal.html')

# PWA / SEO at root-scope
@app.get('/manifest.webmanifest')
def _mf(): return _sfd('public','manifest.webmanifest')
@app.get('/sw.js')
def _sw(): return _sfd('public','sw.js')
@app.get('/robots.txt')
def _rb(): return _sfd('public','robots.txt')
@app.get('/sitemap.xml')
def _sm(): return _sfd('public','sitemap.xml')
