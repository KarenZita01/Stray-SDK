"""Stellar blockchain client for payment operations."""
import logging
from stellar_sdk import Server, Keypair, TransactionBuilder, Asset
from stellar_sdk.operation import Payment
from stellar_sdk.exceptions import NotFoundError, BadRequestError, NetworkError as StellarNetworkError
from typing import Dict, Any, Tuple
from decimal import Decimal
from .config import config
from .exceptions import AccountNotFoundError, InsufficientBalanceError, TransactionError, NetworkError

class StellarClient:
    """Client for interacting with Stellar blockchain."""
    
    def __init__(self):
        self.server = Server(config.horizon_url)
        self.logger = logging.getLogger(__name__)
    
    def get_account_info(self, account_id: str) -> Dict[str, Any]:
        """
        Fetch account information from Horizon.
        
        Args:
            account_id: Public key of the account
            
        Returns:
            Account information dictionary
            
        Raises:
            RuntimeError: If account is not found or network issues occur
        """
        try:
            self.logger.debug(f"Fetching account info for {account_id}")
            response = self.server.accounts().account_id(account_id).call()
            self.logger.debug(f"Successfully fetched account info for {account_id}")
            return response
        except NotFoundError:
            self.logger.error(f"Account not found: {account_id}")
            raise AccountNotFoundError(f"Account {account_id} not found on the Stellar network. Check that the account is funded and the network URL is correct.")
        except StellarNetworkError as e:
            self.logger.error(f"Network error fetching account info: {e}")
            raise NetworkError(f"Network connectivity issue: {e}. Check your internet connection and Horizon URL.")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching account info: {e}")
            raise RuntimeError(f"Failed to fetch account information: {e}. Check your network connectivity and Horizon URL configuration.")
    
    def get_account_balance(self, account_id: str) -> Tuple[Decimal, bool]:
        """
        Get the XLM balance of an account.
        
        Args:
            account_id: Public key of the account
            
        Returns:
            Tuple of (balance_in_xlm, account_exists)
        """
        try:
            account_info = self.get_account_info(account_id)
            # Find XLM balance
            for balance in account_info.get('balances', []):
                if balance.get('asset_type') == 'native':
                    return Decimal(balance['balance']), True
            return Decimal('0'), True
        except RuntimeError:
            return Decimal('0'), False
    
    def check_sufficient_balance(self, source_account_id: str, amount: float) -> Tuple[bool, Decimal, str]:
        """
        Check if account has sufficient balance for payment + fees + minimum balance.
        
        Args:
            source_account_id: Public key of the source account
            amount: Amount to send in XLM
            
        Returns:
            Tuple of (is_sufficient, current_balance, error_message)
        """
        balance, account_exists = self.get_account_balance(source_account_id)
        
        if not account_exists:
            return False, balance, "Source account not found or not funded"
        
        # Calculate total cost: payment + estimated fee + minimum balance reserve
        payment_amount = Decimal(str(amount))
        estimated_fee = Decimal('0.00001')  # Base fee
        minimum_reserve = Decimal(str(config.minimum_balance_xlm))
        
        total_required = payment_amount + estimated_fee + minimum_reserve
        
        if balance < total_required:
            error_msg = (
                f"Insufficient balance. Required: {total_required} XLM "
                f"(Payment: {payment_amount}, Fee: {estimated_fee}, Reserve: {minimum_reserve}), "
                f"Available: {balance} XLM"
            )
            self.logger.warning(f"Insufficient balance for account {source_account_id}: {error_msg}")
            return False, balance, error_msg
        
        return True, balance, ""
    
    def send_payment(
        self, 
        source_secret: str, 
        destination_public: str, 
        amount: float
    ) -> Dict[str, Any]:
        """
        Send XLM payment to a destination address.
        
        Args:
            source_secret: Secret key of the source account
            destination_public: Public key of the destination account
            amount: Amount of XLM to send
            
        Returns:
            Transaction response dictionary
            
        Raises:
            RuntimeError: If balance is insufficient, network issues, or transaction fails
        """
        try:
            self.logger.info(f"Initiating payment: {amount} XLM to {destination_public}")
            source_keypair = Keypair.from_secret(source_secret)
            source_public_key = source_keypair.public_key
            
            # Balance check if enabled
            if config.balance_check_enabled:
                sufficient, balance, error_msg = self.check_sufficient_balance(source_public_key, amount)
                if not sufficient:
                    self.logger.error(f"Balance check failed: {error_msg}")
                    raise InsufficientBalanceError(f"Balance check failed: {error_msg}")
            
            # Load source account
            try:
                self.logger.debug(f"Loading source account: {source_public_key}")
                source_account = self.server.load_account(source_public_key)
            except NotFoundError:
                self.logger.error(f"Source account not found: {source_public_key}")
                raise AccountNotFoundError(f"Source account {source_public_key} not found. Ensure the account is funded and you're connected to the correct network.")
            except StellarNetworkError as e:
                self.logger.error(f"Network error loading source account: {e}")
                raise NetworkError(f"Failed to load source account due to network issues: {e}. Check network connectivity and Horizon URL.")
            except Exception as e:
                self.logger.error(f"Unexpected error loading source account: {e}")
                raise RuntimeError(f"Failed to load source account: {e}. Check network connectivity and Horizon URL.")

            # Build transaction
            self.logger.debug("Building transaction")
            transaction = (
                TransactionBuilder(
                    source_account=source_account,
                    network_passphrase=config.network_passphrase,
                    base_fee=100,
                )
                .append_operation(
                    Payment(
                        destination=destination_public,
                        asset=Asset.native(),
                        amount=str(amount)
                    )
                )
                .set_timeout(30)
                .build()
            )

            # Sign and submit transaction
            self.logger.debug("Signing and submitting transaction")
            transaction.sign(source_keypair)
            
            try:
                response = self.server.submit_transaction(transaction)
                self.logger.info(f"Transaction submitted successfully: {response.get('hash', 'unknown')}")
                return response
            except BadRequestError as e:
                # Parse common Stellar errors
                error_detail = str(e)
                self.logger.error(f"Bad request error in transaction: {error_detail}")
                if "insufficient balance" in error_detail.lower():
                    raise InsufficientBalanceError("Transaction failed: Insufficient balance for payment and fees.")
                elif "destination account does not exist" in error_detail.lower():
                    raise AccountNotFoundError("Transaction failed: Destination account does not exist. The recipient must have an active Stellar account.")
                else:
                    raise TransactionError(f"Transaction failed: {error_detail}. Check transaction parameters and try again.")
            except StellarNetworkError as e:
                self.logger.error(f"Network error submitting transaction: {e}")
                raise NetworkError(f"Transaction submission failed due to network issues: {e}. Check network connectivity and try again.")
            except Exception as e:
                self.logger.error(f"Unexpected error submitting transaction: {e}")
                raise RuntimeError(f"Transaction submission failed: {e}. Check network connectivity and try again.")
                
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Payment operation failed: {e}")
