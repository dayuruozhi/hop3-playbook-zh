from pathlib import Path
import json, hashlib
ROOT=Path(__file__).resolve().parent.parent
E=ROOT/'evidence'
def read(p): return json.loads(p.read_text())
launches=read(E/'agent-launches.json')
assert len(launches)==3
assert len({a['agent_name'] for a in launches})==3
assert all(a['fork_turns']=='none' for a in launches)
marker=read(E/'parent-canary.json')['marker']
articles=read(ROOT/'work/articles.json')
results=[]
fields={'核心判断','原文依据','可取之处','关键缺口','待核实问题','处理建议'}
for n,(launch,article) in enumerate(zip(launches,articles),1):
    packet_path=E/f'writer-{n}-packet.json'
    packet=read(packet_path)
    assert hashlib.sha256(packet_path.read_bytes()).hexdigest()==launch['packet_sha256']
    assert packet['当前文章']==article
    assert marker not in packet_path.read_text()
    pending=read(E/f'child-{n}-pending.json')
    assert set(pending['context']['inputs'])=={'article','rubric'}
    child=read(E/f'child-{n}-result.json')
    assert child['status']=='completed'
    payload=read(ROOT/f'reports/article-{n}.json')
    report=payload['report']
    assert fields<=report.keys()
    assert len(report['原文依据'])>=2
    assert all(q['引文'] in article['正文'] and q['解读'].strip() for q in report['原文依据'])
    assert child['outputs']['report']==report
    audit=read(E/f'writer-{n}-context-audit.json')
    assert audit['父会话校验标记']=='未提供'
    assert marker not in json.dumps(audit,ensure_ascii=False)
    results.append(dict(article_id=article['编号'],agent_name=launch['agent_name'],child_instance=pending['instance_id'],quote_count=len(report['原文依据']),report_characters=len(json.dumps(report,ensure_ascii=False)),audit=audit))
clarification=read(E/'writer-2-audit-clarification.json')
assert results[1]['audit']['是否继承父对话历史'] is True
assert clarification['clarified_value'] is False
results[1]['audit_clarification']=clarification
parent=read(E/'parent-pending.json')
assert parent['status']=='completed'
final=read(E/'final-vars.json')
variables=final.get('variables',final.get('vars',{}))
assert variables['reviews']==[read(ROOT/f'reports/article-{n}.json')['report'] for n in range(1,4)]
summary=dict(parent_status=parent['status'],parent_instance=parent['instance_id'],writers=results,collection_count=len(variables['reviews']),scope='真实引擎与宿主工具集成实测；结构和引文检查，不是质量优劣基准。')
(E/'verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
