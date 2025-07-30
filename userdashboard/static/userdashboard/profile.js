// ========================================
// ENHANCED PROFILE PAGE FUNCTIONALITY
// ========================================

class ProfileManager {
    constructor() {
        this.currentSection = 'profile-overview';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupSmoothScrolling();
        this.setupScrollAnimations();
        this.setupAvatarUpload();
        this.setupPasswordStrength();
        this.setupFormHandling();
        this.setupScrollToTop();
    }

    setupEventListeners() {
        // Navigation dots
        document.querySelectorAll('.nav-dot').forEach(dot => {
            dot.addEventListener('click', (e) => {
                const section = e.target.dataset.section;
                this.scrollToSection(section);
            });
        });

        // Avatar upload
        const avatarInput = document.getElementById('avatar-upload');
        if (avatarInput) {
            avatarInput.addEventListener('change', (e) => {
                this.handleAvatarUpload(e);
            });
        }

        // Form submissions
        this.setupFormSubmissions();

        // Password strength checker
        const newPasswordInput = document.getElementById('new_password');
        if (newPasswordInput) {
            newPasswordInput.addEventListener('input', (e) => {
                this.checkPasswordStrength(e.target.value);
            });
        }

        // Modal close events
        this.setupModalEvents();
    }

    setupSmoothScrolling() {
        // Smooth scroll to sections
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    setupScrollAnimations() {
        // Intersection Observer for scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    this.updateActiveNavDot(entry.target.id);
                }
            });
        }, observerOptions);

        // Observe all profile sections
        document.querySelectorAll('.profile-section-block').forEach(section => {
            observer.observe(section);
        });
    }

    setupAvatarUpload() {
        const avatarInput = document.getElementById('avatar-upload');
        const avatarPreview = document.getElementById('profile-avatar-preview');

        if (avatarInput && avatarPreview) {
            avatarInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    // Validate file
                    if (!this.validateImageFile(file)) {
                        this.showToast('Please select a valid image file (JPG, PNG, GIF) under 5MB.', 'error');
                        return;
                    }

                    // Preview image
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        avatarPreview.src = e.target.result;
                    };
                    reader.readAsDataURL(file);

                    // Upload avatar
                    this.uploadAvatar(file);
                }
            });
        }
    }

    handleAvatarUpload(e) {
        const file = e.target.files[0];
        if (file) {
            // Validate file
            if (!this.validateImageFile(file)) {
                this.showToast('Please select a valid image file (JPG, PNG, GIF) under 5MB.', 'error');
                return;
            }

            // Preview image
            const avatarPreview = document.getElementById('profile-avatar-preview');
            if (avatarPreview) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    avatarPreview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }

            // Upload avatar
            this.uploadAvatar(file);
        }
    }

    setupPasswordStrength() {
        const passwordInput = document.getElementById('new_password');
        const strengthIndicator = document.getElementById('password-strength');

        if (passwordInput && strengthIndicator) {
            passwordInput.addEventListener('input', (e) => {
                const strength = this.calculatePasswordStrength(e.target.value);
                this.updatePasswordStrengthIndicator(strengthIndicator, strength);
            });
        }
    }

    setupFormHandling() {
        // Auto-save functionality
        const forms = ['profile-form', 'social-form', 'settings-form'];
        forms.forEach(formId => {
            const form = document.getElementById(formId);
            if (form) {
                form.addEventListener('input', this.debounce(() => {
                    this.autoSaveForm(form);
                }, 1000));
            }
        });
    }

    setupFormSubmissions() {
        // Profile form
        const profileForm = document.getElementById('profile-form');
        if (profileForm) {
            profileForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitForm(profileForm, 'update_profile');
            });
        }

        // Social form
        const socialForm = document.getElementById('social-form');
        if (socialForm) {
            socialForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitForm(socialForm, 'update_social');
            });
        }

        // Settings form
        const settingsForm = document.getElementById('settings-form');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitForm(settingsForm, 'update_settings');
            });
        }

        // Password form
        const passwordForm = document.getElementById('password-form');
        if (passwordForm) {
            passwordForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitForm(passwordForm, 'change_password');
            });
        }

        // Delete form
        const deleteForm = document.getElementById('delete-form');
        if (deleteForm) {
            deleteForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitForm(deleteForm, 'delete_account');
            });
        }
    }

    setupModalEvents() {
        // Close modal when clicking outside
        const modals = document.querySelectorAll('.modal-overlay');
        modals.forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideModal(modal);
                }
            });
        });

        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideAllModals();
            }
        });
    }

    setupScrollToTop() {
        const scrollBtn = document.querySelector('.scroll-to-top');
        if (scrollBtn) {
            window.addEventListener('scroll', this.throttle(() => {
                if (window.pageYOffset > 300) {
                    scrollBtn.classList.add('visible');
                } else {
                    scrollBtn.classList.remove('visible');
                }
            }, 100));
        }
    }

    // Navigation Methods
    scrollToSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
            this.updateActiveNavDot(sectionId);
        }
    }

    updateActiveNavDot(sectionId) {
        document.querySelectorAll('.nav-dot').forEach(dot => {
            dot.classList.remove('active');
        });
        
        const activeDot = document.querySelector(`[data-section="${sectionId}"]`);
        if (activeDot) {
            activeDot.classList.add('active');
        }
    }

    // Form Handling Methods
    submitForm(form, action) {
        const formData = new FormData(form);
        formData.append('action', action);

        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"], .save-btn');
        if (submitBtn) {
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            submitBtn.disabled = true;

            fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            })
            .then(response => response.text())
            .then(() => {
                this.showToast('Changes saved successfully!', 'success');
                // Reload page to show updated data
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            })
            .catch(error => {
                console.error('Error:', error);
                this.showToast('Error saving changes. Please try again.', 'error');
            })
            .finally(() => {
                if (submitBtn) {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }
            });
        }
    }

    autoSaveForm(form) {
        // Auto-save functionality for better UX
        const formData = new FormData(form);
        const action = formData.get('action') || 'auto_save';

        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showToast('Auto-saved', 'info');
            }
        })
        .catch(error => {
            console.error('Auto-save error:', error);
        });
    }

    // Avatar Upload Methods
    validateImageFile(file) {
        const maxSize = 5 * 1024 * 1024; // 5MB
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];

        if (file.size > maxSize) {
            return false;
        }

        if (!allowedTypes.includes(file.type)) {
            return false;
        }

        return true;
    }

    uploadAvatar(file) {
        const formData = new FormData();
        formData.append('avatar', file);
        formData.append('action', 'upload_avatar');

        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        })
        .then(response => response.text())
        .then(() => {
            this.showToast('Profile picture updated successfully!', 'success');
        })
        .catch(error => {
            console.error('Upload error:', error);
            this.showToast('Error uploading image. Please try again.', 'error');
        });
    }

    // Password Strength Methods
    calculatePasswordStrength(password) {
        let score = 0;
        
        if (password.length >= 8) score += 1;
        if (/[a-z]/.test(password)) score += 1;
        if (/[A-Z]/.test(password)) score += 1;
        if (/[0-9]/.test(password)) score += 1;
        if (/[^A-Za-z0-9]/.test(password)) score += 1;
        
        if (score < 2) return 'weak';
        if (score < 3) return 'fair';
        if (score < 5) return 'good';
        return 'strong';
    }

    updatePasswordStrengthIndicator(indicator, strength) {
        indicator.className = `password-strength ${strength}`;
    }

    // Modal Methods
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }

    hideModal(modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }

    hideAllModals() {
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            this.hideModal(modal);
        });
    }

    // Utility Methods
    showToast(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;

        // Add to page
        document.body.appendChild(toast);

        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);

        // Auto remove
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// Global Functions for HTML onclick handlers
function saveProfile() {
    const form = document.getElementById('profile-form');
    if (form) {
        profileManager.submitForm(form, 'update_profile');
    }
}

function saveSocial() {
    const form = document.getElementById('social-form');
    if (form) {
        profileManager.submitForm(form, 'update_social');
    }
}

function saveSettings() {
    const form = document.getElementById('settings-form');
    if (form) {
        profileManager.submitForm(form, 'update_settings');
    }
}

function changePassword() {
    const form = document.getElementById('password-form');
    if (form) {
        profileManager.submitForm(form, 'change_password');
    }
}

function showDeleteConfirmation() {
    profileManager.showModal('deleteModal');
}

function hideDeleteConfirmation() {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        profileManager.hideModal(modal);
    }
}

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Initialize Profile Manager when DOM is loaded
let profileManager;
document.addEventListener('DOMContentLoaded', function() {
    profileManager = new ProfileManager();
    
    // Add CSS for toast notifications
    const style = document.createElement('style');
    style.textContent = `
        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border-radius: 8px;
            padding: 1rem 1.5rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            transform: translateX(100%);
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 10000;
            max-width: 300px;
        }
        
        .toast.show {
            transform: translateX(0);
            opacity: 1;
        }
        
        .toast-content {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .toast-success {
            border-left: 4px solid #28a745;
        }
        
        .toast-error {
            border-left: 4px solid #dc3545;
        }
        
        .toast-warning {
            border-left: 4px solid #ffc107;
        }
        
        .toast-info {
            border-left: 4px solid #17a2b8;
        }
        
        .toast i {
            font-size: 1.1rem;
        }
        
        .toast-success i {
            color: #28a745;
        }
        
        .toast-error i {
            color: #dc3545;
        }
        
        .toast-warning i {
            color: #ffc107;
        }
        
        .toast-info i {
            color: #17a2b8;
        }
    `;
    document.head.appendChild(style);
}); 