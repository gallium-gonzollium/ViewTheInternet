import threading
import queue
import time
import requests
from config import RDAP_ENDPOINTS, RDAP_REQUEST_TIMEOUT, RDAP_WORKER_THROTTLE
from cache import LRUCache
from countries import translate_country
from rdap_registry import IANA_IPV4_REGISTRY

rdap_cache = LRUCache()
rdap_q = queue.Queue()
RDAP_WORKER_SHUTDOWN = object()

def rdap_worker():
    session = requests.Session()
    headers = {"User-Agent": "clipmap-rdap/1.0"}
    while True:
        try:
            item = rdap_q.get(timeout=1.0)
            if item is RDAP_WORKER_SHUTDOWN:
                break
            key, query = item
            
            if not rdap_cache.contains(key):
                result = None
                for tmpl in RDAP_ENDPOINTS:
                    try:
                        r = session.get(tmpl.format(query), headers=headers, timeout=RDAP_REQUEST_TIMEOUT)
                        if r.status_code == 200:
                            result = r.json()
                            break
                    except requests.RequestException:
                        continue
                
                rdap_cache.put(key, result)
                time.sleep(RDAP_WORKER_THROTTLE)
                
            rdap_q.task_done()
        except queue.Empty:
            continue

def enqueue_rdap_query(key, query):
    if rdap_cache.contains(key) or (key.startswith("net:") and str(query).strip().endswith("/8")):
        return
    try:
        rdap_q.put_nowait((key, query))
    except queue.Full:
        pass

def rdap_score(j):
    if not j:
        return 0
    score = 0
    if j.get('entities'):
        score += 50
        for ent in j.get('entities') or []:
            v = ent.get('vcardArray')
            if v and isinstance(v, list) and len(v) > 1:
                score += min(10, len(v[1]))
    if j.get('name') or j.get('ldhName') or j.get('handle'):
        score += 20
    if j.get('startAddress') and j.get('endAddress'):
        score += 8
    if j.get('cidr'):
        score += 8
    if j.get('country'):
        score += 4
    if j.get('links'):
        score += 3
    return score

def choose_best_rdap(net_json, ip_json):
    for j in (net_json, ip_json):
        if j and j.get('source') == 'iana-registry':
            return j
    s_net, s_ip = rdap_score(net_json), rdap_score(ip_json)
    return net_json if s_net >= s_ip else ip_json

def rdap_summary_from_json(j):
    if not j:
        return None
        
    s = {'handle': j.get('handle') or j.get('name') or j.get('ldhName')}
    
    if 'startAddress' in j and 'endAddress' in j:
        s['network'] = f"{j['startAddress']} - {j['endAddress']}"
    else:
        s['network'] = j.get('cidr') or j.get('name')

    org, abuse_emails, contacts = None, [], []
    for ent in j.get('entities') or []:
        roles = [r.lower() for r in (ent.get('roles') or [])]
        is_registrant = any(r in ('registrant', 'registrant/owner') for r in roles)
        v = ent.get('vcardArray')
        
        if v and isinstance(v, list) and len(v) > 1:
            for entry in v[1]:
                if isinstance(entry, list) and len(entry) >= 4:
                    key, value = entry[0].lower(), entry[3]
                    if key in ('fn', 'org') and (is_registrant or not org):
                        org = value
                    if key == 'email' and isinstance(value, str):
                        contacts.append(value)
                        if 'abuse' in value.lower():
                            abuse_emails.append(value)

    if not org:
        for ent in j.get('entities') or []:
            org = ent.get('handle') or ent.get('objectClassName')
            if org:
                break
        if not org:
            for r in j.get('remarks') or []:
                if t := r.get('description') or r.get('title'):
                    org = str(t[0] if isinstance(t, list) else t)
                    break

    s['org'] = org
    if abuse_emails:
        s['abuse'] = abuse_emails[0]
    elif contacts:
        s['contact'] = contacts[0]
        
    if country := j.get('country'):
        s['country'] = translate_country(country)
        
    if links := [L.get('href') for L in j.get('links') or [] if L.get('href')]:
        s['sources'] = links + ([str(j['port43'])] if j.get('port43') else [])

    return s

for octet, info in IANA_IPV4_REGISTRY.items():
    prefix = f"{octet}.0.0.0/8"
    rdap_cache.put(f"net:{prefix}", {
        "handle": prefix,
        "cidr": prefix,
        "remarks": [{"description": info.get("designation")}],
        "status": info.get("status"),
        "source": "iana-registry"
    })

_worker_thread = threading.Thread(target=rdap_worker, daemon=True)
_worker_thread.start()