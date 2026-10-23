import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const base=path.dirname(fileURLToPath(import.meta.url)),build=path.join(base,'build');
const runtime=process.env.CODEX_DEPENDENCIES||'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies';
process.env.RUNTIME_NODE_MODULES||=path.join(runtime,'node/node_modules');
const skill='C:/Users/user/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(runtime,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const p=Presentation.create({slideSize:{width:1280,height:720}});
await fs.mkdir(build,{recursive:true});
const green='#126831',ink='#183025',muted='#63756B',red='#AB3838',orange='#A65A1F';
const url='https://api.pageplace.de/preview/DT0400.9780192695451_A46510629/preview-9780192695451_A46510629.pdf';
const source=`参考：Tristan Needham, Visual Complex Analysis, 25th Anniversary Edition, OUP, 2023, §1.3.3, pp.18–22，尤其图1.12b；${url}。只节选图1.12的两个构型。以下坐标选择、代数推导、数值任务及45分钟教学组织为本次独立改编，不复制原书长篇正文。`;
let plan=[];
function tx(s,t,x,y,w,h,z=32,col=ink,bold=false,font='Microsoft YaHei'){
 const v=s.shapes.add({geometry:'textbox',name:`text-${s.shapes.items.length+1}`,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 v.text=t;v.text.style={fontSize:z,typeface:font,color:col,bold,autoFit:'none',wrap:'none',insets:0};return v;
}
function body(s,t,y=180,z=32,col=ink,x=76,w=1120,h=75){return tx(s,t,x,y,w,h,z,col);}
function eq(s,t,y=280,z=52,col=green,x=90,w=1100){return tx(s,t,x,y,w,86,z,col,false,'Cambria');}
function sl(title,time,notes){let s=p.slides.add();s.background.fill='#FFFFFF';if(p.slides.items.length>1)tx(s,title,76,48,1135,80,43,green,true);tx(s,`${time} 分钟`,76,668,430,28,18,muted);tx(s,String(p.slides.items.length).padStart(2,'0'),1150,668,60,28,18,muted);s.speakerNotes.text=`时间：${time}\n${notes}\n\n${source}`;plan.push({page:p.slides.items.length,title,time,notes});return s;}
async function im(s,f,x,y,w,h){const b=await fs.readFile(f);s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:f.endsWith('jpeg')?'image/jpeg':'image/png',alt:path.basename(f),fit:'contain',position:{left:x,top:y,width:w,height:h}});}
async function tri(s,labels=false){await im(s,path.join(base,'assets/vca-fig-1-12b.png'),65,150,420,500);if(labels){tx(s,'A(0)',188,343,80,35,25,green,true);tx(s,'B(b)',397,299,85,35,25,green,true);tx(s,'C(c)',350,522,85,35,25,green,true);} }

let s=sl('复数破解平面几何','00:00—00:30','本课以几何问题为主体。上次已经用乘i描述直角旋转，今天把这一动作与位移、中点组合起来。目标是解释一个对任意三角形都成立的关系。原运算版是上一轮初稿，本版按教师明确的几何主题重做。');
await im(s,path.join(base,'../第2课_复数与平面旋转/assets/campus.jpeg'),0,0,1280,345);
tx(s,'复数破解平面几何',78,390,1110,85,61,green,true);tx(s,'两个正方形，藏着什么关系？',82,500,1100,60,36,ink);tx(s,'AI伴学 · 第3课时　　华光辉　　45分钟',82,594,1120,45,26,muted);

s=sl('任意三角形中的一个意外关系','00:30—04:00','图1.12b来自指定参考书。先读条件：非退化三角形的两边外侧分别作正方形，中心为p、s，第三边中点为m。图中已标直角，活动任务是解释它为何必然成立，不能当作盲测猜想。学生先用纸笔尝试连接中心、用全等或旋转分析1分钟。初等解法存在，不能宣称初中方法不可能解决。图中小写标号也用来表示点对应的复数。');
await tri(s);body(s,'两边外侧分别作正方形。',190,32,ink,565,640);body(s,'中心为 p、s，第三边中点为 m。',280,30,ink,565,650);eq(s,'mp = ms，且 mp ⟂ ms',390,42,green,565,650);body(s,'为什么三角形怎样变化，\n这个关系都成立？',500,33,ink,565,650,100);

s=sl('几何中的一段路，用复数相减','04:00—07:00','回顾a+bi与点对应。点的位置是a、b，从A到B的有向位移是b−a，不是a−b。例A=1+i、B=4+3i，位移3+2i。口头说出向右3向上2。本页不引入向量公理；把位移理解为带方向的路。长度与方向的比较都应比较位移。');
eq(s,'A(a)，B(b)    从 A 到 B：b − a',185,48);eq(s,'(4 + 3i) − (1 + i) = 3 + 2i',325,52);body(s,'点的位置，与“从一个点怎样走到另一个点”不同。',475,33);body(s,'要比较两条线段的方向，先把它们写成位移。',575,30,green);

s=sl('旋转中心换了，先减再加','07:00—10:00','上次iz仅是绕原点逆时针90°。绕A(a)旋转：先计算z−a，再乘i，最后加a回到原坐标系。公式w=a+i(z−a)。以a=1+i,z=3+i举例，w=1+3i；错用iz会得−1+3i。来源为原书p.20旋转分解思想，本课只取90°，不需要指数或三角形式。');
eq(s,'w = a + i(z − a)',205,70);body(s,'z − a：从中心出发的位移',365,34);body(s,'i(z − a)：把这段位移逆时针旋转90°',465,34);body(s,'再加 a：得到旋转后终点的位置',565,34,green);

s=sl('小检查：中心不是原点','10:00—12:00','自编基础题：A(1,1)，Z(3,1)，绕A逆时针90°的终点W(1,3)。先独立1分钟，随后口头核对，答案写在备注不提前显示。目标是识别位置与位移，难度基础。若得(−1,3)，说明误用了iz。评价：明确使用z−a，且最后加回a，各1分。');
body(s,'以 A(1,1) 为中心，将 Z(3,1) 逆时针旋转90°。',190,33);body(s,'请先在纸上判断终点，再写复数算式。',315,34);eq(s,'a = 1 + i，z = 3 + i',440,52);body(s,'检查：你最后有没有把中心的位置加回来？',575,31,green);

s=sl('一个正方形的中心怎样表示','12:00—16:00','先以水平边作口头手势，再回到任意方向有向边AB。从A到边中点走(b−a)/2；中点到正方形中心的位移与半条边等长垂直。正方形在有向边AB左侧时取+i，右侧取−i。因此中心=(a+b)/2±i(b−a)/2。强调“左右”相对于有向边，不能只看屏幕上方或下方。此页为主问题唯一新构造工具。');
body(s,'沿有向边 AB，先走到中点，再向侧面走半条边。',175,32);eq(s,'边的中点：(a + b)/2',285,47);eq(s,'左侧中心：(a + b)/2 + i(b − a)/2',405,46);eq(s,'右侧中心：(a + b)/2 − i(b − a)/2',520,46,orange);

s=sl('主问题：把公共顶点取为原点','16:00—18:00','重新展示同一构型便于追踪，不把同一图当独立证据。三角形ABC按顺时针排列，A取作原点，B、C对应b、c；即Im(conj(b)c)<0，只供教师理解，不给学生新术语。改变坐标原点不改变线段长度与夹角，因此选择a=0不损失一般性。图中A、B、C是本课加注，原书p、s、m标号保留。AB外侧在有向AB左侧，AC外侧在有向AC右侧。');
await tri(s,true);body(s,'A 取为原点，B、C 对应 b、c。',180,30,ink,560,665);body(s,'A、B、C 按顺时针排列。',270,31,ink,560,665);body(s,'AB 上的外接正方形中心记 p。',360,29,ink,560,665);body(s,'AC 上的外接正方形中心记 s。',450,29,ink,560,665);body(s,'BC 的中点记 m。',540,31,green,560,665);

s=sl('第一个中心：半条边，再转直角','18:00—20:00','A=0，AB位移为b，左侧中心由b/2+i b/2得到。让学生分别解释两个加数，而不是只抄公式。外侧取+i因为ABC按顺时针，此处若改为逆时针，符号必须同步改变。');
await tri(s,true);body(s,'AB 外侧在有向边 AB 左侧。',190,29,ink,555,665);eq(s,'p = b/2 + ib/2',320,48,green,555,665);eq(s,'p = (b + ib)/2',435,48,green,555,665);body(s,'先到中点，再向外侧走。',565,30,green,555,665);

s=sl('第二个中心：这次向右转','20:00—22:00','AC外侧位于有向AC右侧，故s=c/2−ic/2。顺时针90°对应−i，可用−i·1=−i检验。让学生对照图指出为什么此处不能沿用+i。目标为方向表达，难度中等，易错是两个中心都同号。');
await tri(s,true);body(s,'AC 外侧在有向边 AC 右侧。',190,29,ink,555,665);eq(s,'s = c/2 − ic/2',320,48,green,555,665);eq(s,'s = (c − ic)/2',435,48,green,555,665);body(s,'顺时针90°，对应乘 −i。',565,30,orange,555,665);

s=sl('第三边的中点，只需要平均数','22:00—23:00','m=(b+c)/2，因为横纵坐标分别取平均。请学生把三个表达式放在同一张纸上，下一步要相减而不是比较p和s。避免将复数中点公式背成脱离坐标的规则。');
eq(s,'p = (b + ib)/2',180,52);eq(s,'s = (c − ic)/2',310,52);eq(s,'m = (b + c)/2',440,60);body(s,'中点：横坐标取平均，纵坐标也取平均。',575,30,green);

s=sl('等长且垂直，合成一个目标','23:00—25:00','MP的位移是p−m，MS的位移是s−m。本课方向下目标s−m=i(p−m)。非退化三角形保证这两段非零，故垂直有定义。由等式得两位移等长且相差逆时针90°。不能写s=ip，因为那会把旋转中心错设为原点。');
body(s,'从 m 到 p：p − m；从 m 到 s：s − m。',185,34);eq(s,'s − m = i(p − m)',325,68);body(s,'如果这个等式成立，就同时得到：',470,34);body(s,'mp = ms，且 mp ⟂ ms。',570,37,green);

s=sl('只算两段位移，不算长度和斜率','25:00—28:00','学生先把p−m化简，教师再展示另一式。2(p−m)=b+ib−b−c=ib−c；2(s−m)=c−ic−b−c=−b−ic。乘i得i(ib−c)=−b−ic。只用分配律和i²=−1，不需一般复数乘法公式，不展开模长和斜率。保留学生补出−b这一项的时间。');
eq(s,'2(p − m) = ib − c',170,52);eq(s,'2(s − m) = −b − ic',290,52);eq(s,'i(ib − c) = i²b − ic = −b − ic',420,49);body(s,'同一个表达式出现了：s − m = i(p − m)。',570,31,green);

s=sl('一个等式，解释两个几何结论','28:00—30:00','回到最初图形，邀请学生完整复述：从m到p的位移乘i，就得到从m到s的位移；长度不变，方向逆时针90°。学生必须说旋转中心m，不能说绕A。图中p与s本身不满足s=ip，除非m=0。此处构型重复是有意保持推导标号一致。');
await tri(s);eq(s,'s − m = i(p − m)',235,46,green,555,665);body(s,'以 m 为中心，p 旋转90°后到 s。',365,31,ink,555,665);body(s,'所以 mp = ms，且 mp ⟂ ms。',475,31,ink,555,665);body(s,'任意三角形都成立，\n因为推导没有限定 b、c 的数值。',565,26,muted,555,665,80);

s=sl('换一组数，检验你能否使用它','30:00—33:00','自编支持练习，ABC顺时针非退化：A=0,B=4+2i,C=6−2i。先让学生独立算中心与中点；若困难，先只算p。参考p=1+3i,s=2−4i,m=5；p−m=−4+3i，s−m=−3−4i。难度中等。评价：三个位置各1分，位移相减与乘i关系各1分，说明一次数值核验不能替代一般证明。');
eq(s,'A：0，B：4 + 2i，C：6 − 2i',190,49);body(s,'仍在 AB、AC 外侧作正方形，中心为 p、s。',320,32);body(s,'① 求 p、s，以及 BC 的中点 m。',425,33);body(s,'② 计算 p − m、s − m，检查旋转关系。',535,33,green);

s=sl('核对：两条位移互相检查','33:00—34:00','三个中心位置的计算参见上一页备注。位移−4+3i乘i得到−3−4i，平方长度均25，因此两线段都长5。长度核验可以佐证运算，但单凭等长不能说明垂直；真正解释方向的是乘i关系。');
eq(s,'p = 1 + 3i，s = 2 − 4i，m = 5',175,49);eq(s,'p − m = −4 + 3i',310,53);eq(s,'s − m = −3 − 4i = i(−4 + 3i)',440,48);body(s,'这次算对了，不等于只凭一个例子证明了所有情况。',575,29,green);

s=sl('请AI查错：漏掉的是什么','34:00—36:00','课堂自编错误样例，非真实AI回答。待检查“以m为中心逆时针旋转90°，所以s=ip”漏掉中心m。正确s−m=i(p−m)。教师投屏仅输入这句匿名样例，请求一个检查问题；最多等30秒，没网则教师直接问“i乘的是点的位置还是从m出发的位移？”不用学生身份和整本教材。回答是否可靠以旋转中心及算式为证据。');
body(s,'课堂自编错误样例',165,27,muted);body(s,'“以 m 为中心，逆时针旋转90°。',245,35,red);eq(s,'所以 s = ip。”',315,53,red);body(s,'给AI的请求：',415,30);body(s,'“先问我一个关于旋转中心的问题，\n帮助我检查这句话，不直接给完整证明。”',475,32,green,76,1120,115);body(s,'核验依据：这里应比较点的位置，还是两段位移？',610,26,muted);

s=sl('独立迁移：这次不看AI和例题','36:00—39:00','独立3分钟，新数据A=0,B=4,C=2−2i，仍是顺时针非退化三角形。答案p=2+2i，s=−2i，m=3−i；p−m=−1+3i，s−m=−3−i。6分：三个位置各1分，两个位移共1分，关系1分，几何解释1分。基础支持仅给中心公式，不直接给数值；教师如提供公式应记录为有提示完成。');
eq(s,'A：0，B：4，C：2 − 2i',185,53);body(s,'外接正方形中心仍记 p、s，BC 中点记 m。',310,32);body(s,'① 求 p、s、m，再求从 m 出发的两段位移。',425,31);body(s,'② 用一个等式说明两线段的长度与夹角关系。',545,31,green);

s=sl('核对：结论要回到图形','39:00—40:00','学生保留原始步骤，再核对。三个位置与两位移见式。s−m=i(p−m)说明绕m逆时针90°，两线段等长且垂直。若中心同号错误，回到有向边左右侧；若位置对位移错，回到终点减起点。');
eq(s,'p = 2 + 2i，s = −2i，m = 3 − i',170,49);eq(s,'p − m = −1 + 3i',305,53);eq(s,'s − m = −3 − i = i(p − m)',435,51);body(s,'旋转中心是 m。两条线段等长且垂直。',575,32,green);

s=sl('回看上次的四边形谜题','40:00—42:00','来源原书图1.12a及第2课附加探究。这里明确是回扣，不当作全新定理。对逆时针凸四边形ABCD，在四边外侧作正方形，中心P,Q,R,S。取BD中点M：把四边形分成ABD与CBD，应用今日小结论有S−M=−i(P−M)，R−M=i(Q−M)，于是i(R−P)=S−Q。故PR与QS等长垂直。原书图方向、字母不同，只作构型展示，图中大写A,B是连线位移标记，并非本课顶点名；不要混用。课堂只口头介绍“沿对角线分成两个三角形”，完整拼接作为选做，避免超时。');
await im(s,path.join(base,'assets/vca-fig-1-12a.png'),65,180,525,460);body(s,'四条边外作正方形。',195,32,ink,650,560);body(s,'相对中心的连线，\n也等长且垂直。',295,34,green,650,560,110);body(s,'提示：沿一条对角线分开，\n能否找到今天的两个小构型？',460,29,ink,650,560,110);

s=sl('困难的几何关系，怎样变成算式','42:00—44:00','离堂口头或纸面解释，不再加繁琐计算。①比较两条线段应写终点减起点；②带i的位移等式同时表示等长与90°；③中点条件使公式里b、c消去；④公式是对几何条件的翻译，画图与一般推导互相校验。请学生选择一条完整解释，不要求背五个公式。');
body(s,'位置相减，得到有向位移。',185,36);body(s,'中点取平均，直角旋转乘 i 或 −i。',285,36);body(s,'比较两段位移，用一个等式表达等长与垂直。',385,34,green);body(s,'离堂问题：为什么不能把 s − m = i(p − m)\n随意改写成 s = ip？',520,32,ink,76,1120,100);

s=sl('课后可以留下怎样一份几何报告','44:00—45:00','必做约8分钟：用自己的图和语言解释中心公式与关键位移等式，标注AI支持部分和独立完成部分。选做：一般点T=t替代中点m，若s−t=i(p−t)，代入得(1−i)t=s−ip=(1−i)(b+c)/2，所以t=m，且三角形非退化。此为独立推导的进一步探究，不谎称原书练习原文。另可尝试前页四边形拼接。参考书仅作为教师拓展，不要求学生阅读整本英文教材。');
body(s,'必做：用一张图和关键等式，解释今天的结论。',185,32);body(s,'写清：哪个条件用在了哪一步？',300,34,green);body(s,'选做：把 m 换成 BC 上任意点 t。\n若仍有 s − t = i(p − t)，t 必须是中点吗？',420,32,ink,76,1120,115);body(s,'参考：Needham《Visual Complex Analysis》\n第1章 §1.3.3，图1.12及旋转的讨论',570,23,muted,76,1120,75);

await fs.writeFile(path.join(build,'slide-plan.json'),JSON.stringify(plan,null,2),'utf8');
const candidate=path.join(build,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);console.log(`Exported ${p.slides.items.length} slides`);
if(process.env.FINALIZE_ONLY!=='1')for(const [i,s]of p.slides.items.entries()){const b=await p.export({slide:s,format:'png',scale:1});await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));console.log(`Rendered ${i+1}`);}
const finalPath=path.join(base,'课件/AI伴学_第三课_复数破解平面几何_45分钟.pptx');await fs.mkdir(path.dirname(finalPath),{recursive:true});
console.log(JSON.stringify(await finalizePresentation({workspaceDir:base,candidatePath:candidate,finalPath,pythonExecutable:path.join(runtime,'python/python.exe'),integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],fontPolicy:{basis:'design',families:['Microsoft YaHei','Cambria']},requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')})));
