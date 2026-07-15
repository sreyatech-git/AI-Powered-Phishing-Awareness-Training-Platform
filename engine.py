import smtplib
import csv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_baseline_emails():
    smtp_server = "smtp.gmail.com"  
    port = 587                      
    
    # DETAILS  ===
    sender_email = "sreya00713@gmail.com"  
    sender_password = "okbhdyhfjsehtthc"       
    # ====================================

    try:
        print("Connecting to network server...")
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()  
        server.login(sender_email, sender_password)
        print("Authentication successful! Connection is active.")

        # latin-1 encoding ke sath file open ki
        # Wapas standard format par set kiya
        with open('dataset.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Agar koi line blank hai toh use ignore karo
                if not row:
                    continue
                
                # Column names ko bina kisi crash ke safely clean karna
                clean_row = {}
                for k, v in row.items():
                    if k is not None:
                        clean_row[str(k).strip()] = v if v is not None else ""
                
                # Ab data extract karo bina kisi failure ke
                name = clean_row.get('Name') or clean_row.get('Name ') or "User"
                recipient = clean_row.get('EmailID') or clean_row.get('EmailId') or clean_row.get('Email')
                dept = clean_row.get('Department') or clean_row.get('Departme') or 'Testing'
                
                # Agar email id mili hi nahi us row mein, toh skip karo
                if not recipient or "@" not in str(recipient):
                    print(f"⚠️ Skipping invalid or empty email row for: {name}")
                    continue
                
                # Email Package Assembly
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = str(recipient).strip()
                msg['Subject'] = f"Baseline Connection Test: {dept} Division"
                
                body = f"Hello {name},\n\nThis is a direct automated test message sent programmatically via our Python pipeline script."
                msg.attach(MIMEText(body, 'plain'))
                
                # Mail Dispatch Execution
                server.sendmail(sender_email, str(recipient).strip(), msg.as_string())
                print(f"✔️ Mail delivered to: {name} ({recipient})")
                
        server.quit()
        print("Pipeline execution completed successfully!")

    except Exception as error_log:
        print(f"❌ Error Encountered: {error_log}")

if __name__ == "__main__":
    send_baseline_emails()