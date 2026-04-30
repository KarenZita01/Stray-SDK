"""Command-line interface for Stellar Agent."""
import logging
from decimal import Decimal, InvalidOperation
from .client import StellarClient
from .config import config
from .utils.validators import is_valid_stellar_address, is_valid_amount, validate_amount_precision
from .exceptions import ConfigurationError, ValidationError, TransactionError, NetworkError

def prompt_and_send():
    """Interactive CLI for sending Stellar payments."""
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    client = StellarClient()
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        print(f"❌ Configuration Error: {e}")
        print("Please set SOURCE_SECRET in your environment variables or .env file")
        return
    
    while True:
        print("\n--- Stellar Agent ---")
        destination = input("Enter destination public key (or type 'exit' to quit): ").strip()
        
        if destination.lower() == "exit":
            break
        
        # Validate destination address
        if not is_valid_stellar_address(destination):
            logger.warning(f"Invalid Stellar address provided: {destination}")
            print("❌ Invalid Stellar address. Must start with 'G' and be 56 characters long.")
            continue
        
        amount_str = input("Enter amount to send (in XLM): ").strip()
        
        try:
            # Use Decimal for better precision
            amount = Decimal(amount_str)
            if not is_valid_amount(amount):
                logger.warning(f"Invalid amount provided: {amount_str}")
                print("❌ Amount must be positive and less than 1,000,000 XLM.")
                continue
            if not validate_amount_precision(amount):
                logger.warning(f"Amount precision issue: {amount_str}")
                print("❌ Amount has too many decimal places. Maximum 7 decimal places allowed.")
                continue
        except (InvalidOperation, ValueError):
            logger.warning(f"Amount parsing failed for input: {amount_str}")
            print("❌ Invalid amount. Please enter a valid number.")
            continue
        
        # Check balance before attempting payment (if enabled)
        if config.balance_check_enabled:
            try:
                source_public_key = config.get_source_public_key()
                sufficient, current_balance, error_msg = client.check_sufficient_balance(source_public_key, amount)
                
                if not sufficient:
                    print(f"❌ {error_msg}")
                    print(f"💡 Please check: account funding, network connectivity, or reduce payment amount.")
                    continue
                else:
                    print(f"💰 Current balance: {current_balance} XLM (sufficient for payment)")
            except Exception as e:
                print(f"⚠️  Warning: Could not verify balance: {e}")
                print("Proceeding with payment attempt...")
        
        print(f"Sending {amount} XLM to {destination}...")
        logger.info(f"Attempting to send {amount} XLM to {destination}")
        try:
            response = client.send_payment(config.source_secret, destination, float(amount))
            logger.info(f"Transaction successful: {response.get('hash', 'unknown')}")
            print("✅ Transaction Successful!")
            print("Transaction Hash:", response['hash'])
            if 'ledger' in response:
                print("Ledger:", response['ledger'])
        except ValueError as e:
            logger.error(f"Value error in transaction: {e}")
            print(f"❌ Transaction Failed: {e}")
        except RuntimeError as e:
            logger.error(f"Runtime error in transaction: {e}")
            print(f"❌ Transaction Failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in transaction: {e}")
            print(f"❌ Unexpected error: {e}")
            print("💡 Please check your network connectivity and configuration.")

def run():
    """Entry point for the CLI."""
    prompt_and_send()
