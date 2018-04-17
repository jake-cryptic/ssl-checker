#!/usr/bin/env python
import socket
import sys

from datetime import datetime
from ssl import PROTOCOL_TLSv1

try:
    from OpenSSL import SSL
except ImportError:
    print('Required module does not exist. Install: pip install pyopenssl')
    sys.exit(1)


class TextColor:
    """Text colors."""

    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RESET = '\033[39m'


def get_cert(host):
    """Connection to the host."""
    osobj = SSL.Context(PROTOCOL_TLSv1)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, 443))
        print('\t{}[+]{} --> {}'.format(TextColor.GREEN, TextColor.RESET, host))
    except Exception as e:
        print('\t{}[-]{} {} failed: {}'.format(TextColor.RED, TextColor.RESET, host, e))
        return None

    oscon = SSL.Connection(osobj, sock)
    oscon.set_tlsext_host_name(host.encode())
    oscon.set_connect_state()
    oscon.do_handshake()

    cert = oscon.get_peer_certificate()
    sock.close()
    return cert


def get_cert_info(cert):
    """Get all the information about cert and create a JSON file."""
    context = {}

    context['issuer_c'] = cert.get_issuer().countryName
    context['issuer_o'] = cert.get_issuer().organizationName
    context['issuer_ou'] = cert.get_issuer().organizationalUnitName
    context['issuer_cn'] = cert.get_issuer().commonName
    context['cert_sn'] = cert.get_serial_number()
    context['cert_alg'] = cert.get_signature_algorithm().decode()
    context['cert_ver'] = cert.get_version()
    context['cert_exp'] = cert.has_expired()

    # Valid from
    valid_from = datetime.strptime(cert.get_notBefore().decode('ascii'),
                                   '%Y%m%d%H%M%SZ')
    context['valid_from'] = valid_from.strftime('%Y-%m-%d')

    # Vali till
    valid_till = datetime.strptime(cert.get_notAfter().decode('ascii'),
                                   '%Y%m%d%H%M%SZ')
    context['valid_till'] = valid_till.strftime('%Y-%m-%d')
    return context


def show_result(hosts):
    """Get the context."""
    context = {}
    print('Analyzing {} hosts:\n'.format(len(hosts)))
    for host in hosts:
        host = clean_hostname(host)
        cert = get_cert(host)
        if cert:
            context[host] = get_cert_info(cert)

    print(context)


def clean_hostname(host):
    """Remove unused characters. Order is important."""
    return host.replace('http://', '').replace('https://', '').replace('/', '')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: {} host1 [host2] [host3] ...'.format(sys.argv[0]))
        sys.exit(0)

    show_result(sys.argv[1:])