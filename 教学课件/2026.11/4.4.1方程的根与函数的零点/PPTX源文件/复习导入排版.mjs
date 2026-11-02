import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const runtime=process.env.CODEX_RUNTIME_MODULES||path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const {PresentationFile,FileBlob}=await import(pathToFileURL(path.join(runtime,'@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const [source,draft,specFile]=process.argv.slice(2);
if(!source||!draft||!specFile)throw new Error('用法：node 复习导入排版.mjs 当前PPTX 草稿PPTX 公式配置JSON');
const p=await PresentationFile.importPptx(await FileBlob.load(source));
p.slides.keep([1]);
const first=p.slides.items[0],second=first.duplicate();second.moveTo(1);
const specs={},groups={2:[],35:[]};
let seq=0;
function text(slide,n,txt,x,y,w,h,size=32,step=0,options={}){
  const name=`review${n}_${options.role||'text'}_${++seq}`,color=options.color||(step?'FF0000':'000000');
  const sh=slide.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  sh.text=txt.replace(/\$/g,'');
  sh.text.style={typeface:options.font||'宋体',fontSize:size,bold:options.bold??true,color:`#${color}`,alignment:options.align||'left',verticalAlignment:'middle',insets:0,autoFit:'none',wrap:'square'};
  specs[name]={text:txt,sizePt:size*.75,font:options.font||'宋体',color,bold:options.bold??true,mathBold:options.mathBold??size>=30,align:options.align||'left',lineSpacing:1.2,paragraphAfterPt:0};
  if(step){const key=n===3?35:n;groups[key][step-1]??=[];groups[key][step-1].push(name);}
  return name;
}
function line(slide,n,role,x1,y1,x2,y2,color='000000',width=1.25){
 const l=Math.min(x1,x2),t=Math.min(y1,y2),w=Math.max(.01,Math.abs(x2-x1)),h=Math.max(.01,Math.abs(y2-y1));
 slide.shapes.add({geometry:'custom',name:`review${n}_${role}_${++seq}`,position:{left:l,top:t,width:w,height:h},fill:'none',line:{fill:`#${color}`,width},customPaths:[{width:w,height:h,commands:[{moveTo:{x:x1-l,y:y1-t}},{lineTo:{x:x2-l,y:y2-t}}]}]});
}
function graph(slide,n,{x,y,w,h,f,roots,xticks}){
 const xmin=-.4,xmax=4.4,ymin=-1.5,ymax=4.5;
 const X=v=>x+(v-xmin)/(xmax-xmin)*w,Y=v=>y+h-(v-ymin)/(ymax-ymin)*h;
 line(slide,n,'axis_x',x,Y(0),x+w+10,Y(0));line(slide,n,'axis_y',X(0),y+h,X(0),y-10);
 line(slide,n,'arrow_x1',x+w+10,Y(0),x+w+3,Y(0)-4);line(slide,n,'arrow_x2',x+w+10,Y(0),x+w+3,Y(0)+4);
 line(slide,n,'arrow_y1',X(0),y-10,X(0)-4,y-3);line(slide,n,'arrow_y2',X(0),y-10,X(0)+4,y-3);
 text(slide,n,'$x$',x+w+12,Y(0)-5,28,28,22,0,{font:'Cambria Math',bold:false,mathBold:false});
 text(slide,n,'$y$',X(0)-12,y-40,28,28,22,0,{font:'Cambria Math',bold:false,mathBold:false});
 for(const v of xticks){line(slide,n,'xtick',X(v),Y(0)-3,X(v),Y(0)+3);text(slide,n,`$${v}$`,X(v)-20,Y(0)+5,40,30,22,0,{font:'Cambria Math',bold:false,mathBold:false,align:'center'});}
 for(const v of [2,4]){line(slide,n,'ytick',X(0)-3,Y(v),X(0)+3,Y(v));text(slide,n,`$${v}$`,X(0)-50,Y(v)-15,32,30,22,0,{font:'Cambria Math',bold:false,mathBold:false,align:'right'});}
 const commands=[];let started=false;
 for(let k=0;k<=240;k++){const vx=xmin+(xmax-xmin)*k/240,vy=f(vx);if(vy<ymin||vy>ymax){started=false;continue;}commands.push(started?{lineTo:{x:X(vx)-x,y:Y(vy)-y}}:{moveTo:{x:X(vx)-x,y:Y(vy)-y}});started=true;}
 slide.shapes.add({geometry:'custom',name:`review${n}_function_curve_${++seq}`,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'#176DAB',width:2.5},customPaths:[{width:w,height:h,commands}]});
 for(const v of roots)slide.shapes.add({geometry:'ellipse',name:`review${n}_root_${++seq}`,position:{left:X(v)-4,top:Y(0)-4,width:8,height:8},fill:'#B43D32',line:{fill:'none',width:0}});
}
text(first,2,'复习导入：从函数观点看方程',175,12,1040,52,112/3,0,{font:'微软雅黑',color:'2F9445',role:'heading'});
text(first,2,'求方程的实数根，观察相应二次函数图象与 $x$ 轴的交点。',64,110,1152,60);
const cases=[
 {eq:'$x^2-4x+3=0$',fn:'$y=x^2-4x+3$',f:x=>x*x-4*x+3,roots:[1,3],answers:['实数根：$1,3$。','交点：$(1,0),(3,0)$。']},
 {eq:'$x^2-4x+4=0$',fn:'$y=x^2-4x+4$',f:x=>(x-2)**2,roots:[2],answers:['实数根：$2$（重根）。','交点：$(2,0)$。']},
 {eq:'$x^2-2x+3=0$',fn:'$y=x^2-2x+3$',f:x=>(x-1)**2+2,roots:[],answers:['无实数根。','图象与 $x$ 轴没有交点。']},
];
for(let k=0;k<3;k++){
 const x=64+395*k,c=cases[k];
 text(first,2,c.eq,x,183,350,52,32,0,{align:'center'});
 text(first,2,c.fn,x,243,350,34,24,0,{font:'Cambria Math',bold:false,mathBold:false,align:'center'});
 graph(first,2,{x:x+27,y:302,w:285,h:178,f:c.f,roots:c.roots,xticks:k===0?[1,3]:[1,2,3]});
 text(first,2,c.answers[0],x,511,350,46,32,k+1,{align:'center'});
 text(first,2,c.answers[1],x,560,350,46,32,k+1,{align:'center'});
}
text(first,2,'方程的实数根，就是相应函数图象与 $x$ 轴交点的横坐标。',64,622,1152,48,32,4);

seq=0;
text(second,3,'复习导入：判别式与零点个数',175,12,1040,52,112/3,0,{font:'微软雅黑',color:'2F9445',role:'heading'});
text(second,3,String.raw`设 $f(x)=ax^2+bx+c\ (a\ne0)$，$x\in\mathbb{R}$，$\Delta=b^2-4ac$。`,64,110,1152,60);
const values=[['判别式','方程的实数根','与 x 轴交点','不同零点个数'],['Δ>0','两个不相等的实数根','两个','2'],['Δ=0','两个相等的实数根','一个','1'],['Δ<0','无实数根','无','0']];
const tb=second.tables.add({rows:4,columns:4,left:70,top:192,width:1140,height:240,columnWidths:[170,370,320,280],values});
tb.styleOptions={headerRow:false,bandedRows:false};tb.borders.assign({fill:'#FFFFFF',width:1,style:'solid'});
for(let r=0;r<4;r++)for(let c=0;c<4;c++){const cell=tb.getCell(r,c);cell.fill=r?'#D2D9EE':'#4875D2';cell.text.style={typeface:'宋体',fontSize:32,bold:true,color:r?'#000000':'#FFFFFF',alignment:'center',verticalAlignment:'middle',insets:7};}
groups[35][0]=['review3_table'];
text(second,3,'三例的判别式依次为 $4,0,-8$，零点个数依次为 $2,1,0$。',64,451,1152,66,32,2);
text(second,3,'两个相等的实数根，为什么只对应一个零点？',64,535,1152,52);
text(second,3,'因为重根只对应一个不同的横坐标。',64,598,1152,52,32,3);

await fs.mkdir(path.dirname(draft),{recursive:true});
await fs.writeFile(specFile,JSON.stringify(specs,null,2));
await fs.writeFile(path.join(path.dirname(draft),'reveals.json'),JSON.stringify({slides:groups},null,2));
await (await PresentationFile.exportPptx(p)).save(draft);
console.log(JSON.stringify({newReviewPages:2,totalReviewPages:3,specs:Object.keys(specs).length,draft}));
