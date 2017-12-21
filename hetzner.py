import requests
from requests.auth import HTTPBasicAuth
import logging
import smtplib
import json
import sqlite3
from email.message import EmailMessage
from config import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
fh = logging.FileHandler('info.log')
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


def main():
    r = requests.get('https://robot-ws.your-server.de/order/server_market/product',
        auth=HTTPBasicAuth(robot_username, robot_password))
    result = r.json()
    for x in result:
        cur = x['product']
        total_disk_space_gb = cur['hdd_count'] * cur['hdd_size']
        if ((cur['cpu_benchmark'] < desired_benchmark) or
            (total_disk_space_gb < desired_space_gb) or
            (float(cur['price']) > desired_price_euros)):
            continue
        out = (
            cur['id'],
            cur['price'],
            cur['cpu_benchmark'],
            cur['next_reduce'],
            total_disk_space_gb / 1024
            )
        send_email(cur)
    logger.info("No servers found matching search criteria")


def send_email(obj):
    if already_sent(obj['id']):
        return
    with smtplib.SMTP_SSL(smtp_address) as s:
        s.login(smtp_username, smtp_password)
        msg = EmailMessage()
        url = 'https://robot.your-server.de/order/marketConfirm/{0}/culture/en_GB/country/US'.format(obj['id'])
        msg.set_content(url + "\n\n" + json.dumps(obj, indent=2))
        msg['Subject'] = 'Server meets price criteria'
        msg['From'] = email_address
        msg['To'] = email_address
        print(msg)
        s.send_message(msg)
        logger.info("Email sent")
        logger.info(json.dumps(obj, indent=2))


def already_sent(id):
    with sqlite3.connect('storage.db3') as conn:
        c = conn.cursor()
        sql = "CREATE TABLE IF NOT EXISTS ids (id INTEGER PRIMARY KEY)"
        c.execute(sql)
        sql = "SELECT id FROM ids WHERE id=?"
        c.execute(sql, (id,))
        res = c.fetchall()
        print(res)
        if res:
            return True
        else:
            sql = "INSERT INTO ids (id) VALUES (?)"
            c.execute(sql, (id,))
            conn.commit()
            return False


main()
