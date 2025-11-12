# cli.py

from flask import current_app
from models import db, User
import bcrypt
import click
from flask.cli import with_appcontext


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
        # 관리자는 추가정보 없이 기본값으로 설정
        from datetime import date
        admin_user = User(
            username=username,
            password=hashed_pw.decode("utf-8"),
            nickname="관리자",
            name="관리자",
            gender="male",
            birth_date=date(1970, 1, 1),
            sido="서울특별시",
            sigungu="중구",
            dong="중구",
            phone="010-0000-0000",
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
        from scripts.fetch_senior_jobs import fetch_and_store_jobs
        print(f"🚀 {page} 페이지의 채용 공고를 가져옵니다...")

        # fetch_and_store_jobs 함수에 page 파라미터를 넘겨줍니다.
        fetch_and_store_jobs(page_number=page)

        print(">> 작업이 완료되었습니다.")

    @app.cli.command("db-query")
    @click.argument('query')
    @with_appcontext
    def db_query_command(query):
        """데이터베이스 쿼리를 실행합니다."""
        from sqlalchemy import text
        try:
            result = db.session.execute(text(query))
            
            # SELECT 쿼리인 경우 결과 출력
            if query.strip().upper().startswith('SELECT'):
                rows = result.fetchall()
                if rows:
                    # 컬럼 이름 출력
                    columns = result.keys()
                    click.echo("\n" + " | ".join(columns))
                    click.echo("-" * (len(" | ".join(columns))))
                    
                    # 데이터 출력
                    for row in rows:
                        click.echo(" | ".join(str(val) for val in row))
                    click.echo(f"\n총 {len(rows)}개의 결과")
                else:
                    click.echo("결과가 없습니다.")
            else:
                db.session.commit()
                click.echo("쿼리가 실행되었습니다.")
        except Exception as e:
            db.session.rollback()
            click.echo(f"에러 발생: {str(e)}", err=True)

    @app.cli.command("db-tables")
    @with_appcontext
    def db_tables_command():
        """데이터베이스의 모든 테이블 목록을 표시합니다."""
        from sqlalchemy import text
        try:
            result = db.session.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            
            click.echo("\n📊 데이터베이스 테이블 목록:")
            click.echo("-" * 40)
            for table in tables:
                click.echo(f"  • {table}")
            click.echo(f"\n총 {len(tables)}개의 테이블")
        except Exception as e:
            click.echo(f"에러 발생: {str(e)}", err=True)

    @app.cli.command("db-count")
    @click.argument('table')
    @with_appcontext
    def db_count_command(table):
        """특정 테이블의 레코드 수를 확인합니다."""
        from sqlalchemy import text
        try:
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            click.echo(f"\n📊 {table} 테이블: {count}개의 레코드")
        except Exception as e:
            click.echo(f"에러 발생: {str(e)}", err=True)