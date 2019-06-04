import re
from asn1crypto.core import load as load_asn1


def split_certificate_chain(filename):
    pem_certificates = []
    current_certificate = ""
    with open(filename, "r") as f:
        for line in f:
            if "--BEGIN" in line:
                if current_certificate:
                    pem_certificates.append(current_certificate)
                    current_certificate = ""
            current_certificate = "{}{}".format(current_certificate, line)
    if current_certificate:
        pem_certificates.append(current_certificate)
    return pem_certificates


# the way for example that the logstash filebeat input serializes the serialNumber of a client cert
SERIAL_NUMBER_OID = '2.5.4.5'
ASN1_ENCODED_STRING_RE = re.compile("^#(?P<bytes>(?:[0-9a-f][0-9a-f]){3,})$")


def parse_dn(dn):
    # TODO: poor man's DN parser
    d = {}
    current_attr = ""
    current_val = ""

    state = "ATTR"
    string_state = "NOT_ESCAPED"
    for c in dn:
        if c == "\\" and string_state == "NOT_ESCAPED":
            string_state = "ESCAPED"
        else:
            if string_state == "NOT_ESCAPED" and c in "=,":
                if c == "=":
                    state = "VAL"
                elif c == ",":
                    state = "ATTR"
                    if current_attr:
                        d[current_attr] = current_val
                    current_attr = current_val = ""
            else:
                if state == "ATTR":
                    current_attr += c
                elif state == "VAL":
                    current_val += c
                if string_state == "ESCAPED":
                    string_state = "NOT_ESCAPED"

    if current_attr:
        d[current_attr] = current_val
        current_attr = current_val = ""

    # try to extract the serial number
    encoded_serial_number = d.get(SERIAL_NUMBER_OID)
    if encoded_serial_number:
        m = ASN1_ENCODED_STRING_RE.match(encoded_serial_number.lower())
        if m:
            try:
                d["serialNumber"] = str(load_asn1(bytes.fromhex(m.group("bytes"))))
            except Exception:
                pass
            else:
                d.pop(SERIAL_NUMBER_OID)
    return d
