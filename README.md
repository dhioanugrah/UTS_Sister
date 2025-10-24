# UTS Sistem Terdistribusi – Pub-Sub Log Aggregator  
**Nama:** Dhio Anugrah Prakasa Putro  
**NIM:** 11221004  

---

## Deskripsi Singkat
Proyek ini merupakan implementasi layanan **Pub-Sub Log Aggregator** yang mampu:
- menerima event/log dari **publisher**,  
- memprosesnya melalui **subscriber/consumer** yang **idempotent** (tidak memproses ulang event yang sama),  
- serta melakukan **deduplication** terhadap duplikasi event.

Seluruh komponen dijalankan **lokal di dalam container Docker**, sesuai spesifikasi UTS Bab 1–7 (*Tanenbaum & van Steen, 2023*).

---

## Struktur Repository
```
src/                → kode aplikasi utama (Flask + thread consumer)
tests/              → unit tests (pytest)
requirements.txt    → dependensi Python
Dockerfile          → konfigurasi image utama
docker-compose.yml  → opsional (bonus +10%)
scripts/demo.ps1    → skrip otomatis demo di PowerShell
report.md / .pdf    → laporan teori & desain (Bab 1–7 + sitasi)
README.md           → panduan build/run & dokumentasi
```

---

##  Instruksi Singkat Build & Run
```bash
# Build image
docker build -t uts-aggregator .

# Jalankan container
docker run -p 8080:8080 uts-aggregator

# (opsional) dengan volume agar dedup.json persisten
docker volume create uts_dedup
docker run --name uts-agg -d -p 8080:8080 -v uts_dedup:/app/data uts-aggregator


```

---

##  Asumsi Desain
- Komunikasi antar-komponen berbasis **Publish-Subscribe** (HTTP lokal).  
- Aplikasi menggunakan **Flask** dengan background **ConsumerThread**.  
- **Dedup Store:** file JSON (`dedup.json`) yang disimpan persisten di `/app/data`.  
- **Idempotent consumer:** event `(topic, event_id)` sama tidak akan diproses ulang.  
- **Ordering:** hanya per-topic (tidak perlu total ordering).  
- **Toleransi kegagalan:** jika container direstart, dedup tetap mencegah duplikasi.  
- Seluruh komunikasi hanya lokal (tidak ada akses eksternal).  

---

## 📡 Endpoint API

| Method | Endpoint | Deskripsi |
|--------|-----------|-----------|
| `POST` | `/publish` | Mengirim event (single/batch JSON) ke aggregator |
| `GET`  | `/events?topic=...` | Mengambil daftar event unik berdasarkan topic |
| `GET`  | `/stats` | Melihat statistik: received, unique_processed, duplicate_dropped, topics, uptime |

### Contoh Event JSON
```json
{
  "topic": "orders",
  "event_id": "evt-1001",
  "timestamp": "2025-10-23T15:00:00Z",
  "source": "demo",
  "payload": { "order_id": 1 }
}
```

### Contoh Publish via curl
```bash
curl -X POST http://localhost:8080/publish   -H "Content-Type: application/json"   -d '{"topic":"orders","event_id":"evt-1001","timestamp":"2025-10-23T15:00:00Z","source":"demo","payload":{"order_id":1}}'
```

---

## Unit Tests
Jalankan seluruh pengujian:
```bash
docker run --rm -v ${PWD}:/app uts-aggregator pytest -q
```

Cakupan pengujian:
1. Dedup single event (idempotency)
2. Batch duplikat
3. Validasi skema event
4. Persistensi dedup store setelah restart
5. Konsistensi `/stats` & `/events`

Output yang diharapkan:
```
..... 5 passed in 2.5s
```

---

## (Opsional) Jalankan dengan Docker Compose
```bash
docker compose up -d
docker ps
```
Container `publisher` dapat mengirim event ke service `aggregator` melalui jaringan internal:
```bash
docker exec -it publisher sh -lc   "curl -s -X POST http://aggregator:8080/publish   -H 'Content-Type: application/json'   -d '{\"topic\":\"orders\",\"event_id\":\"evt-5001\",\"timestamp\":\"2025-10-23T15:00:00Z\",\"source\":\"pub\",\"payload\":{\"x\":1}}'"
```

---

## Link Video Demo
**YouTube:** (https://youtu.be/your-demo-link-here)
---

