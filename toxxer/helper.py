import base64
import json
import ssl
import random
# username    = cfg.username
# password    = cfg.password
# invite      = cfg.d_inv
# fingerprint = cfg.d_fingerprint


username = ""
password = ""
invite = ""
fingerprint = "846929804438667274.7Yk69o4NpGUWKRL9LtQdkIllP0M"



def create_context():
    ctx = ssl.SSLContext()
    CIPHERS = 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA:AES256-SHA' 
    ctx.minimum_version = ssl.TLSVersion.TLSv1
    ctx.maximum_version = ssl.TLSVersion.TLSv1_2
    ctx.set_alpn_protocols(["h2", "http/1.1"]) 
    ctx.set_ciphers(CIPHERS)
    return ctx


async def create_register_payload(email: str) -> dict:
    return {
        "fingerprint":fingerprint,
        "username":username,
        "email": email,
        "password": password,
        "consent": True,
        "date_of_birth":"1999-03-23",
        "invite": invite,
        "gift_code_sku_id":None,
        #"captcha_key": await solver.single_solve_captcha()
        }


def get_super_prop(os, browser, useragent, browser_version, os_version, client_build):
    return {
        "os": os,
        "browser": browser,
        "device": "",
        "browser_user_agent": useragent,
        "browser_version": browser_version,
        "os_version": os_version,
        "referrer": "",
        "referring_domain": "",
        "referrer_current": "",
        "referring_domain_current": "",
        "release_channel": "stable",
        "client_build_number": client_build,
        "client_event_source": None
    }


def get_basic_headers_with_super_properties(uc):
        if "Windows" in uc:
            os = "Windows"
            osver = "10"
        elif "Linux" in uc:
            os = "Linux"
            osver = "X11"
        else:
            os = "Apple"
            osver = "10_9_3"
        if "Chrome" in uc:
            browser = "Chrome"
        elif "Firefox" in uc:
            browser = "Firefox"
        browserver = ' '.join(uc.split('/')[3:4]).split(' ')[0]
        superProp = get_super_prop(os, browser, uc, browserver, osver, 84451)
        return {
            'user-agent': uc,
            'Host': 'discord.com',
            'Accept': '*/*',
            'Accept-Language': 'en-US',
            'Content-Type': 'application/json',
            'DNT': '1',
            'Connection': 'keep-alive',
            'X-Super-Properties': base64.b64encode(json.dumps(superProp, separators=(',', '.')).encode()).decode(),
            'X-Fingerprint': '843983133426188298.POtVGUkz77y6aDowN6xTPvVvigQ'
        }


def get_linux_useragent():
    choices = [
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36",
        "Mozilla/5.0 (X11; Datanyze; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.4) Gecko/20100625 Gentoo Firefox/3.6.4",
        ]
    return choices[random.randint(0, len(choices) - 1)]