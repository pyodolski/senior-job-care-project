let currentPage = window.initialPage;
const loadMoreBtn = document.getElementById('load-more-btn');

if (loadMoreBtn) {
    loadMoreBtn.addEventListener('click', async () => {
        currentPage++;
        loadMoreBtn.textContent = '불러오는 중...';
        loadMoreBtn.disabled = true;

        try {
            const response = await fetch(`/resume/api/resumes?page=${currentPage}`);
            const data = await response.json();
            if (data.html) {
                const container = document.getElementById('resume-container');
                container.insertAdjacentHTML('beforeend', data.html);
            }
            if (!data.has_next) {
                loadMoreBtn.style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading more resumes:', error);
        } finally {
            loadMoreBtn.textContent = '더 보기';
            loadMoreBtn.disabled = false;
        }
    });
}
