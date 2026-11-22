import ast, json, pathlib, re
root=pathlib.Path('/home/user/MP/mp-app/backend')
sites=[]; guarded=[]
for f in sorted(root.rglob('*router*.py')):
    if 'tests' in f.parts or '.venv' in f.parts: continue
    tree=ast.parse(f.read_text(encoding='utf-8'))
    for fn in ast.walk(tree):
        if not isinstance(fn,(ast.FunctionDef,ast.AsyncFunctionDef)): continue
        for dec in fn.decorator_list:
            if not (isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute) and dec.func.attr in ('get','post','put','patch','delete')): continue
            if not dec.args or not isinstance(dec.args[0],ast.Constant) or not isinstance(dec.args[0].value,str): continue
            path=dec.args[0].value
            for pname in re.findall(r'\{(\w+)\}',path):
                arg=next((a for a in fn.args.args+fn.args.kwonlyargs if a.arg==pname),None)
                if arg is None or arg.annotation is None: continue
                ann=ast.unparse(arg.annotation)
                rel=str(f.relative_to(root))
                if 'PathId' in ann or re.search(r'Path\(\s*(gt|ge|lt|le)=',ann):
                    guarded.append([rel,dec.func.attr.upper(),path,pname,ann])
                elif ann.strip()=='int' or re.fullmatch(r'Annotated\[int,\s*Path\(\)\]',ann.strip()):
                    sites.append([rel,dec.func.attr.upper(),path,pname,'int'])
by={}
for s in sites: by[s[0]]=by.get(s[0],0)+1
res={'guarded_total':len(guarded),'bare_total':len(sites),'bare_by_file':by,'sites':sites,'guarded':guarded}
json.dump(res,open('/home/user/MP/docs/MuscleParadise/audit/evidence/after/t-rows/T23-pathid-scan.json','w'),ensure_ascii=False,indent=1)
print('guarded',len(guarded),'bare',len(sites))
