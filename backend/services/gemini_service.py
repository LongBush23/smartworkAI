import os
import json
import google.generativeai as genai
from typing import Dict, Any

# Load API key from env or fallback
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

async def get_match_score_from_gemini(user: dict, task: dict) -> Dict[str, Any]:
    """
    Sử dụng Gemini để đánh giá độ khớp giữa nhân viên và công việc.
    Trả về: {"match_score": int, "reasoning": str}
    """
    if not GEMINI_API_KEY:
        # Fallback if no API key
        return fallback_match_logic(user, task)
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        user_info = {
            "name": user.get("name"),
            "role": user.get("role"),
            "skills": [s.get("skill_name") for s in user.get("skills", [])],
            "bio": user.get("bio"),
            "preferences": user.get("preferences", {})
        }
        
        task_info = {
            "title": task.get("title"),
            "description": task.get("description"),
            "required_skills": task.get("required_skills", [])
        }
        
        prompt = f"""
        Bạn là một chuyên gia Quản trị Nhân sự (HR) và Phân bổ Nguồn lực AI.
        Hãy đánh giá độ phù hợp (Match Score) từ 0 đến 100 giữa nhân viên và công việc sau đây.
        
        Thông tin nhân viên:
        {json.dumps(user_info, ensure_ascii=False, indent=2)}
        
        Yêu cầu công việc:
        {json.dumps(task_info, ensure_ascii=False, indent=2)}
        
        Hãy trả về kết quả dưới định dạng JSON hợp lệ chính xác như sau, không kèm markdown code block:
        {{
            "match_score": [điểm số từ 0 đến 100],
            "reasoning": "[Lý do ngắn gọn giải thích tại sao lại cho điểm số này, viết bằng tiếng Việt]"
        }}
        """
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3]
        elif text.startswith("```"):
            text = text[3:-3]
            
        result = json.loads(text)
        return {
            "match_score": float(result.get("match_score", 50)),
            "reasoning": result.get("reasoning", "Dựa trên phân tích AI cơ bản.")
        }
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return fallback_match_logic(user, task)


def fallback_match_logic(user: dict, task: dict) -> Dict[str, Any]:
    """Logic mặc định khi không có Gemini API key"""
    required_skills = task.get("required_skills", [])
    if not required_skills:
        ai_metrics = user.get("ai_metrics", {})
        quality = ai_metrics.get("historical_quality_score", 50)
        on_time = ai_metrics.get("on_time_rate", 0.5) * 100
        score = round((quality * 0.6 + on_time * 0.4), 1)
        return {"match_score": score, "reasoning": "Dựa trên hiệu suất làm việc lịch sử (Không có Gemini)."}

    user_skills = {s["skill_name"].lower(): s.get("self_rating", 3) for s in user.get("skills", [])}
    matched = sum(1 for rs in required_skills if rs.lower() in user_skills)
    coverage = matched / len(required_skills) if required_skills else 1
    
    ai_metrics = user.get("ai_metrics", {})
    quality = ai_metrics.get("historical_quality_score", 50)
    
    final_score = coverage * 70 + quality * 0.3
    return {
        "match_score": round(max(0, min(100, final_score)), 1),
        "reasoning": f"Khớp {matched}/{len(required_skills)} kỹ năng yêu cầu (Không có Gemini)."
    }

async def chat_with_gemini(message: str, user_name: str, history: list = None) -> str:
    """
    Trợ lý AI trả lời tin nhắn của người dùng dựa trên mô hình Gemini.
    """
    if not GEMINI_API_KEY:
        return "Xin lỗi, API Key của Gemini chưa được cấu hình. Vui lòng liên hệ Admin."

    try:
        system_prompt = f"""
        Bạn là SmartWork AI, một trợ lý ảo thông minh được tích hợp trực tiếp vào phần mềm quản lý công việc và nhân sự SmartWork.
        Bạn đang trò chuyện với người dùng tên là '{user_name}'.
        
        Nhiệm vụ của bạn:
        1. Giải đáp các thắc mắc liên quan đến tính năng của hệ thống (Quản lý dự án, Công việc, Đánh giá nhân sự, Dự báo tiến độ).
        2. Hỗ trợ nhân viên về mặt chuyên môn hoặc giải quyết lỗi code/công việc nếu họ cần.
        3. Luôn giữ thái độ chuyên nghiệp, thân thiện, trả lời ngắn gọn, có cấu trúc rõ ràng (sử dụng markdown).
        4. Hạn chế tối đa việc trả lời các câu hỏi không liên quan đến công việc hoặc phần mềm.
        
        Tin nhắn của người dùng: {message}
        """

        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(system_prompt)
        except Exception as inner_e:
            if "404" in str(inner_e):
                model = genai.GenerativeModel('gemini-flash-latest')
                response = model.generate_content(system_prompt)
            else:
                raise inner_e
                
        return response.text

    except Exception as e:
        print(f"Gemini Chat Error: {str(e)}")
        return "Tôi đang gặp chút sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau nhé."
