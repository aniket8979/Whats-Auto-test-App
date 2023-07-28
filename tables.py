from models import mytable, conn

## funtion to create new user in database
def user_new(id, name, password,token, email):
    try:
        user = mytable.new_user.insert().values(
            id = id,
            name = name,
            password = password,
            token =  token,
            email = email,
        )
        print((user))
        print(user.compile().params)
        result = conn.execute(user)
        print('Last Inserted Key : ')
        conn.commit()
        return result.inserted_primary_key
    except Exception as e:
        print('Some error Occured with database entry', e)
        # return e


def save_user_session(sid, phone, user_id, status):
    try:
        session = mytable.user_session.insert().values(
            s_id = sid,
            phone = phone,
            user_id = user_id,
            ac_status = status,
        )
        print(session)
        print(session.compile().params)
        result = conn.execute(session)
        print('last inserted key: ', result.inserted_primary_key)
        conn.commit()
    except:
        print('some error with session model')

