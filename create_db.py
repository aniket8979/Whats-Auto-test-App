import mysql.connector 

mydb = mysql.connector.connect(
    user = 'root',
    password = 'scriza321',
    host = '127.0.0.1',
)

my_cusor = mydb.cursor()

#my_cusor.execute('CREATE DATABASE users')

my_cusor.execute('SHOW DATABASES')

for db in my_cusor:
    print(db)