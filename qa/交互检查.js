(async()=>{
 const 成功=[],失败=[];
 const 确认=(条件,说明)=>(条件?成功:失败).push(说明);
 const 等待布局=()=>new Promise(完成=>requestAnimationFrame(()=>requestAnimationFrame(完成)));
 const 等待=毫秒=>new Promise(完成=>setTimeout(完成,毫秒));
 const 数据=JSON.parse(document.getElementById('演示数据').textContent);
 const 面板=[...document.querySelectorAll('.稿件区')];
 确认(document.documentElement.lang==='zh-CN','文档声明为简体中文');
 确认(面板.length===4&&!面板[2].hidden&&面板.filter(x=>!x.hidden).length===1,'默认显示第三篇');
 确认(数据.记录.length===15,'保留十五次中文录制交互');
 确认(JSON.stringify(数据.记录.at(-1).返回.variables.报告合集)===JSON.stringify(数据.完整报告),'最终合集与完整样稿一致');
 for(let 序号=0;序号<4;序号++){
  document.querySelector(`[data-article="${序号}"]`).click();await 等待布局();
  确认(!面板[序号].hidden&&面板.filter(x=>!x.hidden).length===1,'切换第'+(序号+1)+'篇');
  确认(document.querySelector(`[data-article="${序号}"]`).getAttribute('aria-pressed')==='true','选择状态明确'+序号);
  确认(面板[序号].querySelector('.原稿正文').textContent===数据.稿件[序号].正文,'原稿正文保持原值'+序号);
  if(序号>=2){
   const 退回=document.querySelector(`[data-reject="${序号}"]`),补写=document.querySelector(`[data-fixed="${序号}"]`);
   确认(!退回.hidden&&补写.hidden,'先显示未通过状态'+序号);
   document.querySelector(`[data-repair="${序号}"]`).click();await 等待布局();
   确认(退回.hidden&&!补写.hidden,'显示补写稿'+序号);
   确认(补写.contains(document.activeElement),'补写后焦点到达结果'+序号);
   确认(补写.querySelectorAll('[data-field]').length===6,'补写稿包含六项'+序号);
   document.querySelector(`[data-back="${序号}"]`).click();await 等待布局();
   确认(!退回.hidden&&补写.hidden,'可返回问题样稿'+序号);
  }
  确认(document.documentElement.scrollWidth===innerWidth,'稿件切换后无横向溢出'+序号);
 }
 确认(document.querySelector('[data-reject="2"]').textContent.includes('程序核对失败')||document.querySelector('[data-reject="2"]').textContent.includes('本次代码检查发现漏项'),'漏项由程序核对发现');
 确认(document.querySelector('[data-reject="3"]').textContent.includes('识别套话的判断来自作者'),'套话判定归属明确');
 const 整批=document.querySelector('#普通答复');
 const 连续稿件=[...整批.querySelectorAll('.普通篇目')];
 确认(连续稿件.length===4&&连续稿件.every(x=>x.getClientRects().length),'普通智能体的四篇答复连续完整展示');
 确认(连续稿件.map(x=>x.querySelectorAll('.普通栏目').length).join(',')==='6,6,2,6','从第三篇开始缩水的栏目差别可见');
 确认(整批.querySelectorAll('.问题高亮').length===8&&整批.querySelectorAll('.批注卡').length===8,'八处问题均有高亮和对应批注');
 确认(整批.querySelector('.答复开场').textContent.includes('均按六项标准'),'完整答复包含开场承诺');
 确认(整批.querySelector('.答复结尾').textContent.includes('四篇稿件均已按六项要求完成'),'完整答复包含错误完成声明');
 确认(document.querySelector('#普通答复-来源').textContent.includes('不是某个模型的实测输出'),'普通智能体答复标明为示意');
 const 切换=document.querySelector('.切换批注');切换.click();await 等待布局();
 确认(整批.classList.contains('隐藏审读批注')&&!整批.querySelector('.审读批注').getClientRects().length,'可隐藏批注纯读完整答复');
 确认(连续稿件.every(x=>x.getClientRects().length),'隐藏批注不会删去后面的答复');
 确认(document.documentElement.scrollWidth===innerWidth,'纯读答复无横向溢出');
 切换.click();await 等待布局();确认(整批.querySelector('.审读批注').getClientRects().length>0,'可恢复批注');
 let 已复制='';const 原写入=navigator.clipboard.writeText;navigator.clipboard.writeText=async 文字=>{已复制=文字;};
 document.querySelector('.复制整答').click();await 等待(80);navigator.clipboard.writeText=原写入;
 确认(已复制===数据.普通答复&&已复制.includes('## 第4篇'),'复制包含四篇完整答复且不含批注');
 for(const 号 of [1,2,3,4,5,6,7,8])确认(document.querySelector('#问题-'+号)&&document.querySelector('#批注-'+号),'批注编号与原答复位置对应'+号);
 const 最后按钮=document.querySelector('[data-article="3"]');最后按钮.focus();最后按钮.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));
 确认(document.activeElement.dataset.article==='0','方向键可循环选稿');
 document.activeElement.dispatchEvent(new KeyboardEvent('keydown',{key:'End',bubbles:true}));确认(document.activeElement.dataset.article==='3','End 可选择末篇');
 for(const 链接 of document.querySelectorAll('a[href^="#"]')){
  const 目标=document.getElementById(decodeURIComponent(链接.getAttribute('href').slice(1)));if(!目标)continue;
  链接.click();await 等待布局();
  const 标识=目标.getAttribute('aria-labelledby');const 标题=(标识&&document.getElementById(标识))||目标.querySelector('h1,h2,h3,h4,summary')||目标;
  确认(document.activeElement===标题,'页内链接焦点正确：'+目标.id);
 }
 const 来源=document.querySelector('a[href="#稿件-3"]');来源.scrollIntoView();来源.focus();const 原位置=scrollY;来源.click();await 等待布局();history.back();await 等待(200);await 等待布局();
 确认(document.activeElement===来源,'返回恢复来源焦点');确认(Math.abs(scrollY-原位置)<3,'返回恢复阅读位置');
 const 笔记=document.querySelector('#操作笔记>details');笔记.open=true;await 等待布局();
 const 条目=[...笔记.querySelectorAll('.笔记条目')];确认(条目.length===15,'十五个笔记单元均可读取');
 条目.forEach((项,索引)=>{
  确认(JSON.stringify(JSON.parse(项.querySelector('.完整返回').textContent))===JSON.stringify(数据.记录[索引].返回),'完整返回保留字段值'+索引);
  确认(项.querySelector('.原始返回').textContent===数据.记录[索引].返回原文,'原始输出逐字一致'+索引);
  确认(项.querySelector('.命令内容').getClientRects().length>0&&项.querySelector('.响应摘录').getClientRects().length>0,'命令与返回同时可见'+索引);
  确认(项.querySelector('.笔记目的').textContent.length>10&&项.querySelector('.解读框').textContent.length>20,'每次交互有目的和解释'+索引);
  if(数据.记录[索引].提交内容)确认(JSON.stringify(JSON.parse(项.querySelector('.输入内容').textContent))===JSON.stringify(数据.记录[索引].提交内容),'提交内容保留原值'+索引);
 });
 确认(条目[6].textContent.includes('第三篇的写作任务'),'第三篇退回指向同一篇');
 确认(条目[10].textContent.includes('识别空泛分析的判断来自作者'),'第四篇不把作者判定写成引擎判断');
 const 规约=document.querySelector('#任务规约>details');规约.open=true;await 等待布局();
 const 展开=规约.querySelector('.展开代码'),文本=规约.querySelector('pre');确认(!展开.hidden,'长规约有展开入口');展开.click();确认(文本.classList.contains('展开'),'规约可展开');展开.click();确认(!文本.classList.contains('展开'),'规约可收起');
 const 换行=规约.querySelector('.换行按钮');换行.click();确认(!文本.classList.contains('可换行'),'可恢复原行');换行.click();确认(文本.classList.contains('可换行'),'可自动换行');
 for(const 配色 of ['light','dark','system']){const 选择=document.getElementById('主题');选择.value=配色;选择.dispatchEvent(new Event('change'));确认(配色==='system'?!document.documentElement.dataset.theme:document.documentElement.dataset.theme===配色,'配色切换'+配色);}
 const 复制=document.querySelector('.约定>.复制');复制.click();await 等待(80);确认(['已复制','已选中文字'].includes(复制.textContent),'复制或选中文字回退可用');
 确认(!document.body.innerText.includes('Read the')&&!document.body.innerText.includes('Copy request'),'无残留英文界面标签');
 确认(document.documentElement.scrollWidth===innerWidth,'全部交互后无横向溢出');
 return JSON.stringify({通过:成功.length,失败:失败.length,失败项:失败});
})()
