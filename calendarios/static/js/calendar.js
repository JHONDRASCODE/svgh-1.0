document.addEventListener('DOMContentLoaded', () => {
    const request = '/calendarios/get_all_events/';
    const calendarEl = document.getElementById('calendar');
    let allEvents = [];

    // Cargar opciones de los filtros desde la misma API
    function loadFilterOptions() {
        fetch(request)  // Usar la misma URL que para cargar eventos
            .then(response => response.json())
            .then(data => {
                // Asegurarse de que data.events existe
                const events = data.events || [];
                console.log("Datos de eventos para filtros:", events);
                
                // Poblar los selectores con opciones únicas
                populateFilter('instructorFilter', events, 'id_instructor', 'instructor');
                populateFilter('programaFilter', events, 'id_programa', 'programa');
                populateFilter('locationFilter', events, 'id_ambiente', 'ambiente');
            })
            .catch(error => console.error('Error al cargar los filtros:', error));
    }

    // Función para poblar las opciones de los filtros
    function populateFilter(filterId, data, idKey, textKey) {
        const filterElement = document.getElementById(filterId);
        if (!filterElement) {
            console.error(`Elemento no encontrado: ${filterId}`);
            return;
        }
        
        // Limpiar opciones existentes excepto la primera
        while (filterElement.options.length > 1) {
            filterElement.remove(1);
        }

        // Crear Set para valores únicos
        const uniqueValues = new Set();
        const uniqueItems = [];

        // Filtrar elementos únicos
        data.forEach(item => {
            if (item[idKey] && !uniqueValues.has(item[idKey])) {
                uniqueValues.add(item[idKey]);
                uniqueItems.push(item);
            }
        });

        // Agregar opciones al select
        uniqueItems.forEach(item => {
            const option = document.createElement('option');
            option.value = item[idKey];
            option.textContent = item[textKey];
            filterElement.appendChild(option);
        });
        
        console.log(`Filtro ${filterId} poblado con ${uniqueItems.length} opciones`);
    }

    // Inicializar el calendario
    const calendar = new FullCalendar.Calendar(calendarEl, {
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay',
        },
        initialView: 'timeGridWeek',
        nowIndicator: true,
        locale: 'es',
        allDaySlot: false,
        slotLabelFormat: { hour: 'numeric', hour12: true },
        events: allEvents,
        eventClick: clickInfo => showEventModal(clickInfo),
        height: 'auto',
        timeZone: 'local'
    });

    // Mostrar modal con detalles del evento
    function showEventModal(clickInfo) {
        const { title, extendedProps } = clickInfo.event;
        console.log("Evento clickeado:", clickInfo.event);
        
        const eventDetails = `
            <div class="modal fade" id="eventModal" tabindex="-1" aria-labelledby="eventModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="eventModalLabel">${title || 'Evento'}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p><strong>Instructor:</strong> ${extendedProps.instructor || 'No especificado'}</p>
                            <p><strong>Competencia:</strong> ${extendedProps.competencia || 'No especificada'}</p>
                            <p><strong>Ambiente:</strong> ${extendedProps.ambiente || 'No especificado'}</p>
                            <p><strong>Hora de inicio:</strong> ${clickInfo.event.start ? clickInfo.event.start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'No especificada'}</p>
                            <p><strong>Hora de finalización:</strong> ${clickInfo.event.end ? clickInfo.event.end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'No especificada'}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>`;
        
        // Eliminar modal anterior si existe
        const existingModal = document.getElementById('eventModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', eventDetails);
        new bootstrap.Modal(document.getElementById('eventModal')).show();
        document.getElementById('eventModal').addEventListener('hidden.bs.modal', () => {
            document.getElementById('eventModal').remove();
        });
    }

    // Cargar eventos
    function loadEvents() {
        console.log("Cargando eventos desde:", request);
        fetch(request)
            .then(response => response.json())
            .then(data => {
                console.log("Datos recibidos:", data);
                
                if (!data || !data.events) {
                    console.error('Formato de datos incorrecto:', data);
                    return;
                }
                
                allEvents = data.events.map(event => ({
                    id: `${event.id_programa}-${event.id_instructor}-${event.id_ambiente}-${new Date(event.startDate).getTime()}`,
                    title: event.programa,
                    start: event.startDate,
                    end: event.endDate,
                    extendedProps: {
                        id_instructor: event.id_instructor,
                        instructor: event.instructor,
                        id_ambiente: event.id_ambiente,
                        ambiente: event.ambiente,
                        competencia: event.competencia,
                        id_programa: event.id_programa,
                    },
                }));
                
                console.log(`${allEvents.length} eventos cargados y mapeados`);
                
                calendar.removeAllEvents();
                calendar.addEventSource(allEvents);
            })
            .catch(error => {
                console.error('Error al cargar eventos:', error);
            });
    }

    // Filtrar eventos según los filtros seleccionados
    function filterEvents() {
        const filters = ['instructorFilter', 'programaFilter', 'locationFilter'].map(id => {
            const element = document.getElementById(id);
            if (!element) {
                console.error(`Elemento de filtro no encontrado: ${id}`);
                return { id, value: '' };
            }
            return element;
        });
        
        const filteredEvents = allEvents.filter(event => {
            return filters.every(filter => {
                // Determinar la clave correcta basada en el ID del filtro
                let filterKey;
                if (filter.id === 'instructorFilter') {
                    filterKey = 'id_instructor';
                } else if (filter.id === 'programaFilter') {
                    filterKey = 'id_programa';
                } else if (filter.id === 'locationFilter') {
                    filterKey = 'id_ambiente';
                } else {
                    return true; // Si no reconocemos el filtro, no filtramos
                }
                
                // Si no hay valor seleccionado, no filtramos
                if (!filter.value) return true;
                
                // Comparar el valor del filtro con el valor en el evento
                return event.extendedProps[filterKey] == filter.value;
            });
        });
        
        console.log(`Filtrando eventos: ${filteredEvents.length} de ${allEvents.length} coinciden`);
        
        calendar.removeAllEvents();
        calendar.addEventSource(filteredEvents);
    }

    // Asignar eventos a los filtros
    ['instructorFilter', 'programaFilter', 'locationFilter'].forEach(filterId => {
        const element = document.getElementById(filterId);
        if (element) {
            element.addEventListener('change', filterEvents);
        } else {
            console.error(`Elemento de filtro no encontrado para evento: ${filterId}`);
        }
    });

    // Limpiar filtros
    const clearFiltersBtn = document.getElementById('clearFilters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', () => {
            ['instructorFilter', 'programaFilter', 'locationFilter'].forEach(filterId => {
                const element = document.getElementById(filterId);
                if (element) {
                    element.value = '';
                }
            });
            filterEvents();
        });
    } else {
        console.error('Botón "clearFilters" no encontrado');
    }

    // Inicialización
    loadFilterOptions(); // Cargar las opciones de los filtros
    loadEvents();        // Cargar los eventos
    calendar.render();    // Renderizar el calendario
    
    // Recargar eventos cada 5 minutos para mantener el calendario actualizado
    setInterval(loadEvents, 300000);
    
    console.log('Calendario inicializado correctamente');
});