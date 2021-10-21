from smtplib import SMTP as SMTP       # this invokes the secure SMTP protocol (port 465, uses SSL)
# from smtplib import SMTP                  # use this for standard SMTP protocol   (port 25, no encryption)
from email.mime.text import MIMEText

# old version
# from email.MIMEText import MIMEText

from main import config

import os
import ssl

def send_mail(receiver, subject, content, text_subtype = 'plain'):
    # print(f"send email to {receiver}")

    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    msg = MIMEText(content, text_subtype)
    msg['Subject']= subject
    msg['From']   = config.site.email.sender # some SMTP servers will do this automatically, not all

    conn = SMTP(config.site.email.host, port=config.site.email.port)
    conn.ehlo()
    conn.starttls(context=context)
    conn.ehlo()
    conn.set_debuglevel(False)
    # print(f"try login")
    conn.login(config.site.email.sender, os.environ['SMTP_PASSWORD'])
    # print(f"try send")
    try:
        conn.sendmail(config.site.email.sender, [receiver], msg.as_string())
    finally:
        conn.quit()
