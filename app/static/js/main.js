document.addEventListener('DOMContentLoaded', () => {
    // Mobile Drawer Navigation
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const closeDrawerBtn = document.getElementById('closeDrawerBtn');
    const mobileDrawer = document.getElementById('mobileDrawer');

    if (mobileMenuBtn && mobileDrawer) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileDrawer.classList.remove('hidden');
        });
    }

    if (closeDrawerBtn && mobileDrawer) {
        closeDrawerBtn.addEventListener('click', () => {
            mobileDrawer.classList.add('hidden');
        });
    }

    if (mobileDrawer) {
        mobileDrawer.addEventListener('click', (e) => {
            if (e.target === mobileDrawer) {
                mobileDrawer.classList.add('hidden');
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
