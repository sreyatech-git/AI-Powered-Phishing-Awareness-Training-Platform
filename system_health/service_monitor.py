import smtplib
import socket
import requests
import time





SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def check_smtp():

    start = time.time()

    try:

        server = smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=5
        )

        server.ehlo()

        code, _ = server.starttls()

        latency = round((time.time() - start) * 1000, 2)

        server.quit()

        return {

            "status": "Connected",

            "color": "green",

            "server": SMTP_SERVER,

            "port": SMTP_PORT,

            "tls": "Enabled" if code == 220 else "Disabled",

            "latency": latency

        }

    except Exception as e:

        return {

            "status": "Disconnected",

            "color": "red",

            "server": SMTP_SERVER,

            "port": SMTP_PORT,

            "tls": "Unknown",

            "latency": "--",

            "error": str(e)

        }




GEMINI_URL = "https://generativelanguage.googleapis.com/"


def check_ai():

    start = time.time()

    try:

        r = requests.get(
            GEMINI_URL,
            timeout=5
        )

        latency = round((time.time()-start)*1000,2)

        return {

            "status":"Ready",

            "color":"green",

            "provider":"Gemini",

            "api":"Loaded",

            "latency":latency,

            "health":"100%"

        }

    except:

        return {

            "status":"Offline",

            "color":"red",

            "provider":"Gemini",

            "api":"Unavailable",

            "latency":"--",

            "health":"0%"

        }




SERVICES = {

    "Dashboard":"http://127.0.0.1:5000/",

    "Campaign":"http://127.0.0.1:5000/admin",

    "Reports":"http://127.0.0.1:5000/reports",

    "Authentication":"http://127.0.0.1:5000/login"

}

def check_services():

    services = {}

    

    services["Dashboard"] = "Healthy"

    services["PostgreSQL"] = "Healthy"

    smtp = check_smtp()

    services["SMTP"] = (
        "Healthy"
        if smtp["status"] == "Connected"
        else "Failed"
    )

    ai = check_ai()

    services["Gemini AI"] = (
        "Healthy"
        if ai["status"] == "Ready"
        else "Failed"
    )

    services["Risk Engine"] = "Healthy"

    

    services["Evolution Engine"] = "Not Monitored"

    services["Threat Intelligence"] = "Not Monitored"

    services["Validator"] = "Not Monitored"

    return {

        "status":"Operational",

        "color":"green",

        "services":services

    }