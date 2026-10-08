"""The skills vocabulary, used for the `skills` field and for the
"matched / missing skills" shown next to every score.

Each entry maps the name we display to the spellings we search for.
Matching is whole-word, so "java" does not fire inside "javascript" and
"sql" does not fire inside "mysql".

Single-letter languages (C, R) are left out on purpose: a lone "C" also
appears in grades, initials and "Grade C", so it would cause more wrong hits
than right ones. "Go" is only matched as "golang" for the same reason.
"""
import re

SKILLS = {
    # Programming languages
    "Python": ["python"],
    "Java": ["java", "core java"],
    "JavaScript": ["javascript", "java script"],
    "TypeScript": ["typescript"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "c sharp"],
    "Go": ["golang"],
    "Scala": ["scala"],
    "Kotlin": ["kotlin"],
    "Swift": ["swift"],
    "PHP": ["php"],
    "Solidity": ["solidity"],
    "Shell scripting": ["shell scripting", "shell script", "bash", "unix shell"],
    # Web
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3"],
    "jQuery": ["jquery"],
    "Bootstrap": ["bootstrap"],
    "React": ["react", "reactjs", "react.js"],
    "Angular": ["angular", "angularjs"],
    "Node.js": ["node.js", "nodejs", "node js"],
    "WordPress": ["wordpress"],
    "REST APIs": ["rest api", "rest apis", "restful", "web api", "web apis"],
    # Backend frameworks
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi"],
    "Spring Boot": ["spring boot"],
    "Spring": ["spring mvc", "spring framework", "spring"],
    "Hibernate": ["hibernate", "jpa"],
    "J2EE": ["j2ee", "servlets", "servlet", "jsp"],
    ".NET": [".net", "asp.net", "dotnet", ".net core"],
    "Entity Framework": ["entity framework"],
    "LINQ": ["linq"],
    # Data science and machine learning
    "Machine Learning": ["machine learning"],
    "Deep Learning": ["deep learning", "neural network", "neural networks"],
    "NLP": ["nlp", "natural language processing"],
    "Computer Vision": ["computer vision", "opencv", "open cv"],
    "pandas": ["pandas"],
    "NumPy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "Keras": ["keras"],
    "Statistics": ["statistics", "statistical"],
    "Matplotlib": ["matplotlib"],
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi"],
    "Excel": ["excel", "ms excel", "advanced excel"],
    # Databases
    "SQL": ["sql"],
    "MySQL": ["mysql"],
    "PostgreSQL": ["postgresql", "postgres"],
    "Oracle": ["oracle"],
    "SQL Server": ["sql server", "mssql", "ms sql"],
    "PL/SQL": ["pl/sql", "plsql"],
    "MongoDB": ["mongodb", "mongo db"],
    "Cassandra": ["cassandra"],
    "Redis": ["redis"],
    "Teradata": ["teradata"],
    # Big data
    "Hadoop": ["hadoop", "hdfs", "mapreduce", "map reduce"],
    "Hive": ["hive"],
    "Pig": ["pig"],
    "Sqoop": ["sqoop"],
    "HBase": ["hbase"],
    "Spark": ["spark", "pyspark"],
    "Kafka": ["kafka"],
    # ETL and data warehousing
    "Informatica": ["informatica"],
    "SSIS": ["ssis"],
    "Talend": ["talend"],
    "Data Warehousing": ["data warehouse", "data warehousing"],
    # Cloud and DevOps
    "AWS": ["aws", "amazon web services", "ec2"],
    "Azure": ["azure"],
    "GCP": ["gcp", "google cloud"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Jenkins": ["jenkins"],
    "Ansible": ["ansible"],
    "Terraform": ["terraform"],
    "Git": ["git", "github", "gitlab", "bitbucket"],
    "Linux": ["linux", "unix", "ubuntu", "rhel", "centos"],
    "CI/CD": ["ci/cd", "continuous integration", "continuous delivery"],
    "Maven": ["maven"],
    # Testing
    "Selenium": ["selenium", "webdriver"],
    "TestNG": ["testng"],
    "JUnit": ["junit"],
    "Cucumber": ["cucumber", "bdd"],
    "Manual Testing": ["manual testing", "functional testing", "regression testing"],
    "JIRA": ["jira"],
    "Postman": ["postman"],
    # Networking and security
    "Networking": ["tcp/ip", "routing", "switching", "vlan", "ospf", "bgp"],
    "Firewalls": ["firewall", "firewalls"],
    "CCNA/CCNP": ["ccna", "ccnp"],
    # Enterprise software
    "SAP": ["sap"],
    "ABAP": ["abap"],
    "SAP HANA": ["hana", "s/4hana"],
    # Engineering tools
    "AutoCAD": ["autocad", "auto cad"],
    "SolidWorks": ["solidworks", "solid works"],
    "CATIA": ["catia"],
    "STAAD Pro": ["staad pro", "staad.pro", "staad"],
    "PLC/SCADA": ["plc", "scada"],
    "MATLAB": ["matlab"],
    # Blockchain
    "Blockchain": ["blockchain", "hyperledger"],
    "Ethereum": ["ethereum", "web3"],
    # Business, project and people skills
    "Agile": ["agile", "scrum"],
    "MS Project": ["ms project", "microsoft project"],
    "Project Management": ["project management", "pmp", "prince2"],
    "CRM": ["crm", "salesforce"],
    "Recruitment": ["recruitment", "talent acquisition"],
    "Payroll": ["payroll"],
    "Photoshop": ["photoshop"],
    "Illustrator": ["illustrator"],
}


def _whole_word(alias):
    # A plain \b doesn't work for skills that end in a symbol ("c++", "c#"),
    # so "whole word" is spelled out: no letter, digit, + or # on either side.
    return re.compile(r"(?<![a-z0-9+#])" + re.escape(alias) + r"(?![a-z0-9+#])")


_PATTERNS = {name: [_whole_word(alias) for alias in aliases] for name, aliases in SKILLS.items()}

# Someone who lists a SQL database knows SQL, even if "SQL" never appears on its own.
IMPLIES = {"MySQL": "SQL", "PostgreSQL": "SQL", "SQL Server": "SQL", "PL/SQL": "SQL"}


def find_skills(text):
    """Every vocabulary skill mentioned (or implied) in the text, in vocabulary order."""
    text = text.lower()
    found = {name for name, patterns in _PATTERNS.items() if any(p.search(text) for p in patterns)}
    found |= {implied for skill, implied in IMPLIES.items() if skill in found}
    return [name for name in SKILLS if name in found]
