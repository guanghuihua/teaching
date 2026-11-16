import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const base = path.dirname(fileURLToPath(import.meta.url));
const build = path.join(base, 'build');
const runtime = process.env.CODEX_DEPENDENCIES || 'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies';
process.env.RUNTIME_NODE_MODULES ||= path.join(runtime,'node/node_modules');
const skill = 'C:/Users/user/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
const { Presentation, PresentationFile } = await import(pathToFileURL(path.join(runtime, 'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const { finalizePresentation } = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href);
await fs.mkdir(build, { recursive: true });
const p = Presentation.create({slideSize:{width:1280,height:720}});
const C = {green:'#126831',ink:'#183025',muted:'#65766B',orange:'#A5541A',red:'#B43E35'};
const src = '来源：../教学内容（暂定）.docx，第3课时；../AI伴学_18课时详细教案_40分钟教师用册.docx，第3课时；../第2课_复数与平面旋转/AI伴学_第二课.tex。依实际第2课内容调整顺序，45分钟方案为本次改编。';
const content = [];
function text(s,t,x,y,w,h,size=32,color=C.ink,bold=false,font='Microsoft YaHei'){
  const sh=s.shapes.add({geometry:'textbox',name:`text-${s.shapes.items.length+1}`,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  sh.text=t; sh.text.style={fontSize:size,typeface:font,color,bold,wrap:'none',autoFit:'none',insets:0}; return sh;
}
function body(s,t,y=180,size=32,color=C.ink,x=80,w=1120,h=85){return text(s,t,x,y,w,h,size,color);}
function eq(s,t,y=250,size=52,color=C.green,x=90,w=1100){return text(s,t,x,y,w,90,size,color,false,'Cambria');}
function slide(title,time,notes){
  const s=p.slides.add(); s.background.fill='#FFFFFF';
  if(p.slides.items.length>1) text(s,title,76,50,1130,76,44,C.green,true);
  text(s,`${time} 分钟`,80,666,400,30,19,C.muted);
  text(s,String(p.slides.items.length).padStart(2,'0'),1150,666,60,30,19,C.muted);
  s.speakerNotes.text=`${time}分钟。\n${notes}\n\n${src}`;
  content.push({slide:p.slides.items.length,title,time,notes}); return s;
}
async function img(s,file,x,y,w,h){const b=await fs.readFile(file);s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:file.endsWith('jpeg')?'image/jpeg':'image/png',alt:path.basename(file),fit:'contain',position:{left:x,top:y,width:w,height:h}});}

let s=slide('复数的加法与乘法','00:00—00:30','开场：上次用复数表示点，并看了乘i的旋转。今天学习两个复数怎样相加、相乘，记录自己需要怎样的提示。教师投屏操作AI，学生以纸笔为主。');
await img(s,path.join(base,'../第2课_复数与平面旋转/assets/campus.jpeg'),0,0,1280,365);
text(s,'复数的加法与乘法',78,414,1120,90,60,C.green,true);
text(s,'AI伴学 · 第3课时',82,535,1100,55,30,C.ink);
text(s,'华光辉　　45分钟',82,598,1000,40,25,C.muted);

s=slide('上次的旋转，今天还能解释吗','00:30—04:00','让学生结合图像用1分钟写出i²、i(2+i)及点坐标，再请学生解释计算。图是回顾支架，本页不作独立达标证据。答案：−1，−1+2i，(−1,2)。绕原点逆时针90°，距离不变。若写成1+2i，定位i²替换；若坐标(2,−1)，检查横纵坐标与方向。图取自本课程教师用册配图，计算独立核验。');
await img(s,path.join(base,'../work/teaching_figures/complex_plane.png'),560,160,640,400);
body(s,'结合图像，补全算式',180,32,C.ink,80,480);
eq(s,'i² = ?',265,52,C.green,80,460);eq(s,'i(2 + i) = ?',355,46,C.green,80,470);
body(s,'结果对应哪个点？\n绕哪里、朝哪个方向转？',470,27,C.ink,80,480,110);

s=slide('今天的目标与学习路径','04:00—06:00','教师展示可检验目标。让学生圈出自己最需要检查的一步：展开、替换、合并。今日只需正负数、分配律、合并同类项。三角形式、欧拉公式与微积分均可暂缓。');
body(s,'课末，你能独立完成一道加法和一道乘法。',185,36);
body(s,'需要的基础：正负数、分配律、合并同类项。',290,32);
body(s,'学习次序：回顾定义，尝试运算，用新题检验。',390,32);
body(s,'向AI求助时，能说清自己卡在哪一步。',500,32,C.green);

s=slide('一种新数，沿用熟悉的运算规则','06:00—08:00','回顾定义而非重复整节复数引入。a、b为实数，虚数单位i满足i²=−1。b=0得到实数，复数包含实数。x²+1=0的两个解是±i，不漏−i。不要把实数根式的乘法规则推广到负数。');
eq(s,'i² = −1',175,70);
eq(s,'z = a + bi     (a, b ∈ ℝ)',300,52);
body(s,'3 − 2i 对应点 (3, −2)；5 也可以写成 5 + 0i。',415,30);
body(s,'x² + 1 = 0，在复数范围内有哪些解？',535,34,C.green);

s=slide('先修知识小检查','08:00—11:00','学生先做60秒再核对。①1；②6−3x；③3−2x。此页都是实数代数。将①与−i²连接，②与复数乘法分配律连接，③与带负号的括号连接。若不稳，先给2(3−x)补练，不加新知识。');
body(s,'不用AI，每题写出一步理由。',165,30,C.muted);
eq(s,'①  −(−1)',255,48);eq(s,'②  3(2 − x)',355,48);eq(s,'③  (2 − x) + (1 − x)',455,48);
body(s,'括号前的乘数，要乘到括号里的每一项。',575,29,C.green);

s=slide('复数加法：把两类项分别合并','11:00—14:00','主例来自总教案。先让学生指出可合并的项，再逐行展示。2+1=3，3+(−5)=−2。几何联系只口头说明：坐标分别相加，与上次点表示一致。a+bi+c+di=(a+c)+(b+d)i可口头归纳，不作为记忆门槛。');
eq(s,'(2 + 3i) + (1 − 5i)',180,53);
eq(s,'= (2 + 1) + (3 − 5)i',305,53);
eq(s,'= 3 − 2i',430,60);
body(s,'实数项与实数项相加，含 i 的项合并系数。',568,30);

s=slide('加法练习：负号也要一起带上','14:00—16:00','独立2分钟，不提前翻答案。①基础，考同类项；②基础，考负数和括号。预期方法均为分别合并两类项，易错为−2+5和1+(−3)。评价：每题实数项1分、i的系数1分，口头要求说明负号来源。');
body(s,'先写算式，再写结果对应的点。',175,31);
eq(s,'①  (3 − 2i) + (−1 + 5i)',285,50);
eq(s,'②  (2 − i) + (−3 + 4i)',415,50);
body(s,'检查：3 − 2i 中，i 的系数是多少？',565,30,C.green);

s=slide('核对：结果和坐标能否对上','16:00—17:00','①2+3i，(2,3)；②−1+3i，(−1,3)。学生若只写答案正确但不会解释，要求说明哪两组数字合并。对照原始作答，用不同颜色改最早出错的一行。');
eq(s,'①  2 + 3i',205,58);body(s,'对应点 (2, 3)',295,32,C.muted);
eq(s,'②  −1 + 3i',405,58);body(s,'对应点 (−1, 3)',495,32,C.muted);
body(s,'改错时，保留自己的原始步骤。',590,28,C.green);

s=slide('两个复数相乘，会出现哪些项','17:00—18:00','先不计算结果。邀请学生说出第一个1分别乘2与−i，第二个i也分别乘2与−i，一共四个乘积。强调“两个实部相乘、两个虚部相乘”会漏交叉项。');
eq(s,'(1 + i)(2 − i)',240,72);
body(s,'先不合并，写出展开后的四个乘积。',420,36);
body(s,'每个括号中的每一项，都要与另一括号各项相乘。',535,29,C.green);

s=slide('乘法：展开、替换，再合并','18:00—21:00','主例来自总教案。学生跟写三行，每次追问当前使用的规则。四项2、−i、2i、−i²；用i²=−1得2−i+2i+1；最终3+i。一般公式可在学生追问时补充，不额外要求背诵。');
eq(s,'(1 + i)(2 − i)',155,48);
eq(s,'= 2 − i + 2i − i²',265,52);
eq(s,'= 2 − i + 2i + 1',375,52);
eq(s,'= 3 + i',485,58);
body(s,'四项是否齐全？i² 换成了什么？',595,29,C.green);

s=slide('最容易丢的负号：−i²','21:00—23:00','对比先平方再取负与整体平方。−i²=−(i²)=1，而(−i)²=(−i)(−i)=i²=−1。先做实数类比−2²=−4与(−2)²=4，再返回i。重点是运算顺序，不说“负负得正”而省略括号。');
eq(s,'−i² = −(−1) = 1',205,58,C.green);
eq(s,'(−i)² = (−i)(−i) = −1',360,54,C.orange);
body(s,'两式的括号不同。先确定平方作用于谁。',520,34);

s=slide('平方中的交叉项','23:00—25:00','教学自编错误样例，不冒充AI回答。待检查：(1+i)²=1+i²=0，第一等号漏掉2i。可用(1+1)²≠1²+1²唤起已有经验，说明平方须按两个相同括号相乘。正确结果1+2i+i²=2i。');
body(s,'待检查的算式（课堂自编错误样例）',165,28,C.muted);
eq(s,'(1 + i)² = 1 + i² = 0',250,56,C.red);
body(s,'最早出错的是哪一个等号？漏掉了什么？',390,35);
body(s,'提示：把平方写成两个相同的括号相乘。',515,32,C.green);

s=slide('先尝试，再决定要什么帮助','25:00—28:00','主活动题来自总教案。先独立2分钟，再同桌指出卡点。基础组可先做(2+i)+(1−i)，结果3；之后参与乘法。此时不展示答案。目标是完整展开，难度中等，易错是最后i·(−i)=−i²。观察学生能否指出具体待检查行。');
eq(s,'(2 + i)(1 − i)',220,70);
body(s,'先独立算2分钟，保留所有步骤。',380,35);
body(s,'卡住时圈出：展开、替换 i²，还是合并？',485,32);
body(s,'已经完成：换一种展开次序检查。',585,29,C.green);

s=slide('给AI的一次具体求助','28:00—30:00','教师课前打开已登录的学校认可工具。只输入匿名算式与错误步骤，不含学生身份信息。选一段课堂步骤输入，若现场没有合适样例可用下一页预设错误，但明确为自编。提示词是行为请求，不能保证模型一定遵守。两分钟截止，无网直接口头使用同样提示。');
body(s,'“我只学过初中代数，知道 i² = −1。',180,32);
body(s,'我在计算 (2 + i)(1 − i)，我的步骤是……',270,32);
body(s,'请先检查最早出错的一步，只给一个提示。',360,32,C.green);
body(s,'等我修改后再核验，先不要给完整答案。”',450,32);
body(s,'记录：我原来怎么写、得到什么提示、为何修改。',580,27,C.muted);

s=slide('一条提示之后，自己完成核验','30:00—32:00','让学生指出红色等号两侧为何不等，再核对下方正确计算。自编错误把−i²算成−1。正确结果3−i。学生只记录一条实际提示，没用到AI则写同桌或教师提示，不能虚构真实AI记录。');
body(s,'课堂自编错误样例',155,26,C.muted);
eq(s,'2 − 2i + i − i² = 1 − i',220,52,C.red);
body(s,'检查 −i² 这一项，然后自己改写：',345,32);
eq(s,'2 − 2i + i + 1 = 3 − i',435,54,C.green);
body(s,'核验依据：四个乘积齐全，且 i² = −1。',565,29);

s=slide('合上AI，独立完成新题','32:00—36:00','保持4分钟独立时间，不看例题或AI。①基础加法，答案2+3i，2分：两类项各1分。②基础到中等乘法，答案1+3i，3分：完整展开1分、正确替换i²1分、合并1分。两题合计5分，仅作本课形成性检测，不冒充课程总评价。要求解释一个负号。');
body(s,'两题都写步骤，暂不讨论。',165,31,C.muted);
eq(s,'①  (4 − 3i) + (−2 + 6i)',265,50);
eq(s,'②  (2 + i)(1 + i)',395,54);
body(s,'在第二题中，标出使用 i² = −1 的那一步。',555,31,C.green);

s=slide('核对独立练习','36:00—38:00','先让同桌仅核对指定步骤，再展示答案。①2+3i；②2+2i+i+i²=2+3i−1=1+3i。若①正确②漏交叉项，下次先补分配律；若展开正确但i²错误，回到定义。教师按证据记录，不把一题错误概括为“不会复数”。');
eq(s,'①  2 + 3i',180,60);
eq(s,'②  (2 + i)(1 + i)',300,48);
eq(s,'= 2 + 2i + i + i²',395,48);
eq(s,'= 1 + 3i',490,58);
body(s,'如果错了：最早是哪一行？属于哪一步？',595,29,C.green);

s=slide('回到平面：平方的结果落在哪里','38:00—40:00','连接上一课而不新增任意角旋转。由(1+i)²=1+2i−1=2i，对应(0,2)。错误答案0会把结果画在原点。点表示用于暴露和解释计算结果，本页不将“看起来对”作为独立证明。学生在纸上标出(1,1)与(0,2)，不要求理解一般乘法的角度与伸缩。');
eq(s,'(1 + i)² = 1 + 2i + i² = 2i',205,53);
body(s,'原来的数 1 + i，对应点 (1, 1)。',355,34);
body(s,'运算结果 2i，对应点 (0, 2)。',455,34,C.green);
body(s,'请在纸上标点。若算成0，结果会被画在哪里？',565,30);

s=slide('离堂卡：能算，也能解释','40:00—42:00','两分钟独立写，随后收卡或留原始记录，不提前揭示答案。①i是满足i²=−1的虚数单位；x²+1=0两解±i，2分。②(1−i)²=−2i，展开替换各1分。③写出自己仍需检查的一步，形成下一次支持证据，不计对错分。');
body(s,'① i 满足什么关系？x² + 1 = 0 的两个解是什么？',190,32);
body(s,'② 计算 (1 − i)²，并写出关键一步。',330,34);
body(s,'③ 下次遇到新运算，你会先检查哪一步？',475,32,C.green);
body(s,'独立完成。用证据说明自己会了什么。',590,28,C.muted);

s=slide('最后核对一次','42:00—44:00','①i²=−1，x=±i，代入两个值均使平方加1为0。②(1−i)²=1−2i+i²=−2i。与上次结果i(2−i)=1+2i区分，说明今天会两个复数相乘。学生不抹原始错误，写出修改理由。');
eq(s,'i² = −1       x = i 或 x = −i',200,49);
eq(s,'(1 − i)² = 1 − 2i + i²',345,53);
eq(s,'= −2i',460,62);
body(s,'平方展开中，交叉项和 i² 的替换都要保留。',585,31,C.green);

s=slide('留下自己的学习证据','44:00—45:00','口头回收：我原来卡在……；提示让我注意……；现在能独立完成……。课后约8分钟，两题(2−i)+(−3+4i)=−1+3i，(1+2i)(1−i)=3+i，答案只在教师备注。选做i³=−i、i⁴=1，解释循环。下一课可接加法、伸缩与旋转组合，本页不替代后续课程安排。');
body(s,'我原来卡在……',190,36);
body(s,'一条有用的提示是……，因为……',290,36);
body(s,'现在不看AI，我能独立完成……',390,36,C.green);
body(s,'课后约8分钟',510,28,C.muted);
eq(s,'(2 − i) + (−3 + 4i)     (1 + 2i)(1 − i)',570,37,C.ink);

await fs.writeFile(path.join(build,'slide-plan.json'),JSON.stringify(content,null,2),'utf8');
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(candidate);
console.log(`Exported ${p.slides.items.length} slides`);
for(const [i,sl] of (process.env.FINALIZE_ONLY==='1'?[]:p.slides.items.entries())){
  const b=await p.export({slide:sl,format:'png',scale:1});
  await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));
  console.log(`Rendered ${i+1}`);
}
const finalPath=path.join(base,'课件/AI伴学_第三课_复数加法与乘法_45分钟.pptx');
await fs.mkdir(path.dirname(finalPath),{recursive:true});
if(process.env.RENDER_ONLY!=='1') {
 const result=await finalizePresentation({workspaceDir:base,candidatePath:candidate,finalPath,
 pythonExecutable:path.join(runtime,'python/python.exe'),
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],
 fontPolicy:{basis:'design',families:['Microsoft YaHei','Cambria']},
 requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],verifyArtifactToolImport:true,
 receiptPath:path.join(build,'validation.json')});
 console.log(JSON.stringify(result));
}
