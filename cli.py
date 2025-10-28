# cli.py

from flask import current_app
from models import db, User
import bcrypt
import click
from flask.cli import with_appcontext
from scripts.fetch_senior_jobs import fetch_and_store_jobs

def register_cli(app):
    @app.cli.command("db-init")
    @with_appcontext
    def db_init():
        """Initializes the database and creates all tables."""
        db.create_all()
        click.echo("Database initialized and tables created.")

    @app.cli.command("create-admin")
    def create_admin():
        username = input("관리자 아이디: ")
        password = input("비밀번호: ")

        if User.query.filter_by(username=username).first():
            print("이미 존재하는 아이디입니다.")
            return

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        admin_user = User(
            username=username,
            password=hashed_pw.decode("utf-8"),
            nickname="관리자",
            user_type=2
        )
        db.session.add(admin_user)
        db.session.commit()
        print("관리자 계정이 생성되었습니다.")

    @app.cli.command("fetch-senior-jobs")
    @click.option('--page', default=1, type=int, help='가져올 페이지 번호')
    @with_appcontext
    def fetch_senior_jobs_command(page):
        """한국노인인력개발원 API에서 공고 데이터를 가져옵니다."""
        print(f"🚀 {page} 페이지의 채용 공고를 가져옵니다...")

        # fetch_and_store_jobs 함수에 page 파라미터를 넘겨줍니다.
        fetch_and_store_jobs(page_number=page)

        print(">> 작업이 완료되었습니다.")