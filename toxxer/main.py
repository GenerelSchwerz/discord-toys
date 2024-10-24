import asyncio
from src import (
    create_response,
    create_message_response,
    create_user_response,
    dfs_print,
    parse_report_data,
    search_leaf_breadcrumb,
)
from src.types import REPORT_TYPES
from src.utils import get_report_info, parse_message_link
import aiohttp

from dotenv import load_dotenv


load_dotenv()


async def send_report(
    token: str,
    type: REPORT_TYPES,
    payload: dict,
):
    url = f"https://discord.com/api/v9/reporting/{type}"

    headers = {
        # "accept": "*/*",
        # "accept-language": "en-US,en;q=0.9",
        "authorization": token,
        # "cache-control": "no-cache",
        # "content-type": "application/json",
        # # "cookie": "__dcfduid=296a70808cb711efa33aa5ce7826713e; __sdcfduid=296a70818cb711efa33aa5ce7826713e2220dc06b2eb8c208edfde14f367b0f2c5fe587ca8f905c55ca37b745617b996; __cfruid=a8cdf270069ee0e3b7b40b3a7b608f4214a1e934-1729190377; _cfuvid=KZ1diPLMADEnHp5mxibKjcJWEyDKvzFat4fv6S5uqYA-1729190377359-0.0.1.1-604800000; cf_clearance=jMpvORs34zECUlBeikh4gmk8H_29NDH.VsT.5lH1_B0-1729190379-1.2.1.1-5eNmjlsPddMPYwJZi.NW0fwV8_r6ZZ7rbWVwKRaS0IBlkJYARYugrUbvz1JX8dasYszMi.d5tbBWEoL8BoGBToOHs8NL1ApwvPBGLX81XMrIcNCcJHvctsjxlUPEOhkt2wBuod6sQrLW6VPz8.izcxUZ_Fl1Ap2kKH1MMdAAB.GfBMukxmhhSyq2nPfCnB1Cb0F69Hue3Wp3Lw2XiBgBWiTiBQfb73Gjjd4IEuMaHXAJnpxJj28Lr_34yHVAMLh6mI9cF6BOZaugP3VTq4bg37XXQ0oxdnF_baB3E_tmzXIw68vOv3D6i879T7WgyMOYVXnSVmKz1mFdbAgrOPMR9lWQI9X7fEwqkYAxOT_qa6vJI.oVnjDHIhQMINHPylpd",
        # "origin": "https://discord.com",
        # "pragma": "no-cache",
        # "priority": "u=1, i",
        # # 'referer': 'https://discord.com/channels/1264992393615380690/1265298252174065697',
        # "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        # "sec-ch-ua-mobile": "?0",
        # "sec-ch-ua-platform": '"Linux"',
        # "sec-fetch-dest": "empty",
        # "sec-fetch-mode": "cors",
        # "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        # "x-debug-options": "bugReporterEnabled",
        # "x-discord-locale": "en-US",
        # "x-discord-timezone": "America/New_York",
        "x-super-properties": "eyJvcyI6IkxpbnV4IiwiYnJvd3NlciI6IkNocm9tZSIsImRldmljZSI6IiIsInN5c3RlbV9sb2NhbGUiOiJlbi1VUyIsImJyb3dzZXJfdXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChYMTE7IExpbnV4IHg4Nl82NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEyOC4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTI4LjAuMC4wIiwib3NfdmVyc2lvbiI6IiIsInJlZmVycmVyIjoiIiwicmVmZXJyaW5nX2RvbWFpbiI6IiIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjozMzYxODUsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGx9",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            resp_json = await response.json()
            print(resp_json)


async def main():
    import os
    from dotenv import load_dotenv

    load_dotenv()

    token = os.environ.get("TOKEN")
    if token is None:
        print("Token not found")
        return

    client = aiohttp.ClientSession()
    report_type = "message"

    # Run the async function
    # only needs to be ran once.
    report_data = await get_report_info(client, token, report_type)

    dfs_print(report_data)

    wanted_reason = search_leaf_breadcrumb(
        report_data, "spreading fake news or harmful conspiracy theories"
    )

    if wanted_reason is None:
        print("No breadcrumb found")
        return

    if report_type == "message":

        gid, cid, mid = parse_message_link(
            "https://discord.com/channels/1295119921755324583/1295123951168520328/1296722591524061214"
        )
        payload = create_message_response(report_data, wanted_reason.id, cid, mid)
    elif report_type == "user":
        gid, uid = ["1295119921755324583", "922877704200654849"]
        payload = create_user_response(report_data, wanted_reason.id, gid, uid)
    elif report_type == "guild":
        gid = "1295119921755324583"
        payload = create_response(report_data, wanted_reason.id, gid, gid)

    print(payload)

    resp1 = await send_report(token, report_type, payload)

    await client.close()
    return


if __name__ == "__main__":
    asyncio.run(main())
