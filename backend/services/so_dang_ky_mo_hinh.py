"""
Sổ đăng ký các mô hình của hệ thống — nguồn duy nhất cho trang "Mô hình hỗ trợ
ra quyết định".

VÌ SAO ĐẶT Ở BACKEND, KHÔNG VIẾT CỨNG TRONG GIAO DIỆN
-----------------------------------------------------
Mô tả mô hình viết cứng trong giao diện sẽ lệch khỏi mã nguồn ngay lần sửa
thuật toán đầu tiên: người xem đọc một trang không còn đúng với thứ đang chạy.
Đặt ở đây thì trọng số, ngưỡng, số điều khoản và chỉ số chất lượng đều đọc
thẳng từ chính hằng số mà các mô hình đang dùng — sửa thuật toán là trang tự
đổi theo.

VÌ SAO ĐẶT NGOÀI `services/ai`
------------------------------
Sổ này phải mô tả cả trợ lý hội thoại ở `services/tro_ly` — gói duy nhất được
gọi ra ngoài. Đặt trong `services/ai` thì gói vốn cam kết không gọi mạng lại đi
tham chiếu tới gói có gọi mạng, và test quét mã của gói đó mất ý nghĩa.

Sổ chỉ ĐỌC. Không huấn luyện lại, không ghi vào cơ sở dữ liệu.
"""
from datetime import datetime
from typing import Any, Dict, List

from backend.config import GEMINI_MODEL
from backend.services.ai import anomaly, assignment, guideline, risk
from backend.services.tro_ly import gemini
from backend.services.tro_ly.cong_cu import BANG_CONG_CU

# Hai ranh giới cứng của cả hệ thống. Nêu ngay đầu trang vì đây là điều người
# thẩm định cần biết trước khi đọc bất kỳ con số nào về mô hình.
RANH_GIOI = [
    {
        "tieu_de": "Mô hình không quyết định điểm KPI",
        "noi_dung": (
            "Điểm A, B, C, D và cách phân nhóm là công thức trong Hướng dẫn số "
            "20-HD/ĐUCA — văn bản pháp quy. Không mô hình nào trong hệ thống được "
            "ghi vào kết quả duyệt của kỳ đánh giá; tất cả chỉ đọc dữ liệu rồi gợi "
            "ý và cảnh báo. Người có thẩm quyền là người quyết định, và khi có "
            "khiếu nại thì căn cứ vẫn là công thức của văn bản."
        ),
    },
    {
        "tieu_de": "Bốn mô hình ra quyết định chạy hoàn toàn tại chỗ",
        "noi_dung": (
            "Bốn mô hình ảnh hưởng tới cách lãnh đạo nhìn nhận cán bộ — cảnh báo "
            "nguy cơ, phát hiện chấm hình thức, gợi ý phân công, tra cứu văn bản — "
            "tính toàn bộ trong máy chủ của đơn vị, không một byte dữ liệu nào rời "
            "hệ thống. Có test tự động quét mã nguồn, chặn mọi thư viện gọi mạng "
            "trong gói services/ai. Chỉ trợ lý hội thoại gọi ra ngoài, và trợ lý "
            "không tính điểm, không xếp hạng ai."
        ),
    },
]

GHI_CHU_DU_LIEU_MAU = (
    "Trên dữ liệu mẫu, AUC của hai mô hình dự báo rất cao (khoảng 0,99) vì nhiệm vụ "
    "và kỳ đánh giá đều được sinh ra từ cùng một mức năng lực theo tháng — mô hình "
    "gần như khôi phục lại đúng quy tắc sinh dữ liệu. ĐÂY KHÔNG PHẢI DỰ BÁO VỀ HIỆU "
    "QUẢ THỰC TẾ: với dữ liệu vận hành thật, con người không hành xử theo quy tắc cố "
    "định nên AUC sẽ thấp hơn đáng kể. Chỉ số đáng tin duy nhất là chỉ số đo trên dữ "
    "liệu thật sau vài kỳ."
)

# Mô tả tĩnh của từng mô hình. `chat_luong` và `tham_so` được ghép vào lúc chạy
# từ chính hằng số của mô hình, xem `danh_sach()` bên dưới.
MO_HINH: List[Dict[str, Any]] = [
    {
        "ma": "nguy_co_nhom_3",
        "so": 1,
        "ten": "Nguy cơ rơi Nhóm 3",
        "muc_dich": (
            "Ước lượng xác suất một cán bộ bị xếp Nhóm 3 khi kết thúc kỳ, dựa trên "
            "tiến độ hiện tại và lịch sử các kỳ trước, để lãnh đạo đôn đốc và hỗ trợ "
            "GIỮA kỳ thay vì biết khi đã hết kỳ."
        ),
        "thuat_toan": "Hồi quy logistic, 8 đặc trưng, chuẩn hoá bằng StandardScaler",
        "vi_sao": (
            "Cần giải thích được. Với hồi quy logistic, đóng góp của từng đặc trưng "
            "vào kết quả là hệ số × giá trị — in ra thành lời được, nên mỗi cảnh báo "
            "đều nêu được ba yếu tố đóng góp nhiều nhất. Mô hình phức tạp hơn có thể "
            "chính xác hơn vài phần trăm nhưng không nói được vì sao; cơ quan nhà "
            "nước không dùng được thứ đó để ra quyết định về con người."
        ),
        "noi_chay": "tai_cho",
        "ma_nguon": "backend/services/ai/risk.py",
        "dung_o": [{"nhan": "Trang chủ — khối Cảnh báo sớm", "duong_dan": "/"}],
        "khoa_chat_luong": "group3",
    },
    {
        "ma": "nguy_co_tre_han",
        "so": 2,
        "ten": "Nguy cơ nhiệm vụ trễ hạn",
        "muc_dich": (
            "Ước lượng xác suất một nhiệm vụ đang mở sẽ hoàn thành trễ hạn, để lãnh "
            "đạo can thiệp khi còn kịp: nhắc, giãn tiến độ hoặc bổ sung lực lượng."
        ),
        "thuat_toan": "Hồi quy logistic, 6 đặc trưng, chuẩn hoá bằng StandardScaler",
        "vi_sao": (
            "Cùng lý do như mô hình số 1: mỗi cảnh báo phải nêu được căn cứ. Nhiệm vụ "
            "có độ mật chỉ dùng metadata — điểm, nhóm độ phức tạp, thời hạn, số lần "
            "sửa và nhắc — mô hình không đụng tới nội dung nhiệm vụ."
        ),
        "noi_chay": "tai_cho",
        "ma_nguon": "backend/services/ai/risk.py",
        "dung_o": [{"nhan": "Trang chủ — khối Cảnh báo sớm", "duong_dan": "/"}],
        "khoa_chat_luong": "task_late",
    },
    {
        "ma": "cham_hinh_thuc",
        "so": 3,
        "ten": "Phát hiện chấm điểm hình thức",
        "muc_dich": (
            "Nêu các dấu hiệu đánh giá thiếu thực chất để cơ quan tổ chức cán bộ rà "
            "soát: điểm tiêu chí chung đồng loạt tối đa, KPI trong đơn vị quá đều, "
            "tự nhận lệch xa kết quả, điểm nhảy vọt so với chính mình, và mâu thuẫn "
            "giữa tỷ lệ việc quá hạn với xếp loại. Đây là dấu hiệu để xem lại, không "
            "phải kết luận vi phạm."
        ),
        "thuat_toan": "Thống kê thuần: 5 quy tắc, mỗi quy tắc một ngưỡng công khai",
        "vi_sao": (
            "Không dùng máy học vì kết quả ở đây có thể dẫn tới kiểm tra một đơn vị — "
            "phải nói được chính xác vì sao bị nêu. Mỗi dấu hiệu là một quy tắc rõ "
            "ràng, kèm ngưỡng và số liệu, người đọc tự thẩm định được. Ngoài ra dữ "
            "liệu nhãn 'chấm hình thức' không tồn tại nên cũng không có gì để học."
        ),
        "noi_chay": "tai_cho",
        "ma_nguon": "backend/services/ai/anomaly.py",
        "dung_o": [{"nhan": "Rà soát chất lượng đánh giá", "duong_dan": "/quality-review"}],
        "khoa_chat_luong": None,
    },
    {
        "ma": "goi_y_phan_cong",
        "so": 4,
        "ten": "Gợi ý phân công",
        "muc_dich": (
            "Xếp hạng cán bộ trong đơn vị theo mức phù hợp với nhiệm vụ sắp giao, và "
            "nêu luôn những ai bị loại kèm lý do — để lãnh đạo thấy hệ thống đã cân "
            "nhắc những người nào. Cán bộ chưa đủ cấp độ tiếp cận bị loại cứng."
        ),
        "thuat_toan": "Công thức có trọng số, 5 thành phần, tổng trọng số bằng 1,0",
        "vi_sao": (
            "Dữ liệu quá ít để học 'ai hợp việc gì': mỗi cán bộ chỉ có vài nhiệm vụ "
            "mỗi kỳ, chia tiếp theo nhóm độ phức tạp và loại sản phẩm thì còn rất "
            "mỏng — mô hình học trên đó sẽ khớp nhiễu. Thêm nữa giao nhiệm vụ là "
            "quyết định về con người: công thức có trọng số in ra được từng thành "
            "phần, mô hình học máy thì không. Và nó không cần huấn luyện lại, không "
            "lệch theo thời gian."
        ),
        "noi_chay": "tai_cho",
        "ma_nguon": "backend/services/ai/assignment.py",
        "dung_o": [
            {"nhan": "Nhiệm vụ được giao — hộp thêm/sửa nhiệm vụ", "duong_dan": "/tasks"},
        ],
        "khoa_chat_luong": None,
    },
    {
        "ma": "tra_cuu_huong_dan",
        "so": 5,
        "ten": "Tra cứu Hướng dẫn 20-HD/ĐUCA",
        "muc_dich": (
            "Trả lời câu hỏi về cách tính điểm: mức phần trăm theo số lần chỉnh sửa, "
            "theo số lần bị nhắc, ngưỡng phân nhóm, các bước của quy trình đánh giá — "
            "kèm nguyên văn điều khoản làm căn cứ."
        ),
        "thuat_toan": "Máy quy tắc nhận dạng câu hỏi + tìm điều khoản theo từ khoá",
        "vi_sao": (
            "Câu trả lời về số lấy TRỰC TIẾP từ hằng số của bộ máy chấm điểm, nên "
            "luôn khớp với điều hệ thống thực sự tính — có test khoá lại điều này. "
            "Một mô hình ngôn ngữ tự suy ra con số thì có thể nói khác với thứ hệ "
            "thống đang chấm, và đó là sai sót không thể chấp nhận với văn bản pháp quy."
        ),
        "noi_chay": "tai_cho",
        "ma_nguon": "backend/services/ai/guideline.py",
        "dung_o": [
            {"nhan": "Hộp trợ lý — mở được ở mọi trang", "duong_dan": "/"},
            {"nhan": "Quy trình đánh giá — hộp tra cứu", "duong_dan": "/kpi/evaluate"},
        ],
        "khoa_chat_luong": None,
    },
    {
        "ma": "tro_ly_hoi_thoai",
        "so": 6,
        "ten": "Trợ lý hội thoại",
        "muc_dich": (
            "Hỏi bằng lời thường về nhiệm vụ, điểm KPI của chính mình hoặc của đơn vị "
            "mình phụ trách, và về cách tính điểm. Trợ lý chỉ tra cứu và diễn đạt lại "
            "số liệu người hỏi vốn đã có quyền xem."
        ),
        "thuat_toan": f"Mô hình ngôn ngữ ({GEMINI_MODEL}) + vòng gọi công cụ",
        "vi_sao": (
            "Đây là mô hình DUY NHẤT gọi ra ngoài, và được phép vì nó không tính "
            "điểm, không xếp hạng ai. Bốn rào chắn: chỉ đọc, không ghi cơ sở dữ liệu; "
            "mọi con số về cách tính điểm phải lấy từ máy tra cứu tại chỗ chứ không "
            "để mô hình tự suy; nhiệm vụ có độ mật chỉ được đếm, không được kể tên; "
            "phạm vi dữ liệu đúng bằng phân quyền người hỏi. Mỗi rào chắn có test "
            "riêng trong backend/test_tro_ly.py. Thiếu khoá thì tự lui về máy tra cứu "
            "tại chỗ và nói rõ đang ở chế độ nào."
        ),
        "noi_chay": "goi_ra_ngoai",
        "ma_nguon": "backend/services/tro_ly/",
        "dung_o": [{"nhan": "Hộp trợ lý — nút nổi ở mọi trang", "duong_dan": "/"}],
        "khoa_chat_luong": None,
    },
]


def _tham_so(ma: str) -> List[Dict[str, str]]:
    """
    Tham số đang dùng của từng mô hình, đọc thẳng từ hằng số của mô hình đó.

    Trả về dạng cặp nhãn - giá trị để giao diện vẽ chung một bảng, không phải
    viết riêng cho từng mô hình.
    """
    if ma == "goi_y_phan_cong":
        nhan_thanh_phan = {
            "du_dia_tai_viec": "Dư địa tải việc",
            "chat_luong_lich_su": "Chất lượng lịch sử (ít phải sửa)",
            "tien_do_lich_su": "Tiến độ lịch sử (ít bị nhắc)",
            "khong_qua_han": "Không tồn việc quá hạn",
            "kpi_gan_nhat": "KPI 3 kỳ gần nhất",
        }
        ds = [
            {"nhan": f"Trọng số · {nhan_thanh_phan.get(k, k)}", "gia_tri": f"{v:.0%}"}
            for k, v in assignment.TRONG_SO.items()
        ]
        ds.append({
            "nhan": "Ngưỡng loại cứng · tải việc",
            "gia_tri": f"quá {assignment.TAI_VIEC_TOI_DA:.0f}% định mức thì không giao thêm",
        })
        return ds

    if ma == "cham_hinh_thuc":
        nhan = {
            "ty_le_diem_E_toi_da": "Tỷ lệ cán bộ đạt điểm E tối đa",
            "do_lech_chuan_kpi": "Độ lệch chuẩn KPI trong đơn vị",
            "lech_nhom_tu_danh_gia": "Tự nhận lệch kết quả (số nhóm)",
            "he_so_nhay_vot": "Hệ số nhảy vọt so với chính mình (σ)",
            "thay_doi_tuyet_doi_toi_thieu": "Thay đổi tuyệt đối tối thiểu (điểm)",
            "do_lech_chuan_toi_thieu": "Sàn của độ lệch chuẩn",
            "ty_le_qua_han": "Tỷ lệ việc quá hạn",
            "so_mau_toi_thieu": "Số cán bộ tối thiểu để thống kê",
        }
        return [
            {"nhan": nhan.get(k, k), "gia_tri": (f"{v:.0%}" if 0 < v < 1 else f"{v:g}")}
            for k, v in anomaly.NGUONG.items()
        ]

    if ma == "tra_cuu_huong_dan":
        return [
            {"nhan": "Điều khoản đã lập chỉ mục", "gia_tri": f"{len(guideline.CLAUSES)} điều"},
            {
                "nhan": "Nguồn số liệu",
                "gia_tri": "hằng số của bộ máy chấm điểm (backend/services/kpi_service.py)",
            },
        ]

    if ma == "tro_ly_hoi_thoai":
        san_sang = gemini.san_sang()
        return [
            {"nhan": "Mô hình đang cấu hình", "gia_tri": GEMINI_MODEL},
            {
                "nhan": "Chế độ hiện tại",
                "gia_tri": (
                    "có kết nối mô hình ngôn ngữ" if san_sang
                    else "chưa có khoá — đang dùng máy tra cứu tại chỗ"
                ),
            },
            {"nhan": "Công cụ được phép gọi", "gia_tri": f"{len(BANG_CONG_CU)} công cụ, đều chỉ đọc"},
            {"nhan": "Số vòng gọi công cụ tối đa", "gia_tri": f"{gemini.SO_VONG_TOI_DA} vòng"},
        ]

    # Hai mô hình hồi quy: tham số huấn luyện, còn chất lượng nằm ở `chat_luong`
    return [
        {"nhan": "Ngưỡng AUC tối thiểu để được dùng", "gia_tri": f"{risk.AUC_TOI_THIEU:.2f}"},
        {"nhan": "Số mẫu tối thiểu để huấn luyện", "gia_tri": f"{risk.SO_MAU_TOI_THIEU} mẫu"},
        {"nhan": "Tách tập kiểm tra", "gia_tri": "20% dữ liệu, phân tầng theo nhãn"},
    ]


async def danh_sach() -> Dict[str, Any]:
    """
    Toàn bộ sổ đăng ký, kèm chất lượng thực tế của hai mô hình hồi quy.

    Chất lượng lấy từ bộ đệm mô hình đang chạy — chỉ huấn luyện khi bộ đệm còn
    trống, không huấn luyện lại mô hình đang dùng.
    """
    chat_luong = await risk.tom_tat_chat_luong()

    mo_hinh = []
    for m in MO_HINH:
        khoa = m["khoa_chat_luong"]
        mo_hinh.append({
            **{k: v for k, v in m.items() if k != "khoa_chat_luong"},
            "tham_so": _tham_so(m["ma"]),
            "chat_luong": chat_luong.get(khoa) if khoa else None,
        })

    return {
        "mo_hinh": mo_hinh,
        "auc_threshold": chat_luong["auc_threshold"],
        "so_mau_toi_thieu": chat_luong["so_mau_toi_thieu"],
        "ranh_gioi": RANH_GIOI,
        "ghi_chu_du_lieu_mau": GHI_CHU_DU_LIEU_MAU,
    }


async def tom_tat_ho_tro(nguoi_dung: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dải "AI đang hỗ trợ đồng chí" trên Trang chủ.

    VÌ SAO KHÔNG ĐẾM LUÔN SỐ CẢNH BÁO NGUY CƠ Ở ĐÂY
    -----------------------------------------------
    Khối Cảnh báo sớm nằm ngay dưới dải này đã in "N cán bộ · N nhiệm vụ" ở
    tiêu đề của nó. Lặp lại đúng hai con số đó cách nhau 200px vừa thừa, vừa
    phải chạy lại hai mô hình dự báo mỗi lần mở Trang chủ — tốn gấp đôi mà
    không thêm thông tin nào. Dải này chỉ nêu những thứ Trang chủ CHƯA nói.

    Số thẻ thay đổi theo chức vụ: dấu hiệu rà soát chỉ dành cho lãnh đạo đơn vị
    trở lên, đúng bằng phạm vi của endpoint sinh ra nó.
    """
    vai_tro = nguoi_dung.get("role", "staff")
    tu_lanh_dao = vai_tro in ("leader", "director", "admin")
    tu_truong_phong = vai_tro in ("director", "admin")

    tai_cho = sum(1 for m in MO_HINH if m["noi_chay"] == "tai_cho")
    the: List[Dict[str, Any]] = [{
        "ma": "mo_hinh",
        "nhan": "Mô hình đang chạy",
        "so": str(len(MO_HINH)),
        "phu": f"{tai_cho} chạy tại chỗ · {len(MO_HINH) - tai_cho} gọi ra ngoài",
        # Cán bộ không giữ chức vụ vẫn thấy con số — biết hệ thống dùng mô hình
        # gì với dữ liệu của mình là chuyện minh bạch — nhưng trang chi tiết thì
        # chặn từ cấp lãnh đạo, nên không gắn đường dẫn dẫn tới chỗ bị từ chối.
        "duong_dan": "/kpi/models" if tu_lanh_dao else None,
    }]

    if tu_truong_phong:
        now = datetime.utcnow()
        phong = None if vai_tro == "admin" else nguoi_dung.get("department_id")
        kq = await anomaly.detect(
            period_month=now.month, period_year=now.year, department_id=phong,
        )
        tt = kq["summary"]
        the.append({
            "ma": "ra_soat",
            "nhan": f"Dấu hiệu cần rà soát kỳ {now.month}/{now.year}",
            "so": str(len(kq["flags"])),
            "phu": (
                f"{tt['cao']} cần rà soát ngay · đã soát {kq['total_evaluations']} kỳ đánh giá"
            ),
            "duong_dan": "/quality-review",
        })

    the.append({
        "ma": "dieu_khoan",
        "nhan": "Điều khoản tra cứu được",
        "so": str(len(guideline.CLAUSES)),
        "phu": "Hướng dẫn số 20-HD/ĐUCA — hỏi trợ lý là ra nguyên văn",
        "duong_dan": None,
    })

    san_sang = gemini.san_sang()
    the.append({
        "ma": "tro_ly",
        "nhan": "Trợ lý hội thoại",
        "so": "Sẵn sàng" if san_sang else "Chế độ tại chỗ",
        "phu": (
            f"{len(BANG_CONG_CU)} công cụ chỉ đọc, phạm vi đúng bằng quyền của đồng chí"
            if san_sang
            else "Chưa cấu hình khoá — vẫn trả lời được bằng máy tra cứu tại chỗ"
        ),
        "duong_dan": None,
    })

    return {"the": the}
