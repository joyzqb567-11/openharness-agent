import json, pathlib
p = pathlib.Path('acceptance_controller/runs/computer_use_full_model_loop_paint_tree_real-20260606_143518/events.jsonl')
lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
print('line_count', len(lines))
for i, line in enumerate(lines, 1):
    j = json.loads(line)
    payload = j.get('payload') or {}
    st = j.get('state','')
    tool = payload.get('tool_name','')
    action = str(payload.get('action','') or payload.get('message','') or payload.get('error','')).replace('\r',' ').replace('\n',' ')
    if len(action) > 90: action = action[:90] + '...'
    status = ''
    res = payload.get('result')
    if isinstance(res, dict):
        status = str(res.get('status') or res.get('success') or res.get('error') or res.get('message') or '')[:90]
    elif res is not None:
        status = str(res).replace('\n',' ')[:90]
    print(f'{i:02d} {st} tool={tool} action={action} result={status}')
