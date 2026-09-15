from smart_agents_ch7.planner.openai_planner import OpenAIPlanner


def test_extract_output_text_from_responses_shape():
    data = {
        "output": [
            {"type": "message", "content": [{"type": "output_text", "text": "{\"ok\":true}"}]}
        ]
    }
    assert OpenAIPlanner._extract_output_text(data) == '{"ok":true}'
