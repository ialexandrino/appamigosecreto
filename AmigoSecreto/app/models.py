from . import db, bcrypt  
from flask_login import UserMixin
from datetime import datetime


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    groups = db.relationship('Group', backref='creator', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


    members = db.relationship('Participant', back_populates='group', lazy=True, cascade='all, delete-orphan')


class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    drawn_participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=True) 
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    gift_name = db.Column(db.String(255), nullable=True)
    gift_link = db.Column(db.String(500), nullable=True)
    character_name = db.Column(db.String(100), nullable=True)


    drawn_participant = db.relationship('Participant', remote_side=[id], backref='drawn_by')
    

    group = db.relationship('Group', back_populates='members')


    gifts = db.relationship('Gift', back_populates='participant', lazy=True)
  



class Gift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(500)) 
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)

    participant = db.relationship('Participant', back_populates='gifts')




class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    sender_name = db.Column(db.String(100), nullable=False) 
    content = db.Column(db.Text, nullable=False)  
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    group = db.relationship('Group', back_populates='messages')

Group.messages = db.relationship('Message', back_populates='group', lazy=True)


