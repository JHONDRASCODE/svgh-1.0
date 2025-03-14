document.addEventListener('DOMContentLoaded', () => {
    // Configuración y variables
    const requestEvents = '/calendarios/get_all_events/';
    const requestFilterOptions = '/calendarios/get_filter_options/';
    const calendarEl = document.getElementById('calendar');
    const lastUpdateEl = document.getElementById('last-update');
    const fechaActualEl = document.getElementById('fecha-actual');
    const toggleFiltersBtn = document.getElementById('toggleFilters');
    const filterSidebar = document.getElementById('filterSidebar');
    const applyFiltersBtn = document.getElementById('applyFilters');
    const clearFiltersBtn = document.getElementById('clearFilters');
    
    let allEvents = [];
    let calendar;
    
    // Estado de carga
    let isLoading = false;
    
    // Obtener filtros del almacenamiento local si existen
    const savedFilters = JSON.parse(localStorage.getItem('calendarFilters')) || {};
    
    // Actualizar la fecha actual en el encabezado
    function updateCurrentDate() {
        const now = new Date();
        const options = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        
        if (fechaActualEl) {
            fechaActualEl.textContent = now.toLocaleDateString('es-CO', options)
                .replace(/^\w/, (c) => c.toUpperCase());
        }
    }
    
    // Inicializar tooltips para eventos
    function initTooltips() {
        // Inicializar tooltips en eventos del calendario
        tippy('.fc-event', {
            content(reference) {
                const title = reference.getAttribute('data-title') || 'Evento';
                const instructor = reference.getAttribute('data-instructor') || 'No especificado';
                const ambiente = reference.getAttribute('data-ambiente') || 'No especificado';
                const competencia = reference.getAttribute('data-competencia') || 'No especificada';
                
                return `
                    <div class="event-tooltip">
                        <div class="event-tooltip-header">${title}</div>
                        <div class="event-tooltip-content">
                            <div class="event-tooltip-item">
                                <span class="event-tooltip-label">Instructor:</span>
                                <span>${instructor}</span>
                            </div>
                            <div class="event-tooltip-item">
                                <span class="event-tooltip-label">Ambiente:</span>
                                <span>${ambiente}</span>
                            </div>
                            <div class="event-tooltip-item">
                                <span class="event-tooltip-label">Competencia:</span>
                                <span>${competencia}</span>
                            </div>
                        </div>
                    </div>
                `;
            },
            allowHTML: true,
            placement: 'top',
            arrow: true,
            theme: 'light',
            delay: [300, 0],
            duration: [200, 200],
            animation: 'shift-away',
            interactive: true
        });
    }
    
    // Cargar opciones de los filtros desde el endpoint dedicado
    function loadFilterOptions() {
        if (isLoading) return;
        isLoading = true;
        
        console.log("Intentando cargar opciones de filtro desde:", requestFilterOptions);
        
        // Mostrar estado de carga en los selectores
        ['instructorFilter', 'programaFilter', 'locationFilter'].forEach(id => {
            const select = document.getElementById(id);
            if (select) {
                select.disabled = true;
                select.innerHTML = '<option value="">Cargando opciones...</option>';
            }
        });
        
        // Intentar usar el nuevo endpoint para opciones de filtro
        fetch(requestFilterOptions)
            .then(response => {
                console.log("Respuesta del servidor:", response.status);
                if (!response.ok) {
                    throw new Error(`Error HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Datos de filtros recibidos:", data);
                
                // Poblar instructores
                if (data.instructores && Array.isArray(data.instructores)) {
                    console.log(`Procesando ${data.instructores.length} instructores`);
                    populateSelectOptions('instructorFilter', data.instructores, 'id', 'nombre', 'Todos los instructores');
                } else {
                    console.warn("No se encontraron instructores en la respuesta");
                    initializeFilterDefault('instructorFilter', 'Todos los instructores');
                }
                
                // Poblar programas
                if (data.programas && Array.isArray(data.programas)) {
                    console.log(`Procesando ${data.programas.length} programas`);
                    populateSelectOptions('programaFilter', data.programas, 'id', 'nombre', 'Todos los programas');
                } else {
                    console.warn("No se encontraron programas en la respuesta");
                    initializeFilterDefault('programaFilter', 'Todos los programas');
                }
                
                // Poblar ambientes
                if (data.ambientes && Array.isArray(data.ambientes)) {
                    console.log(`Procesando ${data.ambientes.length} ambientes`);
                    populateSelectOptions('locationFilter', data.ambientes, 'id', 'nombre', 'Todos los ambientes');
                } else {
                    console.warn("No se encontraron ambientes en la respuesta");
                    initializeFilterDefault('locationFilter', 'Todos los ambientes');
                }
                
                // Restaurar filtros guardados
                restoreSavedFilters();
            })
            .catch(error => {
                console.error('Error al cargar filtros del endpoint:', error);
                console.log('Intentando cargar filtros usando el método alternativo...');
                
                // Inicializar filtros con valores por defecto
                initializeFilterDefaults();
                
                // Fallback al método anterior si el nuevo endpoint falla
                loadFilterOptionsFromEvents();
            })
            .finally(() => {
                isLoading = false;
            });
    }
    
    // Inicializar un filtro con valor por defecto
    function initializeFilterDefault(filterId, defaultText) {
        const select = document.getElementById(filterId);
        if (select) {
            select.disabled = false;
            select.innerHTML = `<option value="">${defaultText}</option>`;
        }
    }
    
    // Inicializar todos los filtros con valores por defecto
    function initializeFilterDefaults() {
        // Función de emergencia para garantizar que los filtros tengan al menos las opciones por defecto
        initializeFilterDefault('instructorFilter', 'Todos los instructores');
        initializeFilterDefault('programaFilter', 'Todos los programas');
        initializeFilterDefault('locationFilter', 'Todos los ambientes');
        
        console.log("Inicializados filtros con valores por defecto");
    }
    
    // Método de respaldo: cargar opciones de filtro desde los eventos
    function loadFilterOptionsFromEvents() {
        if (isLoading) return;
        isLoading = true;
        
        console.log("Intentando cargar opciones de filtro desde eventos:", requestEvents);
        
        fetch(requestEvents)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Asegurarse de que data.events existe
                const events = data.events || [];
                console.log(`Datos recibidos: ${events.length} eventos para filtros`);
                
                if (events.length === 0) {
                    console.warn("No se encontraron eventos para extraer filtros");
                    initializeFilterDefaults();
                    return;
                }
                
                // Poblar los selectores con opciones únicas
                populateFilter('instructorFilter', events, 'id_instructor', 'instructor');
                populateFilter('programaFilter', events, 'id_programa', 'programa');
                populateFilter('locationFilter', events, 'id_ambiente', 'ambiente');
                
                // Restaurar filtros guardados
                restoreSavedFilters();
            })
            .catch(error => {
                console.error('Error al cargar los filtros desde eventos:', error);
                showNotification('Error al cargar opciones de filtro', 'error');
                
                // Inicializar con valores por defecto en caso de error
                initializeFilterDefaults();
            })
            .finally(() => {
                isLoading = false;
            });
    }
    
    // Nueva función para poblar los selectores de forma eficiente
    function populateSelectOptions(selectId, options, valueKey, textKey, defaultText) {
        const selectElement = document.getElementById(selectId);
        if (!selectElement) {
            console.error(`Elemento no encontrado: ${selectId}`);
            return;
        }
        
        // Habilitar el selector
        selectElement.disabled = false;
        
        // Limpiar opciones existentes
        selectElement.innerHTML = '';
        
        // Agregar opción por defecto
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = defaultText;
        selectElement.appendChild(defaultOption);
        
        // Agregar opciones
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option[valueKey];
            optionElement.textContent = option[textKey];
            selectElement.appendChild(optionElement);
        });
        
        console.log(`Filtro ${selectId} poblado con ${options.length} opciones`);
    }

    // Función para poblar las opciones de los filtros (método anterior)
    function populateFilter(filterId, data, idKey, textKey) {
        const filterElement = document.getElementById(filterId);
        if (!filterElement) {
            console.error(`Elemento no encontrado: ${filterId}`);
            return;
        }
        
        // Habilitar el selector
        filterElement.disabled = false;
        
        // Limpiar opciones existentes
        filterElement.innerHTML = '';
        
        // Agregar opción por defecto
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = `Todos los ${filterId.replace('Filter', '').toLowerCase()}es`;
        filterElement.appendChild(defaultOption);
        
        // Crear mapa para valores únicos (evita duplicados y mantiene orden)
        const uniqueMap = new Map();
        
        // Filtrar elementos únicos y ordenar
        data.forEach(item => {
            if (item[idKey] && item[textKey] && !uniqueMap.has(item[idKey])) {
                uniqueMap.set(item[idKey], item[textKey]);
            }
        });
        
        // Convertir a array, ordenar alfabéticamente y agregar al select
        const sortedItems = Array.from(uniqueMap.entries())
            .sort((a, b) => a[1].localeCompare(b[1]));
            
        sortedItems.forEach(([id, text]) => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = text;
            filterElement.appendChild(option);
        });
        
        console.log(`Filtro ${filterId} poblado con ${sortedItems.length} opciones`);
    }
    
    // Restaurar filtros guardados
    function restoreSavedFilters() {
        if (Object.keys(savedFilters).length === 0) return;
        
        console.log("Restaurando filtros guardados:", savedFilters);
        
        // Restaurar valores de los filtros
        Object.entries(savedFilters).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element && value) {
                element.value = value;
                console.log(`Restaurado filtro ${id} al valor ${value}`);
            }
        });
        
        // Aplicar filtros restaurados
        filterEvents();
    }
    
    // Guardar filtros actuales en localStorage
    function saveCurrentFilters() {
        const currentFilters = {};
        
        ['instructorFilter', 'programaFilter', 'locationFilter'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                currentFilters[id] = element.value;
            }
        });
        
        localStorage.setItem('calendarFilters', JSON.stringify(currentFilters));
        console.log('Filtros guardados:', currentFilters);
    }

    // Inicializar el calendario
    function initCalendar() {
        calendar = new FullCalendar.Calendar(calendarEl, {
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
            events: function(info, successCallback, failureCallback) {
                // Usar el rango de fechas visible para solicitar eventos
                loadEventsByDateRange(info.start, info.end, successCallback, failureCallback);
            },
            eventClick: clickInfo => showEventModal(clickInfo),
            eventDidMount: function(info) {
                // Asignar clase según tipo de evento basado en alguna propiedad
                const eventType = determineEventType(info.event);
                info.el.classList.add(`event-${eventType}`);
                
                // Agregar datos para tooltip
                info.el.setAttribute('data-title', info.event.title);
                info.el.setAttribute('data-instructor', info.event.extendedProps.instructor || 'No especificado');
                info.el.setAttribute('data-ambiente', info.event.extendedProps.ambiente || 'No especificado');
                info.el.setAttribute('data-competencia', info.event.extendedProps.competencia || 'No especificada');
            },
            height: 'auto',
            timeZone: 'local',
            loading: function(isLoading) {
                // Mostrar/ocultar indicador de carga
                const loadingIndicator = document.getElementById('loading-indicator');
                if (loadingIndicator) {
                    loadingIndicator.style.display = isLoading ? 'flex' : 'none';
                }
            },
            windowResize: function(arg) {
                // Ajustar vista en cambios de tamaño de ventana
                if (window.innerWidth < 768) {
                    calendar.changeView('timeGridDay');
                }
            }
        });
        
        calendar.render();
        
        // Inicializar tooltips después de que los eventos se han renderizado
        setTimeout(initTooltips, 1000);
    }
    
    // Cargar eventos por rango de fechas (para FullCalendar datesSet)
    function loadEventsByDateRange(startDate, endDate, successCallback, failureCallback) {
        if (isLoading) {
            failureCallback({ message: 'Ya hay una carga en progreso' });
            return;
        }
        
        isLoading = true;
        
        // Obtener valores de los filtros
        const instructorValue = document.getElementById('instructorFilter')?.value || '';
        const programaValue = document.getElementById('programaFilter')?.value || '';
        const ambienteValue = document.getElementById('locationFilter')?.value || '';
        
        // Construir URL con parámetros
        let url = new URL(requestEvents, window.location.origin);
        
        // Añadir parámetros de rango de fechas
        if (startDate) url.searchParams.append('start', startDate.toISOString());
        if (endDate) url.searchParams.append('end', endDate.toISOString());
        
        // Añadir parámetros de filtro
        if (instructorValue) url.searchParams.append('instructor_id', instructorValue);
        if (programaValue) url.searchParams.append('programa_id', programaValue);
        if (ambienteValue) url.searchParams.append('ambiente_id', ambienteValue);
        
        console.log("Cargando eventos desde:", url.toString());
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data || !data.events) {
                    showNotification('Formato de datos incorrecto', 'error');
                    console.error('Formato de datos incorrecto:', data);
                    failureCallback({ message: 'Datos incorrectos' });
                    return;
                }
                
                // Actualizar última actualización
                if (lastUpdateEl) {
                    const now = new Date();
                    lastUpdateEl.textContent = now.toLocaleTimeString('es-CO', {
                        hour: '2-digit', 
                        minute: '2-digit',
                        second: '2-digit'
                    });
                }
                
                // Guardar todos los eventos para filtrado local
                allEvents = data.events;
                
                // Mapear eventos para FullCalendar
                const formattedEvents = allEvents.map(event => {
                    return {
                        id: event.id || `${event.id_programa || 'prog'}-${event.id_instructor || 'inst'}-${event.id_ambiente || 'amb'}-${new Date(event.startDate).getTime()}`,
                        title: event.programa || 'Evento sin título',
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
                    };
                });
                
                console.log(`${formattedEvents.length} eventos cargados y mapeados`);
                
                // Devolver eventos formateados a FullCalendar
                successCallback(formattedEvents);
                
                // Re-inicializar tooltips después de cargar nuevos eventos
                setTimeout(initTooltips, 1000);
                
                // Mostrar notificación de actualización (solo si es recarga)
                if (startDate && endDate) {
                    showNotification('Eventos actualizados correctamente', 'success');
                }
            })
            .catch(error => {
                console.error('Error al cargar eventos:', error);
                failureCallback(error);
                showNotification('Error al cargar eventos', 'error');
            })
            .finally(() => {
                isLoading = false;
            });
    }
    
    // Cargar eventos (método compatible con versión anterior)
    function loadEvents() {
        if (isLoading) return;
        
        // Actualizar el calendario con los eventos
        calendar.refetchEvents();
    }
    
    // Determinar tipo de evento (instructor, programa, ambiente)
    function determineEventType(event) {
        const props = event.extendedProps;
        
        // Determinar tipo basado en qué filtro está activo
        const instructorFilter = document.getElementById('instructorFilter');
        const programaFilter = document.getElementById('programaFilter');
        const ambienteFilter = document.getElementById('locationFilter');
        
        if (instructorFilter && instructorFilter.value) {
            return 'instructor';
        } else if (programaFilter && programaFilter.value) {
            return 'programa';
        } else if (ambienteFilter && ambienteFilter.value) {
            return 'ambiente';
        }
        
        // Por defecto o aleatorio si no hay filtro activo
        const types = ['instructor', 'programa', 'ambiente'];
        const hashCode = (str) => {
            let hash = 0;
            for (let i = 0; i < str.length; i++) {
                hash = ((hash << 5) - hash) + str.charCodeAt(i);
                hash |= 0;
            }
            return Math.abs(hash);
        };
        
        // Usar el ID del evento para determinar un tipo consistente
        const eventId = event.id || event.title;
        return types[hashCode(eventId) % types.length];
    }

    // Mostrar modal con detalles del evento
    function showEventModal(clickInfo) {
        const { title, extendedProps } = clickInfo.event;
        console.log("Evento seleccionado:", clickInfo.event);
        
        // Formatear fechas para mejor visualización
        const startDate = clickInfo.event.start ? clickInfo.event.start.toLocaleDateString('es-CO', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        }) : 'No especificada';
        
        const startTime = clickInfo.event.start ? clickInfo.event.start.toLocaleTimeString('es-CO', {
            hour: '2-digit',
            minute: '2-digit'
        }) : '';
        
        const endTime = clickInfo.event.end ? clickInfo.event.end.toLocaleTimeString('es-CO', {
            hour: '2-digit',
            minute: '2-digit'
        }) : 'No especificada';
        
        // Determinar el tipo y su icono correspondiente
        const eventType = determineEventType(clickInfo.event);
        let typeIcon, typeClass;
        
        switch(eventType) {
            case 'instructor':
                typeIcon = 'bi-person-badge';
                typeClass = 'text-success';
                break;
            case 'programa':
                typeIcon = 'bi-journal-bookmark';
                typeClass = 'text-primary';
                break;
            case 'ambiente':
                typeIcon = 'bi-building';
                typeClass = 'text-warning';
                break;
            default:
                typeIcon = 'bi-calendar-event';
                typeClass = 'text-info';
        }
        
        // Crear contenido modal mejorado
        const eventDetails = `
            <div class="modal fade event-modal" id="eventModal" tabindex="-1" aria-labelledby="eventModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow">
                        <div class="modal-header">
                            <h5 class="modal-title" id="eventModalLabel">
                                <i class="bi ${typeIcon} me-2 ${typeClass}"></i>
                                ${title || 'Evento'}
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="event-detail">
                                <div class="event-detail-label">
                                    <i class="bi bi-calendar3 ${typeClass}"></i> Fecha y Hora
                                </div>
                                <div class="event-detail-value">
                                    ${startDate}<br>
                                    <strong>Inicio:</strong> ${startTime} - <strong>Fin:</strong> ${endTime}
                                </div>
                            </div>
                            
                            <div class="event-detail">
                                <div class="event-detail-label">
                                    <i class="bi bi-person-fill ${typeClass}"></i> Instructor
                                </div>
                                <div class="event-detail-value">
                                    ${extendedProps.instructor || 'No especificado'}
                                </div>
                            </div>
                            
                            <div class="event-detail">
                                <div class="event-detail-label">
                                    <i class="bi bi-award-fill ${typeClass}"></i> Competencia
                                </div>
                                <div class="event-detail-value">
                                    ${extendedProps.competencia || 'No especificada'}
                                </div>
                            </div>
                            
                            <div class="event-detail">
                                <div class="event-detail-label">
                                    <i class="bi bi-building-fill ${typeClass}"></i> Ambiente
                                </div>
                                <div class="event-detail-value">
                                    ${extendedProps.ambiente || 'No especificado'}
                                </div>
                            </div>
                            
                            <div class="event-detail">
                                <div class="event-detail-label">
                                    <i class="bi bi-journal-bookmark-fill ${typeClass}"></i> Programa
                                </div>
                                <div class="event-detail-value">
                                    ${extendedProps.id_programa ? clickInfo.event.title : 'No especificado'}
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer bg-light">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                                <i class="bi bi-x-circle me-1"></i> Cerrar
                            </button>
                            
                            <button type="button" class="btn btn-success" onclick="shareEvent('${encodeURIComponent(JSON.stringify({
                                title: title,
                                instructor: extendedProps.instructor,
                                competencia: extendedProps.competencia,
                                ambiente: extendedProps.ambiente,
                                fecha: startDate,
                                horaInicio: startTime,
                                horaFin: endTime
                            }))}')">
                                <i class="bi bi-share me-1"></i> Compartir
                            </button>
                        </div>
                    </div>
                </div>
            </div>`;
        
        // Eliminar modal anterior si existe
        const existingModal = document.getElementById('eventModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Agregar modal al DOM y mostrarlo
        document.body.insertAdjacentHTML('beforeend', eventDetails);
        const modalElement = document.getElementById('eventModal');
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        
        // Limpiar modal al cerrarse
        modalElement.addEventListener('hidden.bs.modal', () => {
            modalElement.remove();
        });
    }

    // Función global para compartir evento
    window.shareEvent = function(eventDataEncoded) {
        try {
            const eventData = JSON.parse(decodeURIComponent(eventDataEncoded));
            
            // Crear texto para compartir
            const shareText = `
                📅 *Evento: ${eventData.title}*
                👨‍🏫 Instructor: ${eventData.instructor}
                📚 Competencia: ${eventData.competencia}
                🏢 Ambiente: ${eventData.ambiente}
                📆 Fecha: ${eventData.fecha}
                ⏰ Hora: ${eventData.horaInicio} - ${eventData.horaFin}
                
                🔗 Sistema de Gestión de Horarios SENA
            `.trim();
            
            // Comprobar si el navegador soporta Web Share API
            if (navigator.share) {
                navigator.share({
                    title: `Horario: ${eventData.title}`,
                    text: shareText,
                })
                .catch(error => {
                    console.error('Error al compartir:', error);
                    copyToClipboard(shareText);
                });
            } else {
                // Fallback para navegadores que no soportan Web Share API
                copyToClipboard(shareText);
            }
        } catch (error) {
            console.error('Error al procesar datos para compartir:', error);
            showNotification('Error al compartir evento', 'error');
        }
    };
    
    // Función para copiar al portapapeles
    function copyToClipboard(text) {
        if (navigator.clipboard && window.isSecureContext) {
            // Usar la API moderna de Clipboard si está disponible
            navigator.clipboard.writeText(text)
                .then(() => showNotification('Información copiada al portapapeles', 'success'))
                .catch(err => {
                    console.error('Error al copiar usando Clipboard API:', err);
                    fallbackCopyToClipboard(text);
                });
        } else {
            // Fallback para navegadores que no soportan Clipboard API
            fallbackCopyToClipboard(text);
        }
    }
    
    // Método de respaldo para copiar al portapapeles
    function fallbackCopyToClipboard(text) {
        // Crear elemento temporal
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                showNotification('Información copiada al portapapeles', 'success');
            } else {
                showNotification('No se pudo copiar la información', 'error');
            }
        } catch (err) {
            console.error('Error al copiar al portapapeles:', err);
            showNotification('Error al copiar la información', 'error');
        }
        
        document.body.removeChild(textArea);
    }
    
    // Mostrar notificación
    function showNotification(message, type = 'info') {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : (type === 'success' ? 'success' : 'info')} notification-toast`;
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi ${type === 'error' ? 'bi-exclamation-circle' : (type === 'success' ? 'bi-check-circle' : 'bi-info-circle')} me-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        notification.style.position = 'fixed';
        notification.style.bottom = '20px';
        notification.style.right = '20px';
        notification.style.maxWidth = '300px';
        notification.style.zIndex = '9999';
        notification.style.boxShadow = '0 5px 15px rgba(0,0,0,0.2)';
        notification.style.borderRadius = '8px';
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(20px)';
        notification.style.transition = 'opacity 0.3s, transform 0.3s';
        
        document.body.appendChild(notification);
        
        // Animar entrada
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 10);
        
        // Eliminar después de 4 segundos
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 4000);
    }

    // Filtrar eventos según los filtros seleccionados
    function filterEvents() {
        if (!calendar) return;
        
        console.log("Aplicando filtros a eventos...");
        
        // Usar el método refetchEvents para aplicar los filtros del lado del servidor
        // Los filtros se aplicarán automáticamente en el método loadEventsByDateRange
        calendar.refetchEvents();
        
        // Re-inicializar tooltips después de filtrar
        setTimeout(initTooltips, 500);
        
        // Guardar filtros actuales
        saveCurrentFilters();
    }

    // Toggle sidebar en dispositivos móviles
    function toggleFilterSidebar() {
        if (filterSidebar) {
            filterSidebar.classList.toggle('active');
        }
    }

    // Inicialización
    function init() {
        // Actualizar fecha actual
        updateCurrentDate();
        
        // Manejar botón de toggle filtros en móvil
        if (toggleFiltersBtn && filterSidebar) {
            toggleFiltersBtn.addEventListener('click', toggleFilterSidebar);
        }
        
        // Inicializar calendario
        initCalendar();
        
        // Cargar opciones para filtros
        loadFilterOptions();
        
        // Manejar botón de aplicar filtros
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', filterEvents);
        }
        
        // Limpiar filtros
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                ['instructorFilter', 'programaFilter', 'locationFilter'].forEach(id => {
                    const element = document.getElementById(id);
                    if (element) {
                        element.value = '';
                    }
                });
                
                // Aplicar limpieza de filtros
                filterEvents();
                
                // Limpiar localStorage
                localStorage.removeItem('calendarFilters');
                
                // Notificar al usuario
                showNotification('Filtros restablecidos', 'info');
            });
        }
        
        // Actualizar eventos periódicamente (cada 5 minutos)
        setInterval(() => {
            calendar.refetchEvents();
        }, 300000);
        
        // Garantizar que los filtros tengan al menos las opciones por defecto
        // si después de 2 segundos no se han cargado correctamente
        setTimeout(initializeFilterDefaults, 2000);
        
        console.log('Calendario inicializado correctamente');
    }
    
    // Iniciar aplicación
    init();
});