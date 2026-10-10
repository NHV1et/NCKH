
import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from web_scraper.export import Export
from ai_bot.infer import predict
from ai_bot.train import train_model


PROJECT_DIR = Path(__file__).resolve().parent


def find_latest_report() -> Path:
    """Tìm report.json mới nhất trong các thư mục scrap_*."""

    reports = list(PROJECT_DIR.glob("scrap_*/report.json"))

    if not reports:
        raise FileNotFoundError(
            f"Không tìm thấy report.json tại {PROJECT_DIR}"
        )

    return max(reports, key=lambda path: path.stat().st_mtime)


def load_report() -> tuple[dict, Path]:
    """Đọc dữ liệu features từ report.json mới nhất."""

    report_path = find_latest_report()

    with report_path.open("r", encoding="utf-8") as f:
        features = json.load(f)

    if not isinstance(features, dict):
        raise ValueError(
            f"{report_path} phải chứa một JSON object."
        )

    return features, report_path


def print_json(data):
    """In dữ liệu dưới dạng JSON dễ đọc."""

    if hasattr(data, "model_dump"):
        data = data.model_dump()
    elif hasattr(data, "dict"):
        data = data.dict()

    print(json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        default=str,
    ))


async def print_mcp_result(result):
    """In kết quả trả về từ MCP."""

    for item in result.content or []:
        if hasattr(item, "text"):
            try:
                print_json(json.loads(item.text))
            except json.JSONDecodeError:
                print(item.text)

    if result.is_error:
        print("MCP tool thực thi thất bại.")


def get_mcp_server_params():
    """Thông số khởi chạy MCP server."""

    return StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "mcp_sv.server"],
        cwd=str(PROJECT_DIR),
        env={
            **os.environ,
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        },
    )


def direct_train():
    """Choice 1: train model trực tiếp."""

    result = train_model()
    print_json(result)


def direct_analyze():
    """Choice 2: phân tích report trực tiếp."""

    features, report_path = load_report()

    print(f"Đọc báo cáo: {report_path}")
    print("Đang phân tích website...")

    result = predict(features)
    print_json(result)


def direct_scrape(domain: str):
    """Choice 3: cào website trực tiếp, không qua MCP."""

    scraper = Export(domain)
    scraper.get_surface_features()
    scraper.to_json()

    report_path = (
        Path(scraper.saved_file).resolve() / "report.json"
    )

    if not report_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy báo cáo: {report_path}"
        )

    print(f"Cào website thành công: {domain}")
    print(f"Báo cáo đã lưu tại: {report_path}")


async def mcp_scrape_and_analyze(domain: str):
    """Choice 4: dùng MCP cào website rồi phân tích."""

    server_params = get_mcp_server_params()

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Đã kết nối MCP.")

            # Bước 1: gọi tool cào website
            print(f"\nĐang cào website: {domain}")

            scan_result = await session.call_tool(
                "scan_website",
                arguments={"domain": domain},
            )

            if scan_result.is_error:
                await print_mcp_result(scan_result)
                return

            # Lấy dữ liệu do tool cào trả về
            scan_data = None

            for item in scan_result.content or []:
                if not hasattr(item, "text"):
                    continue

                try:
                    candidate = json.loads(item.text)
                except json.JSONDecodeError:
                    continue

                if isinstance(candidate, dict):
                    scan_data = candidate
                    break

            if not isinstance(scan_data, dict):
                print("Không đọc được dữ liệu trả về từ MCP Scraper.")
                return

            features = scan_data.get("features")

            if not isinstance(features, dict):
                print("MCP Scraper không trả về features hợp lệ.")
                return

            print("\nCào website thành công.")
            if scan_data.get("report_path"):
                print(f"Báo cáo: {scan_data['report_path']}")

            # Bước 2: gọi tool AI phân tích
            print("\nĐang phân tích bằng AI_BOT...")

            analysis_result = await session.call_tool(
                "analyze_website",
                arguments={"features": features},
            )

            await print_mcp_result(analysis_result)


async def cli_menu():
    while True:
        print("\n=== WEBSITE DETECTION ===")
        print("1. Train model xgboost")
        print("2. Cào website")
        print("3. Phân tích website từ report.json")
        print("4. Cào và phân tích website(MCP)")
        print("0. Thoát")

        choice = input("Chọn chức năng: ").strip()

        if choice == "1":
            try:
                direct_train()
            except Exception as e:
                print(f"Lỗi train model: {e}")

        elif choice == "2":
            domain = input("Nhập domain cần cào: ").strip()

            if not domain:
                print("Domain không được để trống!")
                continue

            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    direct_scrape,
                    domain,
                )
            except Exception as e:
                print(f"Lỗi cào website: {e}")

        elif choice == "3":
            try:
                direct_analyze()
            except Exception as e:
                print(f"Lỗi phân tích website: {e}")
        elif choice == "4":
            domain = input(
                "Nhập domain cần cào và phân tích: "
            ).strip()

            if not domain:
                print("Domain không được để trống!")
                continue

            try:
                await mcp_scrape_and_analyze(domain)
            except Exception as e:
                print(f"Lỗi chạy pipeline MCP: {e}")

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

    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(
            encoding="utf-8",
            errors="replace",
        )

    asyncio.run(cli_menu())
