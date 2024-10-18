import time
import aiohttp

from .report_info import (
    ReportData,
    create_guild_response,
    create_message_response,
    create_user_response,
    search_leaf_breadcrumb,
)
from .http_setup import get_basic_headers_with_super_properties, get_linux_useragent



class AbstractToxClient:
    def __init__(self, client: aiohttp.ClientSession):
        self._client = client
        
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
        
    def get_msg_report_payload(self, reason: str, cid: str, mid: str):
        if self._r_msg_d is None:
            raise ValueError("Message report data not loaded")
        
        wanted_node = search_leaf_breadcrumb(self._r_msg_d, reason)
        if wanted_node is None:
            raise ValueError(f"Invalid reason: {reason}")
    
        return create_message_response(self._r_msg_d, wanted_node.id, cid, mid)
    
    def get_user_report_payload(self, reason: str, gid: str, uid: str):
        if self._r_user_d is None:
            raise ValueError("User report data not loaded")
        
        wanted_node = search_leaf_breadcrumb(self._r_user_d, reason)
        if wanted_node is None:
            raise ValueError(f"Invalid reason: {reason}")

        return create_user_response(self._r_user_d, wanted_node.id, gid, uid)
    
    def get_guild_report_payload(self, reason: str, gid: str):
        """
        Deprecated.
        """
        if self._r_guild_d is None:
            raise ValueError("Guild report data not loaded")
        
        wanted_node = search_leaf_breadcrumb(self._r_guild_d, reason)
        if wanted_node is None:
            raise ValueError(f"Invalid reason: {reason}")
        
        return create_guild_response(self._r_guild_d, wanted_node.id, gid)
    
        
    async def _send_report(self, headers:dict, report_type: str, payload: dict, retries: int):
        url = f"https://discord.com/api/v9/reporting/{report_type}"

        for _ in range(retries):
            async with self._client.post(
                url, headers=headers, json=payload
            ) as response:
                print(response.status)
                if response.status == 200:
                    return await response.json()

                elif response.status == 429:
                    resp = await response.json()
                    time = resp["retry_after"]
                    await asyncio.sleep(time)
                else:
                    # allow the fail out.
                    return await response.json()

class ToxClient(AbstractToxClient):
    def __init__(self, client: aiohttp.ClientSession, token: str, max_retries=2):
        super().__init__(client)

        self._token = token
        self._max_retries = max_retries
        self._headers = self._setup_default_headers()

        # for caching purposes, re-use the same headers as much as possible.

    def _setup_default_headers(self, ua=None) -> dict[str, str]:
        if ua is None:
            ua = get_linux_useragent()  # lazy, replace with more robust UA code.

        headers = get_basic_headers_with_super_properties(ua)
        return headers

    async def report_msg(self, cid: str, mid: str, reason: str):
        payload = super().get_msg_report_payload(reason, cid, mid)
        return await self._send_report("message", payload)

    async def report_user(self, gid: str, uid: str, reason: str):
        payload = super().get_user_report_payload(reason, gid, uid)
        return await self._send_report("user", payload)

    async def report_guild(self, gid: str, reason: str):
        """
        Deprecated. Do not use.
        """
        payload = super().get_guild_report_payload(reason, gid)
        return await self._send_report("guild", payload)

    async def _send_report(self, report_type: str, payload: dict):
        headers = self._headers
        headers["authorization"] = self._token
        return await super()._send_report(headers, report_type, payload, self._max_retries)




class MultiToxClient(ToxClient):
    def __init__(self, client: aiohttp.ClientSession, tokens: list[str], max_retries=2, max_concurrent_reports=50, max_report_queue_size=100):
        super().__init__(client, tokens[0], max_retries=max_retries) # token[0] should never be used.
        
        self._max_retries = max_retries
        self._headers = self._setup_default_headers()
        
        self._tokens = tokens
        self._tokens_ratelimited_map: dict[str, float] = {}
        self._token_idx = 0
        
        self.report_queue = asyncio.Queue(maxsize=max_report_queue_size)
        
        self.flag = asyncio.Event()
        
        self.worker_list = []
        self._report_tracker = {}
    
        self._start_workers(max_concurrent_reports)
        
    def shutdown(self):
        self.flag.set()
        
    def _get_token(self):
        token = self._tokens[self._token_idx]
        self._token_idx = (self._token_idx + 1) % len(self._tokens)
        return token        
    
    async def _get_token_no_rate_limit(self):
        token = self._get_token()
        
        # have a fallback in case all are rate limited.
        checked_amt = 0
        max = len(self._tokens)
        while token in self._tokens_ratelimited_map:
            token = self._get_token()
            checked_amt += 1
            if checked_amt >= max:
                break
            
        if checked_amt >= max:
            # locate the token with the least time left.
            # all of the values will have ratelimits, so just get the smallest.
            lowest_token = min(self._tokens_ratelimited_map, key=lambda x: self._tokens_ratelimited_map.get(x, 0))
            lowest_time = self._tokens_ratelimited_map[lowest_token]
            await asyncio.sleep(lowest_time - time.time())
            self._tokens_ratelimited_map.pop(lowest_token, None)

            token = lowest_token
        return token
        
    def token_ratelimited(self, token: str, retry_after: float):
        """
        time is in seconds, has miliseconds.
        """
        current = time.time()
        self._tokens_ratelimited_map[token] = current + retry_after
        
        async def _remove_ratelimit(token: str, after: float):
            await asyncio.sleep(after)
            self._tokens_ratelimited_map.pop(token, None)
            
        # schedule removal.
        asyncio.create_task(_remove_ratelimit(token, retry_after))
    
        
    def _start_workers(self, amt: int):
        self.worker_list = []
        for _ in range(amt):
            self.worker_list.append(asyncio.create_task(self.__report_worker()))
        
   
    async def __report_worker(self): 
        # even if there are elements in queue, bail if (close) flag is set.
        while not self.flag.is_set():
            try:
                type, payload, counter = await asyncio.wait_for(self.report_queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                if self.flag.is_set():
                    break
                continue
                    
            await self._send_report(type, payload)
            counter["value"] += 1
            self.report_queue.task_done()
        
    
    # for caching purposes, re-use the same headers as much as possible.
    def _setup_default_headers(self, ua=None) -> dict[str, str]:
        if ua is None:
            ua = get_linux_useragent()
            
        headers = get_basic_headers_with_super_properties(ua)
        return headers
    
    async def report_msg(self, cid: str, mid: str, reason: str, amt=-1):
        if amt == -1:
            amt = len(self._tokens)
            
        payload = self.get_msg_report_payload(reason, cid, mid)
        
        counter = {"value": 0}
        
        for _ in range(amt):
            await self.report_queue.put(("message", payload, counter))
            
        while counter["value"] < amt:
            await asyncio.sleep(0.5)
        
    
    async def _send_report(self, report_type: str, payload: dict):
        headers = self._headers
        headers["authorization"] = await self._get_token_no_rate_limit()
        # call AbstractToxClient's _send_report
        url = f"https://discord.com/api/v9/reporting/{report_type}"
        for i in range(self._max_retries):
            async with self._client.post(
                url, headers=headers, json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()

                elif response.status == 429:
                    resp = await response.json()
                    time = resp["retry_after"]
                    self.token_ratelimited(headers["authorization"], time)
                    headers["authorization"] = await self._get_token_no_rate_limit()
                else:
                    # allow the fail out.
                    return await response.json()
        

async def single_test():
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

    gid, cid, mid = parse_message_link(
        "https://discord.com/channels/1296926530001440828/1296926530588381240/1296927200783630346"
    )
    # Example usage
    resp = await toxxer.report_msg(cid, mid, "Spam")
    
 
    print(resp)
    
    
async def multi_test():
    from dotenv import load_dotenv
    import os
    from .utils import get_report_info, parse_message_link

    load_dotenv()

    client = aiohttp.ClientSession()
    token_file = os.environ.get("TOKEN_LIST_FILE")
    
    if token_file is None:
        print("Token file not found")
        return
    
    with open(token_file, "r") as f:
        tokens = f.read().splitlines()
        

    toxxer = MultiToxClient(client, tokens, max_retries=2)
    token = tokens[0]
    
    # only needs to be loaded once, and is passed into every tox client.
    msg_d = await get_report_info(client, token, "message")
    user_d = await get_report_info(client, token, "user")
    guild_d = await get_report_info(client, token, "guild")

    toxxer.load_message_report_data(msg_d)
    toxxer.load_user_report_data(user_d)
    toxxer.load_guild_report_data(guild_d)

    gid, cid, mid = parse_message_link(
       "https://discord.com/channels/1295119921755324583/1295123933670015039/1296650113506349087"
    )
    # Example usage
    resp = await toxxer.report_msg(cid, mid, "Spam")
    print(resp)
    
    await asyncio.sleep(10)
    toxxer.shutdown()
    await client.close()
    
    


if __name__ == "__main__":
    import asyncio

    asyncio.run(multi_test())
