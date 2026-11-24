#!/usr/bin/env python3
"""Ordered, offline reproduction from the supplied inputs. Fail closed on errors."""
from pathlib import Path
import argparse,subprocess,sys,os,json,time,platform,hashlib,importlib.metadata
ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--analysis-only',action='store_true',help='Run numerical replication (the default)')
    parser.add_argument('--figures',action='store_true',help='Also regenerate programmatic figures; requires Arial and XeLaTeX')
    args=parser.parse_args()
    if args.analysis_only and args.figures: parser.error('Choose only one mode')
    out=ROOT/'reproduction_run';out.mkdir(exist_ok=True)
    report={'python':sys.version,'platform':platform.platform(),'dependencies':{k:importlib.metadata.version(k) for k in ['numpy','scipy','pandas','matplotlib','PyMuPDF','xlrd']},'steps':[],'scope':'Offline raw-workbook reconstruction and computational replication; not independent causal identification.'}
    report['mode']='analysis-and-figures' if args.figures else 'analysis-only'
    env=os.environ.copy();env['MPLBACKEND']='Agg'
    base=Path('/usr/share/texlive/texmf-dist')
    if base.exists():
        for k,v in {'TEXINPUTS':'tex','TFMFONTS':'fonts/tfm','T1FONTS':'fonts/type1','TEXFONTMAPS':'fonts/map','ENCFONTS':'fonts/enc','VFFONTS':'fonts/vf'}.items():env[k]=str(base/v)+'//:'+env.get(k,'')
    if (ROOT/'pdflatex.fmt').exists():env['TEXFORMATS']=str(ROOT)+':'+env.get('TEXFORMATS','')
    def run(cmd):
        t=time.monotonic();r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True)
        log=out/f'{len(report["steps"])+1:02d}.log';log.write_text(r.stdout+r.stderr)
        report['steps'].append({'command':cmd,'exit_code':r.returncode,'seconds':round(time.monotonic()-t,3),'log':str(log.relative_to(ROOT))})
        print('PASS' if r.returncode==0 else 'FAIL', ' '.join(cmd),flush=True)
        if r.returncode:raise RuntimeError('Failed command; see '+str(log))
    try:
        # Check only immutable input hashes; generated outputs legitimately change.
        provenance=json.loads((ROOT/'data_provenance.json').read_text())
        for item in provenance['inputs']:
            f=ROOT/item['path'];assert hashlib.sha256(f.read_bytes()).hexdigest()==item['sha256'], 'Input hash mismatch: '+str(f)
        run([sys.executable,'replication/build_nhs_aqp_panel.py','--offline'])
        scripts=['verify_models.py','verify_models_round28.py','reproduce_nhanes_access_use.py','research_audit_20261124/nhanes_sensitivity.py','research_audit_20261124/distribution_stress.py','research_audit_20261124/corner_regression.py','replication/audit_nhs_aqp_pretrends.py']
        for f in scripts:run([sys.executable,f])
        nh=json.loads((ROOT/'nhanes_reproduction_results.json').read_text());assert nh['sample_flow']['primary_known_test_recency']==197
        # The stored estimate is beta on the log-odds scale.
        import math
        assert abs(math.exp(nh['primary_adjusted_logit']['beta_recent'])-2.816264656159935)<1e-8
        st=json.loads((ROOT/'research_audit_20261124/distribution_stress_results.json').read_text());assert st['pass'] and st['tested']==1495 and st['sign_failures']==0
        report['numeric_validation']={'n':197,'primary_OR':math.exp(nh['primary_adjusted_logit']['beta_recent']),'stress_tested':st['tested'],'max_errors':st['max_absolute_errors']}
        if args.figures:
            run([sys.executable,'build_visuals.py'])
        report['status']='passed'
    except Exception as e:
        report['status']='failed';report['error']=str(e);raise
    finally:(out/'report.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()
