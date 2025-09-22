import json
from web3 import Web3
from wallet_manager import WalletManager
from config import (
    CRO_TOKEN_ADDRESS, USDC_TOKEN_ADDRESS, VVS_ROUTER_ADDRESS,
    CRONOS_CHAIN_ID, DEFAULT_SLIPPAGE, MAX_TRADE_AMOUNT
)

class DEXTrader:
    def __init__(self, wallet_manager):
        self.wallet = wallet_manager
        self.w3 = wallet_manager.w3
        
        # VVS Router ABI (simplified for swap functions)
        self.router_abi = [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactTokensForTokens",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountInMax", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapTokensForExactTokens",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsOut",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        # ERC20 ABI for token operations
        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [
                    {"name": "_owner", "type": "address"},
                    {"name": "_spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        self.router_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(VVS_ROUTER_ADDRESS),
            abi=self.router_abi
        )
    
    def get_token_contract(self, token_address):
        """Get ERC20 token contract"""
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=self.erc20_abi
        )
    
    def get_amounts_out(self, amount_in, path):
        """Get expected output amounts for a swap"""
        try:
            amounts = self.router_contract.functions.getAmountsOut(
                amount_in, path
            ).call()
            return amounts
        except Exception as e:
            raise Exception(f"Failed to get amounts out: {str(e)}")
    
    def approve_token(self, token_address, spender_address, amount):
        """Approve token spending"""
        token_contract = self.get_token_contract(token_address)
        
        # Check current allowance
        current_allowance = token_contract.functions.allowance(
            self.wallet.address, spender_address
        ).call()
        
        if current_allowance >= amount:
            return True  # Already approved
        
        # Retry logic for nonce conflicts
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get fresh nonce for each attempt
                nonce = self.wallet.get_nonce()
                
                # Create approval transaction
                transaction = token_contract.functions.approve(
                    spender_address, amount
                ).build_transaction({
                    'from': self.wallet.address,
                    'gas': 100000,
                    'gasPrice': self.wallet.get_gas_price(),
                    'nonce': nonce,
                    'chainId': CRONOS_CHAIN_ID
                })
                
                # Sign and send transaction
                signed_txn = self.wallet.sign_transaction(transaction)
                tx_hash = self.wallet.send_transaction(signed_txn)
                
                # Wait for transaction confirmation
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                return receipt.status == 1
                
            except Exception as e:
                if "invalid nonce" in str(e).lower() and attempt < max_retries - 1:
                    # Wait a bit and try again with fresh nonce
                    import time
                    time.sleep(2)
                    continue
                else:
                    raise e
    
    def swap_tokens(self, token_in, token_out, amount_in, slippage_percent=DEFAULT_SLIPPAGE):
        """Execute token swap"""
        try:
            # Convert amount to wei based on token decimals
            if token_in.lower() == USDC_TOKEN_ADDRESS.lower():
                amount_in_wei = int(amount_in * 10**6)  # USDC has 6 decimals
            else:
                amount_in_wei = int(amount_in * 10**18)  # CRO has 18 decimals
            
            # Define swap path
            path = [Web3.to_checksum_address(token_in), Web3.to_checksum_address(token_out)]
            
            # Get expected output amount
            amounts_out = self.get_amounts_out(amount_in_wei, path)
            expected_amount_out = amounts_out[-1]
            
            # Calculate minimum amount out with slippage
            min_amount_out = int(expected_amount_out * (100 - slippage_percent) / 100)
            
            # Approve token spending
            if not self.approve_token(token_in, VVS_ROUTER_ADDRESS, amount_in_wei):
                raise Exception("Failed to approve token spending")
            
            # Set deadline (10 minutes from now)
            deadline = int(self.w3.eth.get_block('latest').timestamp) + 600
            
            # Retry logic for nonce conflicts
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Get fresh nonce for each attempt
                    nonce = self.wallet.get_nonce()
                    
                    # Create swap transaction
                    transaction = self.router_contract.functions.swapExactTokensForTokens(
                        amount_in_wei,
                        min_amount_out,
                        path,
                        self.wallet.address,
                        deadline
                    ).build_transaction({
                        'from': self.wallet.address,
                        'gas': 300000,
                        'gasPrice': self.wallet.get_gas_price(),
                        'nonce': nonce,
                        'chainId': CRONOS_CHAIN_ID
                    })
                    
                    # Sign and send transaction
                    signed_txn = self.wallet.sign_transaction(transaction)
                    tx_hash = self.wallet.send_transaction(signed_txn)
                    
                    # Convert output amounts based on token decimals
                    if token_out.lower() == USDC_TOKEN_ADDRESS.lower():
                        expected_amount_out_formatted = expected_amount_out / 10**6  # USDC has 6 decimals
                        min_amount_out_formatted = min_amount_out / 10**6
                    else:
                        expected_amount_out_formatted = expected_amount_out / 10**18  # CRO has 18 decimals
                        min_amount_out_formatted = min_amount_out / 10**18
                    
                    return {
                        'success': True,
                        'tx_hash': tx_hash,
                        'amount_in': amount_in,
                        'expected_amount_out': expected_amount_out_formatted,
                        'min_amount_out': min_amount_out_formatted
                    }
                    
                except Exception as e:
                    if "invalid nonce" in str(e).lower() and attempt < max_retries - 1:
                        # Wait a bit and try again with fresh nonce
                        import time
                        time.sleep(2)
                        continue
                    else:
                        raise e
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def buy_cro_with_usdc(self, usdc_amount, slippage_percent=DEFAULT_SLIPPAGE):
        """Buy CRO with USDC"""
        return self.swap_tokens(USDC_TOKEN_ADDRESS, CRO_TOKEN_ADDRESS, usdc_amount, slippage_percent)
    
    def sell_cro_for_usdc(self, cro_amount, slippage_percent=DEFAULT_SLIPPAGE):
        """Sell CRO for USDC"""
        return self.swap_tokens(CRO_TOKEN_ADDRESS, USDC_TOKEN_ADDRESS, cro_amount, slippage_percent)
    
    def get_token_balance(self, token_address):
        """Get token balance"""
        token_contract = self.get_token_contract(token_address)
        balance = token_contract.functions.balanceOf(self.wallet.address).call()
        
        # USDC has 6 decimals, CRO has 18 decimals
        if token_address.lower() == USDC_TOKEN_ADDRESS.lower():
            return balance / 10**6  # USDC has 6 decimals
        else:
            return balance / 10**18  # CRO has 18 decimals
    
    def get_cro_balance(self):
        """Get CRO balance"""
        return self.get_token_balance(CRO_TOKEN_ADDRESS)
    
    def get_usdc_balance(self):
        """Get USDC balance"""
        return self.get_token_balance(USDC_TOKEN_ADDRESS)
