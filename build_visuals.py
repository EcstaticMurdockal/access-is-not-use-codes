"""Rebuild the paper's shared-style plots and exact TikZ diagrams."""
from pathlib import Path
import os
import subprocess
import sys
import fitz

ROOT = Path(__file__).resolve().parent
env = os.environ.copy()
# Fallback for the supplied minimal TeX installation; normal TeX Live also works.
base = Path('/usr/share/texlive/texmf-dist')
if base.exists():
    for name, sub in {'TEXINPUTS':'tex','TFMFONTS':'fonts/tfm','T1FONTS':'fonts/type1',
                      'TEXFONTMAPS':'fonts/map','ENCFONTS':'fonts/enc','VFFONTS':'fonts/vf'}.items():
        env[name] = str(base / sub) + '//:' + env.get(name, '')
if (ROOT/'pdflatex.fmt').exists():
    env['TEXFORMATS'] = str(ROOT) + ':' + env.get('TEXFORMATS','')
env['OPENTYPEFONTS'] = '/usr/share/texmf/fonts/opentype//:/usr/share/texlive/texmf-dist/fonts/opentype//:'
env['TEXFONTMAPS'] = '/usr/share/texlive/texmf-dist/fonts/misc//:' + env.get('TEXFONTMAPS','')
# Verify the required font before overwriting any approved figure.
from matplotlib import font_manager
font_manager.findfont('Arial', fallback_to_default=False)
import tempfile
with tempfile.TemporaryDirectory() as tmp:
    probe=Path(tmp)/'fontcheck.tex'
    probe.write_text(r'\documentclass{article}\usepackage{fontspec}\setmainfont{Arial}\begin{document}Arial\end{document}')
    check=subprocess.run(['xelatex','-interaction=nonstopmode','-halt-on-error','-output-directory='+tmp,str(probe)],cwd=ROOT,env=env,capture_output=True,text=True)
    if check.returncode:
        raise RuntimeError('XeLaTeX cannot load Arial. Install a licensed Arial font, or use reproduce_all.py --use-supplied-figures. No figures were overwritten.')
subprocess.run([sys.executable, str(ROOT/'make_paper_figures.py')], check=True, env=env)
for stem in ['causal_evidence_map']:
    result = subprocess.run(['xelatex','-interaction=nonstopmode','-halt-on-error',
        '-output-directory='+str(ROOT/'figures'), str(ROOT/'tikz'/f'{stem}.tex')],
        cwd=ROOT, env=env, capture_output=True, text=True)
    (ROOT/'figures'/f'{stem}.build.log').write_text(result.stdout+result.stderr)
    result.check_returncode()
    doc = fitz.open(ROOT/'figures'/f'{stem}.pdf')
    doc[0].get_pixmap(matrix=fitz.Matrix(2,2)).save(ROOT/'figures'/f'{stem}.png')
print('Rebuilt programmatic paper figures; supplied model artwork retained.')
