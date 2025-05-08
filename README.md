
## Installation

Clone the repository:

```bash
git clone https://github.com/Sugaam0/JobMania-JobPortal

````
Install Dependencies: (remove versions from requirements.txt) is any error occurs)

````bash
pip install -r requirements.txt
````
Setup email in settings.py write your own email and app password

Migrate the database
```bash
py manage.py makemigrations
py manage.py migrate
```
Run the server
```
py manage.py runserver

