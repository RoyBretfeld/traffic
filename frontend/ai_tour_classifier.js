/**
 * KI-basierte Tour-Klassifizierung und Gruppierung
 * Nutzt LLM für intelligente BAR-Erkennung und Gruppierung
 */

class AITourClassifier {
    constructor() {
        this.cache = new Map();
    }

    /**
     * Klassifiziere Tour mit KI (BAR, Tour-Typ, Gruppierung)
     */
    async classifyTour(tourId, stops = []) {
        const cacheKey = `tour_${tourId}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            const response = await fetch('/api/ai-tour-classify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tour_id: tourId,
                    stop_count: stops.length,
                    sample_stops: stops.slice(0, 5).map(s => ({
                        name: s.customer || s.name,
                        address: `${s.street}, ${s.postal_code} ${s.city}`
                    }))
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.cache.set(cacheKey, result);
                return result;
            }
        } catch (error) {
            console.warn('KI-Klassifizierung fehlgeschlagen, verwende Fallback:', error);
        }

        // Fallback: Pattern-basierte Erkennung
        return this.fallbackClassification(tourId);
    }

    /**
     * Fallback-Klassifizierung (ohne KI)
     */
    fallbackClassification(tourId) {
        const isBar = /BAR/i.test(tourId);
        const baseName = tourId.replace(/\s*(Uhr\s*)?(BAR|Tour)$/i, '').trim();
        const time = this.extractTime(tourId);

        return {
            is_bar: isBar,
            base_name: baseName,
            time: time,
            confidence: 0.7,
            reasoning: 'Pattern-basierte Erkennung'
        };
    }

    /**
     * Gruppiere Touren intelligenter mit KI
     */
    async groupTours(tours) {
        // Für viele Touren: KI verwenden
        if (tours.length > 10) {
            try {
                const response = await fetch('/api/ai-tour-group', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        tours: tours.map(t => ({
                            id: t.tour_id,
                            name: t.tour_id,
                            stop_count: (t.stops || []).length
                        }))
                    })
                });

                if (response.ok) {
                    const result = await response.json();
                    return this.applyGrouping(tours, result.groups);
                }
            } catch (error) {
                console.warn('KI-Gruppierung fehlgeschlagen, verwende Fallback:', error);
            }
        }

        // Fallback: Einfache Gruppierung
        return this.fallbackGrouping(tours);
    }

    /**
     * Fallback-Gruppierung (ohne KI)
     */
    fallbackGrouping(tours) {
        return tours.map((tour, index) => ({
            ...tour,
            index,
            baseName: tour.tour_id ? tour.tour_id.replace(/\s*(Uhr\s*)?(BAR|Tour)$/i, '').trim() : '',
            isBar: /BAR/i.test(tour.tour_id || ''),
            time: this.extractTime(tour.tour_id || '')
        })).sort((a, b) => {
            if (a.baseName !== b.baseName) {
                return a.baseName.localeCompare(b.baseName);
            }
            if (a.isBar && !b.isBar) return -1;
            if (!a.isBar && b.isBar) return 1;
            return 0;
        });
    }

    /**
     * Wende KI-Gruppierung an
     */
    applyGrouping(tours, groups) {
        const tourMap = new Map(tours.map((t, i) => [t.tour_id || `Tour ${i}`, t]));
        
        return groups.map(group => ({
            ...tourMap.get(group.tour_id),
            group_id: group.group_id,
            baseName: group.base_name,
            isBar: group.is_bar,
            time: group.time
        }));
    }

    /**
     * Extrahiere Zeit aus Tour-Namen
     */
    extractTime(tourId) {
        const timeMatch = tourId.match(/(\d{1,2})[.:](\d{2})/);
        if (timeMatch) {
            return `${timeMatch[1]}:${timeMatch[2]}`;
        }
        return '';
    }
}

// Globale Instanz
const aiTourClassifier = new AITourClassifier();

