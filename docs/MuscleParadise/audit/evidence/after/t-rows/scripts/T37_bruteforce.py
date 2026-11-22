import httpx, json, time, collections, sys
B='http://127.0.0.1:8010'
c=httpx.Client(base_url=B, timeout=30)
time.sleep(65)  # fresh rate-limit window
phone='09139900037'
r=c.post('/api/v1/auth/otp/request', json={'phone':phone}); code=r.json()['dev_code']
t0=time.time(); st=[]
for i in range(60):
    w=f"{(int(code)+i+1)%1000000:06d}"
    if w==code: w=f"{(int(code)+i+2)%1000000:06d}"
    st.append(c.post('/api/v1/auth/otp/verify', json={'phone':phone,'code':w}).status_code)
dt=time.time()-t0
real=c.post('/api/v1/auth/otp/verify', json={'phone':phone,'code':code})
replay=c.post('/api/v1/auth/otp/verify', json={'phone':phone,'code':code})
res={'test':'T37-bruteforce (reconstructed; kit probe lacks this mode)','guesses':len(st),'elapsed_s':round(dt,3),
     'guesses_per_s':round(len(st)/dt,1),'status_histogram':dict(collections.Counter(st)),
     'real_code_after_burst_status':real.status_code,'replay_status':replay.status_code,
     'replay_body':replay.text[:120]}
json.dump(res,open('/home/user/MP/docs/MuscleParadise/audit/evidence/after/t-rows/T37-otp-bruteforce.json','w'),ensure_ascii=False,indent=1)
print(json.dumps(res,ensure_ascii=False))
