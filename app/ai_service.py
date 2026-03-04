import os
import json
from dotenv import load_dotenv

# Import theo chuẩn SDK mới nhất
from google import genai
from google.genai import types

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Load API Key từ file .env
load_dotenv()

class ExpenseAI:
    def __init__(self):
        # Khởi tạo Client mới thay vì configure global
        api_key = os.environ.get('GEMINI_API_KEY')
        self.client = genai.Client(api_key=api_key)
        
        # Tên model chuẩn cho SDK mới (không cần tiền tố 'models/')
        self.model_name = 'gemini-2.5-flash'

    def predict(self, text, user_categories):
        """
        Dự đoán danh mục chi tiêu dựa trên danh sách danh mục CỦA RIÊNG NGƯỜI DÙNG.
        Ép kiểu trả về là JSON bằng types.GenerateContentConfig.
        """
        if not text or not user_categories:
            return None
            
        try:
            prompt = f"""
            Bạn là một hệ thống phân loại tài chính tự động. 
            Nhiệm vụ: Phân loại giao dịch sau vào đúng MỘT trong các danh mục người dùng đã tạo.
            
            Danh mục hiện có: {', '.join(user_categories)}
            Giao dịch cần phân loại: "{text}"
            
            Yêu cầu BẮT BUỘC: 
            - Chỉ trả về định dạng JSON hợp lệ. Không giải thích gì thêm.
            - Nếu không có danh mục nào phù hợp, category hãy để là "Khác".
            - confidence là độ tự tin của bạn (từ 0 đến 100).
            
            Định dạng trả về:
            {{"category": "Tên danh mục", "confidence": 95}}
            """
            
            # Gọi API theo cú pháp của thư viện mới
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            # Parse chuỗi JSON thành Dictionary Python
            result = json.loads(response.text.strip())
            
            # Đảm bảo an toàn: Nếu AI bịa ra danh mục không có, gán về "Khác"
            if result.get('category') not in user_categories:
                result['category'] = "Khác"
                
            return result
            
        except Exception as e:
            print(f"Gemini Predict Error: {e}")
            return None
        
    def chat_with_data(self, user_question, context_data):
        if not user_question:
            return "Xin lỗi, tôi chưa nghe rõ câu hỏi của bạn."

        try:
            prompt = f"""
            Bạn là FinAI – một trợ lý tài chính cá nhân thông minh, thân thiện, nói chuyện tự nhiên như một người bạn hiểu về tiền bạc.

            Dữ liệu tài chính gần đây của người dùng:
            {context_data}

            Câu hỏi: "{user_question}"

            Cách trả lời:
            - Trả lời kết quả chính ngay câu đầu tiên (ngắn gọn, rõ ràng).
            - Viết như đang nói chuyện thật, KHÔNG mang văn phong báo cáo.
            - Không dùng các câu mở đầu kiểu: "Dựa trên dữ liệu...", "Theo thông tin tôi có..."
            - Nếu có lời khuyên hoặc cảnh báo, hãy xuống dòng 1 lần trước khi viết.
            - Dùng emoji nhẹ nhàng (1–2 cái là đủ).
            - Giữ câu trả lời trong 3–6 câu, tránh lan man.

            Nếu thiếu dữ liệu, hỏi lại một cách tự nhiên như đang trò chuyện.

            QUY TẮC KẾ TOÁN (BẮT BUỘC):
            - "CHI TIÊU" = tiền ra khỏi hệ thống.
            - "CHUYỂN KHOẢN" = tiền chuyển giữa ví của bạn → KHÔNG phải chi tiêu.
            - Khi tính tổng chi tiêu: TUYỆT ĐỐI không cộng chuyển khoản.
            """
            
            # Trả về một "Luồng" (Generator) thay vì văn bản tĩnh
            response_stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt
            )
            return response_stream
            
        except Exception as e:
            print(f"Chat Error: {e}")
            return "Xin lỗi, hệ thống AI đang bận kết nối. Vui lòng thử lại sau vài giây nhé!"

# Khởi tạo Singleton Engine
ai_engine = ExpenseAI()