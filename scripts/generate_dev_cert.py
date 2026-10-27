"""Generate a self-signed TLS cert/key for local HTTPS dev (certs/dev-*.pem).

getUserMedia (camera access, used by the 센서 재고 등록 scan page) only works
in a "secure context" -- HTTPS or localhost. This app is normally accessed
over plain HTTP via a LAN IP, which browsers do NOT treat as secure, so the
camera feature is blocked on a real phone. Running uvicorn with this cert
makes the LAN address itself HTTPS, which fixes that.

The cert covers the machine's current LAN IP(s) plus localhost/127.0.0.1.
Since this PC's LAN IP changes (DHCP), **re-run this script whenever the IP
changes** -- the old cert will otherwise mismatch the new address.

Extra addresses (e.g. a port-forward's external-facing IP on another
network this PC isn't itself on) can be passed as arguments and are added
to the certificate too, on top of the auto-detected ones:

Usage:
    .venv/Scripts/python scripts/generate_dev_cert.py [extra-ip ...]
    .venv/Scripts/python scripts/generate_dev_cert.py 192.168.120.25
"""

import datetime
import ipaddress
import socket
import sys

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

CERT_DIR = "certs"


def local_ips() -> list[str]:
    ips = {"127.0.0.1"}
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    # most reliable way to find the actual LAN-facing IP: open a dummy UDP
    # socket toward a public address (nothing is actually sent)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ips.add(s.getsockname()[0])
    except OSError:
        pass
    return sorted(ips)


def main():
    import os

    os.makedirs(CERT_DIR, exist_ok=True)

    ips = sorted(set(local_ips()) | set(sys.argv[1:]))
    print("Including IPs/hostnames in certificate:", ips, "+ localhost")

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "stocktaking-dev")]
    )

    san_entries = [x509.DNSName("localhost")] + [
        x509.IPAddress(ipaddress.ip_address(ip)) for ip in ips
    ]

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=825)
        )
        .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
        .sign(key, hashes.SHA256())
    )

    with open(f"{CERT_DIR}/dev-key.pem", "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    with open(f"{CERT_DIR}/dev-cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"Wrote {CERT_DIR}/dev-key.pem and {CERT_DIR}/dev-cert.pem")


if __name__ == "__main__":
    main()
