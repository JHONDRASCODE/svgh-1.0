// El calendario utiliza las bibliotecas FullCalendar y Bootstrap cargadas desde el HTML

document.addEventListener("DOMContentLoaded", () => {
  // ----- CÓDIGO DEL CALENDARIO SENA -----
  // IMPORTANTE: Asegúrate de que esta ruta sea correcta y coincida con tu configuración de URLs en Django
  const baseApiUrl = "/calendarios/get_all_events/"
  const calendarEl = document.getElementById("calendar")
  let allEvents = []
  const originalFilterOptions = {
    instructor: [],
    programa: [],
    ambiente: [],
  }

  // Mapa de colores para instructores
  const instructorColors = {
    // Colores base para instructores (se asignarán dinámicamente)
    colors: [
      { bg: "#39B54A", border: "#33a043" }, // Verde SENA principal
      { bg: "#34A853", border: "#2d9249" }, // Verde más claro
      { bg: "#138A48", border: "#0f7a3e" }, // Verde medio
      { bg: "#0E8749", border: "#0a7038" }, // Verde oscuro
      { bg: "#38B87C", border: "#30a46c" }, // Verde menta
      { bg: "#4CAF50", border: "#43A047" }, // Verde material
      { bg: "#009688", border: "#00897B" }, // Verde azulado
      { bg: "#8BC34A", border: "#7CB342" }, // Verde lima
      { bg: "#3F51B5", border: "#3949AB" }, // Índigo
      { bg: "#2196F3", border: "#1E88E5" }, // Azul
      { bg: "#03A9F4", border: "#039BE5" }, // Azul claro
      { bg: "#00BCD4", border: "#00ACC1" }, // Cian
      { bg: "#607D8B", border: "#546E7A" }, // Azul grisáceo
      { bg: "#9C27B0", border: "#8E24AA" }, // Púrpura
      { bg: "#E91E63", border: "#D81B60" }, // Rosa
      { bg: "#F44336", border: "#E53935" }, // Rojo
      { bg: "#FF5722", border: "#F4511E" }, // Naranja oscuro
      { bg: "#FF9800", border: "#FB8C00" }, // Naranja
      { bg: "#FFC107", border: "#FFB300" }, // Ámbar
      { bg: "#795548", border: "#6D4C41" }, // Marrón
    ],
    // Mapa para almacenar la asignación de colores a instructores
    instructorMap: {},
  }

  // Función para obtener la hora y fecha de Colombia (UTC-5)
  function getColombiaDateTime() {
    const now = new Date()
    const colombiaOffset = -5 * 60
    const localOffset = now.getTimezoneOffset()
    const offsetDiff = localOffset + colombiaOffset
    const colombiaTime = new Date(now.getTime() + offsetDiff * 60 * 1000)
    return colombiaTime
  }

  // Función para actualizar la hora y fecha de Colombia
  function updateColombiaTime() {
    const dateOptions = {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    }

    const timeOptions = {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    }

    const colombiaDateTime = getColombiaDateTime()
    const dateStr = colombiaDateTime.toLocaleDateString("es-CO", dateOptions)
    const timeStr = colombiaDateTime.toLocaleTimeString("es-CO", timeOptions)
    const formattedDate = dateStr.charAt(0).toUpperCase() + dateStr.slice(1)

    const timeElement = document.getElementById("current-time")
    if (timeElement) {
      timeElement.textContent = `${formattedDate} - ${timeStr}`
    }
  }

  // Actualizar inmediatamente y luego cada segundo
  updateColombiaTime()
  setInterval(updateColombiaTime, 1000)

  // Función para mostrar mensaje inicial - MODIFICADA PARA NO HACER NADA
  function showInitialMessage() {
    // Función vacía para evitar que se muestre el mensaje
    return
  }

  // Función para ocultar mensaje inicial
  function hideInitialMessage() {
    const initialMsg = document.getElementById("initial-message")
    if (initialMsg) {
      initialMsg.style.display = "none"
    }
  }

  // Función para analizar correctamente las fechas del servidor
  function parseServerDate(dateString) {
    try {
      // Intentar crear una fecha directamente
      const date = new Date(dateString)

      // Verificar si la fecha es válida
      if (!isNaN(date.getTime())) {
        return date
      }

      // Si no es válida, intentar parsear manualmente
      // Formato esperado: "YYYY-MM-DD HH:MM:SS" o similar
      if (typeof dateString === "string") {
        // Eliminar cualquier 'Z' o zona horaria al final si existe
        const cleanDateStr = dateString.replace(/Z|(\+|-)\d{2}:?\d{2}$/, "")

        // Crear la fecha con el string limpio
        const manualDate = new Date(cleanDateStr)
        if (!isNaN(manualDate.getTime())) {
          return manualDate
        }
      }

      console.error("No se pudo parsear la fecha:", dateString)
      return null
    } catch (error) {
      console.error("Error al parsear fecha:", error, dateString)
      return null
    }
  }

  // Función para asignar un color a un instructor
  function getInstructorColor(instructorId, instructorName) {
    // Si ya tiene un color asignado, devolverlo
    if (instructorColors.instructorMap[instructorId]) {
      return instructorColors.instructorMap[instructorId]
    }

    // Asignar un nuevo color basado en el ID del instructor
    const colorIndex = Object.keys(instructorColors.instructorMap).length % instructorColors.colors.length
    const color = instructorColors.colors[colorIndex]

    // Guardar la asignación
    instructorColors.instructorMap[instructorId] = {
      bg: color.bg,
      border: color.border,
      name: instructorName,
    }

    return instructorColors.instructorMap[instructorId]
  }

  // Función mejorada para cargar eventos pero NO mostrarlos automáticamente
  function loadAllEvents() {
    // Mostrar indicador de carga
    const loadingIndicator = document.getElementById("loading-indicator")
    if (loadingIndicator) {
      loadingIndicator.style.display = "block"
    }

    console.log("Cargando todos los eventos desde:", baseApiUrl)

    // Realizar la petición sin parámetros de rango para obtener todos los eventos
    fetch(baseApiUrl)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Error HTTP: ${response.status}`)
        }
        return response.json()
      })
      .then((data) => {
        console.log("Datos recibidos del servidor:", data)

        if (!data || !data.events) {
          console.error("Formato de datos incorrecto:", data)
          if (loadingIndicator) {
            loadingIndicator.style.display = "none"
          }
          return
        }

        // Transformar eventos al formato de FullCalendar con manejo mejorado de fechas
        allEvents = data.events
          .map((event) => {
            try {
              // Parsear fechas correctamente
              const startDate = parseServerDate(event.startDate)
              const endDate = parseServerDate(event.endDate)

              // Verificar que las fechas sean válidas
              if (!startDate || !endDate) {
                console.error("Fecha inválida en evento:", event)
                return null
              }

              // Imprimir información de depuración para las fechas
              console.log(`Evento ${event.id_programa} - ${event.programa}:`, {
                startDate: startDate.toLocaleString(),
                endDate: endDate.toLocaleString(),
                startDateOriginal: event.startDate,
                endDateOriginal: event.endDate,
              })

              // Obtener color para el instructor desde los colores definidos en el template
              let backgroundColor = "#39B54A" // Color por defecto
              let borderColor = "#33a043" // Borde por defecto

              // Usar los colores definidos en el template si existen
              if (window.instructorColors && window.instructorColors[event.id_instructor]) {
                backgroundColor = window.instructorColors[event.id_instructor].bg
                borderColor = window.instructorColors[event.id_instructor].border
              }

              // Crear el evento con el formato correcto para FullCalendar
              return {
                id: `${event.id_programa}-${event.id_instructor}-${event.id_ambiente}-${startDate.getTime()}`,
                title: event.programa,
                start: startDate,
                end: endDate,
                allDay: false, // Asegurarse de que no sea un evento de todo el día
                backgroundColor: backgroundColor,
                borderColor: borderColor,
                textColor: "#ffffff",
                className: `event-instructor-${event.id_instructor}`,
                extendedProps: {
                  id_instructor: event.id_instructor,
                  instructor: event.instructor,
                  id_ambiente: event.id_ambiente,
                  ambiente: event.ambiente,
                  competencia: event.competencia,
                  id_programa: event.id_programa,
                  startDateOriginal: event.startDate,
                  endDateOriginal: event.endDate,
                },
              }
            } catch (error) {
              console.error("Error al procesar evento:", error, event)
              return null
            }
          })
          .filter((event) => event !== null) // Filtrar eventos con fechas inválidas

        console.log(`${allEvents.length} eventos cargados y mapeados`)

        // Mostrar algunos eventos para depuración
        if (allEvents.length > 0) {
          console.log("Ejemplo de evento:", allEvents[0])
        }

        // Poblar los filtros con los datos recibidos
        populateFilters(data.events)

        // Guardar las opciones originales para el buscador
        saveOriginalFilterOptions()

        // Ocultar indicador de carga
        if (loadingIndicator) {
          loadingIndicator.style.display = "none"
        }

        // Si hay un filtro activo, aplicarlo inmediatamente
        const instructorFilter = document.getElementById("instructorFilter")
        if (instructorFilter && instructorFilter.value) {
          filterEvents()
        }
      })
      .catch((error) => {
        console.error("Error al cargar eventos:", error)
        // Ocultar indicador de carga en caso de error
        if (loadingIndicator) {
          loadingIndicator.style.display = "none"
        }
      })
  }

  // Función para generar la leyenda de instructores - ELIMINADA
  function generateInstructorLegend() {
    // Esta función está desactivada completamente
    return
  }

  // Función para guardar las opciones originales de los filtros
  function saveOriginalFilterOptions() {
    const instructorFilter = document.getElementById("instructorFilter")
    const programaFilter = document.getElementById("programaFilter")
    const locationFilter = document.getElementById("locationFilter")

    if (instructorFilter) {
      originalFilterOptions.instructor = Array.from(instructorFilter.options).map((option) => ({
        value: option.value,
        text: option.textContent,
      }))
    }

    if (programaFilter) {
      originalFilterOptions.programa = Array.from(programaFilter.options).map((option) => ({
        value: option.value,
        text: option.textContent,
      }))
    }

    if (locationFilter) {
      originalFilterOptions.ambiente = Array.from(locationFilter.options).map((option) => ({
        value: option.value,
        text: option.textContent,
      }))
    }

    console.log("Opciones originales de filtros guardadas:", originalFilterOptions)
  }

  // Función para poblar todos los filtros a la vez
  function populateFilters(events) {
    console.log("Poblando filtros con eventos:", events.length)
    populateFilter("instructorFilter", events, "id_instructor", "instructor")
    populateFilter("programaFilter", events, "id_programa", "programa")
    populateFilter("locationFilter", events, "id_ambiente", "ambiente")
  }

  // Función para poblar las opciones de un filtro específico
  function populateFilter(filterId, data, idKey, textKey) {
    const filterElement = document.getElementById(filterId)
    if (!filterElement) {
      console.error(`Elemento no encontrado: ${filterId}`)
      return
    }

    // Limpiar opciones existentes excepto la primera
    while (filterElement.options.length > 1) {
      filterElement.remove(1)
    }

    // Crear Set para valores únicos
    const uniqueValues = new Set()
    const uniqueItems = []

    // Filtrar elementos únicos que tengan valores válidos
    data.forEach((item) => {
      if (item[idKey] && !uniqueValues.has(item[idKey]) && item[textKey]) {
        uniqueValues.add(item[idKey])
        uniqueItems.push(item)
      }
    })

    // Agregar opciones al select
    uniqueItems.forEach((item) => {
      const option = document.createElement("option")
      option.value = item[idKey]
      option.textContent = item[textKey]
      filterElement.appendChild(option)
    })

    console.log(`Filtro ${filterId} poblado con ${uniqueItems.length} opciones`)
  }

  // NUEVA FUNCIÓN: Buscar directamente en los eventos
  function searchEvents(searchText) {
    // Si no hay texto de búsqueda, restaurar filtros y limpiar calendario
    if (!searchText) {
      // Restaurar todas las opciones originales en los selectores
      restoreOriginalOptions("instructorFilter", originalFilterOptions.instructor)
      restoreOriginalOptions("programaFilter", originalFilterOptions.programa)
      restoreOriginalOptions("locationFilter", originalFilterOptions.ambiente)

      // Limpiar selectores
      document.getElementById("instructorFilter").value = ""
      document.getElementById("programaFilter").value = ""
      document.getElementById("locationFilter").value = ""

      // Limpiar calendario
      calendar.removeAllEvents()
      hideNoEventsMessage()
      return
    }

    // Convertir a minúsculas para búsqueda insensible a mayúsculas/minúsculas
    const searchLower = searchText.toLowerCase()

    // Filtrar eventos que coincidan con la búsqueda
    const filteredEvents = allEvents.filter((event) => {
      // Buscar en instructor
      const instructorMatch =
        event.extendedProps.instructor && event.extendedProps.instructor.toLowerCase().includes(searchLower)

      // Buscar en programa (título del evento)
      const programaMatch = event.title && event.title.toLowerCase().includes(searchLower)

      // Buscar en ambiente
      const ambienteMatch =
        event.extendedProps.ambiente && event.extendedProps.ambiente.toLowerCase().includes(searchLower)

      // Devolver true si coincide con alguno de los campos
      return instructorMatch || programaMatch || ambienteMatch
    })

    console.log(`Búsqueda "${searchText}": ${filteredEvents.length} eventos coinciden`)

    // Actualizar el calendario con los eventos filtrados
    calendar.removeAllEvents()

    if (filteredEvents.length > 0) {
      calendar.addEventSource(filteredEvents)
      hideNoEventsMessage()
      setTimeout(() => adjustHoursToEvents(), 300)
    } else {
      showNoEventsMessage()
    }

    // También filtrar las opciones en los selectores
    filterSelectOptions(searchText)
  }

  // Función para filtrar las opciones de los selectores según el texto de búsqueda
  function filterSelectOptions(searchText) {
    if (!searchText) {
      // Si no hay texto de búsqueda, restaurar todas las opciones originales
      restoreOriginalOptions("instructorFilter", originalFilterOptions.instructor)
      restoreOriginalOptions("programaFilter", originalFilterOptions.programa)
      restoreOriginalOptions("locationFilter", originalFilterOptions.ambiente)
      return
    }

    // Convertir a minúsculas para búsqueda insensible a mayúsculas/minúsculas
    const searchLower = searchText.toLowerCase()

    // Filtrar opciones de instructor
    filterOptionsInSelect("instructorFilter", originalFilterOptions.instructor, searchLower)

    // Filtrar opciones de programa
    filterOptionsInSelect("programaFilter", originalFilterOptions.programa, searchLower)

    // Filtrar opciones de ambiente
    filterOptionsInSelect("locationFilter", originalFilterOptions.ambiente, searchLower)
  }

  // Función para filtrar opciones en un select específico
  function filterOptionsInSelect(selectId, originalOptions, searchText) {
    const selectElement = document.getElementById(selectId)
    if (!selectElement) return

    // Limpiar opciones actuales excepto la primera (opción por defecto)
    while (selectElement.options.length > 1) {
      selectElement.remove(1)
    }

    // Filtrar y añadir solo las opciones que coinciden con la búsqueda
    const filteredOptions = originalOptions.filter(
      (option) => option.text.toLowerCase().includes(searchText) || option.value === "",
    )

    // Añadir las opciones filtradas
    filteredOptions.forEach((option) => {
      if (option.value === "") return // Saltar la opción por defecto (ya está en el select)

      const newOption = document.createElement("option")
      newOption.value = option.value
      newOption.textContent = option.text
      selectElement.appendChild(newOption)
    })

    console.log(`Filtro ${selectId}: ${filteredOptions.length - 1} opciones coinciden con "${searchText}"`)
  }

  // Función para restaurar las opciones originales de un select
  function restoreOriginalOptions(selectId, originalOptions) {
    const selectElement = document.getElementById(selectId)
    if (!selectElement) return

    // Limpiar opciones actuales
    while (selectElement.options.length > 1) {
      selectElement.remove(1)
    }

    // Restaurar todas las opciones originales (excepto la primera que ya está)
    originalOptions.forEach((option) => {
      if (option.value === "") return // Saltar la opción por defecto

      const newOption = document.createElement("option")
      newOption.value = option.value
      newOption.textContent = option.text
      selectElement.appendChild(newOption)
    })
  }

  // Inicializar el calendario con configuraciones mejoradas
  const calendar = new FullCalendar.Calendar(calendarEl, {
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay",
    },
    initialView: "timeGridWeek",
    nowIndicator: true,
    locale: "es",
    allDaySlot: false,
    height: "auto", // Usar altura automática para evitar desbordamiento
    fixedWeekCount: false, // Permitir que el número de semanas se ajuste

    // Configuración para mostrar horas en formato de 12 horas (AM/PM)
    slotLabelFormat: {
      hour: "numeric",
      hour12: true,
      omitZeroMinute: true,
      meridiem: "short",
    },

    // Formato de hora para los eventos
    eventTimeFormat: {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
      meridiem: "short",
    },

    events: [], // Iniciar con calendario vacío
    eventClick: (clickInfo) => showEventModal(clickInfo),
    timeZone: "local",

    // Configuraciones para optimizar la visualización de horas
    slotMinTime: "06:00:00", // Comenzar a las 6 AM por defecto
    slotMaxTime: "22:00:00", // Terminar a las 10 PM por defecto
    slotDuration: "01:00:00", // Duración de cada slot (1 hora)

    // Mejoras para evitar amontonamiento
    eventMaxStack: 3, // Limita el número de eventos apilados
    moreLinkClick: "popover", // Muestra popup al hacer clic en "más eventos"
    dayMaxEvents: true, // Muestra link "+más" cuando hay muchos eventos

    // Ajustes específicos para vista de semana para mejorar la visualización
    views: {
      timeGridWeek: {
        eventMinHeight: 22, // Altura mínima del evento
        slotEventOverlap: false, // Evita superposición
        slotDuration: "00:30:00", // Duración de slots de 30 minutos
        slotLabelInterval: "01:00:00", // Etiquetas de hora cada hora
      },
      timeGridDay: {
        eventMinHeight: 25, // Eventos más altos en vista diaria
        slotEventOverlap: false, // Sin superposición
      },
    },

    // Eventos del calendario para manejar la visualización
    viewDidMount: (arg) => {
      // Ajustar horas visibles después de que la vista haya sido montada
      if (arg.view.type === "timeGridWeek" || arg.view.type === "timeGridDay") {
        setTimeout(() => adjustHoursToEvents(), 300)
      }

      // Asegurar que el contenido esté dentro de los límites
      fixCalendarOverflow()
    },

    // Cuando se añaden o cambian eventos
    eventAdd: () => {
      setTimeout(() => {
        adjustHoursToEvents()
        fixCalendarOverflow()
      }, 300)
    },

    // Colorear eventos según su tipo
    eventDidMount: (info) => {
      // Asegura que el texto se corte con elipsis
      info.el.style.overflow = "hidden"
      info.el.style.textOverflow = "ellipsis"
      info.el.style.whiteSpace = "nowrap"

      // Agregar una clase base para todos los eventos
      info.el.classList.add("custom-event")

      // Añadir tooltip para ver información completa al pasar el mouse
      try {
        new bootstrap.Tooltip(info.el, {
          title: `${info.event.title} - ${info.event.extendedProps.instructor || "Sin instructor"}`,
          placement: "top",
          trigger: "hover",
          container: "body",
        })
      } catch (error) {
        console.log("Tooltip no disponible", error)
      }
    },

    // Configuración de carga de datos
    loading: (isLoading) => {
      // Mostrar/ocultar indicador de carga
      var loadingIndicator = document.getElementById("loading-indicator")
      if (loadingIndicator) {
        loadingIndicator.style.display = isLoading ? "block" : "none"
      }
    },
  })

  // Función para corregir cualquier desbordamiento del calendario
  function fixCalendarOverflow() {
    // Asegurar que todos los elementos del calendario estén contenidos
    const fcElements = document.querySelectorAll(".fc-scroller, .fc-timegrid-body, .fc-timegrid-cols, .fc-view-harness")
    fcElements.forEach((el) => {
      el.style.overflow = "hidden"
    })

    // Asegurar que las columnas de fondo estén contenidas
    const bgElements = document.querySelectorAll(".fc-timegrid-col-bg, .fc-bg-event, .fc-non-business, .fc-highlight")
    bgElements.forEach((el) => {
      el.style.overflow = "hidden"
      el.style.position = "absolute"
      el.style.top = "0"
      el.style.left = "0"
      el.style.right = "0"
      el.style.bottom = "0"
      el.style.maxHeight = "100%"
    })

    // Verificar si hay columnas que se extienden fuera del contenedor
    const colBgs = document.querySelectorAll(".fc-timegrid-col-bg")
    colBgs.forEach((bg) => {
      const parent = bg.closest(".fc-timegrid-col")
      if (parent) {
        bg.style.height = parent.offsetHeight + "px"
      }
    })
  }

  // Función para ajustar las horas visibles según los eventos
  function adjustHoursToEvents() {
    const events = calendar.getEvents()
    if (events.length === 0) return

    let earliestHour = 23
    let latestHour = 0

    events.forEach((event) => {
      if (event.start) {
        const startHour = event.start.getHours()
        if (startHour < earliestHour) earliestHour = startHour
      }

      if (event.end) {
        const endHour = event.end.getHours()
        // Si el evento termina justo a la hora en punto, consideramos la hora anterior
        const adjustedEndHour = event.end.getMinutes() === 0 && endHour > 0 ? endHour : endHour + 1

        // Si el evento termina a medianoche (0:00), usar 24 en lugar de 0
        const finalEndHour = endHour === 0 ? 24 : adjustedEndHour

        if (finalEndHour > latestHour) latestHour = finalEndHour
      }
    })

    // Dar margen de 1 hora antes y después, pero con límites más estrictos
    earliestHour = Math.max(6, earliestHour - 1)
    latestHour = Math.min(22, latestHour + 1) // Limitar a 10 PM para evitar desbordamiento

    // Si no hay eventos en un rango amplio, usar un rango predeterminado de horas laborales
    if (earliestHour > 18 || latestHour < 8) {
      earliestHour = 6 // Comenzar a las 6 AM
      latestHour = 22 // Terminar a las 10 PM
    }

    // Formatear horas para FullCalendar (formato 24h)
    const minTime = String(earliestHour).padStart(2, "0") + ":00:00"
    const maxTime = String(latestHour).padStart(2, "0") + ":00:00"

    console.log(`Ajustando rango de horas: ${minTime} - ${maxTime}`)

    // Aplicar nuevas horas
    calendar.setOption("slotMinTime", minTime)
    calendar.setOption("slotMaxTime", maxTime)

    // Asegurar que no haya desbordamiento después de ajustar las horas
    setTimeout(fixCalendarOverflow, 100)
  }

  // Función mejorada para mostrar el modal con detalles del evento
  function showEventModal(clickInfo) {
    const { title, extendedProps } = clickInfo.event
    console.log("Evento clickeado:", clickInfo.event)

    // Formatear fechas para mostrar
    const formatDate = (date) => {
      if (!date) return "No especificada"
      return date.toLocaleDateString("es", {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
      })
    }

    // Formatear horas en formato 12h
    const formatTime = (date) => {
      if (!date) return "No especificada"
      return date.toLocaleTimeString("es", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      })
    }

    // Calcular duración del evento
    const calculateDuration = (start, end) => {
      if (!start || !end) return "Duración no disponible"
      const diff = Math.abs(end - start)
      const hours = Math.floor(diff / (1000 * 60 * 60))
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))

      let duration = ""
      if (hours > 0) duration += `${hours} hora${hours !== 1 ? "s" : ""}`
      if (minutes > 0) duration += `${hours > 0 ? " y " : ""}${minutes} minuto${minutes !== 1 ? "s" : ""}`
      return duration
    }

    // Usar un color estándar para todos los eventos
    const headerColor = "#39B54A" // Color verde SENA estándar

    // HTML mejorado del modal con diseño más limpio y sin duplicaciones
    const eventDetails = `
  <div class="modal fade" id="eventModal" tabindex="-1" aria-labelledby="eventModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content border-0 shadow">
        <div class="modal-header" style="background-color: ${headerColor}; color: white;">
          <h5 class="modal-title fw-bold" id="eventModalLabel">
            ${title || "Evento de Formación"}
          </h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body p-3">
          <!-- Fecha del evento -->
          <div class="mb-3 pb-2 border-bottom">
            <div class="d-flex align-items-center">
              <div class="rounded-circle bg-light p-2 me-3 d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                <i class="bi bi-calendar-event" style="color: ${headerColor}; font-size: 1.2rem;"></i>
              </div>
              <div>
                <h6 class="text-muted mb-1 small">Fecha del evento</h6>
                <p class="mb-0 fw-bold">
                  ${formatDate(clickInfo.event.start)}
                </p>
              </div>
            </div>
          </div>
          
          <!-- Horario -->
          <div class="mb-3 pb-2 border-bottom">
            <div class="d-flex align-items-center">
              <div class="rounded-circle bg-light p-2 me-3 d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                <i class="bi bi-clock" style="color: ${headerColor}; font-size: 1.2rem;"></i>
              </div>
              <div>
                <h6 class="text-muted mb-1 small">Horario</h6>
                <p class="mb-0 fw-bold">
                  ${formatTime(clickInfo.event.start)} - ${formatTime(clickInfo.event.end)}
                </p>
                <p class="mb-0 text-muted small">
                  Duración: ${calculateDuration(clickInfo.event.start, clickInfo.event.end)}
                </p>
              </div>
            </div>
          </div>
          
          <!-- Ambiente -->
          <div class="mb-3 pb-2 border-bottom">
            <div class="d-flex align-items-center">
              <div class="rounded-circle bg-light p-2 me-3 d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                <i class="bi bi-geo-alt" style="color: ${headerColor}; font-size: 1.2rem;"></i>
              </div>
              <div>
                <h6 class="text-muted mb-1 small">Ambiente</h6>
                <p class="mb-0 fw-bold">
                  ${extendedProps.ambiente || "No especificado"}
                </p>
              </div>
            </div>
          </div>
          
          <!-- Instructor -->
          <div class="mb-3 pb-2 border-bottom">
            <div class="d-flex align-items-center">
              <div class="rounded-circle text-white p-2 me-3 d-flex align-items-center justify-content-center" style="width: 40px; height: 40px; background-color: ${headerColor};">
                <span class="fw-bold">${extendedProps.instructor ? extendedProps.instructor.charAt(0).toUpperCase() : "I"}</span>
              </div>
              <div>
                <h6 class="text-muted mb-1 small">Instructor</h6>
                <p class="mb-0 fw-bold">${extendedProps.instructor || "No especificado"}</p>
              </div>
            </div>
          </div>
          
          <!-- Competencia -->
          <div class="mb-3 pb-2 border-bottom">
            <div class="d-flex align-items-start">
              <div class="rounded-circle bg-light p-2 me-3 d-flex align-items-center justify-content-center" style="width: 40px; height: 40px; margin-top: 2px;">
                <i class="bi bi-book" style="color: ${headerColor}; font-size: 1.2rem;"></i>
              </div>
              <div>
                <h6 class="text-muted mb-1 small">Competencia</h6>
                <p class="mb-0">
                  ${extendedProps.competencia || "No especificada"}
                </p>
              </div>
            </div>
          </div>
          
          <!-- Programa de Formación -->
          <div class="mb-2">
            <div class="d-flex align-items-start">
              <div class="rounded-circle bg-light p-2 me-3 d-flex align-items-center justify-content-center" style="width: 40px; height: 40px; margin-top: 2px;">
                <i class="bi bi-journal-text" style="color: ${headerColor}; font-size: 1.2rem;"></i>
              </div>
              <div>
                <h6 class="text-muted mb-1 small">Programa de Formación</h6>
                <p class="mb-0 fw-bold">
                  ${title || "No especificado"}
                </p>
                <p class="mb-0 small text-muted">ID: ${extendedProps.id_programa || "N/A"}</p>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer bg-light">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
        </div>
      </div>
    </div>
  </div>`

    // Eliminar modal anterior si existe
    const existingModal = document.getElementById("eventModal")
    if (existingModal) {
      existingModal.remove()
    }

    // Añadir el modal al documento
    document.body.insertAdjacentHTML("beforeend", eventDetails)

    // Mostrar el modal
    const modal = new bootstrap.Modal(document.getElementById("eventModal"))
    modal.show()

    // Eliminar el modal del DOM cuando se cierre
    document.getElementById("eventModal").addEventListener("hidden.bs.modal", () => {
      document.getElementById("eventModal").remove()
    })
  }

  // Funciones para mostrar/ocultar mensaje cuando no hay eventos
  function showNoEventsMessage() {
    // Verificar si ya existe el mensaje
    let noEventsMsg = document.getElementById("no-events-message")

    if (!noEventsMsg) {
      // Crear el mensaje si no existe
      noEventsMsg = document.createElement("div")
      noEventsMsg.id = "no-events-message"
      noEventsMsg.className = "mt-4 text-center p-4 bg-light rounded shadow-sm"
      noEventsMsg.innerHTML = `
                <i class="bi bi-info-circle me-2 text-warning"></i>
                <span>No hay eventos que coincidan con los filtros seleccionados.</span>
            `

      // Insertar después del calendario
      const calendarEl = document.getElementById("calendar")
      if (calendarEl && calendarEl.parentNode) {
        calendarEl.parentNode.insertBefore(noEventsMsg, calendarEl.nextSibling)
      }
    } else {
      // Mostrar si ya existe
      noEventsMsg.style.display = "block"
    }

    // Ocultar mensaje inicial si está visible
    hideInitialMessage()
  }

  function hideNoEventsMessage() {
    const noEventsMsg = document.getElementById("no-events-message")
    if (noEventsMsg) {
      noEventsMsg.style.display = "none"
    }
  }

  // Filtrar eventos según los filtros seleccionados
  function filterEvents() {
    const instructorFilter = document.getElementById("instructorFilter")
    const programaFilter = document.getElementById("programaFilter")
    const locationFilter = document.getElementById("locationFilter")

    // Verificar si los elementos existen
    if (!instructorFilter || !programaFilter || !locationFilter) {
      console.error("No se encontraron elementos de filtro")
      return
    }

    // Verificar si hay algún filtro activo
    const instructorValue = instructorFilter.value
    const programaValue = programaFilter.value
    const locationValue = locationFilter.value

    const hasActiveFilters = instructorValue || programaValue || locationValue

    // Limpiar el calendario de eventos
    calendar.removeAllEvents()

    // Si no hay filtros activos, mantener el calendario vacío
    if (!hasActiveFilters) {
      console.log("No hay filtros activos. No mostrando eventos.")
      hideNoEventsMessage()
      return
    }

    // Aplicar filtros
    const filteredEvents = allEvents.filter((event) => {
      // Filtro de instructor
      if (instructorValue && event.extendedProps.id_instructor != instructorValue) {
        return false
      }

      // Filtro de programa
      if (programaValue && event.extendedProps.id_programa != programaValue) {
        return false
      }

      // Filtro de ambiente
      if (locationValue && event.extendedProps.id_ambiente != locationValue) {
        return false
      }

      return true
    })

    console.log(`Filtrando eventos: ${filteredEvents.length} de ${allEvents.length} coinciden`)

    // Ocultar mensaje inicial ya que hay filtros aplicados
    hideInitialMessage()

    // Actualizar eventos en el calendario
    if (filteredEvents.length > 0) {
      // Usar un nuevo array para evitar referencias
      const eventsToAdd = filteredEvents.map((event) => ({ ...event }))

      // Añadir eventos al calendario
      calendar.addEventSource(eventsToAdd)

      // Forzar una actualización de la vista
      const currentView = calendar.view.type
      calendar.changeView(currentView)

      hideNoEventsMessage()
      setTimeout(() => {
        adjustHoursToEvents()
        fixCalendarOverflow()
      }, 300)
    } else {
      showNoEventsMessage()
    }
  }
  // Asignar eventos a los filtros
  ;["instructorFilter", "programaFilter", "locationFilter"].forEach((filterId) => {
    const element = document.getElementById(filterId)
    if (element) {
      element.addEventListener("change", filterEvents)
    } else {
      console.error(`Elemento de filtro no encontrado para evento: ${filterId}`)
    }
  })

  // Configurar el buscador
  const searchInput = document.getElementById("searchFilter")
  const clearSearchBtn = document.getElementById("clearSearch")

  if (searchInput) {
    // Evento para filtrar mientras se escribe
    searchInput.addEventListener("input", function () {
      const searchText = this.value.trim()

      // Mostrar/ocultar botón de limpiar
      if (clearSearchBtn) {
        clearSearchBtn.style.display = searchText ? "block" : "none"
      }

      // MODIFICADO: Ahora busca directamente en los eventos
      searchEvents(searchText)
    })

    // Añadir evento para buscar al presionar Enter
    searchInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault() // Evitar envío de formulario
        const searchText = this.value.trim()
        searchEvents(searchText)
      }
    })
  }

  // Configurar botón para limpiar búsqueda
  if (clearSearchBtn) {
    clearSearchBtn.addEventListener("click", function () {
      // Limpiar el campo de búsqueda
      if (searchInput) {
        searchInput.value = ""
      }

      // Ocultar el botón de limpiar
      this.style.display = "none"

      // Limpiar búsqueda y restaurar opciones
      searchEvents("")
    })
  }

  // Limpiar filtros
  const clearFiltersBtn = document.getElementById("clearFilters")
  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener("click", () => {
      // Limpiar todos los selectores de filtro
      ;["instructorFilter", "programaFilter", "locationFilter"].forEach((filterId) => {
        const element = document.getElementById(filterId)
        if (element) {
          element.value = ""
        }
      })

      // Limpiar campo de búsqueda
      if (searchInput) {
        searchInput.value = ""
      }

      // Ocultar botón de limpiar búsqueda
      if (clearSearchBtn) {
        clearSearchBtn.style.display = "none"
      }

      // Restaurar todas las opciones originales
      restoreOriginalOptions("instructorFilter", originalFilterOptions.instructor)
      restoreOriginalOptions("programaFilter", originalFilterOptions.programa)
      restoreOriginalOptions("locationFilter", originalFilterOptions.ambiente)

      // Limpiar calendario
      calendar.removeAllEvents()

      // MODIFICADO: No mostrar mensaje inicial
      // showInitialMessage();
      hideNoEventsMessage()

      console.log("Filtros limpiados - Calendario limpio, esperando selección de filtros")
    })
  } else {
    console.error('Botón "clearFilters" no encontrado')
  }

  // Configuración del manejo de filtros responsivo
  const toggleFilters = document.getElementById("toggleFilters")
  const filterForm = document.getElementById("event-filter-form")

  if (toggleFilters && filterForm) {
    toggleFilters.addEventListener("click", () => {
      const isExpanded = toggleFilters.getAttribute("aria-expanded") === "true"
      toggleFilters.setAttribute("aria-expanded", !isExpanded)

      if (window.innerWidth <= 992) {
        if (!isExpanded) {
          // Mostrar filtros
          filterForm.classList.add("show")
        } else {
          // Ocultar filtros
          filterForm.classList.remove("show")
        }
      }
    })

    // Manejar cambios de tamaño de ventana
    window.addEventListener("resize", () => {
      if (window.innerWidth > 992) {
        filterForm.classList.remove("show")
        if (toggleFilters) {
          toggleFilters.setAttribute("aria-expanded", "false")
        }
      }

      // Asegurar que no haya desbordamiento después de cambiar el tamaño
      setTimeout(fixCalendarOverflow, 100)
    })
  }

  // Inicialización
  calendar.render() // Renderizar el calendario

  // Asegurar que no haya desbordamiento después de renderizar
  setTimeout(fixCalendarOverflow, 300)

  // Cargar todos los eventos pero no mostrarlos hasta que se usen filtros
  loadAllEvents()

  console.log('Calendario inicializado en modo "filtrar primero"')
})
