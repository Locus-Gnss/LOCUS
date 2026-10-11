import json
import urllib.request
import pandas as pd

df = pd.read_csv('data/structured/locus_structured_gnss.csv').iloc[1057:1070]
csv_str = df.to_csv(index=False)
payload = {
    'data': csv_str,
    'format': 'csv',
    'source_name': 'live_test.csv',
    'source_type': 'RECORDED FILE'
}

req = urllib.request.Request(
    'http://localhost:5173/api/pipeline/process',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as res:
        body = json.loads(res.read().decode('utf-8'))
        print('Pipeline Success:', body.get('success'))
        print('Run ID:', body.get('run_id'))
        print('Records Ingested:', body.get('records_ingested'))
        print('Valid Records:', body.get('valid_records'))
        print('Event ID Generated:', body.get('event_id'))
        print('\nStages Breakdown:')
        for s in body.get('stages', []):
            dur = s.get('duration_ms', 0)
            print(f"  [{s.get('status')}] {s.get('name')}: {s.get('details', '')} ({dur:.1f}ms)")
except urllib.error.HTTPError as err:
    print('HTTP Error:', err.code, err.read().decode('utf-8'))
except Exception as ex:
    print('Error:', ex)
