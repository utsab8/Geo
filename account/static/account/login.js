document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const errorDiv = document.getElementById('loginError');
    const submitBtn = loginForm.querySelector('.submit-btn');
    
    // Initialize floating labels
    initializeFloatingLabels();
    
    // Initialize password toggles
    initializePasswordToggles();
    
    // Initialize social login buttons
    initializeSocialLogin();
    
    function showLoading() {
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
    }
    
    function hideLoading() {
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
    }
    
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.add('show');
        setTimeout(() => {
            errorDiv.classList.remove('show');
        }, 5000);
    }
    
    function hideError() {
        errorDiv.classList.remove('show');
    }

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const remember = document.getElementById('remember') ? document.getElementById('remember').checked : false;
        
        hideError();

        // Validation
        if (!email || !password) {
            showError('Please fill in all fields.');
            return;
        }
        
        if (!isValidEmail(email)) {
            showError('Please enter a valid email address.');
            return;
        }

        showLoading();

        try {
            const response = await fetch('/api/account/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ 
                    email, 
                    password, 
                    remember_me: remember 
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Store JWT tokens
                if (data.access) {
                    localStorage.setItem('access', data.access);
                }
                if (data.refresh) {
                    localStorage.setItem('refresh', data.refresh);
                }
                
                // Success animation
                submitBtn.innerHTML = '<span class="btn-text">✓ Success!</span>';
                submitBtn.style.background = 'linear-gradient(135deg, #27ae60, #2ecc71)';
                
                // Redirect after a brief delay
                setTimeout(() => {
                    window.location.href = data.redirect_url || '/dashboard/';
                }, 1000);
            } else {
                hideLoading();
                const errorMessage = data.detail || data.non_field_errors || data.email || data.password || 'Login failed. Please check your credentials.';
                showError(errorMessage);
                
                // Shake animation for error
                loginForm.style.animation = 'shake 0.5s ease-in-out';
                setTimeout(() => {
                    loginForm.style.animation = '';
                }, 500);
            }
        } catch (err) {
            hideLoading();
            showError('Network error. Please check your connection and try again.');
        }
    });
    
    // Input focus effects and validation
    const inputs = loginForm.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
        
        // Auto-hide error when user starts typing
        input.addEventListener('input', hideError);
        
        // Real-time validation
        if (input.type === 'email') {
            input.addEventListener('blur', function() {
                if (this.value && !isValidEmail(this.value)) {
                    this.style.borderColor = '#e74c3c';
                } else {
                    this.style.borderColor = '';
                }
            });
        }
    });
    
    // Initialize floating labels
    function initializeFloatingLabels() {
        const inputs = document.querySelectorAll('.input-wrapper input');
        inputs.forEach(input => {
            if (input.value) {
                input.classList.add('has-value');
            }
            
            input.addEventListener('input', function() {
                if (this.value) {
                    this.classList.add('has-value');
                } else {
                    this.classList.remove('has-value');
                }
            });
        });
    }
    
    // Initialize password toggles
    function initializePasswordToggles() {
        const passwordToggles = document.querySelectorAll('.password-toggle');
        passwordToggles.forEach(toggle => {
            toggle.addEventListener('click', function() {
                const input = this.parentElement.querySelector('input');
                const icon = this.querySelector('i');
                
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                } else {
                    input.type = 'password';
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                }
            });
        });
    }
    
    // Initialize social login buttons
    function initializeSocialLogin() {
        const socialButtons = document.querySelectorAll('.social-btn');
        socialButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const provider = this.classList.contains('google-btn') ? 'google' : 'github';
                
                // Show loading state
                this.innerHTML = '<div class="spinner"></div> Connecting...';
                this.disabled = true;
                
                // Simulate social login (replace with actual implementation)
                setTimeout(() => {
                    showError(`${provider.charAt(0).toUpperCase() + provider.slice(1)} login is not yet implemented.`);
                    this.innerHTML = `<i class="fab fa-${provider}"></i><span>${provider.charAt(0).toUpperCase() + provider.slice(1)}</span>`;
                    this.disabled = false;
                }, 2000);
            });
        });
    }
    
    // Email validation
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    // Get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});

// Global function for password toggle (for onclick attribute)
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const toggle = input.parentElement.querySelector('.password-toggle i');
    
    if (input.type === 'password') {
        input.type = 'text';
        toggle.classList.remove('fa-eye');
        toggle.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        toggle.classList.remove('fa-eye-slash');
        toggle.classList.add('fa-eye');
    }
}

// Add shake animation and enhanced styles
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    .input-wrapper.focused .input-icon {
        color: #667eea;
    }
    
    .input-wrapper input.has-value + .floating-label {
        transform: translateY(-24px) scale(0.85);
        color: #667eea;
    }
    
    .social-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
    
    .social-btn .spinner {
        width: 16px;
        height: 16px;
        border: 2px solid rgba(0, 0, 0, 0.3);
        border-top: 2px solid #333;
    }
`;
document.head.appendChild(style); 