#!/usr/bin/python

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

gmail_user = "MorganStanley.SecretSanta@gmail.com"
gmail_pwd = "coxsimcoxsim"

def send(recipients, subject, body_plain = "", body_html = "", sender = ""):
	if body_plain and body_html:
		msg = MIMEMultipart('alternative')
		msg.attach(MIMEText(body_plain, 'plain'))
		msg.attach(MIMEText(body_html, 'html'))
	elif body_html:
		msg = MIMEText(body_html, 'html')
	else:
		msg = MIMEText(body_plain, 'plain')
	
	# me == the sender's email address
	# you == the recipient's email address
	msg['Subject'] = subject
	msg['From'] = sender
	msg['To'] = ";".join(recipients)

	# Send the message via our own SMTP server, but don't include the
	# envelope header.
	server = smtplib.SMTP('smtp.gmail.com:587')
	server.ehlo()
	server.starttls()
	server.login(gmail_user, gmail_pwd)
	server.sendmail(sender, recipients, msg.as_string())
	server.quit()

if __name__ == "__main__":
	send(["simon.cox@gmail.com"], 
	     "test subject", 
	     body_plain = "test",
	     body_html = """
<h1>Header</h1>
<p>Paragraph 1</p>
<p>Paragraph 2</p>
""")