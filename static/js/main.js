/**
 * Skillora — Main JavaScript
 * Minimal client-side enhancements
 */

document.addEventListener('DOMContentLoaded', function () {

    // ---- Flash message auto-dismiss and manual close ----
    const flashMessages = document.querySelectorAll('.flash');

    flashMessages.forEach(function (flash) {
        // Manual close button
        const closeBtn = flash.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function () {
                dismissFlash(flash);
            });
        }

        // Auto-dismiss after 5 seconds
        setTimeout(function () {
            dismissFlash(flash);
        }, 5000);
    });

    function dismissFlash(el) {
        if (!el || el.classList.contains('fade-out')) return;
        el.classList.add('fade-out');
        setTimeout(function () {
            el.remove();
        }, 300);
    }


    // ---- Mobile nav toggle ----
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function () {
            navLinks.classList.toggle('active');
        });

        // Close nav when clicking a link (mobile)
        navLinks.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                navLinks.classList.remove('active');
            });
        });
    }


    // ---- Registration: password match feedback ----
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        const password = document.getElementById('password');
        const confirm = document.getElementById('confirm_password');
        const hint = document.getElementById('passwordMatchHint');

        function checkMatch() {
            if (!confirm.value) {
                hint.textContent = '';
                hint.className = 'form-hint password-match-hint';
                return;
            }
            if (password.value === confirm.value) {
                hint.textContent = 'Passwords match ✓';
                hint.className = 'form-hint password-match-hint success';
            } else {
                hint.textContent = 'Passwords do not match';
                hint.className = 'form-hint password-match-hint error';
            }
        }

        if (password && confirm && hint) {
            password.addEventListener('input', checkMatch);
            confirm.addEventListener('input', checkMatch);
        }
    }

});
