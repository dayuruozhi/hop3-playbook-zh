"""构建中文审稿手册。文案、数据、规约与操作笔记均为中文重新编写。"""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
from urllib.parse import quote
import json,sys,subprocess,shlex,zipfile,hashlib,re,os
根目录=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(根目录/'src'))
from 内容 import 稿件,完整报告,漏项报告,套话报告,质量说明,套话退回原因,栏目
from 普通答复 import 答复开场,答复结尾,答复报告,批注,完整答复文本
记录=json.loads((根目录/'证据/录制.json').read_text())
状态=json.loads((根目录/'证据/状态.json').read_text())
来源=json.loads((根目录/'证据/说明.json').read_text())
发布目录=根目录/'docs'
发布目录.mkdir(exist_ok=True)
规约=(根目录/'示例/逐篇审查.md').read_text()
assert len(记录)==15
assert 记录[0]['返回']=={'status':'ok','errors':[],'warnings':[]}
assert 记录[-1]['返回']['variables']['报告合集']==完整报告
assert len(状态['retry_history']['2.1'])==2
assert sum(x['event']=='step_start' and x['step_id']=='2.1.1' for x in 状态['exec_events'])==6
assert sum(x['event']=='step_start' and x['step_id']=='2.1.3' for x in 状态['exec_events'])==5
assert hashlib.sha256(规约.encode()).hexdigest()==来源['规约校验值']
for 文章,报告 in zip(稿件,完整报告):
 assert list(报告)==栏目
 for 依据 in 报告['原文依据']:assert 依据['引文'] in 文章['正文']
漏项返回=记录[6]['返回'];套话返回=记录[10]['返回']
assert 漏项返回['step_id']==套话返回['step_id']=='2.1.1'
assert 漏项返回['context']['inputs']['当前稿件']['编号']=='03'
assert 套话返回['context']['inputs']['当前稿件']['编号']=='04'
assert 记录[9]['返回']['step_id']=='2.1.3'
assert 记录[10]['提交内容']['质量通过'] is False

def 转义(值):return escape(str(值),quote=True)
def 代码(内容,类名=''):return '<pre class="'+类名+'"><code>'+转义(内容)+'</code></pre>'
def 折叠(标题,正文,类名=''):return '<details class="'+类名+'"><summary>'+转义(标题)+'</summary><div class="折叠内容">'+正文+'</div></details>'
def 章节(锚点,编号,眉题,标题,正文):return f'<section class="章节" id="{锚点}" aria-labelledby="{锚点}-标题"><div class="章节头"><span class="章节号">{编号}</span><div><p class="眉题">{眉题}</p><h2 id="{锚点}-标题" tabindex="-1">{标题}</h2></div></div>{正文}</section>'
assert [len(报告) for 报告 in 答复报告]==[6,6,2,6]
assert len(批注)==8 and [项['号'] for 项 in 批注]==list(range(1,9))
assert 答复报告[:2]==完整报告[:2]
资料={}
def 出处(路径,标题):
 资料[路径]=标题
 return '<a class="出处" href="https://github.com/hoplogic/hop3/blob/'+来源['引擎提交']+'/'+quote(路径)+'">'+标题+'</a>'
def 呈现报告(报告):
 内容=''
 for 名称 in 栏目:
  if 名称 not in 报告:continue
  if 名称=='原文依据':文本=''.join('<blockquote>“'+转义(项['引文'])+'”</blockquote><p class="引文解读">'+转义(项['解读'])+'</p>' for 项 in 报告[名称])
  else:文本='<p>'+转义(报告[名称])+'</p>'
  内容+='<div class="报告栏目" data-field="'+名称+'"><h4>'+名称+'</h4>'+文本+'</div>'
 return 内容

def 单元(标签,文本,类别='',复制名='内容'):
 换行='可换行' in 类别.split()
 return '<div class="单元"><p class="单元名">'+标签+'</p><div class="代码块">'+代码(文本,类别)+'<div class="代码操作 需脚本"><button type="button" class="复制">复制'+复制名+'</button><button type="button" class="展开代码" data-name="'+复制名+'" hidden>展开'+复制名+'</button><button type="button" class="换行按钮" aria-pressed="'+str(换行).lower()+'">'+('保留原行' if 换行 else '自动换行')+'</button></div></div></div>'
请求='''/hop 请逐篇审查这个文件夹里的稿件，按同一套标准交付报告：

一、核心判断：文章要证明什么，或建议做什么。
二、原文依据：至少两条原样引文，每条解释支持范围。
三、可取之处：具体写出成立或有价值的部分。
四、关键缺口：指出论证、数据和因果判断的问题。
五、待核实问题：提出能回应这些缺口的具体追问。
六、处理建议：说明当前证据支持怎样处理。

每篇都先检查栏目和引文，再判断分析是否具体。
出现漏项或套话时，在约定次数内退回本篇补写。
先和我确认任务规约、检查标准及重试上限，再开始。
保留原稿不动，最后列出哪些通过、哪些仍需人工处理。'''
页面='''<a class="跳过" href="#正文">跳到正文</a><header class="顶栏"><a class="品牌" href="#开头"><span class="品牌字">HOP 3</span><span>逐篇审稿 · 中文实战手册</span></a><nav class="导航" aria-label="页内导航"><a href="#普通答复">读完整答复</a><a href="#试跑">照着试一次</a><a href="#笔记">操作笔记</a><a href="https://github.com/hoplogic/hop3">HOP3 项目</a><label class="仅辅助" for="主题">页面配色</label><select id="主题" class="主题"><option value="system">随系统</option><option value="light">浅色</option><option value="dark">深色</option></select></nav></header><main id="正文"><section class="首屏" id="开头" aria-labelledby="开头-标题"><div><p class="眉题">把一批稿件交给 AI，怎样让审查标准贯穿始终</p><h1 id="开头-标题" tabindex="-1">第一篇认真审，<br>后面几篇也得认真审。</h1><p class="导语">你要的是逐篇、有依据的审查。交到后面的报告，却只剩“内容清晰，建议完善”。</p><p>这份手册用四篇中文稿件，演示 HOP 如何按约定逐篇检查、退回不合格报告，并留下可追查的记录。</p><div class="首屏链接"><a class="主按钮" href="#普通答复">先读普通智能体的完整答复</a><a href="#对照">再看 HOP 如何检查和退回</a></div></div><aside class="清单卡" aria-label="本次演示的最终交付清单"><p class="眉题">交付前复核</p><h3>四篇稿件，一套标准</h3><div class="清单行"><span><span class="序号">01</span>微课培训</span><span class="标记 通过">完整通过</span></div><div class="清单行"><span><span class="序号">02</span>会议室预约</span><span class="标记 通过">完整通过</span></div><div class="清单行"><span><span class="序号">03</span>客服分流</span><span class="标记 退回">漏项后补写</span></div><div class="清单行"><span><span class="序号">04</span>例会压缩</span><span class="标记 退回">套话后补写</span></div><p class="小字">本页使用虚构稿件与作者提供的样稿、质量判定。检查执行、重试与保存由真实引擎完成。<a href="#笔记">查看录制方式</a></p></aside></section><div class="来由"><blockquote>“前面按我要求详细审查，后面就改成每篇简单几行字。”</blockquote><p class="小字">来自这次对话中描述的使用经历。本例把批次缩小为四篇，重点看标准怎样落实，不以篇数或页数展示能力。</p></div>'''
内容='<p class="引言">假设你负责复核一批经验分享稿。你要知道文章的结论是否站得住、还缺什么依据，以及现在是否适合推广。先把“认真审”写成能逐项核对的要求。</p><div class="约定"><p class="眉题">交给 AI 的工作约定</p><p>每篇单独出一份报告，六项内容都要有。至少摘出两处原文，说清它们能支持什么、不能支持什么。原文没有的信息，列为待核实问题。</p><p class="小字">本页的“通过”表示本次演示按规定完成了检查；它不等于对文章事实或审查判断作出保证。</p></div><div class="框架">'
说明=['说明文章的主张和推论，避免只复述题目。','原样引用，逐条分析证据的支持范围。','说明哪些信息确实有价值，或便于核查。','指出具体缺少什么，结论是否走得太远。','围绕缺口提出下一步能查的问题。','说明可直接采用、补证重审，还是暂缓。']
for 名称,解释 in zip(栏目,说明):内容+='<div><h3>'+名称+'</h3><p>'+解释+'</p></div>'
内容+='</div><p class="批注">写得长不一定审得深。六个标题也可能全是套话，所以本例把“栏目与引文核对”和“分析质量判断”分成两道检查。</p>'
页面+=章节('约定','01','先约定怎样才算完成','把“认真审”落到六项要求。',内容)
def 标注(文字,号):
 return '<mark class="问题高亮" id="问题-'+str(号)+'">'+转义(文字)+'</mark><a class="批注号" href="#批注-'+str(号)+'" aria-label="查看批注'+str(号)+'">'+str(号)+'</a>'
答复='<p class="引言">先看一轮完整答复，才容易发现标准是从哪里开始变的。下面保留四篇报告的连续顺序：前两篇逐项展开，第三篇突然变短，第四篇保留标题却换成套话。</p><p class="说明条" id="普通答复-来源">这是作者根据对话中描述的问题构造的普通智能体答复示意，不是某个模型的实测输出，也不表示普通智能体都会这样回答。它与 HOP 受控录制使用同一组稿件和问题样稿。</p><div class="答复工具"><a href="#连贯答复-3">直接看第三篇怎样缩水</a><a href="#连贯答复-4">看第四篇的套话</a><button type="button" class="切换批注 需脚本" aria-pressed="true">隐藏批注，先读原答复</button><button type="button" class="复制整答 需脚本">复制完整示意答复</button></div><div class="答复版面"><div class="聊天答复" aria-label="普通智能体完整答复示意"><div class="答复身份"><span>普通智能体可能交来的答复</span><small>完整一轮 · 作者构造的示意</small></div><div class="答复正文"><p class="答复开场">'+转义(答复开场)+'</p>'
for 序号,(文章,报告) in enumerate(zip(稿件,答复报告),1):
 标题='第'+str(序号)+'篇｜'+文章['标题']
 答复+='<section class="普通篇目" id="连贯答复-'+str(序号)+'" aria-labelledby="连贯答复-'+str(序号)+'-标题"><h3 id="连贯答复-'+str(序号)+'-标题" tabindex="-1">'+(标注(标题,1) if 序号==3 else 转义(标题))+'</h3>'
 for 名称 in 栏目:
  if 名称 not in 报告:continue
  答复+='<div class="普通栏目"><h4>'+名称+'</h4>'
  if 名称=='原文依据':
   for 项号,依据 in enumerate(报告[名称]):
    答复+='<blockquote>“'+转义(依据['引文'])+'”</blockquote><p class="普通解读">'+(标注(依据['解读'],3) if 序号==4 and 项号==0 else 转义(依据['解读']))+'</p>'
  else:
   标记=2 if 序号==3 and 名称=='核心判断' else {'可取之处':4,'关键缺口':5,'待核实问题':6,'处理建议':7}.get(名称) if 序号==4 else None
   答复+='<p>'+(标注(报告[名称],标记) if 标记 else 转义(报告[名称]))+'</p>'
  答复+='</div>'
 答复+='</section>'
答复+='<p class="答复结尾">'+标注(答复结尾,8)+'</p></div></div><aside class="审读批注" aria-label="这份答复哪里没有达标"><div class="批注开头"><p class="眉题">读完后对照这些地方</p><h3>问题不只是篇幅变短</h3><p class="小字">浅色高亮和编号是本手册加的审读批注，不属于示意答复。隐藏批注后仍能读到完整原答复。</p></div>'
for 项 in 批注:
 号=项['号']
 答复+='<section class="批注卡" id="批注-'+str(号)+'" aria-labelledby="批注-'+str(号)+'-标题"><h4 id="批注-'+str(号)+'-标题" tabindex="-1"><span>'+str(号)+'</span>'+项['标题']+'</h4><p>'+项['说明']+'</p><p class="小字">违反的要求：'+项['要求']+'</p><div class="批注链接"><a href="#问题-'+str(号)+'">回到答复中的位置</a>'
 if 项['原文篇']:答复+='<a href="#稿件-'+str(项['原文篇'])+'">对照原稿与 HOP 检查</a>'
 答复+='</div></section>'
答复+='</aside></div><div class="小结"><h3>“四篇都写了”与“四篇都按标准完成”是两件事</h3><p>这份答复没有遗漏文章编号，却在后面省掉了工作：第三篇缺四项，第四篇的引文和标题仍在，分析已经空泛。接下来看 HOP 怎样处理同样的问题样稿。</p><p><a href="#对照">查看对应的 HOP 检查与补写</a></p></div>'
页面+=章节('普通答复','02','先读完整答复，再对照问题','普通智能体交来的整批答复，可能长什么样？',答复)
内容='<p class="引言">第三篇缺栏目，第四篇不缺栏目却缺分析。先读问题样稿，再看它在哪道检查被退回。点击“看补写稿”可查看之后提交的完整报告。</p><p class="说明条">这不是两种模型的跑分对比。问题样稿由作者刻意构造，质量判定也由作者提供；本页分别标明程序检查和判断性检查各自做了什么。</p><div class="选稿 需脚本" role="group" aria-label="选择要查看的稿件">'
for 序号,短题 in enumerate(['微课培训','会议室预约','客服分流','例会压缩']):内容+=f'<button type="button" data-article="{序号}" aria-pressed="{str(序号==2).lower()}"><span>第 {序号+1:02} 篇</span>{短题}</button>'
内容+='</div>'
for 序号,(文章,完整) in enumerate(zip(稿件,完整报告)):
 问题稿=漏项报告 if 序号==2 else 套话报告 if 序号==3 else 完整
 内容+=f'<article class="稿件区" id="稿件-{序号+1}" aria-labelledby="稿件-{序号+1}-标题" data-panel="{序号}"><p class="眉题 无脚本标题">第 {序号+1} 篇</p><h3 id="稿件-{序号+1}-标题" tabindex="-1">{文章["标题"]}</h3>'
 if 序号==2:内容+='<blockquote class="摘录"><p>“试行期间，排班工时增加了两成。”<br>“重新打开的工单未纳入本次统计。”</p><p class="小字">如果报告没有讨论这些信息，你能接受“建议直接推广”吗？</p></blockquote>'
 if 序号==3:内容+='<blockquote class="摘录"><p>“二十四名成员中有十四人填写问卷，其中十一人认为新安排更好。”<br>“试行恰逢项目收尾后的空档期。”</p><p class="小字">填答者觉得更好，足以证明团队产出提高了吗？</p></blockquote>'
 内容+=折叠('先读这篇虚构原稿','<p class="原稿正文">'+文章['正文']+'</p>')+'<div class="对照"><section><div class="栏头"><p class="眉题">交来的报告</p><h3>'+('第一稿看上去已经写完' if 序号>=2 else '按约定完成的样稿')+'</h3><p class="小字">作者提供的演示内容，用来检查流程。</p></div><div class="状态条">'+('只有两项内容' if 序号==2 else '六个栏目齐全，分析仍然空泛' if 序号==3 else '栏目、依据与具体分析都有')+'</div><div class="栏身">'
 内容+=呈现报告(问题稿) if 序号>=2 else 折叠('阅读完整报告',呈现报告(问题稿))
 if 序号==2:内容+='<p class="小字 退回">缺少原文依据、可取之处、关键缺口、待核实问题。看起来有结论，却没有完成约定的审查。</p>'
 if 序号==3:内容+='<p class="小字 退回">“有实践价值”“进一步完善”没有回应本篇的统计口径和推论问题。引文能找到，不代表解读到位。</p>'
 内容+='</div></section><section><div class="栏头"><p class="眉题">按 HOP 任务规约验收</p><h3>'+('先过栏目关，再过分析关' if 序号>=2 else '通过两道检查后收集')+'</h3><p class="小字">本次规约规定每篇最多重试一次。</p></div>'
 if 序号>=2:
  内容+=f'<div class="退回态" data-reject="{序号}"><div class="状态条 不通过">'+('程序检查未通过：退回第三篇补写' if 序号==2 else '栏目检查通过；作者提交质量不通过判定')+'</div><div class="栏身"><ul class="核对单">'
  for 名称 in 栏目:内容+='<li><span>'+名称+'</span><small class="'+('通过' if 名称 in 问题稿 else '退回')+'">'+('已有' if 名称 in 问题稿 else '缺少')+'</small></li>'
  内容+='</ul>'
  if 序号==2:
   反馈=漏项返回['context']['retry_feedback']
   内容+='<div class="反馈"><p class="眉题">引擎实际返回的补写提示</p><p>'+转义(反馈)+'</p></div><p>本次代码检查发现漏项，把写作任务重新交回第三篇。它还没有进入分析质量判断。</p>'
  else:
   反馈=套话返回['context']['retry_feedback']
   内容+='<p>代码能确认栏目齐全、引文存在，不能由此认定分析合格。演示中，作者扮演审查方，提交了“不通过”及以下原因。</p><div class="反馈"><p class="眉题">作者给出的判定，经引擎回传</p><p>'+转义(反馈)+'</p></div><p>引擎据此退回第四篇重写。识别套话的判断来自作者，重试和反馈传递由引擎执行。</p>'
  内容+=f'<div class="补写操作 需脚本"><button type="button" class="补写按钮" data-repair="{序号}">看补写后的完整报告</button></div></div></div><div class="补写态" data-fixed="{序号}"><div class="状态条 已通过">补写稿通过栏目核对，作者提交质量通过判定</div><div class="栏身"><p class="小字">以下是作者在重试时提交的完整样稿。最终收集的是这份报告。</p>'+呈现报告(完整)+f'<div class="补写操作 需脚本"><button type="button" data-back="{序号}">回看问题稿怎样被退回</button></div></div></div>'
 else:
  内容+='<div class="状态条 已通过">栏目核对通过，作者提交质量通过判定</div><div class="栏身"><p>程序核对了六项内容和原文引文，随后收到作者提供的质量通过判定。本篇报告被加入合集。</p>'+折叠('阅读收集的报告',呈现报告(完整))+'</div>'
 内容+='</section></div></article>'
内容+='<div class="小结"><h3>差别体现在不合格报告出现以后</h3><p>流程没有把“交来一段文字”当作完成。第三篇补齐漏项，第四篇重写空泛分析，之后才进入最终合集。实际结果是四份完整报告、六次写作提交、两次重试。</p></div>'
页面+=章节('对照','03','看清两种不合格','漏项能查，<br class="手机换行">套话还得判断。',内容)
内容='<p class="引言">你仍然负责提出标准、确认任务和抽查结果。HOP 将逐篇顺序、检查节点和重试范围写进规约，再由引擎按规约推进。</p><div class="流程">'
for 号,题,文 in [('一','取出一篇','引擎从给定清单取当前稿件，给它同一份审查要求。'),('二','提交报告','写作方按六项框架写报告，不凭印象宣布整批完成。'),('三','逐项检查','程序查栏目和引文；审查方判断分析是否具体。'),('四','收集或退回','通过后收集；未通过则在次数限制内退回本篇。')]:内容+='<div><p class="眉题">'+号+'</p><h3>'+题+'</h3><p>'+文+'</p></div>'
内容+='</div><p class="批注">写报告和查报告必须放进同一个可重试单元。只重复检查，原报告不会自动变好。本例两次重试都重新发出了写报告的任务。</p><p class="小字">本次成功录制没有走到“重试仍失败”的分支。实际使用时应保留未通过状态，交给人工处理，不应为凑齐交付而降低标准。'+出处('docs/tutorials/03-探索与提交.md','参阅：探索、检查与重试')+'</p><div class="边界"><div><h3>清单也要核对</h3><p>引擎遍历的是你提供的清单。原始清单少一篇，它不会凭空知道。开始前核对篇数和文件，交付时核对报告对应关系。</p></div><div><h3>检查通过也要抽查</h3><p>栏目全、引文对，只能说明基础要求满足。判断性检查也可能出错，重要稿件仍应有人复核分析与建议。</p></div></div>'
页面+=章节('流程','04','理解谁负责什么','把标准带到每一篇。',内容)
内容='<p class="引言">先选少量你读过的文章，把“什么算审到位”说清楚，再看后面的报告能否保持同一标准。</p><ol class="步骤清单"><li><h3>准备原稿和一份你认可的样稿</h3><p>说明材料在哪、每篇报告要解决什么问题，哪些情况必须写“待核实”。别只要求“认真”“详细”。</p></li><li><h3>把下面的任务说明交给 AI</h3><div class="约定"><p class="眉题">可复制后按自己的任务修改</p><pre class="请求文本">'+转义(请求)+'</pre><button type="button" class="复制 需脚本 行内">复制任务说明</button></div><p class="小字">在 Codex 中使用 <code>$hop</code>。这里的自然语言请求是使用建议，操作笔记录制走的是命令行，没有录制 /hop 自主执行全过程。</p></li><li><h3>先看规约，再让它跑</h3><p>确认原稿清单、六项要求、两道检查和重试上限。若任务需要修改或发布原稿，另外审查相应动作和授权；本例只做审查。</p></li><li><h3>验收时看后面的稿件</h3><p>抽查一篇靠后的报告，追问：引文解释了什么？缺口针对本篇吗？建议与证据相称吗？还剩哪些失败或未处理项？</p></li></ol>'
安装='<p>需要 Node.js 20 或更新版本，以及 Claude Code、Codex 或 opencode。执行后新开一个智能体会话。</p>'+单元('在终端执行','npm install -g @hoplogic/hopjit\nhopjit setup','可换行 命令内容','安装命令')+'<p class="小字">'+出处('README.md','项目安装说明')+' · '+出处('package.json','运行版本要求')+'</p>'
内容+=折叠('还没安装 HOP？先做这一步',安装)+'<div class="约定"><h3>也可以先跑本页的中文示例</h3><p>压缩包内有四篇虚构稿件、已验证的中文任务规约和中文说明。解压后，在该目录让智能体运行规约。</p><a class="主按钮" href="'+quote('审稿示例.zip')+'">下载中文示例</a>'+单元('对智能体说','/hop 运行「逐篇审查.md」，把稿件路径设为「稿件.json」。','可换行','运行说明')+'<p class="小字">真实使用时，模型会自行生成报告和判定，可能与本页受控样稿不同。本示例不修改原稿、不发消息，也不调用外部资料服务。</p></div>'
页面+=章节('试跑','05','把方法用到自己的任务','先跑一小批，再看后面的质量。',内容)
内容='<p class="引言">下面按笔记单元保留“为什么做 → 执行什么 → 提交了什么 → 返回什么 → 怎样理解”。你可以直接跳到两次退回，也可以顺着看完整过程。</p><p class="说明条">本页重新录制了中文任务规约。版本为 hopjit 0.20.0。四篇稿件、报告样稿和五次质量判定由作者提供；引擎真实执行栏目核对、逐篇推进、重试和保存。没有运行模型能力对比，也没有独立审查智能体。</p><div class="笔记摘要"><span>最终收集 4 份报告</span><span>6 次写作提交</span><span>2 次退回重试</span><span>15 次命令交互</span></div>'
笔记='<p>这里的 15 次交互包括启动、提交报告、提交质量判定和查询结果，不是审查了 15 篇文章。代码单元保留当时的命令，路径属于录制环境。</p><p class="小字"><code>step_ready</code> 表示等待下一步结果；<code>step_id</code> 是规约中的步骤号，同一步骤会用于不同文章；<code>$file</code> 表示内容保存在指向的文件中。普通使用者一般由智能体代为执行这些命令。</p><div class="笔记链接"><a href="#交互-7">跳到第三篇漏项</a><a href="#交互-11">跳到第四篇套话</a><a href="#交互-15">查看最终合集</a></div>'
for 号,事件 in enumerate(记录,1):
 返回=事件['返回'];提交=事件.get('提交内容');文章=事件.get('当前稿件');反馈=返回.get('context',{}).get('retry_feedback')
 if 号==1:
  目的='先检查中文规约的结构是否有效，避免带着不合法的任务计划开始。';解释='返回 ok，错误和警告列表都为空。这里检查的是规约结构，还没有开始审稿。'
 elif 号==2:
  目的='把四篇稿件的文件路径交给规约，启动这一批审查。';解释='引擎读取清单后，给出第一篇的写作任务。step_ready 是要求写作方提交结果，不表示文章已经审完。'
 elif 提交 and '本篇报告' in 提交:
  if 提交['本篇报告']==漏项报告:
   目的='刻意给第三篇提交只有核心判断和处理建议的报告，观察漏项会怎样处理。';解释='程序核对失败。引擎返回的仍是第三篇的写作任务，并附缺项提示。它没有把本篇当成通过，也没有直接推进到下一篇。'
  elif 提交['本篇报告']==套话报告:
   目的='给第四篇提交栏目齐全、有真实引文却分析空泛的样稿，观察程序核对的边界。';解释='栏目与引文检查通过，引擎转到分析质量判断。这证明格式检查能够放行一份空泛报告，不能代替实质审查。'
  else:
   目的='向第'+str(int(文章['编号']))+'篇的写作任务提交作者编写的完整报告。'+('这次提交用于替换前一次未通过的样稿。' if int(文章['编号'])>=3 else '')
   解释='程序核对已通过，引擎请求质量判定。报告是否有针对性的分析，需要在下一次交互作出判断。'
 elif 提交:
  if 提交['质量通过'] is False:
   目的='作者扮演审查方，明确指出第四篇的分析只有套话，并提交不通过判定。';解释='引擎按照不通过判定触发重试，再次发出第四篇的写作任务，并带上具体补写原因。识别空泛分析的判断来自作者，重试由引擎执行。'
  elif 返回['status']=='completed':
   目的='作者对第四篇补写稿提交质量通过判定。';解释='最后一篇通过后，任务完成。outputs 中的报告合集是一个文件引用，完整内容在第 15 次交互中读取。'
  else:
   下一篇=返回['context']['inputs']['当前稿件']['编号']
   目的='作者对第'+str(int(文章['编号']))+'篇提交质量通过判定。';解释='本篇通过后被收集，引擎请求第'+str(int(下一篇))+'篇的写作任务。下一篇仍携带同一套规约和审查要求。'
 elif 号==14:
  目的='查询这一批任务的保存状态，不提交新的报告或判定。';解释='execution_status 为 completed，说明这次任务已完成。完成状态要结合最终保存的内容一起看。'
 else:
  目的='读取保存变量，核实交付清单里究竟是哪四份报告。';解释='variables 中的报告合集包含四份完整报告，顺序对应输入清单；两份问题样稿不在最终合集里。构建时逐项比较了它们与完整样稿，结果一致。'
 条目='<p class="笔记目的">'+目的+'</p>'+单元(f'输入 [{号:02}] · 当时执行的命令',shlex.join(事件['命令']),'可换行 命令内容','命令')
 if 提交:
  条目+='<p class="小字">命令提交的是输出文件。下面保留这一次提交的实际内容，避免后续复用同一路径造成混淆。</p>'+单元('提交的文件内容',json.dumps(提交,ensure_ascii=False,indent=2),'可换行 输入内容','提交内容')
 elif 号<=2:条目+='<p class="小字">输入材料是示例包中的「逐篇审查.md」'+('及「稿件.json」。' if 号==2 else '，可在下方展开查看。')+'</p>'
 else:条目+='<p class="小字">此命令只查询已有实例，没有提交新的审查内容。</p>'
 摘要={键:返回[键] for 键 in ['status','step_id','step_type','summary','execution_status','completed','failed','pending','errors','warnings'] if 键 in 返回}
 上下文=返回.get('context',{})
 if 上下文:
  摘要['context']={}
  下一稿=上下文.get('inputs',{}).get('当前稿件')
  if 下一稿:摘要['context']['inputs']={'当前稿件':{键:下一稿[键] for 键 in ['编号','标题']}}
  if 'retry_feedback' in 上下文:摘要['context']['retry_feedback']=上下文['retry_feedback']
 if 'outputs' in 返回:摘要['outputs']=返回['outputs']
 if 'variables' in 返回:摘要['variables']={'报告合集':[{'核心判断':项['核心判断']} for 项 in 返回['variables']['报告合集']]}
 条目+=单元(f'输出 [{号:02}] · 引擎返回摘录',json.dumps(摘要,ensure_ascii=False,indent=2),'可换行 响应摘录','返回摘录')+'<p class="小字">摘录省略了较长的任务背景和报告细节，保留所示字段的原值。完整返回及原始输出均可在下方展开。</p><div class="解读框"><h4>这次交互说明什么</h4><p>'+解释+'</p></div>'
 if 提交 and '质量通过' in 提交:条目+='<p class="小字">这次质量判定由作者提供，不能据此推断某个模型能稳定识别或修复同类问题。</p>'
 if 反馈:条目+='<div class="反馈"><p class="眉题">请留意返回中的 retry_feedback</p><p>'+转义(反馈)+'</p></div>'
 条目+=折叠('展开完整引擎返回',代码(json.dumps(返回,ensure_ascii=False,indent=2),'完整返回')+折叠('查看未经排版的命令行原始输出',代码(事件['返回原文'],'原始返回')))
 笔记标题={7:"第三篇：提交漏项报告",8:"第三篇：提交补写稿",10:"第四篇：提交套话报告",11:"第四篇：作者判定不通过",12:"第四篇：提交补写稿"}.get(号,事件["说明"])
 笔记+=f'<article class="笔记条目" id="交互-{号}" aria-labelledby="交互-{号}-标题"><h3 id="交互-{号}-标题" tabindex="-1">{号:02}．{转义(笔记标题)}</h3>'+条目+'</article>'
内容+='<div class="笔记入口" id="操作笔记">'+折叠('打开操作笔记：15 次命令、返回与解读',笔记)+'</div>'
内容+='<div id="任务规约">'+折叠('查看本次实跑的中文任务规约','<p class="小字">步骤名、业务变量、报告字段和反馈均使用中文。hop_python 的函数名、类型名及引擎命令保留运行所需的写法。</p>'+单元('任务规约全文',规约,'可换行','规约'))+'</div>'
for 路径,标题 in [('USAGE.md','命令行、状态与运行方式'),('docs/tutorials/05-并行与遍历.md','逐项遍历与结果收集'),('docs/concepts/HopSpec V3语法参考.md','中文关键词及变量语法'),('docs/concepts/HopAnt概念.md','复用模式的信任边界')]:出处(路径,标题)
内容+=折叠('查阅对应版本的项目资料','<p class="小字">以下链接固定到本次录制的仓库版本，避免把后来更新的说明混进本次证据。</p><ul class="资料列表">'+''.join('<li>'+出处(路径,标题)+'</li>' for 路径,标题 in sorted(资料.items()))+'</ul>')
页面+=章节('笔记','06','按笔记读懂实际过程','命令、返回、解释，放在一起看。',内容)
内容='<p class="引言">本次演示证明的是流程怎样执行。真实任务能否审到位，还取决于材料、标准和判断方。</p><div class="边界"><div><h3>模型能力没有做对比实验</h3><p>样稿与判定由作者提供，目的是让两种失败清楚可见。不能从这次受控录制推断普通提示词必然偷懒，或 HOP 一定能提高某个模型的审稿水平。</p></div><div><h3>格式合格不等于内容合格</h3><p>第四篇先通过程序核对，随后才被作者判为分析空泛。真实使用要为质量检查配置可靠的判断方，并保留人工抽查。</p></div><div><h3>重试可能仍然失败</h3><p>本例每篇只允许重试一次，成功录制没有测试用尽次数后的失败分支。请提前约定失败如何交接，不把未通过的稿件伪装成已完成。</p></div><div><h3>复用模式不是全面安全隔离</h3><p>引擎无法监控宿主智能体用自己的终端做出的全部动作。仍要控制智能体的权限。本例只做审查，没有对外发送或不可逆提交。</p></div></div><div class="试跑提示"><h3>验收时，问这三个具体问题</h3><p>每篇都在清单里吗？后面的报告仍按约定逐项分析吗？没通过的部分是否明确列出来？</p><p>这些问题应当由交付材料和记录来回答。</p></div>'
新建实测=json.loads((根目录/'实测/逐篇新建writer/evidence/verification.json').read_text())
assert 新建实测['parent_status']=='completed' and 新建实测['collection_count']==3
assert len({项['agent_name'] for 项 in 新建实测['writers']})==3
实测内容='<p class="引言">循环一次，不等于换一个新会话。HOP 负责逐篇派发与回收；宿主驱动负责实际创建 writer。</p><div class="约定"><h3>已验证：三篇，三个新 writer</h3><p>另一次实测使用三篇稿件，每篇都由宿主创建一个不同的 writer，并设置 <code>fork_turns: &quot;none&quot;</code>。每个 writer 只收到当前文章、完整标准和当前任务，自行生成报告；HOP 核对六项栏目及原文引文，再逐篇收集。</p><p>三份报告均有六项栏目、四条原文引文。三个子实例完成，父任务最终为 <code>completed</code>，收集结果与实际提交一致。这次使用真实 writer，没有提供预写报告。</p></div><div class="边界"><div><h3>是谁启动新 writer？</h3><p>规约明确写出每篇新建的要求，驱动读到要求后调用宿主的创建 agent 工具。单靠 loop 或 call 不会自动创建新会话。其他宿主也需要提供并接入等价能力。</p></div><div><h3>三篇还说明不了什么？</h3><p>这验证了执行方式可行，没有证明长批次审稿质量更好。要检验后段是否缩水，需要相同稿件、模型和预算的长批次对照，比较普通连续审查、HOP 复用 writer 与 HOP 逐篇新建 writer。</p></div></div><p class="小字">新会话指不继承父对话历史，不代表文件系统隔离。第二个 writer 的自述核对表曾误填历史继承状态；原记录及其后续说明均保留。隔离的主要依据是实际启动参数，不能只信自述。</p><p><a href="https://github.com/dayuruozhi/hop3-playbook-zh/tree/main/实测/逐篇新建writer">查看三篇完整报告、执行命令和实测边界</a></p>'
页面+=章节('新会话','07','另一次真实 writer 实测','每篇换新 writer，实际跑通了吗？',实测内容)
页面+=章节('边界','08','交付前再核对一次','标准要清楚，责任也要清楚。',内容)
页面+='<footer><span>dayuruozhi · HOP3 独立中文实践手册</span><a href="https://github.com/dayuruozhi/hop3-playbook-zh">手册源码与证据</a><a href="https://github.com/hoplogic/hop3">HOP3 项目</a><a href="#开头">回到开头</a></footer></main><p class="仅辅助" aria-live="polite" id="播报"></p>'
class 页面检查(HTMLParser):
 def __init__(self):super().__init__();self.标识=[];self.链接=[]
 def handle_starttag(self,标签,属性):
  属性=dict(属性)
  if 属性.get('id'):self.标识.append(属性['id'])
  if 标签=='a' and 属性.get('href','').startswith('#'):self.链接.append(属性['href'][1:])
检查器=页面检查();检查器.feed(页面)
assert len(检查器.标识)==len(set(检查器.标识))
assert set(检查器.链接)<=set(检查器.标识)
if os.environ.get('HOP_REPO'):
 for 路径 in 资料:subprocess.run(['git','cat-file','-e',来源['引擎提交']+':'+路径],cwd=os.environ['HOP_REPO'],check=True,capture_output=True)
数据=json.dumps({'稿件':稿件,'完整报告':完整报告,'漏项报告':漏项报告,'套话报告':套话报告,'记录':记录,'来源':来源,'普通答复':完整答复文本},ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
样式=(根目录/'src/样式.css').read_text();脚本=(根目录/'src/交互.js').read_text()
网页='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="四篇中文稿件，两种退回原因。通过真实 HOP 引擎记录和笔记式演示，理解如何逐篇保持审查标准。"><link rel="canonical" href="https://dayuruozhi.github.io/hop3-playbook-zh/"><meta property="og:title" content="后面的稿件也要认真审｜HOP3 中文实践手册"><meta property="og:description" content="完整答复、逐段批注、命令与响应：用中文审稿示例理解 HOP3。"><meta property="og:type" content="website"><link rel="icon" href="data:,"><title>后面的稿件也要认真审｜HOP 3.0 中文实战手册</title><style>'+样式+'</style></head><body><!--email_off-->'+页面+'<script type="application/json" id="演示数据">'+数据+'</script><script>'+脚本+'</script><!--/email_off--></body></html>'
(根目录/'docs/index.html').write_text(网页)
说明='''# 四篇稿件逐篇审查：中文示例

本包的四篇稿件均为虚构，不对应真实调查或研究。每篇使用同一套六项框架，先核对栏目和引文，再判断分析质量。

使用方法：
1. 安装 Node.js 20 或更新版本，并准备 Claude Code、Codex 或 opencode。
2. 运行 npm install -g @hoplogic/hopjit，再运行 hopjit setup，新开一个智能体会话。
3. 在解压目录告诉智能体：/hop 运行「逐篇审查.md」，把稿件路径设为「稿件.json」。Codex 使用 $hop。
4. 先检查任务规约和重试上限，再运行并验收。

网页上的录制是受控演示：作者故意提供第三篇漏项稿和第四篇套话稿，并提供质量检查判定。真实引擎执行检查、两次重试与保存。你自己的模型输出和判定可能不同。

本规约只读原稿，不发消息，不修改原稿。复用模式下仍须信任并管理宿主智能体的权限。
'''
with zipfile.ZipFile(根目录/'docs/审稿示例.zip','w',compression=zipfile.ZIP_DEFLATED) as 包:
 for 名称,文本 in sorted({'使用说明.md':说明,'逐篇审查.md':规约,'稿件.json':json.dumps(稿件,ensure_ascii=False,indent=2)+'\n','普通答复示意.md':'# 普通智能体完整答复示意\n\n以下内容由作者构造，演示前面详细、后面漏项或空泛的情况；不是模型实测输出。\n\n'+完整答复文本+'\n','审读批注.md':'# 对完整示意答复的八处批注\n\n'+''.join('## '+str(项['号'])+'．'+项['标题']+'\n\n'+项['说明']+'\n\n违反的要求：'+项['要求']+'\n\n' for 项 in 批注)}.items()):
  信息=zipfile.ZipInfo(名称,date_time=(2026,10,16,0,0,0));信息.compress_type=zipfile.ZIP_DEFLATED;信息.external_attr=0o644<<16;包.writestr(信息,文本)
(根目录/'qa/资料.json').write_text(json.dumps(资料,ensure_ascii=False,indent=2)+'\n')
print('中文手册构建完成：',len(网页.encode()),'字节；15 次交互、两次重试、四份报告及所有引文已核验。')
