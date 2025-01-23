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


# 1. TOML 파일 읽기
config = toml.load(".streamlit/secrets.toml")


def resume():
    contract_name = config["contract_name"]

    # 오늘 날짜 가져오기
    today = datetime.date.today()
    year = today.year
    month = today.month
    day = today.day

    # st.title("🎉 SKNs 근로계약서 작성")
    st.title(f"SKNs {contract_name} 작성")
    st.info("서명을 작성하고, 이름을 입력한 후 작성완료 버튼을 눌러주세요.")
    
    if contract_name == '근로계약서':
        bg_image_name = 'snapshot.png'
        name_position = (350, 1220)
        signature_position = (470, 1200)
        year_position = (350, 1250)
        month_position = (450, 1250)
        day_position = (550, 1250)
    elif contract_name == '위탁계약서':
        bg_image_name = 'snapshot_1.png'
        name_position = (350, 1220)
        signature_position = (470, 1200)
        year_position = (350, 1250)
        month_position = (450, 1250)
        day_position = (550, 1250)
    else:
        st.stop()

    # 배경 이미지 로드
    background_image = Image.open(bg_image_name).convert("RGBA")

    # 배경 이미지 크기
    canvas_width, canvas_height = background_image.size


    with st.form(key="my_form_1"):

        # **배경 이미지 미리 보기**
        st.write(f"**{contract_name} 미리 보기:**")
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

    # print('+',name_input,'+',signature_canvas.image_data,'+')
    # 서명 캔버스와 배경 이미지 합성
    if submit:
        if name_input:
            if signature_canvas.image_data is not None:
                if np.all(signature_canvas.image_data[:, :, :3] == 255):
                    st.warning("서명을 작성하고 작성완료 버튼을 눌러주세요.")
                else:
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
                    resized_signature = signature_image.resize((200, 75))  # 서명 이미지를 200x75로 축소
                    combined_image = background_image.copy()
                    combined_image.paste(resized_signature, signature_position, resized_signature)

                    # 이름 텍스트를 이미지로 변환하여 추가
                    # if name_input:
                    draw = ImageDraw.Draw(combined_image)
                    # text_position = (x_position_name, y_position_name)  # 이름 위치 (조정)
                    # 폰트 로딩
                    try:
                        font = ImageFont.truetype("./fonts/NanumGothic-Regular.ttf", size=20)
                    except IOError:
                        font = ImageFont.load_default()  # 폰트 파일을 찾을 수 없으면 기본 폰트 사용

                    # 이름 텍스트를 이미지로 추가
                    draw.text(name_position, name_input, fill="black", font=font)

                    # 날짜 텍스트를 이미지로 추가
                    draw.text(year_position, f"{year}", fill="black", font=font)
                    draw.text(month_position, f"{month}", fill="black", font=font)
                    draw.text(day_position, f"{day}", fill="black", font=font)

                    # 이미지를 저장할 수 있는 버퍼 생성
                    buffer = io.BytesIO()
                    combined_image.save(buffer, format="PNG")
                    buffer.seek(0)
                    # st.success("이미지가 성공적으로 저장되었습니다.")
                    
                    sender_email = "wonchul.no@gmail.com"
                    receiver_email = "ninja0516@naver.com"
                    subject = f"[{today}] {name_input} {contract_name}"
                    body = f"[{today}] {name_input} {contract_name}"

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

                    with st.spinner(f'{contract_name} 생성중 조금만 기다려주세요...'):
                        try:
                            server = smtplib.SMTP('smtp.gmail.com', 587)
                            server.starttls()
                            server.login(sender_email, config["email_passwd"])
                            text = msg.as_string()
                            server.sendmail(sender_email, receiver_email, text)
                            server.quit()
                            st.success(f"{contract_name} 작성이 완료되었습니다. {contract_name}를 다운로드 하시려면 아래의 다운로드 버튼을 눌러주세요")
                        except Exception as e:
                            st.error(f"작성 실패했습니다 담당자에게 문의해주세요.")

                    # 최종 이미지 다운로드 버튼 제공
                    st.download_button(
                        label=f"{contract_name} 다운로드",
                        data=buffer,
                        file_name="signed_with_name_image.png",
                        mime="image/png",
                    )
            else:
                st.warning("서명을 작성하고 작성완료 버튼을 눌러주세요.")
        else:
            st.warning("이름을 작성완료 버튼을 눌러주세요.")


def main():
    if config['contract_visible']:
        resume()
    else:
        st.title(f"SKNs 계약서 작성")
        st.info("계약서 작성 기능은 현재 비활성화 상태입니다. 관리자에게 문의하세요.")



if __name__ == '__main__':
    main()