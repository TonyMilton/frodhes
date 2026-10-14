import sys,urllib.request
# Read only the first 64 bytes (FLAC STREAMINFO) of each remote file via HTTP Range
base='https://raw.githubusercontent.com/sfzinstruments/jlearman.jRhodes3d/master/jRhodes3d-mono/'
for name in sys.argv[1:]:
    req=urllib.request.Request(base+name,headers={'Range':'bytes=0-63'})
    try:
        r=urllib.request.urlopen(req,timeout=20); b=r.read(64)
        total=r.headers.get('Content-Range','')
    except Exception as e:
        print(name,'ERR',e); continue
    if b[:4]!=b'fLaC': print(name,'notflac',b[:8]); continue
    si=b[8:8+34]
    x=int.from_bytes(si[10:18],'big')
    sr=x>>44; ch=((x>>41)&7)+1; bps=((x>>36)&31)+1; ns=x&((1<<36)-1)
    print(name,sr,ch,bps,ns,round(ns/sr,2) if sr else None,total.split('/')[-1])
