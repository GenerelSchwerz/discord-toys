import aiohttp

from .report_info import ReportData, create_guild_response, create_message_response, create_user_response, search_leaf_breadcrumb
from .http_setup import get_basic_headers_with_super_properties, get_linux_useragent


class ToxClient:
    def __init__(
        self, client: aiohttp.ClientSession, token: str, max_retries=2
    ):
        self._client = client
        self._token = token
        self._max_retries = max_retries
        self._headers = self._setup_default_headers()

        # for caching purposes, re-use the same headers as much as possible.

    def _setup_default_headers(self, ua=None) -> dict[str, str]:
        if ua is None:
            ua = get_linux_useragent()  # lazy, replace with more robust UA code.

        headers = get_basic_headers_with_super_properties(ua)
        return headers
    
    def load_message_report_data(self, report_data: ReportData):
        if report_data.name != "message":
            raise ValueError("Invalid report data type")
        
        self._r_msg_d = report_data
        
    def load_user_report_data(self, report_data: ReportData):
        if report_data.name != "user":
            raise ValueError("Invalid report data type")
        
        self._r_user_d = report_data
        
    def load_guild_report_data(self, report_data: ReportData):
        """
        Deprecated. 
        """
        if report_data.name != "guild":
            raise ValueError("Invalid report data type")
        
        self._r_guild_d = report_data
        
    def report_msg(self, cid: str, mid: str, reason: str):
        wanted_node = search_leaf_breadcrumb(self._r_msg_d, reason)
        if wanted_node is None:
            raise ValueError(f"Invalid reason: {reason}")
        
        payload = create_message_response(self._r_msg_d, wanted_node.id, cid, mid)
        return self._send_report("message", payload)
    
    def report_user(self, gid: str, uid: str, reason: str):
        wanted_node = search_leaf_breadcrumb(self._r_user_d, reason)
        if wanted_node is None:
            raise ValueError(f"Invalid reason: {reason}")
        
        payload = create_user_response(self._r_user_d, wanted_node.id, gid, uid)
        return self._send_report("user", payload)
    
    def report_guild(self, gid: str, reason: str):
        """
        Deprecated. Do not use.
        """
        wanted_node = search_leaf_breadcrumb(self._r_guild_d, reason)
        if wanted_node is None:
            raise ValueError(f"Invalid reason: {reason}")
        
        payload = create_guild_response(self._r_guild_d, wanted_node.id, gid)
        return self._send_report("guild", payload)
    
    
    async def _send_report(self, report_type: str, payload: dict):
        url = f"https://discord.com/api/v9/reporting/{report_type}"
        headers = self._headers
        headers["authorization"] = self._token
            
        for _ in range(self._max_retries):
            async with self._client.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                
                elif response.status == 429:
                    resp = await response.json()
                    time = resp["retry_after"]
                    await asyncio.sleep(time)
                else:
                    # allow the fail out.
                    return await response.json()
   
 

async def main():
    from dotenv import load_dotenv
    import os
    from .utils import get_report_info, parse_message_link
    load_dotenv()
    
    client = aiohttp.ClientSession()
    token = os.environ.get("TOKEN")
    
    if token is None:
        print("Token not found")
        return
    
    toxxer = ToxClient(client, token)
    
    # only needs to be loaded once, and is passed into every tox client.
    msg_d = await get_report_info(client, token, "message")
    user_d = await get_report_info(client, token, "user")
    guild_d = await get_report_info(client, token, "guild")
    
    toxxer.load_message_report_data(msg_d)
    toxxer.load_user_report_data(user_d)
    toxxer.load_guild_report_data(guild_d)
    
    gid, cid, mid = parse_message_link("https://discord.com/channels/1295119921755324583/1295123951168520328/1296911412882571454")
    # Example usage
    resp = await toxxer.report_msg(cid, mid, "Spam")
    print(resp)
    
    
    
    

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())