from typing import Optional
import aiohttp
import asyncio

from constants import REPORT_TYPES
from report_info import parse_report_data


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))


async def get_report_info(
    session: aiohttp.ClientSession, token: str, type: REPORT_TYPES
):
    url = f"https://discord.com/api/v9/reporting/menu/{type}"
    headers = {
        # 'accept': '*/*',
        # 'accept-language': 'en-US,en;q=0.9',
        "authorization": token,
        # 'cache-control': 'no-cache',
        # 'cookie': '__dcfduid=296a70808cb711efa33aa5ce7826713e; __sdcfduid=296a70818cb711efa33aa5ce7826713e2220dc06b2eb8c208edfde14f367b0f2c5fe587ca8f905c55ca37b745617b996; __cfruid=a8cdf270069ee0e3b7b40b3a7b608f4214a1e934-1729190377; _cfuvid=KZ1diPLMADEnHp5mxibKjcJWEyDKvzFat4fv6S5uqYA-1729190377359-0.0.1.1-604800000; cf_clearance=jMpvORs34zECUlBeikh4gmk8H_29NDH.VsT.5lH1_B0-1729190379-1.2.1.1-5eNmjlsPddMPYwJZi.NW0fwV8_r6ZZ7rbWVwKRaS0IBlkJYARYugrUbvz1JX8dasYszMi.d5tbBWEoL8BoGBToOHs8NL1ApwvPBGLX81XMrIcNCcJHvctsjxlUPEOhkt2wBuod6sQrLW6VPz8.izcxUZ_Fl1Ap2kKH1MMdAAB.GfBMukxmhhSyq2nPfCnB1Cb0F69Hue3Wp3Lw2XiBgBWiTiBQfb73Gjjd4IEuMaHXAJnpxJj28Lr_34yHVAMLh6mI9cF6BOZaugP3VTq4bg37XXQ0oxdnF_baB3E_tmzXIw68vOv3D6i879T7WgyMOYVXnSVmKz1mFdbAgrOPMR9lWQI9X7fEwqkYAxOT_qa6vJI.oVnjDHIhQMINHPylpd',
        # 'pragma': 'no-cache',
        # 'priority': 'u=1, i',
        # 'referer': 'https://discord.com/channels/1264992393615380690/1265298252174065697',
        # 'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        # 'sec-ch-ua-mobile': '?0',
        # 'sec-ch-ua-platform': '"Linux"',
        # 'sec-fetch-dest': 'empty',
        # 'sec-fetch-mode': 'cors',
        # 'sec-fetch-site': 'same-origin',
        # 'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        # 'x-debug-options': 'bugReporterEnabled',
        # 'x-discord-locale': 'en-US',
        # 'x-discord-timezone': 'America/New_York',
        # 'x-super-properties': 'eyJvcyI6IkxpbnV4IiwiYnJvd3NlciI6IkNocm9tZSIsImRldmljZSI6IiIsInN5c3RlbV9sb2NhbGUiOiJlbi1VUyIsImJyb3dzZXJfdXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChYMTE7IExpbnV4IHg4Nl82NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEyOC4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTI4LjAuMC4wIiwib3NfdmVyc2lvbiI6IiIsInJlZmVycmVyIjoiIiwicmVmZXJyaW5nX2RvbWFpbiI6IiIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjozMzYxODUsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGx9'
    }

    async with session.get(url, headers=headers) as response:
        json = await response.json()
        return parse_report_data(json)


def parse_message_link(url: str) -> tuple[str, str, str]:
    #  https://discord.com/channels/617069298980093963/617069514449748120/1241696990820176012
    # split the last three / and return the tuple

    elements = url.split("/")[-3:]
    return (elements[-3], elements[-2], elements[-1])


async def get_messages(
    session: aiohttp.ClientSession,
    token: str,
    channel_id: str,
    offset: Optional[int] = None,
):
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages/search"
    if offset != None:
        url += f"?offset={offset}"
    headers = {
        # 'accept': '*/*',
        # 'accept-language': 'en-US,en;q=0.9',
        "authorization": token,
        # 'cache-control': 'no-cache',
        # 'cookie': '__dcfduid=296a70808cb711efa33aa5ce7826713e; __sdcfduid=296a70818cb711efa33aa5ce7826713e2220dc06b2eb8c208edfde14f367b0f2c5fe587ca8f905c55ca37b745617b996; __cfruid=a8cdf270069ee0e3b7b40b3a7b608f4214a1e934-1729190377; _cfuvid=KZ1diPLMADEnHp5mxibKjcJWEyDKvzFat4fv6S5uqYA-1729190377359-0.0.1.1-604800000; cf_clearance=jMpvORs34zECUlBeikh4gmk8H_29NDH.VsT.5lH1_B0-1729190379-1.2.1.1-5eNmjlsPddMPYwJZi.NW0fwV8_r6ZZ7rbWVwKRaS0IBlkJYARYugrUbvz1JX8dasYszMi.d5tbBWEoL8BoGBToOHs8NL1ApwvPBGLX81XMrIcNCcJHvctsjxlUPEOhkt2wBuod6sQrLW6VPz8.izcxUZ_Fl1Ap2kKH1MMdAAB.GfBMukxmhhSyq2nPfCnB1Cb0F69Hue3Wp3Lw2XiBgBWiTiBQfb73Gjjd4IEuMaHXAJnpxJj28Lr_34yHVAMLh6mI9cF6BOZaugP3VTq4bg37XXQ0oxdnF_baB3E_tmzXIw68vOv3D6i879T7WgyMOYVXnSVmKz1mFdbAgrOPMR9lWQI9X7fEwqkYAxOT_qa6vJI.oVnjDHIhQMINHPylpd',
        # 'pragma': 'no-cache',
        # 'priority': 'u=1, i',
        # 'referer': 'https://discord.com/channels/1264992393615380690/1265298252174065697',
        # 'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        # 'sec-ch-ua-mobile': '?0',
        # 'sec-ch-ua-platform': '"Linux"',
        # 'sec-fetch-dest': 'empty',
        # 'sec-fetch-mode': 'cors',
        # 'sec-fetch-site': 'same-origin',
        # 'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        # 'x-debug-options': 'bugReporterEnabled',
        # 'x-discord-locale': 'en-US',
        # 'x-discord-timezone': 'America/New_York',
        # 'x-super-properties': 'eyJvcyI6IkxpbnV4IiwiYnJvd3NlciI6IkNocm9tZSIsImRldmljZSI6IiIsInN5c3RlbV9sb2NhbGUiOiJlbi1VUyIsImJyb3dzZXJfdXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChYMTE7IExpbnV4IHg4Nl82NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEyOC4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTI4LjAuMC4wIiwib3NfdmVyc2lvbiI6IiIsInJlZmVycmVyIjoiIiwicmVmZXJyaW5nX2RvbWFpbiI6IiIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjozMzYxODUsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGx9'
    }

    while True:
        async with session.get(url, headers=headers) as resp:
            if resp.ok:
                return await resp.json()

            elif resp.status == 429:
                json = await resp.json()
                await asyncio.sleep(json["retry_after"])

            else:
                print((await resp.json()))
                return {}


async def check_message_exists(
    session: aiohttp.ClientSession, token: str, msg_link: str
):
    _, channel_id, message_id = parse_message_link(msg_link)
    raw_json = await get_messages(session, token, channel_id)
    if raw_json == {}:
        return False

    total_results = raw_json.get("total_results", 0)
    attempts = -(-total_results // 25)

    jsons = await asyncio.gather(
        *(
            get_messages(session, token, channel_id, offset=i * 25)
            for i in range(0, attempts)
        )
    )

    # Discord for some reason has every message in its own list
    messages = [m for json in jsons for msg in json.get("messages", []) for m in msg]
    for msg in messages:
        if msg.get("id", "0") == message_id:
            return True
    return False


if __name__ == "__main__":

    async def main():
        session = aiohttp.ClientSession()
        token = "token"

        exist = await check_message_exists(
            session,
            token,
            "https://discord.com/channels/@me/1278485998170538004/1296179491756048455",
        )
        print(exist)
        await session.close()

    asyncio.run(main())
