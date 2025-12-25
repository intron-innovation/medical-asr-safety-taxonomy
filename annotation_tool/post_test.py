import json
from urllib.request import Request, urlopen

payload = {
    "annotatorId": "ANN_TEST",
    "annotatorName": "Test User",
    "annotatorEmail": "test@example.com",
    "utteranceId": "utt-1",
    "errorType": "DEL",
    "errorMatch": "[DEL:foo]",
    "taxonomy": ["meaning", "fluency"],
    "severity": 3,
    "timestamp": "2025-12-24T12:00:00Z",
    "humanTranscript": "hello world",
    "asrReconstructed": "[DEL:foo] bar"
}

req = Request(
    'http://127.0.0.1:5000/annotations',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type':'application/json'},
    method='POST'
)

with urlopen(req) as resp:
    print(resp.read().decode('utf-8'))
