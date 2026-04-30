
import asyncio
import logging
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Mock dependencies to allow importing without full environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))

with patch('openai.AsyncOpenAI', MagicMock()):
    from app.services.ai.llm_executor import query_ollama

async def test_ollama_pull_logic():
    logging.basicConfig(level=logging.INFO)
    
    # Mock response for model not found (404)
    mock_404 = MagicMock()
    mock_404.status_code = 404
    mock_404.json.return_value = {"error": "model 'mistral' not found"}
    
    # Mock response for successful pull (200)
    mock_200_pull = MagicMock()
    mock_200_pull.status_code = 200
    
    # Mock response for successful chat (200)
    mock_200_chat = MagicMock()
    mock_200_chat.status_code = 200
    mock_200_chat.json.return_value = {"message": {"content": "Hello from Mistral!"}}
    
    # Setup AsyncClient mock
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Define side effects: 
        # 1st call: Chat (404)
        # 2nd call: Pull (200)
        # 3rd call: Chat retry (200)
        mock_client.post.side_effect = [mock_404, mock_200_pull, mock_200_chat]
        
        print("Testing Ollama auto-pull logic...")
        result = await query_ollama("Test prompt")
        
        print(f"Result: {result}")
        assert result == "Hello from Mistral!"
        assert mock_client.post.call_count == 3
        print("✅ Success: Ollama automatically pulled model and retried!")

if __name__ == "__main__":
    asyncio.run(test_ollama_pull_logic())
