import json, pathlib
p = pathlib.Path('acceptance_controller/runs/computer_use_full_model_loop_paint_tree_real-20260606_143518/events.jsonl')
lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
print('path=', p)
print('line_count=', len(lines))
for i, line in list(enumerate(lines, 1))[-18:]:
    j = json.loads(line)
    payload = j.get('payload') or {}
    st = j.get('state','')
    ts = j.get('timestamp','')
    tool = payload.get('tool_name','')
    action = payload.get('action') or payload.get('message') or payload.get('error') or ''
    action = str(action).replace('\r',' ').replace('\n',' ')
    if len(action) > 180:
        action = action[:180] + '...'
    res = payload.get('result')
    summary = ''
    if isinstance(res, dict):
        for k in ['status','success','error','message','action','backend','platform']:
            if k in res and res[k] not in (None, ''):
                summary += f'{k}={str(res[k])[:80]} '
    elif res is not None:
        summary = str(res).replace('\n',' ')[:180]
    print(f'{i:02d} | {ts} | {st} | tool={tool} | action={action} | result={summary}')
