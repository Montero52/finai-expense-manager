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
            Bạn là một trợ lý tài chính cá nhân thông minh, thân thiện và hài hước của FinAI.
            Dưới đây là dữ liệu tài chính gần đây của người dùng (Đã được tổng hợp):
            
            {context_data}
            
            Câu hỏi của người dùng: "{user_question}"
            
            Quy tắc trả lời:
            1. Đi thẳng vào vấn đề, trả lời con số/kết quả ngay câu đầu tiên.
            2. Nếu có đưa ra lời khuyên hoặc cảnh báo, HÃY XUỐNG DÒNG 1 LẦN (cách ra 1 dòng trắng) trước khi viết lời khuyên đó.
            3. Nếu dữ liệu không đủ để trả lời, hãy nói khéo léo và yêu cầu người dùng nhập thêm.
            4. Bỏ qua các câu chào hỏi rườm rà như "Theo dữ liệu tôi có", "Dựa trên thông tin"...
            5. Dùng emoji nhẹ nhàng để tạo cảm giác thân thiện.

            QUY TẮC KẾ TOÁN (BẮT BUỘC TUÂN THỦ):
            1. "CHI TIÊU": Là tiền mất đi.
            2. "CHUYỂN KHOẢN": Là tiền luân chuyển giữa các ví của chính mình, KHÔNG PHẢI LÀ CHI TIÊU.
            3. KHI TÍNH TỔNG CHI TIÊU: TUYỆT ĐỐI KHÔNG cộng các khoản "CHUYỂN KHOẢN" vào.
            """
            
            # Gọi text thông thường không cần ép JSON
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
            
        except Exception as e:
            print(f"Chat Error: {e}")
            return "Xin lỗi, hệ thống AI đang bận kết nối. Vui lòng thử lại sau vài giây nhé!"

# Khởi tạo Singleton Engine
ai_engine = ExpenseAI()