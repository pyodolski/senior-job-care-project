from datetime import datetime
import re

def format_date(date_obj, format_str='%Y-%m-%d'):
    """날짜 포맷팅"""
    if not date_obj:
        return ''
    return date_obj.strftime(format_str)

def format_datetime(datetime_obj, format_str='%Y-%m-%d %H:%M'):
    """날짜시간 포맷팅"""
    if not datetime_obj:
        return ''
    return datetime_obj.strftime(format_str)

def format_salary(salary):
    """급여 포맷팅"""
    if not salary:
        return '급여 협의'
    return salary

def format_phone(phone):
    """전화번호 포맷팅"""
    if not phone:
        return ''
    
    # 숫자만 추출
    numbers = re.sub(r'[^\d]', '', phone)
    
    if len(numbers) == 11:
        return f"{numbers[:3]}-{numbers[3:7]}-{numbers[7:]}"
    elif len(numbers) == 10:
        return f"{numbers[:3]}-{numbers[3:6]}-{numbers[6:]}"
    else:
        return phone

def truncate_text(text, length=100):
    """텍스트 자르기"""
    if not text:
        return ''
    
    if len(text) <= length:
        return text
    
    return text[:length] + '...'

def get_work_days(job):
    """근무 요일 문자열 생성"""
    days = []
    day_mapping = {
        'work_monday': '월',
        'work_tuesday': '화',
        'work_wednesday': '수',
        'work_thursday': '목',
        'work_friday': '금',
        'work_saturday': '토',
        'work_sunday': '일'
    }
    
    for field, day in day_mapping.items():
        if getattr(job, field, False):
            days.append(day)
    
    return ', '.join(days) if days else '협의'

def calculate_time_ago(datetime_obj):
    """상대적 시간 계산 (예: 2시간 전, 3일 전)"""
    if not datetime_obj:
        return ''

    from datetime import timezone, timedelta

    # KST (UTC+9)
    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST)

    # datetime_obj가 timezone aware가 아니면 KST로 설정
    if datetime_obj.tzinfo is None:
        datetime_obj = datetime_obj.replace(tzinfo=KST)

    diff = now - datetime_obj

    seconds = diff.total_seconds()
    minutes = seconds / 60
    hours = minutes / 60
    days = diff.days
    months = days / 30
    years = days / 365

    if minutes < 1:
        return "방금 전"
    elif minutes < 60:
        return f"{int(minutes)}분 전"
    elif hours < 24:
        return f"{int(hours)}시간 전"
    elif days < 30:
        return f"{int(days)}일 전"
    elif days < 365:
        return f"{int(months)}개월 전"
    else:
        return f"{int(years)}년 전"

def validate_email(email):
    """이메일 유효성 검사"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """전화번호 유효성 검사"""
    if not phone:
        return False
    
    # 숫자만 추출
    numbers = re.sub(r'[^\d]', '', phone)
    return len(numbers) in [10, 11]