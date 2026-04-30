"""Configuration management for Stellar Agent."""
import logging
import os
from typing import Optional
from dotenv import load_dotenv
from .exceptions import ConfigurationError
from .utils.validators import is_valid_stellar_secret

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for Stellar Agent."""
    
    def __init__(self):
        self.horizon_url = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org")
        self.network_passphrase = os.getenv(
            "NETWORK_PASSPHRASE", 
            "Test SDF Network ; September 2015"
        )
        self.source_secret = os.getenv("SOURCE_SECRET", "")
        self.monitor_account_id = os.getenv("MONITOR_ACCOUNT_ID", "")
        self.destination_account_id = os.getenv("DESTINATION_ACCOUNT_ID", "")
        # Balance safety settings
        self.minimum_balance_xlm = float(os.getenv("MINIMUM_BALANCE_XLM", "1.0"))
        self.balance_check_enabled = os.getenv("BALANCE_CHECK_ENABLED", "true").lower() == "true"
    
    def validate(self) -> bool:
        """Validate that required configuration is present."""
        logger = logging.getLogger(__name__)
        
        if not self.source_secret:
            logger.error("SOURCE_SECRET is missing from environment variables")
            raise ConfigurationError("SOURCE_SECRET is required in environment variables")
        
        # Validate SOURCE_SECRET format using validator
        if not is_valid_stellar_secret(self.source_secret):
            logger.error(f"Invalid SOURCE_SECRET format: {self.source_secret[:10]}...")
            raise ConfigurationError("SOURCE_SECRET must be a valid Stellar secret key (56 characters starting with 'S')")
        
        # Validate network settings
        if not self.horizon_url:
            logger.error("HORIZON_URL is empty")
            raise ConfigurationError("HORIZON_URL cannot be empty")
        
        if not self.network_passphrase:
            logger.error("NETWORK_PASSPHRASE is empty")
            raise ConfigurationError("NETWORK_PASSPHRASE cannot be empty")
        
        logger.info("Configuration validation successful")
        return True
    
    def get_source_public_key(self) -> str:
        """Get the public key corresponding to the source secret."""
        logger = logging.getLogger(__name__)
        from stellar_sdk import Keypair
        try:
            keypair = Keypair.from_secret(self.source_secret)
            public_key = keypair.public_key
            logger.debug(f"Successfully derived public key from secret: {public_key}")
            return public_key
        except Exception as e:
            logger.error(f"Failed to derive public key from secret: {e}")
            raise ConfigurationError(f"Invalid SOURCE_SECRET: {e}")

# Global config instance
config = Config()
