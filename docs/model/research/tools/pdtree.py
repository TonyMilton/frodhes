import sys,re
# Print a Pd canvas (by name) with indexed objects and connections; nested canvases shown as single object
path,name=sys.argv[1],sys.argv[2]
txt=open(path,encoding='utf-8',errors='replace').read()
recs=[r.strip() for r in re.split(r';\s*\n',txt) if r.strip()]
stack=[];found=None
def newc(head): return {'head':head,'objs':[],'conns':[]}
for r in recs:
    if r.startswith('#A'): continue
    if r.startswith('#N canvas'):
        stack.append(newc(r)); continue
    if r.startswith('#X restore'):
        c=stack.pop()
        last=c
        nm=' '.join(r.split()[4:])
        if found is None and c['head'].split()[6:7]==[name]: found=c
        if stack: stack[-1]['objs'].append('[SUB '+nm+']')
        continue
    if not stack: continue
    if r.startswith('#X connect'):
        stack[-1]['conns'].append(r.split()[2:]); continue
    p=r.split()
    if p[0]=='#X' and p[1] in('obj','msg','text','floatatom','symbolatom','array','coords'):
        stack[-1]['objs'].append(p[1]+' '+' '.join(p[4:]) if p[1] not in('array','coords') else ' '.join(p[1:]))
    elif p[0]=='#X': stack[-1]['objs'].append(' '.join(p[1:3]))
c=found
if name=='TOP': c=stack[0]
for i,o in enumerate(c['objs']): print(i,o[:150])
print('CONN',' '.join('%s:%s>%s:%s'%tuple(x) for x in c['conns']))
