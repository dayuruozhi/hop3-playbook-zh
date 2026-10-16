"""用真实引擎录制中文受控演示。样稿和质量判定由作者提供，不调用模型接口。"""
from pathlib import Path
import sys,json,os,subprocess,datetime,hashlib
根目录=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(根目录/'src'))
from 内容 import 稿件,完整报告,漏项报告,套话报告,质量说明,套话退回原因
工作区=根目录/'示例'
引擎=Path(os.environ.get('HOP_CLI','../hop3/dist/cli.js')).resolve()
环境=dict(os.environ,HOPJIT_SKIP_SKILL='1')
(工作区/'稿件.json').write_text(json.dumps(稿件,ensure_ascii=False,indent=2)+'\n')
记录=[]
def 执行(说明,*参数,提交内容=None,当前稿件=None):
    命令=['node',str(引擎),*参数,'--json']
    进程=subprocess.run(命令,cwd=工作区,env=环境,text=True,capture_output=True,check=True)
    返回=json.loads(进程.stdout)
    条目={'说明':说明,'命令':命令,'返回原文':进程.stdout,'错误输出':进程.stderr,'返回':返回}
    if 提交内容 is not None:条目['提交内容']=提交内容
    if 当前稿件 is not None:条目['当前稿件']=当前稿件
    记录.append(条目)
    print(说明,返回.get('status'),返回.get('step_id'),flush=True)
    assert 返回.get('status')!='error',返回
    return 返回
执行('检查中文任务规约是否有效','validate','逐篇审查.md')
返回=执行('开始逐篇审查','run','逐篇审查.md','--workspace',str(工作区),'--params',json.dumps({'稿件路径':'稿件.json'},ensure_ascii=False))
已送漏项=False
已送套话=False
已退套话=False
while 返回.get('status') not in ['completed','failed']:
    assert 返回['status']=='step_ready',返回
    当前=返回['context']['inputs']['当前稿件']
    序号=int(当前['编号'])-1
    步骤=返回['step_id']
    if 步骤=='2.1.1':
        if 序号==2 and not 已送漏项:
            提交={'本篇报告':漏项报告};已送漏项=True;说明='第三篇：刻意提交漏项的简短报告'
        elif 序号==3 and not 已送套话:
            提交={'本篇报告':套话报告};已送套话=True;说明='第四篇：提交栏目齐全但空泛的报告'
        else:
            提交={'本篇报告':完整报告[序号]};说明=f'第{序号+1}篇：提交'+('补写后的完整报告' if 序号>=2 else '完整报告')
    elif 步骤=='2.1.3':
        if 序号==3 and not 已退套话:
            提交={'质量通过':False,'质量说明':套话退回原因};已退套话=True;说明='第四篇：作者判定分析空泛，提交不通过'
        else:
            提交={'质量通过':True,'质量说明':质量说明[序号]};说明=f'第{序号+1}篇：作者提交质量通过判定'
    else:raise AssertionError(返回)
    输出路径=Path(返回['output_path']);输出路径.parent.mkdir(parents=True,exist_ok=True)
    输出路径.write_text(json.dumps(提交,ensure_ascii=False,indent=2))
    返回=执行(说明,'submit_and_fetch_next',步骤,'--instance',返回['instance_id'],'--output','@'+str(输出路径),提交内容=提交,当前稿件=当前)
    assert len(记录)<20
assert 返回['status']=='completed',返回
实例=返回['instance_id']
执行('查询任务完成状态','status','--instance',实例)
变量=执行('读取最终保存的四份报告','vars','--instance',实例)
assert 变量['variables']['报告合集']==完整报告
状态=json.loads((工作区/'.hopstate'/实例/'state.json').read_text())
assert len(状态['retry_history']['2.1'])==2
for 文件名,内容 in [('录制.json',记录),('状态.json',状态),('说明.json',{'录制时间':datetime.datetime.now(datetime.timezone.utc).isoformat(),'引擎版本':'0.20.0','引擎提交':subprocess.check_output(['git','rev-parse','HEAD'],cwd=引擎.parent.parent,text=True).strip(),'实例编号':实例,'方法':'作者提供中文稿件、审查样稿和质量判定，真实引擎负责栏目检查、逐篇推进、重试、反馈与保存；未运行自主模型对比或独立审查智能体。','规约校验值':hashlib.sha256((工作区/'逐篇审查.md').read_bytes()).hexdigest()})]:
    (根目录/'证据'/文件名).write_text(json.dumps(内容,ensure_ascii=False,indent=2)+'\n')
print('中文录制完成，共',len(记录),'次命令交互。')
