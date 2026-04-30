"""Tests for custom exceptions."""
import pytest
from stellar_agent.exceptions import (
    StellarAgentError, ConfigurationError, ValidationError, 
    InsufficientBalanceError, AccountNotFoundError, TransactionError, NetworkError
)


class TestCustomExceptions:
    """Test custom exception hierarchy and behavior."""
    
    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from StellarAgentError."""
        assert issubclass(ConfigurationError, StellarAgentError)
        assert issubclass(ValidationError, StellarAgentError)
        assert issubclass(InsufficientBalanceError, StellarAgentError)
        assert issubclass(AccountNotFoundError, StellarAgentError)
        assert issubclass(TransactionError, StellarAgentError)
        assert issubclass(NetworkError, StellarAgentError)
    
    def test_exception_messages(self):
        """Test that exceptions can be instantiated with custom messages."""
        test_message = "Test error message"
        
        config_error = ConfigurationError(test_message)
        validation_error = ValidationError(test_message)
        balance_error = InsufficientBalanceError(test_message)
        account_error = AccountNotFoundError(test_message)
        transaction_error = TransactionError(test_message)
        network_error = NetworkError(test_message)
        
        assert str(config_error) == test_message
        assert str(validation_error) == test_message
        assert str(balance_error) == test_message
        assert str(account_error) == test_message
        assert str(transaction_error) == test_message
        assert str(network_error) == test_message
    
    def test_exception_raising_and_catching(self):
        """Test that exceptions can be properly raised and caught."""
        test_message = "Test error message"
        
        # Test ConfigurationError
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError(test_message)
        assert str(exc_info.value) == test_message
        
        # Test ValidationError
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(test_message)
        assert str(exc_info.value) == test_message
        
        # Test InsufficientBalanceError
        with pytest.raises(InsufficientBalanceError) as exc_info:
            raise InsufficientBalanceError(test_message)
        assert str(exc_info.value) == test_message
        
        # Test AccountNotFoundError
        with pytest.raises(AccountNotFoundError) as exc_info:
            raise AccountNotFoundError(test_message)
        assert str(exc_info.value) == test_message
        
        # Test TransactionError
        with pytest.raises(TransactionError) as exc_info:
            raise TransactionError(test_message)
        assert str(exc_info.value) == test_message
        
        # Test NetworkError
        with pytest.raises(NetworkError) as exc_info:
            raise NetworkError(test_message)
        assert str(exc_info.value) == test_message
    
    def test_exception_catching_by_base_class(self):
        """Test that custom exceptions can be caught by their base class."""
        test_message = "Test error message"
        
        # All custom exceptions should be catchable by StellarAgentError
        with pytest.raises(StellarAgentError):
            raise ConfigurationError(test_message)
        
        with pytest.raises(StellarAgentError):
            raise ValidationError(test_message)
        
        with pytest.raises(StellarAgentError):
            raise InsufficientBalanceError(test_message)
        
        with pytest.raises(StellarAgentError):
            raise AccountNotFoundError(test_message)
        
        with pytest.raises(StellarAgentError):
            raise TransactionError(test_message)
        
        with pytest.raises(StellarAgentError):
            raise NetworkError(test_message)
