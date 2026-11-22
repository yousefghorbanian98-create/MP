import json, subprocess, shutil, sys
W='/tmp/mutwork'; MOD='modules/payments/manual_transfer_policy.py'; TF='tests/regression/test_manual_transfer_policy.py'
wit=json.load(open('/home/user/audit-run/kit/unpacked/MP-BUILDER-KIT-2026-11-21/04-evidence/raw/mutmut-verified.json'))
orig_path=f'{W}/{MOD}'; orig=open(orig_path,encoding='utf-8').read().split('\n')
out=[]; mismatch=0
for m in wit['results']:
    lines=orig[:]
    hits=[i for i,l in enumerate(lines) if l.strip()==m['original'].strip()]
    if len(hits)!=1:
        mismatch+=1; out.append({'id':m['id'],'status':'CONTENT_MATCH_%d'%len(hits),'original':m['original']}); continue
    idx=hits[0]
    lines[idx]=lines[idx].replace(m['original'].strip(), m['mutant'].strip(),1)
    out_line=idx+1
    open(orig_path,'w',encoding='utf-8').write('\n'.join(lines))
    r=subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider',TF],cwd=W,capture_output=True,text=True)
    tail=r.stdout.strip().split('\n')[-1]
    out.append({'id':m['id'],'witness_line':m['line'],'line':out_line,'mutant':m['mutant'],'pytest_rc':r.returncode,'killed':r.returncode!=0,'summary':tail,'witness_killed':m['killed']})
open(orig_path,'w',encoding='utf-8').write('\n'.join(orig))
k=sum(1 for x in out if x.get('killed')); total=len(wit['results'])
agree=sum(1 for x in out if x.get('killed')==x.get('witness_killed'))
res={'module':MOD,'total':total,'line_mismatch':mismatch,'killed':k,'survived':total-k-mismatch,'score_pct':round(100*k/total,1),'agree_with_witness':agree,'results':out}
json.dump(res,open('/home/user/MP/docs/MuscleParadise/audit/evidence/after/t-rows/T21-mutmut-manual.json','w'),ensure_ascii=False,indent=1)
print(json.dumps({k2:v for k2,v in res.items() if k2!='results'}))
