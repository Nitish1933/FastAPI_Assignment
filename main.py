from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from peewee import *
import datetime
import bcrypt
import string
import secrets



DATABASE = 'tweepee1.db'

database = SqliteDatabase(DATABASE)

class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    username = CharField(unique=True, primary_key=True)
    password = CharField()
    email = CharField()
    join_date = DateTimeField(default=datetime.datetime.utcnow())


class Authentication(BaseModel):
    token = CharField(max_length=255, unique=True, primary_key=True)
    user_id = ForeignKeyField(User, to_field='username')


class Post(BaseModel):
    content = TextField()
    author = ForeignKeyField(User, to_field='username', backref='author_name')
    number_of_likes = IntegerField(default=0)


class Likes(BaseModel):
    user_id = ForeignKeyField(User, to_field="username")
    post_id = ForeignKeyField(Post, to_field="id")


def create_tables():
    database.connect()
    database.create_tables([User, Post, Likes, Authentication], safe = True)
    database.close()


# create_tables()


# user = User.create(username='Nitish', password='4567', email='nitish@gmail.com')
# User.create(username='Aryan', password='6789', email='aryan@gmail.com')
# User.create(username='Aditya', password='1234', email='aditya@gmail.com')
# User.create(username='KK', password='8765', email='kk@gmail.com')
# User.create(username='Ashutosh', password='4325', email='ashutosh@gmail.com')
# user.save()
# post = Post.create(content='This is the content', author='Nitish')
# Post.create(content='This is my First post', author='Aryan')
# Post.create(content='This is my 2nd post', author='Nitish')
# post.save()
# like = Likes.create(user_id="Nitish",post_id="2",number_of_likes=10)
# like.save()


app = FastAPI()

# @app.get("/")
# def root():
#     return {"message": "Hello World"}


# templates = Jinja2Templates(directory='templates')

# @app.get("/{username}", response_class=HTMLResponse)
# async def home(request: Request, username: str):
#     return templates.TemplateResponse('navbar.html', {'request': request, 'username': username})


@app.get('/get_users')
async def getUsers():
    query = User.select()
    users = []
    for i in query:
        users.append({'username': i.__data__['username'], 'email': i.__data__['email'], 'Joined On': i.__data__['join_date']})

    return users


@app.get('/get_user/{id}')
async def getSingleUser(id):
    # query = User.select().where(User.username == str(id))
    # user = []
    # for i in query:
    #     user.append({'username': i.__data__['username'], 'email': i.__data__['email'], 'Joined On': i.__data__['join_date']})

    user = User.get(User.username == str(id))

    return user


@app.get('/get_posts')
async def getPosts():
    query = Post.select()
    posts = []
    for i in query:
        posts.append({'id': i.__data__['id'], 'content': i.__data__['content'], 'author': i.__data__['author']})

    return posts


@app.get('/get_post_by_id/{id}')
async def getPosts(id):
    query = Post.select().where(Post.id == id)
    posts = []
    for i in query:
        posts.append({'id': i.__data__['id'], 'content': i.__data__['content'], 'author': i.__data__['author']})

    return posts


@app.get('/get_post/{user_id}')
async def getPostsByUser(user_id):
    query = Post.select().where(Post.author == str(user_id))
    posts = []
    for i in query:
        posts.append({'id': i.__data__['id'], 'content': i.__data__['content'], 'author': i.__data__['author']})

    return posts


@app.delete('/delete_post/{id}')
async def deletePost(id):
    query = Post.delete().where(Post.id == int(id))
    query.execute()

    return {"message": "Successfully deleted"}


@app.put('/like/{post_id}')
async def likePost(post_id):
    post = Post.get(Post.id == str(post_id))
    print(post.number_of_likes)

    user_id = 'Kritika'

    query = Likes.select().where(Likes.post_id == post_id)
    for i in query:
        if i.__data__['user_id'] == user_id:
            post.number_of_likes = post.number_of_likes - 1
            post.save()
            sub_query = Likes.delete().where(Likes.user_id == user_id)
            sub_query.execute()
            return {'message': 'Post was disliked'}

    post.number_of_likes = post.number_of_likes + 1
    post.save()
    like = Likes.create(user_id='Kritika', post_id=post_id)
    like.save()

    return {"message": "Post was liked"}


@app.get('/likedby/{post_id}')
async def likedBy(post_id):
    query = Likes.select().where(Likes.post_id == post_id)
    users = []

    if len(query) == 0:
        return {'msg': 'no one has liked this post yet'}
    for i in query:
        users.append(i.__data__['user_id'])

    return users


@app.get("/filter/{keyword}")
async def search_user(keyword):
    query = User.select().where(User.username.contains(keyword))
    users = []
    for i in query:
        users.append({'username': i.__data__['username'], 'email': i.__data__['email'], 'Joined On': i.__data__['join_date']})

    return users


@app.get('/get_head/{limit}')
async def get_head(limit):
    query = Post.select().limit(limit)
    posts = []

    for i in query:
        posts.append({'id': i.__data__['id'], 'content': i.__data__['content'], 'author': i.__data__['author']})

    return posts


@app.post("/upload/")
async def upload(file: UploadFile):
    with open(file.filename, "r") as f_in:
        content = f_in.read()
    return {"filenames": file.filename, 'content': content}


@app.get("/register_form")
async def registerForm():
    with open('templates/register.html', "r") as f_in:
        content = f_in.read()
    return HTMLResponse(content=content)


@app.post('/register')
async def registerUser(username: str = Form(...), password: str = Form(...), email: str = Form(...)):
    # print(username, password, email)

    N = 7
    token = str(''.join(secrets.choice(string.ascii_uppercase + string.digits)
              for i in range(N)))

    with open('.env', "r") as e:
        salt = e.read()

    salt = salt.encode('utf-8')
    enc_token = token.encode('utf-8')
    final_token = bcrypt.hashpw(enc_token, salt)

    byte = password.encode('utf-8')
    hash_pswd = bcrypt.hashpw(byte, salt)


    query = User.select()
    for i in query:
        userPassword = i.__data__['password']
        userBytes = userPassword.encode('utf-8')
        if userBytes == hash_pswd or i.__data__['username'] == username:
            return {"message": "Username or Password already taken"}

    user = User.create(username=username, password=hash_pswd, email=email)
    user.save()

    auth = Authentication.create(token=final_token, user_id=username)
    auth.save()

    return {"message": f"User successfully Created. Your token is {final_token}, keep it saved (token starts with the $ part)"}


@app.get("/login_form")
async def loginForm():
    with open('templates/login.html', "r") as f_in:
        content = f_in.read()
    return HTMLResponse(content=content)


@app.post('/login')
async def loginUser(username: str = Form(...), password: str = Form(...)):
    with open('.env', "r") as e:
        salt = e.read()

    salt = salt.encode('utf-8')
    byte = password.encode('utf-8')
    hash_pswd = bcrypt.hashpw(byte, salt)
    query = User.select()
    for i in query:
        userPassword = i.__data__['password']
        userBytes = userPassword.encode('utf-8')
        if userBytes == hash_pswd and i.__data__['username'] == username:
            return {"message": "Welcome Back"}

    return {'message': 'Invalid Credentials'}


@app.get("/post_form")
async def registerForm():
    with open('templates/post.html', "r") as f_in:
        content = f_in.read()
    return HTMLResponse(content=content)


@app.post('/create_post')
async def createPost(content: str = Form(...), token: str = Form(...)):
    print(content, token)

    auth = Authentication.select().where(Authentication.token == token)

    if len(auth) == 0:
        return {"message": "Invalid Token"}

    query = Authentication.get(Authentication.token == token)
    post = Post.create(content=content, author=query.user_id)
    post.save()
    return {"message": "Thanks for posting"}