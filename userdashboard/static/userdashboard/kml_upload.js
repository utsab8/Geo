// KML Upload Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('kmlFile');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadForm = document.getElementById('kmlUploadForm');
    const progressContainer = document.getElementById('progressContainer');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const fileInfo = document.getElementById('fileInfo');
    const fileDetails = document.getElementById('fileDetails');
    
    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    dropZone.addEventListener('drop', handleDrop, false);
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight(e) {
        dropZone.classList.add('dragover');
    }
    
    function unhighlight(e) {
        dropZone.classList.remove('dragover');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }
    
    function handleFileSelect(e) {
        const files = e.target.files;
        handleFiles(files);
    }
    
    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            validateAndDisplayFile(file);
        }
    }
    
    function validateAndDisplayFile(file) {
        // Validate file type
        if (!file.name.toLowerCase().endsWith('.kml')) {
            showToast('Please select a valid KML file.', 'error');
            return;
        }
        
        // Validate file size (50MB limit)
        const maxSize = 50 * 1024 * 1024; // 50MB in bytes
        if (file.size > maxSize) {
            showToast('File size must be less than 50MB.', 'error');
            return;
        }
        
        // Display file information
        displayFileInfo(file);
        
        // Enable upload button
        uploadBtn.disabled = false;
    }
    
    function displayFileInfo(file) {
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
        const lastModified = new Date(file.lastModified).toLocaleString();
        
        fileDetails.innerHTML = `
            <div class="file-detail">
                <div class="file-detail-icon">📄</div>
                <div class="file-detail-content">
                    <h5>File Name</h5>
                    <p>${file.name}</p>
                </div>
            </div>
            <div class="file-detail">
                <div class="file-detail-icon">💾</div>
                <div class="file-detail-content">
                    <h5>File Size</h5>
                    <p>${fileSizeMB} MB</p>
                </div>
            </div>
            <div class="file-detail">
                <div class="file-detail-icon">📅</div>
                <div class="file-detail-content">
                    <h5>Last Modified</h5>
                    <p>${lastModified}</p>
                </div>
            </div>
            <div class="file-detail">
                <div class="file-detail-icon">✅</div>
                <div class="file-detail-content">
                    <h5>Status</h5>
                    <p>Ready to Upload</p>
                </div>
            </div>
        `;
        
        fileInfo.style.display = 'block';
        fileInfo.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    // Form submission with progress
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(uploadForm);
        const file = fileInput.files[0];
        
        if (!file) {
            showToast('Please select a file to upload.', 'error');
            return;
        }
        
        // Show progress
        progressContainer.style.display = 'block';
        uploadBtn.disabled = true;
        
        // Update button text
        const btnText = uploadBtn.querySelector('.btn-text');
        const btnLoading = uploadBtn.querySelector('.btn-loading');
        btnText.style.display = 'none';
        btnLoading.style.display = 'inline';
        
        // Create XMLHttpRequest for upload with progress
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressFill.style.width = percentComplete + '%';
                progressText.textContent = `Uploading... ${Math.round(percentComplete)}%`;
            }
        });
        
        xhr.addEventListener('load', function() {
            if (xhr.status === 200) {
                progressFill.style.width = '100%';
                progressText.textContent = 'Processing KML file...';
                
                // Parse response
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        showToast('KML file uploaded successfully!', 'success');
                        setTimeout(() => {
                            window.location.href = response.redirect_url;
                        }, 1500);
                    } else {
                        showToast(response.error || 'Upload failed.', 'error');
                        resetUploadForm();
                    }
                } catch (e) {
                    // If response is not JSON, it's a redirect
                    window.location.href = xhr.responseURL;
                }
            } else {
                showToast('Upload failed. Please try again.', 'error');
                resetUploadForm();
            }
        });
        
        xhr.addEventListener('error', function() {
            showToast('Network error. Please check your connection.', 'error');
            resetUploadForm();
        });
        
        xhr.open('POST', uploadForm.action);
        xhr.send(formData);
    });
    
    function resetUploadForm() {
        progressContainer.style.display = 'none';
        uploadBtn.disabled = false;
        fileInfo.style.display = 'none';
        
        const btnText = uploadBtn.querySelector('.btn-text');
        const btnLoading = uploadBtn.querySelector('.btn-loading');
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
        
        fileInput.value = '';
        progressFill.style.width = '0%';
        progressText.textContent = 'Preparing upload...';
    }
    
    // Toast notification function
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 300px;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);
        
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    // Add typing effect to header
    const headerText = document.querySelector('.upload-header h2');
    if (headerText) {
        const originalText = headerText.textContent;
        headerText.textContent = '';
        
        let i = 0;
        const typeWriter = () => {
            if (i < originalText.length) {
                headerText.textContent += originalText.charAt(i);
                i++;
                setTimeout(typeWriter, 100);
            }
        };
        
        setTimeout(typeWriter, 500);
    }
    
    // Add hover effects to file details
    document.addEventListener('mouseover', function(e) {
        if (e.target.closest('.file-detail')) {
            e.target.closest('.file-detail').style.transform = 'translateY(-2px)';
        }
    });
    
    document.addEventListener('mouseout', function(e) {
        if (e.target.closest('.file-detail')) {
            e.target.closest('.file-detail').style.transform = 'translateY(0)';
        }
    });
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !uploadBtn.disabled) {
            uploadForm.dispatchEvent(new Event('submit'));
        }
    });
    
    console.log('KML Upload Page loaded successfully! 🎉');
}); 