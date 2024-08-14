import datetime
import random
import time

from sys import stderr
from pathlib import Path
from typing import List, Dict, Any

from loguru import logger
from web3 import Account, Web3
from eth_account.signers.local import LocalAccount

from config import log_file


def load_logger():
    # LOGGING SETTING
    logger.remove()
    logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <white>{message}</white>")
    logger.add(log_file + f"_{datetime.datetime.now().strftime('%Y%m%d')}.log",
               format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <white>{message}</white>")


def load_accounts_from_keys(path: str) -> List[LocalAccount]:
    file = Path(path).open()
    return [Account.from_key(line.replace("\n", "")) for line in file.readlines()]


def load_wallets(path: str) -> List[str]:
    file = Path(path).open()
    return [line.replace("\n", "") for line in file.readlines()]


class MakePause(BaseException):
    def __init__(self, timer: int = None):
        self.timer = timer


def _create_transaction_params(account: LocalAccount, w3: Web3, eip1559: bool, gas: int = 0, value: int = 0) -> Dict:
    tx_params = {
        "from": account.address,
        "value": value,
        'chainId': w3.eth.chain_id,
        "nonce": w3.eth.get_transaction_count(account.address),
    }

    if eip1559:
        base_fee = w3.eth.gas_price

        if w3.eth.chain_id == 324:  # zksync
            max_priority_fee_per_gas = 1_000_000
        elif w3.eth.chain_id == 250:  # Fantom
            max_priority_fee_per_gas = int(base_fee / 4)
        else:
            max_priority_fee_per_gas = w3.eth.max_priority_fee

        if w3.eth.chain_id == 42170:  # Arb Nova
            base_fee = int(base_fee * 1.25)

        # if w3.eth.chain_id == 42161:  # Arb
        #     tx_params['gas'] = random.randint(320_000, 340_000)

        max_fee_per_gas = int(base_fee * 1.05) + max_priority_fee_per_gas
        tx_params['maxPriorityFeePerGas'] = max_priority_fee_per_gas
        tx_params['maxFeePerGas'] = max_fee_per_gas
        tx_params['type'] = '0x2'

    else:
        if w3.eth.chain_id == 56:  # 'BNB Chain'
            tx_params['gasPrice'] = w3.to_wei(round(random.uniform(1.2, 1.5), 1), 'gwei')
        elif w3.eth.chain_id == 1284:  # 'Moonbeam'
            tx_params['gasPrice'] = int(w3.eth.gas_price * 1.5)
        elif w3.eth.chain_id == 1285:  # 'Moonriver'
            tx_params['gasPrice'] = int(w3.eth.gas_price * 1.5)
        else:
            tx_params['gasPrice'] = w3.eth.gas_price

    if gas != 0:
        tx_params['gas'] = gas

    return tx_params


def send_transaction(raw_tx: Any, w3: Web3, explorer: str, account: LocalAccount, eip1559: bool, gas: int = 0,
                     value: int = 0):
    transaction_params = _create_transaction_params(account=account, w3=w3, eip1559=eip1559, gas=gas, value=value)
    tx = raw_tx.build_transaction(transaction_params)
    if tx['gas'] == 0:
        estimate_gas = int(w3.eth.estimate_gas(tx) * 1.05)
        tx.update({'gas': estimate_gas})
    signed_tx = w3.eth.account.sign_transaction(tx, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    logger.info(f"Tx: {explorer}tx/{tx_hash.hex()}")
    return tx_hash


def check_tx_status(w3: Web3, tx_hash):
    tx_status = get_tx_status(w3=w3, tx_hash=tx_hash)
    if tx_status != 1:
        return False
    return True


def get_tx_status(w3: Web3, tx_hash) -> int:
    time.sleep(20)
    status_ = None
    tries = 0
    while not status_:
        try:
            status_ = w3.eth.get_transaction_receipt(tx_hash)
        except:
            logger.info('Still trying to get tx status')
            tries += 1
            time.sleep(10)
            if tries == 5:
                status_ = 2

    status = status_["status"]
    logger.info(f"Tx status: {status}")

    if status not in [0, 1]:
        raise Exception("could not obtain tx status in 60 seconds")
    else:
        return status
