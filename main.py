import os
import requests
import random
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from loguru import logger
import random

logger.remove()
logger.add(
    "revolving_checker.log",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
    rotation="1 day"
)
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
    colorize=True
)

class ProxyManager:
    def __init__(self, proxy_file):
        self.proxies = self.load_proxies(proxy_file)
        
    def load_proxies(self, proxy_file):
        with open(proxy_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    def get_random_proxy(self):
        if not self.proxies:
            return None
        return random.choice(self.proxies)

class WalletManager:
    def __init__(self, wallet_file):
        self.wallets = self.load_wallets(wallet_file)

    def load_wallets(self, wallet_file):
        with open(wallet_file, 'r') as f:
            wallets = []
            for line in f:
                private_key = line.strip()
                if private_key.startswith('0x'):
                    private_key = private_key[2:]
                if private_key:
                    wallets.append(private_key)
            return wallets

    def get_address_from_private_key(self, private_key):
        if private_key.startswith('0x'):
            private_key = private_key[2:]
        account = Account.from_key(private_key)
        return account.address

class RevolvingGamesAPI:
    BASE_URL = "https://projectnova-backend.revolvinggames.com"
    
    def __init__(self, proxy):
        self.proxy = proxy
        self.session = self.create_session()

    def create_session(self):
        session = requests.Session()
        if self.proxy:
            session.proxies = {'http': self.proxy, 'https': self.proxy}
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "ru,ru-RU;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://hatchlings.revolvinggames.com",
            "Referer": "https://hatchlings.revolvinggames.com/",
            "Content-Type": "text/plain;charset=UTF-8"
        })
        return session

    def login(self, wallet_address, private_key):
        url = f"{self.BASE_URL}/games/dp/login"
        response = None
        
        try:
            message = "Welcome to Hatchlings!\n\nClick to sign in and accept the Hatchlings and Revolvinggames Terms of Service and Privacy Policy.\n\nThis request will not trigger a blockchain transaction or cost any gas fees."
            message_hash = encode_defunct(text=message)
            signed_message = Account.sign_message(message_hash, private_key)
            
            payload = {
                "signatureHash": signed_message.signature.hex()
            }

            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            initial_token = response.json().get('jwtToken')
            if not initial_token:
                return None

            import jwt
            token_data = jwt.decode(initial_token, options={"verify_signature": False})
            user_id = token_data.get('id')

            if not user_id:
                logger.warning(f"Could not extract user ID from token for wallet {wallet_address}")
                return None

            nda_url = f"{self.BASE_URL}/users/{user_id}/games/dp/nda"
            self.session.headers.update({"Authorization": f"Bearer {initial_token}"})
            
            nda_response = self.session.post(nda_url, timeout=10)
            nda_response.raise_for_status()

            final_token = nda_response.json().get('jwtToken')
            if final_token:
                logger.success(f"Successfully completed NDA for wallet {wallet_address}")
                return final_token
            
            return None

        except Exception as e:
            logger.warning(f"Login attempt failed for {wallet_address}: {str(e)}")
            if response:
                logger.warning(f"Response content: {response.text}")
            return None

class AccountChecker:
    def __init__(self, wallet_manager, proxy_manager):
        self.wallet_manager = wallet_manager
        self.proxy_manager = proxy_manager
        self.retry_count = 3
        self.delay_between_retries = 1

    def check_account(self, private_key):
        address = self.wallet_manager.get_address_from_private_key(private_key)
        
        for attempt in range(self.retry_count):
            proxy = self.proxy_manager.get_random_proxy()
            try:
                api = RevolvingGamesAPI(proxy)
                token = api.login(address, private_key)
                
                if token:
                    result = f"{private_key}:{token}"
                    logger.success(f"Successful login: {result}")
                    return result
                    
                if attempt < self.retry_count - 1:
                    time.sleep(self.delay_between_retries)
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {address}: {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.delay_between_retries)
                continue
                
        logger.error(f"All attempts failed for {address}")
        return None

    def check_all_wallets(self):
        results = []
        max_workers = 10
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_wallet = {executor.submit(self.check_account, private_key): private_key 
                              for private_key in self.wallet_manager.wallets}
            
            for future in as_completed(future_to_wallet):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error processing wallet: {str(e)}")
        
        return results

def main():
    proxy_manager = ProxyManager('proxies.txt')
    wallet_manager = WalletManager('wallets.txt')
    account_checker = AccountChecker(wallet_manager, proxy_manager)

    logger.info("Starting Revolving Games account check...")
    results = account_checker.check_all_wallets()

    with open('result.txt', 'w') as f:
        for result in results:
            f.write(f"{result}\n")

    logger.success(f"Check completed. Results saved to result.txt. Total successful accounts: {len(results)}")

if __name__ == "__main__":
    main()
