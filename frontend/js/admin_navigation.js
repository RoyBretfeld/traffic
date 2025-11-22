/**
 * Admin-Navigation Komponente
 * Wiederverwendbare Navigation für alle Admin-Seiten
 * 
 * Verwendung:
 * <div id="admin-nav-container"></div>
 * <script src="/js/admin_navigation.js"></script>
 * <script>
 *   initAdminNavigation('system'); // 'system', 'statistik', 'systemregeln', etc.
 * </script>
 */

const ADMIN_NAV_ITEMS = [
    {
        id: 'system',
        title: 'System/Health',
        icon: 'fa-heartbeat',
        href: '/admin/system.html'
    },
    {
        id: 'statistik',
        title: 'Statistik',
        icon: 'fa-chart-bar',
        href: '/admin/statistik.html'
    },
    {
        id: 'systemregeln',
        title: 'Systemregeln',
        icon: 'fa-book',
        href: '/admin/systemregeln.html'
    },
    {
        id: 'db-verwaltung',
        title: 'DB-Verwaltung',
        icon: 'fa-database',
        href: '/admin/db-verwaltung.html'
    },
    {
        id: 'tour-filter',
        title: 'Tour-Filter',
        icon: 'fa-filter',
        href: '/admin/tour-filter.html'
    },
    {
        id: 'tour-import',
        title: 'Tour-Import',
        icon: 'fa-upload',
        href: '/admin/tour-import.html'
    },
    {
        id: 'dataflow',
        title: 'Datenfluss',
        icon: 'fa-project-diagram',
        href: '/admin/dataflow.html'
    }
];

/**
 * Initialisiert die Admin-Navigation
 * @param {string} activeId - ID des aktiven Navigationspunkts
 */
function initAdminNavigation(activeId) {
    const container = document.getElementById('admin-nav-container');
    if (!container) {
        console.error('admin-nav-container nicht gefunden!');
        return;
    }

    // Navigation HTML generieren
    let navHTML = '<nav class="admin-nav-bar">';
    navHTML += '<div class="admin-nav-items">';
    
    ADMIN_NAV_ITEMS.forEach(item => {
        const isActive = item.id === activeId;
        const activeClass = isActive ? 'active' : '';
        const activeStyle = isActive ? 'style="background-color: white; border-bottom: 2px solid #007bff;"' : '';
        
        navHTML += `
            <a href="${item.href}" class="admin-nav-item ${activeClass}" ${activeStyle}>
                <i class="fas ${item.icon}"></i>
                <span>${item.title}</span>
            </a>
        `;
    });
    
    navHTML += '</div>';
    navHTML += '</nav>';
    
    container.innerHTML = navHTML;
}

// CSS für Navigation (wird dynamisch eingefügt)
const adminNavCSS = `
<style>
.admin-nav-bar {
    background-color: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    padding: 0;
    margin-bottom: 20px;
}

.admin-nav-items {
    display: flex;
    flex-wrap: wrap;
    gap: 0;
    padding: 0;
    margin: 0;
}

.admin-nav-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 20px;
    text-decoration: none;
    color: #495057;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    transition: all 0.2s ease;
    background-color: transparent;
}

.admin-nav-item:hover {
    background-color: #e9ecef;
    color: #007bff;
    border-bottom-color: #007bff;
}

.admin-nav-item.active {
    background-color: white;
    color: #007bff;
    border-bottom: 2px solid #007bff;
}

.admin-nav-item i {
    font-size: 1.1em;
}

.admin-nav-item span {
    white-space: nowrap;
}

@media (max-width: 768px) {
    .admin-nav-items {
        flex-direction: column;
    }
    
    .admin-nav-item {
        border-bottom: 1px solid #dee2e6;
        border-left: 3px solid transparent;
    }
    
    .admin-nav-item.active {
        border-left-color: #007bff;
    }
}
</style>
`;

// CSS automatisch einfügen, wenn noch nicht vorhanden
if (!document.getElementById('admin-nav-css')) {
    const styleElement = document.createElement('div');
    styleElement.id = 'admin-nav-css';
    styleElement.innerHTML = adminNavCSS;
    document.head.appendChild(styleElement);
}

