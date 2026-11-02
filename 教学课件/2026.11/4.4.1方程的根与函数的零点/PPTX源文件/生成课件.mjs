import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {applyCompactLayout} from './紧凑版式.mjs';

// 可编辑PPTX的排版源文件。字体、文字、曲线及揭示步骤分别保留。
const here=path.dirname(fileURLToPath(import.meta.url));
const lesson=path.dirname(here);
const repo=path.resolve(lesson,'../../..');
const runtime=process.env.CODEX_RUNTIME_MODULES || path.join(process.env.USERPROFILE||'', '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const {PresentationFile,FileBlob}=await import(pathToFileURL(path.join(runtime,'@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const build=path.join(lesson,'build/pptx');
await fs.mkdir(build,{recursive:true});
const p=await PresentationFile.importPptx(await FileBlob.load(path.join(repo,'教学课件/高中园模板.pptx')));
p.slides.keep([0,1]);
const cover=p.slides.items[0],base=p.slides.items[1];
// 保留原模板背景、母版、校徽、校名、书本自由曲线，只替换文字。
for(const slide of [cover,base]){
  const found=await p.inspect({kind:'textbox,shape',maxChars:20000});
  const records=found.records||[];
  const targetNames=slide===cover?['文本框 3']:['文本框 21'];
  for(const rec of records){if(targetNames.includes(rec.name)&&rec.id)p.delete(rec.id);}
}
const math=[],reveals={},headings=[];
let current=0,seq=0;
const BLACK='#161616',GREEN='#126831',BLUE='#176DAB',RED='#B43D32';
function T(s,txt,x=64,y=140,w=1152,h=54,size=32,step=0,options={}){
  const name=`s${current}_${options.name||'text'}_${++seq}`;
  const sh=s.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  sh.text=txt.replace(/\$/g,'');
  sh.text.style={typeface:'Microsoft YaHei',fontSize:size,color:options.color||BLACK,bold:options.bold||false,alignment:options.align||'left',verticalAlignment:options.vAlign||'middle',wrap:'square',autoFit:'none',insets:0};
  math.push({slide:current,name,text:txt,size,color:options.color||BLACK,bold:options.bold||false,font:'Cambria Math',textFont:'Microsoft YaHei',align:options.align||'left'});
  if(step>0){reveals[current]??=[];reveals[current][step-1]??=[];reveals[current][step-1].push(name);}
  return sh;
}
function notes(s,source,prompt=''){s.speakerNotes.text=`来源：${source}\n${prompt?`授课提示：${prompt}`:''}`;}
// 在空白模板副本上统一批量建页，防止首个正文页污染后续副本。
const slides=[cover,base];
for(let i=2;i<34;i++){const d=base.duplicate();d.moveTo(p.slides.items.length-1);slides.push(d);}
function page(title){current++;seq=0;const s=slides[current-1];headings.push(title);
  if(current>1){T(s,title,133,17,768,65,40,0,{color:'#FFFFFF',bold:true,name:'heading'});T(s,String(current),1188,674,50,28,20,0,{color:'#888888',align:'right',name:'page'});}return s;
}
function line(s,name,x1,y1,x2,y2,color='#666666',width=1.5,dash=false){
 const l=Math.min(x1,x2),t=Math.min(y1,y2),w=Math.max(Math.abs(x2-x1),.01),h=Math.max(Math.abs(y2-y1),.01);
 return s.shapes.add({geometry:'custom',name:`s${current}_${name}_${++seq}`,position:{left:l,top:t,width:w,height:h},fill:'none',line:{fill:color,width,style:dash?'dashed':'solid'},customPaths:[{width:w,height:h,commands:[{moveTo:{x:x1-l,y:y1-t}},{lineTo:{x:x2-l,y:y2-t}}]}]});
}
function dot(s,x,y,color=RED,r=5){return s.shapes.add({geometry:'ellipse',name:`s${current}_point_${++seq}`,position:{left:x-r,top:y-r,width:2*r,height:2*r},fill:color,line:{fill:color,width:0}});}
function graph(s,{x=700,y=190,w=480,h=340,xmin=-2,xmax=4,ymin=-5,ymax=6,xticks=[],yticks=[],curves=[],points=[],dashes=[],labels=[]}){
 const X=v=>x+(v-xmin)/(xmax-xmin)*w,Y=v=>y+h-(v-ymin)/(ymax-ymin)*h;
 const ay=Math.max(ymin,Math.min(ymax,0)),ax=Math.max(xmin,Math.min(xmax,0));
 line(s,'axis_x',x,Y(ay),x+w+12,Y(ay));line(s,'axis_y',X(ax),y+h,X(ax),y-12);
 line(s,'arrow_x1',x+w+12,Y(ay),x+w+3,Y(ay)-5);line(s,'arrow_x2',x+w+12,Y(ay),x+w+3,Y(ay)+5);
 line(s,'arrow_y1',X(ax),y-12,X(ax)-5,y-3);line(s,'arrow_y2',X(ax),y-12,X(ax)+5,y-3);
 T(s,'$x$',x+w+17,Y(ay)-6,35,34,23);T(s,'$y$',X(ax)-14,y-46,35,34,23);
 for(const tick of xticks){const v=typeof tick==='number'?tick:tick.v,lbl=typeof tick==='number'?String(tick):tick.label;line(s,'xtick',X(v),Y(ay)-4,X(v),Y(ay)+4);if(lbl)T(s,`$${lbl}$`,X(v)-28,Y(ay)+(tick.dy??7),56,33,22,0,{align:'center'});}
 for(const tick of yticks){const v=typeof tick==='number'?tick:tick.v,lbl=typeof tick==='number'?String(tick):tick.label;line(s,'ytick',X(ax)-4,Y(v),X(ax)+4,Y(v));T(s,`$${lbl}$`,X(ax)-60,Y(v)-16,49,32,22,0,{align:'right'});}
 for(const d of dashes)line(s,'projection',X(d[0]),Y(d[1]),X(d[2]),Y(d[3]),'#777777',1.4,true);
 for(const c of curves){let commands=[],started=false;const start=c.a??xmin,end=c.b??xmax,n=c.n??240;for(let i=0;i<=n;i++){const vx=start+(end-start)*i/n,vy=c.f(vx);if(!Number.isFinite(vy)||vy<ymin||vy>ymax){started=false;continue;}commands.push(started?{lineTo:{x:X(vx)-x,y:Y(vy)-y}}:{moveTo:{x:X(vx)-x,y:Y(vy)-y}});started=true;}
   s.shapes.add({geometry:'custom',name:`s${current}_function_curve_${++seq}`,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:c.color||BLUE,width:2.7},customPaths:[{width:w,height:h,commands}]});}
 for(const a of points)dot(s,X(a[0]),Y(a[1]),a[2]||RED,4.8);
 for(const a of labels)T(s,`$${a.text}$`,X(a.x)+(a.dx??0),Y(a.y)+(a.dy??0),a.w??150,40,a.size??24,0,{color:a.color||BLACK,align:a.align||'left'});
 return{X,Y};
}
function table(s,values,x,y,width,height,colWidths,font=27){
 const tb=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width,height,columnWidths:colWidths,values});
 tb.styleOptions={headerRow:false,bandedRows:false};tb.borders.assign({fill:'#6A6A6A',width:1,style:'solid'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){const cell=tb.getCell(r,c);cell.fill='#FFFFFF';cell.text.style={typeface:'Cambria Math',fontSize:font,color:BLACK,alignment:'center',verticalAlignment:'middle',insets:7};}
 return tb;
}
function row(s,y,label,body,step=0){T(s,label,70,y,245,75,30,step,{bold:true});T(s,body,332,y,867,80,30,step);line(s,'row_rule',66,y+85,1210,y+85,'#C0C0C0',1);}
let s=page('方程的根与函数的零点');
T(s,'方程的根与函数的零点',90,423,1100,90,56,0,{bold:true,color:GREEN,align:'center',name:'cover_title'});
T(s,'高一数学  4.4.1',390,559,610,52,32,0,{bold:true,color:GREEN,align:'center'});
T(s,'2026.11',929,633,220,40,25,0,{color:GREEN,align:'center'});
notes(s,'高中园原PowerPoint模板；湘教版必修第一册4.4.1。');

s=page('复习导入：方程与二次函数');
T(s,'解方程：',64,146,530,50);
T(s,'$x^2-2x-3=0$',64,202,560,64,36,0,{align:'center'});
T(s,'$(x+1)(x-3)=0$',64,282,560,60,34,1,{align:'center'});
T(s,'实数根为 $-1,3$。',64,354,575,55,32,1);
T(s,'对应函数 $y=x^2-2x-3$ 的零点也是 $-1,3$。',64,425,575,102,32,1);
T(s,'一元二次方程的实数根，就是相应二次函数的零点。',64,585,1152,65,30,1);
graph(s,{x:737,y:192,w:450,h:335,xmin:-2,xmax:4,ymin:-5,ymax:6,xticks:[-1,1,3],yticks:[-4,4],curves:[{f:x=>x*x-2*x-3}],points:[[-1,0],[3,0]]});
notes(s,'基于一元二次方程与二次函数的对应关系。','本页与下一页合计约3分钟，回顾后直接提出新问题。');

s=page('复习导入：这个方程怎样解');
T(s,'对于方程',64,154,1152,55,34);
T(s,String.raw`$\ln x+2x-6=0,\qquad x>0$`,150,228,980,82,42,0,{align:'center'});
T(s,'不能像一元二次方程那样，直接套用求根公式。',64,332,1152,70,32);
T(s,'能否借助相应的函数',64,431,1152,58,32,1);
T(s,String.raw`$y=\ln x+2x-6$`,230,495,820,72,40,1,{align:'center'});
T(s,'研究方程有没有实数解、解在什么范围内、有几个解？',64,592,1152,65,32,1);
notes(s,'教师本次指定的导入方程。','只提出问题，完整判断放在第16页。');

s=page('新知探究：函数的零点');
T(s,'设函数 $y=f(x)$ 的定义域为 $D$。',64,150,1152,60,34);
T(s,String.raw`使 $f(x_0)=0$ 的实数 $x_0\in D$，叫作函数 $y=f(x)$ 的零点。`,64,242,1152,106,35,0,{bold:false});
line(s,'def_rule',64,366,1216,366,GREEN,2);
T(s,'例如：$f(x)=x^2-4$。',64,401,1152,62,32,1);
T(s,'零点为 $-2,2$；图象与 $x$ 轴的交点为 $(-2,0),(2,0)$。',64,483,1152,75,32,1);
T(s,'零点是实数，函数值为 $0$。',64,591,1152,62,32,1,{bold:true});
notes(s,'用户照片5，湘教版必修第一册4.4.1。','区分实数、函数值、平面上的点。');

s=page('新知探究：三种表述');
T(s,String.raw`$x_0\in D,\quad f(x_0)=0$`,160,141,960,64,38,0,{align:'center'});
T(s,String.raw`$\Longleftrightarrow$  $x_0$ 是方程 $f(x)=0$ 的实数根`,155,243,1000,66,34);
T(s,String.raw`$\Longleftrightarrow$  $x_0$ 是函数 $y=f(x)$ 的零点`,155,328,1000,66,34);
T(s,String.raw`$\Longleftrightarrow$  $(x_0,0)$ 是图象与 $x$ 轴的交点`,155,413,1030,66,34);
T(s,'口答：$f(2)=0$ 时，零点是______，交点是______。',64,533,1152,65,32);
T(s,'零点是 $2$，交点是 $(2,0)$。',64,609,1152,53,32,1);
notes(s,'湘教版教材零点定义及对应关系。');

s=page('新知探究：河流情境');
T(s,'小明从 $A$ 点走到 $B$ 点，哪幅图能说明他一定经过河流？',64,138,1152,70,32);
for(let i=0;i<2;i++){const x=120+i*580,y=300,w=440;
 line(s,'river_bank',x,y,x+w,y,BLACK,2);line(s,'river_bank',x,y+100,x+w,y+100,BLACK,2);
 for(let j=0;j<5;j++){const xx=x+18+j*82;const pts=[{moveTo:{x:0,y:12}},{cubicBezTo:{x1:18,y1:0,x2:43,y2:23,x:64,y:8}}];s.shapes.add({geometry:'custom',name:`s${current}_river_wave_${++seq}`,position:{left:xx,top:y+26+(j%2)*23,width:64,height:23},fill:'none',line:{fill:BLACK,width:1.3},customPaths:[{width:64,height:23,commands:pts}]});}
 dot(s,x+55,y-34,BLACK,4);T(s,'$A$',x+20,y-88,55,48,30);
 dot(s,x+352,i===0?y+145:y-60,BLACK,4);T(s,'$B$',x+365,i===0?y+121:y-106,55,48,30);
 T(s,`图（${i+1}）`,x+150,y+165,150,48,30,0,{align:'center'});}
T(s,'图（1）至少经过一次河流；图（2）不能保证经过。',64,565,1152,65,32,1);
T(s,'假设路线连续，河流在讨论区域贯通，不能绕过源头。',64,635,1152,42,25,1);
notes(s,'原PPT第4页河流情境，图形重建为可编辑线条与点。','将两岸对应正负，将连续路线对应连续图象；不把故事当定理证明。');

s=page('新知探究：观察函数图象');
graph(s,{x:92,y:205,w:535,h:340,xmin:0,xmax:5,ymin:-2.5,ymax:3.2,xticks:[{v:1,label:'a'},{v:2.5,label:'x_0'},{v:4,label:'b'}],curves:[{a:1,b:4,f:x=>-.35*(x-2.5)**3-.5*(x-2.5)}],points:[[2.5,0]],dashes:[[1,0,1,1.93125],[4,0,4,-1.93125]],labels:[{x:1,y:2.6,text:'f(a)>0',w:165},{x:3.15,y:-1.9,text:'f(b)<0',w:170}]});
T(s,'图象在区间上连续不断。',702,175,510,85,32);
T(s,'左端点在 $x$ 轴上方，右端点在 $x$ 轴下方。',702,285,510,120,32);
T(s,'中间至少与 $x$ 轴相交一次。',702,439,510,100,32,1);
T(s,'两端异号：$f(a)f(b)<0$。',64,604,1152,60,34,1,{align:'center'});
notes(s,'用户照片5，湘教版图4.4-1，按函数重绘。');

s=page('新知探究：零点存在定理');
T(s,'设 $a<b$，函数 $y=f(x)$ 满足：',64,146,1152,64,34);
T(s,'（1）在闭区间 $[a,b]$ 上的图象连续不断；',100,238,1110,70,34);
T(s,'（2）$f(a)f(b)<0$。',100,323,1110,65,36);
line(s,'theorem_rule',64,410,1216,410,GREEN,2);
T(s,'则在开区间 $(a,b)$ 内至少有一个零点。',64,445,1152,76,36,1);
T(s,String.raw`即存在 $x_0\in(a,b)$，使 $f(x_0)=0$。`,64,539,1152,74,36,1);
T(s,'注意：连续、异号、开区间、至少一个。',64,630,1152,48,29,2,{bold:true});
notes(s,'湘教版必修第一册4.4.1及2025修订课标。');

s=page('新知探究：连续性不可少');
T(s,String.raw`$f(x)=\frac1x$`,64,148,535,74,38);
T(s,String.raw`$f(-1)=-1,\qquad f(1)=1$`,64,242,570,72,34);
T(s,'能推出 $(-1,1)$ 内有零点吗？',64,343,550,80,32);
T(s,'不能。$x=0$ 不在定义域内。\n函数在 $[-1,1]$ 上不连续。',64,445,570,126,32,1);
T(s,String.raw`而且 $\frac1x=0$ 没有实数解。`,64,600,580,64,32,1);
graph(s,{x:735,y:206,w:445,h:340,xmin:-2,xmax:2,ymin:-3,ymax:3,xticks:[-1,1],yticks:[-1,1],curves:[{a:-2,b:-.15,f:x=>1/x},{a:.15,b:2,f:x=>1/x}],points:[[-1,-1],[1,1]]});
notes(s,'反例：端点异号但闭区间不满足连续条件。');

s=page('新知探究：同号与零点个数');
T(s,'同号，也可能有零点',64,133,545,56,30,0,{bold:true,align:'center'});
T(s,'异号，可能有多个零点',670,133,545,56,30,0,{bold:true,align:'center'});
graph(s,{x:111,y:244,w:445,h:250,xmin:-1.5,xmax:1.5,ymin:-.5,ymax:2,xticks:[-1,1],yticks:[1],curves:[{a:-1.3,b:1.3,f:x=>x*x}],points:[[-1,1],[0,0],[1,1]]});
graph(s,{x:715,y:244,w:445,h:250,xmin:-2.2,xmax:2.2,ymin:-7,ymax:7,xticks:[-2,-1,1,2],curves:[{a:-2,b:2,f:x=>x*x*x-x}],points:[[-1,0],[0,0],[1,0]]});
T(s,'$f(x)=x^2$，$f(-1)f(1)>0$，零点为 $0$。',64,539,545,100,28);
T(s,'$g(x)=x^3-x$，两端异号，零点为 $-1,0,1$。',670,539,545,100,28);
T(s,'定理只保证至少一个，并不确定恰有几个。',64,641,1152,40,29,1,{align:'center',bold:true});
notes(s,'原PPT第6页同号反例；多零点反例自编，可由x(x−1)(x+1)核验。');

s=page('新知探究：零点的唯一性');
T(s,'连续且端点异号，保证至少一个零点。',64,163,1152,70,35);
T(s,'在该区间严格单调，保证至多一个零点。',64,265,1152,70,35);
T(s,'两方面结合，才能说明恰有一个零点。',64,372,1152,70,35,1,{bold:true});
T(s,'若严格递增，$x_1<x_2$ 时 $f(x_1)<f(x_2)$，不可能同时为 $0$。',64,467,1152,90,30,1);
T(s,'想一想：$y=2^x$ 严格递增，为什么没有零点？',64,590,1152,72,32,2);
notes(s,'严格单调只能得至多一个，必须另证存在。');

s=page('新知探究：定理的应用');
T(s,'讨论 $f(x)=2x^3-5$ 在 $(1,2)$ 内零点的个数。',64,140,1152,74,34);
T(s,'函数在 $[1,2]$ 上连续，且',64,238,1152,62,32,1);
T(s,String.raw`$f(1)=-3<0,\qquad f(2)=11>0$`,110,312,1060,72,36,1,{align:'center'});
T(s,'所以在 $(1,2)$ 内至少有一个零点。',64,410,1152,64,32,1);
T(s,'又因 $2x^3-5$ 严格递增，所以至多有一个零点。',64,497,1152,70,32,2);
T(s,'综上，在 $(1,2)$ 内恰有一个零点。',64,594,1152,65,34,2,{bold:true});
notes(s,'湘教版教材4.4.1例1，照片5。','精确根可写为立方根，本题练习的是定位与个数论证。');

s=page('课堂练习：求函数零点');
T(s,'求下列函数的零点：',64,135,1152,54,32);
T(s,'（1）$f(x)=x^2+7x+6$；',64,202,1152,60,34);
T(s,String.raw`（2）$g(x)=1-\log_2(x+3)$。`,64,271,1152,60,34);
line(s,'answer_rule',64,351,1216,351,'#BBBBBB',1);
T(s,String.raw`（1）定义域为 $\mathbb{R}$，由 $(x+1)(x+6)=0$，得零点为 $-1,-6$。`,64,387,1152,108,32,1);
T(s,String.raw`（2）定义域为 $(-3,+\infty)$。由 $\log_2(x+3)=1$，得 $x=-1$，符合定义域。`,64,518,1152,116,32,2);
notes(s,'《三维设计》必修第一册（人教A版适用），照片2第76页对点练习。');

s=page('课堂练习：分式函数');
T(s,String.raw`求函数 $f(x)=\frac{x^2+4x-12}{x-2}$ 的零点。`,64,142,1152,104,34);
T(s,String.raw`定义域：$x\ne2$。`,64,277,1152,60,32,1);
T(s,String.raw`$f(x)=\frac{(x+6)(x-2)}{x-2}=x+6\quad(x\ne2)$`,110,357,1060,95,36,1,{align:'center'});
T(s,'所以 $f(x)=0$ 得 $x=-6$，函数只有一个零点 $-6$。',64,487,1152,78,32,2);
T(s,'约分后，原函数的定义域限制仍须保留。',64,599,1152,61,30,2,{bold:true});
notes(s,'《三维设计》第77页，照片3。');

s=page('课堂练习：分段函数');
T(s,'求函数的零点：',64,132,1152,50,32);
T(s,String.raw`$f(x)=\begin{cases}x^2+2x-3,&x\le0,\\-2+\ln x,&x>0.\end{cases}$`,140,198,1000,132,36);
T(s,String.raw`当 $x\le0$ 时，$(x+3)(x-1)=0$，候选根为 $-3,1$。`+'\n'+String.raw`其中 $1$ 不满足 $x\le0$，只保留 $x=-3$。`,64,364,1152,97,30,1);
T(s,String.raw`当 $x>0$ 时，$\ln x=2$，得到 $x=e^2$，符合范围。`,64,486,1152,82,31,2);
T(s,'所以函数的零点为 $-3,e^2$。',64,604,1152,61,32,2,{bold:true});
notes(s,'原PPT第10页、《三维设计》第77页典例3。','第一段候选根1应舍去。');

s=page('课堂练习：方程根的区间');
T(s,String.raw`判断 $\ln x+2x-6=0$ 的解的个数，并确定相邻整数区间。`,64,137,1152,82,32);
T(s,String.raw`令 $f(x)=\ln x+2x-6$，定义域为 $(0,+\infty)$。`,64,244,1152,70,32,1);
T(s,String.raw`$f(2)=\ln2-2<0,\qquad f(3)=\ln3>0$`,90,329,1100,74,35,1,{align:'center'});
T(s,'函数在 $[2,3]$ 上连续，故在 $(2,3)$ 内至少有一个零点。',64,434,1152,78,32,1);
T(s,String.raw`$\ln x$ 与 $2x$ 都严格递增，故 $f$ 在整个定义域上严格递增。`,64,533,1152,75,31,2);
T(s,'所以原方程恰有一个实数解，且在 $(2,3)$ 内。',64,620,1152,55,32,2,{bold:true});
notes(s,'用户指定的导入方程，本页回扣。','ln2<1，故ln2−2<0；不使用求根公式。');

s=page('课堂练习：判断零点区间');
T(s,String.raw`判断 $f(x)=2^x+\log_2x-3$ 的零点所在区间。`,64,143,1152,75,34);
T(s,String.raw`定义域为 $(0,+\infty)$，选取端点 $1,2$。`,64,247,1152,65,32,1);
T(s,String.raw`$f(1)=-1,\qquad f(2)=2$`,180,335,920,65,36,1,{align:'center'});
T(s,'在 $[1,2]$ 上连续，且端点异号，因此 $(1,2)$ 内至少有一个零点。',64,427,1152,84,32,1);
T(s,'又因两项均严格递增，故整个定义域内只有一个零点，位于 $(1,2)$。',64,546,1152,110,32,2);
notes(s,'《三维设计》第77页对点练习。');

s=page('课堂练习：根据数值表判断');
T(s,String.raw`二次函数 $f(x)=ax^2+bx+c\ (a\ne0)$ 的部分函数值如下。`,64,132,1152,71,31);
T(s,'不求系数，判断两个零点所在的区间。',64,212,1152,58,32);
table(s,[['x','−3','−2','−1','0','1','2','3','4'],['f(x)','6','m','−4','−6','−6','−4','n','6']],100,275,1080,114,[120,120,120,120,120,120,120,120,120],30);
T(s,String.raw`$f(-3)f(-1)<0,\qquad f(2)f(4)<0$`,64,464,1152,65,34,1,{align:'center'});
T(s,'二次函数连续，故 $(-3,-1)$、$(2,4)$ 内各至少一个零点。',64,546,1152,67,31,1);
T(s,'二次函数至多两个不同零点，因此两个区间内各恰有一个。',64,625,1152,52,30,2);
notes(s,'《三维设计》第77页典例2（1），照片3。','数据自洽：f=x²−x−6，m=n=0；课堂无需求系数。');

s=page('课堂练习：两图象的交点');
T(s,String.raw`讨论方程 $2^{-x}=\log_2x$ 的解的个数与所在区间。`,64,130,1152,69,33);
graph(s,{x:104,y:273,w:541,h:290,xmin:0,xmax:4,ymin:-1.2,ymax:2.2,xticks:[1,2,3],yticks:[1,2],curves:[{a:.05,b:4,f:x=>2**(-x)},{a:.4,b:4,f:x=>Math.log2(x),color:RED}],dashes:[[1,0,1,.5],[2,0,2,1]],labels:[{x:2.6,y:.5,text:'y=2^{-x}',color:BLUE,w:160},{x:2.4,y:2.12,text:String.raw`y=\log_2x`,color:RED,w:180}]});
T(s,'共同定义域：$x>0$。',731,231,480,60,31);
T(s,String.raw`$2^{-x}$ 严格递减，$\log_2x$ 严格递增。`,731,325,480,113,31);
T(s,'交点至多一个，横坐标在 $(1,2)$ 内。',731,469,480,113,31,1);
T(s,'怎样用函数性质说明这个判断？',64,624,1152,54,31,1);
notes(s,'湘教版必修第一册4.4.1例2，照片6。');

s=page('课堂练习：零点个数的论证');
T(s,String.raw`令 $h(x)=\log_2x-2^{-x}$，定义域为 $(0,+\infty)$。`,64,136,1152,74,33);
T(s,'$h$ 在 $[1,2]$ 上连续，且',64,246,1152,58,32,1);
T(s,String.raw`$h(1)=-\frac12<0,\qquad h(2)=\frac34>0$`,130,316,1020,92,36,1,{align:'center'});
T(s,'所以在 $(1,2)$ 内至少有一个零点。',64,438,1152,64,32,1);
T(s,String.raw`$\log_2x$ 与 $-2^{-x}$ 都严格递增，故 $h$ 在整个定义域上严格递增。`,64,530,1152,82,31,2);
T(s,'所以原方程恰有一个实数解，且在 $(1,2)$ 内。',64,626,1152,51,32,2,{bold:true});
notes(s,'湘教版教材例2方法二，照片6。');

s=page('课堂练习：绝对值与零点');
T(s,'已知 $f(x)=|x^2-4x|-a$ 恰有3个零点，求 $a$。',64,147,1152,85,34);
T(s,String.raw`$f(x)=0\quad\Longleftrightarrow\quad |x^2-4x|=a$`,130,282,1020,75,38,1,{align:'center'});
T(s,'即研究曲线 $y=|x^2-4x|$ 与直线 $y=a$ 的交点个数。',64,412,1152,88,32,1);
T(s,'把 $y=(x-2)^2-4$ 在 $x$ 轴下方的部分沿 $x$ 轴翻折。',64,529,1152,86,31,1);
T(s,'关键位置：$(0,0),(2,4),(4,0)$。',64,627,1152,51,31,1);
notes(s,'《三维设计》第77页对点练习，照片3。');

s=page('课堂练习：交点个数');
graph(s,{x:107,y:243,w:550,h:340,xmin:-1.5,xmax:5.5,ymin:-1,ymax:7,xticks:[2,4],yticks:[4],curves:[{a:-1.3,b:5.3,f:x=>Math.abs(x*x-4*x)},{a:-1.3,b:5.3,f:x=>4,color:RED}],points:[[-.828427,4],[2,4],[4.828427,4]],labels:[{x:4.1,y:4.8,text:'y=4',color:RED,w:130}]});
table(s,[['a 的范围','交点数'],['a<0','0'],['a=0','2'],['0<a<4','4'],['a=4','3'],['a>4','2']],758,145,430,294,[280,150],28);
T(s,'因此 $a=4$。',738,501,472,60,35,1,{bold:true});
T(s,String.raw`此时零点为 $2-2\sqrt2,\ 2,\ 2+2\sqrt2$。`,64,625,1152,58,31,1);
notes(s,'照片3教辅。','用(x−2)²=8或0验证三个不同零点。');

s=page('课堂练习：两根分居两侧');
T(s,'设 $f_a(x)=x^2-2ax+4$。若 $x_1<1<x_2$，求 $a$ 的范围。',64,133,1152,85,33);
graph(s,{x:99,y:297,w:530,h:280,xmin:-.5,xmax:6,ymin:-6,ymax:6,xticks:[{v:5.236068,label:'x_2'}],curves:[{a:-.2,b:6,f:x=>x*x-6*x+4}],points:[[1,-1]],dashes:[[1,0,1,-1]],labels:[{x:.763932,y:.2,text:'x_1',dx:-54,dy:-29,w:52},{x:1,y:.2,text:'1',dx:7,dy:-28,w:40}]});
T(s,'开口向上。',731,282,480,65,32);
T(s,'$1$ 在两根之间，对应图象在 $x$ 轴下方。',731,380,480,132,32);
T(s,'所以 $f_a(1)<0$。',731,544,480,71,35,1);
notes(s,'《三维设计》第77页典例4（2）。图取a=3，根3±√5。');

s=page('课堂练习：两根分居两侧');
T(s,String.raw`$f_a(1)=5-2a<0\quad\Longleftrightarrow\quad a>\frac52$`,100,148,1080,92,38,0,{align:'center'});
T(s,'这一条件为什么足够？',64,286,1152,60,32);
T(s,'开口向上，$x=1$ 处的函数值为负，左右两端最终都为正。',64,373,1152,88,32,1);
T(s,'因此在 $1$ 的左右各有一个零点。',64,478,1152,68,32,1);
T(s,String.raw`当 $a=\frac52$ 时，零点为 $1,4$，不符合题意。`,64,595,1152,79,32,2);
notes(s,'照片3教辅典例4改编。','一般式f=Ax²+Bx+C，A≠0；条件已保证两个不同实根。');

s=page('课堂练习：两根均大于1');
T(s,'仍设 $f_a(x)=x^2-2ax+4$，要求 $1<x_1<x_2$。',64,134,1152,78,34);
graph(s,{x:98,y:304,w:530,h:280,xmin:0,xmax:4.5,ymin:-2,ymax:5,xticks:[{v:1,label:'1',dy:18},{v:2.25,label:'a',dy:3},{v:3.280776,label:'x_2',dy:18}],curves:[{f:x=>x*x-4.5*x+4}],dashes:[[1,0,1,.5],[2.25,-1.8,2.25,4]],labels:[{x:1.219224,y:0,text:'x_1',dx:0,dy:-40,w:50}]});
T(s,String.raw`$\Delta>0$：有两个不同零点。`,731,265,480,88,31,1);
T(s,'$a>1$：对称轴在 $1$ 右侧。',731,380,480,88,31,1);
T(s,'$f_a(1)>0$：$1$ 在两根外侧。',731,495,480,88,31,1);
notes(s,'照片3典例4（1）改编，明确两个不同零点。图取a=9/4。');

s=page('课堂练习：两根均大于1');
T(s,String.raw`$\begin{cases}\Delta=4a^2-16>0,\\a>1,\\f_a(1)=5-2a>0\end{cases}\quad\Longleftrightarrow\quad 2<a<\frac52$`,100,150,1080,184,38,0,{align:'center'});
T(s,'端点检验',64,382,1152,56,32,1,{bold:true});
T(s,'$a=2$ 时，$f_a(x)=(x-2)^2$，只有一个不同零点。',64,461,1152,73,32,1);
T(s,String.raw`$a=\frac52$ 时，$f_a(x)=(x-1)(x-4)$，一个零点等于 $1$。`,64,562,1152,88,32,1);
notes(s,'《三维设计》第77页典例4（1）改编。');

s=page('课堂练习：两根均在区间内');
T(s,'已知 $f_m(x)=x^2-2mx+2$，两个不同零点均在 $(0,3)$ 内，求 $m$ 的范围。',64,139,1152,114,33);
T(s,'开口向上，需要同时满足：',64,282,1152,56,32,1);
T(s,String.raw`$\Delta>0$，有两个不同零点；`,100,368,1100,70,34,1);
T(s,'$0<m<3$，对称轴在区间内；',100,466,1100,70,34,1);
T(s,String.raw`$f_m(0)>0,\ f_m(3)>0$，两端点在根的外侧。`,100,564,1100,82,34,1);
notes(s,'自编二次根分布巩固题。','防止只写两个端点为正，漏判别式与轴的位置。');

s=page('课堂练习：两根均在区间内');
T(s,String.raw`$\begin{cases}4m^2-8>0,\\0<m<3,\\f_m(0)=2>0,\\f_m(3)=11-6m>0\end{cases}\quad\Longleftrightarrow\quad\sqrt2<m<\frac{11}{6}$`,85,145,1110,224,36,0,{align:'center'});
T(s,String.raw`$m=\sqrt2$ 时，判别式为 $0$，两个根重合。`,64,420,1152,76,32,1);
T(s,String.raw`$m=\frac{11}{6}$ 时，一个根等于端点 $3$。`,64,528,1152,84,32,1);
T(s,'因此两个端点均排除。',64,630,1152,48,31,1);
notes(s,'自编巩固题，数学核查：右端点对应根2/3、3。');

s=page('课堂练习：两个指定区间');
T(s,'$f_a(x)=x^2-2ax+4$ 的一个零点在 $(0,1)$ 内，另一个在 $(6,8)$ 内，求 $a$。',64,129,1152,103,33);
T(s,'开口向上，$1$、$6$ 在两根之间，$0$、$8$ 在两根外侧。',64,264,1152,65,31,1);
T(s,String.raw`$\begin{cases}f_a(0)=4>0,\\f_a(1)=5-2a<0,\\f_a(6)=40-12a<0,\\f_a(8)=68-16a>0\end{cases}\quad\Longleftrightarrow\quad\frac{10}{3}<a<\frac{17}{4}$`,100,356,1080,220,35,1,{align:'center'});
T(s,'两个不相交区间内各有一个零点，二次函数不会再有其他零点。',64,617,1152,60,30,2);
notes(s,'《三维设计》第77页典例4（3）。','参数边界对应根2/3、6以及1/2、8，均排除。');

s=page('课堂练习：综合练习');
T(s,'（1）求 $2x^2-x-1$ 的零点。',64,139,1152,65,33);
T(s,'（2）$f(x)=x^3-8$ 在 $(1,3)$ 内有几个零点？说明理由。',64,224,1152,83,33);
T(s,'（3）连续函数在区间两端同号，区间内就没有零点。判断并举例。',64,330,1152,100,32);
line(s,'answer_rule',64,462,1216,462,'#BBBBBB',1);
T(s,String.raw`（1）$-\frac12,1$。`,64,490,1152,64,31,1);
T(s,'（2）连续、端点异号且严格递增，恰有一个。',64,558,1152,54,30,1);
T(s,'（3）错误。如 $f(x)=x^2$ 在 $[-1,1]$ 上。',64,622,1152,54,30,1);
notes(s,'（1）（2）据湘教版本节练习改编；（3）自编。');

s=page('课堂小结：零点问题的方法');
row(s,143,'求零点','解 $f(x)=0$，检验定义域。');
row(s,254,'判断所在区间','函数连续、端点异号，说明区间内存在零点。');
row(s,365,'判断零点个数','既说明存在，又排除其他零点。');
row(s,476,'二次零点分布','画草图，结合判别式、对称轴和端点符号。');
T(s,'零点是实数。连续、异号保证至少一个，严格单调保证至多一个。',64,616,1152,66,30);
notes(s,'本课方法归纳。');

s=page('课堂小结：二次函数零点分布');
T(s,String.raw`设 $f(x)=Ax^2+Bx+C\ (A\ne0)$，$x_1<x_2$。`,64,130,1152,65,32);
row(s,222,'两根分居两侧',String.raw`$x_1<t<x_2\quad\Longleftrightarrow\quad Af(t)<0$。`);
row(s,335,'两根在同侧',String.raw`$t<x_1<x_2$：$\Delta>0$，轴在 $t$ 右侧，$Af(t)>0$。`);
T(s,'两根在区间内',70,463,245,74,30,0,{bold:true});
T(s,String.raw`$p<x_1<x_2<q$：$\Delta>0$，轴在 $(p,q)$ 内，`,332,451,867,70,30);
T(s,String.raw`$Af(p)>0,\quad Af(q)>0$。`,332,529,867,68,31);
line(s,'row_rule',66,610,1210,610,'#C0C0C0',1);
T(s,'以上均要求两个不同零点；区间端点与重根必须另查。',64,631,1152,45,28);
notes(s,'二次函数零点分布条件归纳，对任意A≠0成立。');

s=page('课堂小结：本课的数学素养');
row(s,142,'数学抽象','从二次函数推广到一般函数，用 $f(x_0)=0$ 刻画零点。');
row(s,255,'直观想象','用交点理解根与零点，用图象解释连续与异号。');
row(s,368,'逻辑推理','检查定理条件，区分至少、至多与恰有。');
row(s,481,'数学运算','解简单方程，计算端点函数值，检验定义域。');
notes(s,'课程标准（2017年版2025年修订）数学学科核心素养，本课活动映射。');

s=page('布置作业');
T(s,'（1）求 $x^3-x^2-4x+4$ 的零点。',64,154,1152,74,34);
T(s,String.raw`（2）求 $\log_2(x^2-2x-2)$ 的零点，并检验定义域。`,64,259,1152,88,34);
T(s,String.raw`（3）证明 $2^x+\lg(x+1)-2$ 有唯一零点，并确定它所在的相邻整数区间。`,64,383,1152,114,33);
T(s,'（4）已知 $x^2-2ax+4$ 的两个不同零点分居 $1$ 两侧，求 $a$ 的范围。',64,534,1152,114,33);
notes(s,'（1）（2）湘教版本节练习；（3）原PPT第15页；（4）教辅典例4改编。','答案：（1）−2,1,2。（2）−1,3，定义域为(−∞,1−√3)∪(1+√3,+∞)。（3）唯一根(0,1)。（4）a>5/2。');

if(current!==34)throw new Error(`Slide count ${current}`);
applyCompactLayout(slides,math);
await fs.writeFile(path.join(build,'math.json'),JSON.stringify(math,null,2));
await fs.writeFile(path.join(build,'reveals.json'),JSON.stringify(reveals,null,2));
await fs.writeFile(path.join(build,'math-spec.json'),JSON.stringify(Object.fromEntries(math.map(x=>[x.name,{text:x.text,sizePt:x.size*.75,align:x.align,color:x.color.replace('#',''),font:x.textFont,bold:x.bold}])),null,2));
await fs.writeFile(path.join(build,'reveal-spec.json'),JSON.stringify({slides:reveals},null,2));
await fs.writeFile(path.join(build,'headings.json'),JSON.stringify(headings,null,2));
await (await PresentationFile.exportPptx(p)).save(path.join(build,'draft.pptx'));
await fs.writeFile(path.join(build,'native.proto.json'),JSON.stringify(p.toProto()));
console.log(JSON.stringify({slides:current,mathBoxes:math.length,revealSlides:Object.keys(reveals).length,path:path.join(build,'draft.pptx')}));
