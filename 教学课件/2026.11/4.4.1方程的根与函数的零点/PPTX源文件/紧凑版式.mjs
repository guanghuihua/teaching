// 仅调整版面。34页内容、公式字号、原生对象和点击顺序保持不变。
export function applyCompactLayout(slides, records) {
  const byName=new Map();
  for(const slide of slides)for(const shape of slide.shapes.items)byName.set(shape.name,shape);
  const locate=(n,prefix)=>{
    const found=records.filter(r=>r.slide===n&&r.text.startsWith(prefix));
    if(found.length!==1)throw new Error(`Layout selector ${n}: ${prefix} matches ${found.length}`);
    return found[0];
  };
  const place=(shape,patch)=>{
    const a=shape.position;
    shape.position={left:patch.x??a.left,top:patch.y??a.top,width:patch.w??a.width,height:patch.h??a.height};
  };
  const box=(n,prefix,patch,text)=>{
    const r=locate(n,prefix),shape=byName.get(r.name);
    place(shape,patch);
    if(patch.align){r.align=patch.align;shape.text.alignment=patch.align;}
    if(text!==undefined){r.text=text;shape.text=text.replace(/\$/g,'');}
  };
  const rule=(n,kind,y,index=0)=>{
    const rules=slides[n-1].shapes.items.filter(s=>s.name?.startsWith(`s${n}_`)&&s.name.includes(`_${kind}_`)).sort((a,b)=>a.position.top-b.position.top);
    if(!rules[index])throw new Error(`Missing rule ${n}/${kind}/${index}`);
    place(rules[index],{y});
  };
  const graph=(n,dx,dy)=>{
    const labels=new Set(records.filter(r=>r.slide===n&&r.size<=24&&!r.name.includes('_page_')).map(r=>r.name));
    for(const shape of slides[n-1].shapes.items){
      if(!shape.name?.startsWith(`s${n}_`))continue;
      if(labels.has(shape.name)||/_(axis|arrow|xtick|ytick|projection|function_curve|point)_/.test(shape.name)){
        place(shape,{x:shape.position.left+dx,y:shape.position.top+dy});
      }
    }
  };
  const summary=(n,items,ys)=>{
    for(let i=0;i<items.length;i++){
      box(n,items[i][0],{x:70,y:ys[i],w:220,h:62});
      box(n,items[i][1],{x:308,y:ys[i],w:891,h:66});
      rule(n,'row_rule',ys[i]+75,i);
    }
  };

  box(2,'解方程：',{y:130,h:48});
  box(2,'$x^2-2x-3=0$',{y:184});
  box(2,'$(x+1)(x-3)=0$',{y:254});
  box(2,'实数根为',{y:324,h:50});
  box(2,'对应函数',{y:385,h:90},'对应函数 $y=x^2-2x-3$\n的零点也是 $-1,3$。');
  box(2,'一元二次方程的实数根',{y:530,h:60});
  graph(2,-35,-25);

  box(3,'对于方程',{x:64,y:146,w:180,h:52});
  box(3,String.raw`$\ln x+2x-6=0`,{x:265,y:132,w:910,h:80,align:'left'});
  box(3,'不能像一元二次方程',{y:237,h:56});
  box(3,'能否借助相应的函数',{x:64,y:338,w:405,h:56});
  box(3,String.raw`$y=\ln x+2x-6$`,{x:495,y:321,w:680,h:75,align:'left'});
  box(3,'研究方程有没有实数解',{y:451,h:76});

  box(4,'设函数',{y:142,h:50});
  box(4,'使 $f(x_0)=0$',{y:214,h:100});
  rule(4,'def_rule',337);
  box(4,'例如：',{y:374,h:52});
  box(4,'零点为',{y:446,h:62});
  box(4,'零点是实数',{y:535,h:52});

  box(5,String.raw`$x_0\in D`,{x:64,y:145,w:1152,h:64,align:'left'});
  box(5,String.raw`$\Longleftrightarrow$  $x_0$ 是方程`,{x:90,y:236,h:58});
  box(5,String.raw`$\Longleftrightarrow$  $x_0$ 是函数`,{x:90,y:310,h:58});
  box(5,String.raw`$\Longleftrightarrow$  $(x_0,0)`,{x:90,y:384,h:58});
  box(5,'口答：',{y:482,h:60});
  box(5,'零点是 $2$',{y:555,h:52});

  box(6,'图（1）至少经过',{y:551,h:56});
  box(6,'假设路线连续',{y:615,h:42});

  box(7,'图象在区间上连续不断',{x:685,y:170,w:527,h:64});
  box(7,'左端点在',{x:685,y:254,w:527,h:96},'左端点在 $x$ 轴上方，\n右端点在 $x$ 轴下方。');
  box(7,'中间至少与',{x:685,y:388,w:527,h:96});
  box(7,'两端异号：',{y:536,h:60});

  box(8,'如果函数',{x:64,y:142,w:1152,h:62});
  box(8,'是一条连续不断的曲线',{x:64,y:211,w:1152,h:62});
  box(8,'$f(a)f(b)<0$',{x:64,y:280,w:1152,h:62});
  rule(8,'theorem_rule',373);
  box(8,'那么，函数',{x:64,y:382,w:1152,h:70});
  box(8,'即存在',{x:64,y:470,w:1152,h:132});
  box(8,'注意：',{y:642,h:52});

  box(9,String.raw`$f(x)=\frac1x$`,{y:140});
  box(9,String.raw`$f(-1)=-1`,{y:230});
  box(9,'能推出',{y:324,h:62});
  box(9,'不能。',{y:405,h:105});
  box(9,String.raw`而且 $\frac1x=0$`,{y:544,h:64});
  graph(9,-30,-20);

  box(10,'定理只保证',{y:632,h:40});

  box(11,'连续且端点异号',{y:150,h:52});
  box(11,'在该区间严格单调',{y:218,h:52});
  box(11,'两方面结合',{y:312,h:60});
  box(11,'若严格递增',{y:404,h:82});
  box(11,'想一想：',{y:518,h:66});

  box(12,'讨论 $f(x)=2x^3-5$',{y:134,h:64});
  box(12,'函数在 $[1,2]$ 上连续',{y:230,h:54});
  box(12,'$f(1)=-3<0',{y:292,h:72});
  box(12,'所以在 $(1,2)$ 内至少',{y:382,h:58});
  box(12,'又因 $2x^3-5$',{y:466,h:65});
  box(12,'综上，',{y:548,h:60});

  box(13,'求下列函数',{y:132,h:50});
  box(13,'（1）$f(x)=x^2+7x+6$',{x:64,y:215,w:550,h:66});
  box(13,String.raw`（2）$g(x)=1-\log_2(x+3)$`,{x:670,y:215,w:546,h:66});
  rule(13,'answer_rule',296);
  box(13,String.raw`（1）定义域为 $\mathbb{R}$`,{x:64,y:320,w:550,h:204},String.raw`（1）定义域为 $\mathbb{R}$，`+'\n'+String.raw`由 $(x+1)(x+6)=0$，`+'\n'+String.raw`得零点为 $-1,-6$。`);
  box(13,'（2）定义域为',{x:670,y:320,w:546,h:204},String.raw`（2）定义域为 $(-3,+\infty)$。`+'\n'+String.raw`由 $\log_2(x+3)=1$，`+'\n'+String.raw`得 $x=-1$，符合定义域。`);

  box(14,'求函数',{y:134,h:92});
  box(14,'定义域：',{y:248,h:52});
  box(14,'$f(x)=',{y:318,h:95});
  box(14,'所以 $f(x)=0$',{y:442,h:65});
  box(14,'约分后，',{y:540,h:54});

  box(15,'求函数的零点：',{y:134,h:50});
  box(15,'$f(x)=',{y:195,h:132});
  box(15,String.raw`当 $x\le0$`,{y:348,h:97});
  box(15,'当 $x>0$',{y:468,h:66});
  box(15,'所以函数的零点为',{y:555,h:58});

  box(16,'判断',{y:134,h:72});
  box(16,'令 $f(x)=',{y:228,h:60});
  box(16,'$f(2)=',{y:305,h:74});
  box(16,'函数在 $[2,3]$',{y:395,h:66});
  box(16,String.raw`$\ln x$ 与`,{y:485,h:66});
  box(16,'所以原方程',{y:563,h:54});

  box(17,'判断',{y:134,h:66});
  box(17,'定义域为',{y:228,h:56});
  box(17,'$f(1)=-1',{y:300,h:65});
  box(17,'在 $[1,2]$',{y:386,h:76});
  box(17,'又因两项',{y:487,h:90});

  box(18,'二次函数 $f(x)=',{y:130,h:64});
  box(18,'不求系数',{y:204,h:52});
  box(18,'$f(-3)f(-1)',{y:420,h:65});
  box(18,'二次函数连续',{y:507,h:65});
  box(18,'二次函数至多',{y:586,h:50});

  graph(19,0,-15);
  box(19,'共同定义域：',{y:224,h:52});
  box(19,'$2^{-x}$ 严格递减',{y:305,h:102});
  box(19,'交点至多一个',{y:429,h:100});
  box(19,'怎样用函数性质',{y:574,h:54});

  box(20,'令 $h(x)=',{y:134,h:66});
  box(20,'$h$ 在',{y:236,h:50});
  box(20,'$h(1)=',{y:300,h:92});
  box(20,'所以在 $(1,2)$',{y:408,h:54});
  box(20,String.raw`$\log_2x$ 与`,{y:486,h:74});
  box(20,'所以原方程',{y:574,h:51});

  box(21,'已知 $f(x)=',{y:134,h:76});
  box(21,'$f(x)=0',{y:240,h:75});
  box(21,'即研究曲线',{y:346,h:76});
  box(21,'把 $y=',{y:446,h:74});
  box(21,'关键位置：',{y:544,h:54});

  graph(22,0,-20);
  box(22,'因此 $a=4$',{y:476,h:54});
  box(22,'此时零点为',{y:585,h:60});

  box(23,'设 $f_a(x)=',{y:132,h:72});
  graph(23,0,-25);
  box(23,'开口向上。',{x:680,y:258,w:530,h:54});
  box(23,'$1$ 在两根之间',{x:680,y:332,w:530,h:108});
  box(23,'所以 $f_a(1)<0$',{x:680,y:463,w:530,h:66});

  box(24,'$f_a(1)=',{y:136,h:90});
  box(24,'这一条件为什么足够',{y:256,h:56});
  box(24,'开口向上，',{y:332,h:76});
  box(24,'因此在 $1$',{y:428,h:60});
  box(24,'当 $a=',{y:520,h:79});

  box(25,'仍设 $f_a(x)=',{y:132,h:72});
  graph(25,0,-34);
  box(25,String.raw`$\Delta>0$`,{x:680,y:244,w:530,h:74});
  box(25,'$a>1$',{x:680,y:345,w:530,h:74});
  box(25,'$f_a(1)>0$',{x:680,y:446,w:530,h:74});

  box(26,'$'+String.raw`\begin{cases}`,{y:136,h:184});
  box(26,'端点检验',{y:356,h:48});
  box(26,'$a=2$',{x:64,y:423,w:550,h:144},'$a=2$ 时，$f_a(x)=(x-2)^2$，\n只有一个不同零点。');
  box(26,String.raw`$a=\frac52$`,{x:670,y:423,w:546,h:144},String.raw`$a=\frac52$ 时，`+'\n'+String.raw`$f_a(x)=(x-1)(x-4)$，`+'\n'+'一个零点等于 $1$。');

  box(27,'已知 $f_m(x)=',{y:132,h:98});
  box(27,'开口向上，需要同时满足',{y:256,h:52});
  box(27,String.raw`$\Delta>0$`,{y:330,h:64});
  box(27,'$0<m<3$',{y:415,h:64});
  box(27,'$f_m(0)>0',{y:500,h:78});

  box(28,'$'+String.raw`\begin{cases}`,{y:136,h:224});
  box(28,String.raw`$m=\sqrt2$`,{x:64,y:405,w:550,h:144},String.raw`$m=\sqrt2$ 时，判别式为 $0$，`+'\n'+'两个根重合。');
  box(28,String.raw`$m=\frac{11}{6}$`,{x:670,y:405,w:546,h:144},String.raw`$m=\frac{11}{6}$ 时，`+'\n'+'一个根等于端点 $3$。');
  box(28,'因此两个端点均排除',{y:589,h:48});

  box(29,'$f_a(x)=',{y:132,h:94});
  box(29,'开口向上，',{y:250,h:60});
  box(29,'$'+String.raw`\begin{cases}`,{y:334,h:220});
  box(29,'两个不相交区间',{y:580,h:60});

  box(30,'（1）求',{y:134,h:58});
  box(30,'（2）$f(x)=',{y:210,h:72});
  box(30,'（3）连续函数',{y:302,h:88});
  rule(30,'answer_rule',416);
  box(30,'（1）$-',{y:440,h:60});
  box(30,'（2）连续、',{y:508,h:50});
  box(30,'（3）错误。',{y:570,h:52});

  summary(31,[['求零点','解 $f(x)=0$'],['判断所在区间','函数连续、端点异号'],['判断零点个数','既说明存在'],['二次零点分布','画草图']], [146,235,324,413]);
  box(31,'零点是实数。',{y:535,h:66});

  box(32,'设 $f(x)=',{y:130,h:58});
  box(32,'两根分居两侧',{x:70,y:205,w:220,h:62});
  box(32,'$x_1<t<x_2',{x:308,y:205,w:891,h:66});
  rule(32,'row_rule',280,0);
  box(32,'两根在同侧',{x:70,y:298,w:220,h:62});
  box(32,'$t<x_1<x_2$',{x:308,y:298,w:891,h:66});
  rule(32,'row_rule',373,1);
  box(32,'两根在区间内',{x:70,y:410,w:220,h:62});
  box(32,'$p<x_1<x_2<q$',{x:308,y:390,w:891,h:66});
  box(32,'$Af(p)>0',{x:308,y:466,w:891,h:60});
  rule(32,'row_rule',540,2);
  box(32,'以上均要求',{y:568,h:54});

  summary(33,[['数学抽象','从二次函数推广'],['直观想象','用交点理解根'],['逻辑推理','检查定理条件'],['数学运算','解简单方程']], [147,237,327,417]);

  box(34,'（1）求',{y:142,h:64});
  box(34,'（2）求',{y:236,h:78});
  box(34,'（3）证明',{y:344,h:102});
  box(34,'（4）已知',{y:476,h:102});
}
