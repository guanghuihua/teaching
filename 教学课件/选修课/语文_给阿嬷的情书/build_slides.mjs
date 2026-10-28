import fs from 'node:fs/promises';
import path from 'node:path';

export async function buildLesson(presentation, lesson, root) {
  presentation.slides.keep([]);
  const C={paper:'#F4EFE4',ink:'#203E39',gray:'#5D6760',red:'#A14B37',white:'#FFFFFF'};
  const font='Microsoft YaHei';
  presentation.theme.defaultFont=font;
  function text(s,value,x,y,w,h,size=30,color=C.ink,bold=false,serif=false){
    const sh=s.shapes.add({geometry:'textbox',name:'text-'+s.shapes.items.length,
      position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
    sh.text=value;
    sh.text.style={fontSize:size,typeface:serif?'SimSun':font,color,bold,verticalAlignment:'top',insets:0,wrap:'square',autoFit:'none'};
    return sh;
  }
  async function image(s,name,x,y,w,h){
    const p=path.join(root,'图片',name);
    try {await fs.access(p);s.images.add({path:p,alt: name==='archive.jpg'?'暨南大学世界华侨华人文献馆展出的侨批':name==='prop.jpg'?'电影展览中的侨批道具':'电影《给阿嬷的情书》宣传图片',fit:'contain',position:{left:x,top:y,width:w,height:h}});return true;} catch{return false;}
  }
  let elapsed=0;
  for (const [i,d] of lesson.slides.entries()) {
    const s=presentation.slides.add({width:1280,height:720});
    s.background.fill=C.paper;
    const dark=['quote','writing','closing'].includes(d.layout);
    if(dark)s.background.fill=C.ink;
    const fg=dark?C.paper:C.ink;
    const muted=dark?'#D8D2BF':C.gray;
    if(d.layout==='cover'){
      text(s,'高中语文选修课',80,75,670,48,25,C.gray);
      text(s,d.title,80,210,780,100,64,C.ink,true);
      text(s,d.sub,84,325,710,65,37,C.red,false,true);
      text(s,d.text[1],84,486,700,90,29,C.ink);
      await image(s,d.image,890,70,310,558);
    } else {
      text(s,d.title,76,58,1120,80,44,fg,true);
      if(d.layout==='still'){
        await image(s,d.image,78,165,790,445);
        text(s,d.text[0],920,202,290,126,29,C.ink);
        text(s,d.text[1],920,365,290,150,29,C.red);
        text(s,d.text[2],920,560,290,74,22,C.gray);
      } else if(['imageRight','imageLeft'].includes(d.layout)){
        const left=d.layout==='imageLeft';
        await image(s,d.image,left?78:894,158,left?330:300,450);
        const x=left?465:80,w=left?720:740;
        const positions=d.text.length===4?[184,290,398,542]:[190,320,452];
        d.text.forEach((v,j)=>text(s,v,x,positions[j]??570,w,j===d.text.length-1?85:95,j===d.text.length-1?25:30,j===d.text.length-1?C.gray:C.ink,false));
      } else if(d.layout==='quote'){
        if(d.text.length===3){
          text(s,d.text[0],90,185,1110,122,40,fg,false,true);
          text(s,d.text[1],90,350,1110,122,40,fg,false,true);
          text(s,d.text[2],90,545,1100,75,27,muted);
        } else {
          text(s,d.text[0],90,180,1090,250,46,fg,false,true);
          text(s,d.text[1],90,492,1100,110,30,muted);
        }
      } else if(d.layout==='contrast'){
        text(s,d.text[0],84,178,1095,113,33,C.gray,false,true);
        text(s,d.text[1],84,324,1095,186,36,C.ink,false,true);
        text(s,d.text[2],84,d.text.length>3?520:556,1095,82,27,C.red);
        if(d.text.length>3)text(s,d.text[3],84,590,1095,54,27,C.ink);
      } else if(d.layout==='story'){
        d.text.slice(0,3).forEach((v,j)=>{
          text(s,String(j+1).padStart(2,'0'),84,188+j*126,80,60,43,C.red);
          text(s,v,194,194+j*126,985,90,33,C.ink);
        });
        text(s,d.text[3],84,614,1110,42,23,C.gray);
      } else if(d.layout==='writing'){
        await image(s,'prop.jpg',850,230,350,300);
        text(s,'6 分钟',85,170,1000,108,72,C.paper,false,true);
        d.text.slice(0,3).forEach((v,j)=>text(s,v,90,326+j*72,700,60,36,C.paper));
        text(s,d.text[3],90,576,1100,60,27,muted);
      } else if(d.layout==='closing'){
        await image(s,'film2.jpg',942,163,258,428);
        text(s,d.text[0],85,183,810,85,50,fg,false,true);
        text(s,d.text[1],85,325,810,160,39,fg);
        text(s,d.text[2],85,548,810,80,27,muted);
      } else if(d.layout==='sources'){
        d.text.forEach((v,j)=>text(s,v,84,178+j*83,1110,73,27,j===0?C.ink:C.gray));
      } else {
        const gap=d.text.length===4?106:122;
        d.text.forEach((v,j)=>text(s,v,86,184+j*gap,1100,90,j===d.text.length-1&&d.text.length===4?29:34,j===d.text.length-1&&d.text.length===4?C.red:fg));
      }
    }
    text(s,String(i+1).padStart(2,'0'),1170,660,50,30,19,muted);
    const start=elapsed;elapsed+=d.minutes;
    s.speakerNotes.text=`第${i+1}页  ${d.title}\n课堂时间：${start}—${elapsed}分钟（本页${d.minutes}分钟）\n\n【教师逐字稿】\n${d.script}\n\n【活动与停顿】\n${d.action}\n${d.follow?'\n【追问或参考回应】\n'+d.follow+'\n':''}\n【来源与说明】\n${d.source}`;
  }
  return {slides:lesson.slides.length,minutes:elapsed};
}
