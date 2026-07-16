from minio import Minio
import json

client = Minio("localhost:9000",
               access_key="admin",
               secret_key="iWdbGMmiWUDpQtlGe89HIKaOLAV7ve9a",
               secure=False)

data = client.get_object(
    "securecodebox",
    "scan-1aa6fa91-3109-4fc2-b64a-bc4980739fb7/findings.json"
)
findings = json.loads(data.read())
print(f"Total findings: {len(findings)}")
for f in findings:
    print(f"  [{f.get('severity','?')}] {f['name']} - {str(f.get('description',''))[:80]}")
