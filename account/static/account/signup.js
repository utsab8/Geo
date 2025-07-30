document.addEventListener('DOMContentLoaded', function() {
    const signupForm = document.getElementById('signupForm');
    const errorDiv = document.getElementById('signupError');
    const submitBtn = signupForm.querySelector('.submit-btn');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    
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
    
    function validatePassword(password) {
        // Simple password validation - just check if it's not empty and has minimum length
        return password.length >= 6;
    }
    
    function validateForm() {
        const fullName = document.getElementById('full_name').value.trim();
        const email = document.getElementById('email').value.trim();
        const phoneNumber = document.getElementById('phone_number').value.trim();
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        const terms = document.getElementById('terms').checked;
        
        if (!fullName) {
            showError('Please enter your full name.');
            return false;
        }
        
        if (!isValidEmail(email)) {
            showError('Please enter a valid email address.');
            return false;
        }
        
        if (!phoneNumber) {
            showError('Please enter your phone number.');
            return false;
        }
        
        if (!password || password.length < 6) {
            showError('Password must be at least 6 characters long.');
            return false;
        }
        
        if (password !== confirmPassword) {
            showError('Passwords do not match.');
            return false;
        }
        
        if (!terms) {
            showError('Please accept the Terms of Service and Privacy Policy.');
            return false;
        }
        
        return true;
    }

    signupForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        hideError();

        if (!validateForm()) {
            return;
        }

        showLoading();

        const formData = {
            full_name: document.getElementById('full_name').value.trim(),
            email: document.getElementById('email').value.trim(),
            phone_number: document.getElementById('phone_number').value.trim(),
            password: passwordInput.value,
            confirm_password: confirmPasswordInput.value,
            newsletter: document.getElementById('newsletter').checked
        };

        try {
            const response = await fetch('/api/account/signup/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Success animation
                submitBtn.innerHTML = '<span class="btn-text">✓ Account Created!</span>';
                submitBtn.style.background = 'linear-gradient(135deg, #27ae60, #2ecc71)';
                
                // Store tokens if provided
                if (data.access && data.refresh) {
                    localStorage.setItem('access', data.access);
                    localStorage.setItem('refresh', data.refresh);
                }
                
                // Redirect to login or dashboard
                setTimeout(() => {
                    window.location.href = '/api/account/login-page/';
                }, 1500);
            } else {
                hideLoading();
                let errorMessage = 'Signup failed. Please try again.';
                
                if (data.email) {
                    errorMessage = data.email[0];
                } else if (data.password) {
                    errorMessage = data.password[0];
                } else if (data.non_field_errors) {
                    errorMessage = data.non_field_errors[0];
                } else if (data.detail) {
                    errorMessage = data.detail;
                }
                
                showError(errorMessage);
                
                // Shake animation for error
                signupForm.style.animation = 'shake 0.5s ease-in-out';
                setTimeout(() => {
                    signupForm.style.animation = '';
                }, 500);
            }
        } catch (err) {
            hideLoading();
            showError('Network error. Please check your connection and try again.');
        }
    });
    

    
    // Confirm password validation
    confirmPasswordInput.addEventListener('input', function() {
        if (this.value && this.value !== passwordInput.value) {
            this.style.borderColor = '#e74c3c';
        } else {
            this.style.borderColor = '';
        }
        hideError();
    });
    
    // Input focus effects and validation
    const inputs = signupForm.querySelectorAll('input');
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
                    showError(`${provider.charAt(0).toUpperCase() + provider.slice(1)} signup is not yet implemented.`);
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
    
    .password-strength-container {
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .password-strength-container.show {
        opacity: 1;
    }
`;
document.head.appendChild(style); 