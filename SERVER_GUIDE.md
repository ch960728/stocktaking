# 서버 접속 안 될 때 체크리스트

`https://192.168.0.3:8010` 또는 `https://192.168.120.25:8010` 접속이 안 될 때 순서대로 확인한다.

## 1. Docker (MariaDB) 켜져 있는지 확인

```
docker compose ps
```

`stocktaking-mariadb-1`이 `Up ... (healthy)` 상태인지 확인. 꺼져 있으면:

```
docker compose up -d
```

## 2. uvicorn(앱 서버) 실행 여부 확인 — 가장 흔한 원인

Docker를 켜는 것과 앱 서버(uvicorn)를 띄우는 건 별개 단계다. Docker만 켜고 uvicorn을 안 띄우면 8010 포트에 아무도 응답하지 않는다.

실행 중인지 확인:

```
netstat -ano | findstr 8010
```

`LISTENING`이 안 보이면 서버가 안 떠 있는 것 — 아래로 실행:

```
.venv/Scripts/python -m uvicorn app.main:app --host 0.0.0.0 --port 8010 --ssl-keyfile certs/dev-key.pem --ssl-certfile certs/dev-cert.pem
```

## 3. 인증서(SAN)에 접속 IP가 포함돼 있는지 확인

PC의 LAN IP가 DHCP로 바뀌면 인증서가 안 맞아서 TLS 자체가 실패한다 (브라우저에서 "안전하지 않음"이 아니라 접속 자체가 안 됨).

현재 IP 확인:

```
ipconfig
```

인증서에 포함된 IP/만료일 확인:

```
.venv/Scripts/python -c "
from cryptography import x509
cert = x509.load_pem_x509_certificate(open('certs/dev-cert.pem','rb').read())
san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
print('만료일:', cert.not_valid_after_utc)
for name in san.value:
    print(name)
"
```

IP가 바뀌었거나 인증서에 안 보이면 재생성 후 서버 재시작:

```
.venv/Scripts/python scripts/generate_dev_cert.py
```
(서버를 재시작해야 새 인증서로 반영됨)

## 4. 공유기 포트포워딩 (192.168.120.25 쪽 접속일 때만)

1~3번이 전부 정상인데도 사무실 네트워크(192.168.120.25)에서 안 되면, 로컬에서는 확인할 수 없는 영역이다 — 공유기/포트포워딩 설정을 다시 봐야 한다.

---

막히면 1→2→3→4 순서로 하나씩 확인. 대부분은 2번(서버 자체가 안 떠 있음)이 원인이다.
