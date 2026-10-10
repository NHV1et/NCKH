from openai import OpenAI

# Ollama client
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    timeout=120.0,
)

MODEL_NAME = "model-qlks"  


FEATURE_DESCRIPTIONS = {
    "has_ip_address_in_url":
        "URL sử dụng địa chỉ IP thay cho tên miền",

    "has_sus_sign":
        "URL chứa dấu hiệu hoặc ký tự đáng ngờ theo quy tắc trích xuất feature",

    "has_prefix":
        "Domain có dấu hiệu tiền tố đáng ngờ theo quy tắc trích xuất feature",

    "has_signature":
        "Feature chữ ký hoặc dấu hiệu nhận diện được mã hóa thành giá trị phân loại",

    "has_icon":
        "Feature liên quan đến biểu tượng website",

    "long_url":
        "URL có độ dài đáng chú ý theo quy tắc trích xuất feature",

    "domain_has_https":
        "Domain hoặc URL có sử dụng HTTPS theo cách crawler kiểm tra",

    "shortcut_url":
        "URL sử dụng dịch vụ rút gọn liên kết",

    "has_index":
        "Feature liên quan đến trang hoặc đường dẫn index",

    "has_sus_port":
        "Website sử dụng cổng được quy tắc kiểm tra đánh dấu đáng ngờ",

    "has_dns_records":
        "Domain có bản ghi DNS theo kết quả thu thập",

    "short_domain_age":
        "Domain có tuổi đời ngắn theo ngưỡng crawler sử dụng",

    "short_domain_registation_length":
        "Thời hạn đăng ký domain ngắn theo quy tắc trích xuất feature",

    "trusted_ssl_certificate":
        "Mức phân loại chứng chỉ SSL/TLS theo quy tắc của crawler",

    "disabled_right_click":
        "Website có hành vi vô hiệu hóa chuột phải",

    "on_mouse_over":
        "Website có hành vi được kiểm tra khi rê chuột",

    "multi_web_forward":
        "Website có nhiều lần chuyển tiếp hoặc chuyển hướng",

    "abnormal_url_anchor":
        "Liên kết neo trên website có dấu hiệu bất thường",

    "has_emc":
        "Feature liên quan đến dấu hiệu EMC theo định nghĩa của crawler",

    "has_iframe_hidden":
        "Website có iframe bị ẩn theo quy tắc kiểm tra",

    "has_nca":
        "Feature NCA theo định nghĩa trong bộ trích xuất dữ liệu",

    "high_web_rank":
        "Feature thứ hạng website theo nguồn hoặc quy tắc thu thập",

    "high_domain_rating":
        "Feature đánh giá domain theo nguồn hoặc quy tắc thu thập",
}


def explain_result(result):
    feature_lines = []

    for item in result.feature_impacts:
        feature_lines.append(
            f"- {item.feature}: "
            f"giá trị={item.value}, "
            f"SHAP={item.impact:.4f}"
        )

    feature_text = "\n".join(feature_lines)

    if result.label == "phishing":
        conclusion = "Mô hình phân loại website là phishing."
    elif result.label == "real":
        conclusion = "Mô hình phân loại website là real."
    else:
        conclusion = f"Mô hình trả về nhãn {result.label}."

    prompt = f"""
Bạn là thành phần giải thích kết quả của hệ thống phát hiện
website giả mạo bằng machine learning.

KẾT QUẢ ĐÃ ĐƯỢC XGBOOST DỰ ĐOÁN:
- Nhãn: {result.label}
- Điểm rủi ro: {result.score}/100
- Độ tin cậy: {result.confidence:.4f}

CÁC FEATURE CÓ ẢNH HƯỞNG ĐẾN DỰ ĐOÁN:
{feature_text}

Hãy viết một đoạn giải thích kết quả bằng tiếng Việt, khoảng 4-6 câu.

Yêu cầu:
1. Giải thích ý nghĩa của nhãn dự đoán và điểm rủi ro.
2. Phân tích những feature đóng góp đáng kể nhất vào kết quả.
3. Kết nối các dấu hiệu với lý do mô hình đưa ra dự đoán,
   thay vì chỉ liệt kê hoặc định nghĩa feature.
4. Không tự thay đổi nhãn, điểm rủi ro hoặc độ tin cậy.
5. Không khẳng định website chắc chắn an toàn hoặc lừa đảo.
6. Không suy diễn rằng website có hành vi đánh cắp dữ liệu
   nếu dữ liệu đầu vào không chứng minh điều đó.
7. Chỉ diễn giải chiều tác động của SHAP khi đã xác nhận
   chiều đó tương ứng với đầu ra của lớp phishing.
8. Nếu dữ liệu chưa đủ để giải thích một kết luận,
   hãy nêu rõ giới hạn đó.
9. Chỉ trả về đoạn giải thích, không dùng tiêu đề hay danh sách.

Lưu ý:
Điểm rủi ro thể hiện xác suất dự đoán của lớp phishing theo thang
0-100 nếu hệ thống đã được cấu hình như vậy.
Độ tin cậy là confidence riêng, không đồng nghĩa với điểm rủi ro.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn giải thích kết quả của mô hình machine learning. "
                        "Không phân loại lại website và không tự tạo dữ liệu."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        explanation = response.choices[0].message.content

        if not explanation or not explanation.strip():
            return conclusion + " Chưa tạo được giải thích chi tiết."

        return conclusion + " " + explanation.strip()

    except Exception:
        return (
            conclusion
            + " Không thể tạo phần giải thích chi tiết bằng LLM."
        )