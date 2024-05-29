from flask import Flask,render_template,request,url_for,redirect,flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime as dt
from transformers import pipeline
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask_socketio import SocketIO




#initialize the SQLalchemy object
db = SQLAlchemy()

# name of the database
db_name = "todo.db" 

#initializing the app
app = Flask(__name__)

job_store = { 
    'default' :SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")
    }
scheduler = BackgroundScheduler(jobstores = job_store)

scheduler.start()

app.secret_key = "arslanwaqar421"

socketio = SocketIO(app, cors_allowed_origins="*")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db.init_app(app)    

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Added autoincrement=True
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




def send_alert(task_title):
    with app.app_context():
        print('alert sent to client')
        task = Task.query.order_by(Task.Creation_Timestamp.desc()).first()
        socketio.emit("alert", {"task_title" : task_title,
                                "task_id" : task.id,
                                "task_status" : task.isComplete})

def schedule_task_alert(task_title, alert_time):
    scheduler.add_job(func=send_alert, trigger='date', run_date = alert_time, args=[task_title])
    print("Alert added successfully")
    scheduler.print_jobs()

@socketio.on('my_event')
def handle_message(data):
    print('Connected '+ data['data'])

@app.route('/')
def home_page():
    todo_list = Task.query.all()
    scheduler.print_jobs()
    return render_template("base.html" ,todo_list = todo_list)

@app.route("/add", methods =["POST"])
def add():
    title = request.form.get("Title")
    description = request.form.get("Description")
    reminder = request.form.get('Reminder')
    print("Reminder from form :", reminder)
    if not title:
        flash("Title cannot be empty", "error")
        return redirect(url_for("home_page"))
    current_time = dt.datetime.now()
    ending_time = current_time + dt.timedelta(hours=1, seconds=15)
    new_task = Task(title,description,current_time,ending_time)
    db.session.add(new_task)
    db.session.commit()
    if reminder:
        #convert to python datetime object
        alert_time = dt.datetime.strptime(reminder, '%Y-%m-%dT%H:%M')
        # verify alert time if its valid or not
        if alert_time > current_time and alert_time < ending_time:
            schedule_task_alert(title,alert_time)
            print("Custom alert time : " , alert_time)
        else:
            flash("Invalid Reminder Time")
            return redirect(url_for("home_page"))

    else:
        alert_time = ending_time - dt.timedelta(hours=1)
        schedule_task_alert(title,alert_time)

    flash("Task Added Successfully!")
    return redirect(url_for("home_page"))

@app.route("/update/<int:task_id>")
def update(task_id):
    update_task = Task.query.filter_by(id=task_id).first()
    update_task.isComplete =  not update_task.isComplete   
    db.session.commit()
    return redirect(url_for("home_page"))


@app.route("/delete/<int:task_id>")
def delete(task_id):
    delete_task = Task.query.filter_by(id = task_id).first()
    db.session.delete(delete_task)
    db.session.commit()
    return redirect(url_for("home_page"))


@app.route("/generate_description")
def generate_description():
    title = request.args.get('title')
    print("Title is ===> " , title)
    if not title:
        return jsonify({"description" : "title is Empty"}), 400
    generator = pipeline("text-generation", model="gpt2")
    prompt = f"Write a task description for the Task: '{title}'"
    ai_response = generator(prompt, num_return_sequences = 1, max_length=90)
    print(ai_response)
    return jsonify({"description" :ai_response[0]['generated_text']}) , 200


# Ensure the scheduler shuts down when the app exits
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":  
    with app.app_context():
        db.create_all() 
    socketio.run(app, debug= True)
