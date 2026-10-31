import csv,sys,json
from pathlib import Path
if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('Usage: python compare_results.py path_to_A1_scoring.csv path_to_A2_scoring.csv')
    sets=[list(csv.DictReader(open(p,encoding='utf-8'))) for p in sys.argv[1:]]
    common=set(r['case'] for r in sets[0]) & set(r['case'] for r in sets[1])
    output=[]
    for data in sets:
        if not data or any(r['pass_1_or_0'] not in ('0','1') or r['tool_appropriate_1_or_0'] not in ('0','1') for r in data):
            raise SystemExit('Human scoring incomplete: fill every pass and tool column with 0 or 1.')
        shared=[r for r in data if r['case'] in common]
        output.append({'version':data[0]['version'],'cases':len(data),'passed':sum(int(r['pass_1_or_0']) for r in data),
                       'shared_task_accuracy':sum(int(r['pass_1_or_0']) for r in shared)/len(shared),
                       'shared_mean_latency_ms':round(sum(float(r['latency_ms']) for r in shared)/len(shared),2),
                       'input_tokens_reported':sum(int(r['input_tokens']) for r in data if r['input_tokens']),
                       'output_tokens_reported':sum(int(r['output_tokens']) for r in data if r['output_tokens']),
                       'cases_without_reported_usage':sum(not r['input_tokens'] for r in data)})
    Path('reports/comparison.json').write_text(json.dumps(output,indent=2))
    print(json.dumps(output,indent=2)); print('Also attach manual reviewer approve/reject and audit evidence; these are separate from chat latency.')
