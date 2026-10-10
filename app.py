
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_DIR = Path(__file__).resolve().parent
REPORT_PATH = PROJECT_DIR / "report.json"


def load_report() -> dict:
    """Đọc features từ report.json."""

    if not REPORT_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file report.json: {REPORT_PATH}"
        )

    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        features = json.load(f)

    if not isinstance(features, dict):
        raise ValueError(
            "report.json phải chứa một JSON object."
        )

    return features


async def print_result(result):
    """In kết quả trả về từ MCP."""

    for item in result.content or []:
        if hasattr(item, "text"):
            try:
                # Nếu MCP trả về JSON dạng chuỗi
                data = json.loads(item.text)
                print(json.dumps(
                    data,
                    ensure_ascii=False,
                    indent=2,
                ))
            except json.JSONDecodeError:
                print(item.text)

    if result.is_error:
        print("MCP tool thực thi thất bại.")


async def cli_menu():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "mcp_sv.server"],
        cwd=str(PROJECT_DIR),
        env={
            **__import__("os").environ,
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        },
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Kết nối MCP thành công.")

            while True:
                print("\n=== AI_BOT WEBSITE DETECTION ===")
                print("1. Train model (MCP)")
                print("2. Phân tích website từ report.json (MCP)")
                print("0. Thoát")

                choice = input("Chọn chức năng: ").strip()

                if choice == "1":
                    result = await session.call_tool(
                        "train_website_model",
                        arguments={},
                    )
                    await print_result(result)

                elif choice == "2":
                    try:
                        features = load_report()
                    except (OSError, json.JSONDecodeError, ValueError) as e:
                        print(f"Lỗi đọc report.json: {e}")
                        continue

                    print(f"Đã đọc dữ liệu từ: {REPORT_PATH}")
                    print("Đang phân tích website...")

                    try:
                        result = await session.call_tool(
                            "analyze_website",
                            arguments={"features": features},
                        )
                        await print_result(result)
                    except Exception as e:
                        print(f"Lỗi gọi MCP: {e}")

                elif choice == "0":
                    print("Đã thoát.")
                    break

                else:
                    print("Lựa chọn không hợp lệ.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(
            encoding="utf-8",
            errors="replace",
        )

    asyncio.run(cli_menu())
