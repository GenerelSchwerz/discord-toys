import aiohttp
import asyncio
import os
import time

class DiscordTokenChecker:
    def __init__(self, tokens: list[str], proxies: list[str], semaphore_limit: int = 100, rate_limit_interval: float = 1.0):
        self.tokens = tokens
        self.proxies = proxies
        self.semaphore = asyncio.Semaphore(semaphore_limit)
        self.proxy_index = 0  # For round-robin proxy usage
        self.valid_proxies = proxies.copy()  # Track valid proxies separately
        self.last_request_time = {proxy: 0. for proxy in self.valid_proxies}  # To track last request time per proxy
        self.rate_limit_interval = rate_limit_interval
        
        
    def format_proxy(self, proxy: str) -> str:
        if proxy.startswith('http://'):
            return proxy

        parts = proxy.split(':')
        if len(parts) == 2:
            return f'http://{parts[0]}:{parts[1]}'
        elif len(parts) == 4:
            return f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}'
        else:
            raise ValueError(f'Invalid proxy format: {proxy}')

    def truncate_proxy(self, proxy: str) -> str:
        return (proxy[:30] + '...') if len(proxy) > 30 else proxy

    async def rate_limit(self, proxy: str):
        now = time.time()
        time_since_last_request = now - self.last_request_time[proxy]
        
        if time_since_last_request < self.rate_limit_interval:
            await asyncio.sleep(self.rate_limit_interval - time_since_last_request)
        self.last_request_time[proxy] = time.time()
        
    async def check_token(self, token: str, session: aiohttp.ClientSession, token_index: int):
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json'
        }

        async with self.semaphore:
            while self.valid_proxies:  # Keep checking while there are valid proxies available
                proxy = self.get_next_proxy()
                formatted_proxy = self.format_proxy(proxy)
                # truncated_proxy = self.truncate_proxy(formatted_proxy)

                await self.rate_limit(proxy)  # Ensure rate limiting for this proxy

                # print(f'Checking token {token_index + 1}/{len(self.tokens)} with proxy {truncated_proxy}. '
                #       f'{len(self.valid_proxies)} proxies left.')

                try:
                    async with session.get('https://discord.com/api/v9/users/@me', headers=headers, proxy=formatted_proxy) as response:
                        if response.status == 200:
                            # print(f'Token {token} is valid using proxy {truncated_proxy}.')
                            return token, True
                        else:
                            # print(f'Token {token} is invalid using proxy {truncated_proxy}. Status code: {response.status}')
                            return token, False
                except Exception as e:
                    # print(f'Error checking token {token} with proxy {truncated_proxy}: {e}')
                    self.remove_proxy(proxy)

        print(f'No valid proxies left for token {token}.')
        return token, False

    def get_next_proxy(self) -> str:
        if not self.valid_proxies:
            raise ValueError("No valid proxies available.")
        
        proxy = self.valid_proxies[self.proxy_index % len(self.valid_proxies)]
        self.proxy_index += 1
        return proxy

    def remove_proxy(self, proxy: str):
        print(f'Removing failed proxy: {self.truncate_proxy(proxy)}')
        if proxy in self.valid_proxies:
            self.valid_proxies.remove(proxy)

    async def check_tokens_async_gen(self):
        connector = aiohttp.TCPConnector(ssl=False)

        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [
                asyncio.create_task(self.check_token(token, session, index))
                for index, token in enumerate(self.tokens)
            ]

            # Yield each result as its task completes
            for task in asyncio.as_completed(tasks):
                result = await task
                yield result
                
async def main():
    
    import aiofiles
    
    # Get tokens and proxies from files that are DIRECTLY NEXT to this file.
    token_path = os.path.join(os.path.dirname(__file__), 'tokens.txt')
    proxy_path = os.path.join(os.path.dirname(__file__), 'proxies.txt')
    
    invalid_tokens_path = os.path.join(os.path.dirname(__file__), 'invalid_tokens.txt')
    valid_tokens_path = os.path.join(os.path.dirname(__file__), 'valid_tokens.txt')

    with open(token_path, 'r') as file:
        tokens = file.read().splitlines()

    with open(proxy_path, 'r') as file:
        proxies = file.read().splitlines()

    checker = DiscordTokenChecker(tokens, proxies, semaphore_limit=100, rate_limit_interval=3)

    idx = 0
    
    async with aiofiles.open(invalid_tokens_path, 'w+') as ifile:
        async with aiofiles.open(valid_tokens_path, 'w+') as vfile:
            async for token, status in checker.check_tokens_async_gen():
                idx += 1
                print(f'Token {token} ({idx}/{len(tokens)}) validation result: {"Valid" if status else "Invalid"}')
                if status:
                    await vfile.write(token + '\n')
                    await vfile.flush()
                else:
                    print(f'writing invalid token {token}')
                    await ifile.write(token + '\n')
                    await ifile.flush()
    
if __name__ == '__main__':
    # Run the main function
    asyncio.run(main())
