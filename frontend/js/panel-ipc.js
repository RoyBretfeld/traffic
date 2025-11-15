/**
 * Panel IPC (Inter-Process Communication)
 * Kommunikation zwischen Hauptfenster und Panel-Fenstern via BroadcastChannel
 */

class PanelIPC {
    /**
     * Erstellt eine neue PanelIPC-Instanz
     * @param {string} channelName - Name des BroadcastChannel
     */
    constructor(channelName = 'trafficapp-panels') {
        // Browser-Kompatibilität prüfen
        if (!window.BroadcastChannel) {
            console.error('[PanelIPC] BroadcastChannel API nicht verfügbar!');
            throw new Error('BroadcastChannel API wird nicht unterstützt');
        }

        try {
            this.channel = new BroadcastChannel(channelName);
            this.listeners = new Map();
            this.messageHandler = null;
            this.setupListeners();
        } catch (e) {
            console.error('[PanelIPC] Fehler beim Erstellen des Channels:', e);
            throw e;
        }
    }

    /**
     * Initialisiert Event-Listener für eingehende Nachrichten
     * @private
     */
    setupListeners() {
        this.messageHandler = (event) => {
            // Defensive Prüfung: Nachricht validieren
            if (!event || !event.data || typeof event.data !== 'object') {
                console.warn('[PanelIPC] Ungültige Nachricht erhalten:', event);
                return;
            }

            const { type, data } = event.data;

            // Typ muss vorhanden sein
            if (!type || typeof type !== 'string') {
                console.warn('[PanelIPC] Nachricht ohne gültigen Typ erhalten:', event.data);
                return;
            }

            // Handler aufrufen
            const handlers = this.listeners.get(type) || [];
            if (handlers.length === 0) {
                console.debug(`[PanelIPC] Keine Handler für Event-Typ '${type}' registriert`);
            }

            handlers.forEach(handler => {
                try {
                    handler(data, event);
                } catch (e) {
                    console.error(`[PanelIPC] Fehler in Handler für '${type}':`, e);
                }
            });
        };

        this.channel.addEventListener('message', this.messageHandler);
    }

    /**
     * Registriere einen Event-Handler
     * @param {string} type - Event-Typ (z.B. 'route-update', 'tour-select')
     * @param {Function} handler - Handler-Funktion
     */
    on(type, handler) {
        // Validierung: type muss ein nicht-leerer String sein
        if (typeof type !== 'string' || !type) {
            console.error('[PanelIPC] on(): type muss ein nicht-leerer String sein');
            return;
        }

        // Validierung: handler muss eine Funktion sein
        if (typeof handler !== 'function') {
            console.error('[PanelIPC] on(): handler muss eine Funktion sein');
            return;
        }

        if (!this.listeners.has(type)) {
            this.listeners.set(type, []);
        }
        this.listeners.get(type).push(handler);
        console.debug(`[PanelIPC] Handler für '${type}' registriert (${this.listeners.get(type).length} gesamt)`);
    }

    /**
     * Entferne einen Event-Handler
     * @param {string} type - Event-Typ
     * @param {Function} handler - Handler-Funktion, die entfernt werden soll
     */
    off(type, handler) {
        // Validierung: type muss ein nicht-leerer String sein
        if (typeof type !== 'string' || !type) {
            console.error('[PanelIPC] off(): type muss ein nicht-leerer String sein');
            return;
        }

        const handlers = this.listeners.get(type) || [];
        const filtered = handlers.filter(h => h !== handler);
        
        if (filtered.length === 0) {
            this.listeners.delete(type);
            console.debug(`[PanelIPC] Alle Handler für '${type}' entfernt`);
        } else {
            this.listeners.set(type, filtered);
            console.debug(`[PanelIPC] Handler für '${type}' entfernt (${filtered.length} verbleiben)`);
        }
    }

    /**
     * Sende Nachricht an alle Panel-Fenster
     * @param {string} type - Event-Typ
     * @param {any} data - Daten (optional)
     */
    postMessage(type, data) {
        // Validierung: type muss ein nicht-leerer String sein
        if (typeof type !== 'string' || !type) {
            console.error('[PanelIPC] postMessage(): type muss ein nicht-leerer String sein');
            return;
        }

        try {
            const message = { 
                type, 
                data: data !== undefined ? data : null, 
                timestamp: Date.now() 
            };
            this.channel.postMessage(message);
            console.debug(`[PanelIPC] Nachricht gesendet: ${type}`, message);
        } catch (e) {
            console.error(`[PanelIPC] Fehler beim Senden von '${type}':`, e);
        }
    }

    /**
     * Schließe den IPC-Kanal und räume Ressourcen auf
     */
    close() {
        try {
            // Event Listener entfernen (Memory Leak vermeiden)
            if (this.messageHandler) {
                this.channel.removeEventListener('message', this.messageHandler);
                this.messageHandler = null;
            }

            // Channel schließen
            this.channel.close();
            
            // Listener Map leeren
            this.listeners.clear();
            
            console.debug('[PanelIPC] Kanal geschlossen');
        } catch (e) {
            console.error('[PanelIPC] Fehler beim Schließen:', e);
        }
    }

    /**
     * Gibt Statistiken über registrierte Handler zurück
     * @returns {Object} Statistiken
     */
    getStats() {
        const stats = {
            totalTypes: this.listeners.size,
            handlers: {}
        };

        this.listeners.forEach((handlers, type) => {
            stats.handlers[type] = handlers.length;
        });

        return stats;
    }
}

// Browser-Kompatibilität prüfen, bevor globale Instanz erstellt wird
if (window.BroadcastChannel) {
    try {
        window.panelIPC = new PanelIPC();
        console.log('[PanelIPC] Globale Instanz initialisiert');
    } catch (e) {
        console.error('[PanelIPC] Fehler beim Initialisieren der globalen Instanz:', e);
        window.panelIPC = null;
    }
} else {
    console.error('[PanelIPC] BroadcastChannel API nicht verfügbar - Panel-Kommunikation deaktiviert');
    window.panelIPC = null;
}

