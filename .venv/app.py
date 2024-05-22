from flask import Flask,render_template,request,url_for,redirect,flash # import Flask class from flask module
from flask_sqlalchemy import SQLAlchemy #SQLAlchemy #import SQLAlchemy class from flasl-sqlalchemy module
from sqlalchemy.sql import text # import text form sql
import datetime as dt
#initialize the SQLalchemy object
db = SQLAlchemy()

# name of the database
db_name = "todo.db" 

#initializing the app
app = Flask(__name__)

app.secret_key = "arslanwaqar421"

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
        return f"Task('{self.title}', '{self.description}', '{self.deadline}', '{self.flag}')"


    

@app.route('/')
def home_page():
    todo_list = Task.query.all()
    return render_template("base.html" ,todo_list = todo_list)

@app.route("/add", methods =["POST"])
def add():
    title = request.form.get("Title")
    description = request.form.get("Description")
    if not title:
        flash("Title cannot be empty", "error")
        return redirect(url_for("home_page"))
    
    current_time = dt.datetime.now()
    new_task = Task(title,description,current_time,current_time + dt.timedelta(days=1) )
    db.session.add(new_task)
    db.session.commit()
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



if __name__ == "__main__":  
    with app.app_context():
        db.create_all() 
    app.run(debug=True)
    

