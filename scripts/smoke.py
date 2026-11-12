"""Exercise the actual running HTTP services without pretending this is rendered browser QA."""
import json
from pathlib import Path
import httpx


def smoke():
    """Check library, live stream, proofs, help, diagnosis, generation, arena and recorded artifacts."""
    records={}
    with httpx.Client(base_url='http://127.0.0.1:8000',timeout=40) as client:
        library=client.get('/api/puzzles').raise_for_status().json()
        assert len(library)>=10 and all('solution' not in p for p in library)
        demo=next(p for p in library if p.get('demo'))
        events=[]
        result=None
        with client.stream('POST','/api/solve/stream',json={'puzzle':demo['puzzle'],'strategy':'human'}) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                item=json.loads(line)
                if item['kind']=='event':events.append(item['event'])
                if item['kind']=='result':result=item['result']
                assert item['kind']!='error'
        assert result and result['verification']['valid']
        assert {'branch','backtrack','solved'}<={e['type'] for e in events}
        records['stream']={'puzzle':demo['id'],'events':len(events),'status':result['status'],'verification':result['verification']}
        chosen=library[0]
        for level in (1,2,3):
            hint=client.post('/api/hint',json={'puzzle':chosen['puzzle'],'level':level}).raise_for_status().json()
            assert ('value' not in hint) if level<3 else bool(hint.get('value'))
        records['hints']='three levels, final verified digit reveal'
        complete=client.post('/api/check',json={'puzzle':demo['puzzle'],'entries':result['solution']}).raise_for_status().json()
        assert complete['complete']
        key=next(iter(result['solution']))
        wrong={key:result['solution'][key]%9+1}
        checked=client.post('/api/check',json={'puzzle':demo['puzzle'],'entries':wrong}).raise_for_status().json()
        assert checked['classification'] in ('rule_violation','solution_incompatible')
        diagnosis=client.post('/api/diagnose',json={'puzzle':demo['puzzle'],'entries':wrong}).raise_for_status().json()
        records['diagnosis']={k:diagnosis[k] for k in ('contradiction','shortest','explored')}
        arena=client.post('/api/arena',json={'ids':[demo['id']]}).raise_for_status().json()
        assert len(arena['results'])==7 and all(r['status']=='solved' for r in arena['results'])
        records['arena']={'runs':len(arena['results']),'fastest':arena['fastest']}
        generated=client.post('/api/generate',json={'size':5,'seed':42,'timeout':5}).raise_for_status().json()
        assert generated['unique']
        records['generation']={k:generated[k] for k in ('unique','difficulty','wall_time_ms')}
        for filename in ('ablation.png','repair-vs-random.png','difficulty-effort.png','generation.csv'):
            assert client.get('/api/results/'+filename).status_code==200
        assert client.post('/api/check',json={'puzzle':chosen['puzzle'],'entries':{'1,1':True}}).status_code==422
    response=httpx.get('http://127.0.0.1:5173/',timeout=5)
    assert response.status_code==200 and 'Kakuro AI Lab' in response.text
    records['frontend_http_status']=response.status_code
    records['browser_visual_qa']='unverified: Computer Use stopped at Windows URL safety detection'
    path=Path(__file__).resolve().parents[1]/'results/live-smoke.json'
    path.write_text(json.dumps(records,indent=2),encoding='utf-8')
    print(json.dumps(records,indent=2))


if __name__=='__main__':
    smoke()
