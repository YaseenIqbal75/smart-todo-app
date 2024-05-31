# Smart ToDo App

This is a smart to-do app that helps users keep track of their daily tasks. It offers the following features:

#### Automatic Task Description Generation
User can automatically generate task descriptions for their tasks using the GPT-2 text generation model, implemented via Hugging Face's transformers library. [Read Docs](https://huggingface.co/docs/transformers/en/index)

#### Custom Reminders
User can set custom reminders for their tasks. By default, reminders are set for 3 hours before 24 hours have passed after creation of the task.The scheduling of the reminders has been implemented using flask-APScheduler library. [Read Docs](https://apscheduler.readthedocs.io/en/3.x/userguide.html)

#### Suitable Alert Messages
The app generates suitable alert messages to provide feedback to the user in case some bad request is sent or the sent data is incomplete.

## Installation

#### Pre-requisites

1. Python (3.6) or higher.
2. pip (Python package installer)

### Create a vitual environment

```bash
python -m venv venv
```
### Activate the virtual environment (Linux)
```bash
source venv/bin/activate
```

### Install project dependencies
```bash
pip install -r requirements.txt
```

### Run the app
```bash
flask run
```
## Features
1. Add task.
2. Update the status of a task.
3. Delete a task.
4. Custom Reminders.
5. Default Reminders.
6. Update the task status through reminders.
7. AI generated description.
8. Informative Alert messages according to situation.

