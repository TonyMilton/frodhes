import math,re,sys
src=open(sys.argv[1]).read()
Ls=[float(x) for x in re.findall(r'([0-9.]+)f',src.split('{',1)[1])]
assert len(Ls)==73
fs=44100.0;rho=7850;E=2e11;r=1.524e-3;s1=0.001
A=math.pi*r*r;I=math.pi*r**4/4;kap=math.sqrt(E*I/(rho*A));c=math.sqrt(E/rho)
names=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
print("midi,note,f0_hz,L_manual_m,L_eq38_m,L_ratio,f_eb_manualL_hz,oversampling,N_intervals,point_updates_per_out_sample")
tot=[]
for i,Lm in enumerate(Ls):
    n=28+i;f=440*2**((n-69)/12)
    L=math.sqrt(1.426*math.pi*(r/2)*c/(8*f))
    os=4 if n<40 else 8 if n<52 else 16 if n<64 else 32
    k=1/(fs*os);h=math.sqrt((4*s1*k+math.sqrt((4*s1*k)**2+16*kap**2*k**2))/2)
    N=int(L/h); feb=1.426*math.pi*(r/2)/(8*Lm**2)*c
    tot.append(N*os)
    print(f"{n},{names[n%12]}{n//12-1},{f:.2f},{Lm:.4f},{L:.4f},{L/Lm:.3f},{feb:.1f},{os},{N},{N*os}")
print("max",max(tot),"mean",sum(tot)/len(tot),file=sys.stderr)
