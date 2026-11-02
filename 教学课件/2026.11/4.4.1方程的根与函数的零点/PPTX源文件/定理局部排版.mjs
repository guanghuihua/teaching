import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {pepTheoremRows} from './人教版定理.mjs';
const here=path.dirname(fileURLToPath(import.meta.url));
const runtime=process.env.CODEX_RUNTIME_MODULES||path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const {PresentationFile,FileBlob}=await import(pathToFileURL(path.join(runtime,'@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const [source,output,specPath]=process.argv.slice(2);
if(!source||!output||!specPath)throw new Error('用法：node 定理局部排版.mjs 当前PPTX 草稿PPTX 公式配置JSON');
const p=await PresentationFile.importPptx(await FileBlob.load(source));
p.slides.keep([7]);
const slide=p.slides.items[0],specs={};
for(const r of pepTheoremRows){
  const name=`pep_${r.name}`,color=r.name.endsWith('_7')||r.name.endsWith('_8')?'FF0000':'000000';
  const sh=slide.shapes.add({geometry:'textbox',name,position:{left:r.x,top:r.y,width:r.w,height:r.h},fill:'none',line:{fill:'none',width:0}});
  sh.text=r.text.replace(/\$/g,'');
  sh.text.style={typeface:'宋体',fontSize:32,bold:true,color:`#${color}`,alignment:'left',verticalAlignment:'top',insets:0,wrap:'square',autoFit:'none'};
  specs[name]={text:r.text,sizePt:24,align:'left',color,font:'宋体',bold:true,mathBold:true,lineSpacing:1.4,paragraphAfterPt:0};
}
await fs.mkdir(path.dirname(output),{recursive:true});
await fs.writeFile(specPath,JSON.stringify(specs,null,2));
await (await PresentationFile.exportPptx(p)).save(output);
console.log(JSON.stringify({slide:8,changedTextBoxes:pepTheoremRows.length,output}));
