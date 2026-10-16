(() => {
 'use strict';
 const 单个=(选择器,范围=document)=>范围.querySelector(选择器);
 const 全部=(选择器,范围=document)=>[...范围.querySelectorAll(选择器)];
 const 稿件区=全部('.稿件区');
 let 当前序号=2,返回计数=0;
 const 补写状态={2:false,3:false};
 const 播报=文字=>{单个('#播报').textContent=文字;};
 function 聚焦(元素){if(!元素)return;if(!元素.hasAttribute('tabindex')&&!/^(A|BUTTON|SELECT)$/.test(元素.tagName))元素.tabIndex=-1;元素.focus({preventScroll:true});}
 function 检查溢出(){
  全部('.代码块').forEach(块=>{
   if(!块.getClientRects().length)return;
   const 文本=单个('pre',块),展开=单个('.展开代码',块),换行=单个('.换行按钮',块);
   if(展开)展开.hidden=!(文本.classList.contains('展开')||文本.scrollHeight>文本.clientHeight+2);
   if(换行)换行.hidden=!(文本.classList.contains('可换行')||文本.scrollWidth>文本.clientWidth+2);
  });
 }
 function 选稿(序号){
  当前序号=序号;
  稿件区.forEach((区,索引)=>区.hidden=索引!==序号);
  全部('[data-article]').forEach((按钮,索引)=>按钮.setAttribute('aria-pressed',String(索引===序号)));
  播报('正在查看第'+(序号+1)+'篇：'+单个('h3',稿件区[序号]).textContent);
  检查溢出();
 }
 function 切换补写(序号,已补写,移动焦点=false){
  补写状态[序号]=已补写;
  单个(`[data-reject="${序号}"]`).hidden=已补写;
  单个(`[data-fixed="${序号}"]`).hidden=!已补写;
  if(移动焦点){const 状态=单个((已补写?`[data-fixed="${序号}"]`:`[data-reject="${序号}"]`)+' .状态条');聚焦(状态);状态.scrollIntoView({block:'nearest'});播报(状态.textContent);}
  检查溢出();
 }
 function 展开上层(元素){for(let 上层=元素.parentElement;上层;上层=上层.parentElement)if(上层.tagName==='DETAILS')上层.open=true;}
 function 跳转(锚点){
  const 标识=decodeURIComponent(锚点.slice(1)),目标=document.getElementById(标识);
  if(!目标)return;
  const 匹配=标识.match(/^稿件-(\d)$/);if(匹配)选稿(Number(匹配[1])-1);
  if(/^批注-/.test(标识)){
   单个('#普通答复').classList.remove('隐藏审读批注');const 按钮=单个('.切换批注');按钮.setAttribute('aria-pressed','true');按钮.textContent='隐藏批注，先读原答复';
  }
  展开上层(目标);
  const 标题标识=目标.getAttribute('aria-labelledby');
  const 标题=(标题标识&&document.getElementById(标题标识))||单个('h1,h2,h3,h4,summary',目标)||目标;
  目标.scrollIntoView({block:'start'});聚焦(标题);检查溢出();
 }
 function 保存状态(来源){
  if(来源&&!来源.id)来源.id='返回点-'+(++返回计数);
  return {位置:scrollY,焦点:来源?.id||document.activeElement?.id||'',当前序号,补写状态:{...补写状态},隐藏批注:单个('#普通答复').classList.contains('隐藏审读批注')};
 }
 选稿(2);切换补写(2,false);切换补写(3,false);
 document.documentElement.classList.add('有脚本');
 全部('[data-article]').forEach(按钮=>{
  按钮.addEventListener('click',()=>{选稿(Number(按钮.dataset.article));history.replaceState(保存状态(),'',`#稿件-${当前序号+1}`);});
  按钮.addEventListener('keydown',事件=>{
   if(!['ArrowLeft','ArrowRight','Home','End'].includes(事件.key))return;
   事件.preventDefault();const 序号=事件.key==='Home'?0:事件.key==='End'?3:(当前序号+(事件.key==='ArrowRight'?1:3))%4;
   选稿(序号);聚焦(单个(`[data-article="${序号}"]`));history.replaceState(保存状态(),'',`#稿件-${序号+1}`);
  });
 });
 全部('[data-repair]').forEach(按钮=>按钮.addEventListener('click',()=>切换补写(Number(按钮.dataset.repair),true,true)));
 全部('[data-back]').forEach(按钮=>按钮.addEventListener('click',()=>切换补写(Number(按钮.dataset.back),false,true)));
 history.scrollRestoration='manual';history.replaceState(保存状态(),'',location.href);
 document.addEventListener('click',async 事件=>{
  const 链接=事件.target.closest('a[href^="#"]');
  if(链接&&!事件.ctrlKey&&!事件.metaKey&&!事件.shiftKey&&!事件.altKey){
   const 锚点=链接.getAttribute('href');if(!document.getElementById(decodeURIComponent(锚点.slice(1))))return;
   事件.preventDefault();history.replaceState(保存状态(链接),'',location.href);history.pushState({},'',锚点);跳转(锚点);history.replaceState(保存状态(),'',location.href);return;
  }
  const 批注切换=事件.target.closest('.切换批注');
  if(批注切换){
   const 隐藏=document.getElementById('普通答复').classList.toggle('隐藏审读批注');
   批注切换.setAttribute('aria-pressed',String(!隐藏));批注切换.textContent=隐藏?'显示批注，看哪里没达标':'隐藏批注，先读原答复';播报(隐藏?'已隐藏批注，保留完整示意答复':'已显示八处审读批注');
  }
  const 整答复制=事件.target.closest('.复制整答');
  if(整答复制){
   const 文字=JSON.parse(单个('#演示数据').textContent).普通答复,原标签=整答复制.textContent;
   try{await navigator.clipboard.writeText(文字);整答复制.textContent='已复制完整答复';播报('完整示意答复已复制，不含审读批注');}
   catch{const 区间=document.createRange();区间.selectNodeContents(单个('.答复正文'));const 选择=window.getSelection();选择.removeAllRanges();选择.addRange(区间);整答复制.textContent='已选中答复文字';播报('答复文字已选中，请使用键盘复制');}
   setTimeout(()=>整答复制.textContent=原标签,2200);
  }
  const 复制=事件.target.closest('.复制');
  if(复制){
   const 文本=单个('pre',复制.closest('.代码块,.约定')),原标签=复制.textContent;
   try{await navigator.clipboard.writeText(文本.textContent);复制.textContent='已复制';播报('内容已复制到剪贴板');}
   catch{const 区间=document.createRange();区间.selectNodeContents(文本);const 选择=window.getSelection();选择.removeAllRanges();选择.addRange(区间);复制.textContent='已选中文字';播报('文字已选中，请使用键盘复制');}
   setTimeout(()=>复制.textContent=原标签,2200);
  }
  const 展开=事件.target.closest('.展开代码');
  if(展开){const 文本=单个('pre',展开.closest('.代码块'));文本.classList.toggle('展开');展开.textContent=(文本.classList.contains('展开')?'收起':'展开')+(展开.dataset.name||'内容');检查溢出();}
  const 换行=事件.target.closest('.换行按钮');
  if(换行){const 文本=单个('pre',换行.closest('.代码块'));文本.classList.toggle('可换行');换行.setAttribute('aria-pressed',String(文本.classList.contains('可换行')));换行.textContent=文本.classList.contains('可换行')?'保留原行':'自动换行';检查溢出();}
 });
 window.addEventListener('popstate',()=>{
  const 已存=history.state;
  if(已存){单个('#普通答复').classList.toggle('隐藏审读批注',Boolean(已存.隐藏批注));const 批注按钮=单个('.切换批注');批注按钮.setAttribute('aria-pressed',String(!已存.隐藏批注));批注按钮.textContent=已存.隐藏批注?'显示批注，看哪里没达标':'隐藏批注，先读原答复';选稿(已存.当前序号??2);for(const 序号 of [2,3])切换补写(序号,Boolean(已存.补写状态?.[序号]));}
  const 目标=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(目标)展开上层(目标);
  requestAnimationFrame(()=>{if(已存){window.scrollTo(0,已存.位置||0);聚焦(document.getElementById(已存.焦点));}else if(location.hash)跳转(location.hash);检查溢出();});
 });
 document.addEventListener('toggle',()=>requestAnimationFrame(检查溢出),true);
 window.addEventListener('resize',检查溢出);
 const 主题=单个('#主题');
 function 设置配色(选择){if(选择==='system')delete document.documentElement.dataset.theme;else document.documentElement.dataset.theme=选择;}
 try{主题.value=localStorage.getItem('中文审稿手册配色')||'system';}catch{}
 设置配色(主题.value);
 主题.addEventListener('change',()=>{设置配色(主题.value);try{localStorage.setItem('中文审稿手册配色',主题.value);}catch{}检查溢出();});
 if(location.hash)跳转(location.hash);requestAnimationFrame(检查溢出);
})();
