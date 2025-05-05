from setuptools import setup, find_packages

setup(
    name="flask-inventory",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "Flask==3.0.0",
        "pymongo==4.6.1",
        "Werkzeug==3.0.1",
        "python-dotenv==1.0.0",
        "gunicorn==21.2.0",
        "pymongo[srv]",
    ],
) 