// KML Preview Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    
    const searchInput = document.getElementById('searchInput');
    const sortSelect = document.getElementById('sortSelect');
    const sortAscBtn = document.getElementById('sortAsc');
    const sortDescBtn = document.getElementById('sortDesc');
    const tableBody = document.getElementById('tableBody');
    const mapContainer = document.getElementById('map');
    
    let currentPage = 1;
    let searchQuery = '';
    let sortBy = 'created_at';
    let sortOrder = 'asc';
    let map = null;
    let markers = [];
    
    // Initialize map
    if (mapContainer) {
        initializeMap();
    }
    
    // Search functionality
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchQuery = this.value;
            currentPage = 1;
            loadData();
        }, 300);
    });
    
    // Sort functionality
    sortSelect.addEventListener('change', function() {
        sortBy = this.value;
        loadData();
    });
    
    sortAscBtn.addEventListener('click', function() {
        sortOrder = 'asc';
        updateSortButtons();
        loadData();
    });
    
    sortDescBtn.addEventListener('click', function() {
        sortOrder = 'desc';
        updateSortButtons();
        loadData();
    });
    
    function updateSortButtons() {
        sortAscBtn.classList.toggle('active', sortOrder === 'asc');
        sortDescBtn.classList.toggle('active', sortOrder === 'desc');
    }
    
    // Load data via AJAX
    function loadData() {
        const kmlId = getKMLIdFromURL();
        if (!kmlId) return;
        
        const url = new URL(`/dashboard/kml/ajax/${kmlId}/`, window.location.origin);
        url.searchParams.set('search', searchQuery);
        url.searchParams.set('sort', sortBy);
        url.searchParams.set('order', sortOrder);
        url.searchParams.set('page', currentPage);
        
        // Show loading state
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px;">
                    <div style="display: inline-block; width: 20px; height: 20px; border: 2px solid #667eea; border-radius: 50%; border-top-color: transparent; animation: spin 1s linear infinite;"></div>
                    <div style="margin-top: 10px; color: #6c757d;">Loading data...</div>
                </td>
            </tr>
        `;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderTable(data.data);
                    updatePagination(data.pagination);
                    updateMap(data.data);
                } else {
                    showToast(data.error || 'Error loading data', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Network error. Please try again.', 'error');
            });
    }
    
    function renderTable(data) {
        if (data.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; padding: 40px; color: #6c757d;">
                        No data found. Try adjusting your search criteria.
                    </td>
                </tr>
            `;
            return;
        }
        
        tableBody.innerHTML = data.map(item => `
            <tr data-id="${item.id}">
                <td>${item.placemark_name || '-'}</td>
                <td>${item.kitta_number || '-'}</td>
                <td>${item.owner_name || '-'}</td>
                <td>
                    <span class="geometry-badge geometry-${item.geometry_type.toLowerCase()}">
                        ${item.geometry_type}
                    </span>
                </td>
                <td>${item.area_hectares ? item.area_hectares.toFixed(4) : '-'}</td>
                <td>${item.area_sqm ? item.area_sqm.toFixed(2) : '-'}</td>
                <td>${item.description ? item.description.substring(0, 50) + (item.description.length > 50 ? '...' : '') : '-'}</td>
                <td class="coordinates-cell" title="${item.coordinates}">
                    ${item.coordinates.substring(0, 30)}${item.coordinates.length > 30 ? '...' : ''}
                </td>
            </tr>
        `).join('');
        
        // Add row hover effects
        addTableRowEffects();
    }
    
    function addTableRowEffects() {
        const rows = tableBody.querySelectorAll('tr');
        rows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.backgroundColor = 'rgba(102, 126, 234, 0.05)';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
            
            row.addEventListener('click', function() {
                const itemId = this.dataset.id;
                highlightMapFeature(itemId);
            });
        });
    }
    
    function updatePagination(pagination) {
        const paginationSection = document.querySelector('.pagination-section');
        if (!paginationSection) return;
        
        if (pagination.total_pages <= 1) {
            paginationSection.style.display = 'none';
            return;
        }
        
        paginationSection.style.display = 'flex';
        
        const infoElement = paginationSection.querySelector('.pagination-info');
        const controlsElement = paginationSection.querySelector('.pagination-controls');
        
        if (infoElement) {
            const startIndex = (pagination.current_page - 1) * 20 + 1;
            const endIndex = Math.min(pagination.current_page * 20, pagination.total_count);
            infoElement.textContent = `Showing ${startIndex} to ${endIndex} of ${pagination.total_count} entries`;
        }
        
        if (controlsElement) {
            let controlsHTML = '';
            
            // Previous buttons
            if (pagination.has_previous) {
                controlsHTML += '<button class="page-btn" onclick="goToPage(1)">«</button>';
                controlsHTML += `<button class="page-btn" onclick="goToPage(${pagination.current_page - 1})">‹</button>`;
            }
            
            // Page numbers
            const startPage = Math.max(1, pagination.current_page - 2);
            const endPage = Math.min(pagination.total_pages, pagination.current_page + 2);
            
            for (let i = startPage; i <= endPage; i++) {
                const activeClass = i === pagination.current_page ? 'active' : '';
                controlsHTML += `<button class="page-btn ${activeClass}" onclick="goToPage(${i})">${i}</button>`;
            }
            
            // Next buttons
            if (pagination.has_next) {
                controlsHTML += `<button class="page-btn" onclick="goToPage(${pagination.current_page + 1})">›</button>`;
                controlsHTML += `<button class="page-btn" onclick="goToPage(${pagination.total_pages})">»</button>`;
            }
            
            controlsElement.innerHTML = controlsHTML;
        }
    }
    
    // Global function for pagination
    window.goToPage = function(page) {
        currentPage = page;
        loadData();
    };
    
    // Map functionality
    function initializeMap() {
        map = L.map('map').setView([0, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        loadGeoJSONToMap();
    }

    function loadGeoJSONToMap() {
        const kmlId = getKMLIdFromURL();
        if (!kmlId) return;
        fetch(`/dashboard/kml/geojson/${kmlId}/`)
            .then(response => response.json())
            .then(geojson => {
                if (!map) return;
                // Remove previous layers
                if (window.geojsonLayer) {
                    map.removeLayer(window.geojsonLayer);
                }
                window.geojsonLayer = L.geoJSON(geojson, {
                    style: function(feature) {
                        if (feature.geometry.type === 'Polygon' || feature.geometry.type === 'MultiPolygon') {
                            return { color: '#667eea', fillColor: '#667eea', fillOpacity: 0.3 };
                        } else if (feature.geometry.type === 'LineString') {
                            return { color: '#e74c3c', weight: 3 };
                        } else {
                            return { color: '#27ae60' };
                        }
                    },
                    pointToLayer: function(feature, latlng) {
                        return L.marker(latlng);
                    },
                    onEachFeature: function(feature, layer) {
                        const props = feature.properties || {};
                        let popup = `<div style="min-width: 200px;">
                            <h4 style="margin: 0 0 10px 0; color: #2c3e50;">${props.placemark_name || 'Unnamed Placemark'}</h4>
                            <p><strong>Kitta Number:</strong> ${props.kitta_number || 'N/A'}</p>
                            <p><strong>Owner:</strong> ${props.owner_name || 'N/A'}</p>
                            <p><strong>Type:</strong> ${props.geometry_type}</p>`;
                        if (props.area_hectares) popup += `<p><strong>Area:</strong> ${props.area_hectares.toFixed(4)} hectares</p>`;
                        if (props.description) popup += `<p><strong>Description:</strong> ${props.description.substring(0, 100)}${props.description.length > 100 ? '...' : ''}</p>`;
                        popup += '</div>';
                        layer.bindPopup(popup);
                    }
                }).addTo(map);
                try {
                    map.fitBounds(window.geojsonLayer.getBounds(), { padding: [20, 20] });
                } catch (e) {
                    // fallback: do nothing
                }
            });
    }
    
    function createPopupContent(item) {
        return `
            <div style="min-width: 200px;">
                <h4 style="margin: 0 0 10px 0; color: #2c3e50;">${item.placemark_name || 'Unnamed Placemark'}</h4>
                <p><strong>Kitta Number:</strong> ${item.kitta_number || 'N/A'}</p>
                <p><strong>Owner:</strong> ${item.owner_name || 'N/A'}</p>
                <p><strong>Type:</strong> ${item.geometry_type}</p>
                ${item.area_hectares ? `<p><strong>Area:</strong> ${item.area_hectares.toFixed(4)} hectares</p>` : ''}
                ${item.description ? `<p><strong>Description:</strong> ${item.description.substring(0, 100)}${item.description.length > 100 ? '...' : ''}</p>` : ''}
            </div>
        `;
    }
    
    function highlightMapFeature(itemId) {
        // Remove previous highlights
        markers.forEach(marker => {
            if (marker.setStyle) {
                marker.setStyle({ color: '#667eea', fillColor: '#667eea', fillOpacity: 0.3 });
            }
        });
        
        // Highlight selected feature
        const selectedMarker = markers.find(marker => marker.featureId === itemId);
        if (selectedMarker && selectedMarker.setStyle) {
            selectedMarker.setStyle({ color: '#e74c3c', fillColor: '#e74c3c', fillOpacity: 0.6 });
        }
    }
    
    function getKMLIdFromURL() {
        const pathParts = window.location.pathname.split('/');
        const kmlIndex = pathParts.indexOf('kml');
        if (kmlIndex !== -1 && pathParts[kmlIndex + 1] === 'preview') {
            return pathParts[kmlIndex + 2];
        }
        return null;
    }
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.key === 'f' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            searchInput.focus();
        }
    });
    
    // Add table row animations
    function addTableAnimations() {
        const rows = tableBody.querySelectorAll('tr');
        rows.forEach((row, index) => {
            row.style.animationDelay = `${index * 0.05}s`;
            row.classList.add('fade-in-row');
        });
    }
    
    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .fade-in-row {
            animation: fadeInUp 0.4s ease-out both;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .geometry-badge {
            transition: all 0.3s ease;
        }
        
        .geometry-badge:hover {
            transform: scale(1.1);
        }
        
        .coordinates-cell {
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .coordinates-cell:hover {
            background: rgba(102, 126, 234, 0.1);
        }
    `;
    document.head.appendChild(style);
    
    // Initialize
    updateSortButtons();
    addTableAnimations();
    
    console.log('KML Preview Page loaded successfully! 🎉');
}); 