"""Source-page transcriptions for chapters 2, 3 and sections 4.1--4.2.

Selectors are chapter / main-label type / printed page / original number.
Unnumbered labels on the same page use their recorded Y coordinate instead.
"""
import re
from pathlib import Path

CODES = {'EX':'例题','PR':'练习','HW':'习题','RV':'复习题',
         'TH':'思考','SU':'小结与复习','CA':'案例','LAB':'数学实验'}

FIGURES = {
 'C02-TH032':(38,(383,631,1098,1168)),
 'C02-CA033':(40,(350,620,900,930)),
 'C02-EX041':(48,(780,1370,1135,1595)),
 'C02-PR042':(49,(450,1050,835,1285)),
 'C02-HW044':(51,(525,320,750,585)),
 'C02-EX046':(53,(515,1290,785,1590)),
 'C02-HW049':(56,(840,770,1070,1040)),
 'C02-RV062':(69,(830,1180,1060,1385)),
 'C02-RV063':(70,(510,520,740,715)),
 'C03-LAB073':(80,(215,660,1035,1020)),
 'C03-HW076':(83,(220,1230,1070,1470)),
 'C03-HW077-08':(84,(190,950,620,1220)),
 'C03-HW077-09':(84,(700,945,1055,1215)),
 'C03-HW078-14':(85,(350,900,585,1130)),
 'C03-HW078-15':(85,(730,900,945,1130)),
 'C03-TH079':(86,(290,1010,955,1370)),
 'C03-TH083':(90,(270,360,1000,680)),
 'C03-PR084':(91,(760,1035,1085,1390)),
 'C03-HW085-01':(92,(350,550,910,813)),
 'C03-HW085-05':(92,(245,1330,1000,1570)),
 'C03-RV090':(97,(820,805,1045,1070)),
 'C03-RV091':(98,(390,890,865,1245)),
 'C03-RV092':(99,(260,465,1025,930)),
 'C04-PR103':(108,(290,1070,815,1425)),
 'C04-HW114':(121,(395,400,895,655)),
}

def load_entries(rows):
    entries = {}
    for chapter in (2,3,4):
        source = Path(__file__).with_name(f'midterm_c{chapter:02}.txt')
        chunks = re.split(r'^@@ (\d+) (\w+) (\d+) (\d+)\s*\n', source.read_text('utf-8'), flags=re.M)
        assert not chunks[0].strip()
        for i in range(1,len(chunks),5):
            c,code,p,n,body = chunks[i:i+5]
            c,p,n = int(c),int(p),int(n)
            candidates = [r for r in rows if r['chapter']==c and r['type']==CODES[code]
                          and r['printed_pages'][0]==p]
            if n:
                candidates = [r for r in candidates if r['original_number']==n
                              or (r['original_number'] is None and int(r['id'].rsplit('Y',1)[1])==n)]
            else:
                candidates = [r for r in candidates if r['original_number'] is None]
            assert len(candidates)==1,(c,code,p,n,[(r['id'],r['original_number']) for r in candidates])
            key=candidates[0]['id']
            assert key not in entries,key
            entries[key]=body.strip()
    expected={r['id'] for r in rows if r['midterm_scope'] and r['chapter']!=1}
    assert set(entries)==expected,{'missing':sorted(expected-set(entries)),'extra':sorted(set(entries)-expected)}
    figures={f for body in entries.values() for f in re.findall(r'\\bankfig\{([^}]+)\}',body)}
    assert figures==set(FIGURES),(figures-set(FIGURES),set(FIGURES)-figures)
    return entries
