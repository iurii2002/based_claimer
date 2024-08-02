import time

from hexbytes import HexBytes
from loguru import logger
from web3 import Web3
from eth_account.signers.local import LocalAccount
from eth_account.messages import encode_defunct
from modules.basedevo_api import BasedApi


class BasedClient:
    def __init__(self, account: LocalAccount):
        self.account = account
        self.address = self.account.address
        self.api = BasedApi(self.address)
        self.w3 = Web3(Web3.HTTPProvider('localhost'))
        self.owned_nfts = None
        self.available_for_claim = None

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
            logger.success(f'Successfully claimed token fot nfts {self.available_for_claim}')
            return True
        else:
            logger.error(f'Could not claim tokens for nfts {self.available_for_claim}')
            return False
