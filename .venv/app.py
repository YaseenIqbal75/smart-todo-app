# all necessary imports
from flask import Flask,render_template,request,url_for,redirect,flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime as dt
from transformers import pipeline
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask_socketio import SocketIO


# initialize the SQLalchemy object
db = SQLAlchemy()

# name of the database
db_name = "todo.db" 

# initializing the app
app = Flask(__name__)

# persistant job store using sqlite database
job_store = { 
    'default' :SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")
    }

# initializing scheduler for alert messages
scheduler = BackgroundScheduler(jobstores = job_store)

scheduler.start()

# app secret key for session it can be anything
app.secret_key = "arslanwaqar421"

# socketio object for enabling the cross communication between server and client
socketio = SocketIO(app, cors_allowed_origins="*")


# flask app db configurations and initalization
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db.init_app(app)    


# Creating a class to map to the database table named "Task"
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    Ending_Timestamp = db.Column(db.DateTime)
    isComplete= db.Column(db.Boolean, default=False)
    Creation_Timestamp = db.Column(db.DateTime)



    def __init__(self, title, description, creation_timestamp, ending_timestamp ,flag=False):
        self.title = title
        self.description = description
        self.isComplete = flag
        self.Creation_Timestamp = creation_timestamp
        self.Ending_Timestamp = ending_timestamp


    def __repr__(self):
        return f"Task( '{self.id}','{self.title}', '{self.description}', '{self.Creation_Timestamp}' ,'{self.Ending_Timestamp}', '{self.isComplete}')"



# function to send alert to the client with the necessary data
def send_alert(task_title,task_id,task_status):
    with app.app_context():
        socketio.emit("alert", {"task_title" : task_title,
                                "task_id" : task_id,
                                "task_status" : task_status})

# function to schedule the task alert currently
def schedule_task_alert(task_title, alert_time):
    task = Task.query.order_by(Task.Creation_Timestamp.desc()).first()
    scheduler.add_job(func=send_alert, trigger='date', run_date = alert_time, args=[task_title,task.id,task.isComplete])
    scheduler.print_jobs()

# socket decorator to see if the sever and client are connected successfuly
@socketio.on('my_event')
def handle_message(data):
    print('Connected '+ data['data'])

# route for homepage that displays all the tasks
@app.route('/')
def home_page():
    todo_list = Task.query.all()
    scheduler.print_jobs()
    return render_template("base.html" ,todo_list = todo_list)

@app.route('/updatelist')
def updated_list():
    return render_template('list.html', todo_list = Task.query.all())

# route for adding the new task, POST request from the client is handled here
@app.route("/add", methods =["POST"])
def add():
    title = request.form.get("Title")
    description = request.form.get("Description")
    reminder = request.form.get('Reminder')

    if not title:
        return jsonify({"success": False, "redirect": url_for("home_page"), "message": "Title cannot be empty"}), 400
    else:
        current_time = dt.datetime.now()
        # by default the ending time is set to 24 hours after the task has been created
        ending_time = current_time + dt.timedelta(hours=24)
        new_task = Task(title,description,current_time,ending_time)
        db.session.add(new_task)
        # by default the reminder appears 3 hour before the dead line
        if reminder:
            # convert to python datetime object
            alert_time = dt.datetime.strptime(reminder, '%Y-%m-%dT%H:%M')
            # verify alert time if its valid or not
            if alert_time > current_time:
                # set custom remider if the alert_time is valid
                db.session.commit()
                schedule_task_alert(title,alert_time)
            else:
                return jsonify({"success": False, "redirect": url_for("home_page"), "message": "Invalid Reminder Time"}), 400

        else:
            db.session.commit()
            # if the reminder not given then default reminder is generated 3 hours before the deadline
            alert_time = ending_time - dt.timedelta(hours=3)
            schedule_task_alert(title,alert_time)
    redirect = render_template('list.html' , todo_list = Task.query.all())
    return jsonify({"success": True, "redirect": redirect, "message": "Task Added successfully"})

# update the task status to done or not done
@app.route("/update/<int:task_id>")
def update(task_id):
    update_task = Task.query.filter_by(id=task_id).first()
    update_task.isComplete =  not update_task.isComplete   
    db.session.commit()
    return redirect(url_for("home_page"))

# delete a specific task
@app.route("/delete/<int:task_id>")
def delete(task_id):
    delete_task = Task.query.filter_by(id = task_id).first()
    db.session.delete(delete_task)
    db.session.commit()
    return render_template("list.html", todo_list = Task.query.all())

# generate AI description through AI model gpt2 using the transformers library
@app.route("/generate_description")
def generate_description():
    title = request.args.get('title')
    print("Title is ===> " , title)
    if not title:
        return jsonify({"description" : "Title cannot be empty to generate AI description."}), 400
    generator = pipeline("text-generation", model="gpt2")
    prompt = f"Write a task description for the Task: '{title}'"
    ai_response = generator(prompt, num_return_sequences = 1, max_length=90)
    return jsonify({"description" :ai_response[0]['generated_text']}) , 200

@app.route("/update_reminder/<int:id>")
def update_from_reminder(id):
    update_task = Task.query.filter_by(id=id).first()
    update_task.isComplete =  not update_task.isComplete
    status = update_task.isComplete
    db.session.commit()
    return render_template('list.html' , todo_list = Task.query.all())


# Ensure the scheduler shuts down when the app exits
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":  
    with app.app_context():
        db.create_all() 
    socketio.run(app, debug= True)
