import json
from pathlib import Path
from loguru import logger
from web3 import Web3
from eth_account.signers.local import LocalAccount
from eth_account.messages import encode_defunct
from modules.basedevo_api import BasedApi
from modules.helpful_scripts import send_transaction, check_tx_status


class BasedClient:
    def __init__(self, account: LocalAccount):
        self.account = account
        self.address = self.account.address
        self.api = BasedApi(self.address)
        self.w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
        self.owned_nfts = None
        self.available_for_claim = None
        self.based_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address('0x32E0f9d26D1e33625742A52620cC76C1130efde6'),
            abi=json.load(Path('files/based_abi.json').open())
        )

    def get_owned_nfts(self) -> None:
        """
        Gets list if nfts numbers from the api and stores them into the self.owned_nfts
        :return: None
        """
        self.owned_nfts = self.api.get_owned_nfts_number()

    def get_available_for_claim_nfts(self) -> None:
        """
        Checks if any nft from the list of self.owned_nfts is available for token claim
        :return: None
        """
        self.available_for_claim = self.api.check_eligibility(self.owned_nfts)

    def sign_message(self, nonce, timestamp) -> str:
        """
        Signs authorization message
        :param nonce: nonce to be used in message
        :param timestamp: timestamp to be used in message (current timestamp)
        :return: Hex of signed message
        """
        msggg = f"Please sign to verify your authenticity. Nonce: {nonce}, Timestamp: {timestamp}, Address: {self.address}"
        logger.info(f'Signing message:{msggg}')
        message = encode_defunct(text=msggg)
        signed_message = self.account.sign_message(message)
        return signed_message.signature.hex()

    def claim_all_nfts_available(self) -> bool:
        """
        Claims tokens from all available nfts to claim $based
        :return: True if claimed or nothing to claim, false if not
        """
        self.get_available_for_claim_nfts()
        if len(self.available_for_claim) == 0:
            logger.info('There is nothing to claim')
            return True
        logger.info(f'{self.address} has {self.available_for_claim} nfts to claim')

        nonce_timestamp = self.api.get_nonce_and_timestamp()
        nonce, timestamp = nonce_timestamp['nonce'], nonce_timestamp['timestamp']
        signed_message = self.sign_message(nonce=nonce, timestamp=timestamp)
        logger.info('Sending message to server')

        if self.api.send_message(nonce=nonce, timestamp=timestamp, signature=signed_message,
                                 nft_id=self.available_for_claim) == 'success':
            logger.success(f'Successfully claimed token for nfts {self.available_for_claim}')
            return True
        else:
            logger.error(f'Could not claim tokens for nfts {self.available_for_claim}')
            return False

    def get_tokens_claimable_amount(self) -> int:
        """
        :return: Amount of claimable tokens
        """
        return self.based_contract.functions.tokensClaimable(self.address).call()

    def claim_tokens(self):
        """
        Claims all available tokens
        :return: True if claimed or nothing to claim, False if not
        """
        if self.get_tokens_claimable_amount() == 0:
            logger.info('Has nothing to claim')
            return True
        raw_tx = self.based_contract.functions.claim()
        tx_hash = send_transaction(raw_tx=raw_tx, w3=self.w3, explorer='https://basescan.org/', account=self.account,
                                   eip1559=True)
        if check_tx_status(w3=self.w3, tx_hash=tx_hash):
            return True
        logger.error('Something went wrong while claiming tokens')
        raise False
