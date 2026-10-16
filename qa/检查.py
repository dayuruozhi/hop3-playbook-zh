from pathlib import Path
import sys,subprocess,os
根=Path(__file__).resolve().parent.parent
宽度=sys.argv[1] if len(sys.argv)>1 else '400'
网址=sys.argv[2] if len(sys.argv)>2 else 'http://127.0.0.1:8875'
结果=subprocess.run(['node',str(根/'qa/浏览器.mjs'),网址,宽度,str(根/('qa/交互-'+宽度)),'0',(根/'qa/交互检查.js').read_text(),'light'],text=True,capture_output=True,env=dict(os.environ,REDUCE='1'))
print(结果.stdout,结果.stderr)
(根/('qa/检查-'+宽度+('-公网' if 'cloudflare' in 网址 else '')+'.log')).write_text(结果.stdout+结果.stderr)
if 结果.returncode or '"失败":0' not in 结果.stdout or 'EXCEPTION' in 结果.stdout or 'LOG:' in 结果.stdout:sys.exit(1)
