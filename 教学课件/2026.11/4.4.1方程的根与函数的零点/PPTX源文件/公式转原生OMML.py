"""Small, dependency-free LaTeX subset -> native PowerPoint OMML.

Preserves native editability. This is not a full TeX engine: unsupported commands
raise ValueError so uncertain formulas never silently become pictures/text.
"""
from __future__ import annotations
import copy
import json
import re
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E

NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'a14': 'http://schemas.microsoft.com/office/drawing/2010/main',
}
for _p, _n in NS.items(): E.register_namespace(_p, _n)

def el(tag, *children, **attrs):
    p, local = tag.split(':')
    node = E.Element('{%s}%s' % (NS[p], local))
    for k, v in attrs.items():
        if k.startswith('m_'): k = '{%s}%s' % (NS['m'], k[2:])
        node.set(k, str(v))
    for c in children:
        if c is not None: node.append(c)
    return node

def run_props(size_pt=24, font='Cambria Math', color='000000', italic=False, bold=False):
    return el('a:rPr', el('a:solidFill', el('a:srgbClr', val=color)),
              el('a:latin', typeface=font), el('a:ea', typeface=font),
              el('a:cs', typeface=font), lang='en-US', altLang='zh-CN',
              sz=round(size_pt*100), b=int(bold), i=int(italic))

class LatexParser:
    symbols = {
        'in':'∈','notin':'∉','ne':'≠','neq':'≠','le':'≤','leq':'≤','ge':'≥','geq':'≥',
        'cdot':'⋅','times':'×','pm':'±','mp':'∓','infty':'∞','cup':'∪','cap':'∩',
        'Longleftrightarrow':'⇔','Leftrightarrow':'⇔','Longrightarrow':'⇒',
        'Rightarrow':'⇒','rightarrow':'→','to':'→','iff':'⇔','implies':'⇒',
        'Delta':'Δ','alpha':'α','beta':'β','gamma':'γ','delta':'δ','theta':'θ',
        'lambda':'λ','mu':'μ','pi':'π','sigma':'σ','varepsilon':'ε','epsilon':'ϵ',
        'varnothing':'∅','emptyset':'∅','ldots':'…','cdots':'⋯','colon':':',
        'lbrace':'{','rbrace':'}','lvert':'|','rvert':'|','vert':'|','mid':'|',
        'langle':'⟨','rangle':'⟩','{':'{','}':'}','%':'%','_':'_',
        ',':' ',';':' ',':':' ','!':'','quad':'　','qquad':'　　',' ':' ',
    }
    functions = {'ln','log','lg','exp','sin','cos','tan','max','min','lim','det'}
    def __init__(self, text, size_pt=24, color='000000'):
        self.s=text; self.i=0; self.size=size_pt; self.color=color

    def r(self, text, plain=False, bold=False, chinese=False):
        if not text: return None
        # Math control characters are encoded structurally, never as pictures.
        mpr = el('m:rPr', el('m:sty', m_val='p' if plain or chinese else ('b' if bold else 'i')))
        if chinese: mpr.append(el('m:nor'))
        t=el('m:t'); t.text=text
        t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
        return el('m:r', mpr,
                  run_props(self.size,'Microsoft YaHei' if chinese else 'Cambria Math',self.color,
                            italic=not(plain or chinese),bold=bold), t)

    def ctrl(self): return el('m:ctrlPr',run_props(self.size,color=self.color))
    def arg(self):
        self.ws()
        if self.i>=len(self.s): return []
        if self.s[self.i]=='{':
            self.i+=1; out=self.seq('}'); self.i+=1; return out
        return self.atom()
    def rawarg(self):
        self.ws()
        if self.i>=len(self.s) or self.s[self.i]!='{': raise ValueError('Expected {...}: '+self.s[self.i:])
        self.i+=1; start=self.i; depth=1
        while self.i<len(self.s):
            if self.s[self.i]=='{': depth+=1
            if self.s[self.i]=='}':
                depth-=1
                if depth==0:
                    ret=self.s[start:self.i]; self.i+=1; return ret
            self.i+=1
        raise ValueError('Unclosed group')
    def ws(self):
        while self.i<len(self.s) and self.s[self.i].isspace(): self.i+=1
    def command(self):
        assert self.s[self.i]=='\\'; self.i+=1; start=self.i
        if self.i<len(self.s) and self.s[self.i].isalpha():
            while self.i<len(self.s) and self.s[self.i].isalpha(): self.i+=1
        else: self.i+=1
        return self.s[start:self.i]
    def container(self, tag, items): return el(tag,*items)
    def seq(self, stop=None):
        out=[]
        while self.i<len(self.s):
            self.ws()
            if self.i>=len(self.s) or (stop and self.s[self.i]==stop): break
            base=self.atom()
            sub=sup=None
            while self.i<len(self.s):
                self.ws()
                if self.i>=len(self.s) or self.s[self.i] not in '_^': break
                kind=self.s[self.i]; self.i+=1
                arg=self.arg()
                if kind=='_': sub=arg
                else: sup=arg
            if sub is not None or sup is not None:
                # Scripts attach to the complete immediately preceding atom.
                if sub is not None and sup is not None:
                    base=[el('m:sSubSup',el('m:sSubSupPr',self.ctrl()),el('m:e',*base),el('m:sub',*sub),el('m:sup',*sup))]
                elif sub is not None:
                    base=[el('m:sSub',el('m:sSubPr',self.ctrl()),el('m:e',*base),el('m:sub',*sub))]
                else:
                    base=[el('m:sSup',el('m:sSupPr',self.ctrl()),el('m:e',*base),el('m:sup',*sup))]
            out.extend(x for x in base if x is not None)
        return out
    def atom(self):
        self.ws()
        if self.i>=len(self.s): return []
        c=self.s[self.i]
        if c=='{': self.i+=1; out=self.seq('}'); self.i+=1; return out
        if c!='\\':
            self.i+=1
            if c=='&': c='　'
            return [self.r(c,plain=not(c.isascii() and c.isalpha()),chinese=bool(re.match(r'[\u3400-\u9fff]',c)))]
        cmd=self.command()
        if cmd in ('frac','dfrac','tfrac'):
            num=self.arg(); den=self.arg()
            return [el('m:f',el('m:fPr',el('m:type',m_val='bar'),self.ctrl()),el('m:num',*num),el('m:den',*den))]
        if cmd=='sqrt':
            self.ws(); degree=[]
            if self.i<len(self.s) and self.s[self.i]=='[':
                self.i+=1; degree=self.seq(']'); self.i+=1
            body=self.arg()
            return [el('m:rad',el('m:radPr',el('m:degHide',m_val='0' if degree else '1'),self.ctrl()),el('m:deg',*degree),el('m:e',*body))]
        if cmd in ('left','right','big','Big','bigl','bigr','Bigl','Bigr'):
            # Delimiters remain native editable math glyphs; cases gets stretching below.
            self.ws()
            if self.i<len(self.s) and self.s[self.i]=='.': self.i+=1; return []
            return self.atom()
        if cmd in ('text','textrm','mathrm','mathbf','mathit','operatorname'):
            raw=self.rawarg()
            return [self.r(raw,plain=cmd not in ('mathit','mathbf'),bold=cmd=='mathbf',chinese=bool(re.search(r'[\u3400-\u9fff]',raw)))]
        if cmd=='mathbb':
            raw=self.rawarg(); return [self.r({'R':'ℝ','N':'ℕ','Z':'ℤ','Q':'ℚ','C':'ℂ'}.get(raw,raw),plain=True)]
        if cmd in ('boxed','box'):
            return [el('m:borderBox',el('m:borderBoxPr',self.ctrl()),el('m:e',*self.arg()))]
        if cmd in ('overline','bar'):
            return [el('m:bar',el('m:barPr',el('m:pos',m_val='top'),self.ctrl()),el('m:e',*self.arg()))]
        if cmd in ('underbrace','overbrace'): raise ValueError('unsupported command '+cmd)
        if cmd=='begin':
            env=self.rawarg()
            end='\\end{'+env+'}'
            finish=self.s.find(end,self.i)
            if finish<0: raise ValueError('unclosed environment '+env)
            raw=self.s[self.i:finish]; self.i=finish+len(end)
            if env not in ('cases','aligned','align*','matrix','pmatrix','array'):
                raise ValueError('unsupported environment '+env)
            if env=='array' and raw.startswith('{'): raw=re.sub(r'^\{[^}]*\}','',raw)
            rows=re.split(r'\\\\(?:\[[^]]*\])?',raw.strip())
            cells=[[x.strip() for x in row.split('&')] for row in rows if row.strip()]
            ncols=max(map(len,cells))
            cols=el('m:mcs',el('m:mc',el('m:mcPr',el('m:count',m_val=ncols),el('m:mcJc',m_val='left'))))
            matrix=el('m:m',el('m:mPr',el('m:baseJc',m_val='center'),cols,self.ctrl()))
            for row in cells:
                mr=el('m:mr')
                for cell in row+['']*(ncols-len(row)):
                    mr.append(el('m:e',*LatexParser(cell,self.size,self.color).seq()))
                matrix.append(mr)
            if env=='cases':
                return [el('m:d',el('m:dPr',el('m:begChr',m_val='{'),el('m:endChr',m_val=''),el('m:grow',m_val='1'),self.ctrl()),el('m:e',matrix))]
            if env=='pmatrix':
                return [el('m:d',el('m:dPr',el('m:begChr',m_val='('),el('m:endChr',m_val=')'),self.ctrl()),el('m:e',matrix))]
            return [matrix]
        if cmd in self.functions: return [self.r(cmd,plain=True)]
        if cmd in self.symbols: return [self.r(self.symbols[cmd],plain=True)]
        if cmd in ('displaystyle','textstyle','scriptstyle','limits','nolimits'): return []
        raise ValueError('Unsupported LaTeX command: \\'+cmd+' in '+self.s)

def latex_to_omml(latex, size_pt=24, color='000000', display=False, align='left', bold=False):
    math=el('m:oMath',*LatexParser(latex,size_pt,color).seq())
    if bold:
        for props in math.findall('.//a:rPr',NS): props.set('b','1')
        for style in math.findall('.//m:rPr/m:sty',NS):
            val=style.get('{%s}val'%NS['m'])
            style.set('{%s}val'%NS['m'],'bi' if val=='i' else 'b')
    if display:
        math=el('m:oMathPara',el('m:oMathParaPr',el('m:jc',m_val=align)),math)
    return el('a14:m',math)

def mixed_paragraph(text, size_pt=24, font='Microsoft YaHei', color='000000', align='left', bold=False, math_bold=False, line_spacing=None, paragraph_after_pt=None):
    p=el('a:p')
    ppr=el('a:pPr',algn={'left':'l','center':'ctr','right':'r'}.get(align,align))
    if line_spacing is not None:ppr.append(el('a:lnSpc',el('a:spcPct',val=round(line_spacing*100000))))
    if paragraph_after_pt is not None:ppr.append(el('a:spcAft',el('a:spcPts',val=round(paragraph_after_pt*100))))
    default=run_props(size_pt,font,color,bold=bold); default.tag='{%s}defRPr'%NS['a']
    ppr.append(default);p.append(ppr)
    pure_math = bool(re.fullmatch(r'\$[^$]*\$', text.strip()))
    for piece in re.split(r'(\$[^$]*\$)',text):
        if not piece: continue
        if piece.startswith('$') and piece.endswith('$'):
            p.append(latex_to_omml(piece[1:-1],size_pt,color,display=pure_math,align=align,bold=math_bold))
        else:
            t=el('a:t');t.text=piece;t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
            p.append(el('a:r',run_props(size_pt,font,color,bold=bold),t))
    p.append(el('a:endParaRPr',lang='zh-CN',sz=round(size_pt*100)))
    return p

def patch_pptx(input_path, output_path, specs):
    """specs: dict keyed by unique cNvPr shape name.

    Values are {text:'中文 $\\frac12$ 混排', sizePt:24, align:'left',
                color:'000000', font:'Microsoft YaHei'}.
    Paragraph line breaks are literal newlines. Shape geometry is retained.
    """
    matched=set()
    with ZipFile(input_path) as source, ZipFile(output_path,'w',ZIP_DEFLATED) as target:
        for member in source.infolist():
            data=source.read(member.filename)
            if re.match(r'ppt/slides/slide\d+\.xml$',member.filename):
                root=E.fromstring(data)
                for shape in root.findall('.//p:sp',NS):
                    nv=shape.find('p:nvSpPr/p:cNvPr',NS)
                    name=nv.get('name') if nv is not None else None
                    if name not in specs: continue
                    spec=specs[name];body=shape.find('p:txBody',NS)
                    if body is None: raise ValueError('no txBody on '+name)
                    for old in list(body):
                        if old.tag=='{%s}p'%NS['a']: body.remove(old)
                    for line in spec['text'].split('\n'):
                        body.append(mixed_paragraph(line,spec.get('sizePt',24),spec.get('font','Microsoft YaHei'),spec.get('color','000000'),spec.get('align','left'),spec.get('bold',False),spec.get('mathBold',False),spec.get('lineSpacing'),spec.get('paragraphAfterPt')))
                    matched.add(name)
                data=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
            target.writestr(member,data)
    missing=set(specs)-matched
    if missing: raise ValueError('Shape names not found: '+','.join(missing))
    return len(matched)

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('specs')
    args=ap.parse_args()
    specs=json.loads(Path(args.specs).read_text(encoding='utf-8'))
    print('patched',patch_pptx(args.input,args.output,specs),'shapes')
