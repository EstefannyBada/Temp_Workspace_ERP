import getpass
import dj_database_url
import psycopg2

print("Consulta de usuarios de Render")
url = getpass.getpass("Pega la External Database URL: ")
config = dj_database_url.parse(url, ssl_require=True)
with psycopg2.connect(dbname=config["NAME"], user=config["USER"], password=config["PASSWORD"], host=config["HOST"], port=config["PORT"] or 5432, sslmode="require", connect_timeout=15) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT username, is_staff, is_superuser FROM auth_user ORDER BY username")
        for row in cur.fetchall():
            print(row)
