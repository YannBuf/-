import pytest
from unittest.mock import AsyncMock, patch
from app.services.llm import OpenAICompatibleLLM
from app.services.insight import InsightGenerator, NLUnderstanding


@pytest.fixture
def mock_llm():
    """Mock LLM for testing without API calls."""
    llm = OpenAICompatibleLLM(api_url="http://localhost/v1/chat/completions", api_key="test")
    llm.chat = AsyncMock(return_value="这是一个测试回复")
    return llm


@pytest.mark.asyncio
async def test_insight_generator_funnel(mock_llm):
    """Test funnel insight generation."""
    generator = InsightGenerator(mock_llm)

    funnel_data = {
        "funnel": [
            {"step": "impression", "user_count": 1000, "conversion_rate": 1.0},
            {"step": "click", "user_count": 500, "conversion_rate": 0.5},
            {"step": "purchase", "user_count": 50, "conversion_rate": 0.1},
        ],
        "biggest_dropoff": {"step": "click", "dropoff_rate": 0.8},
    }

    insight = await generator.generate_funnel_insight(funnel_data)

    assert insight == "这是一个测试回复"
    mock_llm.chat.assert_called_once()


@pytest.mark.asyncio
async def test_nl_understanding_parse(mock_llm):
    """Test natural language query parsing."""
    parser = NLUnderstanding(mock_llm)
    mock_llm.chat.return_value = '{"query_type": "funnel_analysis", "parameters": {"time_range": "最近7天"}, "original_question": "最近7天漏斗"}'

    result = await parser.parse("最近7天的漏斗转化情况怎么样？")

    assert result["query_type"] == "funnel_analysis"
    assert result["parameters"]["time_range"] == "最近7天"


@pytest.mark.asyncio
async def test_nl_understanding_invalid_json(mock_llm):
    """Test handling of invalid LLM response."""
    parser = NLUnderstanding(mock_llm)
    mock_llm.chat.return_value = "这不是JSON格式"

    result = await parser.parse("我的数据怎么样？")

    assert result["query_type"] == "general"
    assert result["original_question"] == "我的数据怎么样？"
