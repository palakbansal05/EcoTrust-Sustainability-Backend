# File: app.py
from flask import Flask, request, jsonify
from scraper import get_certifications_from_website, calculate_score
from urllib.parse import urlparse
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def extract_company_name(url):
    domain = urlparse(url).netloc.replace("www.", "")
    return domain.split('.')[0].lower()

@app.route('/check_certifications', methods=['POST'])
def check_certifications():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400

    website_url = data['url']
    company_name = extract_company_name(website_url)

    print(f"\n🔎 Scraping website: {website_url}")
    cert_list = get_certifications_from_website(website_url)
    print(f"✅ Found certifications: {cert_list}")

    score = calculate_score(cert_list, company_name)
    print(f"🏆 Sustainability Score for {company_name}: {score}")

    return jsonify({
        'url': website_url,
        'certifications': cert_list,
        'sustainability_score': score
    })

if __name__ == '__main__':
    app.run(debug=True)
