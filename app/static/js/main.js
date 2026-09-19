document.addEventListener('DOMContentLoaded', () => {
    // Mobile Drawer Navigation
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const closeDrawerBtn = document.getElementById('closeDrawerBtn');
    const mobileDrawer = document.getElementById('mobileDrawer');
    const drawerContent = document.getElementById('drawerContent');

    window.openDrawer = function() {
        if (!mobileDrawer) return;
        mobileDrawer.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        requestAnimationFrame(() => {
            if (drawerContent) {
                drawerContent.classList.remove('-translate-x-full');
            }
        });
    };

    window.closeDrawer = function() {
        if (!mobileDrawer) return;
        if (drawerContent) {
            drawerContent.classList.add('-translate-x-full');
        }
        document.body.style.overflow = '';
        setTimeout(() => {
            mobileDrawer.classList.add('hidden');
        }, 300);
    };

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', openDrawer);
    }
    if (closeDrawerBtn) {
        closeDrawerBtn.addEventListener('click', closeDrawer);
    }
    if (mobileDrawer) {
        mobileDrawer.addEventListener('click', (e) => {
            if (e.target === mobileDrawer) {
                closeDrawer();
            }
        });
    }

    // Mobile Search Toggle
    const searchToggleBtn = document.getElementById('mobileSearchToggleBtn');
    const searchCollapse = document.getElementById('mobileSearchCollapse');
    if (searchToggleBtn && searchCollapse) {
        searchToggleBtn.addEventListener('click', () => {
            searchCollapse.classList.toggle('hidden');
            if (!searchCollapse.classList.contains('hidden')) {
                const input = searchCollapse.querySelector('input');
                if (input) input.focus();
            }
        });
    }
});

// 클립보드 복사 함수
function copyToClipboard(text, successMsg) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            alert(successMsg || '복사되었습니다: ' + text);
        }).catch(() => {
            fallbackCopy(text, successMsg);
        });
    } else {
        fallbackCopy(text, successMsg);
    }
}

function fallbackCopy(text, successMsg) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        document.execCommand('copy');
        alert(successMsg || '복사되었습니다: ' + text);
    } catch (err) {
        prompt('아래 내용을 복사하세요 (Ctrl+C):', text);
    }
    document.body.removeChild(textArea);
}
