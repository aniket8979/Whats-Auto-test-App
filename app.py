## Libraries for Flask & System related tasks
from flask import Flask 
from flask import request, render_template, jsonify, redirect, url_for, request
from werkzeug.utils import secure_filename
from flask import app
from flask_session import Session
import os
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import random
import smtplib
from time import sleep
from datetime import timedelta
import pandas as pd
from WPP_Whatsapp import Create
from multiprocessing import Process
import shutil
import threading
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, get_jwt
import redis

# MY SQL DATABASE LIBRARY & models
from tables import user_new, save_user_session
from models import engine
from sqlalchemy.sql import text



app = Flask(__name__)

access_expires = timedelta(minutes=5)

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = "nnnnnnnnSCRIZAnnnnnnnnnPVTnnnnnnnLTD"  # Change this!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = access_expires

jwt = JWTManager(app)

jwt_redis_blocklist = redis.StrictRedis(
    host='localhost', decode_responses=True
)

@jwt.token_in_blocklist_loader
def check_token_revoked(jwt_header, jwt_paylod:dict):
    jti = jwt_paylod['jti']
    token_in_redis = jwt_redis_blocklist.get(jti)
    return token_in_redis is not None


mySessions = dict()
forgetPassDict = {}

user_dir = ('D:\\Career\\Jobs\\Scriza Pvt. Ltd\\Internship\\Projects\\W_auto\\saved users')

# @jwt_required()
# @app.route('/')
# def index():
#     if 'user' in session:
#         return redirect(url_for('dash'))
#     else:
#         return render_template('login.html', name = None)


# @app.route('/dash', methods = ['GET', 'POST'])
# def dash():
#     if 'user' in session:
#         my_data = str(session['user'])
#         id, token = my_data.split('+')
#         a = tuple(render(userid=id))
#         return render_template('dash.html', accounts = a)
#     else:
#         return redirect(url_for('index'))


# @app.route('/wa')
# def wa():
#     if 'user' in session and 'tempN' in session:
#         return render_template('wa.html')
#     else:
#         return redirect(url_for('dash'))


@app.route('/logout')
@jwt_required()
def logout():
    global mySessions
    user = get_jwt()
    jti = user['jti']
    if 'number' in user:
        phone = str(user['number'])
        if phone in mySessions and 'number' in user:
            try:
                def logout_dri():
                    client = mySessions[phone].start()
                    client.close()
                log_dr = threading.Thread(target=logout_dri)
                log_dr.start()
                mySessions.pop(phone, None)
                
                jwt_redis_blocklist.set(jti, '', ex=access_expires)
                a = {'Status':'Logged out', 'Token':'Token revoked'}
                return jsonify(a), 200
                
            except:
                mySessions.pop(phone, None)
                jti = user['jti']
                jwt_redis_blocklist.set(jti, '', ex=access_expires)
                a = {'Status':'Logged out', 'Token':'Token revoked'}
                return jsonify(a), 200
                # return redirect(url_for('index'))
        else:
            mySessions.pop(phone, None)
            jwt_redis_blocklist.set(jti, '', ex=access_expires)
            a = {'Status':'Logged out', 'Token':'Token revoked'}
            return jsonify(a), 200
            # return redirect(url_for('index'))
    else:
        jwt_redis_blocklist.set(jti, '', ex=access_expires)
        a = {'Status':'Logged out', 'Token':'Token revoked'}
        return jsonify(a), 200
    


@app.route('/resetall')
@jwt_required()
def resetall():
    user = get_jwt()
    global user_dir
    token = user['token']
    users = (user_dir+'\\'+token)
    try:
        shutil.rmtree(users, ignore_errors=True)
        print(f"Folder '{users}' deleted successfully.")
        token = create_access_token(identity=user['sub'], additional_claims=user)
        a = {'Status':'All User Sessions Deleted', 'token':token}
        return jsonify(a), 200
            # return redirect(url_for('dash'))
    except Exception as e:
        print(f"Error: {e}")
        token = create_access_token(identity=user['sub'], additional_claims=user)
        a = {'Status':'Some Error Occured', 'token':token}
        return jsonify(a), 418



def create_profile(profile):
    directory = (user_dir+'\\'+profile)
    try:
        # Create the directory
        os.mkdir(directory)
        print(f"Folder '{directory}' created successfully.")
    except FileExistsError:
        print(f"Folder '{directory}' already exists.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def delete_account(userid, phone):
    global user_dir
    folder_path = (user_dir+'\\'+userid+'\\'+str(phone))
    try:
        shutil.rmtree(folder_path, ignore_errors=True)
        print(f"Folder '{folder_path}' deleted successfully.")
    except Exception as e:
        print(f"Error: {e}")


def del_db_data(phone):
    query = text(f"DELETE FROM users.user_session WHERE phone = {phone};")
    print(query)
    with engine.connect() as conn:
        conn.execute(query)
        conn.commit()
        print('User Whatsapp deleted from database')


def delete_file(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"File '{filepath}' deleted successfully.")
        else:
            print(f"File '{filepath}' does not exist.")
    except:
        print('file not deleted')




@app.route('/getqr')
@jwt_required()
def myqr():
        user = get_jwt()
        global mySessions
        data = None
        try:
            number = user['number']
            mySessions[number].start()
            data = mySessions[number].getQrcode()
            if data is not None:
                return render_template('qrcode.html', qrdata = data)
            else:
                a = {'Error':'Did not received Respose from whatsapp, Reset account and Scan Qr Again'}
                return jsonify(a), 408
        except:
            a = {'Error':'Did not received Respose from whatsapp, Reset account and Scan Qr Again'}
            return jsonify(a), 408




@app.route('/addaccount', methods = ['GET', 'POST'])
@jwt_required()
def add_account():
    global mySessions
    if request.method == 'GET':
        phone = str(request.values["phone"])

        user = get_jwt()

        try:
            save_user_session(sid=0, phone= phone, user_id= user['id'], status= 'inactive')
            def driver_act():
                a = activate_driver(username= user['token'], user_session=phone)
                print('User Data Saved')
                user_status(phone=phone, status='inactive')
                a.close()
            driver_thread = threading.Thread(target= driver_act())
            driver_thread.start()
            user['number'] = phone
            token = create_access_token(identity=user['sub'], additional_claims= user)
            a = {'Status':'Connecting with server', 'Response':'Fetch QR after few Seconds', 'token':token}
            return jsonify(a), 200
        except:
                a = {"Request timeout": "Reset Account and Rescan QR Code"}
                return jsonify(a), 408
    else:
        return jsonify({'error':'Invalid Request'}), 405



def activate_driver(username, user_session):
    global mySessions, user_dir
    my_dir = (user_dir+'\\'+username+'\\'+ user_session)
    print("Starting Session")
    mySessions[user_session] = Create(session=user_session, user_data_dir=my_dir,  close_already_profile=True)
    client = mySessions[user_session].start()
    print('User Session started')
    return client


@app.route('/access', methods = ['GET', 'POST'])
@jwt_required()
def user_whats():
    global mySessions
    if request.method == 'POST':
        info = get_jwt()
        button = str(request.values['access']).strip()
        print(button)
        if button[0:5] != 'close' and button[0:5] != 'reset':
            if button not in mySessions and 'number' not in info:
                ph_number = button
                def new_dr1():
                    client = activate_driver(username=token, user_session=ph_number)
                dr1 = threading.Thread(target=new_dr1)
                dr1.start()
                info['number'] = button
                token = create_access_token(identity=info['sub'], additional_claims=info)
                az = user_status(phone=str(ph_number), status='active')
                status = render(userid=info['id'])
                a = {'Status':'Session Started', 'token':token, 'Account':status}
                return jsonify(a), 200

            elif button in mySessions and 'number' in info:
                def new_dr2():
                    client = activate_driver(username=token, user_session=button)
                dr2 = threading.Thread(target=new_dr2)
                dr2.start()
                aa = user_status(phone=button, status='active')
                token = create_access_token(identity=info['sub'], additional_claims=info)
                status = render(userid=info['id'])
                a = {'Status':'Session Started', 'token':token, 'Account':status}
                return jsonify(a), 200
                
            elif button != info['number']:
                a = {'Error': 'Please close session :'+info['number']}
                return jsonify(a), 403
                
                
            else:
                old_sess = info['number']
                mySessions.pop(old_sess, None)
                user_status(phone=old_sess, status='inactive')
                info.pop('number', None)
                ph_number = button
                def new_dr3():
                    client = activate_driver(username=token, user_session=ph_number)
                dr3 = threading.Thread(target=new_dr3)             
                dr3.start()
                user_status(phone=ph_number, status='active')
                info['number'] = ph_number
                status = render(userid=info['id'])
                token = create_access_token(identity=info['sub'], additional_claims=info)
                a = {'Status':'Session Started', 'token':token, 'Account':status}
                return jsonify(a), 200
            

        elif button[0:5] == 'close':
            sess_ph = button[5:15]
            if sess_ph in mySessions:
                info.pop('number', None)
                try:
                    def cl_dr2():
                        client = mySessions[sess_ph].start()
                        client.close()
                    c_dr = threading.Thread(target=cl_dr2)
                    c_dr.start()
                    mySessions.pop(sess_ph, None)
                    user_status(phone= sess_ph, status= 'inactive')
                    token = create_access_token(identity=info['sub'], additional_claims=info)
                    status = render(userid=info['id'])
                    a = {'Status':'Session Closed', 'token': token, 'Accounts':status}
                    return jsonify(a), 200
                except:
                    user_status(phone= sess_ph, status= 'inactive')
                    mySessions.pop(sess_ph, None)
                    token = create_access_token(identity=info['sub'], additional_claims=info)
                    status = render(userid=info['id'])
                    a = {'Status':'Session Closed', 'token': token, 'Accounts':status}
                    return jsonify(a), 200
            else:
                user_status(phone= sess_ph, status= 'inactive')
                token = create_access_token(identity=info['sub'], additional_claims=info)
                status = render(userid=info['id'])
                a = {'Status':'Session Closed', 'token': token, 'Accounts':status}
                return jsonify(a), 200
            
        elif button[0:5] =='reset':
            try:
                if 'number' in info:
                    err = info['number']
                    a = {'Error':'Close the current session before resetting : '+err}
                    return jsonify(a), 403
                else:
                    sess_reset = button[5:15]
                    if sess_reset in mySessions:
                        mySessions.pop(sess_reset, None)
                        delete_account(userid=info['token'], phone=sess_reset)
                        del_db_data(phone=button[5:15])
                        token = create_access_token(identity=info['sub'], additional_claims=info)
                        status = render(userid=info['id'])
                        a = {'Status':'Session Deleted', 'token': token, 'Accounts':status}
                        return jsonify(a), 200
                    else:
                        delete_account(userid= info['token'], phone=sess_reset)
                        del_db_data(phone=sess_reset)
                        token = create_access_token(identity=info['sub'], additional_claims=info)
                        status = render(userid=info['id'])
                        a = {'Status':'Session Deleted', 'token': token, 'Accounts':status}
                        return jsonify(a), 200

            except:
                    print("This Reset-session went into Except block", sess_reset)
                    delete_account(userid= info['token'], phone=sess_reset)
                    del_db_data(phone=sess_reset)
                    token = create_access_token(identity=info['sub'], additional_claims=info)
                    status = render(userid=info['id'])
                    a = {'Status':'Session Deleted', 'token': token, 'Accounts':status}
                    return jsonify(a), 200
                   
    else:
        return jsonify({'error':'invalid request method'}), 405



@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            id = 0
            username =  str(request.json.get("username").strip())
            email = str(request.json.get('email').strip())
            password = generate_password_hash(password= str(request.values['password']).strip())
            token = uuid.uuid1()
            print(token)
            print(f'{username} and {email} and {password} and {token}')
            user_new(id=id, name=str(username), password=str(password), token=str(token), email=str(email))
            an = 'Registration Successful'
            create_profile(profile=token)
            a = {'Response': an}
            return jsonify(a), 200
            # return render_template ('register.html', data = an)
        except:
            a = {'Response': 'User Already Exist'}
            return jsonify(a) ,403
    else:
        return jsonify({'error':'invalid request method'}), 405


def render(userid):
    try:
        print(userid)
        # Rendered Data will be in form Table -> (id, user_id, name, number, session_id, account_status
        joinList = []
        query = text(f"SELECT user_session.user_id, new_user.email, user_session.phone, user_session.s_id, user_session.ac_status FROM new_user RIGHT JOIN user_session ON new_user.id = user_session.user_id where new_user.id = '{str(userid)}';")
        with engine.connect() as conn:
            ret = conn.execute(query)
            tup = tuple(ret.fetchall())
            if tup:
                for i in range(len(tup)):
                    response = {'phone': tup[i][2], 'status': tup[i][4]}
                    joinList.append(response)                
                return joinList
            return joinList
    except:
        print('Some Problem in Database Join in Render function')
        return joinList


@app.route('/login', methods = ['GET','POST'])
def User_login():
    us_log = None
    if request.method == 'POST':
        email1 =  str(request.json.get("email", None))
        password1 = str(request.json.get("password", None))
        email = email1.strip()
        password = password1.strip()
        query = text(f"SELECT * FROM users.new_user WHERE email = '{email}';")
        with engine.connect() as conn:
            # global us_log
            verify = conn.execute(query)
            log_user = verify.fetchall()
            us_log = tuple(log_user)
            print('IF this is empty',us_log)
            if us_log:
                if check_password_hash(pwhash=us_log[0][2], password=password):
                    dash = render(userid= us_log[0][0])
                    # Session dict will store -> userid, token, 
                    token_Data = { 'id':str(us_log[0][0]), 'token':str(us_log[0][3])} 
                    print(token_Data)
                    token = create_access_token(identity=us_log[0][0], additional_claims=token_Data)
                    a = {'Login':'Successful', 'Token':token, 'dash':dash}
                    return jsonify(a), 200
                    # return render_template('Dash.html', name = a, accounts = dash, id = us_log[0][0]) #response, name= a)
                else:
                    a = {'login': 'Failed', 'reason':'Incorrect Password'}
                    return jsonify(a), 403

                    # return render_template('login.html', name = a)
            else:
                f = 'Failed'
                r ='Incorrect EmailID'
                a = {'login': f, 'reason':r}
                return jsonify(a), 401
                # return render_template('login.html', name = a)   
    else:
        a = {'err':'Incorrect request method'}
        return jsonify(a) ,405
        # if 'user' in session:
        #     # id, token = session['user'].split('+')
        #     return redirect(url_for('dash'))
        
        # return redirect(url_for('index'))



def send_OTP_mail(mail, otp):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user='inceptionfirm@gmail.com', password='gngcsgqlmkemimbf')
        server.sendmail( from_addr='inceptionfirm@gmail.com', to_addrs=mail,  msg=f'Subject:Your OTP is {otp}')
        return f"OTP Sent on {mail}"
    except Exception as e:
        print(e)
        return f"Failed to send OTP on {mail}"
    

    

@app.route('/forget', methods = ['GET', 'POST'])
def account_exist():
    global forgetPassDict
    email = str(request.values['email']).strip()
    query = text(f"SELECT * FROM users.new_user WHERE email = '{email}';")
    with engine.connect() as conn:
        exist = conn.execute(query)
        isExist = tuple(exist.fetchall())
        try:
            if email == isExist[0][4]:
                gen_otp = str(random.randint(1111,9999))
                con_email = email.strip()
                mail =  send_OTP_mail(mail=con_email, otp=gen_otp)
                forgetPassDict[str(con_email)] = str(gen_otp)
                token = create_access_token(identity = con_email)
                a = {'Status': mail, 'Response':'verify OTP request is Allowed', 'Token':token}
                return jsonify(a), 200
        except:
            a = {'Response':'User Does not exist'}
            return jsonify(a), 200


@app.route('/verify', methods = ['GET', 'POST'])
@jwt_required
def forget_pass():
    global forgetPassDict
    user = get_jwt()
    sent_otp = forgetPassDict[email]
    otp = str(request.values['otp']).strip()
    if sent_otp==otp:
            email = str(user['email'])
            user['secure'] = '!@#$%'
            token = create_access_token(identity=user['sub'], additional_claims=user)
            a = {'Status': 'OTP Varified','Response':'resetpass request is Allowed', 'Token':token}
            forgetPassDict.pop(email)
            return jsonify(a), 200
            # return render_template('resetPass.html', resp = a)
    else:
        a = {'Response': 'Invalid OTP'}
        return jsonify(a), 403
    



@app.route('/resetpass', methods = ['GET', 'POST'])
@jwt_required
def reset_pass():
    if request.method == 'POST':
        pass_1 = str(request.values['pass1'])
        pass_2 = str(request.values['pass2'])
        pass1 = pass_1.strip()
        pass2 = pass_2.strip()
        user = get_jwt()
        print('This is printed from reset_pass',user['sub'])
        if pass1 == pass2 and user['secure'] == '!@#$%':
            new_pass = str(generate_password_hash(password= pass2).strip())
            query = text(f"update users.new_user set password = '{new_pass}' where email = '{str(user['sub'])}';")
            print(query)
            with engine.connect() as conn:
                conn.execute(query)
                print('the query is commting')
                conn.commit()
                print('comitted')
                jti = get_jwt()['jti']
                jwt_redis_blocklist.set(jti, '', ex=access_expires)
                a = {'Status':'Password Changed Successfully', 'Token':'Token Revoked, Please Log in Again'}                    
                return jsonify(a), 200
        else:
            a = {'Response': 'Password did not matched'}
            return jsonify(a), 403
            # return render_template('resetPass.html', resp = 'Password did not matched')    
    else:
        a = {'Response':'Incorret request method'}
        


def user_status(phone, status):
    u_status = tuple()
    query = text(f"UPDATE user_session SET ac_status = '{status}' WHERE (phone = '{phone}');")
    print(query)
    with engine.connect() as conn:
        conn.execute(query)
        conn.commit()
        n_query = text(f"SELECT * FROM user_session WHERE phone = '{str(phone)}';")
        rt = conn.execute(n_query)
        u_status = tuple(rt)
        print('this shows active inactive status: ', u_status)
        a = {'status': u_status[0][3]}
        return a


# @app.route('/cmsg')
# def c_msg():
#     if 'user' in session and 'tempN' in session:
#         return render_template('msg.html')
#     else:
#         return redirect(url_for('dash'))


@app.route('/msg' , methods = ['GET', 'POST'])
@jwt_required
def custom_msg():
    user = get_jwt()
    if 'number' in user:
        global mySessions
        try:
            number = user['number']
            client = mySessions[number].start()
            phone =  str(request.json.get("phone")).strip()
            phone_len = len(phone)
            phone = phone[phone_len - 10:]
            text = str(request.json.get("text"))

            client.sendText("+91"+phone, text)
            # token = create_access_token(identity=user['sub'], additional_claims=user)
            a = {'Status':'Message sent Successfully'}
            return jsonify(a), 200
        except:
            a = {'Status': 'Message not sent'}
            # token = create_access_token(identity=user['sub'], additional_claims=user)
            a = {'Status':'Message not Sent'}
            return jsonify(a), 200
    else:
        # token = create_access_token(identity=user['sub'], additional_claims=user)
        a = {'Status':'User Session Inactive'}
        return jsonify(a), 200
    


@app.route('/imgsend', methods =['GET','POST'])
@jwt_required
def send_image():
    user = get_jwt()
    if 'number' in user:
        global mySessions, user_dir
        user_token_id = user['token']
        numb = str(user['number'])
        my_dir = (user_dir+'\\'+ user_token_id +'\\'+str(numb))
        try:
            if request.method == 'POST':

                file = request.files['myfile']
                image = request.files['myimage']
                textmsg = str(request.values['caption'])

                filename = secure_filename(file.filename)
                file.save(os.path.join(my_dir, filename))
                print('File Uploaded Successfully')

                imagename = secure_filename(image.filename)
                image.save(os.path.join(my_dir, imagename))
                print('Image Uploaded Successfully')

                imagepath = (my_dir+'\\'+imagename)
                file_path = (my_dir+'\\'+filename)
                # Code to read excel files
                data = pd.read_excel(file_path)

                client = mySessions[numb].start()

                count = 0
                for column in data['Phone'].to_list():
                    phone = str(data['Phone'][count])
                    phone_len = len(phone)
                    phone = phone[phone_len - 10:]
                    try:
                        contact = str(column)
                        print('Sending image on : ',contact)
                        reciever = ('+91'+phone)
                        client.sendImage(to=reciever, filePath=imagepath, filename='scz', caption=textmsg, isViewOnce=None)  
                        # client.sendImage(to=phone, filename= imagepath, caption=textmsg, isViewOnce=None)
                        count = count +1
                    except:
                        print('This number does not exist', contact)
                        count = count +1
                
                delete_file(filepath= file_path)
                delete_file(filepath=imagepath)
                a = {'Status':'Image sent Successfully'}
                return jsonify(a), 200
            
            else:
                # delete_file(filepath=imagepath)
                # delete_file(filepath= file_page)
                a = {'Status': 'Incorrect request method'}
                # return jsonify(a)
                return jsonify(a), 405
        except:
            a = {'Status':'some error occoured, Please restart session'}
            return jsonify(a), 404
    



## Upload file function
@app.route('/upload', methods = ['GET','POST'])
@jwt_required
def file_page():
    user = get_jwt()
    if 'number' in user:
        user_token = user['token']
        numb = str(user['number'])

        global user_dir, mySessions
        my_dir = (user_dir+'\\'+user_token+'\\'+ numb)
        try:
            if request.method == 'POST':
                file = request.files['myfile']
                custom_message = str(request.values['message'])
                filename = secure_filename(file.filename)
                file.save(os.path.join(my_dir, filename))
                print('File Uploaded Successfully')
                print('Running Automation Script')

                file_path = (my_dir+'\\'+filename)
                # Code to read excel files
                data = pd.read_excel(file_path)

                client = mySessions[numb].start()

                count = 0
                for column in data['Phone'].to_list():
                    phone = str(data['Phone'][count])
                    phone_len = len(phone)
                    phone = phone[phone_len - 10:]
                    try:
                        contact = str(column)
                        print('Sending text on : ',contact)

                        text1 = str(data['Text1'][count])
                        print(text1[0:5])
                        # For Sending Custom Messsages
                        if text1 !='nan':
                            text2 = str(data['Text2'][count])
                            client.sendText("+91"+phone, text1)
                            #It Checks if there is another msg to be send or not
                            if text2 == None or text2 == 'nan':
                                print('do not have a second messsage')
                            # the Code Continue Looping if it is empty
                            else:
                                client.sendText("+91"+phone, text2)
                            count = count+1
                            sleep(0.25)

                        else:
                            client.sendText("+91"+phone, custom_message)
                            sleep(0.25)
                            count = count+1
                    except:
                        # print('This number does not exist', contact)
                        count = count +1
                
                delete_file(filepath= file_path)
                a = {'Status': 'Msg sent to Contacts'}
                return jsonify(a), 200
            
            else:
                delete_file(filepath= file_page)
                a = {'Status':'Incorrect Form method'}
                return jsonify(a), 405
            
        except:
            a = {'Status':'some error occoured, Please restart session !!'}
            return jsonify(a), 404
    else:
        a = {'Status':'User Session not Started'}
        return jsonify(a), 404
    


@app.route('/unread')
@jwt_required
def unread():
    user = get_jwt()
    global mySessions, user_dir
    if 'number' in user:
        path = user_dir+'\\'+str(user['token'])+'\\'+str(user['number'])
        numb = str(user['number'])
        sender = []
        client = mySessions[numb].start()
        data = client.getAllUnreadMessages()
        for i in data:
            recFrom = str(i['from'])
            recMsg = str(i['body'])
            if len(recFrom) <= 20:
                if recMsg != None and recFrom[2:12] !=numb:
                    sender.append(recFrom)
            else:
                continue
        with open (path+'\\'+'incoming.txt', 'w') as file:
            for number in sender:  
                file.write(str(number))
                file.write('\n')
        chat = len(sender)
        a = {'Status':chat+' new msgs', 'senders':sender}
        return jsonify(a), 200
    

@app.route('/reply', methods = ['GET','POST'])
@jwt_required
def reply():
    global user_dir, mySessions
    user = get_jwt()
    if 'number' in user:
        try:
            path = user_dir+'\\'+str(user['token'])+'\\'+str(user['number'])
            senders = []
            with open(path+'\\'+'incoming.txt', 'r') as file:
                for line in file:
                    senders.append(str(line.strip()))
        except:
            return jsonify({'Status':'Some Error Occured'}), 404
            

        text = str(request.values['reply_msg'])
        reply_fail = 0
        reply_done = 0
        numb = user['number']
        for number in senders:
            number = str(number[3:13])
            count = 0
            client = mySessions[numb].start()            
            
            try:
                client.sendText("+91"+number, text)
                reply_done = reply_done + 1
            except:
                print('Unable to reply to this User')
                reply_fail = reply_fail + 1
                count = count+1
                a = {
                        'Status':{
                            'Status':'Task Completed',
                            'Successful':f"{reply_done}",
                            'Failed':f"{reply_fail}"
                            }
                        }
                    # return jsonify(a)
                return jsonify(a), 200
            else:
                print('No New Chats available')
                a = {
                    'Status':{
                        'Status':'Task Completed',
                        'Successful':f"{reply_done}",
                        'Failed':f"{reply_fail}"
                    }
                }
                return jsonify(a), 200
                # return jsonify(a)
            # return render_template('reply.html',  fail = reply_fail, done = reply_done)


if __name__ == '__main__':
    app.run(debug=True, threaded=True)