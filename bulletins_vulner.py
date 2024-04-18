import requests
from bs4 import BeautifulSoup
import csv
from unidecode import unidecode
import smtplib
from email.mime.text import MIMEText
import re
import os
from dotenv import load_dotenv


def extract_bulletins(url):
    """
    Extract security bulletins from the provided URL.
    """
    base_url = 'https://www.dgssi.gov.ma/fr/bulletins/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    bulletin_list = []

    for bulletin_element in soup.find_all('div', class_='single-blog-content'):
        title = bulletin_element.find('h3').text.replace('\xa0', ' ').strip()
        # Extraire le texte après le dernier espace pour supprimer le numéro
        date = bulletin_element.find('li').text.strip()
        description = bulletin_element.find('p').text.replace('\xa0', ' ').strip()

        title_without_number = title.split('-', 1)[-1].strip()
        title = title_without_number.lower().replace(' ', '-')
        detail_page_url = base_url + title

        bulletin_list.append(
            {'title': title, 'date': date, 'description': description, 'Page_url': detail_page_url})

    return bulletin_list


def filter_bulletins_by_keywords(bulletins_list, keywords):
    """
    Filter bulletins based on provided keywords.
    """
    filtered_bulletins = []
    for bulletin in bulletins_list:
        if any(keyword.lower() in bulletin[field].lower() for field in ['title', 'description'] for keyword in
               keywords):
            filtered_bulletins.append(bulletin)

    return filtered_bulletins


def export_to_csv(data, filename):
    """
    Export bulletin data to a CSV file.
    """
    fieldnames = ['title', 'date', 'description', 'Page_url']
    with open(filename, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def send_email(receiver_email, latest_vulnerability):
    """
    Send email notification for the latest vulnerability.
    """
    load_dotenv()
    sender_email = os.getenv("username_gmail")
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = sender_email
    smtp_password = os.getenv("password_gmail")

    message_text = f"""Une vulnérabilité a été détectée:
    Title: {latest_vulnerability['title']}
    Description: {latest_vulnerability['description']}
    Date: {latest_vulnerability['date']}
    Detail Page Link: {latest_vulnerability['Page_url']}
    """
    message = MIMEText(message_text)
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = 'Vulnérabilité Notification'

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, receiver_email, message.as_string())


def main():
    """
    Main function of the program.
    """
    url = "https://www.dgssi.gov.ma/bulletins-securite"
    bulletins_list = extract_bulletins(url)

    # Filter bulletins based on keywords
    keywords_to_search = ['SCADA', 'ICS', 'Linux', 'Vmware', 'Cisco', 'CISA', 'Siemens', 'ABB', 'Schneider', 'Electric',
                          'PLC', 'OPC', 'MODBUS', 'IHM', 'SNMP', 'DoS', 'SSH', 'UDP', 'NAS']
    filtered_bulletins_list = filter_bulletins_by_keywords(bulletins_list, keywords_to_search)

    if filtered_bulletins_list:
        # Export filtered bulletins to CSV
        export_to_csv(filtered_bulletins_list, 'bulletins.csv')
        print("Exported")

        # Send email notification for the latest vulnerability
        load_dotenv()
        latest_vulnerability = filtered_bulletins_list[0]
        send_email(os.getenv("receiver_email"), latest_vulnerability)
        print("Sent")


if __name__ == "__main__":
    main()
