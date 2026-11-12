#!/usr/bin/env python3
"""Publisher restricted to Kastigo. Never prints HTTP bodies or credentials."""
import base64, hashlib, json, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
API = 'https://api.github.com/repos/Matisandev/kastigo/contents/index.html'
LOCK = ROOT / '.kastigo-update.lock'
PAT = re.compile(r'(<script\b[^>]*\bid="(data(?:-en|-pt)?)"[^>]*>)(.*?)(</script>)', re.S)
def digest(b): return hashlib.sha256(b).hexdigest()
def api(method='GET', payload=None):
    token = (ROOT / '.github-token').read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9_]+', token): raise ValueError('Formato de credencial no válido')
    # Pass credential via stdin, never command arguments or a published file.
    args = ['curl', '-sS', '--max-time', '45', '--config', '-', '-X', method, API + ('?ref=main' if method=='GET' else '')]
    config = 'header = "Authorization: Bearer '+token+'"\nheader = "Accept: application/vnd.github+json"\n'
    if payload is not None:
        config += 'header = "Content-Type: application/json"\n'
        # Payload is public page content, held in a private run directory.
        f = LOCK / 'payload.json'; f.write_text(json.dumps(payload)); args += ['--data-binary', '@'+str(f)]
    r = subprocess.run(args, input=config, capture_output=True, text=True)
    if r.returncode: raise ValueError('No se pudo conectar de forma segura a GitHub')
    d = json.loads(r.stdout)
    if 'sha' not in d and 'commit' not in d: raise ValueError('GitHub rechazó la operación; revisar acceso o conflicto')
    return d

def blocks(b):
    s=b.decode(); matches=list(PAT.finditer(s))
    if [m[2] for m in matches] != ['data','data-en','data-pt']: raise ValueError('Bloques JSON inesperados')
    return PAT.sub(lambda m:m[1]+m[4],s), {m[2]:json.loads(m[3]) for m in matches}
def structure(a,b,path='',compare_values=False):
    if type(a)!=type(b): raise ValueError('Tipo distinto: '+path)
    if isinstance(a,dict):
        if list(a)!=list(b): raise ValueError('Campos u orden distintos: '+path)
        for k in a: structure(a[k],b[k],path+'/'+k,compare_values)
    elif isinstance(a,list):
        if len(a)!=len(b): raise ValueError('Cantidad distinta: '+path)
        for i,(x,y) in enumerate(zip(a,b)): structure(x,y,path+'/'+str(i),compare_values)
    elif compare_values and not isinstance(a,str) and a!=b: raise ValueError('Valor no textual distinto: '+path)
def validate():
    old=(LOCK/'base.html').read_bytes(); new=(ROOT/'.kastigo-candidate.html').read_bytes()
    shell,a=blocks(old); shell2,b=blocks(new)
    if shell!=shell2: raise ValueError('Cambios fuera de JSON')
    for lang in a:
        structure(a[lang],b[lang])
        for k in ['editorial','stance','stanceName']:
            if a[lang][k]!=b[lang][k]: raise ValueError('Texto fijo modificado')
    for lang in ['data-en','data-pt']: structure(b['data'],b[lang],compare_values=True)
    if len({x['updated'] for x in b.values()})!=1: raise ValueError('Fechas distintas')
    if new==old: raise ValueError('Sin cambios para publicar')
    if (ROOT/'index.html').read_bytes()!=old: raise ValueError('La copia local cambió; no sobrescribir')
    return new

def main():
    mode=sys.argv[1] if len(sys.argv)>1 else 'validate'
    if mode=='begin':
        LOCK.mkdir(mode=0o700) # Existing lock always stops the run; never steal it.
        try:
            remote=api(); b=base64.b64decode(remote['content'])
            if b!=(ROOT/'index.html').read_bytes(): raise ValueError('Local y remoto difieren; reconciliar antes de editar')
            (LOCK/'base.html').write_bytes(b); (LOCK/'sha').write_text(remote['sha'])
            (ROOT/'.kastigo-candidate.html').write_bytes(b)
        except Exception:
            if not list(LOCK.iterdir()): LOCK.rmdir()
            raise
        print('Edición vigente guardada; bloqueo adquirido')
    elif mode=='validate': validate(); print('JSON, estructura, textos fijos y copia local: OK')
    elif mode=='publish':
        b=validate()
        receipt=json.loads((LOCK/'browser-check.json').read_text())
        if receipt.get('sha256')!=digest(b) or receipt.get('passed')!=True: raise ValueError('Falta validación visual de esta edición')
        if api()['sha']!=(LOCK/'sha').read_text(): raise ValueError('Cambió GitHub; publicación cancelada')
        # GitHub rejects changes made after this read through its required SHA.
        d=api('PUT',{'message':'Kastigo: actualización verificada de contenido','content':base64.b64encode(b).decode(),'sha':(LOCK/'sha').read_text(),'branch':'main'})
        (LOCK/'published.json').write_text(json.dumps({'commit':d['commit']['sha'],'sha256':digest(b)}))
        print('ENVIADO',d['commit']['sha'])
        # Do not replace the local file: another editor may have changed it during PUT.
        # Reconciliation is explicit after public verification.
    else: raise ValueError('Modo desconocido')
if __name__=='__main__':
    try: main()
    except Exception as e:
        print('DETENIDO:',str(e) if isinstance(e,ValueError) else type(e).__name__);sys.exit(1)
