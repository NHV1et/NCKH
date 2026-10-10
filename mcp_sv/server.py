
from mcp.server.mcpserver import MCPServer

from ai_bot.infer import predict
from ai_bot.train import train_model

mcp = MCPServer("AI_BOT Website Detection")


@mcp.tool()
def train_website_model() -> dict:
    """Huấn luyện lại model phát hiện website phishing."""
    try:
        result = train_model()
        return {
            "status": "success",
            "message": "Train model thành công!",
            "details": result,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Train model thất bại: {e}",
        }
@mcp.tool()
def analyze_website(features: dict[str, float]) -> dict:
    """
    Phân tích website dựa trên bộ feature đã thu thập.

    Args:
        features: Dictionary gồm các feature đầu vào của XGBoost.

    Returns:
        Kết quả phân loại, điểm rủi ro, độ tin cậy,
        các yếu tố SHAP và phần giải thích từ LLM.
    """
    result = predict(features)

    # Chuyển Pydantic model thành dictionary để MCP trả về.
    return result.model_dump()


if __name__ == "__main__":
    mcp.run(transport="stdio")
