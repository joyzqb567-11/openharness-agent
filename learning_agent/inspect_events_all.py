import json, pathlib
p = pathlib.Path('acceptance_controller/runs/computer_use_full_model_loop_paint_tree_real-20260606_143518/events.jsonl')
lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
for i, line in enumerate(lines, 1):
    j = json.loads(line)
    payload = j.get('payload') or {}
    st = j.get('state','')
    tool = payload.get('tool_name','')
    action = str(payload.get('action','') or payload.get('message','') or payload.get('error','')).replace('\n',' ')[:140]
    result = payload.get('result')
    if result is not None:
        result = json.dumps(result, ensure_ascii=False)[:220]
    print(f'{i:02d} {j.get("timestamp")} {st} tool={tool} action={action} result={result}')
