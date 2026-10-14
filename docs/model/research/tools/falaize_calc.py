import numpy as np
def brentq(f,a,b):
    for _ in range(200):
        m=(a+b)/2
        if f(a)*f(m)<=0: b=m
        else: a=m
    return (a+b)/2
E=180e9; rho_s=7750.; r=1e-3
Mb=np.pi*r**2*rho_s; Kb=E*np.pi*r**4/4
# roots of cos x cosh x + 1 = 0
roots=[brentq(lambda x: np.cos(x)*np.cosh(x)+1,(m-0.5)*np.pi-0.5,(m-0.5)*np.pi+0.5) for m in range(1,25)]
roots=np.array(roots)
print("Mb",Mb,"Kb",Kb,"betaL",roots[:6],"ratios",(roots[:8]/roots[0])**2)
for f0 in [55,110,220,440,880,1760]:
    k1=((2*np.pi*f0)**2*Mb/Kb)**0.25; L=roots[0]/k1
    fk=f0*(roots/roots[0])**2
    print(f"f0={f0} L={L*1000:.2f}mm M44.1={np.sum(fk<22050)} M48={np.sum(fk<24000)} freqs<22050={np.round(fk[fk<22050],1)}")
# A4 omega (paper/2016 code formula) and psi(L)
f0=440; k1=((2*np.pi*f0)**2*Mb/Kb)**0.25; L=roots[0]/k1; k=roots[:4]/L
wh=0.015; zh=wh+0.1*(L-2*wh)
kl=k*L
t1=np.sqrt(2)*(2*np.sin(k*wh/2)*(np.cos(k*(L-zh))+np.cos(k*zh)*np.cosh(kl)-np.sin(k*zh)*np.sinh(kl))-2*np.sinh(k*wh/2)*(np.cosh(k*(L-zh))+np.cos(kl)*np.cosh(k*zh)+np.sin(kl)*np.sinh(k*zh)))
t2=np.sqrt(k)*np.sqrt(kl*(-2+np.cos(2*kl))+kl*np.cosh(2*kl)-np.cosh(kl)*(2*np.sin(kl)+np.cosh(kl)*np.sin(2*kl)))
print("zh",zh,"omega",t1/t2)
z=L
a=(np.sqrt(2)*(np.sin(k*L)*(np.sin(k*z)-np.sinh(k*z))-np.sinh(k*(L-z))*np.tanh(k*L)+np.sinh(k*L)*(-np.sin(k*z)+np.cos(k*z)*np.tanh(k*L))))
b=(k*L*(-2+np.cos(2*k*L))+k*L*np.cosh(2*k*L)-np.cosh(k*L)*(2*np.sin(k*L)+np.cosh(k*L)*np.sin(2*k*L)))/k
print("psi(L)",a/np.sqrt(b))
# decay
for A in [5e-2]:
    s=A/(2*Mb); print("paper const Ab: sigma",s,"T60",6.9078/s)
a0=0.045; ratio=(roots[:4]/roots[0])**4
sig=a0*ratio/(2*Mb); print("2016 code sigma per mode",sig,"T60",6.9078/sig)
# pyphs netlist: R=2e-3, A=2e-2, D=2, N=4
Mb2=np.pi*(2e-3)**2*7750; Aarr=2e-2*10**np.linspace(0,2,4); s2=Aarr/(2*Mb2); print("pyphs sigma",s2,"T60",6.9078/s2)
# RLC
Cp=330e-9; Lc=1/(Cp*(2*np.pi*5000)**2); print("Lc",Lc,"Lc/N^2",Lc/1e4, "RC corner (paper R=1e3,C=33e-8)",1/(2*np.pi*1e3*33e-8))
# hammer conversions
Lh=15e-3;Fh=13.8;B=2.5;Ah=0.184
print("K=Fh*Lh^-B",Fh*Lh**-B,"R=Ah*Lh^(1-B)",Ah*Lh**(1-B))
# 2016 code Fin & duration
for fin in np.linspace(0.3,0.9,8):
    Fin=round(fin*100)/100*1300; d=np.sqrt(0.15*0.03/Fin); v=Fin*d/0.03
    print(f"Fin={Fin:.0f}N dur={d*1e3:.2f}ms v_hammer~{v:.2f}m/s")
# pickup g(q) shape
def g(q,Lh,Lv,Rp):
    f1=(q-Rp+Lv)**2+Lh**2; f2=(q+Rp+Lv)**2+Lh**2
    return (f1-2*Lh**2)/f1**2-(f2-2*Lh**2)/f2**2
for name,(Lh_,Lv_,Rp_) in {"paper":(1e-2,1e-3,5e-3),"code2016":(1e-3,-2e-4,1e-3),"pyphs":(1e-2,0.5e-3,5e-3)}.items():
    qs=np.linspace(-2e-3,2e-3,9); print(name,np.array2string(g(qs,Lh_,Lv_,Rp_)/abs(g(0,Lh_,Lv_,Rp_)) if g(0,Lh_,Lv_,Rp_)!=0 else g(qs,Lh_,Lv_,Rp_),precision=3), "g(0)=",g(0,Lh_,Lv_,Rp_))
