import streamlit as st
import pandas as pd
import json
import os
import re
import time
import requests
from PIL import Image
import io
import concurrent.futures
from google import genai
from google.genai import types

# --- CẤU HÌNH TRANG & BẢO MẬT ---
st.set_page_config(layout="wide", page_title="Shopee PH Script Gen - Pro Edition (Real Talk & Budol Check)")

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 Cổng Đăng Nhập Hệ Thống (Philippines Market - Pro Edition)")
        pwd = st.text_input("Nhập mật khẩu truy cập:", type="password")
        if st.button("Đăng nhập"):
            if pwd == st.secrets["APP_PASSWORD"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Mật khẩu không chính xác!")
        st.stop()
    return True

check_password()

# --- CẤU HÌNH API ---
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
MODEL_ID = "gemini-3.8-flash"
PRO_MODEL_ID = "gemini-3.8-flash"

# --- HỆ THỐNG PERSONA ĐỘC QUYỀN CHO THỊ TRƯỜNG PHILIPPINES (CÔ LẬP KHO MEME RIÊNG) ---
PERSONA_DICT_PH = {
    "Real Talk Kuya/Ate (Thánh Bóc Phốt & Check Hàng Sulit - Style Taglish Tech Reviewer)": {
        "traits": (
            "Isang honest at walang-filter na Filipino reviewer na parang trusted Kuya o Ate mo pagdating sa online shopping. "
            "Galit sa overhyped na budol at pekeng marketing claims. Diretsahan magsalita: sasabihin agad kung sino ang "
            "dapat bumili at sino ang masasayang lang ang pera. Natural mag-Taglish (70% conversational Tagalog, 30% English tech terms), "
            "mainit ang energy, relatable, at laging pinoprotektahan ang pinaghirapang pera ng viewers."
        ),
        "memes": [
            "Walang sugarcoating dito, real talk lang tayo bago ka mag-checkout",
            "Budol is real, pero dapat doon tayo sa sulit na budol — hindi sa sayang pera",
            "Bago mo i-add to cart at gamitan ng voucher, panoorin mo muna ito",
            "Sa papel sobrang ganda ng specs, pero sa actual daily use, medyo mapapakamot ka ng ulo",
            "May konting compromise sa part na ito, pero sa presyo niya, mapapatawad mo na agad",
            "Huwag magpadala sa viral TikTok hype kung hindi naman akma sa daily routine mo",
            "Ito yung tipong mapapasabi ka ng 'deserve ko 'to' pagkatapos mong ma-unbox"
        ]
    },
    "WFH & BGC Hustler (Chuyên gia Setup & Làm Việc Từ Xa - Style Productivity Creator)": {
        "traits": (
            "Isang Filipino freelancer / corporate hybrid worker na sanay mag-work from home, sa coffee shops sa BGC o Makati, "
            "at bumiyahe sa traffic ng Metro Manila. Sobrang pinapahalagahan ang reliability, battery life (lalo na kapag brownout o "
            "walang saksakan sa cafe), portability sa bag, at comfort sa mahabang shift. Nagre-review base sa totoong work workflow."
        ),
        "memes": [
            "Bilang isang alipin ng salapi na laging nagwo-work from cafe, sobrang big deal nito sa akin",
            "Kapag nag-lag ito sa gitna ng client meeting, gusto mo na lang mag-log out sa buhay",
            "Hindi ko sure kung tumaas productivity ko, pero nabawasan ang stress ko sa trabaho",
            "Swak na swak sa everyday carry bag nang hindi sumasakit ang balikat sa commute",
            "Sulit na investment para sa mga naghahabol ng deadline at side hustle",
            "Ang linis tingnan sa desk setup, parang ang sipag-sipag mo bigla magtrabaho"
        ]
    },
    "Wais na Nanay / Tita (Chuyên gia Gia Đình & Tiêu Dùng Thông Minh - Style Practical Home Finds)": {
        "traits": (
            "Isang praktikal at wais na Filipino homemaker na marunong mag-budget. Hindi nadadala sa aesthetic lang — ang tinitingnan ay "
            "kung pang-matagalan (durable), madaling linisin, safe gamitin sa bahay, at kung may legit warranty sa Shopee Mall. "
            "Magsalita ay parang caring na Tita o Nanay na nagbibigay ng tipid tips."
        ),
        "memes": [
            "Ang pinaka-ayaw natin ay yung bibilhin mo ngayon tapos next month nakatambak na lang sa sulok",
            "Makinig ka sa payo ng wais na mamimili: huwag magtipid sa gamit na araw-araw mong ginagamit",
            "Sobrang laking ginhawa nito sa gawaing bahay, bawas pagod talaga",
            "Abangan niyo ang payday sale at mega discount voucher sa Shopee para mas makatipid",
            "Pang-matagalan ang quality nito, hindi yung mukhang disposable after isang linggo"
        ]
    },
    "Shopee Review Detective (Thánh Soi Review Reddit PH & Verified Buyers - Style Data & Fact-Checker)": {
        "traits": (
            "Isang masusing researcher na binabasa muna ang daan-daang 1-star at 5-star reviews sa Shopee PH, Reddit (r/ShopeePH, r/Tech_Philippines), "
            "at Facebook groups bago bumili. Mahilig mag-compare ng pros and cons at magbigay ng malinaw na buyer's guide para sa mga "
            "nalilito kung alin ang pipiliin."
        ),
        "memes": [
            "Binasa ko na ang daan-daang verified buyer reviews sa Shopee para hindi ka na mapuyat kakahanap",
            "Akala ko dati overhyped lang ito sa Facebook groups, pero nung na-test ko na, legit pala talaga",
            "Kung nalilito ka na sa dami ng pagpipilian, ito ang pinaka-simpleng cheat sheet para sa'yo",
            "Nasa 1-star reviews ang totoong sikreto ng isang product, at nahuli natin lahat dito",
            "Hindi mo na kailangang mag-trial and error, sundan mo lang ang breakdown na ito"
        ]
    }
}

P1_TEMPLATE_PH = """SHOPEE PHILIPPINES (shopee.ph) SEO & LONG-TAIL KEYWORD ARCHITECT
Bối cảnh: Tôi gửi tệp từ khóa (.CSV) và ghi chú định hướng ngách cho thị trường Philippines.
Nhiệm vụ của bạn là chọn lọc và MỞ RỘNG bộ từ khóa "Chuyển đổi cao & Khác biệt hóa" kết hợp chuẩn văn hóa tìm kiếm của người Philippines (**70% English SEO + 30% Taglish Buyer Intent**).

Thông tin dự án:
- Sản phẩm / Ngách hạt giống: {seed_keywords}
- Ghi chú định hướng ngách: {niche_notes}

YÊU CẦU XỬ LÝ & MỞ RỘNG TỪ KHÓA (QUAN TRỌNG):
1. Ngôn ngữ: Tiếng Anh chuẩn thương mại Philippines kết hợp các cụm từ tìm kiếm Taglish phổ biến của người Phi.
2. Giữ lại toàn bộ các từ khóa gốc có trong CSV (tên model, thương hiệu, từ khóa chính).
3. MỞ RỘNG TỪ KHÓA GÓC NHÌN SO SÁNH & CHECK HÀNG SULIT (Đạt tổng 25 - 35 từ khóa):
   - Bên cạnh các từ khóa chính, hãy tự động sinh thêm các từ khóa ngách đánh vào tâm lý phân vân trước khi chốt đơn của người Philippines:
     + Cụm từ kiểm chứng & so sánh (English): "honest review", "philippines 2026", "worth it", "pros and cons", "budget", "shopee ph", "legit check", "buying guide".
     + Cụm từ bản địa Taglish: "sulit ba", "budol finds", "murang", "magandang", "hindi sayang pera".

Dữ liệu đầu vào:
{csv_data}

YÊU CẦU ĐẦU RA (JSON CHUẨN, KHÔNG BỌC MARKDOWN):
{
    "detected_brands": ["Brand1", "Brand2"],
    "keywords": [
        {"keyword": "từ khóa English hoặc Taglish", "volume": 5000}
    ]
}"""

P2_TEMPLATE_PH = """Phân tích dữ liệu tìm kiếm Shopee Philippines (shopee.ph) và bộ từ khóa để chọn ra Top 15 sản phẩm đáng tiền nhất ("Sulit Finds") cho video Real Talk & Budol Check.

Tiêu chí chọn lọc ĐỘC LẬP (Khác biệt hóa với các bảng xếp hạng đại trà):
1. KHÔNG chỉ chọn theo lượt bán ảo: Ưu tiên các sản phẩm có Điểm đánh giá ("rating" từ 4.8 - 5.0) thực chất, thuộc Shopee Mall / Preferred Seller uy tín, thương hiệu chuyên ngành hoặc giải quyết đúng nỗi đau trong ghi chú ngách (độ bền, pin trâu, có bảo hành nội địa PH).
2. Phân bổ đều: 5 mã Ngon-Bổ-Rẻ ("Budget Sulit / Petsa de Peligro Friendly"), 5 mã Tầm trung Hiệu năng cao ("Best Value Mid-range"), 5 mã Chuyên nghiệp/Cao cấp ("Premium Pang-Matagalan").
3. Loại bỏ hoàn toàn phụ kiện lẻ không phải sản phẩm chính (như túi đựng lẻ, miếng dán lẻ, dây cáp lẻ nếu ngách là thiết bị chính).

Dữ liệu Shopee (JSON): {shopee_data}
Từ khóa SEO: {keywords_json}
Ghi chú định hướng ngách: {niche_notes}

YÊU CẦU ĐẦU RA (JSON):
{
    "top_15": [
        {
            "product_id": "...",
            "name": "...",
            "url": "https://shopee.ph/...",
            "price": "...",
            "sales": "...",
            "reason": "Lý do chọn ngắn gọn bằng tiếng Việt",
            "relevant_keywords": ["keyword 1", "keyword 2"]
        }
    ]
}"""

P3_TEMPLATE_PH = """Đóng vai Giám khảo Thực Chiến cho thị trường Philippines (Góc nhìn Real Talk, Soi Kỹ Thông Số, Chống Mua Hớ / Sayang Pera).
Hãy đọc kỹ thông số, tính năng, mô tả và giá cả (Peso) của các sản phẩm Shopee Philippines để chọn ra ĐÚNG 5 SẢN PHẨM XUẤT SẮC NHẤT đưa vào video review.

QUY TẮC CHỌN ĐỘI HÌNH BẮT BUỘC (TỰ ĐỘNG TẠO SỰ KHÁC BIỆT):
1. Phân bổ vai trò Top 5 theo hướng "Thực Dụng & Đáng Tiền Nhất (Pinaka-Sulit)":
   - `top_5_alternative_1`: Giải pháp Ngân sách Tiết kiệm / Nhập môn không đau ví ("Best Budget / Petsa de Peligro Pick").
   - `top_4_alternative_2`: Vũ khí Ngách / Thiết kế hoặc Tính năng Độc Đáo cho nhu cầu riêng biệt ("Best Niche / Feature Pick").
   - `top_3_value_for_money`: Mẫu Quốc Dân Phổ Biến ("Crowd Favorite / Viral Pick" - Đặt ở vị trí số 3 để làm bàn đạp so sánh).
   - `top_2_premium`: Đỉnh Cao Trải Nghiệm / Chuẩn Mực Cho Người Khó Tính ("Best Premium / Heavy-Duty Pick").
   - `top_1_best_overall`: Quán Quân Thực Chiến Đáng Tiền Nhất ("Overall Sulit King / Dark Horse Champion").
2. NGUYÊN TẮC VÀNG CHO VỊ TRÍ SỐ 1 (`top_1_best_overall`):
   - TUYỆT ĐỐI KHÔNG chọn sản phẩm đắt tiền nhất hoặc sản phẩm đại trà ai cũng biết làm Top 1 (hãy đẩy sản phẩm đại trà xuống Top 3 và sản phẩm đắt nhất sang Top 2).
   - BẮT BUỘC chọn một sản phẩm "Ngựa Ô Thực Chiến" (Dark Horse) — có sự cân bằng hoàn hảo nhất giữa hiệu năng sử dụng thực tế, độ bền và mức giá Peso hợp lý ("Pinaka-sulit sa lahat") làm `top_1_best_overall`.
   {avoid_ch1_instruction}
3. QUAN TRỌNG: Sử dụng CHÍNH XÁC chuỗi `product_id` từ dữ liệu đầu vào.

Dữ liệu sản phẩm chi tiết: {scraped_data}

TRẢ VỀ ĐỊNH DẠNG JSON CHUẨN (Không viết văn bản ngoài JSON):
{
    "reasoning": "Phân tích ngắn gọn lý do xếp hạng đội hình Top 5",
    "top_5_alternative_1": "Mã_product_id_sản_phẩm_thứ_5",
    "top_4_alternative_2": "Mã_product_id_sản_phẩm_thứ_4",
    "top_3_value_for_money": "Mã_product_id_sản_phẩm_thứ_3",
    "top_2_premium": "Mã_product_id_sản_phẩm_thứ_2",
    "top_1_best_overall": "Mã_product_id_sản_phẩm_tốt_nhất_số_1"
}"""

P4_TEMPLATE_PH = """# Kịch Bản YouTube Review Shopee Philippines (PHONG CÁCH "REAL TALK & BUDOL CHECK / STORYTELLING")

Bạn là một YouTube Creator / Reviewer cực kỳ uy tín tại Philippines với phong cách **"Real Talk & Sulit Check" (Nói thẳng sự thật, kể chuyện cuốn hút, bảo vệ túi tiền người xem)**.
Hãy viết kịch bản video (thời lượng đọc 7 - 8 phút) đánh giá TOP 5 sản phẩm bằng **Taglish tự nhiên chuẩn người Manila (70% Conversational Tagalog + 30% English Tech & Shopping Terms)**.

## ĐẦU VÀO DỰ ÁN
- **Ngành hàng / Chủ đề**: {seed_keywords}
- **Định hướng ngách & Góc tiếp cận**: {niche_notes}
- **Thị trường**: Philippines (Shopee PH - shopee.ph)
- **Ngôn ngữ Script**: Natural Taglish (70% Tagalog grammar/flow + 30% English nouns/adjectives)
- **Persona (Nhân cách Reviewer)**: {selected_persona}
  + Đặc điểm giọng điệu: {persona_traits}
{meme_instruction}
- **Bộ từ khóa SEO**: {refined_keywords}
- **Dữ liệu chi tiết 5 sản phẩm**: {final_5_data}
- **Bối cảnh thời gian**: Năm 2026.

---

## NGUYÊN TẮC BẢN ĐỊA HÓA PHILIPPINES & TỐI ƯU GEMINI 3.8 FLASH TTS
1. **QUY TẮC TAGLISH MƯỢT MÀ CHO TTS (CỰC KỲ QUAN TRỌNG)**:
   - Dùng **Tagalog làm khung câu** (*"Kung naghahanap ka ng...", "Ang problema lang dito...", "Pero real talk lang..."*) và dùng **Tiếng Anh cho danh từ kỹ thuật, tính từ đánh giá** (*"battery life", "build quality", "worth it", "budget-friendly", "wireless connectivity"*).
   - **Gắn tiền tố chuẩn dấu gạch nối**: Khi ghép `nag-`, `mag-`, `na-`, `pa-`, `i-` với từ tiếng Anh, BẮT BUỘC dùng dấu gạch nối (VD: `nag-test`, `mag-order`, `na-try`, `i-check`). KHÔNG viết dính liền hay biến dạng khó đọc (tránh `kinocompare` -> hãy viết `kapag kinumpara mo`).
   - **Tiền tệ & Con số**: Luôn viết rõ chữ `pesos` (VD: `1,500 pesos`, `under 2,000 pesos`, `nasa 800 pesos lang`). KHÔNG viết tắt `PHP 1.5k` hay `₱1.5k` trong lời thoại để TTS đọc trôi chảy.
   - **Nhịp ngắt câu**: Dùng dấu phẩy và dấu gạch ngang dài (`—`) để tạo điểm nghỉ tự nhiên giữa các cụm Tagalog và Tiếng Anh.
2. **VĂN HÓA MUA SẮM PHILIPPINES (SULIT VS. SAYANG PERA)**:
   - Đánh trúng tâm lý người mua Shopee PH: kiểm tra xem có **COD (Cash on Delivery)** không, có áp được **Free Shipping & Mega Discount Vouchers** không, shop có phải **Shopee Mall / Preferred Seller** uy tín không, dùng có bền (**pang-matagalan**) trong điều kiện thời tiết nóng ẩm / di chuyển hàng ngày tại Philippines không.
   - CẤM dùng văn phong dịch máy khô cứng như *"In conclusion"*, *"First of all"*, *"Let's dive in"*. Hãy dùng khẩu ngữ tự nhiên của Pinoy YouTubers: *"Real talk lang"*, *"Alam mo yung feeling na..."*, *"Pero ito ang catch"*, *"Sulit ba o sayang pera?"*, *"Dito tayo sa totoo lang"*.
3. **CÁCH ĐẶT TIÊU ĐỀ (ENGLISH SEO CORE + TAGLISH HOOK - HIGH CTR)**:
   - Kết hợp từ khóa tìm kiếm tiếng Anh ở đầu + câu hook Taglish đánh vào tâm lý phân vân ở vế sau.
   - Ví dụ: `Top 5 Best {Từ khóa} Philippines 2026 | Sulit Ba Talaga? (Honest Review & Budol Check)`

---

## CHỈ THỊ ĐIỀU HƯỚNG GIỌNG ĐỌC TTS (CỰC KỲ QUAN TRỌNG)
- Chèn các thẻ cảm xúc bằng **TIẾNG ANH trong dấu ngoặc vuông** trực tiếp vào lời thoại để điều khiển Gemini TTS:
  + Danh sách thẻ hợp lệ duy nhất: `[laugh]`, `[sigh]`, `[gasp]`, `[emphasis]`, `[excited]`, `[disappointed]`.
- **QUY TẮC AN TOÀN TTS**:
  + TUYỆT ĐỐI KHÔNG viết bất kỳ ghi chú đạo diễn tiếng Việt, tiếng Tagalog hay tiếng Anh nào khác trong phần `<intro>...<outro>`.
  + Mỗi sản phẩm chỉ rải **2 - 3 thẻ** đúng chỗ đắt giá nhất.

---

## KHUNG ĐỘ DÀI CHUẨN VIDEO 7 - 8 PHÚT (ĐẾM THEO SỐ TỪ - WORD COUNT)
Phần lời thoại trong `4. SCRIPT` BẮT BUỘC đạt độ dài sâu sắc để đọc tự nhiên trong **7 - 8 phút** (~160 từ/phút):

| Phần | Mục tiêu (Số từ / Words) | Tối đa |
|---|---|---|
| **TOÀN BỘ KỊCH BẢN (SCRIPT)** | **1.150 – 1.350 từ** | **1.450 từ** |
| `<intro>` (Bóc mẽ lầm tưởng & Hook) | 110 – 140 từ | 160 từ |
| `<buying_guide>` (3 Red Flags cần tránh) | 130 – 160 từ | 180 từ |
| Mỗi sản phẩm (`<top5>` đến `<top1>`) | **170 – 210 từ / sản phẩm** | 230 từ / sản phẩm |
| `<outro>` (Chốt đơn 30 giây & CTA) | 90 – 120 từ | 140 từ |

---

## CẤU TRÚC KỊCH BẢN ĐỘC QUYỀN

### 1. `<intro>` (HOOK "REAL TALK & BUDOL CHECK")
- Mở đầu ngay bằng việc chỉ ra **1 sai lầm phổ biến nhất khiến 90% người mua Shopee PH hay bị "budol" nhầm sản phẩm trong ngách này** (VD: ham rẻ mua hàng không rõ nguồn gốc, hoặc mua bản đắt tiền nhưng thừa tính năng không dùng tới).
- Khẳng định giá trị video: Sau khi lọc kỹ thông số, đối chiếu hàng trăm verified reviews trên Shopee PH và trải nghiệm thực tế, đây là 5 lựa chọn **pinaka-sulit** nhất năm 2026 (đặc biệt Top 1 là một "dark horse" cực kỳ đáng tiền).

### 2. `<buying_guide>` (3 RED FLAGS BAGO MAG-CHECKOUT)
- Chỉ thẳng 3 "bẫy" người mua online hay gặp phải và cách check nhanh trước khi bấm đặt hàng.
- Nhắc tự nhiên: Toàn bộ **legit Shopee PH links** (đã lọc sẵn Shopee Mall / Preferred Sellers uy tín) đều nằm ngay dưới phần description để khán giả vừa xem vừa đối chiếu giá và áp voucher.

### 3. ĐÁNH GIÁ TỪ `<top5>` ĐẾN `<top1>` (MỖI SẢN PHẨM 170 - 210 TỪ)
Triển khai theo công thức **"Real-World Pinoy Scenario + Honest Pros & Cons"**:
- **Định vị rõ chân dung người dùng**: Mở đầu bằng việc chỉ rõ sản phẩm này sinh ra cho ai (VD: cho sinh viên, WFH setup, hay người hay commute).
- **Trải nghiệm đời thực**: Biến thông số kỹ thuật khô khan thành cảm giác sử dụng thực tế hàng ngày. Chỉ dùng thông tin có thật trong dữ liệu.
- **Góc nhìn "Real Talk / Walang Filter"**: Chỉ ra 1 điểm hạn chế thực tế (*"Pero ito ang catch..."* — ai không hợp thì đừng cố mua), nhưng nếu đúng nhu cầu thì nó lại cực kỳ **sulit**.
- **Bắc cầu so sánh mượt mà**: Đặt sản phẩm vừa nói lên bàn cân với sản phẩm tiếp theo để dẫn dắt tự nhiên từ Top 5 lên Top 1.
- **Rải Micro-CTA tự nhiên**: Tại `<top3>` và `<top1>`, nhắc người xem bấm vào link Shopee ở description bên dưới để check xem còn **Free Shipping voucher** hay **Mega Discount** hôm nay không.

### 4. `<outro>` (CHEAT SHEET CHỐT ĐƠN 30 GIÂY)
- Phân loại dứt khoát cho khán giả đang phân vân (*"Kung hirap ka pa rin pumili..."*): Nhóm tiết kiệm chọn con nào, Nhóm cần tính năng đặc biệt chọn con nào, Muốn an toàn và **pinaka-sulit** nhất chọn ngay Top 1.
- Kêu gọi check link trong description và comment bên dưới nếu đang phân vân giữa 2 mẫu bất kỳ.

---

## ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (TƯƠNG THÍCH 100% VỚI WORKER)

1. TIÊU ĐỀ: [Viết ngay tiêu đề English SEO + Taglish Hook độc đáo, dài trên 40 ký tự ngay trên cùng dòng này]

2. Mô tả: [Viết ngay 2-3 câu mở đầu mô tả bằng Tiếng Anh chuẩn SEO (có lồng từ khóa chính và từ khóa sulit/budol check) ngay trên dòng này]

📌 【REAL TALK & BUDOL CHECK】Top 5 Best Shopee PH Finds (Legit Links & Vouchers Below):

#5. [Tên Thương Hiệu + Tên Sản phẩm (English)]
✨ Why it's Sulit: [1 câu tóm tắt lý do đáng mua bằng Tiếng Anh rõ ràng]
👉 Check Latest Shopee PH Price & Vouchers: {LINK_5}

#4. [Tên Thương Hiệu + Tên Sản phẩm (English)]
✨ Why it's Sulit: [1 câu tóm tắt lý do đáng mua bằng Tiếng Anh rõ ràng]
👉 Check Latest Shopee PH Price & Vouchers: {LINK_4}

#3. [Tên Thương Hiệu + Tên Sản phẩm (English)]
✨ Why it's Sulit: [1 câu tóm tắt lý do đáng mua bằng Tiếng Anh rõ ràng]
👉 Check Latest Shopee PH Price & Vouchers: {LINK_3}

#2. [Tên Thương Hiệu + Tên Sản phẩm (English)]
✨ Why it's Sulit: [1 câu tóm tắt lý do đáng mua bằng Tiếng Anh rõ ràng]
👉 Check Latest Shopee PH Price & Vouchers: {LINK_2}

#1. [Tên Thương Hiệu + Tên Sản phẩm (English)]
✨ Why it's Sulit: [1 câu tóm tắt lý do đáng mua bằng Tiếng Anh rõ ràng]
👉 Check Latest Shopee PH Price & Vouchers: {LINK_1}

📢 Affiliate Disclaimer: Clicking the Shopee links above won't cost you anything extra, but it helps support the channel so we can keep testing more products for honest reviews! Don't forget to claim your Free Shipping & Mega Discount vouchers before checkout!
Hashtags: #[Hashtag1] #[Hashtag2] #[Hashtag3] #[Hashtag4] #[Hashtag5]

3. TAGS:
[BẮT BUỘC: Liệt kê các từ khóa SEO (70% English + 30% Taglish) cách nhau bằng dấu phẩy (,). Tự động mở rộng thêm các từ khóa liên quan sao cho TỔNG ĐỘ DÀI của riêng mục TAGS này đạt chuẩn từ 300 ĐẾN 450 KÝ TỰ!]

4. SCRIPT:

<intro>
[Lời thoại Taglish mượt mà]

<buying_guide>
[Lời thoại Taglish mượt mà]

<top5>
[Lời thoại Taglish mượt mà]

<top4>
[Lời thoại Taglish mượt mà]

<top3>
[Lời thoại Taglish mượt mà]

<top2>
[Lời thoại Taglish mượt mà]

<top1>
[Lời thoại Taglish mượt mà]

<outro>
[Lời thoại Taglish mượt mà]
"""

# --- HÀM HỖ TRỢ CHUNG ---
def clean_and_parse_json(ai_text):
    text = ai_text.strip()
    text = re.sub(r'^```(json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find('{')
        if start != -1:
            stack = 0
            for i in range(start, len(text)):
                if text[i] == '{':
                    stack += 1
                elif text[i] == '}':
                    stack -= 1
                    if stack == 0:
                        try:
                            return json.loads(text[start:i+1])
                        except Exception:
                            break
        raise ValueError("Lỗi bóc tách JSON từ AI.")

def call_gemini_with_retry(contents, response_mime_type=None, max_retries=3, target_model=PRO_MODEL_ID):
    delay = 3
    for attempt in range(max_retries):
        try:
            if response_mime_type:
                return client.models.generate_content(
                    model=target_model,
                    contents=contents,
                    config=types.GenerateContentConfig(response_mime_type=response_mime_type)
                )
            return client.models.generate_content(model=target_model, contents=contents)
        except Exception as e:
            if any(err in str(e).lower() for err in ["503", "429", "quota", "overloaded", "resource_exhausted"]):
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise e
            else:
                raise e

# --- HÀM ĐỌC FILE GHI CHÚ NGÁCH (.TXT) & CSV ---
def parse_txt_notes(txt_files):
    combined_notes = []
    extracted_kws = []
    for f in txt_files:
        content = f.getvalue().decode("utf-8", errors="ignore").strip()
        if content:
            combined_notes.append(content)
            matches = re.findall(r'^([^\n:：\-=]{2,40}):\s*Search volume\s*([\d\.,]+)', content, flags=re.MULTILINE | re.IGNORECASE)
            for kw, vol_str in matches:
                vol_clean = int(re.sub(r'[^\d]', '', vol_str) or 1000)
                extracted_kws.append({"Keyword": kw.strip(), "Volume": vol_clean})
    return "\n\n".join(combined_notes), extracted_kws

def parse_uploaded_csvs(csv_files, txt_extracted_kws=None):
    dfs = []
    for file in csv_files:
        try:
            df_temp = pd.read_csv(file, sep=None, engine='python', on_bad_lines='skip')
        except Exception:
            file.seek(0)
            df_temp = pd.read_csv(file, sep=',', quotechar='"', on_bad_lines='skip')

        col_kw = next((c for c in df_temp.columns if any(k in c.lower() for k in ['keyword', 'từ khóa', 'query', 'search term'])), None)
        col_vol = next((c for c in df_temp.columns if any(v in c.lower() for v in ['volume', 'search', 'lượt tìm', 'monthly'])), None)

        if col_kw is not None:
            if col_vol is not None:
                df_sub = df_temp[[col_kw, col_vol]].dropna(subset=[col_kw]).copy()
                df_sub.columns = ['Keyword', 'Volume']
                df_sub['Volume'] = df_sub['Volume'].astype(str).str.replace(r'[^\d]', '', regex=True)
                df_sub['Volume'] = pd.to_numeric(df_sub['Volume'], errors='coerce').fillna(500).astype(int)
            else:
                df_sub = df_temp[[col_kw]].dropna().copy()
                df_sub.columns = ['Keyword']
                df_sub['Volume'] = 1000
            dfs.append(df_sub)

    if txt_extracted_kws:
        dfs.append(pd.DataFrame(txt_extracted_kws))

    if not dfs:
        return pd.DataFrame(columns=['Keyword', 'Volume'])

    full_df = pd.concat(dfs, ignore_index=True)
    full_df['Keyword'] = full_df['Keyword'].astype(str).str.strip()
    full_df = full_df[full_df['Keyword'] != '']
    full_df = full_df.sort_values(by='Volume', ascending=False).drop_duplicates(subset=['Keyword'], keep='first')

    if len(full_df) > 35:
        filtered = full_df[full_df['Volume'] >= 150]
        if len(filtered) >= 15:
            full_df = filtered

    return full_df

# --- HÀM BÙ TAGS 300 - 450 KÝ TỰ (PHILIPPINES ANTI-FOOTPRINT EDITION) ---
def enforce_tags_section_ph(script_text, backup_keywords, seed_keyword, final_5_data, min_len=300, max_len=450):
    """
    Đảm bảo mục 3. TAGS đạt chuẩn 300 - 450 ký tự với bộ từ khóa English + Taglish chuẩn Philippines.
    """
    pattern = re.compile(r'(3\.\s*TAGS\s*:\s*\n?)(.*?)(?=\n+\s*4\.\s*SCRIPT\s*:)', re.DOTALL | re.IGNORECASE)
    match = pattern.search(script_text)

    raw_existing = match.group(2).strip() if match else ""
    raw_existing = re.sub(r'[\[\]]', '', raw_existing)
    initial_tags = [t.strip() for t in re.split(r'[,，、\n]+', raw_existing) if t.strip()]

    seen = set()
    tags_list = []

    def add_tag(t_str):
        t_clean = t_str.strip().strip('#').strip()
        if t_clean and len(t_clean) >= 2 and t_clean.lower() not in seen:
            seen.add(t_clean.lower())
            tags_list.append(t_clean)

    # 1. Ưu tiên đưa tên Model của 5 sản phẩm + hậu tố SEO PH vào đầu để phân tách footprint
    if final_5_data:
        for item in final_5_data:
            pname = str(item.get('name', '')).strip()
            clean_name = re.sub(r'【.*?】|\[.*?\]|\(.*?\)|（.*?）', ' ', pname).strip()
            short_tokens = [tok.strip() for tok in re.split(r'[\s/\-|｜,，]+', clean_name) if len(tok.strip()) >= 2]
            if short_tokens:
                model_guess = " ".join(short_tokens[:2])[:22].strip()
                for suf in ["review philippines", "sulit ba", "honest review"]:
                    add_tag(f"{model_guess} {suf}")
                    if len(", ".join(tags_list)) >= 145:
                        break

    # 2. Thêm các tag do AI sinh ra và kho từ khóa gốc
    for t in initial_tags:
        add_tag(t)

    for kw in backup_keywords:
        if len(", ".join(tags_list)) >= min_len + 30:
            break
        add_tag(kw)

    # 3. Nếu vẫn dưới 300 ký tự, bù bằng bộ hậu tố độc quyền thị trường Philippines
    if len(", ".join(tags_list)) < min_len:
        clean_seed = re.sub(r'[^\w\s\-]', '', seed_keyword).strip()
        if not clean_seed and backup_keywords:
            clean_seed = re.sub(r'(review|philippines|shopee|sulit|budol|2026).*$', '', backup_keywords[0], flags=re.IGNORECASE).strip()
        if not clean_seed:
            clean_seed = "shopee ph finds"

        ph_exclusive_suffixes = [
            "philippines 2026", "honest review", "sulit ba", "budol finds",
            "shopee ph", "worth it ba", "pros and cons", "review philippines",
            "budget finds ph", "legit check", "best buy 2026", "shopee haul ph",
            "sulit finds", "buying guide ph"
        ]
        for suf in ph_exclusive_suffixes:
            add_tag(f"{clean_seed} {suf}")
            if len(", ".join(tags_list)) >= min_len + 40:
                break

    final_tags = []
    for t in tags_list:
        candidate = ", ".join(final_tags + [t])
        if len(candidate) <= max_len:
            final_tags.append(t)
        else:
            break

    final_tags_str = ", ".join(final_tags)

    if match:
        return script_text[:match.start()] + f"3. TAGS:\n{final_tags_str}\n\n" + script_text[match.end():]
    else:
        script_pos = script_text.find("4. SCRIPT:")
        if script_pos != -1:
            return script_text[:script_pos] + f"3. TAGS:\n{final_tags_str}\n\n" + script_text[script_pos:]
        return script_text + f"\n\n3. TAGS:\n{final_tags_str}"

def sanitize_tts_script(script_text):
    allowed_tts_tags = {"laugh", "sigh", "gasp", "emphasis", "excited", "disappointed", "pause"}
    script_marker = "4. SCRIPT:"
    if script_marker not in script_text:
        return script_text

    head, body = script_text.split(script_marker, 1)

    def filter_brackets(m):
        inner = m.group(1).strip().lower()
        if inner in allowed_tts_tags:
            return f"[{inner}]"
        return ""

    cleaned_body = re.sub(r'\[([^\]]+)\]', filter_brackets, body)
    return head + script_marker + cleaned_body

# --- HÀM XỬ LÝ DỮ LIỆU SHOPEE PHILIPPINES ---
def extract_ids_from_url_or_text(url_str, raw_id=""):
    if raw_id and str(raw_id).strip() and not str(raw_id).startswith("UNKNOWN"):
        return str(raw_id).strip()
    if url_str:
        m1 = re.search(r'i\.(\d+)\.(\d+)', str(url_str))
        if m1:
            return f"i.{m1.group(1)}.{m1.group(2)}"
        m2 = re.search(r'/product/(\d+)/(\d+)', str(url_str))
        if m2:
            return f"i.{m2.group(1)}.{m2.group(2)}"
    return ""

def normalize_shopee_ph_url(url):
    if not url:
        return ""
    for domain in ["shopee.vn", "shopee.tw", "shopee.co.id", "shopee.co.th", "shopee.com.my", "shopee.sg"]:
        if domain in url:
            url = url.replace(domain, "shopee.ph")
    return url

def parse_shopee_json_search(json_texts):
    products = []
    seen_ids = set()
    for text in json_texts:
        try:
            data = json.loads(text)
            items = data.get('products', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            for idx, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                url = normalize_shopee_ph_url(item.get('productUrl') or item.get('url') or '')
                raw_pid = item.get('productId') or item.get('item_id') or item.get('itemid') or ''
                pid = extract_ids_from_url_or_text(url, raw_pid) or f"ITEM_{idx}_{len(products)}"

                if pid not in seen_ids:
                    products.append({
                        "product_id": str(pid),
                        "name": item.get('name') or item.get('title', 'Unknown Product'),
                        "url": url,
                        "price": str(item.get('price', 'N/A')),
                        "sales": str(item.get('salesVolume') or item.get('historical_sold') or item.get('sales', '0')),
                        "rating": str(item.get('rating') or item.get('item_rating', 'N/A'))
                    })
                    seen_ids.add(pid)
        except Exception as e:
            st.error(f"Lỗi parse JSON: {e}")
    return products

def parse_detailed_shopee_md(md_contents_list):
    scraped_data = []
    for idx, md_text in enumerate(md_contents_list):
        try:
            shop_id_match = re.search(r'\*\*Shop ID\*\*:\s*(\d+)', md_text)
            item_id_match = re.search(r'\*\*Item ID\*\*:\s*(\d+)', md_text)
            url_match = re.search(r'\*\*Product Link\*\*:\s*\[.*?\]\((.*?)\)', md_text)
            url = normalize_shopee_ph_url(url_match.group(1).strip()) if url_match else ""

            if shop_id_match and item_id_match:
                product_id = f"i.{shop_id_match.group(1).strip()}.{item_id_match.group(1).strip()}"
            else:
                extracted = extract_ids_from_url_or_text(url)
                product_id = extracted if extracted else f"PH_ITEM_{idx+1}_{int(time.time()*1000) % 100000}"

            title_match = re.search(r'^#\s+(.*?)\n', md_text, re.MULTILINE)
            price_match = re.search(r'\*\*Current Price\*\*:\s*(.*?)\n', md_text)
            rating_match = re.search(r'\*\*Rating\*\*:\s*(.*?)\n', md_text)

            title = title_match.group(1).strip() if title_match else f"Product_{idx+1}"
            if not url:
                url = f"https://shopee.ph/product-p.{product_id}"

            attr_match = re.search(r'## Product Attributes\n(.*?)(?=\n## |\Z)', md_text, re.DOTALL)
            attributes = f"## Product Specifications (Attributes)\n{attr_match.group(1).strip()}" if attr_match else ""

            desc_match = re.search(r'## Description\n(.*?)(?=\n## Shop Information|\Z)', md_text, re.DOTALL)
            if desc_match:
                raw_desc = desc_match.group(1).strip()
                clean_desc = re.sub(r'!\[.*?\]\(http.*?\)', '', raw_desc)
                description = f"## Product Description\n{clean_desc}"
            else:
                description = ""

            final_description = f"{attributes}\n\n{description}".strip()
            images = re.findall(r'!\[.*?\]\((http.*?)\)', md_text)

            scraped_data.append({
                "product_id": product_id,
                "name": title,
                "url": url,
                "price": price_match.group(1).strip() if price_match else "N/A",
                "rating": rating_match.group(1).strip() if rating_match else "N/A",
                "description": final_description,
                "full_text_length": len(final_description),
                "images": images
            })
        except Exception as e:
            st.error(f"Lỗi đọc file MD Chi tiết #{idx+1}: {e}")
    return scraped_data

def process_single_ocr(item):
    TEXT_THRESHOLD = 450
    if item['full_text_length'] < TEXT_THRESHOLD:
        print(f"[Pro Edition PH] Sản phẩm {item['product_id']} đang quét OCR English...")
        ocr_prompt = """You are an e-commerce product specification OCR extractor for Shopee Philippines.
Task: Extract core technical specifications, key features, warranty info, and real selling points from the product images.
Rules:
1. Output in clear, concise English bullet points.
2. Focus on factual specs (battery capacity, materials, compatibility, dimensions, warranty). No marketing fluff."""

        if 'images' in item and len(item['images']) > 0:
            gemini_contents = [ocr_prompt]
            target_images = item['images'][:4]
            has_valid_image = False

            for img_url in target_images:
                try:
                    res = requests.get(img_url, timeout=10)
                    if res.status_code == 200:
                        img = Image.open(io.BytesIO(res.content))
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        gemini_contents.append(img)
                        has_valid_image = True
                except Exception:
                    pass

            if has_valid_image:
                try:
                    ocr_result = call_gemini_with_retry(gemini_contents, target_model=MODEL_ID).text
                    item['description'] += "\n\n[Shopee Image OCR Specs]:\n" + ocr_result
                except Exception as e:
                    print(f"Lỗi API OCR: {e}")
    return item

def match_selected_top5(selected_ids, scraped_details):
    final_5 = []
    used_indices = set()
    rank_labels = ["Top 5", "Top 4", "Top 3", "Top 2", "Top 1"]

    for pid in selected_ids:
        pid_str = str(pid).strip()
        if not pid_str:
            continue
        matched_idx = None
        for i, item in enumerate(scraped_details):
            if i not in used_indices and str(item['product_id']).strip() == pid_str:
                matched_idx = i
                break
        if matched_idx is None:
            core_digits = re.findall(r'\d{5,}', pid_str)
            for i, item in enumerate(scraped_details):
                if i in used_indices:
                    continue
                item_pid = str(item['product_id'])
                if pid_str in item_pid or item_pid in pid_str or any(d in item_pid for d in core_digits):
                    matched_idx = i
                    break
        if matched_idx is not None:
            used_indices.add(matched_idx)
            final_5.append(scraped_details[matched_idx].copy())

    for i, item in enumerate(scraped_details):
        if len(final_5) >= 5:
            break
        if i not in used_indices:
            used_indices.add(i)
            final_5.append(item.copy())

    for idx, item in enumerate(final_5[:5]):
        item['ASSIGNED_RANK'] = rank_labels[idx]

    return final_5[:5]

# --- GIAO DIỆN CHÍNH ---
st.title("🇵🇭 Tool Tự Động Kịch Bản Shopee Philippines (Pro Edition - Real Talk & Budol Check)")

with st.sidebar:
    st.header("⚙️ Cài Đặt Đầu Vào (Philippines)")
    seed_keywords = st.text_input(
        "Từ khóa ngách (BẮT BUỘC):",
        placeholder="VD: wireless mechanical keyboard philippines..."
    )
    selected_persona = st.selectbox("Chọn Phong cách Reviewer:", list(PERSONA_DICT_PH.keys()))
    specific_theme = st.text_input(
        "Định hướng tệp khách hàng (Tùy chọn):",
        placeholder="VD: WFH setup, student budget under 1500 pesos, pang-matagalan..."
    )
    trending_memes = st.text_input(
        "🔥 Câu nói/Trend muốn chèn riêng (Bỏ trống AI tự sáng tạo):",
        placeholder="VD: Budol is real pero doon tayo sa sulit..."
    )
    manual_niche_notes = st.text_area(
        "📝 Ghi chú định hướng ngách (Hoặc upload zghichu.txt):",
        placeholder="Dán nội dung zghichu.txt vào đây hoặc upload trực tiếp...",
        height=110
    )
    with st.expander("🛠️ Tùy chọn nâng cao (Loại trừ mã sản phẩm)"):
        avoid_ch1_products = st.text_input(
            "Mã ID/Tên sản phẩm không muốn xếp Top 1 (Có thể bỏ trống):",
            placeholder="Bỏ trống hệ thống vẫn tự động chọn Dark Horse làm Top 1..."
        )

tab1, tab2 = st.tabs([
    "📌 BƯỚC 1: Phân Tích Từ Khóa & Lọc 15 Deal Shopee PH",
    "✍️ BƯỚC 2: Xuất Kịch Bản 7-8 Phút Chuẩn Taglish"
])

# ==========================================
# BƯỚC 1: TỪ KHÓA CSV/TXT + JSON SHOPEE -> CHỌN 15 SẢN PHẨM
# ==========================================
with tab1:
    st.info("Upload file Từ khóa (.CSV), file Ghi chú ngách (.TXT như zghichu.txt nếu có) và file Kết quả tìm kiếm Shopee Philippines (.JSON).")
    col1, col2 = st.columns(2)
    with col1:
        vidiq_files = st.file_uploader(
            "1. Tệp Từ khóa (.CSV) & Ghi chú (.TXT)",
            type=["csv", "txt"],
            accept_multiple_files=True,
            key="b1_csv"
        )
    with col2:
        json_files_search = st.file_uploader(
            "2. Tệp Kết quả Shopee PH (.JSON)",
            type="json",
            accept_multiple_files=True,
            key="b1_json"
        )

    if st.button("🚀 Quét & Lọc Bước 1 (Philippines SEO)", type="primary"):
        csv_uploads = [f for f in vidiq_files if f.name.lower().endswith('.csv')] if vidiq_files else []
        txt_uploads = [f for f in vidiq_files if f.name.lower().endswith('.txt')] if vidiq_files else []

        txt_notes_str, txt_kws = parse_txt_notes(txt_uploads)
        combined_niche_notes = "\n".join([s for s in [manual_niche_notes.strip(), txt_notes_str] if s]).strip()

        effective_seed = seed_keywords.strip()
        if not effective_seed and combined_niche_notes:
            m_seed = re.search(r'ĐỊNH HƯỚNG NGÁCH:\s*(.*?)\n', combined_niche_notes)
            if m_seed:
                effective_seed = m_seed.group(1).strip()

        if not effective_seed:
            st.error("⚠️ Vui lòng điền 'Từ khóa ngách' ở cột bên trái hoặc upload file zghichu.txt!")
            st.stop()

        if (not csv_uploads and not txt_kws) or not json_files_search:
            st.warning("⚠️ Vui lòng upload đủ file Từ khóa (.CSV / .TXT) và file Shopee (.JSON)!")
            st.stop()

        with st.status("Đang phân tích từ khóa và lọc 15 sản phẩm 'Sulit' nhất trên Shopee PH..."):
            vidiq_df = parse_uploaded_csvs(csv_uploads, txt_kws)
            if vidiq_df.empty:
                st.error("⚠️ Không tìm thấy dữ liệu từ khóa hợp lệ trong file CSV/TXT. Vui lòng kiểm tra lại!")
                st.stop()

            csv_data = vidiq_df.to_csv(index=False)
            raw_csv_keywords = vidiq_df['Keyword'].tolist()
            st.write(f"📊 Đã đọc {len(raw_csv_keywords)} từ khóa gốc từ file đầu vào.")

            json_texts = [f.getvalue().decode("utf-8", errors="ignore") for f in json_files_search]
            shopee_raw_data = parse_shopee_json_search(json_texts)

            if not shopee_raw_data:
                st.error("⚠️ Không bóc tách được sản phẩm từ file JSON. Vui lòng kiểm tra lại cấu trúc file!")
                st.stop()

            st.write("🧠 AI đang mở rộng bộ từ khóa English + Taglish chuẩn tìm kiếm Philippines...")
            prompt1 = (
                P1_TEMPLATE_PH.replace("{csv_data}", csv_data)
                .replace("{seed_keywords}", effective_seed)
                .replace("{niche_notes}", combined_niche_notes if combined_niche_notes else "Không có")
            )
            res1 = call_gemini_with_retry(prompt1, response_mime_type="application/json")
            keywords_json = clean_and_parse_json(res1.text)

            ai_kws_list = keywords_json.get("keywords", []) if isinstance(keywords_json, dict) else []
            existing_set = {str(k.get("keyword", "")).strip().lower() for k in ai_kws_list if isinstance(k, dict)}
            for _, row in vidiq_df.iterrows():
                kw_orig = str(row['Keyword']).strip()
                if kw_orig.lower() not in existing_set:
                    ai_kws_list.append({"keyword": kw_orig, "volume": int(row['Volume'])})
                    existing_set.add(kw_orig.lower())
            keywords_json = {"detected_brands": keywords_json.get("detected_brands", []) if isinstance(keywords_json, dict) else [], "keywords": ai_kws_list}

            st.write(f"✅ Tổng kho từ khóa sau khi AI mở rộng: {len(ai_kws_list)} từ khóa.")

            st.write("🎯 Đang chấm điểm và chọn Top 15 sản phẩm Shopee Philippines...")
            prompt2 = (
                P2_TEMPLATE_PH.replace("{shopee_data}", json.dumps(shopee_raw_data, ensure_ascii=False))
                .replace("{keywords_json}", json.dumps(keywords_json, ensure_ascii=False))
                .replace("{niche_notes}", combined_niche_notes if combined_niche_notes else "Không có")
            )
            if specific_theme.strip():
                prompt2 += f"\n\nLƯU Ý CỰC KỲ QUAN TRỌNG: Ưu tiên chọn các sản phẩm phù hợp nhất với nhu cầu: '{specific_theme}'."

            res2 = call_gemini_with_retry(prompt2, response_mime_type="application/json")
            top_15_json = clean_and_parse_json(res2.text)

            st.session_state['saved_keywords'] = keywords_json
            st.session_state['raw_csv_keywords'] = raw_csv_keywords
            st.session_state['top_15_json'] = top_15_json
            st.session_state['saved_niche_notes'] = combined_niche_notes
            st.session_state['effective_seed'] = effective_seed

        st.success("✅ Đã chốt danh sách 15 mã 'Sulit' nhất trên Shopee PH! Bấm vào link dưới để lấy dữ liệu .MD chi tiết.")

    if 'top_15_json' in st.session_state:
        st.markdown("### 🎯 DANH SÁCH 15 LINK SHOPEE PHILIPPINES CẦN LẤY DATA:")
        top_15_data = st.session_state['top_15_json']
        items_list = []
        if isinstance(top_15_data, list):
            items_list = top_15_data
        elif isinstance(top_15_data, dict):
            items_list = top_15_data.get('top_15') or next((v for v in top_15_data.values() if isinstance(v, list)), [])

        for count, item in enumerate(items_list, 1):
            if not isinstance(item, dict):
                continue
            url = normalize_shopee_ph_url(item.get('url') or item.get('productUrl') or item.get('product_url') or '')
            product_id = item.get('product_id', 'UNKNOWN')
            name = str(item.get('name', 'Product'))
            reason = str(item.get('reason', ''))
            if url:
                html_link = f'{count}. 👉 **{product_id}** - {name[:45]}... : <a href="{url}" target="_blank">{url}</a> <i>({reason})</i>'
                st.markdown(html_link, unsafe_allow_html=True)
            else:
                st.warning(f'{count}. 👉 **{product_id}** - {name[:45]}... : ⚠️ Thiếu Link. Tìm theo ID: {product_id}')

# ==========================================
# BƯỚC 2: UPLOAD MD CHI TIẾT -> XUẤT KỊCH BẢN 7-8 PHÚT
# ==========================================
with tab2:
    st.info("Upload 15 file .MD chi tiết sản phẩm Shopee PH. (Nếu chạy tắt không qua Bước 1, hãy upload kèm file .CSV/.TXT vào ô số 1 bên dưới).")
    col_b2_1, col_b2_2 = st.columns(2)
    with col_b2_1:
        direct_kw_files = st.file_uploader(
            "1. Upload Từ khóa (.CSV) & Ghi chú (.TXT) (Bỏ qua nếu đã chạy Bước 1):",
            type=["csv", "txt"],
            accept_multiple_files=True,
            key="b2_kw"
        )
    with col_b2_2:
        detailed_md_files = st.file_uploader(
            "2. Upload 15 file .MD chi tiết của Shopee PH:",
            type="md",
            accept_multiple_files=True,
            key="b2_md"
        )

    if st.button("✨ Đạo diễn chọn Top 5 & Xuất Kịch Bản Philippines", type="primary"):
        if not detailed_md_files:
            st.warning("⚠️ Vui lòng upload các file .MD chi tiết sản phẩm!")
            st.stop()

        csv_b2 = [f for f in direct_kw_files if f.name.lower().endswith('.csv')] if direct_kw_files else []
        txt_b2 = [f for f in direct_kw_files if f.name.lower().endswith('.txt')] if direct_kw_files else []
        txt_notes_b2, txt_kws_b2 = parse_txt_notes(txt_b2)

        niche_notes_saved = "\n".join(
            [s for s in [manual_niche_notes.strip(), txt_notes_b2, st.session_state.get('saved_niche_notes', '')] if s]
        ).strip()

        effective_seed = seed_keywords.strip() or st.session_state.get('effective_seed', '')
        if not effective_seed and niche_notes_saved:
            m_seed = re.search(r'ĐỊNH HƯỚNG NGÁCH:\s*(.*?)\n', niche_notes_saved)
            if m_seed:
                effective_seed = m_seed.group(1).strip()

        if not effective_seed:
            st.error("⚠️ BẮT BUỘC: Điền 'Từ khóa ngách' ở cột bên trái hoặc upload file zghichu.txt!")
            st.stop()

        with st.status("Đang thiết lập Đội hình Top 5 & Biên kịch Taglish 'Real Talk & Budol Check' (7-8 phút)..."):
            if 'saved_keywords' not in st.session_state or csv_b2 or txt_kws_b2:
                vidiq_df = parse_uploaded_csvs(csv_b2, txt_kws_b2)
                if not vidiq_df.empty:
                    st.write("🧠 Đang mở rộng kho từ khóa SEO Philippines...")
                    csv_data = vidiq_df.to_csv(index=False)
                    raw_csv_keywords = vidiq_df['Keyword'].tolist()
                    prompt1 = (
                        P1_TEMPLATE_PH.replace("{csv_data}", csv_data)
                        .replace("{seed_keywords}", effective_seed)
                        .replace("{niche_notes}", niche_notes_saved if niche_notes_saved else "Không có")
                    )
                    res1 = call_gemini_with_retry(prompt1, response_mime_type="application/json")
                    keywords_json = clean_and_parse_json(res1.text)
                    ai_kws_list = keywords_json.get("keywords", []) if isinstance(keywords_json, dict) else []
                    existing_set = {str(k.get("keyword", "")).strip().lower() for k in ai_kws_list if isinstance(k, dict)}
                    for _, row in vidiq_df.iterrows():
                        kw_orig = str(row['Keyword']).strip()
                        if kw_orig.lower() not in existing_set:
                            ai_kws_list.append({"keyword": kw_orig, "volume": int(row['Volume'])})
                            existing_set.add(kw_orig.lower())
                    st.session_state['saved_keywords'] = {"keywords": ai_kws_list}
                    st.session_state['raw_csv_keywords'] = raw_csv_keywords
                elif 'saved_keywords' not in st.session_state:
                    st.session_state['saved_keywords'] = {"keywords": [{"keyword": effective_seed, "volume": 5000}]}
                    st.session_state['raw_csv_keywords'] = [effective_seed]

            md_contents = [f.getvalue().decode("utf-8", errors="ignore") for f in detailed_md_files]
            scraped_details = parse_detailed_shopee_md(md_contents)

            st.write("👁️ Quét OCR thông số kỹ thuật cho các sản phẩm thiếu mô tả...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                scraped_details = list(executor.map(process_single_ocr, scraped_details))

            st.write("⚖️ Giám khảo AI đang chọn Đội hình Top 5 Pinaka-Sulit...")
            if avoid_ch1_products.strip():
                avoid_instruction = (
                    f"- LƯU Ý LOẠI TRỪ ĐẶC BIỆT: Tuyệt đối KHÔNG chọn sản phẩm [{avoid_ch1_products.strip()}] làm `top_1_best_overall` (Quán quân), "
                    f"hãy ưu tiên chọn mã sản phẩm khác xuất sắc trong danh sách!"
                )
            else:
                avoid_instruction = ""

            prompt3 = (
                P3_TEMPLATE_PH.replace("{scraped_data}", json.dumps(scraped_details, ensure_ascii=False))
                .replace("{avoid_ch1_instruction}", avoid_instruction)
            )
            if specific_theme.strip() or niche_notes_saved:
                prompt3 += f"\n\nĐỊNH HƯỚNG NGÁCH & GÓC TIẾP CẬN: {specific_theme} | {niche_notes_saved}"

            res3 = call_gemini_with_retry(prompt3, response_mime_type="application/json", target_model=PRO_MODEL_ID)
            top5_decision = clean_and_parse_json(res3.text)
            if isinstance(top5_decision, list):
                top5_decision = top5_decision[0]

            selected_ids = [
                top5_decision.get('top_5_alternative_1'),
                top5_decision.get('top_4_alternative_2'),
                top5_decision.get('top_3_value_for_money'),
                top5_decision.get('top_2_premium'),
                top5_decision.get('top_1_best_overall')
            ]

            final_5_data = match_selected_top5(selected_ids, scraped_details)

            # Tổng hợp từ khóa SEO
            matched_keywords = set()
            top_15_data = st.session_state.get('top_15_json', {})
            items_15 = top_15_data.get('top_15', []) if isinstance(top_15_data, dict) else (top_15_data if isinstance(top_15_data, list) else [])
            for item in items_15:
                if isinstance(item, dict):
                    orig_pid = str(item.get('product_id', ''))
                    if orig_pid and any(orig_pid in str(sel_item.get('product_id', '')) for sel_item in final_5_data):
                        for kw in item.get('relevant_keywords', []):
                            matched_keywords.add(str(kw).strip())

            keywords_json = st.session_state['saved_keywords']
            all_kw_objs = keywords_json.get('keywords', [])
            all_kw_objs_sorted = sorted(
                all_kw_objs,
                key=lambda x: int(re.sub(r'[^\d]', '', str(x.get('volume', 0))) or 0),
                reverse=True
            )
            raw_csv_kws = st.session_state.get('raw_csv_keywords', [])
            combined_seo_kws = []
            seen_kw = set()
            for kw in list(matched_keywords) + raw_csv_kws + [k.get('keyword', '') for k in all_kw_objs_sorted]:
                kw_clean = str(kw).strip()
                if kw_clean and kw_clean.lower() not in seen_kw:
                    seen_kw.add(kw_clean.lower())
                    combined_seo_kws.append(kw_clean)

            seo_keywords_str = ", ".join(combined_seo_kws[:30])

            # Cô lập hoàn toàn traits và kho meme theo từng Persona
            persona_obj = PERSONA_DICT_PH[selected_persona]
            persona_traits_str = persona_obj["traits"]
            persona_memes_str = " | ".join(persona_obj["memes"])

            if trending_memes.strip():
                meme_instruction = (
                    f"- **Sáng tạo Ngôn ngữ mạng theo Nhân cách**: Ưu tiên lồng ghép tự nhiên ý tưởng: [{trending_memes}]. "
                    f"Đồng thời tham khảo tinh thần của riêng nhân cách này: [{persona_memes_str}] để biến tấu câu chữ duyên dáng."
                )
            else:
                meme_instruction = (
                    f"- **Tự do Sáng tạo Khẩu ngữ & Hài hước Độc Quyền theo Nhân cách**: "
                    f"Dưới đây là tinh thần khẩu ngữ riêng biệt của nhân cách '{selected_persona}': [{persona_memes_str}]. "
                    f"Hãy dùng chúng làm cảm hứng để TỰ DO SÁNG TẠO 2-4 câu nhận xét sắc sảo, hài hước khớp với tính năng thực tế của 5 sản phẩm (tuyệt đối không bê nguyên xi một cách máy móc)."
                )

            st.write("✍️ Đang viết kịch bản chuẩn Pinoy Creator (1.150 - 1.350 từ Taglish mượt mà cho TTS)...")
            prompt4 = (
                P4_TEMPLATE_PH.replace("{final_5_data}", json.dumps(final_5_data, ensure_ascii=False))
                .replace("{refined_keywords}", seo_keywords_str)
                .replace("{seed_keywords}", effective_seed)
                .replace("{niche_notes}", niche_notes_saved if niche_notes_saved else "Real talk review, check sulit vs sayang pera")
                .replace("{selected_persona}", selected_persona)
                .replace("{persona_traits}", persona_traits_str)
                .replace("{meme_instruction}", meme_instruction)
            )

            if specific_theme.strip():
                prompt4 = prompt4.replace(
                    "## ĐẦU VÀO DỰ ÁN",
                    f"## ĐẦU VÀO DỰ ÁN\n- **Định hướng tệp khách hàng mục tiêu**: {specific_theme}"
                )

            res4 = call_gemini_with_retry(prompt4, target_model=PRO_MODEL_ID)
            main_script = res4.text

            # 1. Điền Link Shopee PH thật
            for item in final_5_data:
                rank_label = item.get('ASSIGNED_RANK', '')
                if rank_label:
                    rank_num = rank_label.replace('Top ', '').strip()
                    placeholder = f"{{LINK_{rank_num}}}"
                    main_script = main_script.replace(placeholder, item.get('url', ''))

            # 2. Bù TAGS 300 - 450 ký tự theo thuật toán Anti-Footprint PH
            main_script = enforce_tags_section_ph(
                script_text=main_script,
                backup_keywords=combined_seo_kws,
                seed_keyword=effective_seed,
                final_5_data=final_5_data,
                min_len=300,
                max_len=450
            )

            # 3. Làm sạch thẻ TTS trong phần 4. SCRIPT
            main_script = sanitize_tts_script(main_script)

        tags_match = re.search(r'3\.\s*TAGS\s*:\s*\n?(.*?)(?=\n+\s*4\.\s*SCRIPT\s*:)', main_script, re.DOTALL)
        tags_len = len(tags_match.group(1).strip()) if tags_match else 0
        script_part = main_script.split("4. SCRIPT:")[-1] if "4. SCRIPT:" in main_script else main_script
        clean_spoken_text = re.sub(r'<[^>]+>|\[[^\]]+\]', ' ', script_part)
        word_count = len(re.findall(r'\b[\w\-]+\b', clean_spoken_text))
        est_minutes = round(word_count / 160, 1)

        st.success(
            f"🎉 Xuất lò kịch bản Philippines hoàn chỉnh! | "
            f"🏷️ Độ dài TAGS: **{tags_len} ký tự** (Chuẩn 300-450) | "
            f"📝 Số từ (Words): **{word_count} từ** (~{est_minutes} phút đọc)"
        )
        st.text_area("Kịch Bản Hoàn Chỉnh (Copy hoặc đưa vào Worker)", value=main_script, height=650)

        with st.expander("🔍 Xem Đội Hình Top 5 & Lý do xếp hạng"):
            st.write("**Lý do xếp hạng của Giám khảo AI:**", top5_decision.get("reasoning", ""))
            st.write("**Danh sách Từ khóa SEO đã dùng & mở rộng:**", combined_seo_kws)
            st.json(final_5_data)