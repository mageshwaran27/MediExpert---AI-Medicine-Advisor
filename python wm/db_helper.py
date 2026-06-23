import cx_Oracle

def get_connection():
    dsn = cx_Oracle.makedsn('localhost', 1521, service_name='XE')
    return cx_Oracle.connect(user='system', password='magesh123', dsn=dsn)
