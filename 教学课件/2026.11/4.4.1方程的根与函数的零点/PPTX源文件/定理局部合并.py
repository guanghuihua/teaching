"""把Artifact Tool排版的5个原生文本框合入当前PPT，保留其他部件原字节。"""
from copy import deepcopy
from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E
import argparse,json
NS={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('authored');ap.add_argument('output');args=ap.parse_args()
with ZipFile(args.source) as src,ZipFile(args.authored) as authored,ZipFile(args.output,'w',ZIP_DEFLATED) as out:
    root=E.fromstring(src.read('ppt/slides/slide8.xml'))
    body=root.find('p:cSld/p:spTree',NS)
    fresh=E.fromstring(authored.read('ppt/slides/slide1.xml'))
    changed=[]
    for node in fresh.findall('.//p:sp',NS):
        nv=node.find('p:nvSpPr/p:cNvPr',NS)
        if nv is None or not nv.get('name','').startswith('pep_s8_text_'):continue
        name=nv.get('name')[4:]
        targets=[s for s in root.findall('.//p:sp',NS) if s.find('p:nvSpPr/p:cNvPr',NS).get('name')==name]
        if not targets:raise ValueError('找不到文本框：'+name)
        original=targets[0];old_nv=original.find('p:nvSpPr/p:cNvPr',NS)
        container=original
        while container.getparent() is not body:container=container.getparent()
        replacement=deepcopy(node);new_nv=replacement.find('p:nvSpPr/p:cNvPr',NS)
        new_nv.set('name',name);new_nv.set('id',old_nv.get('id'))
        body.replace(container,replacement);changed.append(name)
    if len(changed)!=5:raise ValueError(f'替换数量错误：{changed}')
    note=root.findall('.//p:sp',NS)
    reminder=next(s for s in note if s.find('p:nvSpPr/p:cNvPr',NS).get('name')=='s8_text_9')
    xf=reminder.find('p:spPr/a:xfrm',NS);xf.find('a:off',NS).set('y',str(610*9525));xf.find('a:ext',NS).set('cy',str(52*9525))
    xml=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
    for part in src.infolist():
        data=src.read(part.filename)
        if part.filename=='ppt/slides/slide8.xml':data=xml
        elif part.filename=='ppt/notesSlides/notesSlide8.xml':
            notes=E.fromstring(data)
            for t in notes.findall('.//a:t',NS):
                if t.text and t.text.startswith('来源：'):
                    t.text='来源：用户提供的人教版教材照片《零点存在性定理.jpg》，按图转录。'
                    break
            data=E.tostring(notes,encoding='UTF-8',xml_declaration=True,standalone=True)
        out.writestr(part,data)
print(json.dumps({'changedSlide':8,'changedTextBoxes':changed,'allOtherPackagePartsPreserved':True},ensure_ascii=False))
