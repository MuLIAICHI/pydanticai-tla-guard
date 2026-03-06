import pytest
from pydanticai_tla.verifier import tla_verify

def test_tla_verify_allows_valid_transition():
    state_dict = {
        "pc": "test",
        "artifacts": [{"type": "test_report"}]
    }
    # Should not raise any exception
    assert tla_verify(state_dict, "deploy") is True

def test_tla_verify_blocks_invalid_deploy():
    state_dict = {
        "pc": "code",
        # No test_report present
        "artifacts": [{"type": "python_script"}]
    }
    
    with pytest.raises(ValueError) as exc_info:
        tla_verify(state_dict, "deploy")
        
    assert "NoDeployUntested" in str(exc_info.value)
