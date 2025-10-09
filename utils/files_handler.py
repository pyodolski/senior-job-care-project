import boto3
from flask import current_app
import uuid
from werkzeug.utils import secure_filename
from urllib.parse import urlparse

def upload_file(file, sub_path):
    """AWS S3에 파일 업로드 후 파일 URL 반환"""
    if not file or not file.filename:
        return None

    s3 = boto3.client(
        "s3",
        aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
        region_name=current_app.config["AWS_S3_REGION"]
    )

    filename = secure_filename(file.filename)
    unique_filename = f"{sub_path}/{uuid.uuid4().hex}_{filename}"

    try:
        s3.upload_fileobj(
            file,
            current_app.config["AWS_S3_BUCKET_NAME"],
            unique_filename,
            ExtraArgs={"ContentType": file.content_type}
        )
        bucket = current_app.config["AWS_S3_BUCKET_NAME"]
        region = current_app.config["AWS_S3_REGION"]
        return f"https://{bucket}.s3.{region}.amazonaws.com/{unique_filename}"
    except Exception as e:
        print(f"S3 파일 업로드 실패: {e}")
        return None


def delete_file(file_url):
    """
    AWS S3에 업로드된 파일을 전체 URL을 기반으로 삭제합니다.
    URL을 파싱하여 정확한 S3 객체 키를 추출합니다.
    """
    if not file_url:
        print("삭제할 파일 URL이 없습니다.")
        return False

    try:
        # S3 클라이언트 생성
        s3 = boto3.client(
            "s3",
            aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
            region_name=current_app.config["AWS_S3_REGION"]
        )
        bucket_name = current_app.config['AWS_S3_BUCKET_NAME']

        # ★★★★★ URL에서 S3 객체 키(Key)를 정확하게 추출하는 핵심 로직 ★★★★★
        parsed_url = urlparse(file_url)
        file_key = parsed_url.path.lstrip('/')  # URL 경로의 맨 앞 '/'를 제거

        # --- 디버깅을 위한 로그 출력 ---
        print(f"삭제 요청 URL: {file_url}")
        print(f"추출된 버킷: {bucket_name}, 추출된 키: {file_key}")
        # -----------------------------

        # Boto3의 delete_object API를 호출하여 파일을 삭제
        s3.delete_object(
            Bucket=bucket_name,
            Key=file_key
        )

        print(f"S3에서 파일 삭제 성공: {file_key}")
        return True

    except Exception as e:
        # 실패 시, 터미널에 정확한 오류 메시지를 출력
        print(f"S3 파일 삭제 실패: {e}")
        return False

def generate_presigned_get_url(key, expires=900):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
        region_name=current_app.config["AWS_S3_REGION"]
    )
    return s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': current_app.config["AWS_S3_BUCKET_NAME"],
            'Key': key
        },
        ExpiresIn=expires
    )