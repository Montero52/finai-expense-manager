import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load API Key từ .env
load_dotenv()
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

class ExpenseAI:
    def __init__(self):
        # Chọn model nhẹ và nhanh
        self.model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        # Định nghĩa các danh mục chuẩn của bạn để AI chọn
        self.categories = [
            "Ăn uống", "Di chuyển", "Thuê nhà", "Điện nước", 
            "Mua sắm", "Giải trí", "Y tế", "Giáo dục", 
            "Lương", "Thưởng", "Đầu tư", "Khác",
        ]

    def predict(self, text):
        if not text:
            return None
            
        try:
            # Tạo câu lệnh (Prompt) cho AI
            prompt = f"""
            Bạn là trợ lý tài chính. Hãy phân loại giao dịch sau vào đúng MỘT trong các danh mục này: {', '.join(self.categories)}.
            
            Giao dịch: "{text}"
            
            Chỉ trả về tên danh mục chính xác, không giải thích thêm. Nếu không chắc chắn, trả về "Khác".
            """
            
            # Gọi API
            response = self.model.generate_content(prompt)
            predicted_category = response.text.strip()
            
            # Kiểm tra xem AI có trả về đúng danh mục trong list không
            final_cat = predicted_category if predicted_category in self.categories else "Khác"
            
            return {
                'category': final_cat,
                'confidence': 90.0 # LLM thường khá tự tin
            }
            
        except Exception as e:
            print(f"Gemini Error: {e}")
            return None
        
# app/ai_service.py (Thêm vào class ExpenseAI)

# 4. Đi thẳng vào vấn đề, trả lời con số/kết quả ngay câu đầu tiên.
    def chat_with_data(self, user_question, context_data):
        if not user_question:
            return "Xin lỗi, tôi chưa nghe rõ câu hỏi của bạn."

        try:
            # Tạo Prompt (Câu lệnh) cho AI
            # Đây là bí quyết: Nhồi dữ liệu vào prompt để AI "học" ngay lập tức
            prompt = f"""
            Bạn là một trợ lý tài chính cá nhân thông minh, thân thiện và hài hước.
            Dưới đây là dữ liệu tài chính gần đây của người dùng:
            
            {context_data}
            
            Quy tắc trả lời:
            1. Nếu có đưa ra lời khuyên hoặc cảnh báo, HÃY XUỐNG DÒNG 1 LẦN (cách ra 1 dòng trắng) trước khi viết lời khuyên đó.
            2. Hãy trả lời câu hỏi sau của người dùng dựa trên dữ liệu trên (nếu có liên quan). 
            3. Nếu dữ liệu không đủ để trả lời, hãy nói khéo léo.
            4. Bỏ qua các câu chào hỏi rườm rà như "Theo dữ liệu tôi có", "Dựa trên thông tin"...
            5. Nếu thấy người dùng chi tiêu nhiều, hãy cảnh báo ngắn gọn, thân thiện (tối đa 2 câu).
            6. Dùng emoji nhẹ nhàng.

            QUY TẮC QUAN TRỌNG (BẮT BUỘC TUÂN THỦ):
            1. "CHI TIÊU": Là tiền mất đi (mua sắm, ăn uống...).
            2. "CHUYỂN KHOẢN": Là tiền chuyển từ ví này sang ví khác của chính mình.
            3. KHI TÍNH TỔNG CHI TIÊU: TUYỆT ĐỐI KHÔNG được cộng khoản "CHUYỂN KHOẢN" vào. Chỉ tính tổng các khoản có nhãn "CHI TIÊU".

            Câu hỏi: "{user_question}"
            """
            
            # Gọi Gemini
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Chat Error: {e}")
            return "Xin lỗi, hệ thống AI đang bận. Vui lòng thử lại sau."

# Khởi tạo
ai_engine = ExpenseAI()