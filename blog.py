from flask import Flask,render_template,flash,redirect,url_for,session,logging,request

from flask_mysqldb import MySQL

from wtforms import Form,StringField,TextAreaField,PasswordField,validators

from passlib.hash import sha256_crypt

from functools import wraps

import time

# Kullanıcı Kayıt
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.length(min=3,max=30),validators.DataRequired()])
    username = StringField("Kullanıcı Adı",validators=[validators.length(min=3,max=30),validators.DataRequired()])
    email = StringField("E posta adresi",validators=[validators.Email(message="Lütfen Geçerli Bir Email Adresi Girin")])
    password = PasswordField("Parola",validators=[
        validators.length(min=6,max=40),
        validators.data_required(message=("Lütfen Bir Parola Belirleyin")),
        validators.EqualTo(fieldname = "confirm",message="Parolanız Uyuşmuyor")])
    confirm = PasswordField("Parola Doğrula")

class LoginForm(Form):

    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")


app = Flask(__name__)

app.secret_key= "Aladağ Design"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "aladağ design"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

@app.route("/")
def index():

    return render_template("index.html")

@app.route("/about")
def about():

    return render_template("about.html")


# Kullanıcı Giriş Decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:

            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın","danger")

            return redirect(url_for("login"))

    return decorated_function

# Kayıt Olma
@app.route("/register",methods = ["GET","POST"])
def register():
    
    form =RegisterForm(request.form)

    if request.method == "POST" and form.validate():

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password =  sha256_crypt.encrypt(form.password.data)
        
        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)" # .format olarak ta kullanılabilir.

        cursor.execute(sorgu,(name,email,username,password)) #Sorguda ki yerlerine geçer.

        mysql.connection.commit()

        cursor.close()

        flash("Başarıyla Kayıt Oldunuz...","success")

        return redirect(url_for("login"))

    else:
        return render_template("register.html",form = form)

# Giriş Yapma
@app.route("/login",methods =["GET","POST"])
def login():

    form = LoginForm(request.form)

    if request.method == "POST":

        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * From users where username = %s"

        result = cursor.execute(sorgu,(username,)) # Eğer kullanıcı adı yok ise result 0 değerini girecek.

        if result > 0:

            data = cursor.fetchone()

            real_password = data["password"]

            if sha256_crypt.verify(password_entered,real_password):

                flash("Başarıyla Giriş Yapıldı...","success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))

                

            else:
                flash("Parolanız Hatalı","danger")

                return redirect(url_for("login"))

        else:
            flash("Böyle Bir Kullanıcı Bulunmuyor...","danger")
            return redirect(url_for("login"))

    return render_template("login.html",form = form)

@app.route("/kontrol")
@login_required
def kontrol():

        cursor = mysql.connection.cursor()

        sorgu = "Select * From article where author = %s"

        result = cursor.execute(sorgu,(session["username"],))

        if result > 0:

            article = cursor.fetchall()

            return render_template("kontrol.html",article = article)
        
        else:

            return render_template("kontrol.html")

# Detay Sayfası

@app.route("/article/<string:id>")

def article(id):

    cursor = mysql.connection.cursor()

    sorgu = "Select * from article where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:

        article = cursor.fetchone()

        return render_template("article.html",article = article)

    else:

        return render_template("article.html")

# Logout işlemi

@app.route("/logout")

def logout():

    session.clear()
    
    return redirect(url_for("index"))

# Makale Ekleme
@app.route("/addarticle",methods = ["GET","POST"])

def addarticle():

    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():

        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into article(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()

        flash("Günlük Başarıyla Kayıt Edildi...","success")

        return redirect(url_for("kontrol"))

    return render_template("addarticle.html",form = form)

# Makale Güncelleme

@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required

def update(id):

    if request.method == "GET":

        cursor = mysql.connection.cursor()

        sorgu = "Select * from article where id = %s and author = %s"

        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:

            flash("Böyle bir günlük yok  veya Bu işleme yetkiniz yok","danger")

            return redirect(url_for("index"))

        else:

            article = cursor.fetchone()

            form = ArticleForm()

            form.title.data = article["title"]

            form.content.data = article["content"]

            return render_template("update.html",form = form)

    else:
        
        # Post Request

        form = ArticleForm(request.form)

        newTitle = form.title.data

        newContent = form.content.data

        sorgu2 = "Update article Set title = %s,content = %s where id = %s"

        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()

        flash("Günlük Güncellendi...","success")
        
        return redirect(url_for("kontrol"))

        
# Makale Silme

@app.route("/delete/<string:id>")
@login_required # Eğer Giriş yaptıysa çalışır

def delete(id):

    cursor = mysql.connection.cursor()

    sorgu = "Select * From article where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:

        sorgu2 = "Delete From article where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        flash("Secilen Günlük Silindi...","danger")

        return redirect(url_for("kontrol"))

    else:

        flash("Böyle bir günlük yok veya Böyle bir şey yapma yetkiniz yok","danger")

        return redirect(url_for("index"))

pass


# Makale Form

class ArticleForm(Form):
    
    title = StringField("Günlük Başlığı",validators=[validators.length(min = 5,max= 50)])
    
    content = TextAreaField("Günlük İçeriği",validators=[validators.length(min= 10)])

# Paylaşılan Makale sayfası

@app.route("/articles")

def articles():


    cursor = mysql.connection.cursor()

    sorgu = "Select * From article"

    result = cursor.execute(sorgu)

    if result > 0:
        
        articles = cursor.fetchall()

        return render_template("articles.html",articles = articles)
    
    else:
        return render_template("articles.html")


# Mektup Gönderme

@app.route("/mesages")
@login_required

def mektupgonder():

    return render_template("mesages.html")

    cursor = mysql.connection.cursor()

    sorgu = "Select * From article"

    result = cursor.execute(sorgu)

    if result > 0:
        
        articles = cursor.fetchall()

        return render_template("articles.html",articles = articles)
    
    else:
        return render_template("articles.html")

 # Arama URL

@app.route("/search",methods = ["GET","POST"])

def search():

    if request.method == "GET":

        return redirect(url_for("index"))

    else:

        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()

        sorgu = "Select * from article where title like '%" + keyword + "%' "

        result = cursor.execute(sorgu)

        if result == 0:

            flash("Aranan Günlük bulunamadı..","warning")

            return redirect(url_for("articles"))

        else:

            articles = cursor.fetchall()

            return render_template("articles.html",articles = articles)


if __name__ == "__main__":
    app.run(debug=True)