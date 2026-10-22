// Shree Shree 108 Buri Kali Mandir - Client Script

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Menu Toggle
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    
    if (mobileBtn && mobileMenu) {
        mobileBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // 2. Dynamic Aarti Status Calculation (Indian Standard Time)
    updateAartiStatus();
    setInterval(updateAartiStatus, 60000); // refresh every minute

    function updateAartiStatus() {
        const el = document.getElementById('currentAartiStatus');
        if (!el) return;

        const now = new Date();
        const currentHours = now.getHours();
        const currentMinutes = now.getMinutes();
        const timeVal = currentHours * 60 + currentMinutes;

        // Times in minutes:
        // 05:30 (330) - Mandir Opens
        // 06:00 (360) - Mangala Aarti
        // 12:00 (720) - Bhog Aarti
        // 12:30 (750) - Afternoon Rest / Gates Close
        // 16:30 (990) - Evening Gates Open
        // 19:00 (1140) - Sandhya Maha Aarti
        // 21:15 (1275) - Shayan Aarti
        // 21:30 (1290) - Mandir Closes

        if (timeVal >= 330 && timeVal < 360) {
            el.innerHTML = '<span class="text-yellow-300 animate-pulse">●</span> प्रातः कपाट खुले | मंगला आरती शीघ्र (06:00 AM)';
        } else if (timeVal >= 360 && timeVal < 390) {
            el.innerHTML = '<span class="text-yellow-300 font-bold animate-ping">🔔</span> पावन मंगला आरती चल रही है';
        } else if (timeVal >= 720 && timeVal < 750) {
            el.innerHTML = '<span class="text-amber-300 font-bold">🙏</span> मध्याह्न भोग आरती जारी है (12:00 PM)';
        } else if (timeVal >= 750 && timeVal < 990) {
            el.innerHTML = '<span>⏸</span> मध्याह्न विश्राम काल | सायं कपाट 04:30 PM पर खुलेंगे';
        } else if (timeVal >= 1140 && timeVal < 1170) {
            el.innerHTML = '<span class="text-yellow-300 font-bold animate-bounce">🔔</span> भव्य संध्या महाआरती चल रही है';
        } else if (timeVal >= 1275 && timeVal < 1290) {
            el.innerHTML = '<span class="text-yellow-300">🌙</span> शयन आरती जारी है (09:15 PM)';
        } else if (timeVal >= 1290 || timeVal < 330) {
            el.innerHTML = '<span>🌙</span> मंदिर कपाट बंद | प्रातः 05:30 बजे खुलेंगे';
        } else {
            el.innerHTML = '<span class="text-emerald-400">●</span> पावन दर्शन चालू है';
        }
    }
});

// Helper: Copy to Clipboard
function copyToClipboard(text, successMsg = "कॉपी हो गया!") {
    navigator.clipboard.writeText(text).then(() => {
        showToast(successMsg);
    }).catch(err => {
        console.error('Copy failed', err);
    });
}

// Helper: Toast Notification
function showToast(message, type = "success") {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-5 right-5 z-50 px-5 py-3 rounded-xl shadow-2xl text-white font-medium text-sm flex items-center gap-2 transform transition-all duration-300 translate-y-10 opacity-0 ${
        type === 'success' ? 'bg-emerald-600' : 'bg-red-600'
    }`;
    toast.innerHTML = `<i class="fa-solid fa-check-circle"></i> <span>${message}</span>`;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove('translate-y-10', 'opacity-0');
    }, 50);

    setTimeout(() => {
        toast.classList.add('translate-y-10', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
