document.addEventListener('DOMContentLoaded', () => {
    // ----- CÓDIGO DEL CALENDARIO SENA -----
    const request = '/calendarios/get_all_events/';
    const calendarEl = document.getElementById('calendar');
    let allEvents = [];

    // Función para obtener la hora y fecha de Colombia (UTC-5)
    function getColombiaDateTime() {
        // Crear un objeto Date con la hora actual
        const now = new Date();
        
        // Colombia está en UTC-5
        const colombiaOffset = -5 * 60; // Offset en minutos
        
        // Obtener el offset actual en minutos
        const localOffset = now.getTimezoneOffset();
        
        // Calcular la diferencia entre la hora local y la hora de Colombia
        const offsetDiff = localOffset + colombiaOffset;
        
        // Ajustar la hora al tiempo de Colombia
        const colombiaTime = new Date(now.getTime() + offsetDiff * 60 * 1000);
        
        return colombiaTime;
    }

    // Función para actualizar la hora y fecha de Colombia
    function updateColombiaTime() {
        // Opciones para formatear la fecha y hora
        const dateOptions = { 
            weekday: 'long',
            year: 'numeric', 
            month: 'long', 
            day: 'numeric'
        };
        
        const timeOptions = {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        };
        
        // Obtener la fecha y hora de Colombia
        const colombiaDateTime = getColombiaDateTime();
        
        // Formatear la fecha y hora 
        const dateStr = colombiaDateTime.toLocaleDateString('es-CO', dateOptions);
        const timeStr = colombiaDateTime.toLocaleTimeString('es-CO', timeOptions);
        
        // Formatear con primera letra mayúscula
        const formattedDate = dateStr.charAt(0).toUpperCase() + dateStr.slice(1);
        
        // Actualizar el elemento HTML
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            timeElement.textContent = `${formattedDate} - ${timeStr}`;
        }
    }
    
    // Actualizar inmediatamente y luego cada segundo
    updateColombiaTime();
    setInterval(updateColombiaTime, 1000);

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

    // Inicializar el calendario con configuraciones mejoradas
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
        
        // Configuración para mostrar horas en formato de 12 horas (AM/PM)
        slotLabelFormat: { 
            hour: 'numeric', 
            hour12: true,
            omitZeroMinute: true,
            meridiem: 'short'
        },
        
        // Formato de hora para los eventos
        eventTimeFormat: { 
            hour: 'numeric', 
            minute: '2-digit', 
            hour12: true,
            meridiem: 'short'
        },
        
        events: [],  // Iniciar con calendario vacío
        eventClick: clickInfo => showEventModal(clickInfo),
        height: 'auto',
        timeZone: 'local',
        
        // Configuraciones para optimizar la visualización de horas
        slotMinTime: '07:00:00', // Comenzar a las 7 AM por defecto
        slotMaxTime: '19:00:00', // Terminar a las 7 PM por defecto
        slotDuration: '01:00:00', // Duración de cada slot (1 hora)
        
        // Eventos del calendario para manejar la visualización
        viewDidMount: function(arg) {
            // Ajustar horas visibles después de que la vista haya sido montada
            if (arg.view.type === 'timeGridWeek' || arg.view.type === 'timeGridDay') {
                setTimeout(() => adjustHoursToEvents(), 300);
            }
        },
        
        // Cuando se añaden o cambian eventos
        eventAdd: function() {
            setTimeout(() => adjustHoursToEvents(), 300);
        },
        
        // Colorear eventos según su tipo
        eventDidMount: function(info) {
            // Determinar color según instructor
            if (info.event.extendedProps.id_instructor) {
                const instructorId = parseInt(info.event.extendedProps.id_instructor);
                
                // Agregar una clase base para todos los eventos
                info.el.classList.add('custom-event');
                
                // Asignar clase según ID del instructor (Actualizado para usar colores SENA)
                if (instructorId % 5 === 0) {
                    info.el.classList.add('event-instructor-1'); // Verde SENA principal
                } else if (instructorId % 5 === 1) {
                    info.el.classList.add('event-instructor-2'); // Verde más claro
                } else if (instructorId % 5 === 2) {
                    info.el.classList.add('event-instructor-3'); // Verde medio
                } else if (instructorId % 5 === 3) {
                    info.el.classList.add('event-instructor-4'); // Verde oscuro
                } else {
                    info.el.classList.add('event-instructor-5'); // Verde menta
                }
            }
        },
        
        // Configuración de carga de datos
        loading: function(isLoading) {
            // Mostrar/ocultar indicador de carga
            var loadingIndicator = document.getElementById('loading-indicator');
            if (loadingIndicator) {
                loadingIndicator.style.display = isLoading ? 'block' : 'none';
            }
        }
    });

    // Función para ajustar las horas visibles según los eventos
    function adjustHoursToEvents() {
        const events = calendar.getEvents();
        if (events.length === 0) return;
        
        let earliestHour = 23;
        let latestHour = 0;
        
        events.forEach(event => {
            if (event.start) {
                const startHour = event.start.getHours();
                if (startHour < earliestHour) earliestHour = startHour;
            }
            
            if (event.end) {
                const endHour = event.end.getHours();
                // Si el evento termina justo a la hora en punto, consideramos la hora anterior
                const adjustedEndHour = event.end.getMinutes() === 0 ? endHour : endHour + 1;
                if (adjustedEndHour > latestHour) latestHour = adjustedEndHour;
            }
        });
        
        // Dar margen de 1 hora antes y después
        earliestHour = Math.max(6, earliestHour - 1);
        latestHour = Math.min(22, latestHour + 1);
        
        // Formatear horas para FullCalendar (formato 24h)
        const minTime = String(earliestHour).padStart(2, '0') + ':00:00';
        const maxTime = String(latestHour).padStart(2, '0') + ':00:00';
        
        console.log(`Ajustando rango de horas: ${minTime} - ${maxTime}`);
        
        // Aplicar nuevas horas
        calendar.setOption('slotMinTime', minTime);
        calendar.setOption('slotMaxTime', maxTime);
    }

    // Función mejorada para mostrar el modal con detalles del evento (Actualizada para usar colores SENA)
    function showEventModal(clickInfo) {
        const { title, extendedProps } = clickInfo.event;
        console.log("Evento clickeado:", clickInfo.event);
        
        // Formatear fechas para mostrar
        const formatDate = (date) => {
            if (!date) return 'No especificada';
            return date.toLocaleDateString('es', {
                weekday: 'long',
                day: 'numeric',
                month: 'long',
                year: 'numeric'
            });
        };
        
        // Formatear horas en formato 12h
        const formatTime = (date) => {
            if (!date) return 'No especificada';
            return date.toLocaleTimeString('es', { 
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            });
        };
        
        // Determinar color para la cabecera según tipo de evento (Actualizado para usar colores SENA)
        let headerColor = "#39B54A"; // Color SENA por defecto
        let badgeClass = "bg-success";
        
        // Personalizar color según tipo de evento (Actualizado para usar tonos verdes)
        if (extendedProps.id_instructor) {
            const instructorId = parseInt(extendedProps.id_instructor);
            if (instructorId % 5 === 0) {
                headerColor = "#39B54A"; // Verde SENA principal
                badgeClass = "bg-success";
            } else if (instructorId % 5 === 1) {
                headerColor = "#34A853"; // Verde más claro
                badgeClass = "bg-success";
            } else if (instructorId % 5 === 2) {
                headerColor = "#138A48"; // Verde medio
                badgeClass = "bg-success";
            } else if (instructorId % 5 === 3) {
                headerColor = "#0E8749"; // Verde oscuro
                badgeClass = "bg-success";
            } else {
                headerColor = "#38B87C"; // Verde menta
                badgeClass = "bg-success";
            }
        }
        
        // HTML mejorado del modal (Actualizado para usar colores SENA)
        const eventDetails = `
            <div class="modal fade" id="eventModal" tabindex="-1" aria-labelledby="eventModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow">
                        <div class="modal-header" style="background-color: ${headerColor}; color: white;">
                            <h5 class="modal-title fw-bold" id="eventModalLabel">
                                ${title || 'Evento de Formación'}
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body p-4">
                            <div class="d-flex align-items-center mb-4">
                                <div class="calendar-icon rounded bg-light p-3 me-3 text-center">
                                    <i class="bi bi-calendar-event fs-3" style="color: ${headerColor};"></i>
                                </div>
                                <div>
                                    <h6 class="mb-0 text-muted fw-normal">Fecha del evento</h6>
                                    <p class="mb-0 fw-bold fs-5">
                                        ${formatDate(clickInfo.event.start)}
                                    </p>
                                </div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <div class="info-card p-3 bg-light rounded mb-2">
                                        <h6 class="text-muted mb-2">
                                            <i class="bi bi-clock me-2"></i>Horario
                                        </h6>
                                        <p class="mb-0 fw-bold">
                                            ${formatTime(clickInfo.event.start)}
                                            -
                                            ${formatTime(clickInfo.event.end)}
                                        </p>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="info-card p-3 bg-light rounded mb-2">
                                        <h6 class="text-muted mb-2">
                                            <i class="bi bi-geo-alt me-2"></i>Ambiente
                                        </h6>
                                        <p class="mb-0 fw-bold">
                                            ${extendedProps.ambiente || 'No especificado'}
                                        </p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="instructor-info border-top border-bottom py-3 my-3">
                                <div class="d-flex align-items-center">
                                    <div class="instructor-avatar rounded-circle text-white p-3 me-3 d-flex align-items-center justify-content-center" style="width: 50px; height: 50px; background-color: ${headerColor};">
                                        <span class="fw-bold fs-5">${extendedProps.instructor ? extendedProps.instructor.charAt(0).toUpperCase() : 'I'}</span>
                                    </div>
                                    <div>
                                        <h6 class="text-muted mb-1">Instructor</h6>
                                        <p class="mb-0 fw-bold fs-5">${extendedProps.instructor || 'No especificado'}</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="competencia-info mt-3">
                                <h6 class="text-muted mb-2">
                                    <i class="bi bi-book me-2"></i>Competencia
                                </h6>
                                <div class="p-3 bg-light rounded">
                                    <p class="mb-0">${extendedProps.competencia || 'No especificada'}</p>
                                </div>
                            </div>
                            
                            <div class="mt-4">
                                <span class="badge ${badgeClass} py-2 px-3">Formación</span>
                                <span class="badge bg-info py-2 px-3">ID: ${extendedProps.id_programa || 'N/A'}</span>
                            </div>
                        </div>
                        <div class="modal-footer bg-light">
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
        
        // Añadir el modal al documento
        document.body.insertAdjacentHTML('beforeend', eventDetails);
        
        // Mostrar el modal
        const modal = new bootstrap.Modal(document.getElementById('eventModal'));
        modal.show();
        
        // Eliminar el modal del DOM cuando se cierre
        document.getElementById('eventModal').addEventListener('hidden.bs.modal', () => {
            document.getElementById('eventModal').remove();
        });
    }

    // Funciones para mostrar/ocultar mensaje cuando no hay eventos (Actualizado para estilo SENA)
    function showNoEventsMessage() {
        // Verificar si ya existe el mensaje
        let noEventsMsg = document.getElementById('no-events-message');
        
        if (!noEventsMsg) {
            // Crear el mensaje si no existe
            noEventsMsg = document.createElement('div');
            noEventsMsg.id = 'no-events-message';
            noEventsMsg.className = 'mt-4 text-center';
            noEventsMsg.innerHTML = `
                <i class="bi bi-info-circle me-2"></i>
                <span>No hay eventos visibles. Utilice los filtros para visualizar eventos.</span>
            `;
            
            // Insertar después del calendario
            const calendarEl = document.getElementById('calendar');
            if (calendarEl && calendarEl.parentNode) {
                calendarEl.parentNode.insertBefore(noEventsMsg, calendarEl.nextSibling);
            }
        } else {
            // Mostrar si ya existe
            noEventsMsg.style.display = 'block';
        }
    }

    function hideNoEventsMessage() {
        const noEventsMsg = document.getElementById('no-events-message');
        if (noEventsMsg) {
            noEventsMsg.style.display = 'none';
        }
    }

    // Cargar eventos pero iniciar con calendario vacío
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
                
                // Iniciar con calendario vacío
                calendar.removeAllEvents();
                // No agregamos eventos inicialmente
                
                // Mostrar mensaje de que no hay eventos visibles
                showNoEventsMessage();
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
        
        // Mostrar mensaje si no hay eventos después de filtrar
        if (filteredEvents.length === 0) {
            showNoEventsMessage();
        } else {
            hideNoEventsMessage();
            // Ajustar rango de horas después de filtrar
            setTimeout(() => adjustHoursToEvents(), 300);
        }
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

    // Limpiar filtros - Versión actualizada que deja el calendario vacío
    const clearFiltersBtn = document.getElementById('clearFilters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', () => {
            // Limpiar todos los selectores de filtro
            ['instructorFilter', 'programaFilter', 'locationFilter'].forEach(filterId => {
                const element = document.getElementById(filterId);
                if (element) {
                    element.value = '';
                }
            });
            
            // Vaciar el calendario en lugar de mostrar todos los eventos
            calendar.removeAllEvents();
            
            // Mostrar el mensaje de que no hay eventos visibles
            showNoEventsMessage();
            
            console.log('Filtros limpiados - Calendario vacío');
        });
    } else {
        console.error('Botón "clearFilters" no encontrado');
    }

    // Configuración del manejo de filtros responsivo
    const toggleFilters = document.getElementById('toggleFilters');
    const filterForm = document.getElementById('event-filter-form');
    
    if (toggleFilters && filterForm) {
        toggleFilters.addEventListener('click', function() {
            const isExpanded = toggleFilters.getAttribute('aria-expanded') === 'true';
            toggleFilters.setAttribute('aria-expanded', !isExpanded);
            
            if (window.innerWidth <= 992) {
                if (!isExpanded) {
                    // Mostrar filtros
                    filterForm.classList.add('show');
                } else {
                    // Ocultar filtros
                    filterForm.classList.remove('show');
                }
            }
        });
        
        // Manejar cambios de tamaño de ventana
        window.addEventListener('resize', function() {
            if (window.innerWidth > 992) {
                filterForm.classList.remove('show');
                if (toggleFilters) {
                    toggleFilters.setAttribute('aria-expanded', 'false');
                }
            }
        });
    }

    // Inicialización
    loadFilterOptions(); // Cargar las opciones de los filtros
    loadEvents();        // Cargar los eventos (pero no mostrarlos)
    calendar.render();    // Renderizar el calendario
    
    // Recargar eventos cada 5 minutos para mantener el calendario actualizado
    setInterval(loadEvents, 300000);
    
    console.log('Calendario inicializado correctamente con inicio vacío');
});