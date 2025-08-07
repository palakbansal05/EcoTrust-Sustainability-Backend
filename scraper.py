import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy import signals
from scrapy.signalmanager import dispatcher
from urllib.parse import urlparse
import re
import pandas as pd

KNOWN_CERTIFICATIONS = [
    "ISO 9001", "ISO 14001", "ISO 45001", "ISO 27001",
    "B Corp", "LEED Gold", "LEED Silver", "LEED Platinum",
    "Fair Trade", "Energy Star", "Carbon Trust", "SA8000",
    "FSC", "GOTS", "CE Mark", "RoHS", "Green Seal",
    "EPEAT", "Cradle to Cradle", "EU ECOLABEL","USDA","HALAL Certificate",
    "OEKO TEX 100","ISO 45001","SEDEX"
]

strict_cert_pattern = re.compile(
    r'\b(?:' + '|'.join(re.escape(cert) for cert in KNOWN_CERTIFICATIONS) + r')\b',
    re.IGNORECASE
)

# ---- SCRAPY SPIDER ----
class CertificationSpider(scrapy.Spider):
    name = "certification_spider"

    def _init_(self, start_url, *args, **kwargs):
        super()._init_(*args, **kwargs)
        self.start_urls = [start_url]
        parsed = urlparse(start_url)
        self.allowed_domains = [parsed.netloc]
        self.found_certifications = set()
        self.visited_urls = set()

    def parse(self, response):
        self.visited_urls.add(response.url)

        if any(kw in response.url.lower() for kw in [
            "certification", "sustainability", "iso", "compliance", "green", "about", "awards"
        ]):
            texts = response.css("p, li, h1, h2, h3, span, div::text").getall()
            for text in texts:
                matches = strict_cert_pattern.findall(text)
                for match in matches:
                    self.found_certifications.add(match.strip())

        for href in response.css("a::attr(href)").getall():
            next_url = response.urljoin(href)
            if urlparse(next_url).netloc == urlparse(response.url).netloc and next_url not in self.visited_urls:
                self.visited_urls.add(next_url)
                yield scrapy.Request(url=next_url, callback=self.parse)

# ---- RUN SPIDER AND RETURN LIST ----
def get_certifications_from_website(start_url):
    certifications = []

    def collect_results(spider):
        certifications.extend(sorted(spider.found_certifications))

    dispatcher.connect(collect_results, signal=signals.spider_closed)

    process = CrawlerProcess(settings={"LOG_LEVEL": "ERROR"})
    process.crawl(CertificationSpider, start_url=start_url)
    process.start()

    return certifications

# ---- SCORE CALCULATION FUNCTION ----
def calculate_score(cert_list, company, cert_db_path='certifications.csv'):
    try:
        df = pd.read_csv(cert_db_path)
    except FileNotFoundError:
        print("Certification database not found.")
        return 0

    df = df.dropna(subset=['Certificate', 'Company'])
    company = company.lower().strip()
    cert_list = [cert.lower().strip() for cert in cert_list]

    score = 0
    for _, row in df.iterrows():
        cert_name = str(row['Certificate']).lower().strip()
        cert_company = str(row['Company']).lower().strip()

        if cert_name in cert_list and cert_company == company:
            score += 5

    return score