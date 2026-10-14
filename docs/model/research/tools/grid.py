import math, numpy as np
fs=44100.0
rho=7850; E=2e11
def calc(r, s0, s1, os_fn, notes):
    A=math.pi*r*r; I=math.pi*r**4/4; kap=math.sqrt(E*I/(rho*A)); c=math.sqrt(E/rho)
    out=[]
    for n in notes:
        f=440*2**((n-69)/12)
        L=math.sqrt(1.426*math.pi*(r/2)*c/(8*f))
        os=os_fn(n); k=1/(fs*os)
        h=math.sqrt((4*s1*k+math.sqrt((4*s1*k)**2+16*kap**2*k**2))/2)
        N=int(L/h)
        out.append((n,round(f,2),round(L,4),os,N,N*os))
    return out
osc=lambda n: 4 if n<40 else 8 if n<52 else 16 if n<64 else 32
for r,lab in [(1.524e-3,'code r'),(0.5e-3,'thesis r')]:
    print(lab)
    res=calc(r,0.0005,0.001,osc,range(28,101,6))
    for x in res: print(x)
    # also no oversampling
    res=calc(r,0.0005,0.001,lambda n:1,[28,40,52,64,76,88,100])
    print('os=1', [(x[0],x[4]) for x in res])
# with true tine lengths
L0=[0.1564,0.0226]
