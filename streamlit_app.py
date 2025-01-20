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


# 1. TOML 파일 읽기
config = toml.load(".streamlit/secrets.toml")

# @st.cache_resource
# def redis_resource():
#     redis_client = redis.Redis(
#         host='redis-14168.c340.ap-northeast-2-1.ec2.redns.redis-cloud.com',# Redis 서버 주소
#         port=14168,            # Redis 포트
#         username='default',  # 사용자 이름
#         password=config['redis_passwd'],  # 비밀번호 설정
#         db=0                  # 기본 DB
#     )
#     return redis_client

def resume():
# 타이틀
    st.title("SKNs 근로계약서 작성")
    st.info("서명을 작성하고, 이름을 입력한 후 작성완료 버튼을 눌러주세요.")

    # 배경 이미지 로드
    background_image = Image.open("snapshot.png").convert("RGBA")

    # 배경 이미지 크기
    canvas_width, canvas_height = background_image.size


    with st.form(key="my_form_1"):

        # **배경 이미지 미리 보기**
        st.write("**근로계약서 미리 보기:**")
        st.image(background_image, caption="배경 이미지", use_column_width=True)

        # 이름 입력
        # st.write("**이름을 입력하세요:**")
        name_input = st.text_input("이름 입력", placeholder="여기에 이름을 입력하세요")

        # 서명 드로우 캔버스 설정
        st.write("**서명을 작성해주세요.**")
        signature_canvas = st_canvas(
            background_color="#ffffff",            # 서명 캔버스 배경 색상
            width=400,                             # 서명 캔버스 너비
            height=150,                            # 서명 캔버스 높이
            drawing_mode="freedraw",               # 자유 그리기 모드
            stroke_width=3,                        # 서명 선 두께
            stroke_color="#000000",                # 서명 선 색상 (기본 검정)
            key="signature_canvas"                 # 고유 키
        )
        submit =  st.form_submit_button('작성완료')


    # 서명 캔버스와 배경 이미지 합성
    if submit:
        if signature_canvas.image_data is not None:
            # 서명 데이터를 PIL 이미지로 변환
            signature_image = Image.fromarray((signature_canvas.image_data).astype("uint8")).convert("RGBA")
            
            # 서명 배경을 투명하게 설정
            datas = signature_image.getdata()
            new_data = []
            for item in datas:
                if item[0:3] == (255, 255, 255):  # 흰색 배경 투명화
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            signature_image.putdata(new_data)

            # 서명 이미지를 배경 이미지에 합성 (크기를 조정하여 삽입)
            x_position = 470  # 고정 X 좌표
            y_position = 1200  # 고정 Y 좌표
            resized_signature = signature_image.resize((200, 75))  # 서명 이미지를 200x75로 축소
            combined_image = background_image.copy()
            combined_image.paste(resized_signature, (x_position, y_position), resized_signature)

            # 이름 텍스트를 이미지로 변환하여 추가
            if name_input:
                draw = ImageDraw.Draw(combined_image)
                text_position = (350, 1220)  # 이름 위치 (조정)
                
                # 폰트 로딩
                try:
                    font = ImageFont.truetype("./fonts/NanumGothic-Regular.ttf", size=20)
                except IOError:
                    font = ImageFont.load_default()  # 폰트 파일을 찾을 수 없으면 기본 폰트 사용

                # 이름 텍스트를 이미지로 추가
                draw.text(text_position, name_input, fill="black", font=font)

                # 이미지를 저장할 수 있는 버퍼 생성
                buffer = io.BytesIO()
                combined_image.save(buffer, format="PNG")
                buffer.seek(0)
                # st.success("이미지가 성공적으로 저장되었습니다.")
                
                sender_email = "wonchul.no@gmail.com"
                receiver_email = "ninja0516@naver.com"
                subject = f"[{datetime.date.today()}] {name_input} 근로계약서"
                body = f"[{datetime.date.today()}] {name_input} 근로계약서"

                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = receiver_email
                msg['Subject'] = subject

                msg_alternative = MIMEMultipart('alternative')
                msg.attach(msg_alternative)

                msg_text = MIMEText(body, 'plain')
                msg_alternative.attach(msg_text)

                # HTML 본문에 이미지 포함
                msg_html = MIMEText(f'<html><body><p>{body}</p><img src="cid:image1"></body></html>', 'html')
                msg_alternative.attach(msg_html)

                # 이미지 본문에 포함
                msg_image = MIMEImage(buffer.getvalue())
                msg_image.add_header('Content-ID', '<image1>')
                msg.attach(msg_image)

                # 이미지 첨부 파일로 추가
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(buffer.getvalue())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', "attachment; filename= combined_image.png")
                msg.attach(part)

                with st.spinner('근로계약서 생성중 조금만 기다려주세요...'):
                    try:
                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(sender_email, config["email_passwd"])
                        text = msg.as_string()
                        server.sendmail(sender_email, receiver_email, text)
                        server.quit()
                        st.success("근로계약서 작성이 완료되었습니다. 근로계약서를 다운로드 하시려면 아래의 다운로드 버튼을 눌러주세요")
                    except Exception as e:
                        st.error(f"작성 실패했습니다 담당자에게 문의해주세요.")

            # 최종 이미지 다운로드 버튼 제공
            st.download_button(
                label="근로계약서 다운로드",
                data=buffer,
                file_name="signed_with_name_image.png",
                mime="image/png",
            )
        else:
            st.warning("서명을 먼저 작성해주세요!")
    else:
        # st.info("캔버스에서 서명을 작성하고, 이름을 입력한 후 저장 버튼을 눌러주세요.")
        pass

def main():
    resume()


if __name__ == '__main__':
    main()