import streamlit as st
import toml
import datetime
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw, ImageFont
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import numpy as np

# --- 설정 관리 ---
CONTRACT_CONFIG = {
    "bg_image": "contract.png",
    "font_path": "./fonts/NanumGothic-Regular.ttf",
    "font_size": 20,
    "signature_size": (250, 100),
    "positions": {
        "name_top": (630, 345),
        "date": (630, 918),
        "name_bottom": (720, 1210),
        "signature": (800, 1198),
        "jumin": (720, 1143),
        "contact": (720, 1175),
        "contract_date": (390, 1012)
    }
}

# TOML 비밀 설정 파일 읽기
secrets = toml.load(".streamlit/secrets.toml")

# --- 성능 최적화: 캐싱 ---
@st.cache_data
def load_image(image_path):
    """이미지를 로드하고 캐시에 저장합니다."""
    return Image.open(image_path).convert("RGBA")

@st.cache_data
def load_font(font_path, size):
    """폰트를 로드하고 캐시에 저장합니다."""
    try:
        return ImageFont.truetype(font_path, size=size)
    except IOError:
        return ImageFont.load_default()

# --- 코드 구조 개선: 기능별 함수 ---
def create_contract_image(base_image, signature_data, user_info, today):
    """사용자 정보와 서명을 바탕으로 최종 계약서 이미지를 생성합니다."""
    signature_image = Image.fromarray(signature_data.astype("uint8")).convert("RGBA")

    # 서명 배경 투명 처리
    datas = signature_image.getdata()
    new_data = []
    for item in datas:
        if item[0:3] == (255, 255, 255):
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    signature_image.putdata(new_data)

    resized_signature = signature_image.resize(CONTRACT_CONFIG["signature_size"])
    combined_image = base_image.copy()
    combined_image.paste(resized_signature, CONTRACT_CONFIG["positions"]["signature"], resized_signature)

    draw = ImageDraw.Draw(combined_image)
    font = load_font(CONTRACT_CONFIG["font_path"], CONTRACT_CONFIG["font_size"])

    # 텍스트 추가
    draw.text(CONTRACT_CONFIG["positions"]["jumin"], user_info["jumin"], fill="black", font=font)
    draw.text(CONTRACT_CONFIG["positions"]["contact"], user_info["contact"], fill="black", font=font)
    draw.text(CONTRACT_CONFIG["positions"]["name_bottom"], user_info["name"], fill="black", font=font)
    draw.text(CONTRACT_CONFIG["positions"]["name_top"], user_info["name"], fill="black", font=font)
    
    # 계약일자 추가
    date_text = f"계약일자 :   {today.year} 년   {today.month} 월   {today.day} 일"
    draw.text(CONTRACT_CONFIG["positions"]["contract_date"], date_text, fill="black", font=font)

    return combined_image

def send_contract_email(image_buffer, user_info, today):
    """생성된 계약서 이미지를 이메일로 전송합니다."""
    contract_name = secrets["contract_name"]
    sender_email = secrets['sender']
    receiver_email = secrets['receiver']
    subject = f"[{today}] {user_info['name']} {contract_name}"
    body = f"[{today}] {user_info['name']} {contract_name}"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)
    msg_text = MIMEText(body, 'plain')
    msg_alternative.attach(msg_text)

    msg_html = MIMEText(f'''
    <html><body>
        <p>{body}</p>
        <img src="cid:image1" width="800" height="1080">
    </body></html>
    ''', 'html')
    msg_alternative.attach(msg_html)

    image_buffer.seek(0);
    msg_image = MIMEImage(image_buffer.read(), _subtype="png")
    msg_image.add_header('Content-ID', '<image1>')
    msg.attach(msg_image)

    image_buffer.seek(0);
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(image_buffer.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename=signed_{user_info['name']}_{today}.png")
    msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, secrets["email_passwd"])
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        return True, None
    except Exception as e:
        return False, e

def main_app():
    """메인 애플리케이션 로직"""
    contract_name = secrets["contract_name"]
    st.title(f"SKNs {contract_name} 작성")
    st.info(f"아래 {contract_name}를 검토후 내용을 입력하고 작성완료를 눌러주세요.")

    # 캐시된 리소스 로드
    background_image = load_image(CONTRACT_CONFIG["bg_image"])

    with st.form(key="contract_form"):
        st.write(f"**{contract_name} 미리 보기:**")
        st.image(background_image, use_column_width=True)

        jumin_input = st.text_input("생년월일 입력", placeholder="생년월일 입력하세요 (19970516)")
        contact_input = st.text_input("연락처 입력", placeholder="연락처를 입력하세요 (010-9999-9999)")
        name_input = st.text_input("이름 입력", placeholder="이름을 입력하세요")

        st.write("**서명을 작성해주세요.**")
        signature_canvas = st_canvas(
            background_color="#ffffff",
            width=400,
            height=200,
            drawing_mode="freedraw",
            stroke_width=8,
            stroke_color="#000000",
            key="signature_canvas"
        )
        
        submit_button = st.form_submit_button('작성완료')

    if submit_button:
        # 입력 유효성 검사
        if not jumin_input:
            st.error("생년월일을 입력하고 작성완료 버튼을 눌러주세요.")
        elif not contact_input:
            st.error("연락처를 입력하고 작성완료 버튼을 눌러주세요.")
        elif not name_input:
            st.error("이름을 입력하고 작성완료 버튼을 눌러주세요.")
        elif signature_canvas.image_data is None or np.all(signature_canvas.image_data[:, :, :3] == 255):
            st.error("서명을 작성하고 작성완료 버튼을 눌러주세요.")
        else:
            today = datetime.date.today()
            user_info = {"name": name_input, "jumin": jumin_input, "contact": contact_input}

            with st.spinner(f'{contract_name} 생성중...'):
                # 1. 계약서 이미지 생성
                final_image = create_contract_image(
                    base_image=background_image,
                    signature_data=signature_canvas.image_data,
                    user_info=user_info,
                    today=today
                )
                
                buffer = io.BytesIO()
                final_image.save(buffer, format="PNG")
                buffer.seek(0);

                # 2. 이메일 전송
                success, error = send_contract_email(buffer, user_info, today)

                if success:
                    st.success(f"{contract_name} 작성이 완료되었습니다. 계약서를 저장 하시려면 아래의 다운로드 버튼을 눌러주세요.")
                    st.download_button(
                        label=f"{contract_name} 다운로드",
                        data=buffer,
                        file_name=f"skns_contract_signed_{today}.png",
                        mime="image/png",
                    )
                else:
                    st.error(f"작성 실패했습니다. 담당자에게 문의해주세요.\n에러: {error}")

if __name__ == '__main__':
    if secrets.get('contract_visible', False):
        main_app()
    else:
        st.title("SKNs 계약서 작성")
        st.info("계약서 작성 기능은 현재 비활성화 상태입니다. 관리자에게 문의하세요.")
