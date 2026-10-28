"""Reproducible answer diagrams; parameters are stated, no student data involved."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'题目积累/教材题库/湘教版必修第一册/答案与知识点/figures'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.unicode_minus':False,'figure.dpi':150})
BLUE='#195987';RED='#a54937'

def panel(n=1,cols=2):
    rows=(n+cols-1)//cols if n>1 else 1;cols=min(cols,n)
    fig,axs=plt.subplots(rows,cols,figsize=(6.6,2.9*rows),squeeze=False)
    axes=list(axs.flat)
    for ax in axes:
        ax.axhline(0,color='0.55',lw=.65);ax.axvline(0,color='0.55',lw=.65)
        ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.17)
        ax.set_xlabel('$x$');ax.set_ylabel('$y$',rotation=0,labelpad=8)
    for ax in axes[n:]:ax.set_visible(False)
    return fig,axes

def save(fig,name):
    for ax in fig.axes:
        if ax.get_ylabel() and ax.get_ylabel()!='$y$':
            ax.set_ylabel(ax.get_ylabel(),rotation=90,labelpad=8)
    fig.tight_layout(pad=1.1);fig.savefig(OUT/f'{name}.png',bbox_inches='tight',facecolor='white');plt.close(fig)

def curve(ax,x,y,label=None,color=BLUE):ax.plot(x,y,lw=1.7,color=color,label=label)
def points(ax,x,y):ax.scatter(x,y,s=13,color=BLUE,zorder=3)

def main():
    OUT.mkdir(exist_ok=True)
    f,aa=panel(4)
    xx,yy=np.meshgrid(np.linspace(-2.6,2.6,500),np.linspace(-1.7,1.7,330))
    a=(xx+.65)**2+yy**2<=1.15**2;b=(xx-.65)**2+yy**2<=1.15**2
    for ax,mask,title in zip(aa,[a&~b,b&~a,~a&~b,~(a&b)],['$A\\setminus B$','$B\\setminus A$','$U\\setminus(A\\cup B)$','$U\\setminus(A\\cap B)$']):
        ax.clear();ax.imshow(mask,origin='lower',extent=(-2.6,2.6,-1.7,1.7),cmap='Greys',vmin=0,vmax=2,interpolation='nearest')
        ax.add_patch(Circle((-.65,0),1.15,fill=False,lw=1));ax.add_patch(Circle((.65,0),1.15,fill=False,lw=1))
        ax.add_patch(Rectangle((-2.6,-1.7),5.2,3.4,fill=False,lw=1));ax.text(-1.0,1.25,'A');ax.text(.8,1.25,'B');ax.text(-2.4,1.35,'U');ax.set_title(title);ax.axis('off')
    save(f,'C01-HW013-13')
    f,[ax]=panel();x=np.linspace(-2,3,500);curve(ax,x,x,'$y=x$');curve(ax,x,x*x,'$y=x^2$',RED);points(ax,[0,1],[0,1]);ax.set_ylim(-2,6);ax.legend();save(f,'C01-RV030-17')
    for name,end in [('C03-EX071-5',16),('C03-LAB073',10)]:
        f,[ax]=panel();x=np.linspace(0,end,400);curve(ax,x,np.sqrt(x),'$y=\\sqrt{x}$');k=np.array([0,1,4,9]+([16] if end==16 else [10]));points(ax,k,np.sqrt(k));ax.legend();save(f,name)
    f,[ax]=panel();h=np.array([5,10,15,20,25,30,35]);q=np.array([20,40,90,160,275,437,650]);curve(ax,h,q,'Piecewise linear estimate');points(ax,h,q);points(ax,[7,18],[28,132]);ax.annotate('(7,28)',(7,28),xytext=(9,70));ax.annotate('(18,132)',(18,132),xytext=(20,110));ax.set_xlabel('$H$ (m)');ax.set_ylabel('$Q$ ($10^4$ m$^3$)');ax.legend();save(f,'C03-PR072-2')
    f,[ax]=panel();x=np.linspace(-2,4,400);curve(ax,x,-x*x+2*x+3);points(ax,[-1,0,1,3],[0,3,4,0]);ax.set_title('$f(x)=-(x-1)^2+4$');save(f,'C03-PR072-3')
    for name,fn,title in [('C03-EX075-7',lambda x:abs(x),'$y=|x|$'),('C03-EX075-8',lambda x:abs(x-2)+abs(x+1),'$y=|x-2|+|x+1|$')]:
        f,[ax]=panel();x=np.linspace(-4,5,500);curve(ax,x,fn(x));ax.set_title(title);save(f,name)
    f,aa=panel(2);x=np.linspace(-6,4,500);curve(aa[0],x,abs(x+3));aa[0].set_title('$y=|x+3|$');curve(aa[1],x,abs(x-2)-abs(x+2));aa[1].set_title('$y=|x-2|-|x+2|$');save(f,'C03-PR076-1')
    f,aa=panel(2)
    aa[0].plot([0,10,60,100],[0,8,8,0],color=BLUE);aa[0].set_xlabel('$t$ (s)');aa[0].set_ylabel('$v$ (m/s)')
    for lo,hi,v in [(0,10,.8),(10,60,0),(60,100,-.2)]:
        aa[1].plot([lo,hi],[v,v],color=BLUE);aa[1].plot([lo,hi],[v,v],'o',mfc='white',mec=BLUE,ms=4)
    aa[1].set_xlabel('$t$ (s)');aa[1].set_ylabel('$a$ (m/s$^2$)');save(f,'C03-PR076-3')
    f,aa=panel(2);x=np.linspace(-2,3,400);curve(aa[0],x,3*x*x-5*x+2);points(aa[0],[5/6],[-1/12]);aa[0].set_title('$y=3x^2-5x+2$');curve(aa[1],x,abs(x-1));aa[1].set_title('$y=|x-1|$');save(f,'C03-HW077-6')
    f,[ax]=panel();ax.plot([0,30,50],[6,15,15],color=BLUE);points(ax,[0,30,50],[6,15,15]);ax.set_xlabel('$t$ (s)');ax.set_ylabel('$v$ (m/s)');save(f,'C03-HW077-10')
    f,[ax]=panel();ax.plot([-3,0],[0,0],color=BLUE);ax.plot([0,3],[1,1],color=BLUE);points(ax,[0],[0]);ax.plot(0,1,'o',mfc='white',mec=BLUE);ax.set_ylim(-.2,1.3);ax.set_title('sign as defined in this question');save(f,'C03-HW078-16')
    # The provided answer's qualitative completion matches the current question.
    # Crop just the two completed diagrams from answer PDF page 24 (printed 23).
    im=Image.open(ROOT/'tmp/answer_knowledge/answers/pages/024.png');w,h=im.size
    im.crop((int(w*.085),int(h*.108),int(w*.77),int(h*.222))).save(OUT/'C03-HW085-5-source.png')
    f,[ax]=panel();x=np.linspace(0,20,400);curve(ax,x,np.where(x<=10,9,2*x-11));points(ax,[0,10],[9,9]);ax.set_xlabel('$x$ (m$^3$)');ax.set_ylabel('$y$ (yuan)');save(f,'C03-RV091-14')
    f,[ax]=panel();x=np.linspace(-2,4,400);curve(ax,x,(x-1)**2+1);points(ax,[1],[1]);ax.set_title('One example: $f(x)=(x-1)^2+1$');save(f,'C03-RV091-15')
    f,aa=panel(4)
    for ax,h,k,title in zip(aa,[1,-2,0,0],[0,0,1,-2],['$1/(x-1)$','$1/(x+2)$','$1/x+1$','$1/x-2$']):
        for x in [np.linspace(-5+h,h-.1,250),np.linspace(h+.1,5+h,250)]:curve(ax,x,1/(x-h)+k)
        ax.set_ylim(-6,6);ax.set_title(title)
    save(f,'C03-RV092-19')
    for name,fn,ylim,title in [('C04-PR103-3',lambda x:1/x**2,(0,5),'$y=x^{-2}$'),('C04-HW104-8',lambda x:1/np.cbrt(x),(-3,3),'$y=x^{-1/3}$')]:
        f,[ax]=panel()
        for x in [np.linspace(-5,-.06,500),np.linspace(.06,5,500)]:curve(ax,x,fn(x))
        points(ax,[-1,1],fn(np.array([-1.,1.])));ax.set_ylim(*ylim);ax.set_title(title);save(f,name)
    f,[ax]=panel();x=np.linspace(-2,1.2,400);curve(ax,x,3**x,'$3^x$');curve(ax,x,10**x,'$10^x$',RED);points(ax,[0],[1]);ax.legend();save(f,'C04-EX110-3')
    f,[ax]=panel();x=np.linspace(0,15,400);curve(ax,x,.84**x);ax.axhline(.5,color=RED,ls='--');points(ax,[4],[.84**4]);ax.set_xlabel('$t$ (year)');ax.set_ylabel('$M/M_0$');ax.set_title('$M/M_0=0.84^t$');save(f,'C04-EX112-6')
    f,[ax]=panel();x=np.linspace(-2,2,400);curve(ax,x,5**x,'$5^x$');curve(ax,x,5**(-x),'$5^{-x}$',RED);points(ax,[0],[1]);ax.legend();save(f,'C04-PR113-1')
    f,[ax]=panel();x=np.linspace(-2,1.5,400)
    for fn,label,color in [(lambda x:4**x,'$4^x$',BLUE),(lambda x:4**(-x),'$4^{-x}$',RED),(lambda x:4**(x+1),'$4^{x+1}$','#607848'),(lambda x:4**(x-1),'$4^{x-1}$','#665482')]:curve(ax,x,fn(x),label,color)
    ax.set_ylim(0,12);ax.legend();save(f,'C04-HW113-6')
    f,[ax]=panel();x=np.linspace(-2,5,700);curve(ax,x,2**x,'$2^x$');curve(ax,x,x*x,'$x^2$',RED);roots=[-.766664695962123,2,4];points(ax,roots,2**np.array(roots))
    for r in roots:ax.annotate(f'{r:.4g}',(r,2**r),xytext=(6,8),textcoords='offset points')
    ax.legend();save(f,'C04-HW114-10')
    f,aa=panel(2);x=np.linspace(-3,3,500)
    for ax,a in zip(aa,[2,.5]):
        curve(ax,x,a**x,'$a^x$');curve(ax,x,3*a**x,'$3a^x$',RED);curve(ax,x,-2*a**x,'$-2a^x$','#607848');ax.set_ylim(-12,16);ax.set_title(f'$a={a}$');ax.legend()
    save(f,'C04-HW114-15')
    print('Answer diagrams:',len(list(OUT.glob('*.png'))))

if __name__=='__main__':main()
