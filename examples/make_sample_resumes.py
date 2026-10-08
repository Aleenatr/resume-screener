"""Create the five sample resume PDFs in examples/resumes/.

The people are fictional - names, emails (example.com) and phone numbers are
made up - so the demo can show real PDF parsing without anyone's real data.

Run:  python examples/make_sample_resumes.py
"""
from pathlib import Path

import pymupdf

OUT = Path(__file__).resolve().parent / "resumes"

RESUMES = {
    "ananya_rao.pdf": ("Ananya Rao", """\
ananya.rao@example.com | +91 90000 00001 | linkedin.com/in/ananya-rao-example | github.com/ananya-example

SUMMARY
Backend developer who builds REST APIs in Python. 1 year of internship experience with Django and PostgreSQL.

EDUCATION
B.Tech in Computer Science and Engineering, 2021 - 2025, CGPA: 8.6/10

EXPERIENCE
Backend Developer Intern, a fintech startup (2024 - 2025)
- Built REST APIs with Django and Django REST Framework for a payments dashboard.
- Designed PostgreSQL tables and wrote SQL queries that cut report load time in half.
- Packaged services with Docker and deployed them on AWS EC2.
- Wrote unit tests with pytest and reviewed pull requests on GitHub.

PROJECTS
Library API: a Flask service with JWT login, PostgreSQL storage and Docker deployment.

SKILLS
Python, Django, Flask, SQL, PostgreSQL, Docker, AWS, Git, Linux

CERTIFICATIONS
AWS Certified Cloud Practitioner (2024)
"""),
    "karan_mehta.pdf": ("Karan Mehta", """\
karan.mehta@example.com | +91 90000 00002 | linkedin.com/in/karan-mehta-example

SUMMARY
Java developer with 3 years of experience building enterprise web applications.

EDUCATION
B.E. in Information Technology, 2018 - 2022, CGPA: 7.9/10

EXPERIENCE
Software Engineer, an IT services company (2022 - present)
- Developed REST APIs with Java, Spring Boot and Hibernate for an insurance client.
- Wrote JUnit tests and maintained Maven builds and Jenkins pipelines.
- Tuned MySQL queries and indexes for the claims module.

SKILLS
Core Java, Spring Boot, Spring MVC, Hibernate, MySQL, JUnit, Maven, Git, Jenkins

CERTIFICATIONS
Oracle Certified Professional, Java SE 11 Developer
"""),
    "sneha_iyer.pdf": ("Sneha Iyer", """\
sneha.iyer@example.com | +91 90000 00003 | github.com/sneha-example

SUMMARY
Data scientist with 2 years of experience turning messy data into predictive models.

EDUCATION
M.Sc in Statistics, 2021 - 2023, CGPA: 8.9/10
B.Sc in Mathematics, 2018 - 2021

EXPERIENCE
Data Scientist, a retail analytics firm (2023 - present)
- Built churn prediction models with scikit-learn and XGBoost on two million customer records.
- Created demand forecasting dashboards in Tableau for the supply team.
- Wrote Python and SQL pipelines to clean and join sales data.

SKILLS
Python, pandas, NumPy, scikit-learn, TensorFlow, SQL, Tableau, Statistics, Machine Learning

CERTIFICATIONS
TensorFlow Developer Certificate
"""),
    "rohan_das.pdf": ("Rohan Das", """\
rohan.das@example.com | +91 90000 00004

SUMMARY
QA automation engineer with 4 years of experience testing web and mobile apps.

EDUCATION
BCA, 2017 - 2020

EXPERIENCE
Senior Test Engineer, a product company (2020 - present)
- Built a Selenium WebDriver framework in Java with TestNG and the Page Object Model.
- Automated API tests with Postman and REST Assured, run nightly in Jenkins.
- Logged and tracked defects in JIRA and joined daily Agile stand-ups.

SKILLS
Selenium, TestNG, Java, Postman, JIRA, SQL, Jenkins, Agile

CERTIFICATIONS
ISTQB Certified Tester Foundation Level
"""),
    "meera_nair.pdf": ("Meera Nair", """\
meera.nair@example.com | +91 90000 00005

SUMMARY
HR executive with 5 years of experience in recruitment and employee engagement.

EDUCATION
MBA in Human Resources, 2014 - 2016

EXPERIENCE
HR Executive, a manufacturing company (2016 - present)
- Ran end-to-end recruitment for 200+ roles: sourcing, screening and interview scheduling.
- Managed onboarding, payroll inputs and attendance records for 600 employees.
- Organised engagement programmes that reduced first-year attrition.

SKILLS
Recruitment, Payroll, Onboarding, Employee Engagement, MS Excel, HRMS

CERTIFICATIONS
Certified HR Analytics Professional
"""),
}


def make_pdf(path, name, body):
    pdf = pymupdf.open()
    page = pdf.new_page()  # A4-ish default page
    page.insert_text((50, 60), name, fontsize=18, fontname="hebo")  # Helvetica Bold
    page.insert_textbox(pymupdf.Rect(50, 75, 545, 800), body, fontsize=10, fontname="helv")
    pdf.save(path)


def main():
    OUT.mkdir(exist_ok=True)
    for filename, (name, body) in RESUMES.items():
        make_pdf(OUT / filename, name, body)
        print("wrote", OUT / filename)


if __name__ == "__main__":
    main()
