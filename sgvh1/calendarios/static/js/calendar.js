document.addEventListener('DOMContentLoaded', () => {
	const request = '/calendarios/get_all_events/';
	const calendarEl = document.getElementById('calendar');
	let allEvents = [];

	// Cargar opciones de los filtros desde la API
	function loadFilterOptions() {
		fetch('/eventos/')
			.then(response => response.json())
			.then(data => {
				populateFilter('instructorFilter', data, 'id_instructor', 'instructor');
				populateFilter('programaFilter', data, 'id_programa', 'programa');
				populateFilter('locationFilter', data, 'id_ambiente', 'ambiente');
			})
			.catch(error => console.error('Error al cargar los filtros:', error));
	}

	// Función para poblar las opciones de los filtros
	function populateFilter(filterId, data, idKey, textKey) {
		const filterElement = document.getElementById(filterId);
		const uniqueItems = data.filter(item => item[idKey]);
		uniqueItems.forEach(item => {
			const option = document.createElement('option');
			option.value = item[idKey];
			option.textContent = item[textKey];
			filterElement.appendChild(option);
		});
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
	});

	// Mostrar modal con detalles del evento
	function showEventModal(clickInfo) {
		const { title, extendedProps } = clickInfo.event;
		const eventDetails = `
            <div class="modal fade" id="eventModal" tabindex="-1" aria-labelledby="eventModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="eventModalLabel">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p><strong>Instructor:</strong> ${extendedProps.instructor}</p>
                            <p><strong>Competencia:</strong> ${extendedProps.competencia}</p>
                            <p><strong>Ambiente:</strong> ${extendedProps.location}</p>
                            <p><strong>Hora de inicio:</strong> ${clickInfo.event.start.toLocaleTimeString(
															[],
															{ hour: '2-digit', minute: '2-digit' }
														)}</p>
                            <p><strong>Hora de finalización:</strong> ${clickInfo.event.end.toLocaleTimeString(
															[],
															{ hour: '2-digit', minute: '2-digit' }
														)}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>`;
		document.body.insertAdjacentHTML('beforeend', eventDetails);
		new bootstrap.Modal(document.getElementById('eventModal')).show();
		document.getElementById('eventModal').addEventListener('hidden.bs.modal', () => {
			document.getElementById('eventModal').remove();
		});
	}

	// Cargar eventos
	function loadEvents() {
		fetch(request)
			.then(response => response.json())
			.then(data => {
				allEvents = data.events.map(event => ({
					title: event.programa,
					start: event.startDate,
					end: event.endDate,
					extendedProps: {
						id_instructor: event.id_instructor,
						instructor: event.instructor,
						id_location: event.id_ambiente,
						location: event.ambiente,
						competencia: event.competencia,
						id_programa: event.id_programa,
					},
				}));
				calendar.addEventSource(allEvents);
			})
			.catch(console.error);
	}

	// Filtrar eventos según los filtros seleccionados
	function filterEvents() {
		const filters = ['instructorFilter', 'programaFilter', 'locationFilter'].map(id =>
			document.getElementById(id)
		);
		const filteredEvents = allEvents.filter(event =>
			filters.every(filter => {
				const filterKey = filter.id.replace('Filter', '').toLowerCase();
				return !filter.value || event.extendedProps[`id_${filterKey}`] == filter.value;
			})
		);
		calendar.removeAllEvents();
		calendar.addEventSource(filteredEvents);
	}

	// Asignar eventos a los filtros
	['instructorFilter', 'programaFilter', 'locationFilter'].forEach(filterId => {
		document.getElementById(filterId).addEventListener('change', filterEvents);
	});

	// Limpiar filtros
	document.getElementById('clearFilters').addEventListener('click', () => {
		['instructorFilter', 'programaFilter', 'locationFilter'].forEach(filterId => {
			document.getElementById(filterId).value = '';
		});
		filterEvents();
	});

	loadFilterOptions(); // Cargar las opciones de los filtros al cargar la página
	loadEvents(); // Cargar los eventos
	calendar.render();
});
