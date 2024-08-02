import json
import requests

from loguru import logger
from eth_account.account import ChecksumAddress

from modules.helpful_scripts import MakePause
from modules.requestor import Requestor

endpoint = 'https://basedevo.fun/api/'
headers = {
    'Origin': 'https://basedevo.fun',
    'Referer': 'https://basedevo.fun/'
}


class BasedApi(Requestor):
    def __init__(self, address: ChecksumAddress):
        super().__init__(endpoint, _headers=headers)
        self.address = address

    def get_owned_nfts_number(self) -> list[str]:
        """
        Gets the list of Based, Introduced NFTs associated with the address
        :return: (list) - e.g. [215151, 444687]
        """
        url = ('https://eth-mainnet.g.alchemy.com/v2/8JIZ56KAEw1THx4p2nC-Hbk_06szPK7V/getNFTsForOwner?'
               f'owner={self.address}&contractAddresses[]=0xD4307E0acD12CF46fD6cf93BC264f5D5D1598792&withMetadata'
               f'=true&pageSize=100')

        try:
            response = self.get_request(url=url)
        except requests.exceptions.ConnectionError as err:
            # special case if server error 429
            if err.args[0] == 429:
                logger.info('Have to sleep a bit')
                raise MakePause(60)
            raise ConnectionError()

        # response schema - {'ownedNfts': [{'contract': {'address': '0x........'}, 'id': {'tokenId': '0x00000000....', 'tokenMetadata': {'tokenType': 'ERC721'}}, 'balance': '1', 'title': 'Base, Introduced 268919', 'description': 'Meet Base, an Ethereum L2 that offers a secure, low-cost, developer-friendly way for anyone, anywhere, to build decentralized apps.\n\nWe collectively minted ‘Base, Introduced’ to celebrate the testnet launch and grow the broader Base community. We’re excited to build Base together.', 'tokenUri': {'gateway': '', 'raw': 'data:application/json;base64,eyJuYW1lIjogIkJhc2UsIEludHJvZHVjZWQgMjY4OTE5IiwgImRlc2NyaXB0aW9uIjogIk1lZXQgQmFzZSwgYW4gRXRoZXJldW0gTDIgdGhhdCBvZmZlcnMgYSBzZWN1cmUsIGxvdy1jb3N0LCBkZXZlbG9wZXItZnJpZW5kbHkgd2F5IGZvciBhbnlvbmUsIGFueXdoZXJlLCB0byBidWlsZCBkZWNlbnRyYWxpemVkIGFwcHMuXG5cbldlIGNvbGxlY3RpdmVseSBtaW50ZWQg4oCYQmFzZSwgSW50cm9kdWNlZOKAmSB0byBjZWxlYnJhdGUgdGhlIHRlc3RuZXQgbGF1bmNoIGFuZCBncm93IHRoZSBicm9hZGVyIEJhc2UgY29tbXVuaXR5LiBXZeKAmXJlIGV4Y2l0ZWQgdG8gYnVpbGQgQmFzZSB0b2dldGhlci4iLCAiaW1hZ2UiOiAiaXBmczovL2JhZnliZWliaHRrMjNoNnNhczR5dWFodHl5N3Yya3p2d293dzdoZTQ0cmhpeDdrcTQ0cmYyYWYzZmNxIiwgInByb3BlcnRpZXMiOiB7Im51bWJlciI6IDI2ODkxOSwgIm5hbWUiOiAiQmFzZSwgSW50cm9kdWNlZCJ9fQ=='}, 'media': [{'gateway': 'https://nft-cdn.alchemy.com/eth-mainnet/7d4bbd9b3a3621f0e9cd653f83c91c61', 'thumbnail': 'https://res.cloudinary.com/alchemyapi/image/upload/thumbnailv2/eth-mainnet/7d4bbd9b3a3621f0e9cd653f83c91c61', 'raw': 'ipfs://bafybeibhtk23h6sas4yuahtyy7v2kzvwoww7he44rhix7kq44rf2af3fcq', 'format': 'gif', 'bytes': 3587804}], 'metadata': {'name': 'Base, Introduced 268919', 'description': 'Meet Base, an Ethereum L2 that offers a secure, low-cost, developer-friendly way for anyone, anywhere, to build decentralized apps.\n\nWe collectively minted ‘Base, Introduced’ to celebrate the testnet launch and grow the broader Base community. We’re excited to build Base together.', 'image': 'ipfs://bafybeibhtk23h6sas4yuahtyy7v2kzvwoww7he44rhix7kq44rf2af3fcq', 'properties': {'name': 'Base, Introduced', 'number': 268919}}, 'timeLastUpdated': '2023-11-16T23:32:41.953Z', 'contractMetadata': {'name': 'Base, Introduced', 'symbol': 'BASEINTRODUCED', 'totalSupply': '485078', 'tokenType': 'ERC721', 'contractDeployer': '0x2ea881cecb8b79686a2971c9926e1f92b906b63c', 'deployedBlockNumber': 16691530, 'openSea': {'floorPrice': 0.0018, 'collectionName': 'Base, Introduced', 'collectionSlug': 'base-introduced', 'safelistRequestStatus': 'approved', 'imageUrl': 'https://i.seadn.io/gcs/files/f75d772fba8058dbbbefbc0578bae807.png?w=500&auto=format', 'description': 'Meet Base, an Ethereum L2 that offers a secure, low-cost, developer-friendly way for anyone, anywhere, to build decentralized apps.\n \nMint ‘Base, Introduced’ to celebrate the testnet launch and join the broader Base community. We’re excited to build Base together with you.', 'lastIngestedAt': '2024-07-30T16:37:42.000Z'}}}], 'totalCount': 1, 'blockHash': '....'}

        nfts_owned = [str(nft_owned['metadata']['properties']['number']) for nft_owned in response['ownedNfts']]
        return nfts_owned

    def is_nft_used(self, nft_id: int) -> bool:
        """
        Returns True is nft was already used, False if not
        :param nft_id: int of nft number
        :return: (bool)
        """
        payload = {
            'tokenId': nft_id,
        }
        resp = self.post_request(url=self.endpoint + 'checkToken', json=payload)
        # response data {"status": 200, "body": {"tokenUsed": true}}
        if resp['status'] != 200:
            raise ConnectionError(f'Error while checking nft usage with response {resp}')
        return resp['body']['tokenUsed']

    def check_eligibility(self, nft_id: list[str] | str) -> list[str]:
        """
        Returns the list of nfts available for claim tokens
        :param nft_id: (list[str]|str) Can take the list of nft ids, of single id as argument
        :return: the list of nfts available for claim, e.g - [284574, 457484]
        """

        if type(nft_id) is str:
            nft_id = [nft_id]

        payload = {
            'address': self.address,
            'tokenIds': nft_id,
        }
        resp = self.post_request(url=self.endpoint + 'checkEligible', json=payload)
        # returns {'status': 200, 'body': ['291116']}
        if resp['status'] != 200:
            raise ConnectionError(f'Error while checking eligibility with response {resp}')
        return resp['body']

    def get_nonce_and_timestamp(self) -> dict:
        """
        Gets nonce and timestamp for signature
        :return: dict - e.g. {'nonce': 0, 'timestamp': 1722424371849}
        """
        payload = {
            'address': self.address,
        }
        resp = self.post_request(url=self.endpoint + 'getNonce', json=payload)
        # {"status": 200, "body": "{\"nonce\":0,\"timestamp\":1722242218749}"}
        if resp['status'] != 200:
            raise ConnectionError(f'Error while getting nonce and timestamp with response {resp}')

        return json.loads(resp['body'])

    def send_message(self, nonce: int, nft_id: list[str] | str, signature: str, timestamp: int) -> bool:
        """
        Send message to server
        :param nonce: (int)
        :param nft_id: (list[str]|str) Can take the list of nft ids, of single id as argument
        :param signature: signed message "Please sign to verify your authenticity....."
        :param timestamp: (int)
        :return: (bool) True is success
        """

        if type(nft_id) is str:
            nft_id = [nft_id]

        payload = {
            'address': self.address,
            'nonce': nonce,
            'tokenIDs': nft_id,
            'sig': signature,
            'timestamp': timestamp
        }

        resp = self.post_request(url=self.endpoint + 'callRelayer', json=payload)
        # returns {"statusCode": 200, "body": "{\"message\":\"success\",\"transactionResponse\":{\"transactionId\":\"676fabe1-66ab-4bc6-a288-c03e3d251d83\"}}"}

        if resp['statusCode'] != 200:
            raise ConnectionError(f'Error while sending message with response {resp}')

        return json.loads(resp['body'])['message']
