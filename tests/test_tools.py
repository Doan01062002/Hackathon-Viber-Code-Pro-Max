from ai.tools.example_tool import calculate, search_knowledge


def test_calculate_basic():
    assert calculate.invoke({"expression": "2 + 3 * 4"}) == "14"


def test_calculate_rejects_unsafe_expression():
    result = calculate.invoke({"expression": "__import__('os').system('ls')"})
    assert result.startswith("Lỗi tính toán")


def test_search_knowledge_returns_string():
    assert isinstance(search_knowledge.invoke({"query": "test"}), str)
