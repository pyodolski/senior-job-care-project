from models import db, Resume, Certificate
from utils.files_handler import upload_file, delete_file
from sqlalchemy.orm import selectinload


class ResumeService:

    #  이력서 생성
    @staticmethod
    def create_resume(user_id, resume_data, certificate_names, certificate_images):
        """새로운 이력서 생성 """
        resume = Resume(user_id=user_id)
        db.session.add(resume)

        for key, value in resume_data.items():
            if hasattr(resume, key):
                setattr(resume, key, value)

        # 자격증 추가
        if certificate_names and certificate_images:
            for name, image_file in zip(certificate_names, certificate_images):
                if name.strip() and image_file and image_file.filename:
                    image_url = upload_file(file=image_file, sub_path='certificates')
                    if image_url:
                        new_cert = Certificate(name=name.strip(), image_url=image_url, resume=resume)
                        db.session.add(new_cert)

        try:
            db.session.commit()
            return resume
        except Exception as e:
            db.session.rollback()
            print(f"이력서 생성 중 오류 발생: {e}")
            return None

    #  이력서 수정
    @staticmethod
    def update_resume(resume_id, user_id, resume_data, certificate_names, certificate_images):
        """ 이력서 수정 """
        resume = Resume.query.options(selectinload(Resume.certificates)) \
            .filter_by(id=resume_id, user_id=user_id).first()

        if not resume:
            return None

        for key, value in resume_data.items():
            if hasattr(resume, key):
                setattr(resume, key, value)

        # 새 자격증 추가
        if certificate_names and certificate_images:
            for name, image_file in zip(certificate_names, certificate_images):
                if name.strip() and image_file and image_file.filename:
                    image_url = upload_file(file=image_file, sub_path='certificates')
                    if image_url:
                        new_cert = Certificate(name=name.strip(), image_url=image_url, resume=resume)
                        db.session.add(new_cert)

        try:
            db.session.commit()
            return resume
        except Exception as e:
            db.session.rollback()
            print(f"이력서 업데이트 중 오류 발생: {e}")
            return None

    #  자격증 삭제
    @staticmethod
    def delete_certificate(user_id, cert_id):
        """자격증 삭제 S3 파일 먼저 삭제 하고 DB도 삭제"""
        cert_to_delete = Certificate.query.get(cert_id)

        if cert_to_delete and cert_to_delete.resume and cert_to_delete.resume.user_id == user_id:
            try:
                # S3에서 파일 삭제
                s3_delete_successful = delete_file(cert_to_delete.image_url)
                if not s3_delete_successful:
                    print(f"S3 파일 삭제 실패로 DB 작업을 중단합니다: {cert_to_delete.image_url}")
                    return False

                # DB에서 삭제
                db.session.delete(cert_to_delete)
                db.session.commit()
                return True
            except Exception as e:
                db.session.rollback()
                print(f"자격증 DB 삭제 중 오류 발생: {e}")
                return False

        return False

    # 이력서 조회
    @staticmethod
    def get_resumes_by_user(user_id):
        """특정 사용자의 모든 이력서 조회 """
        return Resume.query.filter_by(user_id=user_id) \
            .order_by(Resume.updated_at.desc()) \
            .all()

    #  이력서 조회 단일
    @staticmethod
    def get_resume_by_id(resume_id):
        """특정 이력서 ID로 조회 """
        return Resume.query.options(selectinload(Resume.certificates)).get(resume_id)

    @staticmethod
    def get_resume_permission_check(resume_id, user_id):
        """ 이력서 조회 및 권한 확인"""
        resume = Resume.query.get(resume_id)

        if not resume:
            return None, False

        is_owner = (resume.user_id == user_id)

        return resume, is_owner

    #  이력서 삭제
    @staticmethod
    def delete_resume(resume_id, user_id):
        """ 이력서 삭제 """
        resume = Resume.query.options(selectinload(Resume.certificates)).get(resume_id)

        if not resume:
            return False

        if resume.user_id != user_id:
            return False

        try:
            # S3에서 모든 자격증 이미지 삭제
            for certificate in resume.certificates:
                if certificate.image_url:
                    s3_delete_successful = delete_file(certificate.image_url)
                    if not s3_delete_successful:
                        print(f"S3 파일 삭제 실패: {certificate.image_url}")

            # DB에서 삭제
            db.session.delete(resume)
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"이력서 삭제 중 오류: {e}")
            return False

    # 공개/비공개 토글
    @staticmethod
    def toggle_resume_public(resume_id, user_id, is_public):
        """ 이력서 공개/비공개 토글 """
        resume = Resume.query.get(resume_id)

        if not resume:
            return False

        if resume.user_id != user_id:
            return False

        try:
            resume.is_public = is_public
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"이력서 공개 상태 변경 중 오류: {e}")
            return False

    # 이력서 개수 조회
    @staticmethod
    def get_resume_count_by_user(user_id):
        """ 특정 사용자의 이력서 개수를 조회 """
        return Resume.query.filter_by(user_id=user_id).count()

    # 공개 이력서 목록
    @staticmethod
    def get_public_resumes_paginated(page, per_page=5):
        """ 공개 설정된 모든 이력서를 페이지별로 조회 (기업회원용)"""
        pagination = Resume.query.options(selectinload(Resume.user)) \
            .filter_by(is_public=True) \
            .order_by(Resume.updated_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        return pagination
