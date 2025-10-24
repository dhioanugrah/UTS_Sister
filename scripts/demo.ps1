
param([int]$Port=8080)
docker build -t uts-aggregator .
docker volume create uts_dedup | Out-Null
docker rm -f uts-agg 2>$null | Out-Null
docker run --name uts-agg -d -p ${Port}:8080 -v uts_dedup:/app/data uts-aggregator
curl.exe http://localhost:$Port/stats

@'
{
  "topic": "orders",
  "event_id": "evt-1001",
  "timestamp": "2025-10-23T15:00:00Z",
  "source": "demo",
  "payload": { "order_id": 1 }
}
'@ | Set-Content -Path .\payload.json -Encoding UTF8

curl.exe -s -X POST http://localhost:$Port/publish -H "Content-Type: application/json" --data-binary "@payload.json"
curl.exe -s -X POST http://localhost:$Port/publish -H "Content-Type: application/json" --data-binary "@payload.json"
curl.exe -s -X POST http://localhost:$Port/publish -H "Content-Type: application/json" --data-binary "@payload.json"
curl.exe "http://localhost:$Port/events?topic=orders"
curl.exe http://localhost:$Port/stats

1..10 | ForEach-Object {
  $evt = @{
    topic="orders"; event_id="evt-$($_+2000)"; timestamp="2025-10-23T15:00:00Z"; source="loader"; payload=@{n=$_}
  } | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Uri http://localhost:$Port/publish -Method POST -ContentType "application/json" -Body $evt | Out-Null
}
curl.exe http://localhost:$Port/stats

docker restart uts-agg | Out-Null
curl.exe -s -X POST http://localhost:$Port/publish -H "Content-Type: application/json" --data-binary "@payload.json"
curl.exe http://localhost:$Port/stats

docker run --rm -v ${PWD}:/app uts-aggregator pytest -q
