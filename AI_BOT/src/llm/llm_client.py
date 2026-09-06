from openai import OpenAI


# ============================================================
# Ollama client
# ============================================================

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)


# ============================================================
# Feature descriptions
# ============================================================

FEATURE_DESCRIPTIONS = {
    "Have_IP":
        "URL sử dụng địa chỉ IP thay cho tên miền",

    "Have_At":
        "URL có chứa ký tự @",

    "URL_Length":
        "Độ dài của URL",

    "URL_Depth":
        "Độ sâu của đường dẫn trong URL",

    "Redirection":
        "URL có dấu hiệu chuyển hướng",

    "https_Domain":
        "Domain có sử dụng HTTPS",

    "Tiny_URL":
        "URL sử dụng dịch vụ rút gọn URL",

    "Prefix/Suffix":
        "Domain chứa ký tự '-'",

    "DNS_Record":
        "Thông tin DNS record của domain",

    "Web_Traffic":
        "Mức độ traffic của website",

    "Domain_Age":
        "Tuổi của domain",

    "Domain_End":
        "Thời gian còn lại trước khi domain hết hạn",

    "iFrame":
        "Website sử dụng iframe",

    "Mouse_Over":
        "Website có hành vi đáng chú ý khi rê chuột",

    "Right_Click":
        "Website can thiệp vào chức năng chuột phải",

    "Web_Forwards":
        "Website có dấu hiệu chuyển tiếp hoặc chuyển hướng"
}


# ============================================================
# LLM explanation
# ============================================================

def explain_result(result):
    """
    Dùng LLM để giải thích kết quả XGBoost + SHAP.

    LLM chỉ giải thích kết quả.
    Không được thay đổi label, score hoặc confidence.
    """

    feature_text = "\n".join(
        [
            (
                f"- Feature: {item.feature}\n"
                f"  Ý nghĩa: "
                f"{FEATURE_DESCRIPTIONS.get(item.feature, 'Không có mô tả')}\n"
                f"  Giá trị: {item.value}\n"
                f"  SHAP: {item.impact:.4f}"
            )
            for item in result.feature_impacts
        ]
    )

    prompt = f"""
Bạn là module giải thích kết quả của hệ thống phát hiện phishing website.

Kết quả được đưa ra bởi mô hình XGBoost:

Label: {result.label}
Risk Score: {result.score}/100
Confidence: {result.confidence:.2f}

Các feature có ảnh hưởng lớn nhất theo SHAP:

{feature_text}

Hãy viết một giải thích ngắn gọn bằng tiếng Việt cho người dùng.

QUY TẮC:

1. Không được thay đổi hoặc phủ nhận Label của XGBoost.
2. Không được thay đổi Risk Score hoặc Confidence.
3. Chỉ sử dụng thông tin được cung cấp ở trên.
4. Không tự suy đoán ý nghĩa của feature.
5. SHAP > 0 nghĩa là feature góp phần đẩy dự đoán về phishing.
6. SHAP < 0 nghĩa là feature góp phần đẩy dự đoán về real.
7. Chỉ tập trung vào những feature có ảnh hưởng đáng kể.
8. Nếu Label là phishing, giải thích tại sao mô hình đánh giá website có nguy cơ phishing.
9. Nếu Label là real, giải thích tại sao mô hình đánh giá website có xu hướng an toàn hơn.
10. Không đưa ra các thông tin không có trong dữ liệu.
11. Không đề cập đến Malwarebytes, Symantec hoặc các công cụ khác.
12. Không sử dụng Markdown.
13. Không sử dụng dấu *, # hoặc bullet.
14. Viết khoảng 3-5 câu, dễ hiểu với người dùng bình thường.

Chỉ trả về phần giải thích, không thêm tiêu đề.
"""

    response = client.chat.completions.create(
        model="model-qlks",
        messages=[
            {
                "role": "system",
                "content": (
                    "Bạn là chuyên gia phân tích phishing website. "
                    "Bạn chỉ giải thích kết quả của mô hình và "
                    "không được tự ý thay đổi kết quả."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()