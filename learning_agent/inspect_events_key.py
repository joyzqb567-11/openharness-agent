import json, pathlib
p = pathlib.Path('acceptance_controller/runs/computer_use_full_model_loop_paint_tree_real-20260606_143518/events.jsonl')
lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
print('path=', p)
print('line_count=', len(lines))
interesting = []
keywords = ['fail','error','denied','complete','final','assert','timeout','stop','success','result','exception','ready','tool_call','tool_result','computer']
for i, line in enumerate(lines, 1):
    try:
        j = json.loads(line)
    except Exception as e:
        interesting.append((i, '', 'JSONERR', '', str(e), ''))
        continue
    st = str(j.get('state',''))
    payload = j.get('payload') or {}
    if i > len(lines)-60 or any(k in st.lower() for k in keywords):
        action = str(payload.get('action','')).replace('\r',' ').replace('\n',' ')
        msg = str(payload.get('message','')).replace('\r',' ').replace('\n',' ')
        err = str(payload.get('error','')).replace('\r',' ').replace('\n',' ')
        tool = str(payload.get('tool_name',''))
        if len(action) > 180: action = action[:180] + '...'
        if len(msg) > 180: msg = msg[:180] + '...'
        if len(err) > 180: err = err[:180] + '...'
        interesting.append((i, j.get('timestamp'), st, tool, err, action or msg))
for row in interesting[-120:]:
    print('{} | {} | {} | tool={} | err={} | {}'.format(*row))
