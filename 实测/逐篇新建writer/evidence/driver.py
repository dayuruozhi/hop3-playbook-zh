"""本次实测的显式驱动。agent 的真实启动由主会话调用 harness 的 spawn_agent 完成。"""
from pathlib import Path
import json,os,subprocess,shlex,sys
ROOT=Path(__file__).resolve().parent.parent
WORK=ROOT/'work';EVIDENCE=ROOT/'evidence';CLI=Path('/home/ec2-user/projects/hop3/dist/cli.js')
RUBRIC='逐篇审查。六项栏目：核心判断、原文依据、可取之处、关键缺口、待核实问题、处理建议。原文依据至少两条，每条含原样引文和针对引文支持范围的解读。其他栏目为具体文字。判断要区分关联与因果，针对本篇的数据、方法和信息缺失提出追问，建议与现有证据相称。不得补造事实，不使用其他文章或审查报告。'
def cli(label,args):
 p=subprocess.run(['node',str(CLI),*args,'--json'],cwd=WORK,env=dict(os.environ,HOPJIT_SKIP_SKILL='1'),capture_output=True,text=True,check=True)
 r=json.loads(p.stdout)
 assert r.get('status')!='error',r
 append({'label':label,'args':args+['--json'],'response':r,'stdout':p.stdout,'stderr':p.stderr})
 return r
def generated(label,command):
 # 引擎提供的协议命令不作改写，按 shell 规则拆成 argv 后执行。
 args=shlex.split(command)
 p=subprocess.run(args,cwd=WORK,env=dict(os.environ,HOPJIT_SKIP_SKILL='1'),capture_output=True,text=True,check=True)
 r=json.loads(p.stdout);assert r.get('status')!='error',r
 append({'label':label,'generated_command':command,'response':r,'stdout':p.stdout,'stderr':p.stderr})
 return r
def append(event):
 path=EVIDENCE/'engine.jsonl'
 with path.open('a') as f:f.write(json.dumps(event,ensure_ascii=False)+'\n')
def save(name,value):(EVIDENCE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def start():
 for name in ['batch.md','review-one.md']:
  result=cli('validate '+name,['validate',name]);assert not result['errors'] and not result['warnings'],result
 r=cli('start parent',['run','batch.md','--workspace',str(WORK),'--params',json.dumps({'source_path':'articles.json','rubric':RUBRIC},ensure_ascii=False)])
 save('parent-pending.json',r);print(json.dumps(r,ensure_ascii=False,indent=2))
def prepare(number):
 parent=json.loads((EVIDENCE/'parent-pending.json').read_text())
 assert parent['status']=='step_ready' and parent['step_type']=='call',parent
 save(f'call-{number}.json',parent)
 protocol=parent['call_protocol']
 init=generated('initialize child '+str(number),protocol['init_command'])
 child=generated('advance child '+str(number),protocol['child_advance'])
 save(f'child-{number}-pending.json',child)
 assert child['status']=='step_ready' and child['step_id']=='1.1',child
 article=child['context']['inputs']['article']
 assert article['编号']==f'{number:02}',article
 # 交给新 writer 的唯一业务输入包，不含父实例上下文和前文报告。
 packet={'当前文章':article,'完整标准':child['context']['inputs']['rubric'],'当前指令':child['context']['instruction'],'输出结构':child['context']['output_schema'],'输出路径':child['output_path'],'上下文核对路径':str(Path(child['work_zone'])/'writer-context-audit.json')}
 save(f'writer-{number}-packet.json',packet)
 print(json.dumps({'number':number,'packet':str(EVIDENCE/f'writer-{number}-packet.json'),'article_id':article['编号'],'child_instance':child['instance_id'],'output_path':child['output_path']},ensure_ascii=False,indent=2))
def collect(number):
 child=json.loads((EVIDENCE/f'child-{number}-pending.json').read_text())
 protocol=json.loads((EVIDENCE/f'call-{number}.json').read_text())['call_protocol']
 path=Path(child['output_path']);payload=json.loads(path.read_text())
 (ROOT/'reports'/f'article-{number}.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
 r=cli('submit writer '+str(number),['submit_and_fetch_next',child['step_id'],'--state-dir',protocol['child_state_dir'],'--instance',child['instance_id'],'--output','@'+str(path)])
 save(f'child-{number}-result.json',r)
 if r['status']!='completed':print(json.dumps(r,ensure_ascii=False,indent=2));return
 parent=generated('collect child '+str(number),protocol['report_completed'])
 save('parent-pending.json',parent)
 print(json.dumps({'child_status':r['status'],'parent_status':parent['status'],'next_article':parent.get('context',{}).get('inputs',{}).get('article')},ensure_ascii=False,indent=2))
 if parent['status']=='completed':
  vars=cli('inspect final collection',['vars','--instance',parent['instance_id']]);save('final-vars.json',vars)
if __name__=='__main__':
 if sys.argv[1]=='start':start()
 elif sys.argv[1]=='prepare':prepare(int(sys.argv[2]))
 elif sys.argv[1]=='collect':collect(int(sys.argv[2]))
