import time
import random
import requests

from loguru import logger
from config import keys_file, sleep_between_accounts
from modules.helpful_scripts import load_logger, load_accounts_from_keys, MakePause
from modules.based_client import BasedClient


def main_script(account):
    client = BasedClient(account=account)
    # claiming tokens
    return client.claim_tokens()


def start_script():
    accounts = load_accounts_from_keys(keys_file)
    logger.info(f"Started for {len(accounts)} accounts")
    if len(accounts) == 0:
        logger.error(f'Add keys to {keys_file} file')
        return

    time.sleep(1)

    random.shuffle(accounts)
    with open(f'errors/error_wallets_{int(time.time())}.txt', 'w') as error_wallets:
        for account in accounts:

            load_logger()

            logger.info(f'Started for wallet {account.address}')
            random_sleep = random.randint(*sleep_between_accounts)

            try:
                try:
                    if not main_script(account=account):
                        error_wallets.write(f'{account.address}\n')
                except requests.exceptions.ConnectionError as err:
                    logger.info(f'ConnectionError: {err}')
                except ValueError as value:
                    logger.info(f'ValueError: {value}')
                except Exception as err:
                    logger.error(f'Something went wrong with account {account.address} : {err}')
            except:
                error_wallets.write(f'{account.address}\n')

            logger.info(f"Sleeping for {random_sleep} seconds")
            time.sleep(random_sleep)


if __name__ == '__main__':
    start_script()



