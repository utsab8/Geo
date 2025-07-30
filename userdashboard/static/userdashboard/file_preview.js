// File Preview Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    
    // Add staggered animation to file info items
    const fileInfoItems = document.querySelectorAll('.file-info-item');
    fileInfoItems.forEach((item, index) => {
        item.style.animationDelay = `${0.1 * index}s`;
    });
    
    // Add hover effects to coordinate items
    const coordinateItems = document.querySelectorAll('.coordinate-item');
    coordinateItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(8px) scale(1.02)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0) scale(1)';
        });
    });
    
    // Add table row hover effects
    const tableRows = document.querySelectorAll('.preview-table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'rgba(102, 126, 234, 0.08)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
    
    // Add button click animations
    const confirmBtn = document.querySelector('.confirm-btn');
    const rejectBtn = document.querySelector('.reject-btn');
    
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function(e) {
            // Add loading state
            const originalText = this.textContent;
            this.textContent = 'Processing...';
            this.disabled = true;
            
            // Add pulse animation
            this.style.animation = 'pulse 1s infinite';
            
            // Re-enable after a delay (in case of error)
            setTimeout(() => {
                this.textContent = originalText;
                this.disabled = false;
                this.style.animation = '';
            }, 5000);
        });
    }
    
    if (rejectBtn) {
        rejectBtn.addEventListener('click', function(e) {
            // Add confirmation dialog
            if (!confirm('Are you sure you want to cancel this upload? The file will be deleted.')) {
                e.preventDefault();
                return;
            }
            
            // Add loading state
            const originalText = this.textContent;
            this.textContent = 'Cancelling...';
            this.disabled = true;
        });
    }
    
    // Add typing effect to header
    const headerText = document.querySelector('.preview-header h2');
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
        
        // Start typing effect after a delay
        setTimeout(typeWriter, 500);
    }
    
    // Add scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe elements for scroll animations
    const animatedElements = document.querySelectorAll('.file-info-card, .preview-content');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // Add file type specific animations
    const fileType = document.querySelector('.file-info-item .file-info-content p');
    if (fileType) {
        const type = fileType.textContent.toLowerCase();
        
        // Add specific animations based on file type
        if (type.includes('kml')) {
            addMapAnimation();
        } else if (type.includes('csv')) {
            addDataAnimation();
        } else if (type.includes('shp')) {
            addShapeAnimation();
        }
    }
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && confirmBtn) {
            confirmBtn.click();
        } else if (e.key === 'Escape' && rejectBtn) {
            rejectBtn.click();
        }
    });
    
    // Add toast notifications
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
    
    // Add file type specific animations
    function addMapAnimation() {
        const mapIcon = document.querySelector('.file-info-icon');
        if (mapIcon) {
            mapIcon.style.animation = 'mapPulse 2s infinite';
        }
    }
    
    function addDataAnimation() {
        const dataIcon = document.querySelector('.file-info-icon');
        if (dataIcon) {
            dataIcon.style.animation = 'dataFlow 2s infinite';
        }
    }
    
    function addShapeAnimation() {
        const shapeIcon = document.querySelector('.file-info-icon');
        if (shapeIcon) {
            shapeIcon.style.animation = 'shapeRotate 3s infinite';
        }
    }
    
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        @keyframes mapPulse {
            0%, 100% { transform: scale(1) rotate(0deg); }
            50% { transform: scale(1.1) rotate(5deg); }
        }
        
        @keyframes dataFlow {
            0% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
            100% { transform: translateY(0); }
        }
        
        @keyframes shapeRotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .file-info-item {
            animation: fadeInUp 0.6s ease-out both;
        }
        
        .coordinate-item {
            animation: slideInRight 0.4s ease-out both;
        }
        
        .coordinate-item:nth-child(1) { animation-delay: 0.1s; }
        .coordinate-item:nth-child(2) { animation-delay: 0.2s; }
        .coordinate-item:nth-child(3) { animation-delay: 0.3s; }
        .coordinate-item:nth-child(4) { animation-delay: 0.4s; }
        .coordinate-item:nth-child(5) { animation-delay: 0.5s; }
        
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .preview-table tbody tr {
            animation: fadeInUp 0.4s ease-out both;
        }
        
        .preview-table tbody tr:nth-child(1) { animation-delay: 0.1s; }
        .preview-table tbody tr:nth-child(2) { animation-delay: 0.2s; }
        .preview-table tbody tr:nth-child(3) { animation-delay: 0.3s; }
        .preview-table tbody tr:nth-child(4) { animation-delay: 0.4s; }
        .preview-table tbody tr:nth-child(5) { animation-delay: 0.5s; }
    `;
    document.head.appendChild(style);
    
    // Add progress indicator for file processing
    function addProgressIndicator() {
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        progressBar.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 0%;
            height: 3px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            z-index: 1001;
            transition: width 0.3s ease;
        `;
        
        document.body.appendChild(progressBar);
        
        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            progressBar.style.width = progress + '%';
            
            if (progress >= 90) {
                clearInterval(interval);
            }
        }, 200);
        
        return progressBar;
    }
    
    // Add file size formatting
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Add file type detection
    function getFileTypeIcon(fileType) {
        const icons = {
            'kml': '🗺️',
            'csv': '📊',
            'shp': '📁',
            'zip': '📦'
        };
        return icons[fileType.toLowerCase()] || '📄';
    }
    
    // Add responsive table handling
    const tableContainer = document.querySelector('.preview-table');
    if (tableContainer) {
        let isScrolling = false;
        
        tableContainer.addEventListener('scroll', function() {
            if (!isScrolling) {
                isScrolling = true;
                this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
                
                setTimeout(() => {
                    this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.1)';
                    isScrolling = false;
                }, 150);
            }
        });
    }
    
    // Add file content preview scrolling
    const contentPreview = document.querySelector('.file-content-preview');
    if (contentPreview) {
        contentPreview.addEventListener('scroll', function() {
            const scrollPercent = (this.scrollTop / (this.scrollHeight - this.clientHeight)) * 100;
            
            // Add scroll indicator
            if (!this.querySelector('.scroll-indicator')) {
                const indicator = document.createElement('div');
                indicator.className = 'scroll-indicator';
                indicator.style.cssText = `
                    position: absolute;
                    bottom: 10px;
                    right: 10px;
                    background: rgba(0,0,0,0.7);
                    color: white;
                    padding: 5px 10px;
                    border-radius: 15px;
                    font-size: 0.8rem;
                    z-index: 10;
                `;
                this.style.position = 'relative';
                this.appendChild(indicator);
            }
            
            const indicator = this.querySelector('.scroll-indicator');
            indicator.textContent = `${Math.round(scrollPercent)}%`;
        });
    }
    
    // Add keyboard navigation for table
    const tableRowsForNav = document.querySelectorAll('.preview-table tbody tr');
    let currentRowIndex = -1;
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            e.preventDefault();
            
            if (e.key === 'ArrowDown') {
                currentRowIndex = Math.min(currentRowIndex + 1, tableRowsForNav.length - 1);
            } else {
                currentRowIndex = Math.max(currentRowIndex - 1, 0);
            }
            
            // Remove previous selection
            tableRowsForNav.forEach(row => row.style.backgroundColor = '');
            
            // Highlight current row
            if (currentRowIndex >= 0) {
                tableRowsForNav[currentRowIndex].style.backgroundColor = 'rgba(102, 126, 234, 0.15)';
                tableRowsForNav[currentRowIndex].scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });
    
    console.log('File Preview Page loaded successfully! 🎉');
}); 