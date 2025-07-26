/**
 * 온보딩 관련 CSS 스타일
 */
export const onboardingStyles = `
<style>
.save-status {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 10px 15px;
    border-radius: 5px;
    font-size: 14px;
    font-weight: 500;
    z-index: 1000;
    display: none;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
}

.save-status.success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.save-status.error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.save-status.warning {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
}

.save-status.info {
    background-color: #d1ecf1;
    color: #0c5460;
    border: 1px solid #bee5eb;
}

/* 입력 필드 검증 상태 스타일 */
.step-input {
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.step-input.valid {
    border-color: #28a745;
    box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25);
}

.step-input.invalid {
    border-color: #dc3545;
    box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
}

.step-input.checking {
    border-color: #ffc107;
    box-shadow: 0 0 0 0.2rem rgba(255, 193, 7, 0.25);
}

.step-input.error {
    border-color: #dc3545;
    box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
}

/* 검증 메시지 스타일 개선 */
.validation-message {
    margin-top: 8px;
    font-size: 14px;
    padding: 8px 12px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    transition: all 0.3s ease;
}

.validation-message.error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.validation-message.success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.validation-message.loading {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
}

/* 로딩 스피너 */
.loading-spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid #f3f3f3;
    border-top: 2px solid #856404;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-right: 8px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* 성별 버튼 스타일 */
.gender-btn {
    transition: all 0.3s ease;
    margin: 0 10px;
    padding: 12px 24px;
    border: 2px solid #dee2e6;
    background-color: white;
    border-radius: 8px;
    cursor: pointer;
}

.gender-btn:hover {
    border-color: #007bff;
    background-color: #f8f9fa;
}

.gender-btn.selected {
    background-color: #007bff;
    color: white;
    border-color: #007bff;
    transform: scale(1.05);
}

/* 단계 전환 애니메이션 */
.step-container.hidden {
    display: none;
}

.step-container.active {
    display: block;
    animation: fadeIn 0.3s ease-in-out;
}

.step-container.completed {
    opacity: 0.7;
    transform: scale(0.98);
    transition: all 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* 진행률 바 스타일 */
.progress-fill {
    transition: width 0.5s ease;
    background: linear-gradient(90deg, #007bff, #0056b3);
}

.step-indicator {
    transition: all 0.3s ease;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    border: 2px solid #dee2e6;
    background-color: white;
    color: #6c757d;
}

.step-indicator.completed {
    background-color: #28a745;
    color: white;
    border-color: #28a745;
    transform: scale(1.1);
}

.step-indicator.current {
    background-color: #007bff;
    color: white;
    border-color: #007bff;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(0, 123, 255, 0); }
    100% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0); }
}

/* 완료된 단계 요약 스타일 */
.completed-steps-summary {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 20px;
}

.summary-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #dee2e6;
}

.summary-item:last-child {
    border-bottom: none;
}

.summary-item .label {
    font-weight: 600;
    color: #495057;
}

.summary-item .value {
    color: #007bff;
    font-weight: 500;
}

.edit-btn {
    background: none;
    border: 1px solid #007bff;
    color: #007bff;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.edit-btn:hover {
    background-color: #007bff;
    color: white;
}
</style>
`;
