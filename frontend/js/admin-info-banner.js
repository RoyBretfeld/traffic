/**
 * Wiederverwendbare Info-Banner-Komponente für Admin-Seiten
 * 
 * Zeigt kontextbezogene Informationen oben auf jeder Admin-Seite an.
 * 
 * Verwendung:
 *   <div id="admin-info-banner"></div>
 *   <script src="/js/admin-info-banner.js"></script>
 *   <script>
 *     showAdminInfoBanner({
 *       title: "Tank- und Strompreise",
 *       description: "Die Preise werden automatisch von der Tankerkönig API geladen...",
 *       icon: "fas fa-gas-pump"
 *     });
 *   </script>
 */

/**
 * Zeigt ein Info-Banner oben auf der Admin-Seite an
 * 
 * @param {Object} config - Konfiguration
 * @param {string} config.title - Titel des Banners
 * @param {string} config.description - Beschreibungstext
 * @param {string} config.icon - FontAwesome Icon-Klasse (z.B. "fas fa-gas-pump")
 * @param {string} config.type - Typ: "info", "warning", "success", "danger" (Standard: "info")
 * @param {boolean} config.dismissible - Ob Banner schließbar ist (Standard: false)
 */
function showAdminInfoBanner(config) {
    const container = document.getElementById('admin-info-banner');
    if (!container) {
        console.warn('admin-info-banner Container nicht gefunden');
        return;
    }
    
    const {
        title = 'Information',
        description = '',
        icon = 'fas fa-info-circle',
        type = 'info',
        dismissible = false
    } = config;
    
    // Bootstrap Alert-Klassen
    const alertClasses = {
        'info': 'alert-info',
        'warning': 'alert-warning',
        'success': 'alert-success',
        'danger': 'alert-danger'
    };
    
    const alertClass = alertClasses[type] || alertClasses['info'];
    
    // HTML generieren
    let html = `<div class="alert ${alertClass} mb-4`;
    if (dismissible) {
        html += ' alert-dismissible fade show" role="alert">';
        html += '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
    } else {
        html += '" role="alert">';
    }
    
    html += `<i class="${icon}"></i> `;
    html += `<strong>${escapeHtml(title)}:</strong> `;
    html += escapeHtml(description);
    html += '</div>';
    
    container.innerHTML = html;
}

/**
 * Entfernt HTML-Sonderzeichen (XSS-Schutz)
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Vordefinierte Banner-Konfigurationen für verschiedene Admin-Seiten
 */
const AdminInfoBanners = {
    tankpreise: {
        title: 'Tank- und Strompreise',
        description: 'Die Preise werden automatisch von der Tankerkönig API geladen und alle 5-10 Minuten aktualisiert. Strompreise werden vorsorglich angezeigt (Berechnung folgt später).',
        icon: 'fas fa-gas-pump',
        type: 'info'
    },
    system: {
        title: 'System-Status',
        description: 'Überwachen Sie den Gesundheitszustand aller Systemkomponenten in Echtzeit.',
        icon: 'fas fa-heartbeat',
        type: 'info'
    },
    statistik: {
        title: 'Statistik & KPIs',
        description: 'Detaillierte Statistiken und Kennzahlen zu Touren, Kosten und Performance.',
        icon: 'fas fa-chart-bar',
        type: 'info'
    },
    dbVerwaltung: {
        title: 'Datenbank-Verwaltung',
        description: 'Verwalten Sie Datenbank-Backups, Migrationen und Schema-Informationen.',
        icon: 'fas fa-database',
        type: 'info'
    },
    kiIntegration: {
        title: 'KI-Integration',
        description: 'Überwachen Sie KI-Kosten, Aktivitäten und Effektivität.',
        icon: 'fas fa-robot',
        type: 'info'
    },
    tourFilter: {
        title: 'Tour-Filter',
        description: 'Verwalten Sie welche Touren ignoriert oder erlaubt werden sollen.',
        icon: 'fas fa-filter',
        type: 'info'
    },
    geoCache: {
        title: 'Geo-Cache Vorverarbeitung',
        description: 'Laden Sie Tourplan-Dateien hoch, um Adressen im Geo-Cache vorzuverarbeiten.',
        icon: 'fas fa-globe',
        type: 'info'
    },
    tourplanUebersicht: {
        title: 'Tourplan-Übersicht',
        description: 'Übersicht aller Tourpläne mit Statistiken zu Touren, Stops, Distanz, Zeit und Kosten.',
        icon: 'fas fa-list-alt',
        type: 'info'
    }
};

/**
 * Zeigt ein vordefiniertes Banner an
 * 
 * @param {string} key - Schlüssel aus AdminInfoBanners
 */
function showPredefinedBanner(key) {
    const config = AdminInfoBanners[key];
    if (config) {
        showAdminInfoBanner(config);
    } else {
        console.warn(`Unbekanntes Banner: ${key}`);
    }
}

