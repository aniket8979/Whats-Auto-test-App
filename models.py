from sqlalchemy import Column, String, Integer, Table, MetaData, create_engine, ForeignKeyConstraint
from sqlalchemy.inspection import inspect

meta_data = MetaData()

db_connection = "mysql+pymysql://root:scriza321@localhost/users"

engine = create_engine(db_connection)


try:
    conn = engine.connect()
    print('DB Connected')
    print('Connection object is :{}' .format(conn))
except:
    print('DB not connected')


# Models Tables added here
class mytable:
    new_user = Table(
        'new_user', meta_data,
        Column('id', Integer(), primary_key=True ,nullable=False, autoincrement=True), 
        Column('name', String(51), nullable=False),
        Column('password', String(300), nullable=False),
        Column('token', String(300)),
        Column('email', String(100), nullable=False, unique=True)
    ) 

    user_session = Table(
        'user_session', meta_data,
        Column('s_id', Integer(), primary_key=True, nullable=False, autoincrement=True,),
        Column('phone', String(10), nullable=False, unique=True),
        Column('user_id', Integer(), nullable=False,),
        Column('ac_status', String(15), nullable=True,),
    
    )
    

meta_data.create_all(engine)