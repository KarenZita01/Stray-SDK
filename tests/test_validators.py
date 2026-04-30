"""Tests for validation utilities and client balance checks."""
import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from stellar_agent.utils.validators import is_valid_stellar_address, is_valid_amount, is_valid_stellar_secret, validate_amount_precision
from stellar_agent.client import StellarClient
from stellar_agent.config import config
from stellar_agent.exceptions import ConfigurationError, ValidationError, InsufficientBalanceError, AccountNotFoundError

class TestValidators:
    """Test validation functions."""
    
    def test_valid_stellar_address(self):
        """Test valid Stellar address format."""
        valid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_address(valid_address) is True
    
    def test_invalid_stellar_address_wrong_prefix(self):
        """Test address with wrong prefix."""
        invalid_address = "ABRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_address(invalid_address) is False
    
    def test_invalid_stellar_address_wrong_length(self):
        """Test address with wrong length."""
        invalid_address = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX"
        assert is_valid_stellar_address(invalid_address) is False
    
    def test_empty_address(self):
        """Test empty address."""
        assert is_valid_stellar_address("") is False
    
    def test_valid_amount(self):
        """Test valid payment amount."""
        assert is_valid_amount(10.5) is True
        assert is_valid_amount(0.0000001) is True
    
    def test_invalid_amount(self):
        """Test invalid payment amounts."""
        assert is_valid_amount(0) is False
        assert is_valid_amount(-10) is False
        assert is_valid_amount("invalid") is False
        assert is_valid_amount(1000001) is False  # Over 1M limit
    
    def test_valid_stellar_secret(self):
        """Test valid Stellar secret key format."""
        valid_secret = "SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_secret(valid_secret) is True
    
    def test_invalid_stellar_secret_wrong_prefix(self):
        """Test secret key with wrong prefix."""
        invalid_secret = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
        assert is_valid_stellar_secret(invalid_secret) is False
    
    def test_invalid_stellar_secret_wrong_length(self):
        """Test secret key with wrong length."""
        invalid_secret = "SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX"
        assert is_valid_stellar_secret(invalid_secret) is False
    
    def test_empty_secret(self):
        """Test empty secret key."""
        assert is_valid_stellar_secret("") is False
    
    def test_amount_precision_valid(self):
        """Test valid amount precision."""
        assert validate_amount_precision("10.1234567") is True  # 7 decimal places
        assert validate_amount_precision("10") is True
        assert validate_amount_precision("10.1") is True
    
    def test_amount_precision_invalid(self):
        """Test invalid amount precision."""
        assert validate_amount_precision("10.12345678") is False  # 8 decimal places
        assert validate_amount_precision("invalid") is False


class TestStellarClientBalanceChecking:
    """Test balance checking functionality in StellarClient."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = StellarClient()
        self.test_account_id = "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H"
    
    @patch.object(StellarClient, 'get_account_info')
    def test_get_account_balance_success(self, mock_get_account_info):
        """Test successful balance retrieval."""
        mock_get_account_info.return_value = {
            'balances': [
                {'asset_type': 'native', 'balance': '100.5000000'}
            ]
        }
        
        balance, exists = self.client.get_account_balance(self.test_account_id)
        assert balance == Decimal('100.5000000')
        assert exists is True
    
    @patch.object(StellarClient, 'get_account_info')
    def test_get_account_balance_account_not_found(self, mock_get_account_info):
        """Test balance check for non-existent account."""
        mock_get_account_info.side_effect = RuntimeError("Account not found")
        
        balance, exists = self.client.get_account_balance(self.test_account_id)
        assert balance == Decimal('0')
        assert exists is False
    
    @patch.object(StellarClient, 'get_account_balance')
    def test_check_sufficient_balance_success(self, mock_get_balance):
        """Test sufficient balance check."""
        mock_get_balance.return_value = (Decimal('100.0'), True)
        
        sufficient, balance, error_msg = self.client.check_sufficient_balance(self.test_account_id, 10.0)
        assert sufficient is True
        assert balance == Decimal('100.0')
        assert error_msg == ""
    
    @patch.object(StellarClient, 'get_account_balance')
    def test_check_insufficient_balance(self, mock_get_balance):
        """Test insufficient balance check."""
        mock_get_balance.return_value = (Decimal('0.5'), True)
        
        sufficient, balance, error_msg = self.client.check_sufficient_balance(self.test_account_id, 10.0)
        assert sufficient is False
        assert balance == Decimal('0.5')
        assert "Insufficient balance" in error_msg
        assert "Required:" in error_msg
        assert "Available:" in error_msg
    
    @patch.object(StellarClient, 'get_account_balance')
    def test_check_balance_account_not_found(self, mock_get_balance):
        """Test balance check for account that doesn't exist."""
        mock_get_balance.return_value = (Decimal('0'), False)
        
        sufficient, balance, error_msg = self.client.check_sufficient_balance(self.test_account_id, 10.0)
        assert sufficient is False
        assert balance == Decimal('0')
        assert error_msg == "Source account not found or not funded"


class TestConfig:
    """Test configuration validation."""
    
    def test_config_validation_missing_source_secret(self):
        """Test config validation fails with missing SOURCE_SECRET."""
        with patch.dict('os.environ', {'SOURCE_SECRET': ''}, clear=True):
            test_config = config.__class__()
            with pytest.raises(ConfigurationError, match="SOURCE_SECRET is required"):
                test_config.validate()
    
    def test_config_validation_invalid_source_secret(self):
        """Test config validation fails with invalid SOURCE_SECRET format."""
        with patch.dict('os.environ', {'SOURCE_SECRET': 'invalid_secret'}, clear=True):
            test_config = config.__class__()
            with pytest.raises(ConfigurationError, match="SOURCE_SECRET must be a valid Stellar secret key"):
                test_config.validate()
    
    @patch.dict('os.environ', {
        'SOURCE_SECRET': 'SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',
        'HORIZON_URL': 'https://horizon-testnet.stellar.org',
        'NETWORK_PASSPHRASE': 'Test SDF Network ; September 2015'
    })
    def test_config_validation_success(self):
        """Test config validation succeeds with valid values."""
        test_config = config.__class__()
        assert test_config.validate() is True
    
    def test_config_validation_invalid_horizon_url(self):
        """Test config validation fails with empty HORIZON_URL."""
        with patch.dict('os.environ', {
            'SOURCE_SECRET': 'SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',
            'HORIZON_URL': '',
            'NETWORK_PASSPHRASE': 'Test SDF Network ; September 2015'
        }, clear=True):
            test_config = config.__class__()
            with pytest.raises(ConfigurationError, match="HORIZON_URL cannot be empty"):
                test_config.validate()
    
    def test_config_validation_invalid_network_passphrase(self):
        """Test config validation fails with empty NETWORK_PASSPHRASE."""
        with patch.dict('os.environ', {
            'SOURCE_SECRET': 'SBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H',
            'HORIZON_URL': 'https://horizon-testnet.stellar.org',
            'NETWORK_PASSPHRASE': ''
        }, clear=True):
            test_config = config.__class__()
            with pytest.raises(ConfigurationError, match="NETWORK_PASSPHRASE cannot be empty"):
                test_config.validate()
