from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from backend.database import db
from backend.security import get_current_user
from backend.dependencies import (
    require_leader_or_above,
    require_director_or_above,
    require_admin
)
from backend.models.kpi_schemas import (
    KPICatalogCreate, KPICatalogUpdate, KPICatalogResponse,
    KPIEvaluationCreate, KPIEvaluationResponse,
    SelfEvaluationSubmit, ReviewSubmit, GeneralCriteriaSubmit
)
from backend.services.kpi_service import (
    process_evaluation_approval, get_kpi_ranking,
    get_quarterly_kpi, get_yearly_kpi
)

router = APIRouter(prefix="/api/kpi", tags=["KPI"])

# Tiêu chí chung theo Phụ lục Hướng dẫn số 20-HD/ĐUCA
_CRITERIA_TEMPLATES = {
    "collective": {
        "id": "collective",
        "type": "collective",
        "name": "Tiêu chí chung đối với tập thể",
        "total_max_score": 30,
        "criteria": [
            {
                "id": "A1", "max_score": 5,
                "name": "Kết quả công tác xây dựng, chỉnh đốn Đảng và hệ thống chính trị; xây dựng tổ chức đảng trong sạch vững mạnh; nâng cao chất lượng cán bộ, đảng viên theo nghị quyết, kế hoạch, chỉ tiêu được cấp có thẩm quyền giao."
            },
            {
                "id": "A2", "max_score": 5,
                "name": "Năng lực lãnh đạo của cấp ủy, tổ chức đảng trong CAND theo thẩm quyền; hiệu quả lãnh đạo, chỉ đạo của cấp ủy, chỉ đạo đối với đơn vị, cá nhân trong phối hợp kết nối nội bộ."
            },
            {
                "id": "A3", "max_score": 5,
                "name": "Hiệu quả trong công tác thanh tra, kiểm tra, giám sát và kỷ luật đảng; thực hiện các quy định về phòng, chống tham nhũng, lãng phí, tiêu cực; thực hiện các quy định về 'tự diễn biến', 'tự chuyển hóa' trong nội bộ."
            },
            {
                "id": "A4", "max_score": 5,
                "name": "Kết quả thực hiện các nguyên tắc tổ chức và hoạt động của đảng, việc chấp hành quy chế làm việc, lề lối làm việc; tổ chức và hoạt động của đảng, việc chấp hành quy chế làm việc."
            },
            {
                "id": "A5", "max_score": 5,
                "name": "Kết quả lãnh đạo, chỉ đạo, tổ chức thực hiện nhiệm vụ chính trị; xây dựng văn hóa công vụ trong hoạt động quản lý lý, điều hành, công tác tổ chức cán bộ."
            },
            {
                "id": "A6", "max_score": 5,
                "name": "Tình thần tự phê bình và phê bình, tu sửa của tập thể đơn vị; kết quả khắc phục những hạn chế, khuyết điểm đã được chỉ ra trong các kỳ kiểm điểm trước hoặc qua thanh tra, kiểm tra, giám sát."
            }
        ]
    },
    "leader": {
        "id": "leader",
        "type": "leader",
        "name": "Tiêu chí chung đối với cá nhân là lãnh đạo, chỉ huy",
        "total_max_score": 30,
        "criteria": [
            {
                "id": "II_1", "max_score": 18,
                "name": "Về phẩm chất chính trị, đạo đức, lối sống, thực hiện trách nhiệm nêu gương",
                "sub_criteria": [
                    {"id": "II_1_1", "max_score": 2, "name": "Tuyệt đối trung thành với Đảng, Tổ quốc và Nhân dân; kiên định, bảo vệ và thực hiện các quy định về phòng, chống tham nhũng, lãng phí, tiêu cực; kiên định lập trường, quan điểm, tư tưởng Mác-Lênin, tư tưởng Hồ Chí Minh."},
                    {"id": "II_1_2", "max_score": 2, "name": "Về tinh thần yêu nước sâu sắc, tận tụy phục vụ Nhân dân; luôn hành động vì lợi ích của Đảng, của Nhân dân; giữ gìn và bảo vệ uy tín, danh dự của Đảng, Nhà nước, lực lượng CAND."},
                    {"id": "II_1_3", "max_score": 2, "name": "Chấp hành nghiêm chủ trương của Đảng, nghị quyết, chỉ thị, quy định, nguyên tắc tổ chức của Đảng; chính sách, pháp luật của Nhà nước và quy định, quy chế của cơ quan, đơn vị, địa phương."},
                    {"id": "II_1_4", "max_score": 2, "name": "Tư tưởng công tác rõ ràng, kiên quyết, dứt khoát, không dao động; các nghị quyết, chỉ thị được thi hành nghiêm, phương pháp, cách thức triển khai khoa học, thuyết phục."},
                    {"id": "II_1_5", "max_score": 2, "name": "Có phẩm chất đạo đức tốt, lối sống lành mạnh, không có biểu hiện cơ hội, vụ lợi; không có biểu hiện 'tự diễn biến', 'tự chuyển hóa'; thực hiện nghiêm quy định về những điều đảng viên không được làm."},
                    {"id": "II_1_6", "max_score": 2, "name": "Không tham nhũng, không biểu hiện suy thoái về tư tưởng chính trị, đạo đức, lối sống; không có biểu hiện về 'tự diễn biến', 'tự chuyển hóa'."},
                    {"id": "II_1_7", "max_score": 2, "name": "Thực hiện kế hoạch khai, thực hiện các cam kết, công khai tài sản, thu nhập theo quy định."},
                    {"id": "II_1_8", "max_score": 2, "name": "Báo cáo đầy đủ, trung thực, cung cấp thông tin chính xác, khách quan về những nội dung liên quan đến tổ chức đảng, đơn vị."},
                    {"id": "II_1_9", "max_score": 2, "name": "Gắn bó đoàn kết nội bộ; có quan hệ tốt với đồng chí, đồng nghiệp; tích cực tham gia xây dựng tổ chức đảng và các cơ quan Nhà nước, các tổ chức chính trị, xã hội."}
                ]
            },
            {
                "id": "II_2", "max_score": 8,
                "name": "Tư duy đổi mới, chiến lược, khát vọng công hiến, dám nghĩ, dám làm, dám chịu trách nhiệm",
                "sub_criteria": [
                    {"id": "II_2_1", "max_score": 1, "name": "Có tư duy đổi mới, làm nhân chủ chức hoạch cán bộ CAND theo hướng: phát huy sức mạnh lãnh đạo, khả năng lãnh đạo, chỉ đạo thực tiễn; tổ chức thực hiện nhiệm vụ hiệu quả, vững mạnh."},
                    {"id": "II_2_2", "max_score": 1, "name": "Luôn bám sát thực tiễn, có nhiều cách làm hay, sáng tạo, đạt hiệu quả cao trong lãnh đạo, chỉ đạo, tổ chức thực hiện nhiệm vụ; vì sự ổn định, phát triển của đơn vị."},
                    {"id": "II_2_3", "max_score": 1, "name": "Nói đối với lãnh đạo và cá nhân tập thể, đơn vị, công tác và các đơn vị có liên quan trong thực hiện nhiệm vụ, lề hành chính chiến lược, hành vi chiến lược."},
                    {"id": "II_2_4", "max_score": 1, "name": "Có khát vọng công hiến, đề xuất hoặc quyết định những giải pháp phù hợp, kịp thời, hiệu quả mạnh."}
                ]
            },
            {
                "id": "II_3", "max_score": 2,
                "name": "Về tự phê bình và phê bình, khắc phục hạn chế, khuyết điểm"
            },
            {
                "id": "II_4", "max_score": 2,
                "name": "Tự soi, tự sửa trên tinh thần trách nhiệm chính trị cao, không né tránh, không đổ lỗi"
            }
        ]
    },
    "staff": {
        "id": "staff",
        "type": "staff",
        "name": "Tiêu chí chung đối với cá nhân không là lãnh đạo, chỉ huy",
        "total_max_score": 30,
        "criteria": [
            {
                "id": "III_1", "max_score": 20,
                "name": "Về chính trị, phẩm chất đạo đức và ý thức tổ chức kỷ luật",
                "sub_criteria": [
                    {"id": "III_1_1", "max_score": 2, "name": "Có chính trị, phẩm chất đạo đức và ý thức tổ chức kỷ luật; kiên định lập trường, không dao động trước mọi"},
                    {"id": "III_1_2", "max_score": 2, "name": "Thực hiện các nguyên tắc tổ chức và hoạt động của Đảng, nhất là nguyên tắc tập trung dân chủ, chấp hành nghiêm lời giải, chỉ, quyết định của Đảng, pháp luật Nhà nước; tư tưởng Hồ Chí Minh, không có biểu hiện suy thoái, 'tự diễn biến', 'tự chuyển hóa'. Không có tư tưởng cục bộ, địa phương."},
                    {"id": "III_1_3", "max_score": 2, "name": "Có ý thức chính trị tư tưởng vững vàng; kiên quyết bảo vệ quan điểm, chủ trương, đường lối của Đảng, chính sách pháp luật của Nhà nước. Tuyệt đối không có biểu hiện chạy chức, chạy quyền, chạy tuổi, chạy bằng cấp."},
                    {"id": "III_1_4", "max_score": 2, "name": "Có phẩm chất đạo đức tốt, lối sống lành mạnh, không tham nhũng, không vi phạm Quy định về những điều đảng viên không được làm. Không có tư tưởng phân biệt đối xử, không tham gia bè phái, cục bộ; không gây mất đoàn kết nội bộ."},
                    {"id": "III_1_5", "max_score": 2, "name": "Có ý thức tổ chức kỷ luật, giữ gìn lối sống đạo đức, chấp hành các quy định của đơn vị, không có biểu hiện 'tự diễn biến', 'tự chuyển hóa'; không có tư tưởng cơ hội, thực dụng, cá nhân chủ nghĩa; không có những biểu hiện 'tu chuyển hóa' trong nội bộ."},
                    {"id": "III_1_6", "max_score": 2, "name": "Không tham nhũng, không biểu hiện tham nhũng; không vi phạm quy định về những điều đảng viên không được làm; không có những biểu hiện suy thoái về tư tưởng chính trị, đạo đức, lối sống. Không có những biểu hiện 'tự diễn biến', 'tự chuyển hóa'."},
                    {"id": "III_1_7", "max_score": 2, "name": "Thực hiện đầy đủ, trung thực, cung cấp thông tin chính xác, khách quan về tài sản, thu nhập theo quy định."},
                    {"id": "III_1_8", "max_score": 2, "name": "Báo cáo đầy đủ, trung thực, cung cấp thông tin chính xác, khách quan về những nội dung liên quan đến tổ chức đảng, đơn vị và về mình theo quy định."},
                    {"id": "III_1_9", "max_score": 2, "name": "Gắn bó đoàn kết nội bộ; có quan hệ tốt với đồng chí, đồng nghiệp; tích cực tham gia xây dựng tổ chức đảng và các cơ quan Nhà nước, các tổ chức chính trị, xã hội, cộng đồng."},
                    {"id": "III_1_10", "max_score": 2, "name": "Gắn gũi, sâu sát với cơ sở; thực hiện tốt việc gữ mối liên hệ với cấp ủy và Nhân dân nơi cư trú."}
                ]
            },
            {
                "id": "III_2", "max_score": 8,
                "name": "Về năng lực chuyên môn, nghiệp vụ theo yêu cầu của vị trí việc làm; khả năng đáp ứng yêu cầu thực hiện nhiệm vụ; tình thần",
                "sub_criteria": [
                    {"id": "III_2_1", "max_score": 2, "name": "Năng lực chuyên môn, nghiệp vụ theo yêu cầu của vị trí việc làm: (1) Có hiểu biết đầy đủ về lĩnh vực công tác; (2) Thường xuyên cập nhật kiến thức mới, cải tiến quy trình nghiệp vụ; (3) Có kỹ năng xử lý độc lập, làm việc nhóm hiệu quả; (4) Khả năng ứng dụng công nghệ thông tin."},
                    {"id": "III_2_2", "max_score": 2, "name": "Khả năng đáp ứng yêu cầu thực hiện nhiệm vụ được giao: (1) Nhiệm vụ thường xuyên: Có khả năng đáp ứng tốt yêu cầu; (2) Nhiệm vụ đột xuất: Phối hợp theo kế hoạch điều tri trong định chất lượng chuyên môn, nghiệp vụ đề xuất giải pháp; các ứng dụng kỹ thuật, thực hành đủ chuẩn."},
                    {"id": "III_2_3", "max_score": 2, "name": "Thái độ công tác trong thực hiện nhiệm vụ: (1) Tinh thần trách nhiệm, tích cực trong công cộng; đề xuất cải điều kiện làm việc, phong cách làm việc chuẩn mực; lề hành chính chiến lược, quy trình chuẩn mực, vì lợi ích chung. (2) Có thể đóng góp mức, phong cách tan của nhiệm vụ vụ và các cấp đơn vị, tập thể, lề hành chính chiến lược nhiệm vụ vụ được giao."},
                    {"id": "III_2_4", "max_score": 2, "name": "Về tự phê bình và phê bình, khắc phục hạn chế, khuyết điểm: Tình thân tự phê bình, tu sửa của cá nhân, tự sửa của các cán bộ, phê bình những hạn chế, khuyết điểm của bản thân và kết quả khắc phục những hạn chế, khuyết điểm đã được chỉ ra."}
                ]
            },
            {
                "id": "III_3", "max_score": 2,
                "name": "Tự soi, tự sửa trên tinh thần trách nhiệm chính trị cao, không né tránh, không đổ lỗi"
            }
        ]
    }
}

# ================= 1. DANH MỤC NHIỆM VỤ CÔNG TÁC =================

@router.get("/catalog", response_model=List[KPICatalogResponse])
async def get_kpi_catalogs(
    department_id: Optional[str] = None,
    period_year: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if department_id:
        query["department_id"] = department_id
    if period_year:
        query["period_year"] = period_year
        
    cursor = db.kpi_task_catalog.find(query)
    catalogs = await cursor.to_list(length=None)
    for c in catalogs:
        c["id"] = str(c.pop("_id"))
    return catalogs

@router.post("/catalog", response_model=KPICatalogResponse)
async def create_kpi_catalog(
    catalog_in: KPICatalogCreate,
    current_user: dict = Depends(require_director_or_above)
):
    doc = catalog_in.model_dump()
    doc["status"] = "draft"
    doc["created_by"] = str(current_user["_id"])
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()
    
    # Ensure IDs are string
    for item in doc["items"]:
        item["id"] = str(item.get("id", ObjectId()))
    
    result = await db.kpi_task_catalog.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return doc

@router.put("/catalog/{catalog_id}/approve")
async def approve_kpi_catalog(
    catalog_id: str,
    current_user: dict = Depends(require_director_or_above)
):
    result = await db.kpi_task_catalog.update_one(
        {"_id": ObjectId(catalog_id)},
        {
            "$set": {
                "status": "approved",
                "approved_by": str(current_user["_id"]),
                "approved_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Catalog not found")
    return {"message": "Catalog approved"}

# ================= 2. QUẢN LÝ KỲ ĐÁNH GIÁ =================

@router.post("/evaluations", response_model=KPIEvaluationResponse)
async def create_evaluation(
    eval_in: KPIEvaluationCreate,
    current_user: dict = Depends(require_leader_or_above)
):
    # Determine target details
    if eval_in.evaluation_type.value == "individual":
        target = await db.users.find_one({"_id": ObjectId(eval_in.target_id)})
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        target_name = target.get("name", target.get("username"))
        target_role = target.get("role")
        department_id = target.get("department_id")
    else:
        target = await db.departments.find_one({"_id": ObjectId(eval_in.target_id)})
        if not target:
            raise HTTPException(status_code=404, detail="Department not found")
        target_name = target.get("name")
        target_role = None
        department_id = str(target["_id"])
        
    doc = {
        "evaluation_type": eval_in.evaluation_type.value,
        "target_id": eval_in.target_id,
        "target_name": target_name,
        "target_role": target_role,
        "department_id": department_id,
        "period_type": eval_in.period_type.value,
        "period_month": eval_in.period_month,
        "period_year": eval_in.period_year,
        "overall_status": "draft",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.kpi_evaluations.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return doc

@router.get("/evaluations", response_model=List[KPIEvaluationResponse])
async def list_evaluations(
    target_id: Optional[str] = None,
    department_id: Optional[str] = None,
    period_type: Optional[str] = None,
    period_year: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if target_id:
        query["target_id"] = target_id
    elif current_user["role"] == "staff":
        query["target_id"] = str(current_user["_id"])
        
    if department_id:
        query["department_id"] = department_id
    if period_type:
        query["period_type"] = period_type
    if period_year:
        query["period_year"] = period_year
        
    cursor = db.kpi_evaluations.find(query)
    evaluations = await cursor.to_list(length=None)
    for e in evaluations:
        e["id"] = str(e.pop("_id"))
    return evaluations

@router.get("/evaluations/{eval_id}", response_model=KPIEvaluationResponse)
async def get_evaluation(
    eval_id: str,
    current_user: dict = Depends(get_current_user)
):
    doc = await db.kpi_evaluations.find_one({"_id": ObjectId(eval_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    doc["id"] = str(doc.pop("_id"))
    return doc

# ================= 3. QUY TRÌNH ĐÁNH GIÁ 3 BƯỚC =================

@router.put("/evaluations/{eval_id}/self-evaluate")
async def submit_self_evaluation(
    eval_id: str,
    eval_in: SelfEvaluationSubmit,
    current_user: dict = Depends(get_current_user)
):
    # Basic check - ensure user owns this evaluation if they are staff
    eval_doc = await db.kpi_evaluations.find_one({"_id": ObjectId(eval_id)})
    if not eval_doc:
        raise HTTPException(status_code=404, detail="Evaluation not found")
        
    if current_user["role"] == "staff" and eval_doc["target_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not allowed to evaluate this target")
    
    self_eval_data = {
        "status": "submitted",
        "submitted_at": datetime.utcnow(),
        "task_scores": [t.model_dump() for t in eval_in.task_scores],
        "proposed_rating": eval_in.proposed_rating.value
    }
    
    await db.kpi_evaluations.update_one(
        {"_id": ObjectId(eval_id)},
        {
            "$set": {
                "self_evaluation": self_eval_data,
                "overall_status": "self_evaluating",
                "updated_at": datetime.utcnow()
            }
        }
    )
    return {"message": "Self evaluation submitted"}

@router.put("/evaluations/{eval_id}/review")
async def submit_review(
    eval_id: str,
    review_in: ReviewSubmit,
    current_user: dict = Depends(require_leader_or_above)
):
    review_data = {
        "status": "reviewed",
        "reviewed_by": str(current_user["_id"]),
        "reviewed_at": datetime.utcnow(),
        "task_scores": [t.model_dump() for t in review_in.task_scores],
        "review_note": review_in.review_note
    }
    
    await db.kpi_evaluations.update_one(
        {"_id": ObjectId(eval_id)},
        {
            "$set": {
                "review": review_data,
                "overall_status": "reviewing",
                "updated_at": datetime.utcnow()
            }
        }
    )
    return {"message": "Review submitted"}

@router.put("/evaluations/{eval_id}/approve")
async def approve_evaluation(
    eval_id: str,
    current_user: dict = Depends(require_director_or_above)
):
    try:
        result = await process_evaluation_approval(eval_id, str(current_user["_id"]))
        return {"message": "Evaluation approved", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/evaluations/{eval_id}/general-criteria")
async def submit_general_criteria(
    eval_id: str,
    criteria_in: GeneralCriteriaSubmit,
    current_user: dict = Depends(require_director_or_above)
):
    # First get the evaluation to check kpi score
    eval_doc = await db.kpi_evaluations.find_one({"_id": ObjectId(eval_id)})
    if not eval_doc:
        raise HTTPException(status_code=404, detail="Evaluation not found")
        
    kpi_score = eval_doc.get("approval", {}).get("kpi_score", 0)
    total_E = sum(score.actual_score for score in criteria_in.scores)
    total_final_score = total_E + (kpi_score * 0.7)
    
    criteria_data = {
        "criteria_type": criteria_in.criteria_type,
        "scores": [s.model_dump() for s in criteria_in.scores],
        "total_E": total_E,
        "total_kpi_weighted": kpi_score * 0.7,
        "total_final_score": total_final_score,
        "scored_by": str(current_user["_id"]),
        "scored_at": datetime.utcnow()
    }
    
    await db.kpi_evaluations.update_one(
        {"_id": ObjectId(eval_id)},
        {
            "$set": {
                "general_criteria": criteria_data,
                "updated_at": datetime.utcnow()
            }
        }
    )
    return {"message": "General criteria scored", "total_final_score": total_final_score}

# ================= 4. KẾT QUẢ KPI & XẾP HẠNG =================

@router.get("/scores/ranking")
async def get_ranking(
    department_id: Optional[str] = None,
    period_year: Optional[int] = None,
    period_month: Optional[int] = None,
    current_user: dict = Depends(require_leader_or_above)
):
    # Directors can only see their department
    if current_user["role"] in ["director", "leader"] and not department_id:
        department_id = current_user.get("department_id")
        
    ranking = await get_kpi_ranking(department_id, period_month, period_year)
    return ranking

# ================= 5. TEMPLATES TIÊU CHÍ CHUNG (PHỤ LỤC) =================

@router.get("/criteria-templates")
async def get_criteria_templates(
    criteria_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Trả về templates tiêu chí chung theo Phụ lục Hướng dẫn số 20-HD/ĐUCA.
    criteria_type: 'collective' | 'leader' | 'staff'
    """
    if criteria_type:
        template = _CRITERIA_TEMPLATES.get(criteria_type)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{criteria_type}' not found")
        return template
    return list(_CRITERIA_TEMPLATES.values())
