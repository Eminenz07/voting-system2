import urllib.request as r
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    req_login = r.Request(
        'https://voting-system2-production.up.railway.app/api/auth/login/',
        data=b'{"matric":"ADMIN001","password":"admin123"}',
        headers={'Content-Type': 'application/json'}
    )
    res_login = r.urlopen(req_login, context=ctx)
    token = json.loads(res_login.read().decode())['token']
    
    req_api = r.Request(
        'https://voting-system2-production.up.railway.app/api/elections/1/ballot/',
        headers={'Authorization': 'Token ' + token}
    )
    res_api = r.urlopen(req_api, context=ctx)
    print("SUCCESS", res_api.status)
    print(res_api.read().decode()[:500])
except r.HTTPError as e:
    print("HTTP ERROR", e.code)
    try:
        body = e.read().decode()
        # Look for the exact exception in the Django HTML
        import re
        match = re.search(r'(?i)<title>(.*?)</title>', body)
        if match:
            print("Title:", match.group(1))
        
        match2 = re.search(r'(?i)Exception Value:</th>\s*<td><pre>(.*?)</pre>', body)
        if match2:
            print("Error:", match2.group(1))
        else:
            print("Full body excerpt:", body[:1000])
    except Exception as ie:
        print("Inner error", ie)
