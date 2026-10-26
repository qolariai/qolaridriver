import os,re,json,sys
root=sys.argv[1]; out=sys.argv[2]; dirs=sys.argv[3:]
T={'Z':'boolean','I':'int','J':'long','D':'double','F':'float','S':'short','B':'byte'}
def ty(t):
    a=''
    while t.startswith('['): a+='[]'; t=t[1:]
    t=T.get(t, t[1:-1].replace('/','.') if t.startswith('L') else t)
    return t+a
models={}
for d in dirs:
    for dp,_,fs in os.walk(os.path.join(root,d)):
        for f in fs:
            if not f.endswith('.smali') or '$' in f: continue
            src=open(os.path.join(dp,f),encoding='utf-8',errors='replace').read()
            cls=re.search(r'^\.class .*?L([^;]+);',src,re.M).group(1).replace('/','.')
            if 'interface' in src.split('\n',1)[0]: continue
            fields=[{'name':n,'type':ty(t)} for n,t in re.findall(r'^\.field (?:private|public|protected) final (?!static)(\w+):(\S+)',src,re.M)]
            sig={}
            for n,s in re.findall(r'^\.field private final (\w+):\S+\s*\n\s*\.annotation system Ldalvik/annotation/Signature;\s*\n\s*value = \{([^}]*)\}',src,re.M):
                sig[n]=''.join(re.findall(r'"([^"]*)"',s))
            for fd in fields:
                if fd['name'] in sig: fd['type']=sig[fd['name']].replace('/','.')
            if fields: models[cls]={'fields':fields}
json.dump(models,open(out,'w',encoding='utf-8'),indent=1)
print(len(models))
