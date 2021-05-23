from flask import Flask, render_template
from flask import Blueprint, request
from flask.templating import render_template
from flask_restplus import Api, Resource, fields
import mysql.connector
import datetime
from functools import wraps
from collections import OrderedDict


db = mysql.connector.connect(
  host="localhost",
  user="shashank",
  password="shashu2000",
  database="mysql",
  auth_plugin='mysql_native_password'
)

authorizations =  {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}


api_main = Flask(__name__)
api = Api(api_main, version='1.0', title='TodoMVC API',
    description='A simple TodoMVC API',
    authorizations= authorizations
)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        token = None

        if 'X-API-KEY' in request.headers:
            token = request.headers['X-API-KEY']

        if not token:
            return {'message' : 'Token is missing.'}, 401

        if token != 'token':
            return {'message' : 'Your token is wrong!!!'}, 401

        print('TOKEN: {}'.format(token))
        return f(*args, **kwargs)

    return decorated            

ns = api.namespace('todos', description='TODO operations')

todo = api.model('Todo', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details'),
    'dueby': fields.Date(required=True, description='The task due date'),
    'status': fields.String(required=True, description='The status of the task')
})



class TodoDAO(object):
    def __init__(self):
        self.counter = 0
    #Lists All Records in DB
    def list_all(self):
        cursor = db.cursor()
        query = 'SELECT * FROM List_tasks'
        cursor.execute(query)
        records = cursor.fetchall()
        if len(records) == 0:
            api.abort(404, "No Todo exists".format(id))
        else:
            content = [];
            for record in records:
                content.append({
                    'id': record[0], 
                    'task':record[1], 
                    'dueby':record[2].strftime('%Y-%m-%d'), 
                    'status': record[3]
                })
            return content

    #Creating a new Record
    def create(self, data):
        task = data['task'];due_by = data['due_by'];status = data['status']
        self.counter += 1
        cursor = db.cursor()
        query = 'INSERT INTO List_tasks VALUES (%s, %s, %s, %s)'
        values =  (self.counter, task, due_by, status)
        cursor.execute(query, values)
        db.commit()

    #Getting a Record based on ID
    def get(self, id):
        cursor = db.cursor()
        query = 'SELECT * FROM List_tasks WHERE id = %s'
        values = (id,)
        cursor.execute(query, values)
        records = cursor.fetchall()
        if len(records) == 0:
            api.abort(404, "Todo {} doesn't exist".format(id))
        else:
            return {
                'id': records[0][0], 
                'task':records[0][1], 
                'dueby':records[0][2].strftime('%Y-%m-%d'), 
                'status':records[0][3]
            }
            
    #Deleting a record based on ID
    def delete(self, id):
        cursor = db.cursor()
        query = 'DELETE FROM List_tasks WHERE id = %s'
        values = (id,)
        cursor.execute(query, values)
        db.commit()
        if cursor.rowcount == 0:
            api.abort(404, "Todo {} doesn't exist".format(id))
    
    
    #Finding the records which are due
    def get_dues(self, due_by):
        cursor = db.cursor()
        query = 'SELECT * FROM List_tasks WHERE due_by = %s AND status != %s'
        values = (due_by, "Finished")
        cursor.execute(query, values)
        records = cursor.fetchall()
        if len(records) == 0:
            api.abort(404, "No overdue")
        else:
            content = [];
            for record in records:
                content.append({
                    'id': record[0], 
                    'task':record[1], 
                    'dueby':record[2].strftime('%Y-%m-%d'), 
                    'status': record[3]
                })
            return content

    #Finding All records which are Overdue with respect to the current date
    def get_over_dues(self):
        curdate = datetime.datetime.now().strftime('%Y-%m-%d')
        cursor = db.cursor()
        query = 'SELECT * FROM List_tasks WHERE due_by < %s AND status != %s'
        values = (curdate, "Finished")
        cursor.execute(query, values)
        records = cursor.fetchall()
        if len(records) == 0:
            api.abort(404, "No get_over_dues")
        else:
            content = [];
            for record in records:
                content.append({
                    'id': record[0], 
                    'task':record[1], 
                    'dueby':record[2].strftime('%Y-%m-%d'), 
                    'status': record[3]
                })
            return content
    
    #Finding all the Tasks which are Done
    def get_finished(self):
        cursor = db.cursor()
        query = 'SELECT * FROM List_tasks WHERE status = %s'
        values = ("Finished",)
        cursor.execute(query, values)
        records = cursor.fetchall()
        if len(records) == 0:
            api.abort(404, "No Todo exists")
        else:
            content = [];
            for record in records:
                content.append({
                    'id': record[0], 
                    'task':record[1], 
                    'dueby':record[2].strftime('%Y-%m-%d'), 
                    'status': record[3]
                })
            return content
    
    #Updating the Status of a task Given ID and data 
    def update(self, id, status):
        cursor = db.cursor()
        query = 'UPDATE List_tasks SET status = %s WHERE id = %s'
        values = (status, id)
        cursor.execute(query, values)
        db.commit()
        if cursor.rowcount == 0:
            api.abort(404, "Todo {} doesn't exist".format(id))


DAO = TodoDAO()


@ns.route('/')
class TodoList(Resource):
    '''Shows a list of all List_tasks, and lets you POST to add new tasks'''
    @ns.doc('List_tasks')
    @ns.marshal_list_with(todo)
    def get(self):
        '''List of tasks'''
        todos = DAO.list_all()
        return todos

    @ns.doc('create_todo')
    @ns.expect(todo)
    @ns.marshal_with(todo, code=201)
    @api.doc(security='apikey')
    @token_required
    def post(self):
        '''Post a task to be achieved'''
        print(api.payload)
        DAO.create(api.payload)
        return '', 204


@ns.route('/todo')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    def get(self):
        '''Find a task based on ID'''
        id = int(request.values.get('id'))
        return DAO.get(id)

    @ns.doc('delete_todo', security='apikey')
    @ns.response(204, 'Todo deleted')
    @token_required
    def delete(self):
        '''Delete a task based on ID'''
        id = int(request.values.get('id'))
        DAO.delete(id)
        return '', 204

@ns.route('/due')
@ns.response(404, 'Todo not found')
@ns.param('due_by', 'The due date')
class Due(Resource):
    @ns.doc('todo_due')
    @ns.marshal_list_with(todo)
    def get(self):
        '''Find All tasks due on a Given date'''
        due_by = request.values.get('due_by')
        return DAO.get_dues(due_by)


@ns.route('/overdue')
@ns.response(404, 'Todo not found')
class OverDue(Resource):
    @ns.doc('todo_overdue')
    @ns.marshal_list_with(todo)
    def get(self):
        '''Find All tasks that are Overdue'''
        return DAO.get_over_dues()

@ns.route('/finished')
@ns.response(404, 'Todo not found')
class Finished(Resource):
    @ns.doc('finished_todo')
    @ns.marshal_list_with(todo)
    def get(self):
        '''Find All tasks that are Finished'''
        return DAO.get_finished()

@ns.route('/status')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The id')
@ns.param('status', 'New Status')
class Update(Resource):
    @ns.doc('status_update', security='apikey')
    @ns.response('204', 'Todo updated')
    @token_required
    def post(self):
        '''Update a Task Given ID'''
        id = int(request.values.get('id'))
        status = request.values.get('status')
        DAO.update(id, status)
        return '', 204


if __name__ == "__main__":
    api_main.run(debug=True)