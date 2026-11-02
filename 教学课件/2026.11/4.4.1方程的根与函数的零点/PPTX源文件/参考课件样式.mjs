// 样式依据：用户提供《4.2.2指数函数的图像与性质》PPT。
// 仅改变格式和几何位置，不改文字、公式、图象数据或动画分组。
export function applyReferenceStyle(slides,records,reveals){
  const green='#2F9445',red='#FF0000',black='#000000';
  const revealNames=new Set(Object.values(reveals).flat(2));
  const byName=new Map(slides.flatMap(s=>s.shapes.items.map(sh=>[sh.name,sh])));
  const move=(sh,p)=>{const q=sh.position;sh.position={left:p.x??q.left,top:p.y??q.top,width:p.w??q.width,height:p.h??q.height};};
  for(const r of records.filter(r=>r.slide===10&&r.text.includes('，零点为'))){
    r.text=r.text.replace('，零点为','，\n零点为');
    const sh=byName.get(r.name);sh.text=r.text.replace(/\$/g,'');move(sh,{y:532,h:112});
  }
  for(const [n,prefix,before,after] of [[19,'交点至多一个','，横坐标','，\n横坐标'],[23,'$1$ 在两根之间','，对应图象','，\n对应图象']]){
    const r=records.find(r=>r.slide===n&&r.text.startsWith(prefix));
    r.text=r.text.replace(before,after);byName.get(r.name).text=r.text.replace(/\$/g,'');
  }
  for(let i=1;i<slides.length;i++){
    const slide=slides[i];
    for(const sh of slide.shapes.items){
      if(!sh.name?.startsWith(`s${i+1}_`)||sh.name.includes('_heading_')||sh.name.includes('_page_'))continue;
      move(sh,{y:sh.position.top-32});
      if(/_(answer_rule|row_rule|def_rule|theorem_rule)_/.test(sh.name))sh.line={fill:'none',width:0};
      if(/_(axis|arrow|xtick|ytick)_/.test(sh.name))sh.line={fill:black,width:1.25};
    }
    for(const tb of slide.tables.items){
      const p=tb.position;
      tb.position={left:p.left,top:p.top-32,width:p.width,height:p.height};
      tb.borders.assign({fill:'#FFFFFF',width:1,style:'solid'});
      const dims={18:[2,9],22:[6,2]}[i+1];
      if(!dims)throw new Error(`Unexpected content table on slide ${i+1}`);
      for(let r=0;r<dims[0];r++)for(let c=0;c<dims[1];c++){
        const cell=tb.getCell(r,c);
        cell.fill=r===0?'#4875D2':'#D2D9EE';
        cell.text.style={typeface:'宋体',fontSize:32,bold:true,color:r===0?'#FFFFFF':black,alignment:'center',verticalAlignment:'middle',insets:7};
      }
    }
    const header=records.find(r=>r.slide===i+1&&r.name.includes('_heading_'));
    const rule=slide.shapes.items.find(s=>s.name==='直接连接符 2');
    if(rule){
      const start=Math.min(1080,Math.max(350,175+Array.from(header.text).reduce((a,ch)=>a+(ch.charCodeAt(0)>255?37.33:19),0)+18));
      move(rule,{x:start,y:69.33,w:1204.67-start,h:0});
      rule.line={fill:green,width:2.4};
    }
  }
  for(const r of records){
    const sh=byName.get(r.name);
    if(r.slide===1){
      r.textFont='微软雅黑';r.color=r.name.includes('_cover_title_')?'#FFFFFF':green;
      if(r.name.includes('_cover_title_')){r.size=64;move(sh,{x:64,y:467,w:1152,h:125});}
      else if(r.text==='高一数学  4.4.1'){r.size=28;move(sh,{x:335,y:628,w:610,h:46});}
      else{r.size=20;move(sh,{x:1010,y:677,w:210,h:31});}
      r.lineSpacing=1.1;
    }else if(r.name.includes('_heading_')){
      r.textFont='微软雅黑';r.size=112/3;r.bold=true;r.color=green;r.lineSpacing=1.1;
      move(sh,{x:175,y:12,w:1040,h:52});
    }else if(r.name.includes('_page_')){
      r.textFont='宋体';r.size=16;r.bold=false;r.color='#888888';
      move(sh,{x:35,y:679,w:40,h:24});
    }else if(r.size<=24){
      r.textFont='Cambria Math';r.size=24;r.bold=false;r.lineSpacing=1;
    }else{
      r.textFont='宋体';r.size=32;r.bold=true;r.mathBold=true;
      r.color=revealNames.has(r.name)?red:black;
      if([24,26,28].includes(r.slide)&&/^\$[^$]*\$$/.test(r.text.trim()))r.color=red;
      r.lineSpacing=r.slide>=31?1.2:1.4;r.paragraphAfterPt=0;
    }
    const body=r.slide>1&&!r.name.includes('_heading_')&&!r.name.includes('_page_')&&r.size>24;
    sh.text.style={typeface:r.textFont,fontSize:r.size,bold:r.bold,color:r.color,alignment:r.align,verticalAlignment:body&&!/^\$[^$]*\$$/.test(r.text.trim())?'top':'middle',insets:0,autoFit:'none',wrap:'square'};
    if(r.slide===10&&r.text.startsWith('定理只保证'))move(sh,{y:614,h:44});
  }
}
