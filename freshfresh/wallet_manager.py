import os
from eth_account import Account
from web3 import Web3
from config import WALLET_ADDRESS, RECOVERY_PHRASE, CRONOS_RPC_URL, CRONOS_CHAIN_ID

# Enable mnemonic features
Account.enable_unaudited_hdwallet_features()

class WalletManager:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(CRONOS_RPC_URL))
        self.account = self._load_account()
        self.address = WALLET_ADDRESS
        
    def _load_account(self):
        """Load account from recovery phrase"""
        try:
            account = Account.from_mnemonic(RECOVERY_PHRASE)
            return account
        except Exception as e:
            raise Exception(f"Failed to load wallet: {str(e)}")
    
    def get_balance(self, token_address=None):
        """Get balance of native CRO or ERC20 token"""
        if token_address is None:
            # Native CRO balance
            balance_wei = self.w3.eth.get_balance(self.address)
            return self.w3.from_wei(balance_wei, 'ether')
        else:
            # ERC20 token balance
            return self._get_erc20_balance(token_address)
    
    def _get_erc20_balance(self, token_address):
        """Get ERC20 token balance"""
        # ERC20 balanceOf function ABI
        balance_abi = [{
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }]
        
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=balance_abi
        )
        
        balance = contract.functions.balanceOf(self.address).call()
        return balance
    
    def sign_transaction(self, transaction):
        """Sign a transaction with the private key"""
        try:
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            return signed_txn
        except Exception as e:
            raise Exception(f"Failed to sign transaction: {str(e)}")
    
    def send_transaction(self, signed_transaction):
        """Send a signed transaction to the network"""
        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            return tx_hash.hex()
        except Exception as e:
            raise Exception(f"Failed to send transaction: {str(e)}")
    
    def get_nonce(self):
        """Get the current nonce for the account"""
        return self.w3.eth.get_transaction_count(self.address, 'pending')
    
    def estimate_gas(self, transaction):
        """Estimate gas for a transaction"""
        try:
            return self.w3.eth.estimate_gas(transaction)
        except Exception as e:
            raise Exception(f"Failed to estimate gas: {str(e)}")
    
    def get_gas_price(self):
        """Get current gas price"""
        return self.w3.eth.gas_price
