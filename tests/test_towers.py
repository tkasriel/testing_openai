import os
from unittest.mock import MagicMock

import pytest
from ..requests import GPT


@pytest.fixture
def mock_gpt():
    os.environ["OPENAI_API_KEY"] = "aa"
    gpt = GPT()
    ret_val = MagicMock()
    gpt.client = MagicMock(return_value=ret_val)
    return gpt


def test_message_response(mock_gpt):
    mock_gpt.send_message("I like fish")

    create = mock_gpt.client.chat.completions.create
    create.assert_called_once()

    assert len(create.call_args) == 2
    arg = create.call_args[1]
    assert isinstance(arg, dict)
    print(arg)
    assert arg["messages"][0]["content"] == "I like fish"


def test_image_response(mock_gpt):
    mock_gpt.send_image("imgs/tests/example_image.jpeg", "I like captions too")

    create = mock_gpt.client.chat.completions.create
    create.assert_called_once()

    assert len(create.call_args) == 2
    arg = create.call_args[1]
    assert isinstance(arg, dict)
    assert arg["messages"][0]["content"][0]["text"] == "I like captions too"
