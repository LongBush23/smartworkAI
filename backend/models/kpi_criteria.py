"""
Khung tiêu chí chung (Điểm E - tối đa 30 điểm) theo Phụ lục
Hướng dẫn số 20-HD/ĐUCA ngày 08/6/2026.

Dùng chung cho router KPI (trả về template) và seeder (sinh dữ liệu mẫu).
Mỗi tiêu chí được chấm theo 2 mức: "đảm bảo" (đạt tối đa điểm) hoặc
"không đảm bảo" (0 điểm).
"""
from typing import Dict, List, Any

# I. Danh mục điểm chấm tiêu chí chung đối với tập thể (Tổng 30 điểm)
_COLLECTIVE = {
    "id": "collective",
    "type": "collective",
    "name": "Danh mục điểm chấm tiêu chí chung đối với tập thể",
    "total_max_score": 30,
    "criteria": [
        {
            "id": "A1", "max_score": 5,
            "name": "Kết quả công tác xây dựng, chỉnh đốn Đảng; củng cố, xây dựng tổ chức đảng "
                    "và hệ thống chính trị; nâng cao chất lượng đội ngũ cán bộ, đảng viên theo "
                    "nghị quyết, kế hoạch, chỉ tiêu được giao.",
        },
        {
            "id": "A2", "max_score": 5,
            "name": "Năng lực lãnh đạo của cấp ủy; hiệu quả lãnh đạo, chỉ đạo của cấp ủy đối với "
                    "đơn vị, các cấp ủy, tổ chức đảng cấp dưới trong CAND theo thẩm quyền; "
                    "hiệu quả trong phối hợp công tác; xây dựng đoàn kết nội bộ.",
        },
        {
            "id": "A3", "max_score": 5,
            "name": "Hiệu quả trong công tác thanh tra, kiểm tra, giám sát và kỷ luật đảng; "
                    "thực hiện các quy định về kiểm soát quyền lực; không để xảy ra tham nhũng, "
                    "lãng phí, tiêu cực, suy thoái về tư tưởng chính trị, đạo đức, lối sống, "
                    "\"tự diễn biến\", \"tự chuyển hóa\" trong nội bộ.",
        },
        {
            "id": "A4", "max_score": 5,
            "name": "Kết quả thực hiện các nguyên tắc tổ chức và hoạt động của đảng, nhất là "
                    "nguyên tắc tập trung dân chủ, tự phê bình và phê bình; việc chấp hành quy chế "
                    "làm việc, nội quy, chế độ công tác; phân công nhiệm vụ, tổ chức thực hiện hiệu quả.",
        },
        {
            "id": "A5", "max_score": 5,
            "name": "Kết quả lãnh đạo, chỉ đạo, kiểm tra, giám sát việc thực hiện nhiệm vụ chính trị; "
                    "xây dựng bộ máy tinh gọn, tinh giản biên chế, hoạt động hiệu năng, hiệu lực, "
                    "hiệu quả; thực hiện cải cách hành chính, chuyển đổi số, đẩy mạnh ứng dụng khoa học, "
                    "công nghệ; đổi mới phương pháp quản lý gắn với xây dựng văn hóa công vụ.",
        },
        {
            "id": "A6", "max_score": 5,
            "name": "Tinh thần tự phê bình và phê bình, tự soi, tự sửa của tập thể đơn vị; kết quả "
                    "khắc phục những hạn chế, yếu kém, khuyết điểm đã được chỉ ra trong các kỳ "
                    "kiểm điểm trước hoặc qua thanh tra, kiểm tra, giám sát.",
        },
    ],
}

# II. Danh mục điểm chấm tiêu chí chung đối với cá nhân là lãnh đạo, chỉ huy
#     (18 + 04 + 08 = 30 điểm)
_LEADER = {
    "id": "leader",
    "type": "leader",
    "name": "Danh mục điểm chấm tiêu chí chung đối với cá nhân là lãnh đạo, chỉ huy",
    "total_max_score": 30,
    "criteria": [
        {
            "id": "II_1", "max_score": 18,
            "name": "Về phẩm chất chính trị, đạo đức, lối sống, thực hiện trách nhiệm nêu gương",
            "sub_criteria": [
                {"id": "II_1_1", "max_score": 2, "name": "Tuyệt đối trung thành với Đảng, Tổ quốc và Nhân dân; kiên định chủ nghĩa Mác - Lênin, tư tưởng Hồ Chí Minh, mục tiêu độc lập dân tộc và chủ nghĩa xã hội. Có lập trường, quan điểm, bản lĩnh chính trị vững vàng; kiên quyết bảo vệ nền tảng tư tưởng, Cương lĩnh chính trị, Hiến pháp, pháp luật của Đảng, Nhà nước; đấu tranh phản bác các quan điểm sai trái, thù địch, các biểu hiện suy thoái, \"tự diễn biến\", \"tự chuyển hóa\"."},
                {"id": "II_1_2", "max_score": 2, "name": "Có tinh thần yêu nước sâu sắc, tận tụy phục vụ Nhân dân, sâu sát cơ sở, luôn hành động vì lợi ích của Nhân dân. Đặt lợi ích của Đảng, quốc gia - dân tộc, Nhân dân, tập thể lên trên lợi ích cá nhân, sẵn sàng vì sự nghiệp cách mạng của Đảng, vì độc lập, tự do của Tổ quốc, vì hạnh phúc của Nhân dân."},
                {"id": "II_1_3", "max_score": 2, "name": "Chấp hành nghiêm chủ trương, đường lối, nghị quyết, chỉ thị, quy định, nguyên tắc tổ chức, kỷ luật của Đảng, nhất là nguyên tắc tập trung dân chủ, tự phê bình và phê bình; chấp hành nghiêm pháp luật và quy định của Nhà nước và quy định của đơn vị. Tuyệt đối chấp hành sự phân công của tổ chức, yên tâm công tác và hoàn thành tốt mọi nhiệm vụ được giao."},
                {"id": "II_1_4", "max_score": 2, "name": "Có tinh thần tự giác, trách nhiệm cao trong nghiên cứu, học tập chủ nghĩa Mác - Lênin, tư tưởng Hồ Chí Minh, các nghị quyết, chỉ thị của Đảng và các chương trình bồi dưỡng, cập nhật kiến thức mới nhằm nâng cao trình độ về mọi mặt, đáp ứng yêu cầu, nhiệm vụ."},
                {"id": "II_1_5", "max_score": 2, "name": "Có phẩm chất đạo đức, lối sống trong sáng, trung thực, khiêm tốn, chân thành, giản dị; cần, kiệm, liêm, chính, chí công vô tư; chấp hành nghiêm quy định về chuẩn mực đạo đức cách mạng của cán bộ, đảng viên trong giai đoạn mới, trách nhiệm nêu gương; không vi phạm Quy định về những điều đảng viên không được làm. Không né tránh công việc, chạy theo thành tích; không vi phạm đến mức bị xử lý kỷ luật."},
                {"id": "II_1_6", "max_score": 2, "name": "Không tham vọng quyền lực; không chạy chức, chạy quyền; không tham nhũng, lãng phí, cơ hội, vụ lợi, cục bộ, lợi ích nhóm; không để gia đình, người thân và người khác lợi dụng chức vụ, vị trí công tác để mưu lợi. Không có biểu hiện suy thoái về tư tưởng chính trị, đạo đức, lối sống, những biểu hiện \"tự diễn biến\", \"tự chuyển hóa\" trong nội bộ. Kiên quyết đấu tranh chống quan liêu, tham nhũng, xa hoa, lãng phí, tiêu cực, chủ nghĩa cá nhân, lối sống cơ hội, thực dụng, bè phái, lợi ích nhóm, nói không đi đôi với làm."},
                {"id": "II_1_7", "max_score": 2, "name": "Có uy tín cao, tiêu biểu về phẩm chất đạo đức và phong cách công tác; là trung tâm đoàn kết, thương yêu đồng chí, đồng nghiệp."},
                {"id": "II_1_8", "max_score": 2, "name": "Có tinh thần chủ động, đổi mới sáng tạo; phấn đấu vì mục tiêu chung của đất nước, đóng góp vào mục tiêu chung của đất nước."},
                {"id": "II_1_9", "max_score": 2, "name": "Thực hiện việc kê khai và công khai tài sản, thu nhập theo quy định. Báo cáo đầy đủ, trung thực, cung cấp thông tin chính xác, khách quan về những nội dung liên quan đến việc thực hiện chức trách, nhiệm vụ được giao và hoạt động của đơn vị với cấp trên khi được yêu cầu."},
            ],
        },
        {
            "id": "II_2", "max_score": 4,
            "name": "Tư duy đổi mới, chiến lược, khát vọng cống hiến, dám nghĩ, dám làm",
            "sub_criteria": [
                {"id": "II_2_1", "max_score": 1, "name": "Có tư duy đổi mới, tầm nhìn chiến lược, khả năng lãnh đạo, chỉ đạo thích ứng với sự phát triển của thời đại và xu thế toàn cầu hóa; phương pháp làm việc khoa học, nhạy bén chính trị; có năng lực cụ thể hóa trong lãnh đạo, chỉ đạo đơn vị thực hiện và hoàn thành tốt chức năng, nhiệm vụ được giao."},
                {"id": "II_2_2", "max_score": 1, "name": "Luôn bám sát thực tiễn, có nhiều cách làm hay, sáng tạo, đạt hiệu quả cao trong lãnh đạo, chỉ đạo, tổ chức thực hiện nhiệm vụ; xây dựng cấp ủy, tổ chức đảng trong sạch, vững mạnh, đơn vị vững mạnh toàn diện."},
                {"id": "II_2_3", "max_score": 1, "name": "Nói đi đôi với làm, dám nghĩ, dám làm, dám chịu trách nhiệm, dám đột phá vì lợi ích chung."},
                {"id": "II_2_4", "max_score": 1, "name": "Có khát vọng phấn đấu, cống hiến; có khả năng quy tụ và phát huy được sức mạnh của tập thể, cá nhân trong đơn vị và các đơn vị có liên quan."},
            ],
        },
        {
            "id": "II_3", "max_score": 8,
            "name": "Về tự phê bình và phê bình, tự soi, tự sửa, khắc phục hạn chế, khuyết điểm",
            "sub_criteria": [
                {"id": "II_3_1", "max_score": 2, "name": "Chủ động, nghiêm túc thực hiện tự phê bình và phê bình, có tinh thần cầu thị và tiếp thu phản biện, góp ý."},
                {"id": "II_3_2", "max_score": 2, "name": "Có kế hoạch rõ ràng và quyết liệt trong khắc phục hạn chế, khuyết điểm đã được chỉ ra."},
                {"id": "II_3_3", "max_score": 2, "name": "Kết quả khắc phục hoàn thành từ > 80% nội dung, có tiến bộ rõ, được tổ chức đánh giá tốt; không để tái diễn tồn tại."},
                {"id": "II_3_4", "max_score": 2, "name": "Tự soi, tự sửa trên tinh thần trách nhiệm chính trị cao, không né tránh, không đổ lỗi."},
            ],
        },
    ],
}

# III. Danh mục điểm chấm tiêu chí chung đối với cá nhân không là lãnh đạo, chỉ huy
#      (20 + 08 + 02 = 30 điểm)
_STAFF = {
    "id": "staff",
    "type": "staff",
    "name": "Danh mục điểm chấm tiêu chí chung đối với cá nhân không là lãnh đạo, chỉ huy",
    "total_max_score": 30,
    "criteria": [
        {
            "id": "III_1", "max_score": 20,
            "name": "Về chính trị, phẩm chất đạo đức và ý thức tổ chức kỷ luật",
            "sub_criteria": [
                {"id": "III_1_1", "max_score": 2, "name": "Có quan điểm, bản lĩnh chính trị vững vàng; kiên định lập trường; không dao động trước mọi khó khăn, thách thức."},
                {"id": "III_1_2", "max_score": 2, "name": "Thực hiện nghiêm các nguyên tắc tổ chức và hoạt động của Đảng, nhất là nguyên tắc tập trung dân chủ, tự phê bình và phê bình. Chấp hành đường lối, chủ trương của Đảng, chính sách pháp luật của Nhà nước; thực hiện nghiêm về kỷ luật phát ngôn, bảo vệ bí mật Nhà nước."},
                {"id": "III_1_3", "max_score": 2, "name": "Có ý thức nghiên cứu, học tập, vận dụng chủ nghĩa Mác - Lênin, tư tưởng Hồ Chí Minh, nghị quyết, chỉ thị, quyết định và các văn bản của Đảng."},
                {"id": "III_1_4", "max_score": 2, "name": "Giữ gìn phẩm chất đạo đức, lối sống trong sáng, trung thực, khiêm tốn, chân thành, giản dị; có ý thức tham gia công tác đấu tranh phòng, chống tham nhũng, lãng phí, tiêu cực; không có biểu hiện suy thoái về tư tưởng chính trị, đạo đức, lối sống, \"tự diễn biến\", \"tự chuyển hóa\"; không vi phạm Quy định về những điều đảng viên không được làm."},
                {"id": "III_1_5", "max_score": 2, "name": "Không tham nhũng, tham ô, tiêu cực, quan liêu, hách dịch, cửa quyền, vụ lợi; không để người quen lợi dụng quyền hạn của mình để trục lợi."},
                {"id": "III_1_6", "max_score": 2, "name": "Có ý thức tổ chức kỷ luật, tinh thần trách nhiệm trong công tác; chấp hành sự phân công của tổ chức; thực hiện các quy định, quy chế, nội quy của đơn vị và nơi công tác."},
                {"id": "III_1_7", "max_score": 2, "name": "Thực hiện việc kê khai và công khai tài sản, thu nhập theo quy định."},
                {"id": "III_1_8", "max_score": 2, "name": "Báo cáo đầy đủ, trung thực, cung cấp thông tin chính xác, khách quan về những nội dung liên quan đến việc thực hiện chức trách, nhiệm vụ được giao và hoạt động của đơn vị với cấp trên khi được yêu cầu."},
                {"id": "III_1_9", "max_score": 2, "name": "Giữ gìn đoàn kết nội bộ; có quan hệ tốt với đồng chí, đồng nghiệp; tích cực tham gia xây dựng tổ chức đảng, đoàn thể và các hoạt động xã hội, cộng đồng và phong trào tập thể do đơn vị tổ chức."},
                {"id": "III_1_10", "max_score": 2, "name": "Gần gũi, sâu sát với cơ sở; thực hiện tốt việc giữ mối liên hệ với cấp ủy và Nhân dân nơi cư trú."},
            ],
        },
        {
            "id": "III_2", "max_score": 8,
            "name": "Về năng lực chuyên môn, nghiệp vụ theo yêu cầu của vị trí việc làm; khả năng đáp ứng "
                    "yêu cầu thực thi nhiệm vụ được giao; thái độ công tác trong thực hiện nhiệm vụ; "
                    "tinh thần đổi mới sáng tạo, dám nghĩ, dám làm, dám chịu trách nhiệm vì lợi ích chung",
            "sub_criteria": [
                {"id": "III_2_1", "max_score": 2, "name": "Năng lực chuyên môn, nghiệp vụ theo yêu cầu của vị trí việc làm: (1) Có hiểu biết đầy đủ về lĩnh vực công tác được phân công; nắm vững quy định pháp luật, quy trình nghiệp vụ có liên quan đến vị trí việc làm. (2) Thường xuyên cập nhật kiến thức mới, có khả năng nghiên cứu, phân tích, tổng hợp và vận dụng sáng tạo vào công việc. (3) Có kỹ năng xử lý công việc độc lập, làm việc nhóm hiệu quả. (4) Khả năng sử dụng công nghệ thông tin, áp dụng vào công việc chuyên môn."},
                {"id": "III_2_2", "max_score": 2, "name": "Khả năng đáp ứng yêu cầu thực thi nhiệm vụ được giao: (1) Nhiệm vụ thường xuyên: Có khả năng vận dụng thành thạo kiến thức chuyên môn, nghiệp vụ để xử lý công việc chuyên môn theo kế hoạch định kỳ; duy trì ổn định chất lượng chuyên môn. (2) Nhiệm vụ đột xuất: Có khả năng đề xuất giải pháp, thực hiện hiệu quả các công việc phát sinh; có khả năng phản ứng kịp thời, đáp ứng với yêu cầu, nhiệm vụ cụ thể."},
                {"id": "III_2_3", "max_score": 2, "name": "Thái độ công tác trong thực hiện nhiệm vụ: (1) Tinh thần trách nhiệm, tích cực trong công việc; kịp thời tiếp cận kiến thức mới để điều chỉnh, đề xuất cải tiến quy trình hoặc giải pháp nâng cao hiệu quả công việc. (2) Có thái độ đúng mực, phong cách làm việc chuẩn mực, lề lối hành chính chuyên nghiệp trong quan hệ công tác. (3) Phối hợp có hiệu quả với tập thể, cá nhân có liên quan trong công việc triển khai thực hiện các nhiệm vụ được phân công."},
                {"id": "III_2_4", "max_score": 2, "name": "Tinh thần đổi mới, sáng tạo, dám nghĩ, dám làm, dám chịu trách nhiệm vì lợi ích chung: (1) Có sản phẩm, giải pháp đột phá, sáng tạo đem lại giá trị, hiệu quả thiết thực, tác động tích cực đến kết quả thực hiện nhiệm vụ của đơn vị. (2) Sẵn sàng tham gia thực hiện nhiệm vụ có tính chất đột xuất, phức tạp hoặc trong điều kiện khó khăn. (3) Có tinh thần chịu trách nhiệm trước kết quả công việc; sẵn sàng nhận trách nhiệm khi có sai sót và có biện pháp khắc phục rõ ràng, cụ thể."},
            ],
        },
        {
            "id": "III_3", "max_score": 2,
            "name": "Về tự phê bình và phê bình, khắc phục hạn chế, khuyết điểm: Tinh thần tự phê bình và "
                    "phê bình, tự soi, tự sửa của cá nhân; mức độ tự giác nhận diện hạn chế, khuyết điểm "
                    "của bản thân và kết quả khắc phục những hạn chế, khuyết điểm đã được chỉ ra.",
        },
    ],
}

CRITERIA_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "collective": _COLLECTIVE,
    "leader": _LEADER,
    "staff": _STAFF,
}


def get_template(criteria_type: str) -> Dict[str, Any]:
    """Lấy 1 template theo loại: collective | leader | staff"""
    return CRITERIA_TEMPLATES[criteria_type]


def flatten_criteria(criteria_type: str) -> List[Dict[str, Any]]:
    """
    Trả về danh sách tiêu chí LÁ (đơn vị được chấm điểm) của một template.
    Tiêu chí có sub_criteria thì chỉ lấy các sub; ngược lại lấy chính nó.
    Tổng max_score của các lá luôn bằng total_max_score (30 điểm).
    """
    leaves: List[Dict[str, Any]] = []
    for c in CRITERIA_TEMPLATES[criteria_type]["criteria"]:
        subs = c.get("sub_criteria")
        if subs:
            leaves.extend({"id": s["id"], "name": s["name"], "max_score": s["max_score"]} for s in subs)
        else:
            leaves.append({"id": c["id"], "name": c["name"], "max_score": c["max_score"]})
    return leaves


def criteria_type_for(evaluation_type: str, role: str | None) -> str:
    """Xác định bộ tiêu chí áp dụng cho một đối tượng đánh giá."""
    if evaluation_type == "collective":
        return "collective"
    return "leader" if role in ("leader", "director") else "staff"
