from functools import wraps
from flask import g,Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
#Kullanıcı giriş decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın.","danger")
            return redirect(url_for("login"))
    return decorated_function



#Kullanıcı kayıt form classı
class RegisterForm(Form):
    name=StringField("İsim Soyisim", validators=[validators.Length(min=4,max=25,message="İsim ve soyisim 4-25 karakter arasında olmalı.")])
    username=StringField("Kullanıcı Adı", validators=[validators.Length(min=5,max=35,message="Kullanıcı adı 5-35 karakter arasında olmalı.")])
    email=StringField("E-posta", validators=[validators.email(message="Lütfen geçerli bir mail adresi giriniz.")])
    password=PasswordField("Parola",validators=[
        validators.Length(min=5,max=16,message="Parola 5-16 karakter uzunluğunda olmalıdır"),
        validators.DataRequired(message="Bu alan boş bırakılamaz"),
        validators.EqualTo(fieldname="confirm",message="Parolanız uyuşmuyor")
    ])   
    confirm=PasswordField("Parolanızı doğrulayın")

class LoginForm(Form):
    username=StringField("Kullanıcı adı:")
    password=PasswordField("Parola")

app=Flask(__name__)
app.secret_key="aliblog"
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="aliblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"
mysql=MySQL(app)


#navbarı ve diğer önemli şeyleri layout.html e ekledim sayfa dosyalarına da layout u extend ediyorum
@app.route('/')
def index():
    return render_template("index.html")
@app.route("/about")# hem get hem post request yapmamızı sağlıyor
def about():
    return render_template("about.html")

"""@app.route("/article/<string:id>")# burada <string:id> sayesinde browser daki url ekranında yazdığımız id yi alabiliyoruz.
def detail(id):
    return "Article ID "+id
"""
@app.route('/register',methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)
    if request.method =="POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)
        cursor=mysql.connection.cursor()
        # email check

        sorgu="select * from users where email=%s"
        result=cursor.execute(sorgu,(email,))
        if result>0:
            flash("Girdiğiniz email adresi zaten kullanımda","danger")
            return redirect(url_for("register"))

        #__________________________
        # username check

        sorgu="select * from users where username=%s"
        result=cursor.execute(sorgu,(username,))
        if result>0:
            flash("Girdiğiniz kullanıcı adı daha önce alınmış","danger")
            return redirect(url_for("register"))

        #__________________________
        sorgu="insert into users(name, email, username, password) VALUES(%s,%s,%s,%s)" 
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        
        cursor.close()
        flash("Başarıyla Kayıt Oldunuz...","success")    
        return redirect(url_for("login"))
    else:
        #eğer get request yapılmışsa sayfayı gösteriyoruz   
        return render_template("register.html",form=form)# form u direkt html e gönderiyoruz         

#login işlemi:
@app.route("/login",methods=["GET","POST"])
def login():
    form=LoginForm(request.form)
    if request.method=="POST":
        
        username=form.username.data
        password_entered=form.password.data
        cursor=mysql.connection.cursor()
        sorgu="select * from users where username = %s"
        result=cursor.execute(sorgu,(username,))
        if result > 0:
            data=cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla giriş yaptınız. Hoşgeldin {}".format(username),"success")
                
                session["logged_in"]=True
                session["username"]=username
                return redirect(url_for("index"))
            else:
                flash("Kullanıcı adı veya şifrenizi yanlış girdiniz","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))

    else:
        return render_template("login.html",form=form)
#Makale detay sayfası
@app.route("/article/<string:id>")
@login_required
def article(id):
    cursor=mysql.connection.cursor()
    sorgu="select * from articles where id=%s"
    result=cursor.execute(sorgu,(id,))
    if result>0:
        article=cursor.fetchone()
        return render_template("article.html",article=article)   

    else:
        return render_template("article.html")   


#Log out işlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    sorgu="select * from articles where author=%s"
    result=cursor.execute(sorgu,(session["username"],))
    if result>0:
        articles=cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
        return render_template("dashboard.html")
    return render_template("dashboard.html")

@app.route("/addarticle",methods=["GET","POST"])
@login_required
def addarticle():
    form=ArticleForm(request.form)
    if request.method=="POST" and form.validate():
        title=form.title.data
        content=form.content.data
        cursor=mysql.connection.cursor()
        sorgu="insert into articles(title,author,content) values(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()

        cursor.close()
        flash("Makale başarıyla eklendi","succes")

        return redirect(url_for("dashboard"))
    return render_template("addarticle.html",form=form)

#Makale sayfası
@app.route("/articles")
@login_required
def articles():
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles"
    result=cursor.execute(sorgu)
    if result>0:
        articles=cursor.fetchall()
        
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")



#Makale güncelleme
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method=="GET":
        cursor=mysql.connection.cursor()
        sorgu="select * from articles where id=%s and author=%s"
        result=cursor.execute(sorgu,(id,session["username"]))
        if result==0:
            flash("Böyle bir makale yok ya da bu işleme yetkiniz yok.")
            return redirect(url_for("index"))
        else:
            article=cursor.fetchone()
            form=ArticleForm()
            form.title.data=article["title"]
            form.content.data=article["content"]
            return render_template("update.html",form=form)
    #post request
    elif request.method=="POST":
        form=ArticleForm(request.form)
        new_title=form.title.data
        new_content=form.content.data
        sorgu2="update articles set title=%s,content=%s where id=%s"
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(new_title,new_content,id))
        mysql.connection.commit()
        flash("Makale başarıyla güncellendi","success")
        return redirect(url_for("dashboard"))
#Makale silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    sorgu="select * from articles where author=%s and id=%s"
    result=cursor.execute(sorgu,(session["username"],id))
    if result>0:
        sorgu2="delete from articles where id=%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        flash("Makale başarıyla silindi","success")
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok ya da bu işleme yetkiniz yok.","danger")
        return redirect(url_for("dashboard"))
#Makale arama
@app.route('/search',methods=["GET","POST"])
@login_required
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")
        cursor=mysql.connection.cursor()
        sorgu="select * from articles where title like '%"+keyword+"%'"
        result=cursor.execute(sorgu)
        if result==0:
            flash("Aranılan kelimeye uygun makale bulunamadı","warning")
            return redirect(url_for("articles"))
        else:
            articles=cursor.fetchall()
            return render_template("articles.html",articles=articles)

#Makale formu
class ArticleForm(Form):
    title=StringField("Makale Başlığı",validators=[validators.Length(min=5,max=100)])
    content=TextAreaField("Makale içeriği",validators=[validators.Length(min=10)])



if __name__=="__main__":
    app.run(debug=True)

"""
    articles=[
        {"id":1, "title":"Deneme1","content":"Deneme1 icerik"},
        {"id":2, "title":"Deneme2","content":"Deneme2 icerik"},
        {"id":3, "title":"Deneme3","content":"Deneme3 icerik"}
    ]
""" 