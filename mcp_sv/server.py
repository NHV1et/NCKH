from web_scraper.export import Export
from mcp.server.mcpserver import MCPServer
from ai_bot.infer import predict
from ai_bot.train import train_model
import re
import time
import json
from pathlib import Path

mcp = MCPServer("AI_BOT Website Detection")


# @mcp.tool()
# def train_website_model() -> dict:
#     """Huấn luyện lại model phát hiện website phishing."""
#     try:
#         result = train_model()
#         return {
#             "status": "success",
#             "message": "Train model thành công!",
#             "details": result,
#         }
#     except Exception as e:
#         return {
#             "status": "error",
#             "message": f"Train model thất bại: {e}",
#         }
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

@mcp.tool()
def scan_website(domain: str) -> dict:
    """Cào features của website và trả về báo cáo JSON."""

    domain = domain.strip()

    if (
        not re.fullmatch(
            r"(?=.{1,253}$)"
            r"(?:[A-Za-z0-9]"
            r"(?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
            r"[A-Za-z]{2,63}",
            domain,
        )
    ):
        raise ValueError(
            "Domain không hợp lệ. Ví dụ: chinhphu.vn"
        )

    start = time.perf_counter()

    scraper = Export(domain)
    scraper.get_surface_features()

    # Lấy đúng đường dẫn của báo cáo vừa tạo.
    scraper.to_json()
    report_path = Path(scraper.saved_file).resolve() / "report.json"

    execute_time = time.perf_counter() - start

    with report_path.open("r", encoding="utf-8") as f:
        features = json.load(f)

    if not isinstance(features, dict):
        raise ValueError("report.json phải chứa JSON object.")

    return {
        "domain": domain,
        "report_path": str(report_path),
        "execute_time_seconds": round(execute_time, 3),
        "features": features,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")

