"""局部替换复习页，并在其后插入一页归纳；保留其余页面的原生对象。"""
from copy import deepcopy
from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E
import argparse,json,re
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/package/2006/relationships'
OR='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
C='http://schemas.openxmlformats.org/package/2006/content-types'
NS={'p':P,'a':A,'r':OR}
def xml(root):return E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
def names(node):return node.xpath('.//p:cNvPr/@name',namespaces=NS)
def shape(root,name):
    return next(s for s in root.findall('.//p:sp',NS) if s.find('p:nvSpPr/p:cNvPr',NS).get('name')==name)
def set_text_body(root,name,body):
    old=shape(root,name);old.replace(old.find('p:txBody',NS),deepcopy(body))
def set_page(root,value):
    sp=next(s for s in root.findall('.//p:sp',NS) if '_page_' in s.find('p:nvSpPr/p:cNvPr',NS).get('name',''))
    ts=sp.findall('.//a:t',NS)
    if len(ts)!=1:raise ValueError('页码文本框结构异常')
    ts[0].text=str(value)
def new_page(base,fresh,prefix,page_number):
    root=deepcopy(base);tree=root.find('p:cSld/p:spTree',NS)
    for child in list(tree):
        ns=names(child)
        if any(n.startswith('s2_') and n not in ('s2_heading_1','s2_page_2') for n in ns):tree.remove(child)
    old_timing=root.find('p:timing',NS)
    if old_timing is not None:root.remove(old_timing)
    fresh_tree=fresh.find('p:cSld/p:spTree',NS)
    added=0;title=''
    for child in fresh_tree:
        ns=names(child)
        if any(n.startswith(prefix+'_heading_') for n in ns):
            header=child.find('p:txBody',NS)
            set_text_body(root,'s2_heading_1',header)
            title=''.join(header.xpath('.//a:t/text()',namespaces=NS))
            continue
        is_table=child.find('.//a:tbl',NS) is not None
        if not any(n.startswith(prefix+'_') for n in ns) and not is_table:continue
        node=deepcopy(child);added+=1
        for nv in node.findall('.//p:cNvPr',NS):
            nv.set('id',str(100+added))
            if is_table:nv.set('name','review3_table')
        tree.append(node)
    if not title or not added:raise ValueError('未匹配新复习页')
    start=min(1080,max(350,175+sum(37.33 if ord(c)>255 else 19 for c in title)+18))
    rule=next(s for s in root.findall('.//p:sp',NS) if '直接连接符' in s.find('p:nvSpPr/p:cNvPr',NS).get('name',''))
    xf=rule.find('p:spPr/a:xfrm',NS);xf.find('a:off',NS).set('x',str(round(start*9525)));xf.find('a:ext',NS).set('cx',str(round((1204.67-start)*9525)))
    set_page(root,page_number)
    return root
def notes_from(base,text,page_number):
    root=E.fromstring(base)
    body=None
    for sp in root.findall('.//p:sp',NS):
        ph=sp.find('p:nvSpPr/p:nvPr/p:ph',NS)
        if ph is not None and ph.get('type')=='body':body=sp.find('p:txBody',NS);break
    if body is None:raise ValueError('备注中没有正文占位符')
    for p in list(body.findall('a:p',NS)):body.remove(p)
    for line in text.split('\n'):
        p=E.SubElement(body,f'{{{A}}}p');run=E.SubElement(p,f'{{{A}}}r');E.SubElement(run,f'{{{A}}}t').text=line
    for fld in root.findall('.//a:fld',NS):
        if fld.get('type')=='slidenum':
            t=fld.find('a:t',NS)
            if t is not None:t.text=str(page_number)
    return xml(root)
ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('authored');ap.add_argument('output');args=ap.parse_args()
with ZipFile(args.source) as src,ZipFile(args.authored) as author:
    presentation=E.fromstring(src.read('ppt/presentation.xml'));lst=presentation.find('p:sldIdLst',NS)
    if len(lst)!=34 or 'ppt/slides/slide35.xml' in src.namelist():raise ValueError('应从34页当前版本生成')
    base=E.fromstring(src.read('ppt/slides/slide2.xml'))
    changes={
      'ppt/slides/slide2.xml':xml(new_page(base,E.fromstring(author.read('ppt/slides/slide1.xml')),'review2',2)),
      'ppt/slides/slide35.xml':xml(new_page(base,E.fromstring(author.read('ppt/slides/slide2.xml')),'review3',3)),
    }
    # 原第3页起仅更新印刷页码，正文、公式、图象与动画保持原有结构。
    for n in range(3,35):
        root=E.fromstring(src.read(f'ppt/slides/slide{n}.xml'));set_page(root,n+1);changes[f'ppt/slides/slide{n}.xml']=xml(root)
    changes['ppt/notesSlides/notesSlide2.xml']=notes_from(src.read('ppt/notesSlides/notesSlide2.xml'),'来源：用户提供《2.2 从函数观点看一元二次方程》原第2—4、6页。\n授课提示：三组方程与图象对照约2分钟；第一组算根，另两组结合图象口答。三页复习导入合计约4—5分钟。',2)
    changes['ppt/notesSlides/notesSlide35.xml']=notes_from(src.read('ppt/notesSlides/notesSlide2.xml'),'来源：用户提供《2.2 从函数观点看一元二次方程》原第4—6页。\n授课提示：a≠0且定义域为实数集。三个判别式为4、0、−8。重根只对应一个不同横坐标；不再推导求根公式。',3)
    note3=E.fromstring(src.read('ppt/notesSlides/notesSlide3.xml'))
    for t in note3.findall('.//a:t',NS):
        if t.text:t.text=t.text.replace('完整判断放在第16页','完整判断放在第17页')
    changes['ppt/notesSlides/notesSlide3.xml']=xml(note3)
    rels=E.fromstring(src.read('ppt/_rels/presentation.xml.rels'))
    used={r.get('Id') for r in rels};n=1
    while f'rId{n}' in used:n+=1
    rid=f'rId{n}'
    E.SubElement(rels,f'{{{R}}}Relationship',Id=rid,Type=OR+'/slide',Target='slides/slide35.xml')
    sid=E.Element(f'{{{P}}}sldId',id=str(max(int(s.get('id')) for s in lst)+1));sid.set(f'{{{OR}}}id',rid);lst.insert(2,sid)
    changes['ppt/presentation.xml']=xml(presentation);changes['ppt/_rels/presentation.xml.rels']=xml(rels)
    slide_rels=E.fromstring(src.read('ppt/slides/_rels/slide2.xml.rels'))
    for r in slide_rels:
        if r.get('Type','').endswith('/notesSlide'):r.set('Target','../notesSlides/notesSlide35.xml')
    changes['ppt/slides/_rels/slide35.xml.rels']=xml(slide_rels)
    note_rels=E.fromstring(src.read('ppt/notesSlides/_rels/notesSlide2.xml.rels'))
    for r in note_rels:
        if r.get('Type','').endswith('/slide'):r.set('Target','../slides/slide35.xml')
    changes['ppt/notesSlides/_rels/notesSlide35.xml.rels']=xml(note_rels)
    ct=E.fromstring(src.read('[Content_Types].xml'))
    for part,typ in [('/ppt/slides/slide35.xml','application/vnd.openxmlformats-officedocument.presentationml.slide+xml'),('/ppt/notesSlides/notesSlide35.xml','application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml')]:
        E.SubElement(ct,f'{{{C}}}Override',PartName=part,ContentType=typ)
    changes['[Content_Types].xml']=xml(ct)
    if 'docProps/app.xml' in src.namelist():
        app=E.fromstring(src.read('docProps/app.xml'))
        for s in app.iter():
            if E.QName(s).localname=='Slides':s.text='35'
        changes['docProps/app.xml']=xml(app)
    with ZipFile(args.output,'w',ZIP_DEFLATED) as out:
        for info in src.infolist():out.writestr(info,changes.pop(info.filename,src.read(info.filename)))
        for part,data in changes.items():out.writestr(part,data)
print(json.dumps({'slides':35,'reviewPages':[2,3,4],'newNativeTablePage':3,'remainingContentPreserved':True},ensure_ascii=False))
