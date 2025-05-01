import streamlit as st
import imaplib
import email
from email.header import decode_header
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
PORT = 993


def get_imap_host():
    return "".join(chr(c) for c in [105, 109, 97, 112, 46, 102, 105, 114, 115, 116, 109, 97, 105, 108, 46, 108, 116, 100])


def fetch_latest_emails(email_user, email_pass):
    results = []
    try:
        mail = imaplib.IMAP4_SSL(get_imap_host(), PORT)
        mail.login(email_user, email_pass)
        mail.select("inbox")

        status, messages = mail.search(None, "ALL")
        mail_ids = messages[0].split()

        if not mail_ids:
            return ["📭 받은 메일이 없습니다."]

        latest_ids = mail_ids[-5:][::-1]

        for idx, i in enumerate(latest_ids, 1):
            status, msg_data = mail.fetch(i, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    subject = subject.decode(encoding or "utf-8") if isinstance(subject, bytes) else subject
                    from_ = msg.get("From")
                    date_raw = msg.get("Date")

                    try:
                        date_parsed = email.utils.parsedate_to_datetime(date_raw)
                        kst_time = date_parsed.astimezone(KST)
                        date_str = kst_time.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        date_str = date_raw or "알 수 없음"

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() in ["text/plain", "text/html"] and "attachment" not in str(part.get("Content-Disposition")):
                                try:
                                    content = part.get_payload(decode=True)
                                    decoded = content.decode(part.get_content_charset() or "utf-8", errors="replace")
                                    if part.get_content_type() == "text/html":
                                        soup = BeautifulSoup(decoded, "html.parser")
                                        body = soup.get_text()
                                    else:
                                        body = decoded
                                    break
                                except:
                                    pass
                    else:
                        try:
                            content = msg.get_payload(decode=True)
                            decoded = content.decode(msg.get_content_charset() or "utf-8", errors="replace")
                            if msg.get_content_type() == "text/html":
                                soup = BeautifulSoup(decoded, "html.parser")
                                body = soup.get_text()
                            else:
                                body = decoded
                        except:
                            pass

                    code_match = re.search(r"\d{4}", body)
                    code = code_match.group(0) if code_match else "❌ 없음"

                    results.append(f"{idx}. 🗓 {date_str}\n📨 From: {from_}\n📍 제목: {subject}\n🔑 인증코드: {code}\n")

        mail.logout()
        return results

    except Exception as e:
        return [f"❌ 오류 발생: {str(e)}"]


# Streamlit 웹 UI
st.set_page_config(page_title="메일 인증코드 수신기", layout="centered")
st.title("📬 메일 인증코드 수신기")

with st.form("login_form"):
    email_user = st.text_input("이메일 주소")
    email_pass = st.text_input("비밀번호", type="password")
    submitted = st.form_submit_button("📥 메일 확인")

if submitted:
    with st.spinner("메일을 불러오는 중입니다..."):
        results = fetch_latest_emails(email_user, email_pass)
        for item in results:
            st.code(item, language="text")
