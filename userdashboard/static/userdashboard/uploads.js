// Enhanced uploads page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add staggered animation to upload options
    const options = document.querySelectorAll('.upload-option');
    options.forEach((option, index) => {
        option.style.opacity = '0';
        option.style.transform = 'translateY(30px)';
        setTimeout(() => {
            option.style.transition = 'all 0.6s ease';
            option.style.opacity = '1';
            option.style.transform = 'translateY(0)';
        }, index * 200);
    });

    // Add hover effects for stat items
    const statItems = document.querySelectorAll('.stat-item');
    statItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 10px 20px rgba(0, 0, 0, 0.1)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'none';
        });
    });

    // Add typing effect to header
    const headerText = document.querySelector('.uploads-header h1');
    if (headerText) {
        const originalText = headerText.textContent;
        headerText.textContent = '';
        
        let charIndex = 0;
        const typeInterval = setInterval(() => {
            headerText.textContent += originalText[charIndex];
            charIndex++;
            if (charIndex >= originalText.length) {
                clearInterval(typeInterval);
            }
        }, 100);
    }

    // Add click handlers for upload options
    const uploadOptions = document.querySelectorAll('.upload-option');
    uploadOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            // Don't trigger if clicking on a link inside the option
            if (e.target.tagName === 'A') {
                return;
            }
            
            // Find the link inside this option and navigate to it
            const link = this.querySelector('a');
            if (link) {
                window.location.href = link.href;
            }
        });
    });

    // Add loading states for buttons
    const buttons = document.querySelectorAll('.upload-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Add loading state
            const originalText = this.textContent;
            this.textContent = 'Loading...';
            this.style.opacity = '0.7';
            this.style.pointerEvents = 'none';
            
            // Reset after a short delay (in case navigation doesn't happen)
            setTimeout(() => {
                this.textContent = originalText;
                this.style.opacity = '1';
                this.style.pointerEvents = 'auto';
            }, 2000);
        });
    });
});

// Utility function for drop areas (if needed in other templates)
function setupDropArea(dropAreaId, fileInputId) {
    const dropArea = document.getElementById(dropAreaId);
    const fileInput = document.getElementById(fileInputId);
    if (!dropArea || !fileInput) return;

    // Click to upload
    dropArea.addEventListener('click', function(e) {
        if (e.target.classList.contains('drop-click') || e.target.classList.contains('drop-area') || e.target.classList.contains('drop-text')) {
            fileInput.click();
        }
    });

    // Drag and drop
    dropArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropArea.classList.add('dragover');
    });
    dropArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        dropArea.classList.remove('dragover');
    });
    dropArea.addEventListener('drop', function(e) {
        e.preventDefault();
        dropArea.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            fileInput.dispatchEvent(new Event('change'));
        }
    });

    // Show selected file name
    fileInput.addEventListener('change', function() {
        let label = dropArea.querySelector('.file-selected');
        if (!label) {
            label = document.createElement('div');
            label.className = 'file-selected';
            dropArea.appendChild(label);
        }
        label.textContent = fileInput.files.length ? fileInput.files[0].name : '';
    });
} 