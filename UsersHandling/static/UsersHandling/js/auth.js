document.addEventListener('DOMContentLoaded', () => {
    const formSlider = document.getElementById('formSlider');
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const ownerForm = document.getElementById('owner-form');
    const loginBtn = document.getElementById('login-btn');
    const signupBtn = document.getElementById('signup-btn');
    const ownerBtn = document.getElementById('owner-btn');
    const formViewport = document.querySelector('.form-slider-viewport');
    
    let currentMode = 'login';
    let loginHeight = 0;
    let signupHeight = 0;

    function calculateFormHeights() {
        loginHeight = loginForm.offsetHeight;
        signupHeight = signupForm.offsetHeight;

        if (currentMode === 'login') formViewport.style.height = loginHeight + 'px';
        else if (currentMode === 'signup') formViewport.style.height = signupHeight + 'px';
        else if (currentMode === 'owner' && ownerForm) formViewport.style.height = ownerForm.scrollHeight + 'px';
    }

    // Initialize heights immediately and on load to catch slow-rendering elements
    calculateFormHeights();
    window.addEventListener('load', calculateFormHeights);

    // File upload label update
    const fileInput = document.getElementById('profile-image');
    const fileLabel = document.querySelector('label[for="profile-image"]');
    if (fileInput && fileLabel) {
        fileInput.addEventListener('change', (e) => {
            fileLabel.textContent = e.target.files.length > 0
                ? "Selected: " + e.target.files[0].name
                : "Upload Profile Picture";
            calculateFormHeights();
        });
    }

    function switchMode(newMode) {
        // Force a recalculation if we are switching and heights look suspicious
        if (loginHeight === 0 || signupHeight === 0) calculateFormHeights();

        // Reset visibility
        formSlider.style.display = '';
        if (ownerForm) ownerForm.style.display = 'none';

        if (newMode === 'owner') {
            formSlider.style.display = 'none';
            if (ownerForm) {
                ownerForm.style.display = 'block';
                formViewport.style.height = ownerForm.scrollHeight + 'px';
            }
        } else if (newMode === 'signup') {
            formSlider.style.transform = `translateY(-${loginHeight}px)`;
            formViewport.style.height = signupHeight + 'px';
        } else {
            formSlider.style.transform = 'translateY(0)';
            formViewport.style.height = loginHeight + 'px';
        }

        if (document.activeElement) document.activeElement.blur();

        loginBtn.classList.toggle('active', newMode === 'login');
        signupBtn.classList.toggle('active', newMode === 'signup');
        if (ownerBtn) ownerBtn.classList.toggle('active', newMode === 'owner');

        currentMode = newMode;
    }

    loginBtn.addEventListener('click', () => switchMode('login'));
    signupBtn.addEventListener('click', () => switchMode('signup'));
    if (ownerBtn) ownerBtn.addEventListener('click', () => switchMode('owner'));

    // 1. Password Real-time Validation
    const passwordInputs = document.querySelectorAll('.password-input');
    
    passwordInputs.forEach(input => {
        const requirementsDiv = input.closest('form').querySelector('.password-requirements');
        if (!requirementsDiv) return;

        input.addEventListener('input', () => {
            const val = input.value;
            const criteria = {
                length: val.length >= 8,
                upper: /[A-Z]/.test(val),
                lower: /[a-z]/.test(val),
                number: /[0-9]/.test(val)
            };

            for (const [criterion, met] of Object.entries(criteria)) {
                const reqEl = requirementsDiv.querySelector(`[data-criterion="${criterion}"]`);
                if (reqEl) {
                    reqEl.classList.toggle('met', met);
                    const icon = reqEl.querySelector('i');
                    if (icon) {
                        icon.className = met ? 'fas fa-check-circle' : 'fas fa-circle';
                    }
                }
            }
        });
    });

    // 2. Tab initialization and persistence
    const initAuthMode = () => {
        const mode = (typeof INITIAL_MODE !== 'undefined' && INITIAL_MODE) || 
                     (new URLSearchParams(window.location.search)).get('mode') || 
                     'login';
        
        // Ensure heights are calculated before switching
        calculateFormHeights();
        if (loginHeight === 0 || signupHeight === 0) {
            // If still 0, retry in a bit
            setTimeout(initAuthMode, 50);
            return;
        }
        
        switchMode(mode);
    };

    // Run initialization with a few attempts to ensure forms are rendered
    initAuthMode();
    setTimeout(initAuthMode, 150); // Second pass for stability

    // Final insurance for height on dynamic content
    window.addEventListener('resize', calculateFormHeights);
});