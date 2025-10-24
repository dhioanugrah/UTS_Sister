#  UTS Sistem Terdistribusi – Pub-Sub Log Aggregator  
**Nama:** Dhio Anugrah Prakasa Putro  
**NIM:** 11221004  

---

##  Deskripsi Singkat
Proyek ini merupakan implementasi layanan **Pub-Sub Log Aggregator** yang mampu:
- menerima event/log dari **publisher**,  
- memprosesnya melalui **subscriber/consumer** yang **idempotent** (tidak memproses ulang event yang sama),  
- serta melakukan **deduplication** terhadap duplikasi event.

Seluruh komponen dijalankan **lokal di dalam container Docker**, sesuai spesifikasi UTS Bab 1–7 (*Tanenbaum & van Steen, 2023*).

---

##  Struktur Repository
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

## Langkah Pengujian (sesuai video demo)

### 1 Build & Run Container
```powershell
cd D:\UTS_SISTER

# Build image
docker build -t uts-aggregator .

# (opsional) volume untuk persistensi dedup.json
docker volume create uts_dedup

# Jalankan container
docker rm -f uts-agg 2>$null
docker run --name uts-agg -d -p 8080:8080 -v uts_dedup:/app/data uts-aggregator

# Cek status awal
curl.exe http://localhost:8080/stats
```

---

### 2️ Kirim Event Unik dan Duplikat
```powershell
# Siapkan payload JSON tanpa escape ribet
@'
{
  "topic": "orders",
  "event_id": "evt-1001",
  "timestamp": "2025-10-23T15:00:00Z",
  "source": "demo",
  "payload": { "order_id": 1 }
}
'@ | Set-Content -Path .\payload.json -Encoding UTF8

# Kirim event unik
curl.exe -s -X POST http://localhost:8080/publish -H "Content-Type: application/json" --data-binary "@payload.json"

# Kirim duplikat (2x)
curl.exe -s -X POST http://localhost:8080/publish -H "Content-Type: application/json" --data-binary "@payload.json"
curl.exe -s -X POST http://localhost:8080/publish -H "Content-Type: application/json" --data-binary "@payload.json"
```

---

### 3️ Cek `/events` dan `/stats`
```powershell
curl.exe "http://localhost:8080/events?topic=orders"
curl.exe http://localhost:8080/stats
```
> ✅ `unique_processed` tetap 1 dan `duplicate_dropped` bertambah, menunjukkan mekanisme **idempotent consumer + deduplication** berjalan dengan benar.

---

### 4️ Restart Container (Uji Persistensi Dedup)
```powershell
docker restart uts-agg

# Kirim ulang event lama → tetap dideteksi duplikat
curl.exe -s -X POST http://localhost:8080/publish -H "Content-Type: application/json" --data-binary "@payload.json"

# Cek metrik lagi
curl.exe http://localhost:8080/stats
```
> ✅ Nilai `unique_processed` tidak berubah, membuktikan **dedup store (JSON)** tetap persisten setelah restart.

---

### 5️ Jalankan Unit Tests
```powershell
docker run --rm -v ${PWD}:/app uts-aggregator pytest -q
```
> Output yang diharapkan:
```
..... 5 passed in 2.5s
```

Cakupan test:
1. Dedup single event (idempotency)  
2. Batch duplikat  
3. Validasi skema event  
4. Persistensi dedup store setelah restart  
5. Konsistensi `/stats` & `/events`

---

### 6️ (Opsional Bonus) Jalankan dengan Docker Compose
#### File `docker-compose.yml`
```yaml
version: "3.9"
services:
  aggregator:
    build: .
    container_name: uts-agg
    ports: ["8080:8080"]
    volumes: [ "uts_dedup:/app/data" ]
    environment: [ "DATA_DIR=/app/data" ]
    healthcheck:
      test: ["CMD","curl","-f","http://localhost:8080/stats"]
      interval: 5s
      timeout: 3s
      retries: 10
    restart: unless-stopped

  publisher:
    image: curlimages/curl:8.10.1
    container_name: uts-pub
    command: ["sleep","infinity"]
    depends_on:
      aggregator:
        condition: service_healthy
    restart: unless-stopped

volumes:
  uts_dedup:
```

#### Jalankan Compose
```powershell
docker compose up -d
docker ps
```

#### Kirim Event dari Publisher
```powershell
docker exec -it uts-pub sh -lc "printf '%s\n' '{"topic":"orders","event_id":"evt-5001","timestamp":"2025-10-23T15:00:00Z","source":"pub","payload":{"x":1}}'  | curl -s -X POST http://aggregator:8080/publish -H 'Content-Type: application/json' --data-binary @-"

curl.exe http://localhost:8080/stats
curl.exe "http://localhost:8080/events?topic=orders"
```

---

##  Asumsi Desain
- Arsitektur **Publish–Subscribe** (Flask sebagai broker).  
- **Idempotent consumer**: tidak memproses ulang event `(topic, event_id)` yang sama.  
- **Dedup store** menggunakan JSON file (`dedup.json`), bersifat persisten.  
- **Ordering** hanya per-topic (tidak total ordering).  
- **Toleransi kegagalan**: restart tidak menghapus dedup store.  
- Komunikasi hanya lokal, tanpa jaringan eksternal.

---

##  Laporan / Report
**File:** `report.md` atau `report.pdf`  

Isi laporan:
- Penjelasan teori Bab 1–7 (*Distributed Systems – Tanenbaum & van Steen, 2023*)  
- Desain arsitektur sistem  
- Idempotency, deduplication, ordering, fault tolerance  
- Analisis performa (throughput, latency, duplicate rate)  
- Sitasi APA edisi ke-7  

**Contoh sitasi:**
> Van Steen, M., & Tanenbaum, A. S. (2023).  
> *Distributed Systems: Principles and Paradigms* (4th ed.). Vrije Universiteit Amsterdam.

---

##  Link Video Demo
 **YouTube:** (https://youtu.be/your-demo-link-here)


---

